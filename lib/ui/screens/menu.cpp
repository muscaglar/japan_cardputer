#include <cstdio>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

struct Entry {
    std::string id;          // for checks run from a computer
    std::string ja;
    std::string en;
    ScreenId target;         // where it leads, unless it starts a sitting
    const deck::Deck* deck;  // the deck of a sitting
    bool sitting;
};

class MenuScreen : public Screen {
public:
    void enter(App&) override
    {
        _entries.clear();
        _entries.push_back({"all", "ぜんぶ", "all cards, mixed", ScreenId::Cards, nullptr, true});
        for (size_t i = 0; i < deck::count(); ++i) {
            const deck::Deck& d = deck::at(i);
            _entries.push_back({d.id, d.nameJa, d.nameEn, ScreenId::Cards, &d, true});
        }
        _entries.push_back({"kana", "かな", "kana round", ScreenId::Kana, nullptr, false});
        _entries.push_back({"settings", "せってい", "settings", ScreenId::Settings, nullptr, false});
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
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab) {
            app.show(ScreenId::Home);
        } else if (key.code == Key::Char && key.ch >= '1' && key.ch < '1' + count && key.ch <= '9') {
            _selected = key.ch - '1';
            open(app, _selected);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, "メニュー", "", "; . えらぶ", "Enter きめる");
        if (t.id == ThemeId::Rpg) {
            daruma(c, 22, 114, true);
            text(c, 42, 101, "どれに する？", font12(), t.ink);
        }
        const Area a        = contentArea(t);
        const int rowHeight = 17;
        const int visible   = a.h / rowHeight;
        const int count     = static_cast<int>(_entries.size());

        // keep the chosen row in view
        if (_selected < _first) {
            _first = _selected;
        } else if (_selected >= _first + visible) {
            _first = _selected - visible + 1;
        }

        int y = a.y + ((t.id == ThemeId::Techo) ? 0 : 2);
        for (int i = _first; i < count && i < _first + visible; ++i) {
            const Entry& entry = _entries[i];
            const bool chosen  = (i == _selected);
            if (chosen) {
                c.fillRect(a.x - 2, y - 1, a.w, rowHeight - 1, t.row);
            }
            char number[4] = {static_cast<char>(i < 9 ? '1' + i : ' '), 0, 0, 0};
            text(c, a.x, y + 2, number, font12(), chosen ? t.accent : t.dim);
            const int x = text(c, a.x + 12, y + 2, entry.ja.c_str(), font12(), chosen ? t.rowInk : t.ink);
            text(c, x + 8, y + 2, entry.en.c_str(), font12(), t.dim);
            y += rowHeight;
        }
        if (_first > 0) {
            textRight(c, a.x + a.w - 4, a.y + 1, "▲", font12(), t.dim);
        }
        if (_first + visible < count) {
            textRight(c, a.x + a.w - 4, a.y + (visible - 1) * rowHeight + 2, "▼", font12(), t.dim);
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
