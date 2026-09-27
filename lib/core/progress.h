// What the owner has learnt so far, kept across restarts.
//
// Two files. "progress.txt" is a snapshot, one card per line. "reviews.log" gets one line per
// answer and is replayed over the snapshot at start. A power cut can therefore cost at most the
// answer being written. checkpoint() folds the log into a new snapshot.
#pragma once

#include <cstdint>
#include <vector>

#include "srs.h"
#include "storage.h"

namespace progress {

class Store {
public:
    explicit Store(core::Storage& storage);

    void load();

    // The card for an item. A card that was never answered is returned as new.
    srs::Card get(uint32_t itemKey) const;

    // Applies the answer, keeps the result in memory and appends it to the log.
    // Returns the card after the answer.
    srs::Card record(uint32_t itemKey, srs::Grade grade, uint16_t today);

    // Writes the snapshot and empties the log. Called at the end of a session.
    bool checkpoint();

    size_t seen() const;                       // cards answered at least once
    size_t dueOn(uint16_t today) const;        // cards in review or learning that are due
    size_t learnt() const;                     // cards that reached the review stage

    // Forgets everything, on the device too.
    void reset();

private:
    struct Entry {
        uint32_t key;
        srs::Card card;
    };

    Entry* find(uint32_t itemKey);
    const Entry* find(uint32_t itemKey) const;
    void put(uint32_t itemKey, const srs::Card& card);

    core::Storage& _storage;
    std::vector<Entry> _entries;  // sorted by key
    size_t _logged = 0;           // lines in the log since the last snapshot
};

}  // namespace progress
