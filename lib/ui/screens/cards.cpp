// A sitting: one card after the other, typed answers, marked at once.
#include <cstdio>
#include <string>

#include "../screens.h"
#include "../widgets.h"
#include "buddy.h"
#include "kana.h"
#include "match.h"
#include "romaji.h"

namespace ui {

namespace {

constexpr size_t kLongestAnswer = 48;  // letters
constexpr int kTriesBeforeHelp  = 2;   // wrong tries on a new card before the romaji is shown

enum class State : uint8_t {
    Introduce,  // a card never seen: the answer is shown, the learner types it
    Asking,
    Marked,
};

bool startsWithKatakana(const char* utf8)
{
    const unsigned char* p = reinterpret_cast<const unsigned char*>(utf8);
    if (p[0] != 0xE3 || p[1] == 0 || p[2] == 0) {
        return false;
    }
    const uint32_t code = ((p[0] & 0x0Fu) << 12) | ((p[1] & 0x3Fu) << 6) | (p[2] & 0x3Fu);
    return code >= 0x30A1 && code <= 0x30FC;
}

// The end of `text` that fits into `width`, with a mark in front when the start was cut off.
std::string tailThatFits(Canvas& c, const std::string& text, const lgfx::IFont* font, int width)
{
    if (textWidth(c, text.c_str(), font) <= width) {
        return text;
    }
    const std::vector<std::string> beats = kana::beats(text);
    std::string tail;
    for (size_t i = beats.size(); i > 0; --i) {
        const std::string longer = beats[i - 1] + tail;
        if (textWidth(c, ("…" + longer).c_str(), font) > width) {
            break;
        }
        tail = longer;
    }
    return "…" + tail;
}

const char* question(deck::Kind kind)
{
    switch (kind) {
        case deck::Kind::Counter:
        case deck::Kind::Number:
            return "なんと いう？";
        default:
            return "よみかたは？";
    }
}

const char* slipHint(match::Slip slip)
{
    switch (slip) {
        case match::Slip::LongVowel: return "のばす おと long sound";
        case match::Slip::SmallTsu:  return "ちいさい っ small tsu";
        case match::Slip::N:         return "ん を わすれずに";
        case match::Slip::Voicing:   return "てんてん ゛ に ちゅうい";
        default:                     return "";
    }
}

class CardsScreen : public Screen {
public:
    void enter(App& app) override
    {
        _streak = 0;
        next(app);
    }

