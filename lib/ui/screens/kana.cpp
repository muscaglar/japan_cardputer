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
            next(app);
            return;
        }
        switch (key.code) {
            case Key::Tab:
                _katakana = !_katakana;
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
                if (key.fn && (key.ch == 'r' || key.ch == 'R')) {
                    _peek = !_peek;
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
        char right[32];
        std::snprintf(right, sizeof(right), "%s %d/%d", _katakana ? "カタカナ" : "ひらがな",
                      _asked + (_state == State::Done ? 0 : 1), kRound);

        if (_state == State::Done) {
            drawFrame(c, t, "かな", "おわり", "Enter もういちど", "");
            if (t.id == ThemeId::Rpg) {
                daruma(c, 22, 114, true);
            }
            const Area a = contentArea(t);
            textCentre(c, a.x + a.w / 2, a.y + 6, "おつかれさま！", font16(), t.ink);
            char score[32];
            std::snprintf(score, sizeof(score), "%d / %d", _correct, kRound);
            textCentre(c, a.x + a.w / 2, a.y + 28, score, font24(), t.good);
            drawMessage(c, t, _correct == kRound ? "ぜんぶ せいかい！" : "もういちど やって みよう。", t.dim);
            return;
        }

        const char* footer = (_state == State::Typing) ? "Enter こたえる" : "キーで つぎへ";
        drawFrame(c, t, "かな", right, footer, _state == State::Typing ? "Tab きりかえ" : "");
        if (t.id == ThemeId::Rpg) {
            daruma(c, 22, 114, true);
        }

        const Area a              = contentArea(t);
        const std::string shown   = _katakana ? kana::toKatakana(_prompt) : _prompt;
        const int centre          = a.x + a.w / 2;
        const int bigTop          = a.y + ((t.id == ThemeId::Rpg) ? 0 : 4);
        textCentre(c, centre, bigTop, shown.c_str(), fontBig(), t.ink);

        const bool showRomaji = (s.romaji == RomajiMode::Always) || (_peek && s.romaji != RomajiMode::Never) ||
                                _state != State::Typing;
        const std::string answer = kana::toRomaji(_prompt, !s.textbookN);
        const int lineY          = bigTop + 38;

        if (_state == State::Typing) {
            std::string typed = _typed;
            typed.push_back('_');
            textCentre(c, centre, lineY, typed.c_str(), font16(), t.type);
            if (showRomaji) {
                drawMessage(c, t, answer.c_str(), t.dim);
            } else if (s.romaji == RomajiMode::Peek) {
                drawMessage(c, t, "Fn+R ローマじ", t.faint);
            }
            return;
        }

        const bool right_ = (_state == State::Right);
        std::string line  = right_ ? "〇 " : "× ";
        line += answer;
        textCentre(c, centre, lineY, line.c_str(), font16(), right_ ? t.good : t.bad);
        if (right_) {
            drawMessage(c, t, "せいかい！", t.good);
        } else {
            std::string said = "you typed ";
            said += _typed;
            drawMessage(c, t, said.c_str(), t.dim);
        }
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
    }

    void next(App& app)
    {
        ++_asked;
        _typed.clear();
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
};

}  // namespace

std::unique_ptr<Screen> makeKanaScreen()
{
    return std::unique_ptr<Screen>(new KanaScreen());
}

}  // namespace ui
