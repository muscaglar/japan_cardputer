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
constexpr int kLine             = 17;  // line height of the 16 px font

enum class State : uint8_t {
    Meet,    // a card never seen, with a note: prompt, reading, meaning and the note, to be read
    Copy,    // a card never seen: the answer is shown, the learner types it
    Asking,
    Marked,
    Note,    // the note of a marked card, asked for with Tab
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
            return "How do you say it?";
        default:
            return "How is it read?";
    }
}

const char* slipHint(match::Slip slip)
{
    switch (slip) {
        case match::Slip::LongVowel: return "Nearly: the long sound";
        case match::Slip::SmallTsu:  return "Nearly: the small っ";
        case match::Slip::N:         return "Nearly: the ん";
        case match::Slip::Voicing:   return "Nearly: か or が?";
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
        switch (_state) {
            case State::Meet:
                _state = State::Copy;
                return;
            case State::Note:
                next(app);
                return;
            case State::Marked:
                if (key.code == Key::Tab && _pick.item->note[0] != 0) {
                    _state = State::Note;
                } else {
                    next(app);
                }
                return;
            default:
                break;
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
                help(app);
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
            drawFrame(c, t, "Cards", "", "", "");
            return;
        }
        const deck::Item& item = *_pick.item;
        const Area a           = contentArea(t);
        const int centre       = a.x + a.w / 2;
        const bool fresh       = (_state == State::Meet || _state == State::Copy);
        const bool reads       = (_state == State::Meet || _state == State::Note);
        const bool romajiOn    = (s.romaji == RomajiMode::Always) || _peeked || _helped;
        const std::string reading = (_state == State::Marked) ? _outcome.expected : std::string(item.reading);

        // the line at the top: the meaning, the question, or the romaji when help was asked for
        std::string top;
        uint32_t topColour = headerInk(t);
        if (_state == State::Asking && !romajiOn) {
            top = question(item.kind);
        } else if (romajiOn && _state != State::Marked && !reads) {
            top       = kana::toRomaji(item.reading, !s.textbookN);
            topColour = headerAccent(t);
        } else {
            top = item.gloss;
        }
        char tag[24];
        if (fresh) {
            std::snprintf(tag, sizeof(tag), "new");
        } else {
            std::snprintf(tag, sizeof(tag), "%d left", _remaining + 1);
        }
        const int tagWidth = textWidth(c, tag, font16());
        const char* footerLeft  = "Any key: next";
        const char* footerRight = "";
        switch (_state) {
            case State::Meet:
                footerLeft = "Enter: go on";
                break;
            case State::Copy:
                footerLeft  = "Type it + Enter";
                footerRight = (s.romaji == RomajiMode::Never || romajiOn) ? "" : "Tab: help";
                break;
            case State::Asking:
                footerLeft  = "Enter: answer";
                footerRight = romajiOn ? "Tab: show" : "Tab: help";
                break;
            case State::Marked:
                footerRight = (item.note[0] != 0) ? "Tab: note" : "";
                break;
            default:
                break;
        }
        const std::string fitted = headThatFits(c, top, font16(), a.w - tagWidth - 14);
        drawFrame(c, t, "", tag, footerLeft, footerRight);
        text(c, t.id == ThemeId::Rpg ? a.x + 4 : a.x, 1, fitted.c_str(), font16(), topColour);
        if (t.id == ThemeId::Rpg) {
            // the frame of the game look is interrupted where the line at the top stands
            c.fillRect(a.x, 9, textWidth(c, fitted.c_str(), font16()) + 8, 3, t.bg);
            text(c, a.x + 4, 1, fitted.c_str(), font16(), topColour);
        }

        // the prompt; a page with a note of two lines has room for a smaller one only
        int noteLines = 0;
        if (reads) {
            noteLines = linesNeeded(c, a.w - 4, item.note, font16());
            if (noteLines > 2) {
                noteLines = 2;
            }
        }
        const int tallest = (noteLines == 2) ? 24 : 32;
        const Face large  = fitFace(c, item.prompt, a.w - 4, tallest);
        const bool tight  = (a.h < 92);  // the game look has the lowest window
        int y             = a.y + (tight ? 0 : 1);
        faceCentre(c, centre, y, item.prompt, large, t.ink);
        y += large.height;

        if (_state == State::Asking) {
            drawTyped(c, t, s, item, a, y + 14);
            return;
        }

        // the reading, with its mark after an answer and its pitch line where the accent is known
        y += tight ? 5 : 6;
        const lgfx::IFont* font = (textWidth(c, reading.c_str(), font24()) + 30 <= a.w) ? font24() : font16();
        std::string mark;
        uint32_t markColour = t.ink;
        if (_state == State::Marked || _state == State::Note) {
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
        const std::string shownReading = tailThatFits(c, reading, font, a.w - 30);
        const int markWidth = mark.empty() ? 0 : textWidth(c, mark.c_str(), font) + 4;
        const int width     = markWidth + textWidth(c, shownReading.c_str(), font);
        int x               = centre - width / 2;
        if (!mark.empty()) {
            text(c, x, y, mark.c_str(), font, markColour);
            x += markWidth;
        }
        PitchStyle style;
        style.font        = font;
        style.ink         = t.ink;
        style.line        = t.accent;
        style.particleInk = t.dim;
        // The accent belongs to the main reading. Another accepted answer is drawn without.
        const bool mainReading = (reading == item.reading) && (shownReading == reading);
        pitchText(c, x, y, shownReading, mainReading ? item.accent : -1, style);
        y += (font == font24() ? 24 : 16) + (tight ? 1 : 3);

        if (_state == State::Copy) {
            drawTyped(c, t, s, item, a, y);
            return;
        }
        if (reads) {
            textWrapped(c, a.x + 2, y, a.w - 4, item.note, font16(), t.ink, kLine, 2);
            return;
        }

        // marked: one line about the answer
        std::string message;
        uint32_t colour = t.dim;
        if (_gaveUp) {
            message = "";
        } else if (_outcome.verdict == match::Verdict::Almost) {
            message = slipHint(_outcome.slip);
            colour  = t.wait;
        } else if (_outcome.verdict == match::Verdict::Wrong) {
            message = "You typed " + _answered;
        } else if (_praise) {
            message = std::string(_praise->ja) + "  " + _praise->en;
            if (textWidth(c, message.c_str(), font16()) > a.w - 4) {
                message = _praise->en;
            }
        }
        if (!message.empty()) {
            const std::string line = headThatFits(c, message, font16(), a.w - 4);
            textCentre(c, centre, y + 2, line.c_str(), font16(), colour);
        }
    }

    void describe(std::string& json) const override
    {
        if (!_pick.item) {
            return;
        }
        const char* state = "asking";
        switch (_state) {
            case State::Meet:   state = "meet"; break;
            case State::Copy:   state = "copy"; break;
            case State::Marked: state = "marked"; break;
            case State::Note:   state = "note"; break;
            default:            break;
        }
        const char* verdict = "none";
        if (_state == State::Marked || _state == State::Note) {
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
        json += ",\"romajiShown\":";
        json += (_romajiShown ? "true" : "false");
        json += ",\"left\":";
        json += std::to_string(_remaining);
    }

private:
    // What is being typed, as kana, with the letters not yet decided in another colour.
    void drawTyped(Canvas& c, const Theme& t, const Settings& s, const deck::Item& item, const Area& a, int y)
    {
        romaji::Options options;
        options.nStyle      = s.textbookN ? romaji::NStyle::Hepburn : romaji::NStyle::Ime;
        options.punctuation = false;
        const romaji::Result live   = romaji::convert(_typed, options, false);
        const std::string kanaSoFar = startsWithKatakana(item.reading) ? kana::toKatakana(live.kana) : live.kana;
        const std::string whole     = kanaSoFar + live.pending + "_";
        const lgfx::IFont* font     = (textWidth(c, whole.c_str(), font24()) <= a.w - 8) ? font24() : font16();
        const int room              = a.w - 8 - textWidth(c, (live.pending + "_").c_str(), font);
        const std::string shown     = tailThatFits(c, kanaSoFar, font, room);
        const int width = textWidth(c, shown.c_str(), font) + textWidth(c, (live.pending + "_").c_str(), font);
        int x           = a.x + a.w / 2 - width / 2;
        x               = text(c, x, y, shown.c_str(), font, t.type);
        x               = text(c, x, y, live.pending.c_str(), font, t.wait);
        text(c, x, y, "_", font, t.type);
        if (_tries > 0 && _state == State::Copy) {
            const int under = y + (font == font24() ? 25 : 17);
            if (under + 16 <= a.y + a.h) {
                textCentre(c, a.x + a.w / 2, under, "Look again, then type", font16(), t.wait);
            }
        }
    }

    void next(App& app)
    {
        _typed.clear();
        _answered.clear();
        _peeked    = false;
        _helped    = false;
        _gaveUp    = false;
        _praise    = nullptr;
        _tries     = 0;
        _romajiShown = false;
        if (!app.queue().next(_pick)) {
            _pick = session::Pick();
            app.endSitting();
            app.show(ScreenId::Summary);
            return;
        }
        _remaining = app.queue().remaining();
        if (_pick.isNew) {
            ++app.sitting().introduced;
            _state = (_pick.item->note[0] != 0) ? State::Meet : State::Copy;
        } else {
            _state = State::Asking;
        }
        _romajiShown = (app.settings().romaji == RomajiMode::Always);
    }

    void leave(App& app)
    {
        _pick = session::Pick();
        app.endSitting();
        app.show(app.sitting().asked > 0 ? ScreenId::Summary : ScreenId::Home);
    }

    // Tab: first the romaji, then, on a question, the answer itself.
    void help(App& app)
    {
        const bool romajiAllowed = (app.settings().romaji != RomajiMode::Never);
        const bool romajiOn      = (app.settings().romaji == RomajiMode::Always) || _peeked || _helped;
        if (romajiAllowed && !romajiOn) {
            _peeked    = true;
            _romajiShown = true;
            return;
        }
        if (_state == State::Asking) {
            giveUp(app);
        }
    }

    void record(App& app, srs::Grade grade)
    {
        app.queue().answered(_pick, grade);
        Sitting& sitting = app.sitting();
        sitting.asked    = app.queue().asked();
        sitting.right    = app.queue().right();
        ++app.settings().answeredToday;
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

        if (_state == State::Copy) {
            // Copying what is shown is practice, not a test: wrong tries cost nothing.
            if (_outcome.verdict != match::Verdict::Right) {
                ++_tries;
                if (_tries >= kTriesBeforeHelp && app.settings().romaji != RomajiMode::Never) {
                    _helped    = true;
                    _romajiShown = true;
                }
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
            _praise = buddy::say(_streak >= 5 ? "streak" : "right", app.platform().random());
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
    const deck::BuddyLine* _praise = nullptr;
    State _state    = State::Asking;
    int _remaining  = 0;
    int _tries      = 0;
    int _streak     = 0;
    bool _peeked    = false;  // asked for the romaji before answering
    bool _helped    = false;  // the romaji is shown because copying failed twice
    bool _gaveUp    = false;
    bool _romajiShown = false;  // the romaji is on the screen now
};

class SummaryScreen : public Screen {
public:
    void enter(App& app) override
    {
        _line = buddy::say("finish", app.platform().random());
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
        drawFrame(c, t, "Done", "", "Enter: again", "Any key: home");
        const Area a     = contentArea(t);
        const int centre = a.x + a.w / 2;

        char score[32];
        std::snprintf(score, sizeof(score), "%d of %d right", sitting.right, sitting.asked);
        textCentre(c, centre, a.y + 2, score, font24(), t.good);

        char more[48];
        std::snprintf(more, sizeof(more), "%d new   %d to repeat", sitting.introduced, app.dueToday());
        textCentre(c, centre, a.y + 30, more, font16(), t.ink);

        if (_line) {
            textCentre(c, centre, a.y + 52, _line->ja, font16(), t.ink);
            const std::string english = headThatFits(c, _line->en, font16(), a.w - 4);
            textCentre(c, centre, a.y + 52 + kLine, english.c_str(), font16(), t.dim);
        }
    }

private:
    const deck::BuddyLine* _line = nullptr;
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
