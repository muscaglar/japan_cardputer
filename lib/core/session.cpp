#include "session.h"

#include <algorithm>

namespace session {

namespace {

constexpr size_t kComesBackAfter = 3;  // other cards shown before a card is repeated
constexpr int kMostRepeats       = 3;  // in one sitting, per card

struct Candidate {
    Pick pick;
    size_t deckIndex;
    uint32_t overdue;
};

}  // namespace

uint8_t openStage(const progress::Store& store, const std::vector<const deck::Deck*>& decks, uint8_t level)
{
    uint8_t lowest = 0;
    for (const deck::Deck* deck : decks) {
        if (!deck || (lowest != 0 && deck->stage >= lowest)) {
            continue;
        }
        for (uint16_t i = 0; i < deck->count; ++i) {
            const deck::Item& item = deck->items[i];
            if (item.level <= level && store.get(deck::key(item.id)).stage == srs::Stage::New) {
                lowest = deck->stage;
                break;
            }
        }
    }
    return lowest;
}

Queue::Queue(progress::Store& store) : _store(store) {}

void Queue::start(const Plan& plan, const std::vector<const deck::Deck*>& decks)
{
    _plan     = plan;
    _position = 0;
    _asked    = 0;
    _right    = 0;
    _cards.clear();

    // 1. What is due, the longest overdue first.
    std::vector<Candidate> due;
    for (size_t d = 0; d < decks.size(); ++d) {
        const deck::Deck* deck = decks[d];
        for (uint16_t i = 0; deck && i < deck->count; ++i) {
            const deck::Item& item = deck->items[i];
            if (item.level > plan.level) {
                continue;
            }
            const srs::Card card = _store.get(deck::key(item.id));
            if (srs::due(card, plan.today)) {
                Candidate c;
                c.pick.deck  = deck;
                c.pick.item  = &item;
                c.deckIndex  = d;
                c.overdue    = static_cast<uint32_t>(plan.today - card.due);
                due.push_back(c);
            }
        }
    }
    std::stable_sort(due.begin(), due.end(),
                     [](const Candidate& a, const Candidate& b) { return a.overdue > b.overdue; });
    if (due.size() > plan.maxCards) {
        due.resize(plan.maxCards);
    }

    // 2. New cards, one deck after the other in turn, each deck in its own order. In a course
    //    they come from the lowest stage that still has unseen cards. Kana count for less than
    //    words: a sitting takes maxNewKana of them where it would take maxNew words.
    std::vector<Candidate> chosen = due;
    std::vector<uint16_t> cursor(decks.size(), 0);
    const uint8_t stage = plan.course ? openStage(_store, decks, plan.level) : 0;
    // A sitting has room for maxNew words or maxNewKana kana: counted in parts of that room.
    const uint32_t room = static_cast<uint32_t>(plan.maxNew) * plan.maxNewKana;
    uint32_t filled     = 0;
    bool anyLeft        = true;
    size_t rotate       = decks.empty() ? 0 : plan.seed % decks.size();
    while (anyLeft && filled < room && chosen.size() < plan.maxCards) {
        anyLeft = false;
        for (size_t step = 0; step < decks.size() && filled < room && chosen.size() < plan.maxCards; ++step) {
            const size_t d         = (step + rotate) % decks.size();
            const deck::Deck* deck = decks[d];
            if (deck && plan.course && deck->stage != stage) {
                continue;
            }
            while (deck && cursor[d] < deck->count) {
                const deck::Item& item = deck->items[cursor[d]++];
                if (item.level > plan.level) {
                    continue;
                }
                if (_store.get(deck::key(item.id)).stage != srs::Stage::New) {
                    continue;
                }
                const bool kana = (item.kind == deck::Kind::Kana);
                Candidate c;
                c.pick.deck  = deck;
                c.pick.item  = &item;
                c.pick.isNew = true;
                c.pick.probe = kana;
                c.deckIndex  = d;
                c.overdue    = 0;
                chosen.push_back(c);
                filled += kana ? plan.maxNew : plan.maxNewKana;
                anyLeft = true;
                break;
            }
        }
    }

    // 3. Keep that order, but where two cards of the same deck would follow each other and a card
    //    of another deck is waiting, let that one go first.
    std::vector<bool> used(chosen.size(), false);
    size_t previous = decks.size();
    for (size_t n = 0; n < chosen.size(); ++n) {
        size_t take = chosen.size();
        for (size_t i = 0; i < chosen.size(); ++i) {
            if (used[i]) {
                continue;
            }
            if (take == chosen.size()) {
                take = i;  // the first one waiting, in case every other card is of the same deck
            }
            if (chosen[i].deckIndex != previous) {
                take = i;
                break;
            }
        }
        used[take] = true;
        previous   = chosen[take].deckIndex;
        _cards.push_back(chosen[take].pick);
    }
}

bool Queue::next(Pick& pick)
{
    if (_position >= _cards.size()) {
        return false;
    }
    pick = _cards[_position++];
    return true;
}

void Queue::answered(const Pick& pick, srs::Grade grade)
{
    if (!pick.item) {
        return;
    }
    ++_asked;
    if (grade == srs::Grade::Good || grade == srs::Grade::Known) {
        ++_right;
    }
    const srs::Card card = _store.record(deck::key(pick.item->id), grade, _plan.today);

    // Still being learnt: it comes back in this sitting, a few cards later.
    if (card.stage != srs::Stage::Learning) {
        return;
    }
    int shown = 0;
    for (size_t i = 0; i < _position; ++i) {
        if (_cards[i].item == pick.item) {
            ++shown;
        }
    }
    for (size_t i = _position; i < _cards.size(); ++i) {
        if (_cards[i].item == pick.item) {
            return;  // already waiting
        }
    }
    if (shown > kMostRepeats) {
        return;
    }
    Pick again   = pick;
    again.isNew  = false;
    again.probe  = false;
    again.repeat = true;
    const size_t at = std::min(_position + kComesBackAfter, _cards.size());
    _cards.insert(_cards.begin() + static_cast<std::ptrdiff_t>(at), again);
}

int Queue::remaining() const
{
    return static_cast<int>(_cards.size() - _position);
}

}  // namespace session
