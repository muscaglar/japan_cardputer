#include "deck.h"

#include <cstring>

// Written by tools/build_decks.py into deck_data.cpp.
extern const deck::Deck kDeckTable[];
extern const size_t kDeckTableSize;

namespace deck {

size_t count()
{
    return kDeckTableSize;
}

const Deck& at(size_t index)
{
    return kDeckTable[index < kDeckTableSize ? index : 0];
}

const Deck* find(const char* deckId)
{
    if (!deckId) {
        return nullptr;
    }
    for (size_t i = 0; i < kDeckTableSize; ++i) {
        if (std::strcmp(kDeckTable[i].id, deckId) == 0) {
            return &kDeckTable[i];
        }
    }
    return nullptr;
}

const Item* findItem(const char* itemId)
{
    if (!itemId) {
        return nullptr;
    }
    for (size_t i = 0; i < kDeckTableSize; ++i) {
        const Deck& d = kDeckTable[i];
        for (uint16_t k = 0; k < d.count; ++k) {
            if (std::strcmp(d.items[k].id, itemId) == 0) {
                return &d.items[k];
            }
        }
    }
    return nullptr;
}

uint32_t key(const char* itemId)
{
    uint32_t hash = 2166136261u;
    if (itemId) {
        for (const char* p = itemId; *p; ++p) {
            hash ^= static_cast<unsigned char>(*p);
            hash *= 16777619u;
        }
    }
    return hash;
}

}  // namespace deck
