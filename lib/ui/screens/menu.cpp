#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

struct Entry {
    const char* ja;
    const char* en;
    ScreenId target;
};

const Entry kEntries[] = {
    {"かな", "kana practice", ScreenId::Kana},
    {"せってい", "settings", ScreenId::Settings},
};
constexpr int kEntryCount = sizeof(kEntries) / sizeof(kEntries[0]);

class MenuScreen : public Screen {
public:
    void key(App& app, const Key& key) override
    {
        const Key::Code move = navigation(key);
        if (move == Key::Up) {
            _selected = (_selected + kEntryCount - 1) % kEntryCount;
        } else if (move == Key::Down) {
            _selected = (_selected + 1) % kEntryCount;
        } else if (key.code == Key::Enter || move == Key::Right) {
            app.show(kEntries[_selected].target);
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab) {
            app.show(ScreenId::Home);
        } else if (key.code == Key::Char && key.ch >= '1' && key.ch < '1' + kEntryCount) {
            app.show(kEntries[key.ch - '1'].target);
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
        const Area a = contentArea(t);
        const int rowHeight = (t.id == ThemeId::Techo) ? 17 : 20;
        int y = a.y + ((t.id == ThemeId::Techo) ? 1 : 4);
        for (int i = 0; i < kEntryCount; ++i) {
            const bool chosen = (i == _selected);
            if (chosen) {
                c.fillRect(a.x - 2, y - 1, a.w, rowHeight - 1, t.row);
            }
            char number[4] = {static_cast<char>('1' + i), 0, 0, 0};
            text(c, a.x, y + 1, number, font12(), chosen ? t.accent : t.dim);
            const int x = text(c, a.x + 14, y - 1, kEntries[i].ja, font16(), chosen ? t.rowInk : t.ink);
            text(c, x + 10, y + 2, kEntries[i].en, font12(), t.dim);
            y += rowHeight;
        }
    }

private:
    int _selected = 0;
};

}  // namespace

std::unique_ptr<Screen> makeMenuScreen()
{
    return std::unique_ptr<Screen>(new MenuScreen());
}

}  // namespace ui
