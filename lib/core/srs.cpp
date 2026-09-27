#include "srs.h"

namespace srs {

namespace {

constexpr uint8_t kEaseLowest   = 130;
constexpr uint8_t kEaseHardStep = 15;
constexpr uint8_t kEaseLapse    = 20;

uint16_t capped(uint32_t days)
{
    if (days < 1) {
        return 1;
    }
    return days > kLongestInterval ? kLongestInterval : static_cast<uint16_t>(days);
}

uint16_t dayAfter(uint16_t today, uint16_t interval)
{
    const uint32_t day = static_cast<uint32_t>(today) + interval;
    return day > 0xFFFF ? 0xFFFF : static_cast<uint16_t>(day);
}

uint8_t lowered(uint8_t ease, uint8_t by)
{
    return (ease > kEaseLowest + by) ? static_cast<uint8_t>(ease - by) : kEaseLowest;
}

Card learning(Card card, Grade grade, uint16_t today)
{
    card.stage = Stage::Learning;
    card.due   = today;
    if (grade == Grade::Again) {
        card.streak = 0;
        return card;
    }
    if (grade == Grade::Hard) {
        return card;
    }
    ++card.streak;
    if (card.streak >= kGraduateAfter) {
        card.stage    = Stage::Review;
        card.streak   = 0;
        card.interval = capped(card.interval);  // 1 for a new card, what was kept for a forgotten one
        card.due      = dayAfter(today, card.interval);
    }
    return card;
}

Card review(Card card, Grade grade, uint16_t today)
{
    if (grade == Grade::Again) {
        if (card.lapses < 255) {
            ++card.lapses;
        }
        card.ease     = lowered(card.ease, kEaseLapse);
        card.interval = capped(card.interval / 4u);
        card.stage    = Stage::Learning;
        card.streak   = 0;
        card.due      = today;
        return card;
    }
    if (grade == Grade::Hard) {
        const uint32_t longer = (static_cast<uint32_t>(card.interval) * 120u + 50u) / 100u;
        card.interval         = capped(longer > card.interval ? longer : card.interval + 1u);
        card.ease             = lowered(card.ease, kEaseHardStep);
        card.due              = dayAfter(today, card.interval);
        return card;
    }
    // Remembered. If it was answered late, half of the extra wait counts as having been earned.
    const uint32_t late   = (today > card.due) ? static_cast<uint32_t>(today - card.due) : 0u;
    const uint32_t basis2 = static_cast<uint32_t>(card.interval) * 2u + late;  // twice the basis
    const uint32_t longer = (basis2 * card.ease + 100u) / 200u;
    card.interval         = capped(longer > card.interval ? longer : card.interval + 1u);
    card.due              = dayAfter(today, card.interval);
    return card;
}

}  // namespace

Card answer(const Card& card, Grade grade, uint16_t today)
{
    if (grade == Grade::Known) {
        if (card.stage == Stage::New) {
            Card known     = card;
            known.stage    = Stage::Review;
            known.streak   = 0;
            known.interval = kKnownInterval;
            known.due      = dayAfter(today, known.interval);
            return known;
        }
        grade = Grade::Good;  // a card met before is known in the ordinary way
    }
    if (card.stage == Stage::Review) {
        return review(card, grade, today);
    }
    return learning(card, grade, today);
}

bool due(const Card& card, uint16_t today)
{
    if (card.stage == Stage::New) {
        return false;
    }
    return card.due <= today;
}

}  // namespace srs
