#include "theme.h"

#include <cstring>
#include <string>

namespace ui {

namespace {

constexpr uint32_t kWhite = 0xFFFFFFu;
constexpr uint32_t kBlack = 0x000000u;
constexpr uint32_t kNavy  = 0x0C2048u;
constexpr uint32_t kPaper = 0xFAF7EEu;
constexpr uint32_t kSumi  = 0x18181Cu;
constexpr uint32_t kShu   = 0xD63C2Au;  // vermilion

const Theme kThemes[] = {
    {ThemeId::Techo, "techo", "手帳", "Notebook", kPaper, kSumi, 0x5F5F69u, 0xCDD7E1u, kShu, 0x14783Cu, 0xBE1E1Eu,
     0xB46E00u, 0xFFEEA0u, kSumi, 0x1E3C8Cu, 0xFFEEA0u, kSumi, 0x6E6450u, 28, 16, 119},
    {ThemeId::Eki, "eki", "駅", "Station sign", kNavy, kWhite, 0xBECDEBu, 0x465F96u, 0xFFA532u, 0x82EBA0u, 0xFF877Du,
     0xFFC878u, 0x1E386Eu, kWhite, kWhite, kWhite, kNavy, 0x5A6E96u, 6, 24, 118},
    {ThemeId::Rpg, "rpg", "ゲーム", "Game windows", kBlack, kWhite, 0xA0A0A0u, 0x5A5A5Au, 0xFFDC5Au, 0x78FF8Cu,
     0xFF6E6Eu, 0xFFB450u, 0x282846u, kWhite, kWhite, kBlack, kWhite, 0xA0A0A0u, 12, 16, 95},
    {ThemeId::Washi, "washi", "和紙", "Paper and vermilion", 0xFDFAF3u, kSumi, 0x6E645Fu, 0xE1D7C8u, kShu, 0x1E7846u,
     0xAA1E1Eu, 0xB46E00u, 0xF4E8D6u, kSumi, kSumi, 0xF4E8D6u, kSumi, 0x6E645Fu, 14, 20, 115},
};

void window(Canvas& c, int x, int y, int w, int h, uint32_t ink)
{
    c.drawRoundRect(x, y, w, h, 4, ink);
    c.drawRoundRect(x + 1, y + 1, w - 2, h - 2, 3, ink);
}

}  // namespace

const Theme& theme(ThemeId id)
{
    const size_t index = static_cast<size_t>(id);
    return kThemes[index < static_cast<size_t>(ThemeId::Count) ? index : 0];
}

const Theme& themeByKey(const char* key)
{
    for (const Theme& t : kThemes) {
        if (key && std::strcmp(t.key, key) == 0) {
            return t;
        }
    }
    return kThemes[0];
}

ThemeId nextTheme(ThemeId id)
{
    return static_cast<ThemeId>((static_cast<int>(id) + 1) % static_cast<int>(ThemeId::Count));
}

const lgfx::IFont* font12()  { return &fonts::efontJA_12; }
const lgfx::IFont* font16()  { return &fonts::efontJA_16; }
const lgfx::IFont* font24()  { return &fonts::efontJA_24; }
const lgfx::IFont* fontBig() { return &fonts::lgfxJapanGothic_32; }

int textWidth(Canvas& c, const char* utf8, const lgfx::IFont* font)
{
    return c.textWidth(utf8, font);
}

int text(Canvas& c, int x, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour)
{
    c.setFont(font);
    c.setTextSize(1);
    c.setTextWrap(false);
    c.setTextDatum(top_left);
    c.setTextColor(colour);
    c.setCursor(x, y);
    c.print(utf8);
    return c.getCursorX();
}

int textRight(Canvas& c, int rightX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour)
{
    const int w = textWidth(c, utf8, font);
    text(c, rightX - w, y, utf8, font, colour);
    return rightX - w;
}

int textCentre(Canvas& c, int centreX, int y, const char* utf8, const lgfx::IFont* font, uint32_t colour)
{
    const int w = textWidth(c, utf8, font);
    return text(c, centreX - w / 2, y, utf8, font, colour);
}

int textWrapped(Canvas& c, int x, int y, int width, const char* utf8, const lgfx::IFont* font, uint32_t colour,
                int lineHeight, int maxLines)
{
    std::string line;
    std::string word;
    int lines = 0;
    const char* p = utf8;
    while (lines < maxLines) {
        const bool end = (*p == 0);
        if (end || *p == ' ') {
            std::string candidate = line.empty() ? word : line + " " + word;
            if (!line.empty() && textWidth(c, candidate.c_str(), font) > width) {
                text(c, x, y, line.c_str(), font, colour);
                y += lineHeight;
                ++lines;
                line = word;
            } else {
                line = candidate;
            }
            word.clear();
            if (end) {
                if (!line.empty() && lines < maxLines) {
                    text(c, x, y, line.c_str(), font, colour);
                    y += lineHeight;
                }
                break;
            }
        } else {
            word.push_back(*p);
        }
        ++p;
    }
    return y;
}

Area contentArea(const Theme& t)
{
    switch (t.id) {
        case ThemeId::Techo: return {28, 16, 208, 102};
        case ThemeId::Eki:   return {6, 24, 228, 92};
        case ThemeId::Rpg:   return {12, 14, 216, 74};
        case ThemeId::Washi:
        default:             return {14, 20, 220, 94};
    }
}

void drawMessage(Canvas& c, const Theme& t, const char* utf8, uint32_t colour)
{
    if (t.id == ThemeId::Rpg) {
        text(c, 42, 101, utf8, font12(), colour);
        return;
    }
    const Area a = contentArea(t);
    text(c, a.x, a.y + a.h - 13, utf8, font12(), colour);
}

void drawFrame(Canvas& c, const Theme& t, const char* title, const char* right, const char* footerLeft,
               const char* footerRight)
{
    c.fillScreen(t.bg);
    switch (t.id) {
        case ThemeId::Eki:
            c.fillRect(0, 0, kWidth, 16, kWhite);
            text(c, 4, 2, title, font12(), kNavy);
            textRight(c, kWidth - 4, 2, right, font12(), kNavy);
            c.fillRect(0, 16, kWidth, 4, 0xF08200u);
            c.fillRect(0, kHeight - 17, kWidth, 17, kWhite);
            text(c, 6, kHeight - 15, footerLeft, font12(), kNavy);
            textRight(c, kWidth - 6, kHeight - 15, footerRight, font12(), 0xC85F00u);
            break;

        case ThemeId::Techo:
            for (int y = 14; y < kHeight; y += 17) {
                c.drawFastHLine(0, y, kWidth, t.faint);
            }
            c.drawFastVLine(22, 0, kHeight, 0xEB9696u);
            text(c, 28, 1, title, font12(), 0x786E64u);
            textRight(c, kWidth - 4, 1, right, font12(), 0x786E64u);
            text(c, 28, kHeight - 15, footerLeft, font12(), t.type);
            textRight(c, kWidth - 4, kHeight - 15, footerRight, font12(), 0x786E64u);
            break;

        case ThemeId::Rpg: {
            window(c, 2, 5, kWidth - 4, 86, t.ink);
            const int titleWidth = textWidth(c, title, font12()) + 8;
            c.fillRect(12, 5, titleWidth, 3, kBlack);
            text(c, 16, 0, title, font12(), t.ink);
            const int rightWidth = textWidth(c, right, font12()) + 8;
            c.fillRect(kWidth - 14 - rightWidth, 5, rightWidth, 3, kBlack);
            textRight(c, kWidth - 18, 0, right, font12(), t.dim);
            window(c, 2, 95, kWidth - 4, 39, t.ink);
            text(c, 42, 117, footerLeft, font12(), t.dim);
            textRight(c, kWidth - 12, 117, footerRight, font12(), t.accent);
            break;
        }

        case ThemeId::Washi:
        default:
            c.fillRect(0, 0, 6, kHeight, kShu);
            text(c, 14, 2, title, font12(), kShu);
            textRight(c, kWidth - 6, 2, right, font12(), 0x82786Eu);
            c.drawFastHLine(14, 17, kWidth - 20, t.faint);
            c.fillRoundRect(12, kHeight - 20, kWidth - 18, 18, 3, 0xF0E9DCu);
            text(c, 18, kHeight - 17, footerLeft, font12(), kSumi);
            textRight(c, kWidth - 12, kHeight - 17, footerRight, font12(), kShu);
            break;
    }
}

}  // namespace ui