    void key(App& app, const Key& key) override
    {
        if (!_pick.item) {
            app.show(ScreenId::Home);
            return;
        }
        if (key.code == Key::Escape) {
            leave(app);
            return;
        }
        if (_state == State::Marked) {
            next(app);
            return;
        }
        switch (key.code) {
            case Key::Backspace:
                if (!_typed.empty()) {
                    _typed.pop_back();
                }
                break;
            case Key::Enter:
                if (!_typed.empty()) {
                    answer(app);
                }
                break;
            case Key::Tab:
                giveUp(app);
                break;
            case Key::Char:
                if (key.fn && (key.ch == 'r' || key.ch == 'R')) {
                    if (app.settings().romaji != RomajiMode::Never) {
                        _peeked = true;
                    }
                } else if (key.ch >= ' ' && key.ch < 127 && _typed.size() < kLongestAnswer) {
                    if (!(key.ch == ' ' && _typed.empty())) {
                        _typed.push_back(key.ch);
                    }
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
        if (!_pick.item) {
            drawFrame(c, t, "カード", "", "", "");
            return;
        }
        const deck::Item& item = *_pick.item;

        char right[32];
        if (_state == State::Introduce) {
            std::snprintf(right, sizeof(right), "あたらしい");
        } else {
            std::snprintf(right, sizeof(right), "あと %d", app.queue().remaining() + 1);
        }
        const char* footerLeft = (_state == State::Marked)      ? "キーで つぎへ"
                                 : (_state == State::Introduce) ? "よんで、うって、Enter"
                                                                : "Enter こたえる";
        const char* footerRight = (_state == State::Marked) ? "" : (_state == State::Introduce ? "" : "Tab みる");
        drawFrame(c, t, _pick.deck ? _pick.deck->nameJa : "カード", right, footerLeft, footerRight);
        if (t.id == ThemeId::Rpg) {
            daruma(c, 22, 114, true);
        }

        const Area a     = contentArea(t);
        const int centre = a.x + a.w / 2;
        const bool roomy = (t.id == ThemeId::Techo);
        int y            = a.y + 1;

        // the prompt
        const lgfx::IFont* promptFont = fitFont(c, item.prompt, a.w - 4, roomy ? 32 : 24);
        textCentre(c, centre, y, item.prompt, promptFont, t.ink);
        c.setFont(promptFont);
        y += c.fontHeight() + 6;  // room for the pitch line above the reading

        const bool showReading = (_state != State::Asking);
        const bool showRomaji  = showReading ? (s.romaji == RomajiMode::Always || _peeked || _helped)
                                             : (_peeked && s.romaji != RomajiMode::Never);
        const std::string reading = (_state == State::Marked) ? _outcome.expected : std::string(item.reading);

        if (showReading) {
            const lgfx::IFont* font = (textWidth(c, reading.c_str(), font16()) + 24 <= a.w) ? font16() : font12();
            const bool small        = (font == font12());
            std::string mark;
            uint32_t markColour = t.ink;
            if (_state == State::Marked) {
                if (_gaveUp) {
                    mark       = "→";
                    markColour = t.dim;
                } else if (_outcome.verdict == match::Verdict::Right) {
                    mark       = "〇";
                    markColour = t.good;
                } else if (_outcome.verdict == match::Verdict::Almost) {
                    mark       = "△";
                    markColour = t.wait;
                } else {
                    mark       = "×";
                    markColour = t.bad;
                }
            }
            const int markWidth = mark.empty() ? 0 : textWidth(c, mark.c_str(), font) + 4;
            const int width     = markWidth + textWidth(c, reading.c_str(), font);
            int x               = centre - width / 2;
            if (!mark.empty()) {
                text(c, x, y + 1, mark.c_str(), font, markColour);
                x += markWidth;
            }
            PitchStyle style;
            style.font        = font;
            style.ink         = t.ink;
            style.line        = t.accent;
            style.particleInk = t.dim;
            // The accent belongs to the main reading. Another accepted answer is drawn without.
            const bool mainReading = (reading == item.reading);
            pitchText(c, x, y + 1, reading, mainReading ? item.accent : -1, style);
            y += (small ? 13 : 17) + 1;

            if (t.id != ThemeId::Rpg) {
                textCentre(c, centre, y, item.gloss, font12(), t.dim);
                y += 13;
            }
        }

        // what is being typed
        if (_state != State::Marked) {
            romaji::Options options;
            options.nStyle      = s.textbookN ? romaji::NStyle::Hepburn : romaji::NStyle::Ime;
            options.punctuation = false;
            const romaji::Result live = romaji::convert(_typed, options, false);
            const std::string kanaSoFar =
                startsWithKatakana(item.reading) ? kana::toKatakana(live.kana) : live.kana;
            const lgfx::IFont* font = font16();
            const std::string shown = tailThatFits(c, kanaSoFar, font, a.w - 40);
            const int width         = textWidth(c, shown.c_str(), font) + textWidth(c, live.pending.c_str(), font) +
                                      textWidth(c, "_", font);
            int x                   = centre - width / 2;
            x                       = text(c, x, y, shown.c_str(), font, t.type);
            x                       = text(c, x, y, live.pending.c_str(), font, t.wait);
            text(c, x, y, "_", font, t.type);
        }

        // one line of help or comment
        std::string message;
        uint32_t messageColour = t.dim;
        if (_state == State::Marked) {
            const deck::BuddyLine* line = nullptr;
            if (t.id == ThemeId::Rpg) {
                // in the game look the buddy speaks, and the meaning has its place above
                textCentre(c, centre, a.y + a.h - 14, item.gloss, font12(), t.dim);
                const char* mood = _gaveUp ? "wrong"
                                   : _outcome.verdict == match::Verdict::Right ? (_streak >= 5 ? "streak" : "right")
                                   : _outcome.verdict == match::Verdict::Almost ? "almost" : "wrong";
                line = buddy::say(mood, _said);
            }
            if (line) {
                message       = line->ja;
                messageColour = t.ink;
            } else if (_outcome.verdict == match::Verdict::Almost && !_gaveUp) {
                message = slipHint(_outcome.slip);
            } else if (_outcome.verdict == match::Verdict::Wrong && !_gaveUp && !_answered.empty()) {
                message = "うった: " + _answered;  // what was typed, to compare
            } else if (item.note[0] != 0) {
                message = item.note;
            }
            if (showRomaji && t.id != ThemeId::Rpg && message.empty()) {
                message = kana::toRomaji(reading, !s.textbookN);
            }
        } else if (showRomaji) {
            message       = kana::toRomaji(item.reading, !s.textbookN);
            messageColour = t.accent;
        } else if (_state == State::Introduce) {
            // the footer says what to do; this line speaks up only after a slip
            message = _tries > 0 ? "もういちど。よく みて。" : "";
            if (t.id == ThemeId::Rpg && _tries == 0) {
                message = item.gloss;
            }
        } else {
            message = question(item.kind);
        }
        if (!message.empty()) {
            const std::string fitted = tailThatFits(c, message, font12(), t.id == ThemeId::Rpg ? 186 : a.w - 4);
            drawMessage(c, t, fitted.c_str(), messageColour);
        }
    }

    void describe(std::string& json) const override
    {
        if (!_pick.item) {
            return;
        }
        const char* state   = (_state == State::Introduce) ? "introduce" : (_state == State::Asking) ? "asking" : "marked";
        const char* verdict = "none";
        if (_state == State::Marked) {
            verdict = _gaveUp ? "shown"
                      : _outcome.verdict == match::Verdict::Right ? "right"
                      : _outcome.verdict == match::Verdict::Almost ? "almost" : "wrong";
        }
        json += ",\"card\":\"";
        json += _pick.item->id;
        json += "\",\"cardState\":\"";
        json += state;
        json += "\",\"verdict\":\"";
        json += verdict;
        json += "\",\"repeat\":";
        json += _pick.repeat ? "true" : "false";
        json += ",\"left\":";
        json += std::to_string(_remaining);
    }

private:
    void next(App& app)
    {
        _typed.clear();
        _peeked = false;
        _helped = false;
        _gaveUp = false;
        _tries  = 0;
        if (!app.queue().next(_pick)) {
            _pick = session::Pick();
            app.endSitting();
            app.show(ScreenId::Summary);
            return;
        }
        _state     = _pick.isNew ? State::Introduce : State::Asking;
        _remaining = app.queue().remaining();
        if (_pick.isNew) {
            ++app.sitting().introduced;
        }
    }

    void leave(App& app)
    {
        _pick = session::Pick();
        app.endSitting();
        app.show(app.sitting().asked > 0 ? ScreenId::Summary : ScreenId::Home);
    }

    void record(App& app, srs::Grade grade)
    {
        app.queue().answered(_pick, grade);
        Sitting& sitting = app.sitting();
        sitting.asked    = app.queue().asked();
        sitting.right    = app.queue().right();
        ++app.settings().answeredToday;
        _said = app.platform().random();
        if (app.settings().sound) {
            const bool good = (grade != srs::Grade::Again);
            app.platform().tone(good ? 1320 : 440, good ? 80 : 200);
        }
    }

    void answer(App& app)
    {
        romaji::Options options;
        options.nStyle      = app.settings().textbookN ? romaji::NStyle::Hepburn : romaji::NStyle::Ime;
        options.punctuation = false;
        const std::string typed = romaji::convert(_typed, options, true).kana;
        _outcome                = match::check(typed, *_pick.item);
        _answered               = startsWithKatakana(_pick.item->reading) ? kana::toKatakana(typed) : typed;

        if (_state == State::Introduce) {
            // Copying what is shown is practice, not a test: wrong tries cost nothing.
            if (_outcome.verdict != match::Verdict::Right) {
                ++_tries;
                _helped = (_tries >= kTriesBeforeHelp) && app.settings().romaji != RomajiMode::Never;
                _typed.clear();
                return;
            }
            record(app, srs::Grade::Good);
            next(app);
            return;
        }

        srs::Grade grade = srs::Grade::Again;
        if (_outcome.verdict == match::Verdict::Right) {
            grade = _peeked ? srs::Grade::Hard : srs::Grade::Good;
            ++_streak;
        } else {
            if (_outcome.verdict == match::Verdict::Almost && _outcome.sameSound) {
                grade = srs::Grade::Hard;
            }
            _streak = 0;
        }
        record(app, grade);
        _state = State::Marked;
    }

    void giveUp(App& app)
    {
        if (_state == State::Introduce) {
            return;
        }
        _outcome          = match::Outcome();
        _outcome.expected = _pick.item->reading;
        _gaveUp           = true;
        _streak           = 0;
        record(app, srs::Grade::Again);
        _state = State::Marked;
    }

    session::Pick _pick;
    match::Outcome _outcome;
    std::string _typed;
    std::string _answered;  // the last answer as kana
    State _state   = State::Asking;
    uint32_t _said = 0;
    int _remaining = 0;
    int _tries     = 0;
    int _streak    = 0;
    bool _peeked   = false;  // asked for the romaji before answering
    bool _helped   = false;  // the romaji is shown because copying failed twice
    bool _gaveUp   = false;
};

class SummaryScreen : public Screen {
public:
    void enter(App& app) override
    {
        const deck::BuddyLine* line = buddy::say("finish", app.platform().random());
        _line                       = line ? line->ja : "おつかれさま！";
    }

    void key(App& app, const Key& key) override
    {
        if (key.code == Key::Enter && (app.dueToday() > 0 || app.newAvailable() > 0)) {
            app.startSitting(app.sitting().deck);
        } else {
            app.show(ScreenId::Home);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t         = app.theme();
        const Sitting& sitting = app.sitting();
        drawFrame(c, t, "おわり", "", "Enter もういちど", "キーで ホーム");
        const Area a     = contentArea(t);
        const int centre = a.x + a.w / 2;

        if (t.id == ThemeId::Rpg) {
            daruma(c, 22, 114, true);
            text(c, 42, 101, _line, font12(), t.ink);
        } else {
            textCentre(c, centre, a.y + 2, _line, font16(), t.ink);
        }
        const int top = a.y + (t.id == ThemeId::Rpg ? 4 : 24);

        char score[24];
        std::snprintf(score, sizeof(score), "%d / %d", sitting.right, sitting.asked);
        textCentre(c, centre - 40, top, score, font24(), t.good);
        text(c, centre - 40 - textWidth(c, score, font24()) / 2, top + 26, "せいかい right", font12(), t.dim);

        char fresh[40];
        std::snprintf(fresh, sizeof(fresh), "あたらしい %d", sitting.introduced);
        text(c, centre + 14, top + 2, fresh, font12(), t.ink);
        char later[40];
        std::snprintf(later, sizeof(later), "のこり %d", app.dueToday());
        text(c, centre + 14, top + 16, later, font12(), t.ink);

        if (sitting.asked > 0 && sitting.right == sitting.asked) {
            stamp(c, a.x + a.w - 18, a.y + a.h - 20, "済", t.bad, t.bg);
        }
    }

private:
    const char* _line = "";
};

}  // namespace

std::unique_ptr<Screen> makeCardsScreen()
{
    return std::unique_ptr<Screen>(new CardsScreen());
}

std::unique_ptr<Screen> makeSummaryScreen()
{
    return std::unique_ptr<Screen>(new SummaryScreen());
}

}  // namespace ui
