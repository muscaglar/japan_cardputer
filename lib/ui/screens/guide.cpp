// The guide to how Japanese sounds: one page at a time, with clips to hear.
#include <cstdio>
#include <cstring>
#include <string>

#include "../screens.h"
#include "deck.h"

namespace ui {

namespace {

constexpr int kMostLines   = 5;    // lines of a page
constexpr int kTallestLine = 19;   // the ruled lines of the notebook are this far apart
constexpr int kBodyWidth   = 216;  // 27 letters
constexpr int kHintWidth   = 210;  // the footer of the look that has the least room
constexpr int kHintGap     = 8;    // between the two hints of the footer

int clipCount(const char* clips)
{
    if (!clips || clips[0] == 0) {
        return 0;
    }
    int count = 1;
    for (const char* p = clips; *p; ++p) {
        if (*p == '|') {
            ++count;
        }
    }
    return count;
}

// The clip at that place, counting from 0: the kana that is heard.
std::string clipAt(const char* clips, int index)
{
    const char* start = clips;
    while (index > 0 && start) {
        start = std::strchr(start, '|');
        if (start) {
            ++start;
        }
        --index;
    }
    if (!start) {
        return std::string();
    }
    const char* end = std::strchr(start, '|');
    return end ? std::string(start, static_cast<size_t>(end - start)) : std::string(start);
}

// Where the lines of a page stand: five of them, in the middle of the content area.
struct Lines {
    int x;
    int y;      // the top of the first line
    int step;   // from one line to the next
    int width;
};

Lines linesIn(const Area& a)
{
    Lines lines;
    lines.step  = (a.h / kMostLines < kTallestLine) ? a.h / kMostLines : kTallestLine;
    lines.width = (a.w < kBodyWidth) ? a.w : kBodyWidth;
    lines.x     = a.x + (a.w - lines.width) / 2;
    lines.y     = a.y + (a.h - kMostLines * lines.step) / 2;
    return lines;
}

// The start of the text that fits into `width` at 16 px, ending in … when something was cut off.
std::string fitted(Canvas& c, const std::string& utf8, int width)
{
    if (textWidth(c, utf8.c_str(), font16()) <= width) {
        return utf8;
    }
    std::string head = utf8;
    while (!head.empty()) {
        // drop one whole character from the end: its last bytes, then the byte that starts it
        while (head.size() > 1 && (static_cast<unsigned char>(head.back()) & 0xC0) == 0x80) {
            head.pop_back();
        }
        head.pop_back();
        const std::string shown = head + "…";
        if (textWidth(c, shown.c_str(), font16()) <= width) {
            return shown;
        }
    }
    return std::string();
}

class GuideScreen : public Screen {
public:
    void enter(App&) override
    {
        if (_page >= pages()) {
            _page = 0;
        }
        forgetClips();
    }

    void key(App& app, const Key& key) override
    {
        if (pages() == 0 || key.code == Key::Escape) {
            app.show(ScreenId::Menu);
            return;
        }
        // The arrow printed on / needs Fn on this screen: the bare key plays.
        if (key.code == Key::Char && key.ch == '/' && !key.fn) {
            hear(app);
            return;
        }
        const Key::Code move = navigation(key);
        if (move == Key::Right || key.code == Key::Enter || (key.code == Key::Char && key.ch == ' ')) {
            turn(1);
        } else if (move == Key::Left || key.code == Key::Backspace) {
            turn(-1);
        }
    }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t  = app.theme();
        const int count = pages();
        if (count == 0) {
            drawFrame(c, t, "Sounds", "", "Any key: back", "");
            // on the middle line of a page, which the ruled lines of the notebook leave free
            const Area a      = contentArea(t);
            const Lines lines = linesIn(a);
            textCentre(c, a.x + a.w / 2, lines.y + (kMostLines / 2) * lines.step, "The guide has no pages.", font16(),
                       t.ink);
            return;
        }

        const deck::GuidePage& page = deck::guidePage(static_cast<size_t>(_page));
        const bool ahead            = (_page + 1 < count);
        const bool behind           = (_page > 0);
        const char* left            = ahead ? "Enter: next" : behind ? "Del: back" : "Esc: menu";
        std::string right           = hearing(app, c, page, kHintWidth - kHintGap - textWidth(c, left, font16()));
        if (right.empty()) {
            right = (ahead && behind) ? "Del: back" : (ahead || behind) ? "Esc: menu" : "";
        }
        char number[16];
        std::snprintf(number, sizeof(number), "%d/%d", _page + 1, count);
        drawFrame(c, t, page.title, number, left, right.c_str());

