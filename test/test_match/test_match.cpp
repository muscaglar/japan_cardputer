#include <unity.h>

#include <string>

#include "match.h"

using match::Slip;
using match::Verdict;

namespace {

deck::Item word(const char* prompt, const char* reading, const char* accepted = "")
{
    return deck::Item{"test-item", prompt, reading, accepted, "", "", "", -1, 2, deck::Kind::Word};
}

void expect(const char* typed, const deck::Item& item, Verdict verdict, Slip slip, const char* expected = nullptr)
{
    const match::Outcome o = match::check(typed, item);
    TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(verdict), static_cast<int>(o.verdict), typed);
    TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(slip), static_cast<int>(o.slip), typed);
    if (expected) {
        TEST_ASSERT_EQUAL_STRING_MESSAGE(expected, o.expected.c_str(), typed);
    }
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_normalise()
{
    TEST_ASSERT_EQUAL_STRING("かいさつ", match::normalise("かいさつ").c_str());
    TEST_ASSERT_EQUAL_STRING("こおひい", match::normalise("コーヒー").c_str());
    TEST_ASSERT_EQUAL_STRING("らあめん", match::normalise("らーめん").c_str());
    TEST_ASSERT_EQUAL_STRING("きゃあ", match::normalise("キャー").c_str());
    TEST_ASSERT_EQUAL_STRING("えきはどこですか", match::normalise("えき は どこ です か？").c_str());
    TEST_ASSERT_EQUAL_STRING("はいそうです", match::normalise("はい、そうです。").c_str());
    TEST_ASSERT_EQUAL_STRING("", match::normalise("").c_str());
    TEST_ASSERT_EQUAL_STRING("", match::normalise(" 、。").c_str());
    // a long mark with nothing to lengthen is dropped
    TEST_ASSERT_EQUAL_STRING("あ", match::normalise("ーあ").c_str());
    TEST_ASSERT_EQUAL_STRING("ん", match::normalise("んー").c_str());
    // Latin letters stay, so that they can never match
    TEST_ASSERT_EQUAL_STRING("かk", match::normalise("かk").c_str());
}

void test_right()
{
    expect("かいさつ", word("改札", "かいさつ"), Verdict::Right, Slip::None, "かいさつ");
    expect("カイサツ", word("改札", "かいさつ"), Verdict::Right, Slip::None);
    expect("かい さつ", word("改札", "かいさつ"), Verdict::Right, Slip::None);
    const match::Outcome o = match::check("せいさんき", word("精算機", "せいさんき"));
    TEST_ASSERT_EQUAL_INT(-1, o.beat);
}

void test_katakana_words_and_the_long_mark()
{
    const deck::Item coffee = word("コーヒー", "コーヒー");
    expect("こーひー", coffee, Verdict::Right, Slip::None, "コーヒー");
    expect("こおひい", coffee, Verdict::Right, Slip::None);
    expect("コーヒー", coffee, Verdict::Right, Slip::None);
    expect("こひ", coffee, Verdict::Wrong, Slip::Other);
    expect("こーひ", coffee, Verdict::Almost, Slip::LongVowel);
    expect("こひー", coffee, Verdict::Almost, Slip::LongVowel);

    const deck::Item set = word("モーニングセット", "モーニングセット");
    expect("もーにんぐせっと", set, Verdict::Right, Slip::None);
    expect("もーにんぐせと", set, Verdict::Almost, Slip::SmallTsu);
    expect("もにんぐせっと", set, Verdict::Almost, Slip::LongVowel);
}

void test_accepted_answers()
{
    const deck::Item beer =
        deck::Item{"count-hai-3", "ビール × 3", "さんばい", "みっつ|さんはい", "three glasses", "", "", -1, 1, deck::Kind::Counter};
    expect("さんばい", beer, Verdict::Right, Slip::None, "さんばい");
    expect("みっつ", beer, Verdict::Right, Slip::None, "みっつ");
    expect("さんはい", beer, Verdict::Right, Slip::None, "さんはい");
    expect("みつ", beer, Verdict::Almost, Slip::SmallTsu, "みっつ");
    expect("よっつ", beer, Verdict::Wrong, Slip::Other, "さんばい");
}

