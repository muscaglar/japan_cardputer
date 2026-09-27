// A sitting: one card after the other, typed answers, marked at once.
//
// A word card has its prompt in the middle, the reading under it and one or two lines of text
// under that. A kana card has the kana on the left, as large as fits, and beside it what to type
// and what there is to say about it.
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"
#include "buddy.h"
#include "kana.h"
#include "match.h"
#include "romaji.h"

namespace ui {

namespace {

constexpr size_t kLongestAnswer = 48;   // letters
constexpr int kTriesBeforeHelp  = 2;    // wrong tries on a new card before the romaji is shown
constexpr int kLine             = 17;   // line height of the 16 px font
constexpr size_t kLinesOnPage   = 2;    // lines of text under prompt and reading, in every look
constexpr size_t kLinesByKana   = 3;    // lines of text beside a kana, under what to type
constexpr int kWidestKana       = 100;  // a pair of kana is drawn at 48 px, so that text fits beside it
constexpr int kGapByKana        = 10;
constexpr int kMarkRoom         = 30;   // kept free beside a reading, so that its mark does not move it

enum class State : uint8_t {
    Probe,   // a kana never seen is asked first: known at first sight, it is not taught
    Meet,    // a card never seen that has something to say: its pages, to be read
    Copy,    // a card never seen: the answer is shown, the learner types it
    Asking,
    Marked,
    Note,    // the pages of a marked card, asked for with Tab
};

// What one page says under the reading: lines of the kanji meanings, then lines of the note.
struct Page {
    uint8_t partsFrom  = 0;
    uint8_t partsCount = 0;
    uint8_t noteFrom   = 0;
    uint8_t noteCount  = 0;

