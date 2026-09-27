#include "kana.h"

#include <cstdint>
#include <cstring>

namespace kana {

namespace {

// Decodes one UTF-8 character starting at `i`. Returns its length in bytes (at least 1).
size_t decode(const std::string& s, size_t i, uint32_t& code)
{
    const unsigned char b0 = static_cast<unsigned char>(s[i]);
    const size_t left = s.size() - i;
    if (b0 < 0x80) {
        code = b0;
        return 1;
    }
    if ((b0 & 0xE0) == 0xC0 && left >= 2) {
        code = ((b0 & 0x1Fu) << 6) | (static_cast<unsigned char>(s[i + 1]) & 0x3Fu);
        return 2;
    }
    if ((b0 & 0xF0) == 0xE0 && left >= 3) {
        code = ((b0 & 0x0Fu) << 12) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 6) |
               (static_cast<unsigned char>(s[i + 2]) & 0x3Fu);
        return 3;
    }
    if ((b0 & 0xF8) == 0xF0 && left >= 4) {
        code = ((b0 & 0x07u) << 18) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 12) |
               ((static_cast<unsigned char>(s[i + 2]) & 0x3Fu) << 6) | (static_cast<unsigned char>(s[i + 3]) & 0x3Fu);
        return 4;
    }
    code = b0;
    return 1;
}

