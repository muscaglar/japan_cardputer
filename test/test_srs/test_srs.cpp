#include <unity.h>

#include "srs.h"

using srs::Card;
using srs::Grade;
using srs::Stage;

void setUp() {}
void tearDown() {}

void test_a_new_card_is_learnt_with_two_right_answers()
{
    Card c;
    TEST_ASSERT_FALSE(srs::due(c, 1));

    c = srs::answer(c, Grade::Good, 1);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(1, c.streak);
    TEST_ASSERT_TRUE(srs::due(c, 1));

    c = srs::answer(c, Grade::Good, 1);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(1, c.interval);
    TEST_ASSERT_EQUAL_UINT(2, c.due);
    TEST_ASSERT_FALSE(srs::due(c, 1));
    TEST_ASSERT_TRUE(srs::due(c, 2));
}

void test_a_wrong_answer_while_learning_starts_the_count_again()
{
    Card c = srs::answer(Card(), Grade::Good, 1);
    c      = srs::answer(c, Grade::Again, 1);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(0, c.streak);
    c = srs::answer(c, Grade::Hard, 1);
    TEST_ASSERT_EQUAL_UINT(0, c.streak);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(c.stage));
    c = srs::answer(c, Grade::Good, 1);
    c = srs::answer(c, Grade::Good, 1);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(0, c.lapses);
}

void test_intervals_grow_when_remembered()
{
    Card c = srs::answer(srs::answer(Card(), Grade::Good, 1), Grade::Good, 1);  // due on day 2, interval 1
    uint16_t day      = c.due;
    uint16_t previous = c.interval;
    const uint16_t expected[] = {3, 8, 20, 50, 125, 313, 365, 365};
    for (uint16_t want : expected) {
        c = srs::answer(c, Grade::Good, day);
        TEST_ASSERT_EQUAL_UINT(want, c.interval);
        TEST_ASSERT_TRUE(c.interval >= previous);
        TEST_ASSERT_EQUAL_UINT(day + c.interval, c.due);
        previous = c.interval;
        day      = c.due;
    }
    TEST_ASSERT_EQUAL_UINT(250, c.ease);
}

void test_a_late_answer_earns_part_of_the_wait()
{
    Card c;
    c.stage    = Stage::Review;
    c.interval = 10;
    c.due      = 20;
    const Card onTime = srs::answer(c, Grade::Good, 20);
    const Card late   = srs::answer(c, Grade::Good, 30);
    TEST_ASSERT_EQUAL_UINT(25, onTime.interval);
    TEST_ASSERT_EQUAL_UINT(38, late.interval);  // (10 + 10 / 2) * 2.5, rounded
    TEST_ASSERT_EQUAL_UINT(68, late.due);
}

void test_hard_grows_slowly_and_lowers_the_ease()
{
    Card c;
    c.stage    = Stage::Review;
    c.interval = 10;
    c.due      = 20;
    c          = srs::answer(c, Grade::Hard, 20);
    TEST_ASSERT_EQUAL_UINT(12, c.interval);
    TEST_ASSERT_EQUAL_UINT(235, c.ease);
    TEST_ASSERT_EQUAL_UINT(32, c.due);

    Card one;
    one.stage    = Stage::Review;
    one.interval = 1;
    one.due      = 5;
    one          = srs::answer(one, Grade::Hard, 5);
    TEST_ASSERT_EQUAL_UINT(2, one.interval);  // always at least a day longer
}

void test_forgetting()
{
    Card c;
    c.stage    = Stage::Review;
    c.interval = 40;
    c.due      = 100;
    c          = srs::answer(c, Grade::Again, 100);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(1, c.lapses);
    TEST_ASSERT_EQUAL_UINT(230, c.ease);
    TEST_ASSERT_EQUAL_UINT(10, c.interval);
    TEST_ASSERT_TRUE(srs::due(c, 100));

    // learnt again: it keeps the shortened interval
    c = srs::answer(c, Grade::Good, 100);
    c = srs::answer(c, Grade::Good, 100);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(10, c.interval);
    TEST_ASSERT_EQUAL_UINT(110, c.due);
}

void test_known_at_first_sight()
{
    Card c = srs::answer(Card(), Grade::Known, 3);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(c.stage));
    TEST_ASSERT_EQUAL_UINT(4, c.interval);
    TEST_ASSERT_EQUAL_UINT(7, c.due);
    TEST_ASSERT_FALSE(srs::due(c, 6));
    TEST_ASSERT_TRUE(srs::due(c, 7));

    // on a card met before it counts as an ordinary right answer
    Card learning = srs::answer(Card(), Grade::Good, 1);
    learning      = srs::answer(learning, Grade::Known, 1);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(learning.stage));
    TEST_ASSERT_EQUAL_UINT(1, learning.interval);
}

void test_limits()
{
    Card c;
    c.stage = Stage::Review;
    c.ease  = 135;
    c.interval = 3;
    c.due   = 10;
    for (int i = 0; i < 20; ++i) {
        c = srs::answer(c, Grade::Again, 10);
        c.stage = Stage::Review;
    }
    TEST_ASSERT_EQUAL_UINT(130, c.ease);
    TEST_ASSERT_EQUAL_UINT(20, c.lapses);
    TEST_ASSERT_EQUAL_UINT(1, c.interval);

    Card far;
    far.stage    = Stage::Review;
    far.interval = 365;
    far.due      = 65530;
    far          = srs::answer(far, Grade::Good, 65530);
    TEST_ASSERT_EQUAL_UINT(365, far.interval);
    TEST_ASSERT_EQUAL_UINT(65535, far.due);  // the day number does not wrap round
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_a_new_card_is_learnt_with_two_right_answers);
    RUN_TEST(test_a_wrong_answer_while_learning_starts_the_count_again);
    RUN_TEST(test_intervals_grow_when_remembered);
    RUN_TEST(test_a_late_answer_earns_part_of_the_wait);
    RUN_TEST(test_hard_grows_slowly_and_lowers_the_ease);
    RUN_TEST(test_forgetting);
    RUN_TEST(test_known_at_first_sight);
    RUN_TEST(test_limits);
    return UNITY_END();
}
