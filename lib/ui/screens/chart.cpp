// The kana chart: the table of the textbooks, to look a kana up and to see how the kana hang
// together. Three rows are shown at a time, the chosen kana large beside them, and below what
// its deck says about it.
#include <cstdio>
#include <cstring>
#include <string>

#include "../screens.h"

namespace ui {

namespace {

constexpr int kColumns    = 5;
constexpr int kRowsShown  = 3;    // rows of the table on one page
constexpr int kRowHeight  = 18;   // a kana of 16 px between the two lines of the mark
constexpr int kTableWidth = 120;
constexpr int kNoteLine   = 16;
constexpr int kNoteLines  = 2;

enum Part : uint8_t { kBasic, kDots, kPairs, kPartCount };

const char* const kPartNames[kPartCount] = {"basic", "dots", "pairs"};

struct Row {
    Part part;
    const char* keys[kColumns];  // what is typed for the kana of each column. nullptr: the table has a gap
};

const Row kRows[] = {
    {kBasic, {"a", "i", "u", "e", "o"}},
    {kBasic, {"ka", "ki", "ku", "ke", "ko"}},
    {kBasic, {"sa", "shi", "su", "se", "so"}},
    {kBasic, {"ta", "chi", "tsu", "te", "to"}},
    {kBasic, {"na", "ni", "nu", "ne", "no"}},
    {kBasic, {"ha", "hi", "fu", "he", "ho"}},
    {kBasic, {"ma", "mi", "mu", "me", "mo"}},
    {kBasic, {"ya", nullptr, "yu", nullptr, "yo"}},
    {kBasic, {"ra", "ri", "ru", "re", "ro"}},
    {kBasic, {"wa", nullptr, nullptr, nullptr, "wo"}},
    {kBasic, {"nn", nullptr, nullptr, nullptr, nullptr}},
    {kDots, {"ga", "gi", "gu", "ge", "go"}},
    {kDots, {"za", "ji", "zu", "ze", "zo"}},
    {kDots, {"da", "di", "du", "de", "do"}},
    {kDots, {"ba", "bi", "bu", "be", "bo"}},
    {kDots, {"pa", "pi", "pu", "pe", "po"}},
    {kPairs, {"kya", "kyu", "kyo", nullptr, nullptr}},
    {kPairs, {"sha", "shu", "sho", nullptr, nullptr}},
    {kPairs, {"cha", "chu", "cho", nullptr, nullptr}},
    {kPairs, {"nya", "nyu", "nyo", nullptr, nullptr}},
    {kPairs, {"hya", "hyu", "hyo", nullptr, nullptr}},
    {kPairs, {"mya", "myu", "myo", nullptr, nullptr}},
    {kPairs, {"rya", "ryu", "ryo", nullptr, nullptr}},
    {kPairs, {"gya", "gyu", "gyo", nullptr, nullptr}},
    {kPairs, {"ja", "ju", "jo", nullptr, nullptr}},
    {kPairs, {"bya", "byu", "byo", nullptr, nullptr}},
    {kPairs, {"pya", "pyu", "pyo", nullptr, nullptr}},
};
constexpr int kRowCount = sizeof(kRows) / sizeof(kRows[0]);

int columnsOf(Part part)
{
    return (part == kPairs) ? 3 : kColumns;
}

int firstRowOf(int part)
{
    for (int row = 0; row < kRowCount; ++row) {
        if (kRows[row].part == part) {
            return row;
        }
    }
    return 0;
}

int pagesOf(int part)
{
    int rows = 0;
    for (const Row& row : kRows) {
        rows += (row.part == part) ? 1 : 0;
    }
    return (rows + kRowsShown - 1) / kRowsShown;
}

int pageCount()
{
    int pages = 0;
    for (int part = 0; part < kPartCount; ++part) {
        pages += pagesOf(part);
    }
    return pages;
}

// Pages never mix the parts of the table: each part starts a page of its own.
int firstRowOnPage(int row)
{
    const int first = firstRowOf(kRows[row].part);
    return first + (row - first) / kRowsShown * kRowsShown;
}

int pageOf(int row)
{
    int pages = 0;
    for (int part = 0; part < kRows[row].part; ++part) {
        pages += pagesOf(part);
    }
    return pages + (row - firstRowOf(kRows[row].part)) / kRowsShown;
}

// The item of a kana deck whose id ends in what is typed for it: "hiragana-ka".
const deck::Item* itemOf(const deck::Deck* deck, const char* typed)
{
    if (!deck || !typed) {
        return nullptr;
    }
    const size_t head = std::strlen(deck->id);
    for (uint16_t i = 0; i < deck->count; ++i) {
        const char* id = deck->items[i].id;
        if (std::strncmp(id, deck->id, head) == 0 && id[head] == '-' && std::strcmp(id + head + 1, typed) == 0) {
            return &deck->items[i];
        }
    }
    return nullptr;
}

enum class Heard : uint8_t { Nothing, Played, SoundOff, NoCard, NoClip };

class ChartScreen : public Screen {
public:
    void enter(App& app) override
    {
        _app = &app;
        index();
        _heard = Heard::Nothing;
    }