void test_long_vowels()
{
    const deck::Item tokyo = word("東京", "とうきょう");
    expect("とうきょう", tokyo, Verdict::Right, Slip::None);
    expect("とおきょお", tokyo, Verdict::Almost, Slip::LongVowel);  // the same sounds, another spelling
    expect("とうきょ", tokyo, Verdict::Almost, Slip::LongVowel);    // one beat short
    expect("ときょう", tokyo, Verdict::Almost, Slip::LongVowel);
    expect("ときょ", tokyo, Verdict::Wrong, Slip::Other);           // two beats short
    expect("とうきょうう", tokyo, Verdict::Wrong, Slip::Other);

    const deck::Item police = word("警察", "けいさつ");
    expect("けえさつ", police, Verdict::Almost, Slip::LongVowel);
    expect("けさつ", police, Verdict::Almost, Slip::LongVowel);
}

void test_small_tsu_and_n()
{
    const deck::Item ticket = word("切符", "きっぷ");
    expect("きぷ", ticket, Verdict::Almost, Slip::SmallTsu);
    expect("きっっぷ", ticket, Verdict::Almost, Slip::SmallTsu);

    const deck::Item stamp = word("切手", "きって");
    expect("きて", stamp, Verdict::Almost, Slip::SmallTsu);
    expect("きいて", stamp, Verdict::Wrong, Slip::Other);

    const deck::Item smoking = word("禁煙", "きんえん");
    expect("きんえん", smoking, Verdict::Right, Slip::None);
    expect("きねん", smoking, Verdict::Wrong, Slip::Other);  // ね is another sound, not a missing ん
    expect("きえん", smoking, Verdict::Almost, Slip::N);
    expect("きんえ", smoking, Verdict::Almost, Slip::N);
}

void test_voicing()
{
    const deck::Item exit = word("出口", "でぐち");
    expect("でくち", exit, Verdict::Almost, Slip::Voicing);
    expect("てぐち", exit, Verdict::Almost, Slip::Voicing);
    expect("てくち", exit, Verdict::Wrong, Slip::Other);  // two slips
    const match::Outcome o = match::check("でくち", exit);
    TEST_ASSERT_EQUAL_INT(1, o.beat);

    const deck::Item platform = word("三番線", "さんばんせん");
    expect("さんぱんせん", platform, Verdict::Almost, Slip::Voicing);
    expect("さんはんせん", platform, Verdict::Almost, Slip::Voicing);
}

void test_wrong()
{
    const deck::Item gate = word("改札", "かいさつ");
    expect("", gate, Verdict::Wrong, Slip::Other, "かいさつ");
    expect("   ", gate, Verdict::Wrong, Slip::Other);
    expect("かいさつk", gate, Verdict::Wrong, Slip::Other);
    expect("kaisatsu", gate, Verdict::Wrong, Slip::Other);
    expect("でぐち", gate, Verdict::Wrong, Slip::Other);
    const match::Outcome o = match::check("かいせつ", gate);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Verdict::Wrong), static_cast<int>(o.verdict));
    TEST_ASSERT_EQUAL_INT(2, o.beat);
}

void test_kana_items()
{
    const deck::Item kya = deck::Item{"kana-kya", "きゃ", "きゃ", "", "kya", "", "", -1, 1, deck::Kind::Kana};
    expect("きゃ", kya, Verdict::Right, Slip::None);
    expect("きや", kya, Verdict::Wrong, Slip::Other);
    expect("ぎゃ", kya, Verdict::Almost, Slip::Voicing);
    const deck::Item n = deck::Item{"kana-n", "ん", "ん", "", "n", "", "", -1, 1, deck::Kind::Kana};
    expect("ん", n, Verdict::Right, Slip::None);
    expect("な", n, Verdict::Wrong, Slip::Other);
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_normalise);
    RUN_TEST(test_right);
    RUN_TEST(test_katakana_words_and_the_long_mark);
    RUN_TEST(test_accepted_answers);
    RUN_TEST(test_long_vowels);
    RUN_TEST(test_small_tsu_and_n);
    RUN_TEST(test_voicing);
    RUN_TEST(test_wrong);
    RUN_TEST(test_kana_items);
    return UNITY_END();
}
