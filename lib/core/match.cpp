#include "match.h"

#include <cstdint>
#include <vector>

#include "kana.h"

namespace match {

namespace {

const char* const kLong = "L";  // stands for "the vowel before is held for one more beat"

size_t decode(const std::string& s, size_t i, uint32_t& code)
{
    const unsigned char b0 = static_cast<unsigned char>(s[i]);
    const size_t left      = s.size() - i;
    if ((b0 & 0xE0) == 0xC0 && left >= 2) {
        code = ((b0 & 0x1Fu) << 6) | (static_cast<unsigned char>(s[i + 1]) & 0x3Fu);
        return 2;
    }
    if ((b0 & 0xF0) == 0xE0 && left >= 3) {
        code = ((b0 & 0x0Fu) << 12) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 6) |
               (static_cast<unsigned char>(s[i + 2]) & 0x3Fu);
        return 3;
    }
    if ((b0 & 0xF8) == 0xF0 && left >= 4) {
        code = ((b0 & 0x07u) << 18) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 12) |
               ((static_cast<unsigned char>(s[i + 2]) & 0x3Fu) << 6) | (static_cast<unsigned char>(s[i + 3]) & 0x3Fu);
        return 4;
    }
    code = b0;
    return 1;
}

void encode(uint32_t code, std::string& out)
{
    if (code < 0x80) {
        out.push_back(static_cast<char>(code));
    } else if (code < 0x800) {
        out.push_back(static_cast<char>(0xC0 | (code >> 6)));
        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
    } else {
        out.push_back(static_cast<char>(0xE0 | (code >> 12)));
        out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
    }
}

bool contains(const char* set, uint32_t code)
{
    const std::string s(set);
    size_t i = 0;
    while (i < s.size()) {
        uint32_t c = 0;
        i += decode(s, i, c);
        if (c == code) {
            return true;
        }
    }
    return false;
}

// The vowel a hiragana ends in: 'a', 'i', 'u', 'e', 'o', or 0 for ん, っ and anything else.
char vowelOf(uint32_t code)
{
    if (contains("あかがさざただなはばぱまやらわぁゃゎ", code)) return 'a';
    if (contains("いきぎしじちぢにひびぴみりぃ", code)) return 'i';
    if (contains("うくぐすずつづぬふぶぷむゆるぅゅゔ", code)) return 'u';
    if (contains("えけげせぜてでねへべぺめれぇ", code)) return 'e';
    if (contains("おこごそぞとどのほぼぽもよろをぉょ", code)) return 'o';
    return 0;
}

uint32_t vowelKana(char vowel)
{
    switch (vowel) {
        case 'a': return 0x3042;
        case 'i': return 0x3044;
        case 'u': return 0x3046;
        case 'e': return 0x3048;
        case 'o': return 0x304A;
        default:  return 0;
    }
}

bool dropped(uint32_t code)
{
    if (code == ' ' || code == 0x3000 || code == '\t') {
        return true;
    }
    if (code < 0x80) {
        return code == ',' || code == '.' || code == '!' || code == '?' || code == '\'' || code == '"' || code == '-';
    }
    return contains("、。！？・「」〜", code);
}

uint32_t lastCode(const std::string& s)
{
    uint32_t code = 0;
    size_t i      = 0;
    while (i < s.size()) {
        i += decode(s, i, code);
    }
    return code;
}

uint32_t firstCode(const std::string& s)
{
    uint32_t code = 0;
    if (!s.empty()) {
        decode(s, 0, code);
    }
    return code;
}

// Whether a beat that is a bare vowel only lengthens the beat before it.
bool lengthens(const std::string& beat, const std::string& before)
{
    const uint32_t code = firstCode(beat);
    if (beat.size() != 3 || !contains("あいうえお", code)) {
        return false;
    }
    const char held = vowelOf(lastCode(before));
    switch (held) {
        case 'a': return code == 0x3042;
        case 'i': return code == 0x3044;
        case 'u': return code == 0x3046;
        case 'e': return code == 0x3048 || code == 0x3044;  // ええ, えい
        case 'o': return code == 0x304A || code == 0x3046;  // おお, おう
        default:  return false;
    }
}

// The sounds of a normalised answer, one entry per beat, with every long vowel written the same way.
std::vector<std::string> sounds(const std::string& normalised)
{
    const std::vector<std::string> beats = kana::beats(normalised);
    std::vector<std::string> out;
    out.reserve(beats.size());
    for (size_t i = 0; i < beats.size(); ++i) {
        // A vowel that follows a long vowel is a syllable of its own again.
        if (i > 0 && out.back() != kLong && lengthens(beats[i], beats[i - 1])) {
            out.push_back(kLong);
        } else {
            out.push_back(beats[i]);
        }
    }
    return out;
}

