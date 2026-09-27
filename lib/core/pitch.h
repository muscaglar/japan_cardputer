// Pitch accent of a word as the standard dictionaries number it.
//   0  flat: the first beat is low, the rest high, and a following particle stays high
//   1  the first beat is high, then the pitch falls
//   k  the pitch rises after the first beat and falls after beat k
// Pure C++, no hardware.
#pragma once

#include <vector>

namespace pitch {

constexpr int kUnknown = -1;

// One entry per beat: true where the beat is high. Empty when the accent is unknown or does not
// fit the word.
std::vector<bool> heights(int beatCount, int accent);

// Whether a particle attached to the word is high (only after a flat word).
bool particleIsHigh(int accent);

}  // namespace pitch
