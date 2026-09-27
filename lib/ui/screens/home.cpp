#include <cstdio>

#include "../screens.h"
#include "../widgets.h"
#include "buddy.h"

namespace ui {

namespace {

class HomeScreen : public Screen {
public:
    void enter(App& app) override
    {
        // The device has no clock. After a day on which cards were answered, the first thing at
        // the next start is the question whether a new day has begun.
        if (_firstEntry) {
            _firstEntry = false;
            _askDay     = (app.settings().answeredToday > 0);
        }
        const deck::BuddyLine* line = buddy::say("greeting", app.platform().random());
        _ja                         = line ? line->ja : "こんにちは！";
        _en                         = line ? line->en : "Hello!";
        _english                    = false;
    }

    void key(App& app, const Key& key) override
    {
        if (_askDay) {
            if (key.code == Key::Enter || (key.code == Key::Char && (key.ch == 'y' || key.ch == 'Y'))) {
                app.startNewDay();
                _askDay = false;
            } else if (key.code == Key::Escape || key.code == Key::Backspace ||
                       (key.code == Key::Char && (key.ch == 'n' || key.ch == 'N' || key.ch == ' '))) {
                _askDay = false;
            }
            return;
        }
        if (key.code == Key::Tab) {
            app.show(ScreenId::Menu);
        } else if (key.code == Key::Char && key.ch == ' ') {
            _english = !_english;
        } else if (key.code == Key::Escape || key.code == Key::Backspace) {
            // nothing to go back to
        } else {
            app.startSitting(nullptr);
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

        const char* words  = _askDay ? "あたらしい ひ？" : (_english ? _en : _ja);
        const char* toggle = _askDay ? "new day?" : (_english ? "Space にほんご" : "Space えいご");
        if (_askDay) {
            drawFrame(c, t, title, right, "Enter はい", "Space いいえ");
        } else {
            drawFrame(c, t, title, right, "キーで スタート", "Tab メニュー");
        }
        const Area a = contentArea(t);

        char waiting[48];
        std::snprintf(waiting, sizeof(waiting), "ふくしゅう %d", app.dueToday());
        char fresh[48];
        std::snprintf(fresh, sizeof(fresh), "あたらしい %d", app.newAvailable());

        if (t.id == ThemeId::Rpg) {
            // The buddy speaks in the lower window; the upper one holds the day's numbers.
            daruma(c, 22, 114, true);
            textWrapped(c, 42, 100, 186, words, font12(), t.ink, 13, 1);
            text(c, a.x + 4, a.y + 8, "きょう", font16(), t.ink);
            text(c, a.x + 4, a.y + 32, waiting, font12(), t.ink);
            text(c, a.x + 4, a.y + 47, fresh, font12(), t.ink);
            textRight(c, a.x + a.w - 4, a.y + a.h - 14, toggle, font12(), t.dim);
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

        const int row = top + 58;
        int x         = text(c, a.x + 4, row, "きょう", font12(), t.dim);
        x             = text(c, x + 10, row, waiting, font12(), t.ink);
        text(c, x + 10, row, fresh, font12(), t.ink);
    }

    void describe(std::string& json) const override
    {
        json += _askDay ? ",\"asksForDay\":true" : ",\"asksForDay\":false";
    }

private:
    const char* _ja  = "";
    const char* _en  = "";
    bool _english    = false;
    bool _askDay     = false;
    bool _firstEntry = true;
};

}  // namespace

std::unique_ptr<Screen> makeHomeScreen()
{
    return std::unique_ptr<Screen>(new HomeScreen());
}

}  // namespace ui
