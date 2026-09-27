// Home: where the owner is in the course and what a key will bring. Below it, the page of keys.
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "../screens.h"
#include "../widgets.h"
#include "buddy.h"

namespace ui {

namespace {

constexpr int kLine       = 17;  // line height of the 16 px font
constexpr int kBarHeight  = 6;
constexpr int kTries      = 16;  // lines of the buddy looked at to find one that fits
constexpr int kBubbleLeft = 32;  // from the edge of the content to the bubble, past the buddy

struct Step {
    const deck::Deck* deck;
    DeckProgress progress;
};

// The decks in the order in which the course takes them.
std::vector<Step> course(const App& app)
{
    std::vector<Step> steps;
    for (size_t i = 0; i < deck::count(); ++i) {
        steps.push_back({&deck::at(i), app.progressOf(deck::at(i))});
    }
    std::stable_sort(steps.begin(), steps.end(),
                     [](const Step& a, const Step& b) { return a.deck->stage < b.deck->stage; });
    return steps;
}

// The width of a text in the 16 px font, which gives every letter 8 pixels and every kana 16.
int width16(const char* utf8)
{
    int width = 0;
    for (const unsigned char* p = reinterpret_cast<const unsigned char*>(utf8); *p; ++p) {
        if (*p < 0x80) {
            width += 8;
        } else if ((*p & 0xC0) == 0xC0) {
            width += 16;
        }
    }
    return width;
}

}  // namespace

// What a sitting of the course would hold if it began now: cards to review and new ones. The
// cards are chosen as App::startCourse() has them chosen, with the sizes session::Plan starts
// with, so these are the figures of the sitting itself. The menu asks for them too.
void nextSitting(App& app, int& review, int& fresh)
{
    std::vector<const deck::Deck*> decks;
    for (size_t i = 0; i < deck::count(); ++i) {
        decks.push_back(&deck::at(i));
    }
    session::Plan plan;
    plan.today  = app.today();
    plan.level  = static_cast<uint8_t>(app.settings().level);
    plan.course = true;
    plan.seed   = static_cast<uint32_t>(app.settings().dayNumber);
    session::Queue queue(app.store());
    queue.start(plan, decks);

    review = 0;
    fresh  = 0;
    session::Pick pick;
    while (queue.next(pick)) {
        ++(pick.isNew ? fresh : review);
    }
}

namespace {

// The course as a row of boxes, one for each deck, each filled as far as its cards were seen.
// The box of the deck that is being learnt has a line around it.
void drawCourse(Canvas& c, const Theme& t, const std::vector<Step>& steps, const deck::Deck* now, int x, int y,
                int width)
{
    const int count = static_cast<int>(steps.size());
    if (count == 0) {
        return;
    }
    const int gap = 4;
    const int box = (width - gap * (count - 1)) / count;
    for (int i = 0; i < count; ++i) {
        const DeckProgress& p = steps[i].progress;
        const int left        = x + i * (box + gap);
        int filled            = (p.total > 0) ? box * p.seen / p.total : 0;
        if (p.seen > 0 && filled < 2) {
            filled = 2;
        }
        c.fillRect(left, y, box, kBarHeight, t.faint);
        c.fillRect(left, y, filled, kBarHeight, t.good);
        if (steps[i].deck == now) {
            c.drawRect(left - 1, y - 1, box + 2, kBarHeight + 2, t.ink);
        }
    }
}

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
        const Area a = contentArea(app.theme());
        choose(app.platform().random(), a.w - kBubbleLeft - 8, a.w - 4);
        refresh(app);
    }

