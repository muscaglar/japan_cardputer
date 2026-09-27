// Decks: every deck in the order of the course, with how far it is learnt. Enter starts a
// sitting from the chosen one.
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

constexpr int kRows      = 5;   // on the screen at a time
constexpr int kBarHeight = 2;
constexpr int kTrack     = 3;   // the width of the mark at the right edge that shows where the list stands
constexpr int kDueWidth  = 24;  // three figures
constexpr int kSeenWidth = 56;  // "104/164"

struct Row {
    const deck::Deck* deck;
    DeckProgress progress;
};

class DecksScreen : public Screen {
public:
    void enter(App& app) override
    {
        _rows.clear();
        for (size_t i = 0; i < deck::count(); ++i) {
            _rows.push_back({&deck::at(i), app.progressOf(deck::at(i))});
        }
        std::stable_sort(_rows.begin(), _rows.end(),
                         [](const Row& a, const Row& b) { return a.deck->stage < b.deck->stage; });
        if (_selected >= static_cast<int>(_rows.size())) {
            _selected = 0;
        }
    }

    void key(App& app, const Key& key) override
    {
        const int count      = static_cast<int>(_rows.size());
        const Key::Code move = navigation(key);
        if (move == Key::Up && count > 0) {
            _selected = (_selected + count - 1) % count;
        } else if (move == Key::Down && count > 0) {
            _selected = (_selected + 1) % count;
        } else if (key.code == Key::Enter || move == Key::Right) {
            if (count > 0 && waits(_rows[_selected])) {
                app.startSitting(_rows[_selected].deck);
            }
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab ||
                   move == Key::Left) {
            app.show(ScreenId::Menu);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t  = app.theme();
        const int count = static_cast<int>(_rows.size());
        const bool open = (count > 0 && waits(_rows[_selected]));
        drawFrame(c, t, "Decks", "", "↑↓ choose", open ? "Enter: start" : "Nothing waits");
        const Area a    = contentArea(t);
        const int pitch = a.h / kRows;

        // The columns: the name, how many cards were seen of all, how many wait today.
        const int dueRight  = a.x + a.w - kTrack - 4;
        const int seenRight = dueRight - kDueWidth - 8;
        const int nameLeft  = a.x + 2;
        const int nameWidth = seenRight - kSeenWidth - 6 - nameLeft;
        heading(c, t, "seen", seenRight);
        heading(c, t, "due", dueRight);

        // keep the chosen row in view
        if (_selected < _first) {
            _first = _selected;
        } else if (_selected >= _first + kRows) {
            _first = _selected - kRows + 1;
        }

        int y = a.y + (a.h - kRows * pitch) / 2;
        for (int i = _first; i < count && i < _first + kRows; ++i) {
            const Row& row    = _rows[i];
            const bool chosen = (i == _selected);
            // the bar stands under the line of text; the top row of a line of text is empty
            const int barY  = y + pitch - kBarHeight - (pitch > 18 ? 1 : 0);
            const int textY = barY - 16;
            if (chosen) {
                c.fillRoundRect(a.x - 2, y, a.w - kTrack, pitch, 3, t.row);
            }
            const std::string name = headThatFits(c, capitalised(row.deck->nameEn), font16(), nameWidth);
            text(c, nameLeft, textY, name.c_str(), font16(), chosen ? t.rowInk : t.ink);

            char figures[24];
            std::snprintf(figures, sizeof(figures), "%d/%d", row.progress.seen, row.progress.total);
            textRight(c, seenRight, textY, figures, font16(), chosen ? t.rowInk : t.dim);
            std::snprintf(figures, sizeof(figures), "%d", row.progress.due);
            textRight(c, dueRight, textY, figures, font16(), row.progress.due > 0 ? t.accent : t.dim);

            const int barWidth = dueRight - nameLeft;
            int filled = (row.progress.total > 0) ? barWidth * row.progress.seen / row.progress.total : 0;
            if (row.progress.seen > 0 && filled < 2) {
                filled = 2;
            }
            c.fillRect(nameLeft, barY, barWidth, kBarHeight, t.faint);
            c.fillRect(nameLeft, barY, filled, kBarHeight, t.good);
            y += pitch;
        }

        // where the list stands, when it has more rows than the screen
        if (count > kRows) {
            const int left   = a.x + a.w - kTrack;
            const int length = a.h * kRows / count;
            c.fillRect(left, a.y, kTrack, a.h, t.faint);
            c.fillRect(left, a.y + (a.h - length) * _first / (count - kRows), kTrack, length, t.dim);
        }
    }

    void describe(std::string& json) const override
    {
        json += ",\"decks\":[";
        for (size_t i = 0; i < _rows.size(); ++i) {
            json += (i ? ",\"" : "\"");
            json += _rows[i].deck->id;
            json += "\"";
        }
        json += "],\"chosen\":";
        json += std::to_string(_selected);
        json += ",\"first\":";
        json += std::to_string(_first);
        list(json, "deckSeen", [](const Row& row) { return row.progress.seen; });
        list(json, "deckTotal", [](const Row& row) { return row.progress.total; });
        list(json, "deckDue", [](const Row& row) { return row.progress.due; });
    }

private:
    // Whether a sitting from this deck would have a card: one that is due, or one never seen.
    static bool waits(const Row& row)
    {
        return row.progress.due > 0 || row.progress.seen < row.progress.total;
    }

    // The name of a column, written into the header above it.
    static void heading(Canvas& c, const Theme& t, const char* name, int right)
    {
        const int width = textWidth(c, name, font16());
        if (t.id == ThemeId::Rpg) {
            // the frame of the game look is interrupted where the name stands
            c.fillRect(right - width - 4, 9, width + 8, 3, t.bg);
        }
        textRight(c, right, 1, name, font16(), headerInk(t));
    }

    template <typename Value>
    void list(std::string& json, const char* name, Value value) const
    {
        json += ",\"";
        json += name;
        json += "\":[";
        for (size_t i = 0; i < _rows.size(); ++i) {
            json += (i ? "," : "");
            json += std::to_string(value(_rows[i]));
        }
        json += "]";
    }

    std::vector<Row> _rows;
    int _selected = 0;
    int _first    = 0;
};

}  // namespace

std::unique_ptr<Screen> makeDecksScreen()
{
    return std::unique_ptr<Screen>(new DecksScreen());
}

}  // namespace ui