std::string unvoiced(const std::string& beat)
{
    static const char* const kVoiced   = "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゔ";
    static const char* const kUnvoiced = "かきくけこさしすせそたちつてとはひふへほはひふへほう";
    const std::string voiced(kVoiced);
    const std::string plain(kUnvoiced);
    const uint32_t first = firstCode(beat);
    size_t i = 0;
    size_t index = 0;
    while (i < voiced.size()) {
        uint32_t c = 0;
        i += decode(voiced, i, c);
        if (c == first) {
            std::string out(plain, index * 3, 3);
            out.append(beat, 3, std::string::npos);
            return out;
        }
        ++index;
    }
    return beat;
}

std::vector<std::string> split(const char* list)
{
    std::vector<std::string> out;
    std::string current;
    for (const char* p = list; p && *p; ++p) {
        if (*p == '|') {
            if (!current.empty()) {
                out.push_back(current);
            }
            current.clear();
        } else {
            current.push_back(*p);
        }
    }
    if (!current.empty()) {
        out.push_back(current);
    }
    return out;
}

int firstDifference(const std::vector<std::string>& a, const std::vector<std::string>& b)
{
    size_t i = 0;
    while (i < a.size() && i < b.size() && a[i] == b[i]) {
        ++i;
    }
    return static_cast<int>(i);
}

// If removing one entry from `longer` gives `shorter`, returns that entry; otherwise an empty string.
std::string oneExtra(const std::vector<std::string>& longer, const std::vector<std::string>& shorter)
{
    if (longer.size() != shorter.size() + 1) {
        return std::string();
    }
    size_t i = 0;
    while (i < shorter.size() && longer[i] == shorter[i]) {
        ++i;
    }
    for (size_t k = i; k < shorter.size(); ++k) {
        if (longer[k + 1] != shorter[k]) {
            return std::string();
        }
    }
    return longer[i];
}

Slip slipFor(const std::string& unit)
{
    if (unit == kLong) return Slip::LongVowel;
    if (unit == "っ") return Slip::SmallTsu;
    if (unit == "ん") return Slip::N;
    return Slip::Other;
}

Outcome compare(const std::string& typed, const std::string& candidate)
{
    Outcome outcome;
    outcome.expected = candidate;

    const std::string a = normalise(typed);
    const std::string b = normalise(candidate);
    if (!a.empty() && a == b) {
        outcome.verdict = Verdict::Right;
        outcome.slip    = Slip::None;
        outcome.beat    = -1;
        return outcome;
    }

    const std::vector<std::string> said   = sounds(a);
    const std::vector<std::string> wanted = sounds(b);
    outcome.beat = firstDifference(wanted, said);
    if (a.empty()) {
        return outcome;
    }

    if (said == wanted) {
        // the same sounds, spelled another way: おお for おう
        outcome.verdict = Verdict::Almost;
        outcome.slip    = Slip::LongVowel;
        outcome.beat    = firstDifference(kana::beats(b), kana::beats(a));
        return outcome;
    }

    const std::string missing = oneExtra(wanted, said);
    const std::string extra   = oneExtra(said, wanted);
    const Slip slip           = !missing.empty() ? slipFor(missing) : !extra.empty() ? slipFor(extra) : Slip::Other;
    if (slip != Slip::Other) {
        outcome.verdict = Verdict::Almost;
        outcome.slip    = slip;
        return outcome;
    }

    if (said.size() == wanted.size()) {
        int differences = 0;
        size_t where    = 0;
        for (size_t i = 0; i < said.size(); ++i) {
            if (said[i] != wanted[i]) {
                ++differences;
                where = i;
            }
        }
        if (differences == 1 && unvoiced(said[where]) == unvoiced(wanted[where])) {
            outcome.verdict = Verdict::Almost;
            outcome.slip    = Slip::Voicing;
            outcome.beat    = static_cast<int>(where);
            return outcome;
        }
    }
    return outcome;
}

int rank(Verdict verdict)
{
    switch (verdict) {
        case Verdict::Right:  return 2;
        case Verdict::Almost: return 1;
        default:              return 0;
    }
}

}  // namespace

std::string normalise(const std::string& text)
{
    const std::string hira = kana::toHiragana(text);
    std::string out;
    out.reserve(hira.size());
    uint32_t previous = 0;
    size_t i          = 0;
    while (i < hira.size()) {
        uint32_t code  = 0;
        const size_t n = decode(hira, i, code);
        i += n;
        if (code == 0x30FC) {  // ー
            const uint32_t vowel = vowelKana(vowelOf(previous));
            if (vowel) {
                encode(vowel, out);
                previous = vowel;
            }
            continue;
        }
        if (dropped(code)) {
            continue;
        }
        encode(code, out);
        previous = code;
    }
    return out;
}

Outcome check(const std::string& typedKana, const deck::Item& item)
{
    std::vector<std::string> candidates;
    candidates.push_back(item.reading ? item.reading : "");
    const std::vector<std::string> more = split(item.accepted);
    candidates.insert(candidates.end(), more.begin(), more.end());

    Outcome best = compare(typedKana, candidates[0]);
    for (size_t i = 1; i < candidates.size() && best.verdict != Verdict::Right; ++i) {
        const Outcome next = compare(typedKana, candidates[i]);
        if (rank(next.verdict) > rank(best.verdict)) {
            best = next;
        }
    }
    return best;
}

}  // namespace match
