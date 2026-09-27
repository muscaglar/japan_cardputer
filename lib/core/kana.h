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

// Hepburn romaji for a kana string, for display only: しんばし -> shinbashi, きっぷ -> kippu,
// らーめん -> raamen, とうきょう -> toukyou. Long vowels are written as typed, so that the
// romaji shown is also what the keyboard accepts.
std::string toRomaji(const std::string& text);

// Number of Unicode characters in a UTF-8 string.
size_t length(const std::string& text);

}  // namespace kana
