// Romaji -> kana conversion for typing Japanese on a QWERTY keyboard.
// Pure C++ with no hardware dependencies, so it is unit-tested on the host.
#pragma once

#include <string>

namespace romaji {

enum class NStyle {
    // Textbook style: "minna" -> みんな, "konnichiha" -> こんにちは.
    // ん before a vowel or y is typed with an apostrophe: "kin'en" -> きんえん.
    // m before b, p or m is ん, as written on station signs: "shimbashi" -> しんばし.
    Hepburn,
    // PC input method style: "nn" is always ん, so "minnna" -> みんな and "kinnenn" -> きんえん.
    Ime,
};

struct Options {
    NStyle nStyle = NStyle::Hepburn;
    // Turn , . ? ! [ ] into Japanese punctuation. "-" always becomes the long vowel mark ー.
    bool punctuation = true;
};

struct Result {
    std::string kana;     // converted text, hiragana, UTF-8
    std::string pending;  // trailing letters that cannot be decided yet ("k", "sh", "n")
};

// Converts `input` (ASCII romaji, any case) to hiragana.
// With flush = false the undecidable tail is returned in `pending`, for live display while typing.
// With flush = true the tail is resolved: a trailing "n" becomes ん and other leftovers are kept as typed.
Result convert(const std::string& input, const Options& options = Options(), bool flush = false);

// Hiragana -> katakana. Everything else passes through unchanged.
std::string toKatakana(const std::string& text);

// How to type one kana unit: a single hiragana (し) or one with a small kana (しゃ, てぃ, ふぁ).
// Taken from the conversion table, so typing the answer gives the unit back. Where the table
// has several spellings, the textbook one wins: shi, chi, tsu, fu, ji, sha, che.
// Empty when the table has no such unit. ん, っ and ー are not units: how they are typed depends
// on what follows.
std::string spelling(const std::string& hiraganaUnit);

}  // namespace romaji
