// Kana helpers shared by the drills: beats, scripts and a romaji rendering for readers whose
// kana is still shaky. Pure C++, no hardware.
#pragma once

#include <string>
#include <vector>

namespace kana {

// Splits kana into beats (morae). きゃ is one beat; っ, ん and ー are one beat each.
std::vector<std::string> beats(const std::string& text);

// Katakana -> hiragana. Everything else passes through unchanged.
std::string toHiragana(const std::string& text);

// Hiragana -> katakana. Everything else passes through unchanged.
std::string toKatakana(const std::string& text);

// Romaji for a kana string, as a textbook writes it and as the keyboard accepts it:
// しんばし -> shinbashi, きっぷ -> kippu, とうきょう -> toukyou, チェックイン -> chekkuin.
// The spellings come from the conversion table, so typing what is shown gives the kana back.
// The long mark is shown as the vowel it lengthens (らーめん -> raamen), which the marking
// accepts as the same answer.
// doubledN: write every ん as nn, for the keyboard style in which n alone is never ん.
std::string toRomaji(const std::string& text, bool doubledN = false);

// Number of Unicode characters in a UTF-8 string.
size_t length(const std::string& text);

}  // namespace kana
