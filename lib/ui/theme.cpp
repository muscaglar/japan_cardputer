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
    {ThemeId::Rpg, "rpg", "ゲーム", "Game", kBlack, kWhite, 0xA0A0A0u, 0x5A5A5Au, 0xFFDC5Au, 0x78FF8Cu,
     0xFF6E6Eu, 0xFFB450u, 0x282846u, kWhite, kWhite, kBlack, kWhite, 0xA0A0A0u, 12, 16, 95},
    {ThemeId::Washi, "washi", "和紙", "Paper", 0xFDFAF3u, kSumi, 0x6E645Fu, 0xE1D7C8u, kShu, 0x1E7846u,
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
    c.setTextSize(1);
    return c.textWidth(utf8, font);
}

bool hasGlyphs(const lgfx::IFont* font, const char* utf8)
{
    lgfx::FontMetrics metrics;
    font->getDefaultMetric(&metrics);
    const unsigned char* p = reinterpret_cast<const unsigned char*>(utf8);
    while (*p) {
        uint32_t code = *p;
        int extra     = 0;
        if ((code & 0xE0) == 0xC0) {
            code &= 0x1F;
            extra = 1;
        } else if ((code & 0xF0) == 0xE0) {
            code &= 0x0F;
            extra = 2;
        } else if ((code & 0xF8) == 0xF0) {
            code &= 0x07;
            extra = 3;
        }
        ++p;
        while (extra-- > 0 && *p) {
            code = (code << 6) | (*p & 0x3F);
            ++p;
        }
        if (code > 0xFFFF || !font->updateFontMetric(&metrics, static_cast<uint16_t>(code))) {
            return false;
        }
    }
    return true;
}

Face face16()
{
    return Face{font16(), 1, 16};
}

Face face24()
{
    return Face{font24(), 1, 24};
}

int faceWidth(Canvas& c, const char* utf8, const Face& face)
{
    c.setTextSize(1);
    return c.textWidth(utf8, face.font) * face.scale;
}

int faceText(Canvas& c, int x, int y, const char* utf8, const Face& face, uint32_t colour)
{
    c.setFont(face.font);
    c.setTextSize(face.scale);
    c.setTextWrap(false);
    c.setTextDatum(top_left);
    c.setTextColor(colour);
    c.setCursor(x, y);
    c.print(utf8);
    const int end = c.getCursorX();
    c.setTextSize(1);
    return end;
}

int faceCentre(Canvas& c, int centreX, int y, const char* utf8, const Face& face, uint32_t colour)
{
    return faceText(c, centreX - faceWidth(c, utf8, face) / 2, y, utf8, face, colour);
}

