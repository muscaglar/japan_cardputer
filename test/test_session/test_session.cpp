#include <unity.h>

#include <map>
#include <string>
#include <vector>

#include "session.h"

using srs::Grade;

namespace {

class Memory : public core::Storage {
public:
    bool load(const char* name, std::string& text) override
    {
        const auto found = files.find(name);
        if (found == files.end()) {
            return false;
        }
        text = found->second;
        return true;
    }
    bool save(const char* name, const std::string& text) override
    {
        files[name] = text;
        return true;
    }
    bool append(const char* name, const std::string& line) override
    {
        files[name] += line + "\n";
        return true;
    }
    std::map<std::string, std::string> files;
};

#define ITEM(id, level) {id, id, "あ", "", "", "", -1, level, deck::Kind::Word}

const deck::Item kSigns[] = {ITEM("s1", 1), ITEM("s2", 1), ITEM("s3", 2), ITEM("s4", 1), ITEM("s5", 1), ITEM("s6", 1)};
const deck::Item kWords[] = {ITEM("w1", 1), ITEM("w2", 1), ITEM("w3", 1), ITEM("w4", 3)};
const deck::Item kCount[] = {ITEM("c1", 1), ITEM("c2", 1)};

const deck::Deck kSignDeck  = {"signs", "かんばん", "signs", kSigns, 6};
const deck::Deck kWordDeck  = {"words", "ことば", "words", kWords, 4};
const deck::Deck kCountDeck = {"count", "かぞえかた", "counters", kCount, 2};

std::vector<const deck::Deck*> all()
{
    return {&kSignDeck, &kWordDeck, &kCountDeck};
}

// Plays a sitting, answering with `grade`, and returns the ids in the order shown.
std::string play(session::Queue& queue, Grade grade, int limit = 100)
{
    std::string order;
    session::Pick pick;
    while (limit-- > 0 && queue.next(pick)) {
        if (!order.empty()) {
            order += " ";
        }
        order += pick.item->id;
        if (pick.repeat) {
            order += "'";
        }
        queue.answered(pick, grade);
    }
    return order;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_first_sitting_brings_new_cards_from_each_deck_in_turn()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew = 4;
    queue.start(plan, all());
    TEST_ASSERT_EQUAL_INT(4, queue.remaining());

    session::Pick pick;
    std::string first;
    std::string decks;
    while (queue.next(pick)) {
        TEST_ASSERT_TRUE(pick.isNew);
        TEST_ASSERT_FALSE(pick.repeat);
        first += pick.item->id;
        first += " ";
        decks += pick.deck->id[0];
    }
    // seed 1 with three decks starts the turn with the second deck
    TEST_ASSERT_EQUAL_STRING("w1 c1 s1 w2 ", first.c_str());
    TEST_ASSERT_EQUAL_STRING("wcsw", decks.c_str());
}

void test_right_answers_bring_each_new_card_back_once()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew = 3;
    plan.seed   = 3;
    queue.start(plan, all());
    const std::string order = play(queue, Grade::Good);
    TEST_ASSERT_EQUAL_STRING("s1 w1 c1 s1' w1' c1'", order.c_str());
    TEST_ASSERT_EQUAL_INT(6, queue.asked());
    TEST_ASSERT_EQUAL_INT(6, queue.right());
    TEST_ASSERT_EQUAL_UINT(3, store.learnt());
    TEST_ASSERT_EQUAL_INT(0, queue.remaining());
}

void test_a_wrong_answer_comes_back_after_three_other_cards()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew   = 6;
    plan.maxCards = 6;
    plan.seed     = 3;
    queue.start(plan, all());

    session::Pick pick;
    TEST_ASSERT_TRUE(queue.next(pick));
    const std::string first = pick.item->id;
    queue.answered(pick, Grade::Again);
    std::string between;
    for (int i = 0; i < 3; ++i) {
        TEST_ASSERT_TRUE(queue.next(pick));
        TEST_ASSERT_TRUE(first != pick.item->id);
        queue.answered(pick, Grade::Hard);  // stays in learning, waits further on
    }
    TEST_ASSERT_TRUE(queue.next(pick));
    TEST_ASSERT_EQUAL_STRING(first.c_str(), pick.item->id);
    TEST_ASSERT_TRUE(pick.repeat);
}

