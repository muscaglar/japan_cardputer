#include <unity.h>

#include <string>

#include "romaji.h"

using romaji::NStyle;
using romaji::Options;

namespace {

std::string hep(const char* s)
{
    return romaji::convert(s, Options(), true).kana;
}

std::string ime(const char* s)
{
    Options o;
    o.nStyle = NStyle::Ime;
    return romaji::convert(s, o, true).kana;
}

void expectLive(const char* input, const char* kana, const char* pending)
{
    const romaji::Result r = romaji::convert(input, Options(), false);
    TEST_ASSERT_EQUAL_STRING_MESSAGE(kana, r.kana.c_str(), input);
    TEST_ASSERT_EQUAL_STRING_MESSAGE(pending, r.pending.c_str(), input);
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_vowels_and_basic_syllables()
{
    TEST_ASSERT_EQUAL_STRING("あいうえお", hep("aiueo").c_str());
    TEST_ASSERT_EQUAL_STRING("かきくけこ", hep("kakikukeko").c_str());
    TEST_ASSERT_EQUAL_STRING("さしすせそ", hep("sashisuseso").c_str());
    TEST_ASSERT_EQUAL_STRING("たちつてと", hep("tachitsuteto").c_str());
    TEST_ASSERT_EQUAL_STRING("はひふへほ", hep("hahifuheho").c_str());
    TEST_ASSERT_EQUAL_STRING("やゆよ", hep("yayuyo").c_str());
    TEST_ASSERT_EQUAL_STRING("らりるれろ", hep("rarirurero").c_str());
    TEST_ASSERT_EQUAL_STRING("わをん", hep("wawon").c_str());
    TEST_ASSERT_EQUAL_STRING("がぎぐげご", hep("gagigugego").c_str());
    TEST_ASSERT_EQUAL_STRING("ぱぴぷぺぽ", hep("papipupepo").c_str());
}

void test_alternative_spellings_agree()
{
    TEST_ASSERT_EQUAL_STRING(hep("shi").c_str(), hep("si").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("chi").c_str(), hep("ti").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("tsu").c_str(), hep("tu").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("fu").c_str(), hep("hu").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("ji").c_str(), hep("zi").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("sha").c_str(), hep("sya").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("cho").c_str(), hep("tyo").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("ja").c_str(), hep("zya").c_str());
    TEST_ASSERT_EQUAL_STRING(hep("ja").c_str(), hep("jya").c_str());
}

void test_digraphs()
{
    TEST_ASSERT_EQUAL_STRING("きょう", hep("kyou").c_str());
    TEST_ASSERT_EQUAL_STRING("とうきょう", hep("toukyou").c_str());
    TEST_ASSERT_EQUAL_STRING("りょかん", hep("ryokan").c_str());
    TEST_ASSERT_EQUAL_STRING("しゅくはく", hep("shukuhaku").c_str());
    TEST_ASSERT_EQUAL_STRING("ぎゅうにゅう", hep("gyuunyuu").c_str());
    TEST_ASSERT_EQUAL_STRING("じゃあ", hep("jaa").c_str());
    TEST_ASSERT_EQUAL_STRING("ひゃくえん", hep("hyakuen").c_str());
}

void test_small_tsu()
{
    TEST_ASSERT_EQUAL_STRING("きって", hep("kitte").c_str());
    TEST_ASSERT_EQUAL_STRING("きっぷ", hep("kippu").c_str());
    TEST_ASSERT_EQUAL_STRING("いっしょ", hep("issho").c_str());
    TEST_ASSERT_EQUAL_STRING("みっつ", hep("mittsu").c_str());
    TEST_ASSERT_EQUAL_STRING("まっちゃ", hep("matcha").c_str());
    TEST_ASSERT_EQUAL_STRING("まっちゃ", hep("maccha").c_str());
    TEST_ASSERT_EQUAL_STRING("ざっし", hep("zasshi").c_str());
    TEST_ASSERT_EQUAL_STRING("いらっしゃいませ", hep("irasshaimase").c_str());
    TEST_ASSERT_EQUAL_STRING("っ", hep("xtsu").c_str());
    TEST_ASSERT_EQUAL_STRING("っ", hep("ltu").c_str());
}

void test_n_before_consonant_and_at_end()
{
    TEST_ASSERT_EQUAL_STRING("ほん", hep("hon").c_str());
    TEST_ASSERT_EQUAL_STRING("せんせい", hep("sensei").c_str());
    TEST_ASSERT_EQUAL_STRING("こんばんは", hep("konbanha").c_str());
    TEST_ASSERT_EQUAL_STRING("しんかんせん", hep("shinkansen").c_str());
    TEST_ASSERT_EQUAL_STRING("ほん です", hep("hon desu").c_str());
    TEST_ASSERT_EQUAL_STRING("にほんご", hep("nihongo").c_str());
    TEST_ASSERT_EQUAL_STRING("おんせん", hep("onsen").c_str());
}

void test_n_with_apostrophe()
{
    TEST_ASSERT_EQUAL_STRING("きんえん", hep("kin'en").c_str());
    TEST_ASSERT_EQUAL_STRING("ほんや", hep("hon'ya").c_str());
    TEST_ASSERT_EQUAL_STRING("てんいん", hep("ten'in").c_str());
    TEST_ASSERT_EQUAL_STRING("きんえん", ime("kin'en").c_str());
    // Without the apostrophe the n joins the vowel, in both styles
    TEST_ASSERT_EQUAL_STRING("きねん", hep("kinen").c_str());
    TEST_ASSERT_EQUAL_STRING("きねん", ime("kinen").c_str());
}

void test_double_n_textbook_style()
{
    TEST_ASSERT_EQUAL_STRING("こんにちは", hep("konnichiha").c_str());
    TEST_ASSERT_EQUAL_STRING("みんな", hep("minna").c_str());
    TEST_ASSERT_EQUAL_STRING("おんな", hep("onna").c_str());
    TEST_ASSERT_EQUAL_STRING("あんない", hep("annai").c_str());
    TEST_ASSERT_EQUAL_STRING("こんにゃく", hep("konnyaku").c_str());
    // Habits from PC input methods still work where they cannot be confused
    TEST_ASSERT_EQUAL_STRING("みんな", hep("minnna").c_str());
    TEST_ASSERT_EQUAL_STRING("こんばんは", hep("konnbannha").c_str());
    TEST_ASSERT_EQUAL_STRING("ほん", hep("honn").c_str());
}

void test_double_n_ime_style()
{
    TEST_ASSERT_EQUAL_STRING("みんな", ime("minnna").c_str());
    TEST_ASSERT_EQUAL_STRING("みんあ", ime("minna").c_str());
    TEST_ASSERT_EQUAL_STRING("きんえん", ime("kinnenn").c_str());
    TEST_ASSERT_EQUAL_STRING("てんいん", ime("tenninn").c_str());
    TEST_ASSERT_EQUAL_STRING("こんばんは", ime("konnbannha").c_str());
    TEST_ASSERT_EQUAL_STRING("こんにちは", ime("konnnichiha").c_str());
    TEST_ASSERT_EQUAL_STRING("ほんや", ime("honnya").c_str());
}

void test_station_sign_spellings()
{
    TEST_ASSERT_EQUAL_STRING("しんばし", hep("shimbashi").c_str());
    TEST_ASSERT_EQUAL_STRING("なんば", hep("namba").c_str());
    TEST_ASSERT_EQUAL_STRING("にほんばし", hep("nihombashi").c_str());
    TEST_ASSERT_EQUAL_STRING("ぐんま", hep("gumma").c_str());
    TEST_ASSERT_EQUAL_STRING("さんぽ", hep("sampo").c_str());
    TEST_ASSERT_EQUAL_STRING("てんぷら", hep("tempura").c_str());
    // m before a vowel is untouched
    TEST_ASSERT_EQUAL_STRING("まみむめも", hep("mamimumemo").c_str());
}

void test_long_vowel_and_punctuation()
{
    TEST_ASSERT_EQUAL_STRING("らーめん", hep("ra-men").c_str());
    TEST_ASSERT_EQUAL_STRING("えきはどこですか？", hep("ekihadokodesuka?").c_str());
    TEST_ASSERT_EQUAL_STRING("はい、そうです。", hep("hai,soudesu.").c_str());
    Options plain;
    plain.punctuation = false;
    TEST_ASSERT_EQUAL_STRING("はい.", romaji::convert("hai.", plain, true).kana.c_str());
    TEST_ASSERT_EQUAL_STRING("3じ", hep("3ji").c_str());
}

void test_foreign_sounds_for_katakana_words()
{
    TEST_ASSERT_EQUAL_STRING("ふぁ", hep("fa").c_str());
    TEST_ASSERT_EQUAL_STRING("てぃ", hep("thi").c_str());
    TEST_ASSERT_EQUAL_STRING("でぃ", hep("dhi").c_str());
    TEST_ASSERT_EQUAL_STRING("うぃ", hep("wi").c_str());
    TEST_ASSERT_EQUAL_STRING("ゔぁ", hep("va").c_str());
    TEST_ASSERT_EQUAL_STRING("しぇ", hep("she").c_str());
    TEST_ASSERT_EQUAL_STRING("ちぇ", hep("che").c_str());
    TEST_ASSERT_EQUAL_STRING("じぇ", hep("je").c_str());
}

void test_case_is_ignored()
{
    TEST_ASSERT_EQUAL_STRING("とうきょう", hep("TouKyou").c_str());
}

void test_live_typing_keeps_undecided_tail()
{
    expectLive("", "", "");
    expectLive("k", "", "k");
    expectLive("ky", "", "ky");
    expectLive("kyo", "きょ", "");
    expectLive("sh", "", "sh");
    expectLive("ts", "", "ts");
    expectLive("ko", "こ", "");
    expectLive("kon", "こ", "n");
    expectLive("konn", "こん", "n");
    expectLive("konni", "こんに", "");
    expectLive("kit", "き", "t");
    expectLive("kitt", "きっ", "t");
    expectLive("kitte", "きって", "");
    expectLive("matc", "ま", "tc");
    expectLive("match", "まっ", "ch");
    expectLive("hon ", "ほん ", "");
    expectLive("xts", "", "xts");
}

void test_flush_resolves_tail()
{
    TEST_ASSERT_EQUAL_STRING("こん", romaji::convert("kon", Options(), true).kana.c_str());
    TEST_ASSERT_EQUAL_STRING("", romaji::convert("kon", Options(), true).pending.c_str());
    // Letters that never became a syllable are kept as typed
    TEST_ASSERT_EQUAL_STRING("こk", romaji::convert("kok", Options(), true).kana.c_str());
}

void test_unconvertible_input_passes_through()
{
    TEST_ASSERT_EQUAL_STRING("123", hep("123").c_str());
    TEST_ASSERT_EQUAL_STRING("あ い", hep("a i").c_str());
}

void test_katakana()
{
    TEST_ASSERT_EQUAL_STRING("コーヒー", romaji::toKatakana(hep("ko-hi-")).c_str());
    TEST_ASSERT_EQUAL_STRING("ラーメン", romaji::toKatakana(hep("ra-men")).c_str());
    TEST_ASSERT_EQUAL_STRING("ホテル", romaji::toKatakana(hep("hoteru")).c_str());
    TEST_ASSERT_EQUAL_STRING("ヴァイオリン", romaji::toKatakana(hep("vaiorin")).c_str());
    TEST_ASSERT_EQUAL_STRING("チェックイン", romaji::toKatakana(hep("chekkuin")).c_str());
    TEST_ASSERT_EQUAL_STRING("ファミリーマート", romaji::toKatakana(hep("famiri-ma-to")).c_str());
    // Kanji, ASCII and existing katakana are left alone
    TEST_ASSERT_EQUAL_STRING("東京ABCカ", romaji::toKatakana("東京ABCカ").c_str());
    // Truncated UTF-8 at the end must not read out of bounds
    TEST_ASSERT_EQUAL_STRING("\xE3\x81", romaji::toKatakana("\xE3\x81").c_str());
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_vowels_and_basic_syllables);
    RUN_TEST(test_alternative_spellings_agree);
    RUN_TEST(test_digraphs);
    RUN_TEST(test_small_tsu);
    RUN_TEST(test_n_before_consonant_and_at_end);
    RUN_TEST(test_n_with_apostrophe);
    RUN_TEST(test_double_n_textbook_style);
    RUN_TEST(test_double_n_ime_style);
    RUN_TEST(test_station_sign_spellings);
    RUN_TEST(test_long_vowel_and_punctuation);
    RUN_TEST(test_foreign_sounds_for_katakana_words);
    RUN_TEST(test_case_is_ignored);
    RUN_TEST(test_live_typing_keeps_undecided_tail);
    RUN_TEST(test_flush_resolves_tail);
    RUN_TEST(test_unconvertible_input_passes_through);
    RUN_TEST(test_katakana);
    return UNITY_END();
}
