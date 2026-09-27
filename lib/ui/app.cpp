#include "app.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "screens.h"

namespace ui {

namespace {

const char* const kSettingsFile = "settings.txt";

constexpr uint16_t kCardsPerSitting = 12;
constexpr uint16_t kNewPerSitting   = 4;

const char* romajiKey(RomajiMode mode)
{
    switch (mode) {
        case RomajiMode::Always: return "always";
        case RomajiMode::Never:  return "never";
        default:                 return "peek";
    }
}

RomajiMode romajiFromKey(const std::string& key)
{
    if (key == "always") return RomajiMode::Always;
    if (key == "never") return RomajiMode::Never;
    return RomajiMode::Peek;
}

}  // namespace

Key::Code navigation(const Key& key)
{
    switch (key.code) {
        case Key::Up:
        case Key::Down:
        case Key::Left:
        case Key::Right:
            return key.code;
        case Key::Char:
            switch (key.ch) {
                case ';': return Key::Up;
                case '.': return Key::Down;
                case ',': return Key::Left;
                case '/': return Key::Right;
                default:  return Key::None;
            }
        default:
            return Key::None;
    }
}

App::App(Platform& platform) : _platform(platform), _store(platform), _queue(_store)
{
    _screens[static_cast<size_t>(ScreenId::Home)]     = makeHomeScreen();
    _screens[static_cast<size_t>(ScreenId::Menu)]     = makeMenuScreen();
    _screens[static_cast<size_t>(ScreenId::Kana)]     = makeKanaScreen();
    _screens[static_cast<size_t>(ScreenId::Settings)] = makeSettingsScreen();
    _screens[static_cast<size_t>(ScreenId::Cards)]    = makeCardsScreen();
    _screens[static_cast<size_t>(ScreenId::Summary)]  = makeSummaryScreen();
    _screens[static_cast<size_t>(ScreenId::Keys)]     = makeKeysScreen();
}

App::~App() = default;

void App::begin()
{
    loadSettings();
    _store.load();
    _current = ScreenId::Home;
    _screens[static_cast<size_t>(_current)]->enter(*this);
    _dirty = true;
}

void App::key(const Key& key)
{
    if (key.code == Key::None) {
        return;
    }
    // The button on the edge of the device goes back, like Esc, which needs two fingers.
    const Key pressed = (key.code == Key::Button) ? Key::of(Key::Escape) : key;
    _screens[static_cast<size_t>(_current)]->key(*this, pressed);
    _dirty = true;
}

void App::tick()
{
    _screens[static_cast<size_t>(_current)]->tick(*this);
}

bool App::draw(Canvas& canvas)
{
    if (!_dirty) {
        return false;
    }
    _dirty = false;
    _screens[static_cast<size_t>(_current)]->draw(*this, canvas);
    return true;
}

void App::show(ScreenId id)
{
    if (id >= ScreenId::Count) {
        return;
    }
    _current = id;
    _screens[static_cast<size_t>(_current)]->enter(*this);
    _dirty = true;
}

void App::startSitting(const deck::Deck* deck)
{
    _sitting      = Sitting();
    _sitting.deck = deck;

    std::vector<const deck::Deck*> decks;
    if (deck) {
        decks.push_back(deck);
    } else {
        for (size_t i = 0; i < deck::count(); ++i) {
            decks.push_back(&deck::at(i));
        }
    }
    session::Plan plan;
    plan.today    = today();
    plan.maxCards = kCardsPerSitting;
    plan.maxNew   = kNewPerSitting;
    plan.level    = static_cast<uint8_t>(_settings.level);
    // The same day brings the decks in the same turn; the next day starts with another deck.
    plan.seed = static_cast<uint32_t>(_settings.dayNumber);
    _queue.start(plan, decks);
    show(ScreenId::Cards);
}

void App::endSitting()
{
    _store.checkpoint();
    saveSettings();
}

void App::startNewDay()
{
    ++_settings.dayNumber;
    _settings.answeredToday = 0;
    saveSettings();
}

int App::dueToday() const
{
    return static_cast<int>(_store.dueOn(today()));
}

int App::newAvailable() const
{
    int count = 0;
    for (size_t d = 0; d < deck::count(); ++d) {
        const deck::Deck& deck = deck::at(d);
        for (uint16_t i = 0; i < deck.count; ++i) {
            if (deck.items[i].level <= _settings.level &&
                _store.get(deck::key(deck.items[i].id)).stage == srs::Stage::New) {
                if (++count >= kNewPerSitting) {
                    return count;
                }
            }
        }
    }
    return count;
}

std::string App::describe() const
{
    char text[320];
    std::snprintf(text, sizeof(text),
                  "{\"screen\":%d,\"look\":\"%s\",\"romaji\":\"%s\",\"sound\":%s,\"textbookN\":%s,\"level\":%d,"
                  "\"day\":%d,\"answeredToday\":%d,\"due\":%d,\"new\":%d,\"seen\":%u,\"learnt\":%u",
                  static_cast<int>(_current), theme().key, romajiKey(_settings.romaji),
                  _settings.sound ? "true" : "false", _settings.textbookN ? "true" : "false", _settings.level,
                  _settings.dayNumber, _settings.answeredToday, dueToday(), newAvailable(),
                  static_cast<unsigned>(_store.seen()), static_cast<unsigned>(_store.learnt()));
    std::string all = text;
    _screens[static_cast<size_t>(_current)]->describe(all);
    all += "}";
    return all;
}

void App::startFresh()
{
    _store.reset();
    _settings.dayNumber     = 1;
    _settings.answeredToday = 0;
    saveSettings();
    show(ScreenId::Home);
}

namespace {

const char* const kKept[][2] = {
    {"settings.txt", "settings.bak"},
    {"progress.txt", "progress.bak"},
    {"reviews.log", "reviews.bak"},
};

}  // namespace

bool App::keepAside()
{
    saveSettings();
    bool ok = true;
    for (const auto& pair : kKept) {
        std::string text;
        _platform.load(pair[0], text);  // a file that does not exist yet is kept as an empty one
        ok = _platform.save(pair[1], text) && ok;
    }
    return ok;
}

bool App::bringBack()
{
    bool ok = true;
    for (const auto& pair : kKept) {
        std::string text;
        if (!_platform.load(pair[1], text)) {
            return false;  // nothing was kept aside
        }
        ok = _platform.save(pair[0], text) && ok;
    }
    _settings = Settings();
    loadSettings();
    _store.load();
    show(ScreenId::Home);
    return ok;
}

void App::loadSettings()
{
    std::string text;
    if (!_platform.load(kSettingsFile, text)) {
        return;
    }
    size_t start = 0;
    while (start < text.size()) {
        size_t end = text.find('\n', start);
        if (end == std::string::npos) {
            end = text.size();
        }
        const std::string line = text.substr(start, end - start);
        start                  = end + 1;
        const size_t equals    = line.find('=');
        if (equals == std::string::npos) {
            continue;
        }
        const std::string name  = line.substr(0, equals);
        const std::string value = line.substr(equals + 1);
        if (name == "theme") {
            _settings.theme = themeByKey(value.c_str()).id;
        } else if (name == "romaji") {
            _settings.romaji = romajiFromKey(value);
        } else if (name == "textbook_n") {
            _settings.textbookN = (value != "0");
        } else if (name == "sound") {
            _settings.sound = (value == "1");
        } else if (name == "day") {
            const int day = std::atoi(value.c_str());
            _settings.dayNumber = (day > 0 && day < 60000) ? day : 1;
        } else if (name == "answered_today") {
            const int answered = std::atoi(value.c_str());
            _settings.answeredToday = answered > 0 ? answered : 0;
        } else if (name == "level") {
            const int level = std::atoi(value.c_str());
            _settings.level = (level >= 1 && level <= 3) ? level : 3;
        }
    }
}

void App::saveSettings()
{
    std::string text;
    text += "theme=";
    text += ui::theme(_settings.theme).key;
    text += "\nromaji=";
    text += romajiKey(_settings.romaji);
    text += "\ntextbook_n=";
    text += _settings.textbookN ? "1" : "0";
    text += "\nsound=";
    text += _settings.sound ? "1" : "0";
    text += "\nday=";
    text += std::to_string(_settings.dayNumber);
    text += "\nanswered_today=";
    text += std::to_string(_settings.answeredToday);
    text += "\nlevel=";
    text += std::to_string(_settings.level);
    text += "\n";
    _platform.save(kSettingsFile, text);
}

}  // namespace ui
