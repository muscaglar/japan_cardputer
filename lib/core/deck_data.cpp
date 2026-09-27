// Written by tools/build_decks.py from content/decks/*.tsv. Do not edit by hand.
#include "deck.h"

namespace {

const deck::Item kPlaceholderItems[] = {
    {"placeholder-a", "あ", "あ", "", "a", "", -1, 1, deck::Kind::Kana},
};

}  // namespace

extern const deck::Deck kDeckTable[] = {
    {"placeholder", "じゅんびちゅう", "not built yet", kPlaceholderItems, 1},
};
extern const size_t kDeckTableSize = sizeof(kDeckTable) / sizeof(kDeckTable[0]);
