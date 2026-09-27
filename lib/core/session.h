// One sitting: which cards, in which order, and when it ends.
#pragma once

#include <cstdint>
#include <vector>

#include "deck.h"
#include "progress.h"
#include "srs.h"

namespace session {

struct Plan {
    uint16_t today    = 1;
    uint16_t maxCards = 12;  // a sitting ends after this many answers
    uint16_t maxNew   = 4;   // of which at most this many are cards never seen before
    uint8_t level     = 1;   // cards above this level are left out
    uint32_t seed     = 1;   // the same seed gives the same sitting
};

struct Pick {
    const deck::Deck* deck = nullptr;
    const deck::Item* item = nullptr;
    bool isNew             = false;
    bool repeat            = false;  // shown again in this sitting after a wrong answer
};

class Queue {
public:
    explicit Queue(progress::Store& store);

    // Chooses the cards: due ones first, the most overdue first, then new ones in deck order,
    // mixed so that two cards of the same deck rarely follow each other.
    void start(const Plan& plan, const std::vector<const deck::Deck*>& decks);

    // The next card. False when the sitting is over.
    bool next(Pick& pick);

    // Records the answer. A card answered wrongly comes back after three other cards, or at the
    // end if fewer are left, and does not count against maxCards again.
    void answered(const Pick& pick, srs::Grade grade);

    int asked() const { return _asked; }
    int right() const { return _right; }
    int remaining() const;

private:
    progress::Store& _store;
    std::vector<Pick> _cards;
    size_t _position = 0;
    Plan _plan;
    int _asked = 0;
    int _right = 0;
};

}  // namespace session
