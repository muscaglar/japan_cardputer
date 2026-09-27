#include "progress.h"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace progress {

namespace {

const char* const kSnapshot = "progress.txt";
const char* const kLog      = "reviews.log";
constexpr size_t kFoldAfter = 200;  // answers in the log before it is folded into the snapshot

// Calls `each` with every line of `text`, without the line ending.
template <typename F>
void lines(const std::string& text, F each)
{
    size_t start = 0;
    while (start < text.size()) {
        size_t end = text.find('\n', start);
        if (end == std::string::npos) {
            end = text.size();
        }
        std::string line = text.substr(start, end - start);
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        if (!line.empty()) {
            each(line);
        }
        start = end + 1;
    }
}

// Reads unsigned numbers separated by spaces. The first is hexadecimal when `firstHex` is set.
bool numbers(const std::string& line, unsigned long* out, size_t count, size_t hexIndex)
{
    const char* p = line.c_str();
    for (size_t i = 0; i < count; ++i) {
        while (*p == ' ') {
            ++p;
        }
        if (*p == 0) {
            return false;
        }
        char* end = nullptr;
        out[i]    = std::strtoul(p, &end, i == hexIndex ? 16 : 10);
        if (end == p) {
            return false;
        }
        p = end;
    }
    while (*p == ' ') {
        ++p;
    }
    return *p == 0;
}

}  // namespace

Store::Store(core::Storage& storage) : _storage(storage) {}

Store::Entry* Store::find(uint32_t itemKey)
{
    auto it = std::lower_bound(_entries.begin(), _entries.end(), itemKey,
                               [](const Entry& e, uint32_t key) { return e.key < key; });
    return (it != _entries.end() && it->key == itemKey) ? &*it : nullptr;
}

const Store::Entry* Store::find(uint32_t itemKey) const
{
    auto it = std::lower_bound(_entries.begin(), _entries.end(), itemKey,
                               [](const Entry& e, uint32_t key) { return e.key < key; });
    return (it != _entries.end() && it->key == itemKey) ? &*it : nullptr;
}

void Store::put(uint32_t itemKey, const srs::Card& card)
{
    auto it = std::lower_bound(_entries.begin(), _entries.end(), itemKey,
                               [](const Entry& e, uint32_t key) { return e.key < key; });
    if (it != _entries.end() && it->key == itemKey) {
        it->card = card;
    } else {
        _entries.insert(it, Entry{itemKey, card});
    }
}

void Store::load()
{
    _entries.clear();
    _logged = 0;

    std::string text;
    if (_storage.load(kSnapshot, text)) {
        lines(text, [this](const std::string& line) {
            unsigned long v[7];
            if (!numbers(line, v, 7, 0) || v[4] > 2 || v[3] > 255 || v[5] > 255 || v[6] > 255 || v[1] > 0xFFFF ||
                v[2] > 0xFFFF) {
                return;  // a damaged line costs one card, not the file
            }
            srs::Card card;
            card.due      = static_cast<uint16_t>(v[1]);
            card.interval = static_cast<uint16_t>(v[2]);
            card.ease     = static_cast<uint8_t>(v[3]);
            card.stage    = static_cast<srs::Stage>(v[4]);
            card.streak   = static_cast<uint8_t>(v[5]);
            card.lapses   = static_cast<uint8_t>(v[6]);
            put(static_cast<uint32_t>(v[0]), card);
        });
    }

    text.clear();
    if (_storage.load(kLog, text)) {
        lines(text, [this](const std::string& line) {
            unsigned long v[3];
            if (!numbers(line, v, 3, 1) || v[2] > 2 || v[0] > 0xFFFF) {
                return;
            }
            const uint32_t itemKey = static_cast<uint32_t>(v[1]);
            put(itemKey, srs::answer(get(itemKey), static_cast<srs::Grade>(v[2]), static_cast<uint16_t>(v[0])));
            ++_logged;
        });
    }
}

srs::Card Store::get(uint32_t itemKey) const
{
    const Entry* entry = find(itemKey);
    return entry ? entry->card : srs::Card();
}

srs::Card Store::record(uint32_t itemKey, srs::Grade grade, uint16_t today)
{
    const srs::Card card = srs::answer(get(itemKey), grade, today);
    put(itemKey, card);

    char line[40];
    std::snprintf(line, sizeof(line), "%u %08lx %u", static_cast<unsigned>(today), static_cast<unsigned long>(itemKey),
                  static_cast<unsigned>(grade));
    _storage.append(kLog, line);
    if (++_logged >= kFoldAfter) {
        checkpoint();
    }
    return card;
}

bool Store::checkpoint()
{
    std::string text;
    text.reserve(_entries.size() * 32);
    for (const Entry& e : _entries) {
        char line[64];
        std::snprintf(line, sizeof(line), "%08lx %u %u %u %u %u %u\n", static_cast<unsigned long>(e.key),
                      static_cast<unsigned>(e.card.due), static_cast<unsigned>(e.card.interval),
                      static_cast<unsigned>(e.card.ease), static_cast<unsigned>(e.card.stage),
                      static_cast<unsigned>(e.card.streak), static_cast<unsigned>(e.card.lapses));
        text += line;
    }
    // The snapshot first: if power fails between the two writes, replaying the old log over the
    // new snapshot repeats a few answers, which is harmless compared with losing them.
    if (!_storage.save(kSnapshot, text)) {
        return false;
    }
    if (!_storage.save(kLog, std::string())) {
        return false;
    }
    _logged = 0;
    return true;
}

size_t Store::seen() const
{
    return _entries.size();
}

size_t Store::dueOn(uint16_t today) const
{
    size_t count = 0;
    for (const Entry& e : _entries) {
        if (srs::due(e.card, today)) {
            ++count;
        }
    }
    return count;
}

size_t Store::learnt() const
{
    size_t count = 0;
    for (const Entry& e : _entries) {
        if (e.card.stage == srs::Stage::Review) {
            ++count;
        }
    }
    return count;
}

void Store::reset()
{
    _entries.clear();
    _logged = 0;
    _storage.save(kSnapshot, std::string());
    _storage.save(kLog, std::string());
}

}  // namespace progress
