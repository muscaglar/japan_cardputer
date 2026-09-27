// Marks a typed answer against an item.
#pragma once

#include <string>

#include "deck.h"

namespace match {

enum class Verdict : uint8_t {
    Right,
    Almost,  // the same sounds with a different spelling, or one beat of length away
    Wrong,
};

enum class Slip : uint8_t {
    None,
    LongVowel,   // とうきょ for とうきょう, or おう written おお
    SmallTsu,    // きて for きって
    N,           // a missing or extra ん
    Voicing,     // か for が
    Other,
};

struct Outcome {
    Verdict verdict = Verdict::Wrong;
    Slip slip       = Slip::Other;
    std::string expected;  // the right answer nearest to what was typed, as stored in the deck
    int beat = -1;         // first beat of `expected` that differs. -1 when right.
};

// typedKana is what the romaji converter produced. It may hold stray Latin letters.
Outcome check(const std::string& typedKana, const deck::Item& item);

// Katakana to hiragana; spaces and punctuation removed; ー replaced by the vowel it lengthens.
// Two answers that normalise to the same string are the same answer.
std::string normalise(const std::string& kana);

}  // namespace match
