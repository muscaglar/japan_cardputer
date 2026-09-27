#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

enum Row { kLook, kLevel, kRomaji, kSound, kTyping, kRowCount };

const char* const kLabels[kRowCount] = {"Look", "Cards", "Romaji", "Sound", "Typing ん"};

class SettingsScreen : public Screen {
public:
    void key(App& app, const Key& key) override
    {
        Settings& s          = app.settings();
        const Key::Code move = navigation(key);
        if (move == Key::Up) {
            _row = (_row + kRowCount - 1) % kRowCount;
        } else if (move == Key::Down) {
            _row = (_row + 1) % kRowCount;
        } else if (move == Key::Left || move == Key::Right || key.code == Key::Enter) {
            const int step = (move == Key::Left) ? -1 : 1;
            switch (_row) {
                case kLook: {
                    const int count = static_cast<int>(ThemeId::Count);
                    s.theme = static_cast<ThemeId>((static_cast<int>(s.theme) + count + step) % count);
                    break;
                }
                case kLevel:
                    s.level = 1 + (s.level - 1 + 3 + step) % 3;
                    break;
                case kRomaji: {
                    const int count = static_cast<int>(RomajiMode::Count);
                    s.romaji = static_cast<RomajiMode>((static_cast<int>(s.romaji) + count + step) % count);
                    break;
                }
                case kSound:
                    s.sound = !s.sound;
                    break;
                case kTyping:
                    s.textbookN = !s.textbookN;
                    break;
                default:
                    break;
            }
            app.saveSettings();
        } else if (key.code == Key::Escape || key.code == Key::Backspace || key.code == Key::Tab) {
            app.show(ScreenId::Menu);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t    = app.theme();
        const Settings& s = app.settings();
        drawFrame(c, t, "Settings", "", "↑↓ choose", "←→ change");
        const Area a        = contentArea(t);
        const int rowHeight = a.h / kRowCount;
        int y               = a.y + (a.h - rowHeight * kRowCount) / 2;
        for (int row = 0; row < kRowCount; ++row) {
            const bool chosen = (row == _row);
            if (chosen) {
                c.fillRoundRect(a.x - 2, y, a.w, rowHeight, 3, t.row);
            }
            const int textY = y + (rowHeight - 16) / 2;
            text(c, a.x + 2, textY, kLabels[row], font16(), chosen ? t.rowInk : t.ink);

            const char* value = "";
            switch (row) {
                case kLook:
                    value = theme(s.theme).nameEn;
                    break;
                case kLevel:
                    value = (s.level == 1) ? "kana only" : (s.level == 2) ? "easy kanji too" : "all";
                    break;
                case kRomaji:
                    value = (s.romaji == RomajiMode::Always) ? "always" : (s.romaji == RomajiMode::Never) ? "never" : "with Tab";
                    break;
                case kSound:
                    value = s.sound ? "on" : "off";
                    break;
                case kTyping:
                    value = s.textbookN ? "minna = みんな" : "minnna = みんな";
                    break;
                default:
                    break;
            }
            textRight(c, a.x + a.w - 6, textY, value, font16(), chosen ? t.accent : t.dim);
            y += rowHeight;
        }
    }

private:
    int _row = 0;
};

}  // namespace

std::unique_ptr<Screen> makeSettingsScreen()
{
    return std::unique_ptr<Screen>(new SettingsScreen());
}

}  // namespace ui
