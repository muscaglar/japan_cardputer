#include <cstdio>
#include <string>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

enum Row { kLook, kLevel, kRomaji, kSound, kVolume, kVoice, kTyping, kRowCount };

constexpr int kVisible   = 5;  // rows on the screen at once
constexpr int kLoudest   = 5;
constexpr int kArrowRoom = 8;  // kept free at the right edge for ▲ and ▼

const char* const kIds[kRowCount]    = {"look", "cards", "romaji", "sound", "volume", "voice", "typing"};
const char* const kLabels[kRowCount] = {"Look", "Cards", "Romaji", "Sound", "Volume", "Voice", "Typing ん"};

// What is played after a change to volume or voice: あ, which every voice has.
const char* const kSample = "/hiragana/hiragana-a.wav";

bool sample(App& app, const char* folder)
{
    const std::string path = std::string("/audio/") + folder + kSample;
    return app.speakFile(path.c_str());
}

std::string valueOf(App& app, int row)
{
    const Settings& s = app.settings();
    switch (row) {
        case kLook:
            return theme(s.theme).nameEn;
        case kLevel:
            return (s.level == 1) ? "kana only" : (s.level == 2) ? "easy kanji too" : "all";
        case kRomaji:
            return (s.romaji == RomajiMode::Always) ? "always" : (s.romaji == RomajiMode::Never) ? "never" : "with Tab";
        case kSound:
            if (!s.sound) {
                return "off";
            }
            return app.platform().hasCard() ? "on" : "on, no card";
        case kVolume:
            return std::to_string(s.volume) + " of " + std::to_string(kLoudest);
        case kVoice:
            return (s.voice == Voice::Female) ? "female" : (s.voice == Voice::Male) ? "male" : "both";
        case kTyping:
            return s.textbookN ? "minna = みんな" : "minnna = みんな";
        default:
            return "";
    }
}

class SettingsScreen : public Screen {
public:
    // Always opens at the first row, the look.
    void enter(App& app) override
    {
        _app   = &app;
        _row   = 0;
        _first = 0;
        _then  = nullptr;
        _card  = app.platform().hasCard();
    }

    void key(App& app, const Key& key) override
    {
        Settings& s          = app.settings();
        const Key::Code move = navigation(key);
        _then                = nullptr;
        if (move == Key::Up) {
            _row = (_row + kRowCount - 1) % kRowCount;
            keepInSight();
        } else if (move == Key::Down) {
            _row = (_row + 1) % kRowCount;
            keepInSight();
        } else if (move == Key::Left || move == Key::Right || key.code == Key::Enter) {
            const int step = (move == Key::Left) ? -1 : 1;
            bool changed   = true;
            switch (_row) {
                case kLook: {
                    const int count = static_cast<int>(ThemeId::Count);
                    s.theme = static_cast<ThemeId>((static_cast<int>(s.theme) + count + step) % count);
                    break;
                }
                case kLevel:
                    s.level = 1 + (s.level - 1 + 3 + step) % 3;
                    break;
                case kRomaji: {
                    const int count = static_cast<int>(RomajiMode::Count);
                    s.romaji = static_cast<RomajiMode>((static_cast<int>(s.romaji) + count + step) % count);
                    break;
                }
                case kSound:
                    s.sound = !s.sound;
                    break;
                case kVolume: {
                    // Stops at both ends: one step past the loudest must not be the quietest.
                    const int volume = s.volume + step;
                    changed          = (volume >= 1 && volume <= kLoudest);
                    if (changed) {
                        s.volume = volume;
                    }
                    break;
                }
                case kVoice: {
                    const int count = static_cast<int>(Voice::Count);
                    s.voice = static_cast<Voice>((static_cast<int>(s.voice) + count + step) % count);
                    break;
                }
                case kTyping:
                    s.textbookN = !s.textbookN;
                    break;
                default:
                    break;
            }
            if (changed) {
                app.saveSettings();
            }
            if (_row == kVolume || _row == kVoice) {
                hear(app, _row == kVoice);
            }
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab) {
            app.show(ScreenId::Menu);
        }
    }

