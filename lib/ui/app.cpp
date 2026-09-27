#include "app.h"

#include <cstdlib>
#include <cstring>

#include "screens.h"

namespace ui {

namespace {

const char* const kSettingsFile = "settings.txt";

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

App::App(Platform& platform) : _platform(platform)
{
    _screens[static_cast<size_t>(ScreenId::Home)]     = makeHomeScreen();
    _screens[static_cast<size_t>(ScreenId::Menu)]     = makeMenuScreen();
    _screens[static_cast<size_t>(ScreenId::Kana)]     = makeKanaScreen();
    _screens[static_cast<size_t>(ScreenId::Settings)] = makeSettingsScreen();
}

App::~App() = default;

void App::begin()
{
    loadSettings();
    _current = ScreenId::Home;
    _screens[static_cast<size_t>(_current)]->enter(*this);
    _dirty = true;
}

void App::key(const Key& key)
{
    if (key.code == Key::None) {
        return;
    }
    _screens[static_cast<size_t>(_current)]->key(*this, key);
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
            _settings.dayNumber = day > 0 ? day : 1;
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
    text += "\n";
    _platform.save(kSettingsFile, text);
}

}  // namespace ui
