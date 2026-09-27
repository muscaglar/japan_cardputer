#include <cstdio>
#include <string>

#include "../screens.h"
#include "../widgets.h"
#include "kana.h"
#include "romaji.h"

namespace ui {

namespace {

// The 46 basic kana, then the voiced ones, then the combinations. A round draws from the first
// group until most of it is answered correctly, then widens.
const char* const kBasic[] = {
    "あ", "い", "う", "え", "お", "か", "き", "く", "け", "こ", "さ", "し", "す", "せ", "そ", "た", "ち", "つ",
    "て", "と", "な", "に", "ぬ", "ね", "の", "は", "ひ", "ふ", "へ", "ほ", "ま", "み", "む", "め", "も", "や",
    "ゆ", "よ", "ら", "り", "る", "れ", "ろ", "わ", "を", "ん",
};
const char* const kVoiced[] = {
    "が", "ぎ", "ぐ", "げ", "ご", "ざ", "じ", "ず", "ぜ", "ぞ", "だ", "で", "ど", "ば", "び", "ぶ", "べ", "ぼ",
    "ぱ", "ぴ", "ぷ", "ぺ", "ぽ",
};
const char* const kCombined[] = {
    "きゃ", "きゅ", "きょ", "しゃ", "しゅ", "しょ", "ちゃ", "ちゅ", "ちょ", "にゃ", "にゅ", "にょ",
    "ひゃ", "ひゅ", "ひょ", "みゃ", "みゅ", "みょ", "りゃ", "りゅ", "りょ", "ぎゃ", "ぎゅ", "ぎょ",
    "じゃ", "じゅ", "じょ", "びゃ", "びゅ", "びょ", "ぴゃ", "ぴゅ", "ぴょ",
};
constexpr int kBasicCount    = sizeof(kBasic) / sizeof(kBasic[0]);
constexpr int kVoicedCount   = sizeof(kVoiced) / sizeof(kVoiced[0]);
constexpr int kCombinedCount = sizeof(kCombined) / sizeof(kCombined[0]);
constexpr int kRound         = 20;

enum class State : uint8_t { Typing, Right, Wrong, Done };

const deck::Item* itemWithPrompt(const deck::Deck* deck, const std::string& prompt)
{
    for (uint16_t i = 0; deck && i < deck->count; ++i) {
        if (prompt == deck->items[i].prompt) {
            return &deck->items[i];
        }
    }
    return nullptr;
}

class KanaScreen : public Screen {
public:
    void enter(App& app) override
    {
        _asked   = 0;
        _correct = 0;
        _state   = State::Typing;
        _typed.clear();
        pick(app);
    }

