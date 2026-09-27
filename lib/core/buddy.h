// What the buddy says. The lines are written in content/buddy.tsv.
#pragma once

#include <cstdint>

#include "deck.h"

namespace buddy {

// One of the lines for a mood ("greeting", "right", "wrong", "almost", "streak", "start",
// "finish", "back", "low-battery", "idle"), chosen by `pick`. nullptr if the mood has no lines.
const deck::BuddyLine* say(const char* mood, uint32_t pick);

}  // namespace buddy
