#include <unity.h>

#include <string>
#include <vector>

#include "kana.h"
#include "pitch.h"

namespace {

std::string joined(const std::vector<std::string>& parts)
{
    std::string out;
    for (const std::string& part : parts) {
        if (!out.empty()) {
            out += "|";
        }
        out += part;
    }
    return out;
}

std::string pattern(int beats, int accent)
{
    std::string out;
    for (bool high : pitch::heights(beats, accent)) {
        out.push_back(high ? 'H' : 'L');
    }
    return out;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_beats()
{
    TEST_ASSERT_EQUAL_STRING("か|い|さ|つ", joined(kana::beats("かいさつ")).c_str());
    TEST_ASSERT_EQUAL_STRING("だ|い|じょ|う|ぶ", joined(kana::beats("だいじょうぶ")).c_str());
    TEST_ASSERT_EQUAL_STRING("き|っ|ぷ", joined(kana::beats("きっぷ")).c_str());
    TEST_ASSERT_EQUAL_STRING("ラ|ー|メ|ン", joined(kana::beats("ラーメン")).c_str());
    TEST_ASSERT_EQUAL_STRING("チェ|ッ|ク|イ|ン", joined(kana::beats("チェックイン")).c_str());
    TEST_ASSERT_EQUAL_STRING("きゃ|きゅ|きょ", joined(kana::beats("きゃきゅきょ")).c_str());
    TEST_ASSERT_EQUAL_STRING("", joined(kana::beats("")).c_str());
    // A small kana at the very start has nothing to join
    TEST_ASSERT_EQUAL_STRING("ゃ|あ", joined(kana::beats("ゃあ")).c_str());
}

void test_scripts()
{
    TEST_ASSERT_EQUAL_STRING("らーめん", kana::toHiragana("ラーメン").c_str());
    TEST_ASSERT_EQUAL_STRING("ラーメン", kana::toKatakana("らーめん").c_str());
    TEST_ASSERT_EQUAL_STRING("ヴァイオリン", kana::toKatakana("ゔぁいおりん").c_str());
    TEST_ASSERT_EQUAL_STRING("東京えき abc", kana::toHiragana("東京エキ abc").c_str());
    TEST_ASSERT_EQUAL_UINT(4, kana::length("かいさつ"));
    TEST_ASSERT_EQUAL_UINT(5, kana::length("東京abc"));
}

void test_romaji_for_display()
{
    TEST_ASSERT_EQUAL_STRING("kaisatsu", kana::toRomaji("かいさつ").c_str());
    TEST_ASSERT_EQUAL_STRING("daijoubu", kana::toRomaji("だいじょうぶ").c_str());
    TEST_ASSERT_EQUAL_STRING("kippu", kana::toRomaji("きっぷ").c_str());
    TEST_ASSERT_EQUAL_STRING("matcha", kana::toRomaji("まっちゃ").c_str());
    TEST_ASSERT_EQUAL_STRING("zasshi", kana::toRomaji("ざっし").c_str());
    TEST_ASSERT_EQUAL_STRING("raamen", kana::toRomaji("ラーメン").c_str());
    TEST_ASSERT_EQUAL_STRING("koohii", kana::toRomaji("コーヒー").c_str());
    TEST_ASSERT_EQUAL_STRING("toukyou", kana::toRomaji("とうきょう").c_str());
    TEST_ASSERT_EQUAL_STRING("shinkansen", kana::toRomaji("しんかんせん").c_str());
    TEST_ASSERT_EQUAL_STRING("kin'en", kana::toRomaji("きんえん").c_str());
    TEST_ASSERT_EQUAL_STRING("hon'ya", kana::toRomaji("ほんや").c_str());
    TEST_ASSERT_EQUAL_STRING("konnichiha", kana::toRomaji("こんにちは").c_str());
    TEST_ASSERT_EQUAL_STRING("ryokan", kana::toRomaji("りょかん").c_str());
    TEST_ASSERT_EQUAL_STRING("jaa", kana::toRomaji("じゃあ").c_str());
    TEST_ASSERT_EQUAL_STRING("chotto", kana::toRomaji("ちょっと").c_str());
}

void test_pitch_patterns()
{
    TEST_ASSERT_EQUAL_STRING("LHHH", pattern(4, 0).c_str());   // かいさつ, flat
    TEST_ASSERT_EQUAL_STRING("HL", pattern(2, 1).c_str());     // 箸
    TEST_ASSERT_EQUAL_STRING("LH", pattern(2, 2).c_str());     // 橋, falls after the last beat
    TEST_ASSERT_EQUAL_STRING("LH", pattern(2, 0).c_str());     // 端
    TEST_ASSERT_EQUAL_STRING("LHHLL", pattern(5, 3).c_str());  // だいじょうぶ
    TEST_ASSERT_EQUAL_STRING("LHLLL", pattern(5, 2).c_str());  // ありがとう
    TEST_ASSERT_EQUAL_STRING("H", pattern(1, 1).c_str());
    TEST_ASSERT_EQUAL_STRING("H", pattern(1, 0).c_str());
    TEST_ASSERT_EQUAL_STRING("", pattern(4, pitch::kUnknown).c_str());
    TEST_ASSERT_EQUAL_STRING("", pattern(2, 3).c_str());       // accent beyond the word
    TEST_ASSERT_TRUE(pitch::particleIsHigh(0));
    TEST_ASSERT_FALSE(pitch::particleIsHigh(1));
    TEST_ASSERT_FALSE(pitch::particleIsHigh(2));
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_beats);
    RUN_TEST(test_scripts);
    RUN_TEST(test_romaji_for_display);
    RUN_TEST(test_pitch_patterns);
    return UNITY_END();
}
