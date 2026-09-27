// When a card comes back. Days are counted by the device's own day number, because it has no
// clock: the owner confirms the day at the first start of each day.
#pragma once

#include <cstdint>

namespace srs {

enum class Stage : uint8_t {
    New,       // never answered
    Learning,  // being learnt today; comes back within the session
    Review,    // comes back after `interval` days
};

enum class Grade : uint8_t {
    Again,  // wrong
    Hard,   // right after a look at the romaji, or almost right
    Good,   // right
    Known,  // right at first sight, before it was taught: the learning is spared
};

struct Card {
    uint16_t due      = 0;    // day number on which it is due
    uint16_t interval = 0;    // days
    uint8_t ease      = 250;  // percent, 130 to 300
    Stage stage       = Stage::New;
    uint8_t streak    = 0;    // right answers in a row while learning
    uint8_t lapses    = 0;    // times it was forgotten after it had been learnt
};

constexpr uint8_t kGraduateAfter    = 2;    // right answers in a row that end the learning stage
constexpr uint16_t kKnownInterval   = 4;    // days until a card known at first sight is asked again
constexpr uint16_t kLongestInterval = 365;

// The card after an answer given on day `today`.
Card answer(const Card& card, Grade grade, uint16_t today);

// Whether the card should be shown on day `today`. New cards are never due; they are introduced.
bool due(const Card& card, uint16_t today);

}  // namespace srs