    void key(App& app, const Key& key) override
    {
        _app = &app;
        index();
        _heard = Heard::Nothing;
        if (key.code == Key::Escape || key.code == Key::Backspace) {
            app.show(ScreenId::Menu);
            return;
        }
        // The bare / key is the key for sound, so on this screen it does not move the mark.
        if (key.code == Key::Enter || (key.code == Key::Char && key.ch == '/' && !key.fn)) {
            say(app);
            return;
        }
        if (key.code == Key::Tab) {
            nextPart();
            return;
        }
        if (key.code == Key::Char && key.ch == ' ') {
            _katakana = !_katakana;
            settle();
            return;
        }
        switch (navigation(key)) {
            case Key::Up:
                alongColumn(-1);
                break;
            case Key::Down:
                alongColumn(1);
                break;
            case Key::Left:
                alongRow(-1);
                break;
            case Key::Right:
                alongRow(1);
                break;
            default:
                break;
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        _app           = &app;
        index();
        const deck::Item* item = chosen();
        if (!item) {
            drawFrame(c, t, "Kana chart", "", "Esc: back", "");
            drawMessage(c, t, "The kana decks are missing", t.bad);
            return;
        }

        char title[32];
        std::snprintf(title, sizeof(title), "%s %d/%d", _katakana ? "Katakana" : "Hiragana", pageOf(_row) + 1,
                      pageCount());
        drawFrame(c, t, title, _katakana ? "Space: あ" : "Space: ア", "Enter: sound", "Tab: more");

        // the table and the chosen kana side by side, the note in two lines below them
        const Area a     = contentArea(t);
        const int noteY  = a.y + a.h - kNoteLines * kNoteLine;
        const int height = noteY - a.y;
        const int panel  = a.x + kTableWidth + 2;
        drawTable(c, t, a.x, a.y + (height - kRowsShown * kRowHeight) / 2);
        drawChosen(c, t, *item, panel, a.y, a.x + a.w - panel, height);

        if (_heard == Heard::Nothing || _heard == Heard::Played) {
            textWrapped(c, a.x + 2, noteY, a.w - 4, item->note, font16(), t.ink, kNoteLine, kNoteLines);
        } else {
            const char* why = (_heard == Heard::SoundOff) ? "Sound is off in Settings"
                              : (_heard == Heard::NoCard) ? "No memory card" : "No sound for this kana";
            text(c, a.x + 2, noteY, why, font16(), t.bad);
        }
    }

    void describe(std::string& json) const override
    {
        const deck::Item* item = chosen();
        json += ",\"script\":\"";
        json += _katakana ? "katakana" : "hiragana";
        json += "\",\"kana\":\"";
        json += item ? item->prompt : "";
        json += "\",\"types\":\"";
        json += item ? item->gloss : "";
        json += "\",\"item\":\"";
        json += item ? item->id : "";
        json += "\",\"part\":\"";
        json += kPartNames[kRows[_row].part];
        json += "\",\"page\":";
        json += std::to_string(pageOf(_row) + 1);
        json += ",\"pages\":";
        json += std::to_string(pageCount());
        json += ",\"row\":";
        json += std::to_string(_row);
        json += ",\"column\":";
        json += std::to_string(_column);
        json += ",\"met\":";
        json += (item && met(*item)) ? "true" : "false";
        json += ",\"heard\":\"";
        json += (_heard == Heard::Played) ? "played" : (_heard == Heard::SoundOff) ? "sound off"
                : (_heard == Heard::NoCard) ? "no card" : (_heard == Heard::NoClip) ? "no clip" : "";
        json += "\"";
    }

private:
    // Whether the owner has answered the kana at least once.
    bool met(const deck::Item& item) const
    {
        return _app && _app->store().get(deck::key(item.id)).stage != srs::Stage::New;
    }

    void index()
    {
        if (_indexed) {
            return;
        }
        _indexed = true;
        _decks[0] = deck::find("hiragana");
        _decks[1] = deck::find("katakana");
        for (int script = 0; script < 2; ++script) {
            for (int row = 0; row < kRowCount; ++row) {
                for (int column = 0; column < kColumns; ++column) {
                    _cells[script][row][column] = itemOf(_decks[script], kRows[row].keys[column]);
                }
            }
        }
        settle();
    }

    const deck::Item* at(int row, int column) const
    {
        if (row < 0 || row >= kRowCount || column < 0 || column >= kColumns) {
            return nullptr;
        }
        return _cells[_katakana ? 1 : 0][row][column];
    }

    const deck::Item* chosen() const { return at(_row, _column); }

    // The column of the row that has a kana and lies nearest to the one wanted. -1: the row is empty.
    int nearest(int row, int wanted) const
    {
        for (int away = 0; away < kColumns; ++away) {
            if (at(row, wanted - away)) {
                return wanted - away;
            }
            if (at(row, wanted + away)) {
                return wanted + away;
            }
        }
        return -1;
    }

    // Up and down. The column wanted is kept in mind across rows that have a gap there.
    void alongColumn(int step)
    {
        for (int row = _row + step; row >= 0 && row < kRowCount; row += step) {
            const int column = nearest(row, _wanted);
            if (column >= 0) {
                _row    = row;
                _column = column;
                return;
            }
        }
    }

    // Left and right, in reading order: past the end of a row the mark goes on in the next one.
    void alongRow(int step)
    {
        for (int column = _column + step; column >= 0 && column < kColumns; column += step) {
            if (at(_row, column)) {
                _column = column;
                _wanted = column;
                return;
            }
        }
        for (int row = _row + step; row >= 0 && row < kRowCount; row += step) {
            const int column = nearest(row, step > 0 ? 0 : kColumns - 1);
            if (column >= 0) {
                _row    = row;
                _column = column;
                _wanted = column;
                return;
            }
        }
    }

    void nextPart()
    {
        for (int turn = 1; turn <= kPartCount; ++turn) {
            const int row    = firstRowOf((kRows[_row].part + turn) % kPartCount);
            const int column = nearest(row, _wanted);
            if (column >= 0) {
                _row    = row;
                _column = column;
                return;
            }
        }
    }

    // Makes sure the mark stands on a kana, if there is any.
    void settle()
    {
        if (chosen()) {
            return;
        }
        int column = nearest(_row, _wanted);
        for (int row = 0; column < 0 && row < kRowCount; ++row) {
            column = nearest(row, _wanted);
            if (column >= 0) {
                _row = row;
            }
        }
        if (column >= 0) {
            _column = column;
        }
    }

    void say(App& app)
    {
        const deck::Item* item = chosen();
        if (!item) {
            return;
        }
        if (app.speak(_decks[_katakana ? 1 : 0], item)) {
            _heard = Heard::Played;
        } else if (!app.settings().sound) {
            _heard = Heard::SoundOff;
        } else if (!app.platform().hasCard()) {
            _heard = Heard::NoCard;
        } else {
            _heard = Heard::NoClip;
        }
    }

    void drawTable(Canvas& c, const Theme& t, int left, int top)
    {
        const Part part   = kRows[_row].part;
        const int columns = columnsOf(part);
        const int width   = kTableWidth / columns;
        const int first   = firstRowOnPage(_row);
        for (int shown = 0; shown < kRowsShown; ++shown) {
            const int row = first + shown;
            if (row >= kRowCount || kRows[row].part != part) {
                break;
            }
            const int y = top + shown * kRowHeight;
            for (int column = 0; column < columns; ++column) {
                const deck::Item* item = at(row, column);
                const int x            = left + column * width;
                if (!item) {
                    c.fillRect(x + width / 2 - 1, y + 8, 2, 2, t.faint);
                    continue;
                }
                const bool marked = (row == _row && column == _column);
                const bool known  = met(*item);
                if (marked) {
                    c.fillRoundRect(x, y, width, kRowHeight, 3, t.row);
                    c.drawRoundRect(x, y, width, kRowHeight, 3, t.accent);
                }
                const uint32_t ink = marked ? t.rowInk : known ? t.ink : t.dim;
                textCentre(c, x + width / 2, y + 1, item->prompt, font16(), ink);
                if (known) {
                    c.drawFastHLine(x + 4, y + kRowHeight - 1, width - 8, t.good);
                }
            }
        }
    }

    void drawChosen(Canvas& c, const Theme& t, const deck::Item& item, int left, int top, int width, int height)
    {
        const bool known   = met(item);
        const bool pair    = (kRows[_row].part == kPairs);
        const Face large   = fitFace(c, item.prompt, width, pair ? 32 : 48);
        const int kanaW    = faceWidth(c, item.prompt, large);
        const int typedW   = textWidth(c, item.gloss, font24());
        const char* word   = known ? "met" : "new";
        const int wordW    = textWidth(c, word, font16());
        const uint32_t ink = known ? t.good : t.dim;
        const int centre   = left + width / 2;
        if (pair) {
            // two kana are too wide to have anything beside them
            const int y = top + (height - large.height - 24) / 2;
            faceCentre(c, centre, y, item.prompt, large, t.ink);
            const int below = y + large.height;
            const int x     = text(c, centre - (typedW + 8 + wordW) / 2, below, item.gloss, font24(), t.accent);
            text(c, x + 8, below + 6, word, font16(), ink);
        } else {
            const int side = (typedW > wordW) ? typedW : wordW;
            const int x    = centre - (kanaW + 6 + side) / 2;
            const int y    = top + (height - large.height) / 2;
            faceText(c, x, y, item.prompt, large, t.ink);
            text(c, x + kanaW + 6, y + 3, item.gloss, font24(), t.accent);
            text(c, x + kanaW + 6, y + 29, word, font16(), ink);
        }
    }

    App* _app                   = nullptr;  // for describe(), which is given nothing
    const deck::Deck* _decks[2] = {nullptr, nullptr};
    const deck::Item* _cells[2][kRowCount][kColumns] = {};
    int _row       = 0;
    int _column    = 0;
    int _wanted    = 0;  // the column to come back to after rows that have a gap there
    Heard _heard   = Heard::Nothing;
    bool _katakana = false;
    bool _indexed  = false;
};

}  // namespace

std::unique_ptr<Screen> makeChartScreen()
{
    return std::unique_ptr<Screen>(new ChartScreen());
}

}  // namespace ui
