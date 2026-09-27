// The four looks. A theme is colours plus the way the frame around every screen is drawn.
#pragma once

#include <M5GFX.h>

#include <cstdint>

namespace ui {

using Canvas = lgfx::LovyanGFX;

constexpr int kWidth  = 240;
constexpr int kHeight = 135;

enum class ThemeId : uint8_t { Techo, Eki, Rpg, Washi, Count };

struct Theme {
    ThemeId id;
    const char* key;     // stored in settings
    const char* nameJa;
    const char* nameEn;
    uint32_t bg;
    uint32_t ink;        // main text
    uint32_t dim;        // secondary text
    uint32_t faint;      // rules and inactive marks
    uint32_t accent;     // pitch line, highlights
    uint32_t good;
    uint32_t bad;
    uint32_t wait;       // letters not yet decided while typing
    uint32_t row;        // background of the selected row or bubble
    uint32_t rowInk;     // text on that background
    uint32_t type;       // what the user types
    uint32_t bubble;     // speech bubble
    uint32_t bubbleInk;
    uint32_t bubbleDim;
    int left;            // x where content starts
    int top;             // y where content starts
    int bottom;          // first y that belongs to the footer
};

const Theme& theme(ThemeId id);
const Theme& themeByKey(const char* key);
ThemeId nextTheme(ThemeId id);

const lgfx::IFont* font12();
const lgfx::IFont* font16();
const lgfx::IFont* font24();
const lgfx::IFont* fontBig();  // 32 px, for a single word or kana

struct Area {
    int x;
    int y;
    int w;
    int h;
};

// Where a screen may draw between header and footer.
Area contentArea(const Theme& t);

// One line for what the app says to the user: a result, a hint. The game look puts it in the
// lower window next to the buddy; the others put it at the bottom of the content area.
void drawMessage(Canvas& c, const Theme& t, const char* utf8, uint32_t colour);

// Clears the canvas and draws header and footer in the theme's manner.
void drawFrame(Canvas& c, const Theme& t, const char* title, const char* right, const char* footerLeft,
               const char* footerRight);

// Text helpers. Coordinates are the top-left corner unless the name says otherwise.
int text(Canvas& c, int x, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textRight(Canvas& c, int rightX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textCentre(Canvas& c, int centreX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textWidth(Canvas& c, const char* utf8, const lgfx::IFont* font);

// Draws text broken at spaces so that no line is wider than `width`. Returns the y below the
// last line. At most `maxLines` lines are drawn.
int textWrapped(Canvas& c, int x, int y, int width, const char* utf8, const lgfx::IFont* font, uint32_t colour,
                int lineHeight, int maxLines);

}  // namespace ui
