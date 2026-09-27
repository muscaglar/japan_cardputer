#include "kana.h"

#include <cstdint>
#include <cstring>

#include "romaji.h"

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

std::string toRomaji(const std::string& text, bool doubledN)
{
    const std::string h = toHiragana(text);
    std::vector<std::string> units;  // one kana each, UTF-8
    std::vector<uint32_t> codes;
    size_t i = 0;
    while (i < h.size()) {
        uint32_t code  = 0;
        const size_t n = decode(h, i, code);
        units.emplace_back(h, i, n);
        codes.push_back(code);
        i += n;
    }

    // First the spelling of every unit, so that ん and っ can look at what follows them.
    struct Piece {
        std::string roma;
        uint32_t code;  // っ, ん, ー, or 0 for everything else
    };
    std::vector<Piece> pieces;
    for (size_t k = 0; k < codes.size(); ++k) {
        const uint32_t c = codes[k];
        if (c == 0x3063 || c == 0x3093 || c == 0x30FC) {
            pieces.push_back(Piece{std::string(), c});
            continue;
        }
        std::string roma;
        if (k + 1 < codes.size() && isSmall(codes[k + 1])) {
            roma = romaji::spelling(units[k] + units[k + 1]);
            if (!roma.empty()) {
                ++k;
            }
        }
        if (roma.empty()) {
            roma = romaji::spelling(units[k]);
        }
        if (roma.empty()) {
            roma = units[k];  // not kana: shown as it is
        }
        pieces.push_back(Piece{roma, 0});
    }

    std::string out;
    for (size_t k = 0; k < pieces.size(); ++k) {
        const Piece& piece   = pieces[k];
        const std::string* next = (k + 1 < pieces.size() && pieces[k + 1].code == 0) ? &pieces[k + 1].roma : nullptr;
        if (piece.code == 0x30FC) {  // ー repeats the vowel before it
            const char v = lastVowel(out);
            out.push_back(v ? v : '-');
        } else if (piece.code == 0x3093) {  // ん
            if (doubledN) {
                out += "nn";
            } else if (next && !next->empty() && std::strchr("aiueoy", (*next)[0]) != nullptr) {
                out += "n'";
            } else {
                out += "n";
            }
        } else if (piece.code == 0x3063) {  // っ doubles the consonant that follows
            const bool consonant = next && !next->empty() && (*next)[0] >= 'a' && (*next)[0] <= 'z' &&
                                   std::strchr("aiueon", (*next)[0]) == nullptr;
            if (!consonant) {
                out += "xtsu";
            } else if (next->compare(0, 2, "ch") == 0) {
                out.push_back('t');
            } else {
                out.push_back((*next)[0]);
            }
        } else {
            out += piece.roma;
        }
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