    void key(App& app, const Key& key) override
    {
        if (key.code == Key::Escape) {
            app.show(ScreenId::Home);
            return;
        }
        if (_state == State::Done) {
            if (key.code == Key::Enter) {
                enter(app);
            } else {
                app.show(ScreenId::Home);
            }
            return;
        }
        if (_state != State::Typing) {
            // / lets the kana be heard once more; without a clip it is a key like any other
            if (_heard && navigation(key) == Key::Right && hear(app)) {
                return;
            }
            next(app);
            return;
        }
        switch (key.code) {
            case Key::Tab:
                if (app.settings().romaji != RomajiMode::Never) {
                    _peek = true;
                }
                break;
            case Key::Backspace:
                if (!_typed.empty()) {
                    _typed.pop_back();
                }
                break;
            case Key::Enter:
                if (!_typed.empty()) {
                    check(app);
                }
                break;
            case Key::Char:
                if (key.ch == ' ') {
                    _katakana = !_katakana;
                } else if (key.fn && (key.ch == 'r' || key.ch == 'R')) {
                    if (app.settings().romaji != RomajiMode::Never) {
                        _peek = true;
                    }
                } else if (_typed.size() < 8 && key.ch > ' ') {
                    _typed.push_back(key.ch);
                }
                break;
            default:
                break;
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t    = app.theme();
        const Settings& s = app.settings();
        const Area a      = contentArea(t);
        const int centre  = a.x + a.w / 2;

        if (_state == State::Done) {
            drawFrame(c, t, "Kana", "done", "Enter: again", "Any key: home");
            char score[32];
            std::snprintf(score, sizeof(score), "%d of %d right", _correct, kRound);
            textCentre(c, centre, a.y + 18, score, font24(), t.good);
            drawMessage(c, t, _correct == kRound ? "Every one right!" : "Once more?", t.dim);
            return;
        }

        char title[32];
        std::snprintf(title, sizeof(title), "Kana %d/%d", _asked + 1, kRound);
        const bool typing = (_state == State::Typing);
        // After the answer Space is a key like any other, so its hint is shown while typing only.
        const char* script = !typing ? "" : _katakana ? "Space: あ" : "Space: ア";
        drawFrame(c, t, title, script, typing ? "Enter: answer" : "Any key: next",
                  typing ? "Tab: help" : _heard ? "/: again" : "");

        const std::string shown = _katakana ? kana::toKatakana(_prompt) : _prompt;
        const Face large        = fitFace(c, shown.c_str(), a.w - 4, 64);
        faceCentre(c, centre, a.y, shown.c_str(), large, t.ink);

        const bool showRomaji    = (s.romaji == RomajiMode::Always) || _peek;
        const std::string answer = kana::toRomaji(_prompt, !s.textbookN);
        const int lineY          = a.y + 66;

        if (typing) {
            std::string typed = _typed;
            typed.push_back('_');
            if (showRomaji) {
                // the help on the left, what is typed on the right of it
                const int width = textWidth(c, answer.c_str(), font24()) + 16 + textWidth(c, typed.c_str(), font24());
                int x           = centre - width / 2;
                x               = text(c, x, lineY, answer.c_str(), font24(), t.accent);
                text(c, x + 16, lineY, typed.c_str(), font24(), t.type);
            } else {
                textCentre(c, centre, lineY, typed.c_str(), font24(), t.type);
            }
            return;
        }

        const bool right = (_state == State::Right);
        std::string line = right ? "〇 " : "× ";
        line += answer;
        if (!right) {
            line += "  not ";
            line += _typed;
        }
        const lgfx::IFont* font = (textWidth(c, line.c_str(), font24()) <= a.w) ? font24() : font16();
        textCentre(c, centre, lineY + (font == font24() ? 0 : 4), line.c_str(), font, right ? t.good : t.bad);
    }

    void describe(std::string& json) const override
    {
        const char* state = (_state == State::Typing) ? "typing" : (_state == State::Right) ? "right"
                            : (_state == State::Wrong) ? "wrong" : "done";
        json += ",\"kana\":\"";
        json += _prompt;
        json += "\",\"script\":\"";
        json += _katakana ? "katakana" : "hiragana";
        json += "\",\"kanaState\":\"";
        json += state;
        json += "\",\"asked\":";
        json += std::to_string(_asked);
        json += ",\"correct\":";
        json += std::to_string(_correct);
        json += _heard ? ",\"heard\":true" : ",\"heard\":false";
    }

private:
    void pick(App& app)
    {
        // Widen the pool as the round goes well.
        int pool = kBasicCount;
        if (_correct >= 8) {
            pool += kVoicedCount;
        }
        if (_correct >= 14) {
            pool += kCombinedCount;
        }
        std::string chosen;
        for (int attempt = 0; attempt < 4; ++attempt) {
            const int index = static_cast<int>(app.platform().random() % static_cast<uint32_t>(pool));
            if (index < kBasicCount) {
                chosen = kBasic[index];
            } else if (index < kBasicCount + kVoicedCount) {
                chosen = kVoiced[index - kBasicCount];
            } else {
                chosen = kCombined[index - kBasicCount - kVoicedCount];
            }
            if (chosen != _prompt) {
                break;
            }
        }
        _prompt = chosen;
        _peek   = false;
        _heard  = false;
    }

    // Plays the clip of the kana, in the script that is shown. The kana sounds the same in
    // both scripts, so the other deck serves when the first has no such card.
    bool hear(App& app)
    {
        const deck::Deck* deck = deck::find(_katakana ? "katakana" : "hiragana");
        const deck::Item* item = itemWithPrompt(deck, _katakana ? kana::toKatakana(_prompt) : _prompt);
        if (!item) {
            deck = deck::find(_katakana ? "hiragana" : "katakana");
            item = itemWithPrompt(deck, _katakana ? _prompt : kana::toKatakana(_prompt));
        }
        return app.speak(deck, item);
    }

    void check(App& app)
    {
        romaji::Options options;
        options.nStyle      = app.settings().textbookN ? romaji::NStyle::Hepburn : romaji::NStyle::Ime;
        options.punctuation = false;
        const romaji::Result typed = romaji::convert(_typed, options, true);
        const bool right           = (typed.kana == _prompt);
        _state                     = right ? State::Right : State::Wrong;
        if (right) {
            ++_correct;
        }
        if (app.settings().sound) {
            app.platform().tone(right ? 1320 : 440, right ? 80 : 200);
        }
        _heard = hear(app);
    }

    void next(App& app)
    {
        ++_asked;
        _typed.clear();
        _heard = false;
        if (_asked >= kRound) {
            _state = State::Done;
            return;
        }
        _state = State::Typing;
        pick(app);
    }

    std::string _prompt;
    std::string _typed;
    State _state   = State::Typing;
    int _asked     = 0;
    int _correct   = 0;
    bool _katakana = false;
    bool _peek     = false;
    bool _heard    = false;  // the kana was played after the answer
};

}  // namespace

std::unique_ptr<Screen> makeKanaScreen()
{
    return std::unique_ptr<Screen>(new KanaScreen());
}

}  // namespace ui