    size_t lines() const { return static_cast<size_t>(partsCount) + noteCount; }
};

// Where the text beside a kana stands.
struct Column {
    Face face;  // of the kana
    int kanaX;
    int x;
    int width;
    int top;
};

// The character that starts at `utf8`, and how many bytes it takes.
uint32_t codeAt(const char* utf8, size_t& bytes)
{
    const unsigned char* p = reinterpret_cast<const unsigned char*>(utf8);
    uint32_t code          = p[0];
    size_t extra           = 0;
    if ((code & 0xE0) == 0xC0) {
        code &= 0x1F;
        extra = 1;
    } else if ((code & 0xF0) == 0xE0) {
        code &= 0x0F;
        extra = 2;
    } else if ((code & 0xF8) == 0xF0) {
        code &= 0x07;
        extra = 3;
    }
    bytes = 1;
    while (extra-- > 0 && (p[bytes] & 0xC0) == 0x80) {
        code = (code << 6) | (p[bytes] & 0x3Fu);
        ++bytes;
    }
    return code;
}

// As textWidth(), but without a canvas: the pages of a card are laid out when a key arrives,
// and there is nothing to draw on then.
int widthOf(const std::string& utf8, const lgfx::IFont* font)
{
    lgfx::FontMetrics metrics;
    font->getDefaultMetric(&metrics);
    int width = 0;
    size_t at = 0;
    while (at < utf8.size()) {
        size_t bytes        = 1;
        const uint32_t code = codeAt(utf8.c_str() + at, bytes);
        at += bytes;
        if (code > 0xFFFF || !font->updateFontMetric(&metrics, static_cast<uint16_t>(code))) {
            font->updateFontMetric(&metrics, 0);
        }
        width += metrics.x_advance;
    }
    return width;
}

// As fitFace(), without a canvas.
Face faceFor(const char* utf8, int width, int tallest)
{
    const Face choices[] = {
        {fontBig(), 2, 64}, {font24(), 2, 48}, {fontBig(), 1, 32}, {font16(), 2, 32}, {font24(), 1, 24},
    };
    for (const Face& choice : choices) {
        if (choice.height <= tallest && hasGlyphs(choice.font, utf8) &&
            widthOf(utf8, choice.font) * choice.scale <= width) {
            return choice;
        }
    }
    return face16();
}

std::vector<std::string> split(const char* text, const std::string& separator)
{
    std::vector<std::string> pieces;
    const std::string all = text ? text : "";
    size_t from           = 0;
    while (from <= all.size()) {
        size_t to = all.find(separator, from);
        if (to == std::string::npos) {
            to = all.size();
        }
        if (to > from) {
            pieces.push_back(all.substr(from, to - from));
        }
        from = to + separator.size();
    }
    return pieces;
}

// Lines of at most `width` pixels in the 16 px font, broken only between the pieces.
std::vector<std::string> linesOf(const std::vector<std::string>& pieces, const std::string& separator, int width)
{
    std::vector<std::string> lines;
    std::string line;
    for (const std::string& piece : pieces) {
        const std::string longer = line.empty() ? piece : line + separator + piece;
        if (!line.empty() && widthOf(longer, font16()) > width) {
            lines.push_back(line);
            line = piece;
        } else {
            line = longer;
        }
    }
    if (!line.empty()) {
        lines.push_back(line);
    }
    return lines;
}

bool clings(const std::string& beat)
{
    return beat == "ん" || beat == "ン" || beat == "っ" || beat == "ッ" || beat == "ー";
}

// The reading as it is drawn in a content area `room` pixels wide: in one line at 24 px, or at
// 16 px where that is too wide, or in two lines where even that is. It is broken at the beat
// nearest the middle, and never before ん, っ or ー, which belong to what they follow.
std::vector<std::string> readingLines(const std::string& reading, int room)
{
    std::vector<std::string> lines;
    const std::vector<std::string> beats = kana::beats(reading);
    if (widthOf(reading, font16()) + kMarkRoom <= room || beats.size() < 2) {
        lines.push_back(reading);
        return lines;
    }
    size_t at = (beats.size() + 1) / 2;
    while (at + 1 < beats.size() && clings(beats[at])) {
        ++at;
    }
    std::string first;
    std::string second;
    for (size_t i = 0; i < beats.size(); ++i) {
        (i < at ? first : second) += beats[i];
    }
    lines.push_back(first);
    lines.push_back(second);
    return lines;
}

Column columnOf(const Area& a, const deck::Item& item)
{
    Column column;
    column.face  = faceFor(item.prompt, kWidestKana, 64);
    column.kanaX = a.x + 4;
    column.x     = column.kanaX + widthOf(item.prompt, column.face.font) * column.face.scale + kGapByKana;
    column.width = a.x + a.w - 2 - column.x;
    column.top   = a.y + (a.h < 92 ? 2 : 6);  // the game look has the lowest window
    return column;
}

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
        case deck::Kind::Kana:
            return "What sound is it?";
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
        _app    = &app;
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
        _spoken = false;
        _tone   = 0;
        press(app, key);
        // A clip says more than a tone does, and the two would sound at once.
        if (_tone != 0 && !_spoken && app.settings().sound) {
            app.platform().tone(_tone, _tone > 1000 ? 80 : 200);
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
        const bool kanaCard    = (item.kind == deck::Kind::Kana);
        const bool fresh       = (_state == State::Meet || _state == State::Copy);
        const bool romajiOn    = (s.romaji == RomajiMode::Always) || _peeked || _helped;
        const bool hears       = canHear(app);

        // the line at the top: the meaning, the question, or the romaji when help was asked for
        std::string top;
        uint32_t topColour = headerInk(t);
        if (_state == State::Probe) {
            top = "Do you know it?";
        } else if (_state == State::Asking && !romajiOn) {
            top = question(item.kind);
        } else if (romajiOn && (_state == State::Asking || (_state == State::Copy && !kanaCard))) {
            top       = kanaCard ? std::string(item.gloss) : kana::toRomaji(item.reading, !s.textbookN);
            topColour = headerAccent(t);
        } else if (_state == State::Copy && _tries > 0 && !kanaCard) {
            top       = "Look again, then type";  // under the line a word leaves no room for it
            topColour = headerAccent(t);
        } else if (kanaCard) {
            top = capitalised(_pick.deck ? _pick.deck->nameEn : "kana");  // what is typed stands beside the kana
        } else {
            top = item.gloss;
        }
        char tag[24];
        if (_state == State::Meet && _pages.size() > 1) {
            std::snprintf(tag, sizeof(tag), "new %d/%d", static_cast<int>(_page) + 1, static_cast<int>(_pages.size()));
        } else if (fresh) {
            std::snprintf(tag, sizeof(tag), "new");
        } else {
            std::snprintf(tag, sizeof(tag), "%d left", _remaining + 1);
        }

        const char* footerLeft  = "Any key: next";
        const char* footerRight = hears ? "/: hear" : "";
        switch (_state) {
            case State::Probe:
                footerLeft  = "Enter: answer";
                footerRight = "Tab: no";
                break;
            case State::Meet:
                footerLeft = lastPage() ? "Enter: go on" : "Enter: more";
                break;
            case State::Copy:
                footerLeft = "Type it + Enter";
                if (!kanaCard && s.romaji != RomajiMode::Never && !romajiOn) {
                    footerRight = "Tab: help";
                }
                break;
            case State::Asking:
                footerLeft  = "Enter: answer";
                footerRight = (romajiOn || s.romaji == RomajiMode::Never) ? "Tab: show" : "Tab: help";
                break;
            case State::Marked:
                if (!_pages.empty()) {
                    footerRight = turnHint(_pages[0], nullptr);
                }
                break;
            case State::Note:
                if (!lastPage()) {
                    footerRight = turnHint(_pages[_page + 1], &_pages[_page]);
                }
                break;
        }

        // The meaning matters more than the count: where both do not fit, the count gives way.
        int room = a.w - textWidth(c, tag, font16()) - 14;
        if (textWidth(c, top.c_str(), font16()) > room) {
            tag[0] = 0;
            room   = a.w - 8;
        }
        const std::string fitted = headThatFits(c, top, font16(), room);
        drawFrame(c, t, "", tag, footerLeft, footerRight);
        text(c, t.id == ThemeId::Rpg ? a.x + 4 : a.x, 1, fitted.c_str(), font16(), topColour);
        if (t.id == ThemeId::Rpg) {
            // the frame of the game look is interrupted where the line at the top stands
            c.fillRect(a.x, 9, textWidth(c, fitted.c_str(), font16()) + 8, 3, t.bg);
            text(c, a.x + 4, 1, fitted.c_str(), font16(), topColour);
        }

        if (kanaCard) {
            drawKana(c, t, item, a);
        } else {
            drawWord(c, t, s, item, a);
        }
    }

