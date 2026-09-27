#include <cstdio>

#include "../screens.h"
#include "../widgets.h"
#include "buddy.h"

namespace ui {

namespace {

constexpr int kLine = 17;  // line height of the 16 px font

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
        std::snprintf(title, sizeof(title), "Day %d", app.settings().dayNumber);
        char right[16] = "";
        const int battery = app.platform().batteryPercent();
        if (battery >= 0) {
            std::snprintf(right, sizeof(right), "%d%%", battery);
        }
        if (_askDay) {
            drawFrame(c, t, title, right, "Enter: yes", "Space: no");
        } else {
            drawFrame(c, t, title, right, "Any key: start", "Tab: menu");
        }

        const Area a     = contentArea(t);
        const int left   = a.x + 44;
        const int width  = a.w - 46;
        const int inner  = width - 12;
        const int most   = (a.h - kLine - 10) / kLine;  // lines that fit above the day's numbers
        const uint32_t edge = (t.id == ThemeId::Rpg) ? t.ink : t.bubble;

        daruma(c, a.x + 19, a.y + 23);
        if (_askDay) {
            bubble(c, left, a.y + 1, width, 24 + kLine + 10, t.bubble, edge);
            text(c, left + 7, a.y + 5, "New day?", font24(), t.bubbleInk);
            text(c, left + 7, a.y + 31, "あたらしい ひ？", font16(), t.bubbleDim);
        } else {
            int japanese = linesNeeded(c, inner, _ja, font16());
            int english  = linesNeeded(c, inner, _en, font16());
            if (japanese > 2) {
                japanese = 2;
            }
            if (japanese + english > most) {
                english = most - japanese;
            }
            bubble(c, left, a.y + 1, width, (japanese + english) * kLine + 8, t.bubble, edge);
            int y = textWrapped(c, left + 7, a.y + 5, inner, _ja, font16(), t.bubbleInk, kLine, japanese);
            if (english > 0) {
                textWrapped(c, left + 7, y, inner, _en, font16(), t.bubbleDim, kLine, english);
            }
        }

        char numbers[48];
        std::snprintf(numbers, sizeof(numbers), "To review %d   New %d", app.dueToday(), app.newAvailable());
        text(c, a.x + 2, a.y + a.h - kLine, numbers, font16(), t.ink);
    }

    void describe(std::string& json) const override
    {
        json += _askDay ? ",\"asksForDay\":true" : ",\"asksForDay\":false";
    }

private:
    const char* _ja  = "";
    const char* _en  = "";
    bool _askDay     = false;
    bool _firstEntry = true;
};

class KeysScreen : public Screen {
public:
    void key(App& app, const Key&) override { app.show(ScreenId::Menu); }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, "Keys", "", "Any key: back", "");
        const Area a = contentArea(t);
        static const char* const kRows[][2] = {
            {"Enter", "answer, next"},
            {"Tab", "help, show answer"},
            {"esc", "back (Fn and `)"},
            {"G0", "back (side button)"},
            {"; . , /", "up down left right"},
        };
        int y = a.y + 1;
        for (const auto& row : kRows) {
            text(c, a.x + 2, y, row[0], font16(), t.accent);
            text(c, a.x + 66, y, row[1], font16(), t.ink);
            y += kLine;
        }
    }
};

}  // namespace

std::unique_ptr<Screen> makeHomeScreen()
{
    return std::unique_ptr<Screen>(new HomeScreen());
}

std::unique_ptr<Screen> makeKeysScreen()
{
    return std::unique_ptr<Screen>(new KeysScreen());
}

}  // namespace ui
