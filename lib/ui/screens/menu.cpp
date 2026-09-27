#include <cstdio>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

constexpr int kRowHeight = 27;

struct Entry {
    std::string id;          // for checks run from a computer
    std::string en;
    std::string ja;
    ScreenId target;         // where it leads, unless it starts a sitting
    const deck::Deck* deck;  // the deck of a sitting
    bool sitting;
};

class MenuScreen : public Screen {
public:
    void enter(App&) override
    {
        _entries.clear();
        _entries.push_back({"course", "Course", "", ScreenId::Cards, nullptr, true});
        _entries.push_back({"decks", "Decks", "", ScreenId::Decks, nullptr, false});
        _entries.push_back({"kana", "Kana quiz", "", ScreenId::Kana, nullptr, false});
        _entries.push_back({"chart", "Kana chart", "", ScreenId::Chart, nullptr, false});
        _entries.push_back({"guide", "Sounds", "", ScreenId::Guide, nullptr, false});
        _entries.push_back({"keys", "Keys", "", ScreenId::Keys, nullptr, false});
        _entries.push_back({"settings", "Settings", "", ScreenId::Settings, nullptr, false});
        if (_selected >= static_cast<int>(_entries.size())) {
            _selected = 0;
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
        drawFrame(c, t, nullptr, "", "↑↓ choose", "Enter: open");
        const Area a      = contentArea(t, false);
        const int visible = a.h / kRowHeight;
        const int count   = static_cast<int>(_entries.size());

        // keep the chosen row in view
        if (_selected < _first) {
            _first = _selected;
        } else if (_selected >= _first + visible) {
            _first = _selected - visible + 1;
        }

        int y = a.y + (a.h - visible * kRowHeight) / 2;
        for (int i = _first; i < count && i < _first + visible; ++i) {
            const Entry& entry = _entries[i];
            const bool chosen  = (i == _selected);
            if (chosen) {
                c.fillRoundRect(a.x - 2, y, a.w, kRowHeight - 1, 3, t.row);
            }
            char number[4] = {static_cast<char>(i < 9 ? '1' + i : ' '), 0, 0, 0};
            text(c, a.x + 2, y + 6, number, font16(), chosen ? t.accent : t.dim);
            const int x = text(c, a.x + 18, y + 1, entry.en.c_str(), font24(), chosen ? t.rowInk : t.ink);
            const int japanese = textWidth(c, entry.ja.c_str(), font16());
            if (japanese > 0 && x + 8 + japanese <= a.x + a.w - 16) {
                textRight(c, a.x + a.w - 16, y + 6, entry.ja.c_str(), font16(), t.dim);
            }
            y += kRowHeight;
        }
        if (_first > 0) {
            textRight(c, a.x + a.w - 3, a.y + 2, "▲", font16(), t.dim);
        }
        if (_first + visible < count) {
            textRight(c, a.x + a.w - 3, a.y + a.h - 18, "▼", font16(), t.dim);
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
    }

private:
    void open(App& app, int index)
    {
        const Entry& entry = _entries[index];
        if (entry.sitting) {
            app.startSitting(entry.deck);
        } else {
            app.show(entry.target);
        }
    }

    std::vector<Entry> _entries;
    int _selected = 0;
    int _first    = 0;
};

}  // namespace

std::unique_ptr<Screen> makeMenuScreen()
{
    return std::unique_ptr<Screen>(new MenuScreen());
}

}  // namespace ui