    void tick(App& app) override
    {
        // the row Sound says whether the memory card is in
        const bool card = app.platform().hasCard();
        if (card != _card) {
            _card = card;
            app.invalidate();
        }
        if (_then && !app.platform().playing()) {
            const char* folder = _then;
            _then              = nullptr;
            sample(app, folder);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        char place[12];
        std::snprintf(place, sizeof(place), "%d/%d", _row + 1, static_cast<int>(kRowCount));
        drawFrame(c, t, "Settings", place, "↑↓ choose", "←→ change");
        const Area a        = contentArea(t);
        const int rowHeight = a.h / kVisible;
        const int top       = a.y + (a.h - rowHeight * kVisible) / 2;
        const int textTop   = (rowHeight - 16) / 2;
        int y               = top;
        for (int row = _first; row < _first + kVisible; ++row) {
            const bool chosen = (row == _row);
            if (chosen) {
                c.fillRoundRect(a.x - 2, y, a.w, rowHeight, 3, t.row);
            }
            text(c, a.x + 2, y + textTop, kLabels[row], font16(), chosen ? t.rowInk : t.ink);
            textRight(c, a.x + a.w - 6 - kArrowRoom, y + textTop, valueOf(app, row).c_str(), font16(),
                      chosen ? t.accent : t.dim);
            y += rowHeight;
        }
        // more rows above or below
        if (_first > 0) {
            textRight(c, a.x + a.w - 3, top + textTop, "▲", font16(), t.dim);
        }
        if (_first + kVisible < kRowCount) {
            textRight(c, a.x + a.w - 3, top + (kVisible - 1) * rowHeight + textTop, "▼", font16(), t.dim);
        }
    }

    void describe(std::string& json) const override
    {
        json += ",\"rows\":[";
        for (int row = 0; row < kRowCount; ++row) {
            json += (row ? ",\"" : "\"");
            json += kIds[row];
            json += "\"";
        }
        json += "],\"values\":[";
        for (int row = 0; row < kRowCount; ++row) {
            json += (row ? ",\"" : "\"");
            json += _app ? valueOf(*_app, row) : std::string();
            json += "\"";
        }
        json += "],\"chosen\":";
        json += std::to_string(_row);
        json += ",\"first\":";
        json += std::to_string(_first);
        json += ",\"visible\":";
        json += std::to_string(kVisible);
    }

private:
    void keepInSight()
    {
        if (_row < _first) {
            _first = _row;
        } else if (_row >= _first + kVisible) {
            _first = _row - kVisible + 1;
        }
    }

    // Lets the owner hear what was set. After a change of voice it is the voice that was
    // chosen, and nothing if that voice has no clip; "both" is the woman, then the man.
    // After a change of volume it is one voice, the same at every step, so that only the
    // loudness differs. The turn the voices take on the cards is left as it was.
    void hear(App& app, bool voiceChanged)
    {
        const Settings& s = app.settings();
        if (!s.sound || !app.platform().hasCard()) {
            return;
        }
        if (voiceChanged && s.voice == Voice::Both) {
            if (sample(app, "f")) {
                _then = "m";
            } else {
                sample(app, "m");
            }
            return;
        }
        const bool male = (s.voice == Voice::Male);
        if (!sample(app, male ? "m" : "f") && !voiceChanged) {
            sample(app, male ? "f" : "m");
        }
    }

    App* _app         = nullptr;  // for describe(), which is not handed the app
    int _row          = 0;
    int _first        = 0;        // the row at the top of the screen
    const char* _then = nullptr;  // the voice to be heard once the first has finished
    bool _card        = false;    // whether the memory card was in when last looked
};

}  // namespace

std::unique_ptr<Screen> makeSettingsScreen()
{
    return std::unique_ptr<Screen>(new SettingsScreen());
}

}  // namespace ui