    void key(App& app, const Key& key) override
    {
        if (_askDay) {
            if (key.code == Key::Enter || (key.code == Key::Char && (key.ch == 'y' || key.ch == 'Y'))) {
                app.startNewDay();
                _askDay = false;
                refresh(app);
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
        } else if (_review > 0 || _fresh > 0) {
            app.startCourse();
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
        const bool waits = (_review > 0 || _fresh > 0);
        if (_askDay) {
            drawFrame(c, t, title, right, "Enter: yes", "Space: no");
        } else {
            drawFrame(c, t, title, right, waits ? "Any key: start" : "", "Tab: menu");
        }

        const Area a        = contentArea(t);
        const uint32_t edge = (t.id == ThemeId::Rpg) ? t.ink : t.bubble;
        int bottom          = a.y + a.h;

        if (_askDay) {
            const int left = a.x + 44;
            daruma(c, a.x + 19, a.y + 23);
            bubble(c, left, a.y + 1, a.w - 46, 24 + kLine + 10, t.bubble, edge);
            text(c, left + 7, a.y + 5, "New day?", font24(), t.bubbleInk);
            text(c, left + 7, a.y + 31, "あたらしい ひ？", font16(), t.bubbleDim);
        } else {
            // what the buddy says, and under it what that means
            const int left  = a.x + kBubbleLeft;
            const int width = a.w - kBubbleLeft;
            daruma(c, a.x + 14, a.y + 13, true);
            bubble(c, left, a.y + 1, width, 24, t.bubble, edge);
            text(c, left + 4, a.y + 5, headThatFits(c, _ja, font16(), width - 8).c_str(), font16(), t.bubbleInk);
            text(c, a.x + 2, a.y + 28, headThatFits(c, _en, font16(), a.w - 4).c_str(), font16(), t.dim);

            // what a key will bring
            bottom -= 16;
            text(c, a.x + 2, bottom, next(c, a.w - 4).c_str(), font16(), waits ? t.ink : t.dim);
        }

        // where the owner is in the course; the lowest window has no pixel to spare
        const int air = (a.h < 92) ? 0 : 2;
        bottom -= kBarHeight + 2 + air;
        drawCourse(c, t, _steps, _now, a.x + 2, bottom, a.w - 4);
        bottom -= 16 + 2 + air;
        char count[24];
        std::snprintf(count, sizeof(count), "%d of %d", _seen, _total);
        const int countLeft = textRight(c, a.x + a.w - 2, bottom, count, font16(), t.dim);
        const std::string name = headThatFits(c, _name, font16(), countLeft - 8 - (a.x + 2));
        text(c, a.x + 2, bottom, name.c_str(), font16(), t.ink);
    }

    void describe(std::string& json) const override
    {
        json += _askDay ? ",\"asksForDay\":true" : ",\"asksForDay\":false";
        json += ",\"says\":\"";
        json += (_line && !_askDay) ? _line->id : "";
        json += "\",\"deckSeen\":" + std::to_string(_seen) + ",\"deckTotal\":" + std::to_string(_total);
        json += ",\"dueToday\":" + std::to_string(_due) + ",\"nextReview\":" + std::to_string(_review);
        json += ",\"nextNew\":" + std::to_string(_fresh);
        json += ",\"steps\":[";
        for (size_t i = 0; i < _steps.size(); ++i) {
            json += (i ? ",[" : "[") + std::to_string(_steps[i].progress.seen) + "," +
                    std::to_string(_steps[i].progress.total) + "]";
        }
        json += "]";
    }

private:
    // The numbers on the screen. They change with the day and with every sitting.
    void refresh(App& app)
    {
        _steps = course(app);
        _now   = app.courseDeck();
        nextSitting(app, _review, _fresh);
        _due   = 0;
        _seen  = 0;
        _total = 0;
        for (const Step& step : _steps) {
            _due += step.progress.due;
            if (_now == nullptr || step.deck == _now) {
                _seen += step.progress.seen;
                _total += step.progress.total;
            }
        }
        _name = _now ? capitalised(_now->nameEn) : std::string("Every card seen");
    }

    // A line of the buddy that fits: the Japanese into the bubble, the English under it. When
    // none does, the first one is taken and cut.
    void choose(uint32_t pick, int japanese, int english)
    {
        _line = nullptr;
        for (int i = 0; i < kTries; ++i) {
            const deck::BuddyLine* line = buddy::say("greeting", pick + static_cast<uint32_t>(i));
            if (!line) {
                break;
            }
            if (!_line) {
                _line = line;
            }
            if (width16(line->ja) <= japanese && width16(line->en) <= english) {
                _line = line;
                break;
            }
        }
        _ja = _line ? _line->ja : "こんにちは！";
        _en = _line ? _line->en : "Hello!";
    }

    // What the sitting brings that a key starts. When more is due than a sitting holds, it
    // says how many of them come now.
    std::string next(Canvas& c, int width) const
    {
        char words[64];
        if (_review > 0 && _fresh > 0) {
            std::snprintf(words, sizeof(words), "Next: %d to review, %d new", _review, _fresh);
        } else if (_review > 0 && _due > _review) {
            std::snprintf(words, sizeof(words), "Next: %d of %d to review", _review, _due);
        } else if (_review > 0) {
            std::snprintf(words, sizeof(words), "Next: %d to review", _review);
        } else if (_fresh > 0) {
            std::snprintf(words, sizeof(words), "Next: %d new", _fresh);
        } else {
            std::snprintf(words, sizeof(words), "Nothing waits today");
        }
        return headThatFits(c, words, font16(), width);
    }

    std::vector<Step> _steps;
    std::string _name;  // of the deck the course stands at
    const deck::Deck* _now       = nullptr;
    const deck::BuddyLine* _line = nullptr;
    const char* _ja              = "";
    const char* _en              = "";
    int _due         = 0;  // today, within the level that is set
    int _review      = 0;  // of them, in the sitting that a key starts
    int _fresh       = 0;  // new cards in that sitting
    int _seen        = 0;
    int _total       = 0;
    bool _askDay     = false;
    bool _firstEntry = true;
};

class KeysScreen : public Screen {
public:
    void key(App& app, const Key&) override { app.show(ScreenId::Menu); }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, nullptr, "", "Any key: back", "");
        const Area a = contentArea(t, false);
        static const char* const kRows[][2] = {
            {"Enter", "answer, next"},
            {"Tab", "help"},
            {"/", "hear again"},
            {"esc", "back (Fn and `)"},
            {"Button", "back (on the edge)"},
            {"; . , /", "up down left right"},
        };
        const int count = static_cast<int>(sizeof(kRows) / sizeof(kRows[0]));
        const int pitch = std::min(kLine + 1, a.h / count);
        int y           = a.y + (a.h - pitch * count) / 2;
        for (const auto& row : kRows) {
            text(c, a.x + 2, y, row[0], font16(), t.accent);
            text(c, a.x + 66, y, row[1], font16(), t.ink);
            y += pitch;
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
