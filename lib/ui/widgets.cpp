#include "widgets.h"

#include <vector>

#include "kana.h"
#include "pitch.h"

namespace ui {

namespace {

constexpr uint32_t kSumi   = 0x18181Cu;
constexpr uint32_t kBody   = 0xC82824u;
constexpr uint32_t kFace   = 0xFAF0E1u;
constexpr uint32_t kGold   = 0xF0BE3Cu;

struct Span {
    int from;
    int to;
    bool high;
};

}  // namespace

int pitchText(Canvas& c, int x, int y, const std::string& kanaText, int accent, const PitchStyle& style,
              const std::string& particle, int whisperedBeat)
{
    const lgfx::IFont* font = style.font ? style.font : font16();
    const std::vector<std::string> beats = kana::beats(kanaText);
    const std::vector<bool> high         = pitch::heights(static_cast<int>(beats.size()), accent);
    const bool known                     = !high.empty();

    std::vector<Span> spans;
    int cursor = x;
    for (size_t i = 0; i < beats.size(); ++i) {
        const int width = textWidth(c, beats[i].c_str(), font);
        text(c, cursor, y, beats[i].c_str(), font, style.ink);
        if (static_cast<int>(i) == whisperedBeat) {
            c.setFont(font);
            const int under = y + c.fontHeight();
            for (int dot = cursor + 2; dot < cursor + width - 2; dot += 3) {
                c.drawPixel(dot, under, style.particleInk);
            }
        }
        spans.push_back({cursor, cursor + width, known && high[i]});
        cursor += width;
    }
    const int wordEnd = cursor;
    if (!particle.empty()) {
        const int width = textWidth(c, particle.c_str(), font);
        text(c, cursor, y, particle.c_str(), font, style.particleInk);
        spans.push_back({cursor, cursor + width, known && pitch::particleIsHigh(accent)});
        cursor += width;
    }
    if (!known) {
        return cursor;
    }

    const int top = y - 4;
    size_t i      = 0;
    while (i < spans.size()) {
        if (!spans[i].high) {
            ++i;
            continue;
        }
        const int start = spans[i].from;
        while (i + 1 < spans.size() && spans[i + 1].high) {
            ++i;
        }
        const int end = spans[i].to;
        c.fillRect(start + 1, top, end - start - 1, 2, style.line);
        if (start > x) {
            c.fillRect(start + 1, top, 2, 5, style.line);  // the rise
        }
        if (accent != 0 && end <= wordEnd + 1) {
            c.fillRect(end - 2, top, 2, 7, style.line);    // the fall
        }
        ++i;
    }
    return cursor;
}

void daruma(Canvas& c, int cx, int cy, bool small, bool secondEye)
{
    if (small) {
        c.fillRoundRect(cx - 12, cy - 13, 24, 27, 11, kBody);
        c.fillRoundRect(cx - 8, cy - 9, 16, 13, 5, kFace);
        c.fillRect(cx - 6, cy - 6, 4, 1, kSumi);
        c.fillRect(cx + 2, cy - 6, 4, 1, kSumi);
        c.fillRoundRect(cx + 2, cy - 4, 4, 4, 2, kSumi);
        if (secondEye) {
            c.fillRoundRect(cx - 6, cy - 4, 4, 4, 2, kSumi);
        } else {
            c.drawRoundRect(cx - 6, cy - 4, 4, 4, 2, kSumi);
        }
        c.fillRect(cx - 2, cy + 1, 4, 1, kSumi);
        c.fillRect(cx - 5, cy + 7, 10, 1, kGold);
        c.fillRect(cx - 4, cy + 10, 8, 1, kGold);
        return;
    }
    c.fillRoundRect(cx - 17, cy - 19, 34, 38, 15, kBody);
    c.fillRoundRect(cx - 12, cy - 13, 24, 19, 8, kFace);
    c.fillRect(cx - 9, cy - 8, 6, 2, kSumi);
    c.fillRect(cx + 3, cy - 8, 6, 2, kSumi);
    // By custom the daruma's own left eye, on the viewer's right, is painted when the goal is
    // set, and the other one when it is reached.
    c.fillRoundRect(cx + 3, cy - 5, 6, 6, 3, kSumi);
    if (secondEye) {
        c.fillRoundRect(cx - 9, cy - 5, 6, 6, 3, kSumi);
    } else {
        c.drawRoundRect(cx - 9, cy - 5, 6, 6, 3, kSumi);
    }
    c.fillRect(cx - 3, cy + 2, 6, 1, kSumi);
    c.fillRect(cx - 8, cy + 9, 16, 2, kGold);
    c.fillRect(cx - 6, cy + 13, 12, 2, kGold);
}

void stamp(Canvas& c, int cx, int cy, const char* character, uint32_t colour, uint32_t paper)
{
    c.fillCircle(cx, cy, 14, paper);
    c.drawCircle(cx, cy, 14, colour);
    c.drawCircle(cx, cy, 13, colour);
    textCentre(c, cx, cy - 8, character, font16(), colour);
}

void bubble(Canvas& c, int x, int y, int w, int h, uint32_t fill, uint32_t edge)
{
    c.fillRoundRect(x, y, w, h, 5, fill);
    c.fillRect(x - 4, y + 16, 6, 6, fill);
    if (edge != fill) {
        c.drawRoundRect(x, y, w, h, 5, edge);
        c.drawFastVLine(x - 4, y + 16, 6, edge);
        c.drawFastHLine(x - 4, y + 16, 4, edge);
        c.drawFastHLine(x - 4, y + 21, 4, edge);
        c.drawFastVLine(x, y + 17, 4, fill);
    }
}

std::string capitalised(const char* text)
{
    std::string out = text ? text : "";
    if (!out.empty() && out[0] >= 'a' && out[0] <= 'z') {
        out[0] = static_cast<char>(out[0] - 'a' + 'A');
    }
    return out;
}

}  // namespace ui