void encode(uint32_t code, std::string& out)
{
    if (code < 0x80) {
        out.push_back(static_cast<char>(code));
    } else if (code < 0x800) {
        out.push_back(static_cast<char>(0xC0 | (code >> 6)));
        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
    } else if (code < 0x10000) {
        out.push_back(static_cast<char>(0xE0 | (code >> 12)));
        out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
    } else {
        out.push_back(static_cast<char>(0xF0 | (code >> 18)));
        out.push_back(static_cast<char>(0x80 | ((code >> 12) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
    }
}

bool isSmall(uint32_t c)
{
    switch (c) {
        case 0x3041: case 0x3043: case 0x3045: case 0x3047: case 0x3049:  // ぁぃぅぇぉ
        case 0x3083: case 0x3085: case 0x3087: case 0x308E:              // ゃゅょゎ
        case 0x30A1: case 0x30A3: case 0x30A5: case 0x30A7: case 0x30A9:  // ァィゥェォ
        case 0x30E3: case 0x30E5: case 0x30E7: case 0x30EE:              // ャュョヮ
            return true;
        default:
            return false;
    }
}

uint32_t hira(uint32_t c)
{
    if ((c >= 0x30A1 && c <= 0x30F6) || c == 0x30FD || c == 0x30FE) {
        return c - 0x60;
    }
    return c;
}

struct Syllable {
    uint32_t code;
    const char* roma;
};

// Single hiragana. Digraphs are built from the consonant of the first kana and the small kana.
const Syllable kSyllables[] = {
    {0x3042, "a"},  {0x3044, "i"},   {0x3046, "u"},   {0x3048, "e"},  {0x304A, "o"},
    {0x304B, "ka"}, {0x304D, "ki"},  {0x304F, "ku"},  {0x3051, "ke"}, {0x3053, "ko"},
    {0x304C, "ga"}, {0x304E, "gi"},  {0x3050, "gu"},  {0x3052, "ge"}, {0x3054, "go"},
    {0x3055, "sa"}, {0x3057, "shi"}, {0x3059, "su"},  {0x305B, "se"}, {0x305D, "so"},
    {0x3056, "za"}, {0x3058, "ji"},  {0x305A, "zu"},  {0x305C, "ze"}, {0x305E, "zo"},
    {0x305F, "ta"}, {0x3061, "chi"}, {0x3064, "tsu"}, {0x3066, "te"}, {0x3068, "to"},
    {0x3060, "da"}, {0x3062, "ji"},  {0x3065, "zu"},  {0x3067, "de"}, {0x3069, "do"},
    {0x306A, "na"}, {0x306B, "ni"},  {0x306C, "nu"},  {0x306D, "ne"}, {0x306E, "no"},
    {0x306F, "ha"}, {0x3072, "hi"},  {0x3075, "fu"},  {0x3078, "he"}, {0x307B, "ho"},
    {0x3070, "ba"}, {0x3073, "bi"},  {0x3076, "bu"},  {0x3079, "be"}, {0x307C, "bo"},
    {0x3071, "pa"}, {0x3074, "pi"},  {0x3077, "pu"},  {0x307A, "pe"}, {0x307D, "po"},
    {0x307E, "ma"}, {0x307F, "mi"},  {0x3080, "mu"},  {0x3081, "me"}, {0x3082, "mo"},
    {0x3084, "ya"}, {0x3086, "yu"},  {0x3088, "yo"},
    {0x3089, "ra"}, {0x308A, "ri"},  {0x308B, "ru"},  {0x308C, "re"}, {0x308D, "ro"},
    {0x308F, "wa"}, {0x3092, "wo"},  {0x3094, "vu"},
    {0x3041, "a"},  {0x3043, "i"},   {0x3045, "u"},   {0x3047, "e"},  {0x3049, "o"},
    {0x3083, "ya"}, {0x3085, "yu"},  {0x3087, "yo"},  {0x308E, "wa"},
};

const char* syllable(uint32_t code)
{
    for (const Syllable& s : kSyllables) {
        if (s.code == code) {
            return s.roma;
        }
    }
    return nullptr;
}

char lastVowel(const std::string& roma)
{
    for (size_t i = roma.size(); i > 0; --i) {
        const char c = roma[i - 1];
        if (c == 'a' || c == 'i' || c == 'u' || c == 'e' || c == 'o') {
            return c;
        }
    }
    return 0;
}

}  // namespace

std::vector<std::string> beats(const std::string& text)
{
    std::vector<std::string> out;
    size_t i = 0;
    while (i < text.size()) {
        uint32_t code = 0;
        const size_t n = decode(text, i, code);
        if (isSmall(code) && !out.empty()) {
            out.back().append(text, i, n);
        } else {
            out.emplace_back(text, i, n);
        }
        i += n;
    }
    return out;
}

std::string toHiragana(const std::string& text)
{
    std::string out;
    out.reserve(text.size());
    size_t i = 0;
    while (i < text.size()) {
        uint32_t code = 0;
        const size_t n = decode(text, i, code);
        const uint32_t mapped = hira(code);
        if (mapped != code) {
            encode(mapped, out);
        } else {
            out.append(text, i, n);
        }
        i += n;
    }
    return out;
}

std::string toKatakana(const std::string& text)
{
    std::string out;
    out.reserve(text.size());
    size_t i = 0;
    while (i < text.size()) {
        uint32_t code = 0;
        const size_t n = decode(text, i, code);
        if ((code >= 0x3041 && code <= 0x3096) || code == 0x309D || code == 0x309E) {
            encode(code + 0x60, out);
        } else {
            out.append(text, i, n);
        }
        i += n;
    }
    return out;
}

std::string toRomaji(const std::string& text)
{
    const std::string h = toHiragana(text);
    std::vector<uint32_t> codes;
    size_t i = 0;
    while (i < h.size()) {
        uint32_t code = 0;
        i += decode(h, i, code);
        codes.push_back(code);
    }

    std::string out;
    bool doubleNext = false;
    for (size_t k = 0; k < codes.size(); ++k) {
        const uint32_t c = codes[k];
        const uint32_t next = (k + 1 < codes.size()) ? codes[k + 1] : 0;

        if (c == 0x3063) {  // っ
            doubleNext = true;
            continue;
        }
        if (c == 0x30FC) {  // ー repeats the vowel before it
            const char v = lastVowel(out);
            out.push_back(v ? v : '-');
            continue;
        }
        if (c == 0x3093) {  // ん
            const char* following = syllable(next);
            const bool ambiguous = following && (strchr("aiueoy", following[0]) != nullptr);
            out += ambiguous ? "n'" : "n";
            continue;
        }

        std::string roma;
        const char* base = syllable(c);
        if (!base) {
            encode(c, out);
            doubleNext = false;
            continue;
        }
        roma = base;
        const bool digraph = (next == 0x3083 || next == 0x3085 || next == 0x3087);  // ゃゅょ
        if (digraph && roma.size() >= 2 && roma.back() == 'i') {
            const char vowel = (next == 0x3083) ? 'a' : (next == 0x3085) ? 'u' : 'o';
            roma.pop_back();
            if (roma == "sh" || roma == "ch" || roma == "j") {
                roma.push_back(vowel);
            } else {
                roma.push_back('y');
                roma.push_back(vowel);
            }
            ++k;
        }
        if (doubleNext) {
            out += (roma.compare(0, 2, "ch") == 0) ? 't' : roma[0];
            doubleNext = false;
        }
        out += roma;
    }
    return out;
}

size_t length(const std::string& text)
{
    size_t count = 0;
    size_t i = 0;
    while (i < text.size()) {
        uint32_t code = 0;
        i += decode(text, i, code);
        ++count;
    }
    return count;
}

}  // namespace kana