void test_a_card_never_answered_right_does_not_keep_the_sitting_going()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew = 1;
    queue.start(plan, all());
    const std::string order = play(queue, Grade::Again);
    TEST_ASSERT_EQUAL_STRING("w1 w1' w1' w1'", order.c_str());
    TEST_ASSERT_EQUAL_INT(4, queue.asked());
    TEST_ASSERT_EQUAL_INT(0, queue.right());
}

void test_levels_above_the_plan_are_left_out()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew   = 20;
    plan.maxCards = 20;
    plan.level    = 1;
    plan.seed     = 3;
    queue.start(plan, all());
    session::Pick pick;
    int count = 0;
    while (queue.next(pick)) {
        TEST_ASSERT_TRUE(pick.item->level <= 1);
        ++count;
    }
    TEST_ASSERT_EQUAL_INT(10, count);  // s3 and w4 are above the level
}

void test_due_cards_come_first_the_longest_overdue_first()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    // learnt on different days, all due by day 10
    for (const char* id : {"s1", "w1", "c1"}) {
        store.record(deck::key(id), Grade::Good, 1);
    }
    store.record(deck::key("s1"), Grade::Good, 1);  // due day 2
    store.record(deck::key("w1"), Grade::Good, 4);  // due day 5
    store.record(deck::key("c1"), Grade::Good, 7);  // due day 8

    session::Queue queue(store);
    session::Plan plan;
    plan.today    = 10;
    plan.maxCards = 3;
    plan.maxNew   = 3;
    queue.start(plan, all());
    session::Pick pick;
    std::string order;
    while (queue.next(pick)) {
        TEST_ASSERT_FALSE(pick.isNew);
        order += pick.item->id;
        order += " ";
    }
    TEST_ASSERT_EQUAL_STRING("s1 w1 c1 ", order.c_str());
}

void test_same_deck_cards_are_kept_apart_when_possible()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    plan.maxNew   = 8;
    plan.maxCards = 8;
    plan.seed     = 3;
    queue.start(plan, all());
    session::Pick pick;
    const deck::Deck* previous = nullptr;
    int neighbours             = 0;
    int count                  = 0;
    while (queue.next(pick)) {
        if (pick.deck == previous) {
            ++neighbours;
        }
        previous = pick.deck;
        ++count;
    }
    TEST_ASSERT_EQUAL_INT(8, count);
    TEST_ASSERT_TRUE(neighbours <= 1);
}

void test_the_same_plan_gives_the_same_sitting()
{
    Memory a;
    Memory b;
    progress::Store first(a);
    progress::Store second(b);
    first.load();
    second.load();
    session::Queue one(first);
    session::Queue two(second);
    session::Plan plan;
    plan.seed = 42;
    one.start(plan, all());
    two.start(plan, all());
    TEST_ASSERT_EQUAL_STRING(play(one, Grade::Good).c_str(), play(two, Grade::Good).c_str());
}

void test_nothing_to_do()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    session::Queue queue(store);
    session::Plan plan;
    queue.start(plan, {});
    session::Pick pick;
    TEST_ASSERT_FALSE(queue.next(pick));
    TEST_ASSERT_EQUAL_INT(0, queue.remaining());
    queue.answered(pick, Grade::Good);  // no card: ignored
    TEST_ASSERT_EQUAL_INT(0, queue.asked());
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_first_sitting_brings_new_cards_from_each_deck_in_turn);
    RUN_TEST(test_right_answers_bring_each_new_card_back_once);
    RUN_TEST(test_a_wrong_answer_comes_back_after_three_other_cards);
    RUN_TEST(test_a_card_never_answered_right_does_not_keep_the_sitting_going);
    RUN_TEST(test_levels_above_the_plan_are_left_out);
    RUN_TEST(test_due_cards_come_first_the_longest_overdue_first);
    RUN_TEST(test_same_deck_cards_are_kept_apart_when_possible);
    RUN_TEST(test_the_same_plan_gives_the_same_sitting);
    RUN_TEST(test_nothing_to_do);
    return UNITY_END();
}
