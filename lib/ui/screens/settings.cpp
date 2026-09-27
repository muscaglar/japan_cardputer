#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

enum Row { kLook, kLevel, kRomaji, kSound, kTyping, kRowCount };

const char* const kLabels[kRowCount][2] = {
    {"みため", "look"},
    {"レベル", "level"},
    {"ローマじ", "romaji"},
    {"おと", "sound"},
    {"ん", "typing n"},
};

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
        drawFrame(c, t, "せってい", "settings", "; . えらぶ  , / かえる", "");
        if (t.id == ThemeId::Rpg) {
            daruma(c, 22, 114, true);
            text(c, 42, 101, "すきな ように どうぞ。", font12(), t.ink);
        }
        const Area a        = contentArea(t);
        const int rowHeight = (t.id == ThemeId::Rpg) ? 14 : 17;
        int y               = a.y + ((t.id == ThemeId::Techo) ? 1 : 2);
        for (int row = 0; row < kRowCount; ++row) {
            const bool chosen = (row == _row);
            if (chosen) {
                c.fillRect(a.x - 2, y - 1, a.w, rowHeight - 1, t.row);
            }
            const int x = text(c, a.x, y + 1, kLabels[row][0], font12(), chosen ? t.rowInk : t.ink);
            text(c, x + 6, y + 1, kLabels[row][1], font12(), t.dim);

            const char* value = "";
            switch (row) {
                case kLook:
                    value = theme(s.theme).nameJa;
                    break;
                case kLevel:
                    value = (s.level == 1) ? "かな だけ kana" : (s.level == 2) ? "かんじ すこし" : "ぜんぶ all";  // 3 is the default
                    break;
                case kRomaji:
                    value = (s.romaji == RomajiMode::Always) ? "いつも always"
                            : (s.romaji == RomajiMode::Never) ? "なし never" : "キーで on a key";
                    break;
                case kSound:
                    value = s.sound ? "あり on" : "なし off";
                    break;
                case kTyping:
                    value = s.textbookN ? "minna=みんな" : "minnna=みんな";
                    break;
                default:
                    break;
            }
            textRight(c, a.x + a.w - 6, y + 1, value, font12(), chosen ? t.accent : t.ink);
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
