#include "romaji.h"

#include <cstring>

namespace romaji {

namespace {

struct Entry {
    const char* roma;
    const char* kana;
};

// Longest key is 4 letters ("xtsu", "ltsu").
constexpr size_t kMaxKeyLength = 4;

const Entry kTable[] = {
    {"a", "あ"},    {"i", "い"},    {"u", "う"},    {"e", "え"},    {"o", "お"},

    {"ka", "か"},   {"ki", "き"},   {"ku", "く"},   {"ke", "け"},   {"ko", "こ"},
    {"kya", "きゃ"}, {"kyi", "きぃ"}, {"kyu", "きゅ"}, {"kye", "きぇ"}, {"kyo", "きょ"},
    {"kwa", "くぁ"},
    {"ca", "か"},   {"ci", "し"},   {"cu", "く"},   {"ce", "せ"},   {"co", "こ"},
    {"qa", "くぁ"}, {"qi", "くぃ"}, {"qu", "く"},   {"qe", "くぇ"}, {"qo", "くぉ"},

    {"ga", "が"},   {"gi", "ぎ"},   {"gu", "ぐ"},   {"ge", "げ"},   {"go", "ご"},
    {"gya", "ぎゃ"}, {"gyi", "ぎぃ"}, {"gyu", "ぎゅ"}, {"gye", "ぎぇ"}, {"gyo", "ぎょ"},
    {"gwa", "ぐぁ"},

    {"sa", "さ"},   {"si", "し"},   {"su", "す"},   {"se", "せ"},   {"so", "そ"},
    {"shi", "し"},
    {"sya", "しゃ"}, {"syi", "しぃ"}, {"syu", "しゅ"}, {"sye", "しぇ"}, {"syo", "しょ"},
    {"sha", "しゃ"}, {"shu", "しゅ"}, {"she", "しぇ"}, {"sho", "しょ"},

    {"za", "ざ"},   {"zi", "じ"},   {"zu", "ず"},   {"ze", "ぜ"},   {"zo", "ぞ"},
    {"ji", "じ"},
    {"zya", "じゃ"}, {"zyi", "じぃ"}, {"zyu", "じゅ"}, {"zye", "じぇ"}, {"zyo", "じょ"},
    {"ja", "じゃ"},  {"ju", "じゅ"},  {"je", "じぇ"},  {"jo", "じょ"},
    {"jya", "じゃ"}, {"jyi", "じぃ"}, {"jyu", "じゅ"}, {"jye", "じぇ"}, {"jyo", "じょ"},

    {"ta", "た"},   {"ti", "ち"},   {"tu", "つ"},   {"te", "て"},   {"to", "と"},
    {"chi", "ち"},  {"tsu", "つ"},
    {"tya", "ちゃ"}, {"tyi", "ちぃ"}, {"tyu", "ちゅ"}, {"tye", "ちぇ"}, {"tyo", "ちょ"},
    {"cha", "ちゃ"}, {"chu", "ちゅ"}, {"che", "ちぇ"}, {"cho", "ちょ"},
    {"cya", "ちゃ"}, {"cyi", "ちぃ"}, {"cyu", "ちゅ"}, {"cye", "ちぇ"}, {"cyo", "ちょ"},
    {"tsa", "つぁ"}, {"tsi", "つぃ"}, {"tse", "つぇ"}, {"tso", "つぉ"},
    {"tha", "てゃ"}, {"thi", "てぃ"}, {"thu", "てゅ"}, {"the", "てぇ"}, {"tho", "てょ"},
    {"twa", "とぁ"}, {"twi", "とぃ"}, {"twu", "とぅ"}, {"twe", "とぇ"}, {"two", "とぉ"},

    {"da", "だ"},   {"di", "ぢ"},   {"du", "づ"},   {"de", "で"},   {"do", "ど"},
    {"dya", "ぢゃ"}, {"dyi", "ぢぃ"}, {"dyu", "ぢゅ"}, {"dye", "ぢぇ"}, {"dyo", "ぢょ"},
    {"dha", "でゃ"}, {"dhi", "でぃ"}, {"dhu", "でゅ"}, {"dhe", "でぇ"}, {"dho", "でょ"},
    {"dwa", "どぁ"}, {"dwi", "どぃ"}, {"dwu", "どぅ"}, {"dwe", "どぇ"}, {"dwo", "どぉ"},

    {"na", "な"},   {"ni", "に"},   {"nu", "ぬ"},   {"ne", "ね"},   {"no", "の"},
    {"nya", "にゃ"}, {"nyi", "にぃ"}, {"nyu", "にゅ"}, {"nye", "にぇ"}, {"nyo", "にょ"},

    {"ha", "は"},   {"hi", "ひ"},   {"hu", "ふ"},   {"he", "へ"},   {"ho", "ほ"},
    {"fu", "ふ"},
    {"hya", "ひゃ"}, {"hyi", "ひぃ"}, {"hyu", "ひゅ"}, {"hye", "ひぇ"}, {"hyo", "ひょ"},
    {"fa", "ふぁ"},  {"fi", "ふぃ"},  {"fe", "ふぇ"},  {"fo", "ふぉ"},
    {"fya", "ふゃ"}, {"fyu", "ふゅ"}, {"fyo", "ふょ"},

    {"ba", "ば"},   {"bi", "び"},   {"bu", "ぶ"},   {"be", "べ"},   {"bo", "ぼ"},
    {"bya", "びゃ"}, {"byi", "びぃ"}, {"byu", "びゅ"}, {"bye", "びぇ"}, {"byo", "びょ"},

    {"pa", "ぱ"},   {"pi", "ぴ"},   {"pu", "ぷ"},   {"pe", "ぺ"},   {"po", "ぽ"},
    {"pya", "ぴゃ"}, {"pyi", "ぴぃ"}, {"pyu", "ぴゅ"}, {"pye", "ぴぇ"}, {"pyo", "ぴょ"},

    {"ma", "ま"},   {"mi", "み"},   {"mu", "む"},   {"me", "め"},   {"mo", "も"},
    {"mya", "みゃ"}, {"myi", "みぃ"}, {"myu", "みゅ"}, {"mye", "みぇ"}, {"myo", "みょ"},

    {"ya", "や"},   {"yu", "ゆ"},   {"yo", "よ"},   {"ye", "いぇ"},

    {"ra", "ら"},   {"ri", "り"},   {"ru", "る"},   {"re", "れ"},   {"ro", "ろ"},
    {"rya", "りゃ"}, {"ryi", "りぃ"}, {"ryu", "りゅ"}, {"rye", "りぇ"}, {"ryo", "りょ"},

    {"wa", "わ"},   {"wi", "うぃ"}, {"wu", "う"},   {"we", "うぇ"}, {"wo", "を"},
    {"wyi", "ゐ"},  {"wye", "ゑ"},

    {"va", "ゔぁ"}, {"vi", "ゔぃ"}, {"vu", "ゔ"},   {"ve", "ゔぇ"}, {"vo", "ゔぉ"},
    {"vya", "ゔゃ"}, {"vyu", "ゔゅ"}, {"vyo", "ゔょ"},

    // Small kana, typed with an x or l prefix as in PC input methods.
    {"xa", "ぁ"},   {"xi", "ぃ"},   {"xu", "ぅ"},   {"xe", "ぇ"},   {"xo", "ぉ"},
    {"la", "ぁ"},   {"li", "ぃ"},   {"lu", "ぅ"},   {"le", "ぇ"},   {"lo", "ぉ"},
    {"xya", "ゃ"},  {"xyu", "ゅ"},  {"xyo", "ょ"},
    {"lya", "ゃ"},  {"lyu", "ゅ"},  {"lyo", "ょ"},
    {"xtu", "っ"},  {"xtsu", "っ"}, {"ltu", "っ"},  {"ltsu", "っ"},
    {"xwa", "ゎ"},  {"lwa", "ゎ"},
    {"xka", "ゕ"},  {"xke", "ゖ"},  {"lka", "ゕ"},  {"lke", "ゖ"},
    {"xn", "ん"},
};

constexpr size_t kTableSize = sizeof(kTable) / sizeof(kTable[0]);

bool isVowel(char c)
{
    return c == 'a' || c == 'i' || c == 'u' || c == 'e' || c == 'o';
}

bool isLetter(char c)
{
    return c >= 'a' && c <= 'z';
}

bool isConsonant(char c)
{
    return isLetter(c) && !isVowel(c);
}

char lower(char c)
{
    return (c >= 'A' && c <= 'Z') ? static_cast<char>(c - 'A' + 'a') : c;
}

// Lower is better.
int preference(const char* roma)
{
    static const char* const kTextbook[] = {
        "shi", "chi", "tsu", "fu", "ji", "sha", "shu", "sho", "she", "cha", "chu", "cho", "che", "ja", "ju", "jo", "je",
    };
    int score = static_cast<int>(std::strlen(roma));
    // x and l type small kana one by one, q and c are keyboard shortcuts: never what a textbook writes
    if (roma[0] == 'x' || roma[0] == 'l' || roma[0] == 'q' || (roma[0] == 'c' && roma[1] != 'h')) {
        score += 100;
    }
    for (const char* textbook : kTextbook) {
        if (std::strcmp(roma, textbook) == 0) {
            score -= 50;
        }
    }
    return score;
}

const char* lookup(const char* s, size_t length)
{
    for (size_t i = 0; i < kTableSize; ++i) {
        if (std::strlen(kTable[i].roma) == length && std::strncmp(kTable[i].roma, s, length) == 0) {
            return kTable[i].kana;
        }
    }
    return nullptr;
}

// True when `s` is the beginning of a table key that is longer than `s`.
bool isPrefixOfKey(const char* s, size_t length)
{
    for (size_t i = 0; i < kTableSize; ++i) {
        if (std::strlen(kTable[i].roma) > length && std::strncmp(kTable[i].roma, s, length) == 0) {
            return true;
        }
    }
    return false;
}

const char* punctuation(char c)
{
    switch (c) {
        case ',': return "、";
        case '.': return "。";
        case '?': return "？";
        case '!': return "！";
        case '[': return "「";
        case ']': return "」";
        case '~': return "〜";
        default:  return nullptr;
    }
}

}  // namespace

Result convert(const std::string& input, const Options& options, bool flush)
{
    std::string s;
    s.reserve(input.size());
    for (char c : input) {
        s.push_back(lower(c));
    }

    Result result;
    const size_t n = s.size();
    size_t i = 0;

    while (i < n) {
        const char c = s[i];
        const bool hasNext = (i + 1 < n);
        const char next = hasNext ? s[i + 1] : '\0';

        if (c == '-') {
            result.kana += "ー";
            ++i;
            continue;
        }

        if (!isLetter(c)) {
            const char* mark = options.punctuation ? punctuation(c) : nullptr;
            if (mark) {
                result.kana += mark;
            } else if (c != '\'') {
                // A stray apostrophe only separates syllables, so it is dropped.
                result.kana.push_back(c);
            }
            ++i;
            continue;
        }

        if (c == 'n') {
            if (!hasNext) {
                if (flush) {
                    result.kana += "ん";
                } else {
                    result.pending = "n";
                }
                break;
            }
            if (next == '\'') {
                result.kana += "ん";
                i += 2;
                continue;
            }
            if (next == 'n') {
                result.kana += "ん";
                if (options.nStyle == NStyle::Ime) {
                    i += 2;
                    continue;
                }
                // Textbook style: the second n starts the next syllable when a vowel or y follows
                // ("minna" -> みんな). Otherwise it belongs to the same ん ("konnbanha" -> こんばんは).
                const bool hasThird = (i + 2 < n);
                const char third = hasThird ? s[i + 2] : '\0';
                if (hasThird && (isVowel(third) || third == 'y')) {
                    i += 1;
                } else if (!hasThird && !flush) {
                    result.pending = "n";
                    break;
                } else {
                    i += 2;
                }
                continue;
            }
            if (!isVowel(next) && next != 'y') {
                // n before any other consonant, a space, a digit or punctuation
                result.kana += "ん";
                ++i;
                continue;
            }
            // n followed by a vowel or y: handled by the table below
        } else if (c == 'm' && options.nStyle == NStyle::Hepburn && hasNext &&
                   (next == 'b' || next == 'p' || next == 'm')) {
            // Traditional Hepburn as seen on station signs: Shimbashi, Namba, Gumma
            result.kana += "ん";
            ++i;
            continue;
        } else if (isConsonant(c) && hasNext) {
            // Doubled consonant, or t before ch ("matcha"): small tsu
            const bool doubled = (next == c);
            const bool tch = (c == 't' && next == 'c' && i + 2 < n && s[i + 2] == 'h');
            if (doubled || tch) {
                result.kana += "っ";
                ++i;
                continue;
            }
        }

        // Longest match against the table
        bool matched = false;
        const size_t remaining = n - i;
        const size_t longest = remaining < kMaxKeyLength ? remaining : kMaxKeyLength;
        for (size_t length = longest; length >= 1; --length) {
            const char* kana = lookup(s.c_str() + i, length);
            if (kana) {
                result.kana += kana;
                i += length;
                matched = true;
                break;
            }
        }
        if (matched) {
            continue;
        }

        // No match. If the rest could still grow into a syllable, wait for more letters.
        if (!flush && remaining < kMaxKeyLength && isPrefixOfKey(s.c_str() + i, remaining)) {
            result.pending = s.substr(i);
            break;
        }
        // "tc" is the start of "tch"
        if (!flush && remaining == 2 && c == 't' && next == 'c') {
            result.pending = s.substr(i);
            break;
        }

        // Not convertible: keep the letter as typed and move on.
        result.kana.push_back(c);
        ++i;
    }

    return result;
}

std::string spelling(const std::string& hiraganaUnit)
{
    const char* best = nullptr;
    int bestScore    = 0;
    for (size_t i = 0; i < kTableSize; ++i) {
        if (hiraganaUnit != kTable[i].kana) {
            continue;
        }
        const int score = preference(kTable[i].roma);
        if (!best || score < bestScore) {
            best      = kTable[i].roma;
            bestScore = score;
        }
    }
    return best ? std::string(best) : std::string();
}

std::string toKatakana(const std::string& text)
{
    std::string out;
    out.reserve(text.size());
    const size_t n = text.size();
    size_t i = 0;
    while (i < n) {
        const unsigned char b0 = static_cast<unsigned char>(text[i]);
        if (b0 >= 0xE0 && b0 <= 0xEF && i + 2 < n) {
            const unsigned char b1 = static_cast<unsigned char>(text[i + 1]);
            const unsigned char b2 = static_cast<unsigned char>(text[i + 2]);
            unsigned int cp = ((b0 & 0x0Fu) << 12) | ((b1 & 0x3Fu) << 6) | (b2 & 0x3Fu);
            // ぁ..ゖ and the iteration marks ゝ ゞ
            if ((cp >= 0x3041 && cp <= 0x3096) || cp == 0x309D || cp == 0x309E) {
                cp += 0x60;
            }
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
            i += 3;
        } else {
            out.push_back(text[i]);
            ++i;
        }
    }
    return out;
}

}  // namespace romaji
