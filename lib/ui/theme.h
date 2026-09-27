// The four looks. A theme is colours plus the way the frame around every screen is drawn.
#pragma once

#include <M5GFX.h>

#include <cstdint>
#include <string>

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
const lgfx::IFont* font16();  // the smallest size used for anything that has to be read
const lgfx::IFont* font24();
const lgfx::IFont* fontBig();  // 32 px, for a single word or kana

// Whether the font can draw every character of the text. The 32 px font lacks rarer kanji.
bool hasGlyphs(const lgfx::IFont* font, const char* utf8);

// A font at a size: the fonts are bitmaps, so sizes above 32 px are a font drawn twice as large.
struct Face {
    const lgfx::IFont* font;
    int scale;
    int height;  // in pixels, scale included
};

Face face16();
Face face24();

// The largest face, of at most `tallest` pixels (64, 48, 32, 24 or 16), that can draw the text
// and keeps it within `width`. The 16 px face is returned when nothing fits.
Face fitFace(Canvas& c, const char* utf8, int width, int tallest);

struct Area {
    int x;
    int y;
    int w;
    int h;
};

// Where a screen may draw between header and footer. Without a header the area starts higher.
Area contentArea(const Theme& t, bool header = true);

// One line at the bottom of the content area, for what the app says: a hint, a comment.
void drawMessage(Canvas& c, const Theme& t, const char* utf8, uint32_t colour);

// Colours for text that a screen writes into the header itself: plain, and standing out.
uint32_t headerInk(const Theme& t);
uint32_t headerAccent(const Theme& t);

// Clears the canvas and draws header and footer in the theme's manner, in the 16 px font.
// title == nullptr leaves the header out.
void drawFrame(Canvas& c, const Theme& t, const char* title, const char* right, const char* footerLeft,
               const char* footerRight);

// Text helpers. All take UTF-8 and return the x position after the text.
int text(Canvas& c, int x, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textRight(Canvas& c, int rightX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textCentre(Canvas& c, int centreX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour);
int textWidth(Canvas& c, const char* utf8, const lgfx::IFont* font);

int faceText(Canvas& c, int x, int y, const char* utf8, const Face& face, uint32_t colour);
int faceCentre(Canvas& c, int centreX, int y, const char* utf8, const Face& face, uint32_t colour);
int faceWidth(Canvas& c, const char* utf8, const Face& face);

// Draws text broken at spaces so that no line is wider than `width`. Returns the y below the
// last line. At most `maxLines` lines are drawn; what does not fit is left out.
int textWrapped(Canvas& c, int x, int y, int width, const char* utf8, const lgfx::IFont* font, uint32_t colour,
                int lineHeight, int maxLines);

// How many lines textWrapped would need.
int linesNeeded(Canvas& c, int width, const char* utf8, const lgfx::IFont* font);

// The start of the text that fits into `width`, ending in … when something was cut off.
std::string headThatFits(Canvas& c, const std::string& utf8, const lgfx::IFont* font, int width);

}  // namespace ui