        const Lines lines = linesIn(contentArea(t));
        int y             = lines.y;
        const char* p     = page.body;
        for (int i = 0; i < kMostLines; ++i) {
            const char* end       = std::strchr(p, '\n');
            const std::string row = end ? std::string(p, static_cast<size_t>(end - p)) : std::string(p);
            text(c, lines.x, y, fitted(c, row, lines.width).c_str(), font16(), t.ink);
            y += lines.step;
            if (!end) {
                break;
            }
            p = end + 1;
        }
    }

    void describe(std::string& json) const override
    {
        const int count             = pages();
        const deck::GuidePage* page = count ? &deck::guidePage(static_cast<size_t>(_page)) : nullptr;
        json += ",\"page\":";
        json += std::to_string(page ? _page + 1 : 0);
        json += ",\"pages\":";
        json += std::to_string(count);
        json += ",\"pageId\":\"";
        json += page ? page->id : "";
        json += "\",\"clips\":";
        json += std::to_string(page ? clipCount(page->clips) : 0);
        json += ",\"clipNumber\":";
        json += std::to_string(_number);
        json += ",\"clip\":\"";
        json += _clip;
        json += _heard ? "\",\"heard\":true" : "\",\"heard\":false";
    }

private:
    static int pages() { return static_cast<int>(deck::guidePageCount()); }

    void forgetClips()
    {
        _next   = 0;
        _number = 0;
        _heard  = false;
        _clip.clear();
    }

    void turn(int step)
    {
        const int to = _page + step;
        if (to < 0 || to >= pages()) {
            return;
        }
        _page = to;
        forgetClips();
    }

    void hear(App& app)
    {
        const deck::GuidePage& page = deck::guidePage(static_cast<size_t>(_page));
        const int count             = clipCount(page.clips);
        if (count == 0 || !app.settings().sound || !app.platform().hasCard()) {
            return;
        }
        _number = _next + 1;
        _next   = (_next + 1) % count;
        _heard  = false;

        // The other voice is better than silence when the wanted one has no clip of this page.
        bool male = (app.voiceFolder()[0] == 'm');
        for (int attempt = 0; attempt < 2 && !_heard; ++attempt) {
            const std::string path = std::string("/audio/") + (male ? "m" : "f") + "/guide/" + page.id + "-" +
                                     std::to_string(_number) + ".wav";
            if (app.speakFile(path.c_str())) {
                _clip  = path;
                _heard = true;
            }
            male = !male;
        }
    }

    // What the footer says about hearing, no wider than `room`: how to hear, what was heard, or
    // why the clips of this page stay silent. Empty for a page without clips.
    std::string hearing(App& app, Canvas& c, const deck::GuidePage& page, int room) const
    {
        const int count = clipCount(page.clips);
        if (count == 0) {
            return std::string();
        }
        if (!app.settings().sound) {
            return "Sound is off";
        }
        if (!app.platform().hasCard()) {
            return "No memory card";
        }
        if (_number == 0) {
            return "/: hear";
        }
        std::string which;
        if (count > 1) {
            which = " " + std::to_string(_number) + "/" + std::to_string(count);
        }
        if (!_heard) {
            return "No clip" + which;
        }
        // The kana that was heard, with its number where both fit.
        const std::string heard = "/: " + clipAt(page.clips, _number - 1);
        if (textWidth(c, (heard + which).c_str(), font16()) <= room) {
            return heard + which;
        }
        return fitted(c, heard, room);
    }

    std::string _clip;    // the path of the clip last played on this page
    int _page   = 0;
    int _next   = 0;      // the clip the next press plays, counting from 0
    int _number = 0;      // the clip last asked for, counting from 1. 0: none yet
    bool _heard = false;  // whether that clip was played
};

}  // namespace

std::unique_ptr<Screen> makeGuideScreen()
{
    return std::unique_ptr<Screen>(new GuideScreen());
}

}  // namespace ui