Face fitFace(Canvas& c, const char* utf8, int width, int tallest)
{
    const Face choices[] = {
        {fontBig(), 2, 64}, {font24(), 2, 48}, {fontBig(), 1, 32}, {font16(), 2, 32}, {font24(), 1, 24},
    };
    for (const Face& choice : choices) {
        if (choice.height <= tallest && hasGlyphs(choice.font, utf8) && faceWidth(c, utf8, choice) <= width) {
            return choice;
        }
    }
    return face16();
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

int linesNeeded(Canvas& c, int width, const char* utf8, const lgfx::IFont* font)
{
    std::string line;
    std::string word;
    int lines     = 0;
    const char* p = utf8;
    while (true) {
        const bool end = (*p == 0);
        if (end || *p == ' ') {
            const std::string candidate = line.empty() ? word : line + " " + word;
            if (!line.empty() && textWidth(c, candidate.c_str(), font) > width) {
                ++lines;
                line = word;
            } else {
                line = candidate;
            }
            word.clear();
            if (end) {
                return lines + (line.empty() ? 0 : 1);
            }
        } else {
            word.push_back(*p);
        }
        ++p;
    }
}

std::string headThatFits(Canvas& c, const std::string& utf8, const lgfx::IFont* font, int width)
{
    if (textWidth(c, utf8.c_str(), font) <= width) {
        return utf8;
    }
    std::string head = utf8;
    while (!head.empty()) {
        // drop one whole character from the end
        head.pop_back();
        while (!head.empty() && (static_cast<unsigned char>(head.back()) & 0xC0) == 0x80) {
            head.pop_back();
        }
        if (!head.empty() && (static_cast<unsigned char>(head.back()) & 0xC0) == 0xC0) {
            head.pop_back();
            continue;
        }
        const std::string shown = head + "…";
        if (textWidth(c, shown.c_str(), font) <= width) {
            return shown;
        }
    }
    return std::string();
}

Area contentArea(const Theme& t, bool header)
{
    switch (t.id) {
        case ThemeId::Techo: return header ? Area{20, 20, 216, 96} : Area{20, 2, 216, 114};
        case ThemeId::Eki:   return header ? Area{6, 23, 228, 93} : Area{6, 2, 228, 114};
        case ThemeId::Rpg:   return header ? Area{10, 20, 220, 88} : Area{10, 8, 220, 100};
        case ThemeId::Washi:
        default:             return header ? Area{14, 21, 220, 94} : Area{14, 2, 220, 113};
    }
}

void drawMessage(Canvas& c, const Theme& t, const char* utf8, uint32_t colour)
{
    const Area a = contentArea(t);
    textCentre(c, a.x + a.w / 2, a.y + a.h - 17, utf8, font16(), colour);
}

uint32_t headerInk(const Theme& t)
{
    switch (t.id) {
        case ThemeId::Techo: return 0x786E64u;
        case ThemeId::Eki:   return kNavy;
        case ThemeId::Rpg:   return t.ink;
        default:             return 0x82786Eu;
    }
}

uint32_t headerAccent(const Theme& t)
{
    return (t.id == ThemeId::Eki) ? 0xC85F00u : t.accent;
}

void drawFrame(Canvas& c, const Theme& t, const char* title, const char* right, const char* footerLeft,
               const char* footerRight)
{
    const bool header = (title != nullptr);
    if (!right) {
        right = "";
    }
    c.fillScreen(t.bg);
    switch (t.id) {
        case ThemeId::Eki:
            if (header) {
                c.fillRect(0, 0, kWidth, 18, kWhite);
                text(c, 4, 1, title, font16(), kNavy);
                textRight(c, kWidth - 4, 1, right, font16(), kNavy);
                c.fillRect(0, 18, kWidth, 3, 0xF08200u);
            }
            c.fillRect(0, kHeight - 18, kWidth, 18, kWhite);
            text(c, 6, kHeight - 17, footerLeft, font16(), kNavy);
            textRight(c, kWidth - 6, kHeight - 17, footerRight, font16(), 0xC85F00u);
            break;

        case ThemeId::Techo:
            for (int y = 18; y < kHeight; y += 19) {
                c.drawFastHLine(0, y, kWidth, t.faint);
            }
            c.drawFastVLine(14, 0, kHeight, 0xEB9696u);
            if (header) {
                text(c, 20, 1, title, font16(), 0x786E64u);
                textRight(c, kWidth - 4, 1, right, font16(), 0x786E64u);
            }
            text(c, 20, kHeight - 18, footerLeft, font16(), t.type);
            textRight(c, kWidth - 4, kHeight - 18, footerRight, font16(), 0x786E64u);
            break;

        case ThemeId::Rpg: {
            const int top = header ? 9 : 2;
            window(c, 2, top, kWidth - 4, 112 - top, t.ink);
            if (header) {
                const int titleWidth = textWidth(c, title, font16()) + 8;
                c.fillRect(10, top, titleWidth, 3, kBlack);
                text(c, 14, 1, title, font16(), t.ink);
                if (right[0] != 0) {
                    const int rightWidth = textWidth(c, right, font16()) + 8;
                    c.fillRect(kWidth - 10 - rightWidth, top, rightWidth, 3, kBlack);
                    textRight(c, kWidth - 14, 1, right, font16(), t.dim);
                }
            }
            window(c, 2, 114, kWidth - 4, 21, t.ink);
            text(c, 10, 116, footerLeft, font16(), t.dim);
            textRight(c, kWidth - 10, 116, footerRight, font16(), t.accent);
            break;
        }

        case ThemeId::Washi:
        default:
            c.fillRect(0, 0, 6, kHeight, kShu);
            if (header) {
                text(c, 14, 1, title, font16(), kShu);
                textRight(c, kWidth - 6, 1, right, font16(), 0x82786Eu);
                c.drawFastHLine(14, 18, kWidth - 20, t.faint);
            }
            c.fillRoundRect(12, kHeight - 19, kWidth - 18, 18, 3, 0xF0E9DCu);
            text(c, 18, kHeight - 18, footerLeft, font16(), kSumi);
            textRight(c, kWidth - 12, kHeight - 18, footerRight, font16(), kShu);
            break;
    }
}

}  // namespace ui
