#include <cstdio>

#include "../screens.h"
#include "../widgets.h"

namespace ui {

namespace {

struct Line {
    const char* ja;
    const char* en;
};

// What the buddy says. Kana only, with spaces between words, for a reader whose kana is shaky.
const Line kGreetings[] = {
    {"こんにちは！", "Hello!"},
    {"きょうも がんばろう。", "Let's do our best today too."},
    {"ゆっくりで いいよ。", "Slowly is fine."},
    {"いっしょに やろう。", "Let's do it together."},
    {"すこしずつ おぼえよう。", "Let's learn little by little."},
};
constexpr int kGreetingCount = sizeof(kGreetings) / sizeof(kGreetings[0]);

class HomeScreen : public Screen {
public:
    void enter(App& app) override
    {
        _line    = static_cast<int>(app.platform().random() % kGreetingCount);
        _english = false;
    }

    void key(App& app, const Key& key) override
    {
        if (key.code == Key::Tab) {
            app.show(ScreenId::Menu);
        } else if (key.code == Key::Char && key.ch == ' ') {
            _english = !_english;
        } else if (key.code == Key::Escape || key.code == Key::Backspace) {
            // nothing to go back to
        } else {
            app.show(ScreenId::Kana);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        char title[24];
        std::snprintf(title, sizeof(title), "%d日目", app.settings().dayNumber);
        char right[32];
        const int battery = app.platform().batteryPercent();
        const char* sound = app.settings().sound ? "おと" : "マナー";
        if (battery >= 0) {
            std::snprintf(right, sizeof(right), "%s %d%%", sound, battery);
        } else {
            std::snprintf(right, sizeof(right), "%s", sound);
        }
        drawFrame(c, t, title, right, "キーで スタート", "Tab メニュー");

        const Line& line  = kGreetings[_line];
        const char* words = _english ? line.en : line.ja;

        const char* toggle = _english ? "Space にほんご" : "Space えいご";
        const Area a       = contentArea(t);

        if (t.id == ThemeId::Rpg) {
            // The buddy speaks in the lower window; the upper one is left for the day's numbers.
            daruma(c, 22, 114, true);
            textWrapped(c, 42, 100, 186, words, font12(), t.ink, 13, 1);
            text(c, a.x + 2, a.y + 8, toggle, font12(), t.dim);
            return;
        }

        const int top = a.y + 4;
        daruma(c, a.x + 20, top + 26);
        const int inner = a.w - 66;
        bubble(c, a.x + 48, top, a.w - 52, 50, t.bubble);
        if (textWidth(c, words, font16()) <= inner) {
            text(c, a.x + 56, top + 8, words, font16(), t.bubbleInk);
        } else {
            textWrapped(c, a.x + 56, top + 5, inner, words, font12(), t.bubbleInk, 13, 2);
        }
        text(c, a.x + 56, top + 33, toggle, font12(), t.bubbleDim);
    }

private:
    int _line     = 0;
    bool _english = false;
};

}  // namespace

std::unique_ptr<Screen> makeHomeScreen()
{
    return std::unique_ptr<Screen>(new HomeScreen());
}

}  // namespace ui
