#include "buddy.h"

#include <cstring>

// Written by tools/build_decks.py into deck_data.cpp.
extern const deck::BuddyLine kBuddyLines[];
extern const size_t kBuddyLineCount;

namespace buddy {

const deck::BuddyLine* say(const char* mood, uint32_t pick)
{
    size_t matching = 0;
    for (size_t i = 0; i < kBuddyLineCount; ++i) {
        if (std::strcmp(kBuddyLines[i].mood, mood) == 0) {
            ++matching;
        }
    }
    if (matching == 0) {
        return nullptr;
    }
    size_t wanted = pick % matching;
    for (size_t i = 0; i < kBuddyLineCount; ++i) {
        if (std::strcmp(kBuddyLines[i].mood, mood) == 0) {
            if (wanted == 0) {
                return &kBuddyLines[i];
            }
            --wanted;
        }
    }
    return nullptr;
}

}  // namespace buddy
