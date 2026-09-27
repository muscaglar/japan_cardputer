// Drawing pieces shared by the screens.
#pragma once

#include <string>

#include "theme.h"

namespace ui {

struct PitchStyle {
    const lgfx::IFont* font = nullptr;  // defaults to the 16 px font
    uint32_t ink            = 0;
    uint32_t line           = 0;
    uint32_t particleInk    = 0;
};

// Draws kana with its pitch pattern: a line over the high beats, a hook where the pitch falls.
// accent < 0 draws the kana alone. `whisperedBeat` marks one beat whose vowel is whispered with
// dots underneath (-1 for none). Returns the x position after the last character.
int pitchText(Canvas& c, int x, int y, const std::string& kanaText, int accent, const PitchStyle& style,
              const std::string& particle = std::string(), int whisperedBeat = -1);

// The buddy. `secondEye` is painted once the owner's goal is reached.
void daruma(Canvas& c, int centreX, int centreY, bool small = false, bool secondEye = false);

// A round red stamp with one character, as collected at stations.
void stamp(Canvas& c, int centreX, int centreY, const char* character, uint32_t colour, uint32_t paper);

// Speech bubble with its tail on the left side.
void bubble(Canvas& c, int x, int y, int w, int h, uint32_t fill);

}  // namespace ui