    void describe(std::string& json) const override
    {
        if (!_pick.item) {
            return;
        }
        const char* state = "asking";
        switch (_state) {
            case State::Probe:  state = "probe"; break;
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
        const bool reads = (_state == State::Meet || _state == State::Note);
        const char* says = "";
        if (reads && _page < _pages.size()) {
            const Page& page = _pages[_page];
            says = (page.partsCount == 0) ? "note" : (page.noteCount == 0) ? "parts" : "parts+note";
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
        json += ",\"page\":";
        json += std::to_string(reads ? _page + 1 : 0);
        json += ",\"pages\":";
        json += std::to_string(_pages.size());
        json += ",\"says\":\"";
        json += says;
        json += "\",\"cut\":";
        json += _cut ? "true" : "false";
        json += ",\"hears\":";
        json += (_app && canHear(*_app) && _state != State::Probe && _state != State::Asking) ? "true" : "false";
        json += ",\"typed\":";
        json += std::to_string(_typed.size());
    }

private:
    static bool canHear(App& app) { return app.settings().sound && app.platform().hasCard(); }

    bool lastPage() const { return _page + 1 >= _pages.size(); }

    // What Tab leads to, in a word: the page `next`, coming from the page `from` or from the mark.
    static const char* turnHint(const Page& next, const Page* from)
    {
        if (next.partsCount > 0) {
            return (from && from->partsCount > 0) ? "Tab: more" : "Tab: kanji";
        }
        return (from && from->noteCount > 0) ? "Tab: more" : "Tab: note";
    }

    void markOf(const Theme& t, std::string& mark, uint32_t& colour) const
    {
        if (_gaveUp) {
            mark   = "→";
            colour = t.dim;
        } else if (_outcome.verdict == match::Verdict::Right) {
            mark   = "〇";
            colour = t.good;
        } else if (_outcome.verdict == match::Verdict::Almost) {
            mark   = "△";
            colour = t.wait;
        } else {
            mark   = "×";
            colour = t.bad;
        }
    }

    // One line of kanji meanings: each kanji stands out, its meaning follows in plain ink.
    int drawParts(Canvas& c, const Theme& t, int x, int y, const std::string& line)
    {
        for (const std::string& unit : split(line.c_str(), "  ")) {
            // what stands before the first space is the kanji, or several that form a word
            const size_t space = unit.find(' ');
            const size_t bytes = (space == std::string::npos) ? unit.size() : space;
            x = text(c, x, y, unit.substr(0, bytes).c_str(), font16(), t.accent);
            x = text(c, x, y, unit.substr(bytes).c_str(), font16(), t.ink);
            x += 16;
        }
        return x - 16;
    }

    // The lines of the page that is open. The meanings stand in the middle, as the word does.
    void drawPage(Canvas& c, const Theme& t, int x, int y, int width, bool centred)
    {
        if (_page >= _pages.size()) {
            return;
        }
        const Page& page = _pages[_page];
        for (size_t i = 0; i < page.partsCount; ++i) {
            const std::string& line = _parts[page.partsFrom + i];
            drawParts(c, t, centred ? x + (width - widthOf(line, font16())) / 2 : x, y, line);
            y += kLine;
        }
        for (size_t i = 0; i < page.noteCount; ++i) {
            text(c, x, y, _note[page.noteFrom + i].c_str(), font16(), t.ink);
            y += kLine;
        }
    }

    void drawWord(Canvas& c, const Theme& t, const Settings& s, const deck::Item& item, const Area& a)
    {
        const int centre = a.x + a.w / 2;
        const bool reads = (_state == State::Meet || _state == State::Note);
        const std::string reading = (_state == State::Marked) ? _outcome.expected : std::string(item.reading);

        // the prompt; two lines of text or of reading leave room for a smaller one only
        const std::vector<std::string> lines = readingLines(reading, a.w);
        const bool asked  = (_state == State::Asking || _state == State::Probe);
        const int tallest = ((reads && _tall) || (!asked && lines.size() > 1)) ? 24 : 32;
        const Face large  = fitFace(c, item.prompt, a.w - 4, tallest);
        const bool tight  = (a.h < 92);  // the game look has the lowest window
        int y             = a.y + (tight ? 0 : 1);
        faceCentre(c, centre, y, item.prompt, large, t.ink);
        y += large.height;

        if (asked) {
            drawTyped(c, t, s, item, a, y + 14);
            return;
        }

        // the reading, with its mark after an answer and its pitch line where the accent is known
        y += tight ? 5 : 6;
        const lgfx::IFont* font = (widthOf(reading, font24()) + kMarkRoom <= a.w) ? font24() : font16();
        std::string mark;
        uint32_t markColour = t.ink;
        if (_state == State::Marked || _state == State::Note) {
            markOf(t, mark, markColour);
        }
        const int markWidth = mark.empty() ? 0 : textWidth(c, mark.c_str(), font) + 4;
        const int width     = markWidth + textWidth(c, lines[0].c_str(), font);
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
        // The accent belongs to the main reading. Another accepted answer is drawn without, and
        // so is a reading in two lines.
        const bool mainReading = (reading == item.reading) && lines.size() == 1;
        pitchText(c, x, y, lines[0], mainReading ? item.accent : -1, style);
        y += (font == font24() ? 24 : 16);
        if (lines.size() > 1) {
            textCentre(c, centre, y + 1, lines[1].c_str(), font, t.ink);
            y += kLine;
        }
        y += tight ? 1 : 3;

        if (_state == State::Copy) {
            drawTyped(c, t, s, item, a, y);
            return;
        }
        if (reads) {
            drawPage(c, t, a.x + 2, y, a.w - 4, true);
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

    void drawKana(Canvas& c, const Theme& t, const deck::Item& item, const Area& a)
    {
        const Column column = columnOf(a, item);
        faceText(c, column.kanaX, column.top + (64 - column.face.height) / 2, item.prompt, column.face, t.ink);

        if (_state == State::Probe || _state == State::Asking) {
            drawLetters(c, t, column.x, column.top + 20, column.width);
            return;
        }

        // what to type, where a word has its reading, with its mark after an answer
        int x = column.x;
        if (_state == State::Marked || _state == State::Note) {
            std::string mark;
            uint32_t markColour = t.ink;
            markOf(t, mark, markColour);
            x = text(c, x, column.top, mark.c_str(), font24(), markColour) + 4;
        }
        const bool fits         = (x + textWidth(c, item.gloss, font24()) <= column.x + column.width);
        const lgfx::IFont* font = fits ? font24() : font16();
        text(c, x, column.top + (font == font24() ? 0 : 4), item.gloss, font, t.ink);

        const int under = column.top + 28;
        if (_state == State::Copy) {
            drawLetters(c, t, column.x, under + 2, column.width);
            if (_tries > 0) {
                text(c, column.x, under + 30, "Look again", font16(), t.wait);
            }
            return;
        }
        if (_state != State::Marked) {
            drawPage(c, t, column.x, under, column.width, false);
            return;
        }

        // marked: what was typed instead, or a word of praise
        if (_gaveUp) {
            return;
        }
        if (_outcome.verdict != match::Verdict::Right) {
            const std::string line = headThatFits(c, "You typed " + _entered, font16(), column.width);
            text(c, column.x, under, line.c_str(), font16(), t.dim);
        } else if (_praise) {
            const std::string japanese = headThatFits(c, _praise->ja, font16(), column.width);
            text(c, column.x, under, japanese.c_str(), font16(), t.dim);
            textWrapped(c, column.x, under + kLine, column.width, _praise->en, font16(), t.dim, kLine, 2);
        }
    }

    // What is being typed for a kana, as the letters themselves: they are the answer.
    void drawLetters(Canvas& c, const Theme& t, int x, int y, int width)
    {
        std::string shown       = _typed + "_";
        const lgfx::IFont* font = (textWidth(c, shown.c_str(), font24()) <= width) ? font24() : font16();
        while (shown.size() > 2 && textWidth(c, shown.c_str(), font) > width) {
            shown.erase(0, 1);
        }
        text(c, x, y + (font == font24() ? 0 : 4), shown.c_str(), font, t.type);
    }

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
    }

    void press(App& app, const Key& key)
    {
        // The key / says the card again wherever its answer can be seen. It is never part of an
        // answer. Without sound it is a key like any other.
        const bool slash = (navigation(key) == Key::Right);
        const bool hear  = slash && canHear(app);
        switch (_state) {
            case State::Meet:
                if (hear) {
                    say(app);
                } else if (!lastPage()) {
                    ++_page;
                } else {
                    _page  = 0;
                    _state = State::Copy;
                }
                return;
            case State::Note:
                if (hear) {
                    say(app);
                } else if (key.code == Key::Tab && !lastPage()) {
                    ++_page;
                } else {
                    next(app);
                }
                return;
            case State::Marked:
                if (hear) {
                    say(app);
                } else if (key.code == Key::Tab && !_pages.empty()) {
                    _page  = 0;
                    _state = State::Note;
                } else {
                    next(app);
                }
                return;
            default:
                break;
        }
        if (slash) {
            if (hear && _state == State::Copy) {
                say(app);
            }
            return;  // while a question is open, hearing the card would give the answer away
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
                    help(app, true);
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

    void next(App& app)
    {
        _typed.clear();
        _answered.clear();
        _entered.clear();
        _peeked    = false;
        _helped    = false;
        _gaveUp    = false;
        _praise    = nullptr;
        _tries     = 0;
        _page      = 0;
        _romajiShown = false;
        if (!app.queue().next(_pick)) {
            _pick = session::Pick();
            _pages.clear();
            app.endSitting();
            app.show(ScreenId::Summary);
            return;
        }
        _remaining = app.queue().remaining();
        layOut(app);
        if (_pick.probe) {
            _state = State::Probe;
        } else if (_pick.isNew) {
            teach(app);
        } else {
            _state = State::Asking;
        }
        _romajiShown = (app.settings().romaji == RomajiMode::Always);
    }

    // Breaks what the card has to say into lines and pages, for the look that is set.
    void layOut(App& app)
    {
        const deck::Item& item = *_pick.item;
        const Area a           = contentArea(app.theme());
        const bool kanaCard    = (item.kind == deck::Kind::Kana);
        const int width        = kanaCard ? columnOf(a, item).width : a.w - 4;
        const std::vector<std::string> reading = readingLines(item.reading, a.w);
        // a reading in two lines leaves room for one line of text under it
        const size_t most = kanaCard ? kLinesByKana : (reading.size() > 1) ? 1 : kLinesOnPage;

        _parts = kanaCard ? std::vector<std::string>() : linesOf(split(item.parts, "  "), "  ", width);
        _note  = linesOf(split(item.note, " "), " ", width);
        _pages.clear();
        _cut  = false;
        _tall = false;
        for (const std::vector<std::string>* lines : {&_parts, &_note}) {
            for (const std::string& line : *lines) {
                _cut = _cut || widthOf(line, font16()) > width;
            }
        }
        if (!kanaCard && reading.size() > 1) {
            _cut = _cut || widthOf(reading[0], font16()) + kMarkRoom > a.w || widthOf(reading[1], font16()) > a.w - 4;
        }
        for (size_t from = 0; from < _parts.size(); from += most) {
            Page page;
            page.partsFrom  = static_cast<uint8_t>(from);
            page.partsCount = static_cast<uint8_t>(_parts.size() - from < most ? _parts.size() - from : most);
            _pages.push_back(page);
        }
        size_t from = 0;
        if (!_pages.empty() && !_note.empty() && _pages.back().lines() + _note.size() <= most) {
            // a short note finds room under the last meanings
            _pages.back().noteCount = static_cast<uint8_t>(_note.size());
            from                    = _note.size();
        }
        for (; from < _note.size(); from += most) {
            Page page;
            page.noteFrom  = static_cast<uint8_t>(from);
            page.noteCount = static_cast<uint8_t>(_note.size() - from < most ? _note.size() - from : most);
            _pages.push_back(page);
        }
        // One size of prompt for all pages of a card: the smaller one if any page has two lines.
        for (const Page& page : _pages) {
            _tall = _tall || page.lines() > 1;
        }
    }

    // A new card is met, then copied. Its answer can be seen from here on, so it is said.
    void teach(App& app)
    {
        ++app.sitting().introduced;
        _typed.clear();
        _tries = 0;
        _page  = 0;
        _state = _pages.empty() ? State::Copy : State::Meet;
        say(app);
    }

    void leave(App& app)
    {
        _pick = session::Pick();
        _pages.clear();
        app.endSitting();
        app.show(app.sitting().asked > 0 ? ScreenId::Summary : ScreenId::Home);
    }

    void say(App& app)
    {
        if (app.speak(_pick.deck, _pick.item)) {
            _spoken = true;
        }
    }

    // Tab: first the romaji, then, on a question, the answer itself. Fn and R: the romaji only.
    void help(App& app, bool romajiOnly = false)
    {
        const bool kanaCard = (_pick.item->kind == deck::Kind::Kana);
        if (_state == State::Probe) {
            teach(app);  // not known: nothing is counted, the card is taught
            return;
        }
        if (_state == State::Copy && kanaCard) {
            return;  // what to type stands beside the kana
        }
        const bool romajiAllowed = (app.settings().romaji != RomajiMode::Never);
        const bool romajiOn      = (app.settings().romaji == RomajiMode::Always) || _peeked || _helped;
        if (romajiAllowed && !romajiOn) {
            _peeked    = true;
            _romajiShown = true;
            return;
        }
        if (_state == State::Asking && !romajiOnly) {
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
        _tone = (grade != srs::Grade::Again) ? 1320 : 440;
    }

    // The answer is on the screen from here on, so it is said.
    void mark(App& app, srs::Grade grade)
    {
        record(app, grade);
        _state = State::Marked;
        say(app);
    }

    void answer(App& app)
    {
        romaji::Options options;
        options.nStyle      = app.settings().textbookN ? romaji::NStyle::Hepburn : romaji::NStyle::Ime;
        options.punctuation = false;
        const std::string typed = romaji::convert(_typed, options, true).kana;
        _outcome                = match::check(typed, *_pick.item);
        _answered               = startsWithKatakana(_pick.item->reading) ? kana::toKatakana(typed) : typed;
        _entered                = _typed;

        if (_state == State::Probe) {
            if (_outcome.verdict == match::Verdict::Right) {
                ++_streak;
                ++app.sitting().introduced;
                _praise = buddy::say("right", app.platform().random());
                mark(app, srs::Grade::Known);
            } else {
                teach(app);
            }
            return;
        }
        if (_state == State::Copy) {
            // Copying what is shown is practice, not a test: wrong tries cost nothing.
            if (_outcome.verdict != match::Verdict::Right) {
                ++_tries;
                if (_tries >= kTriesBeforeHelp && app.settings().romaji != RomajiMode::Never &&
                    _pick.item->kind != deck::Kind::Kana) {
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
        mark(app, grade);
    }

    void giveUp(App& app)
    {
        _outcome          = match::Outcome();
        _outcome.expected = _pick.item->reading;
        _gaveUp           = true;
        _streak           = 0;
        mark(app, srs::Grade::Again);
    }

    session::Pick _pick;
    match::Outcome _outcome;
    std::string _typed;
    std::string _answered;            // the last answer as kana
    std::string _entered;             // the last answer as it was typed
    std::vector<std::string> _parts;  // what each kanji means, in lines
    std::vector<std::string> _note;   // the note, in lines
    std::vector<Page> _pages;
    const deck::BuddyLine* _praise = nullptr;
    App* _app       = nullptr;
    State _state    = State::Asking;
    size_t _page    = 0;
    int _remaining  = 0;
    int _tries      = 0;
    int _streak     = 0;
    int _tone       = 0;      // hertz of the tone this key has earned, 0 for none
    bool _spoken    = false;  // this key has started a clip
    bool _tall      = false;  // a page of the card has two lines
    bool _cut       = false;  // a line of the card is wider than its room
    bool _peeked    = false;  // asked for the romaji before answering
    bool _helped    = false;  // the romaji is shown because copying failed twice
    bool _gaveUp    = false;
    bool _romajiShown = false;  // the romaji is on the screen now
};

class SummaryScreen : public Screen {
public:
    void enter(App& app) override
    {
        // A line whose English fits one line of this look: a letter is 8 pixels wide.
        const size_t letters = static_cast<size_t>(contentArea(app.theme()).w - 4) / 8;
        _line = nullptr;
        for (int attempt = 0; attempt < 12 && !_line; ++attempt) {
            const deck::BuddyLine* line = buddy::say("finish", app.platform().random());
            if (line && std::strlen(line->en) <= letters) {
                _line = line;
            }
        }
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
