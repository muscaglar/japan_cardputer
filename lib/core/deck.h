// The things to learn. Decks are written as tables in content/decks/, checked and compiled into
// deck_data.cpp by tools/build_decks.py. Nothing here is loaded at run time, so the first cards
// need no memory card.
#pragma once

#include <cstddef>
#include <cstdint>

namespace deck {

enum class Kind : uint8_t {
    Kana,     // prompt: one kana or a combination. Answer: its reading.
    Word,     // prompt: a word as printed, in kanji or katakana. Answer: how it is read.
    Counter,  // prompt: a quantity such as "ビール × 3". Answer: how it is said.
    Number,   // prompt: a number, price, time or date. Answer: how it is read.
};

struct Item {
    const char* id;        // stable across builds, for example "sign-seisanki"
    const char* prompt;    // what is shown
    const char* reading;   // the main answer in kana, shown with the result
    const char* accepted;  // further right answers in kana, separated by '|'. Empty if none.
    const char* gloss;     // the meaning in English
    const char* note;      // one short line shown with the result. Empty if none.
    int8_t accent;         // pitch accent number of `reading`. -1 when unknown.
    uint8_t level;         // 1 kana only, 2 common kanji with help, 3 kanji without help
    Kind kind;
};

struct Deck {
    const char* id;      // "kana", "katakana-words", "signs", "counters", "numbers"
    const char* nameJa;  // in kana, for the menu
    const char* nameEn;
    const Item* items;
    uint16_t count;
};

size_t count();
const Deck& at(size_t index);
const Deck* find(const char* deckId);
const Item* findItem(const char* itemId);

// A number that stands for an item id in the progress files. The same id always gives the same
// number (FNV-1a, 32 bit).
uint32_t key(const char* itemId);

// One thing the buddy on the home screen can say. The lines are written in content/buddy.tsv and
// compiled into deck_data.cpp as kBuddyLines and kBuddyLineCount.
struct BuddyLine {
    const char* id;
    const char* mood;  // when it is said: "greeting", "right", "low-battery", ...
    const char* ja;    // kana, with spaces between the words
    const char* en;
};

}  // namespace deck
