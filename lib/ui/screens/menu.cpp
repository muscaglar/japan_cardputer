#include <cstdio>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

// In home.cpp: what a sitting of the course would hold if it began now.
void nextSitting(App& app, int& review, int& fresh);

namespace {

constexpr int kRows  = 4;  // on the screen at a time
constexpr int kTrack = 3;  // the width of the mark at the right edge that shows where the list stands

struct Entry {
    std::string id;          // for checks run from a computer
    std::string en;
    ScreenId target;         // where it leads, unless it starts the course
    bool course;
    std::string says;        // at the right end of the row: what is worth knowing before it is opened
    std::string saysShort;   // the same in fewer letters, for when the long form does not fit
    std::string shown;       // the one of the two that is drawn; empty when neither fits
};

class MenuScreen : public Screen {
public:
    void enter(App& app) override
    {
        _entries.clear();
        _entries.push_back({"course", "Course", ScreenId::Cards, true, "", "", ""});
        _entries.push_back({"decks", "Decks", ScreenId::Decks, false, "", "", ""});
        _entries.push_back({"kana", "Kana quiz", ScreenId::Kana, false, "", "", ""});
        _entries.push_back({"chart", "Kana chart", ScreenId::Chart, false, "", "", ""});
        _entries.push_back({"guide", "Sounds", ScreenId::Guide, false, "", "", ""});
        _entries.push_back({"keys", "Keys", ScreenId::Keys, false, "", "", ""});
        _entries.push_back({"settings", "Settings", ScreenId::Settings, false, "", "", ""});
        if (_selected >= static_cast<int>(_entries.size())) {
            _selected = 0;
        }

        int seen  = 0;
        int total = 0;
        int due   = 0;
        for (size_t i = 0; i < deck::count(); ++i) {
            const DeckProgress progress = app.progressOf(deck::at(i));
            seen += progress.seen;
            total += progress.total;
            due += progress.due;
        }

        // Course: what waits today within the level that is set, and the new cards that the
        // next sitting has room for
        nextSitting(app, _review, _fresh);
        char words[40];
        if (due > 0 && _fresh > 0) {
            std::snprintf(words, sizeof(words), "%d due, %d new", due, _fresh);
            _entries[0].says = words;
            std::snprintf(words, sizeof(words), "%d due", due);
            _entries[0].saysShort = words;
        } else if (due > 0) {
            std::snprintf(words, sizeof(words), "%d due", due);
            _entries[0].says = words;
        } else if (_fresh > 0) {
            std::snprintf(words, sizeof(words), "%d new", _fresh);
            _entries[0].says = words;
        } else {
            _entries[0].says = "done";
        }

        // Decks: how many cards were seen, of all there are
        std::snprintf(words, sizeof(words), "%d of %d", seen, total);
        _entries[1].says = words;
        std::snprintf(words, sizeof(words), "%d", seen);
        _entries[1].saysShort = words;

        // Sounds: why nothing would be heard
        if (!app.platform().hasCard()) {
            _entries[4].says = "no card";
        } else if (!app.settings().sound) {
            _entries[4].says = "sound off";
        }

        // Which form has room beside the name: a letter of the name is 12 wide, one of these 8.
        const Area a = contentArea(app.theme(), false);
        for (Entry& entry : _entries) {
            const int room = a.w - kTrack - 5 - 18 - 12 * static_cast<int>(entry.en.size()) - 8;
            for (const std::string* says : {&entry.says, &entry.saysShort}) {
                if (!says->empty() && 8 * static_cast<int>(says->size()) <= room) {
                    entry.shown = *says;
                    break;
                }
            }
        }
    }

    void key(App& app, const Key& key) override
    {
        const int count      = static_cast<int>(_entries.size());
        const Key::Code move = navigation(key);
        if (move == Key::Up) {
            _selected = (_selected + count - 1) % count;
        } else if (move == Key::Down) {
            _selected = (_selected + 1) % count;
        } else if (key.code == Key::Enter || move == Key::Right) {
            open(app, _selected);
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab ||
                   move == Key::Left) {
            app.show(ScreenId::Home);
        } else if (key.code == Key::Char && key.ch >= '1' && key.ch < '1' + count && key.ch <= '9') {
            _selected = key.ch - '1';
            open(app, _selected);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        char numbers[24];
        std::snprintf(numbers, sizeof(numbers), "↑↓ or 1-%d", static_cast<int>(_entries.size()));
        drawFrame(c, t, nullptr, "", numbers, "Enter: open");
        const Area a        = contentArea(t, false);
        const int rowHeight = a.h / kRows;
        const int count     = static_cast<int>(_entries.size());

        // keep the chosen row in view
        if (_selected < _first) {
            _first = _selected;
        } else if (_selected >= _first + kRows) {
            _first = _selected - kRows + 1;
        }

        const int right = a.x + a.w - kTrack - 5;
        int y           = a.y + (a.h - kRows * rowHeight) / 2;
        for (int i = _first; i < count && i < _first + kRows; ++i) {
            const Entry& entry = _entries[i];
            const bool chosen  = (i == _selected);
            const int textY    = y + (rowHeight - 24) / 2;
            if (chosen) {
                c.fillRoundRect(a.x - 2, y, a.w - kTrack, rowHeight - 1, 3, t.row);
            }
            char number[4] = {static_cast<char>(i < 9 ? '1' + i : ' '), 0, 0, 0};
            text(c, a.x + 2, textY + 5, number, font16(), chosen ? t.accent : t.dim);
            text(c, a.x + 18, textY, entry.en.c_str(), font24(), chosen ? t.rowInk : t.ink);
            if (!entry.shown.empty()) {
                textRight(c, right, textY + 5, entry.shown.c_str(), font16(), chosen ? t.accent : t.dim);
            }
            y += rowHeight;
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
        json += ",\"menu\":[";
        for (size_t i = 0; i < _entries.size(); ++i) {
            json += (i ? ",\"" : "\"");
            json += _entries[i].id;
            json += "\"";
        }
        json += "],\"chosen\":";
        json += std::to_string(_selected);
        json += ",\"first\":";
        json += std::to_string(_first);
        json += ",\"says\":[";
        for (size_t i = 0; i < _entries.size(); ++i) {
            json += (i ? ",\"" : "\"");
            json += _entries[i].shown;
            json += "\"";
        }
        json += "]";
    }

private:
    void open(App& app, int index)
    {
        const Entry& entry = _entries[index];
        if (entry.course) {
            if (_review > 0 || _fresh > 0) {
                app.startCourse();
            }
        } else {
            app.show(entry.target);
        }
    }

    std::vector<Entry> _entries;
    int _selected = 0;
    int _first    = 0;
    int _review   = 0;  // what a sitting of the course would hold
    int _fresh    = 0;
};

}  // namespace

std::unique_ptr<Screen> makeMenuScreen()
{
    return std::unique_ptr<Screen>(new MenuScreen());
}

}  // namespace ui
