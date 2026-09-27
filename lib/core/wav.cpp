#include "wav.h"

#include <cstring>

namespace wav {

namespace {

constexpr uint32_t kRiffHeader   = 12;  // "RIFF", a size, "WAVE"
constexpr uint32_t kChunkHeader  = 8;   // four letters and a size
constexpr uint32_t kFormatLength = 16;  // what every format chunk holds
constexpr uint16_t kPlain        = 1;   // format tag of samples that are not compressed

uint16_t two(const uint8_t* p)
{
    return static_cast<uint16_t>(p[0] | (p[1] << 8));
}

uint32_t four(const uint8_t* p)
{
    return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) | (static_cast<uint32_t>(p[3]) << 24);
}

bool named(const uint8_t* p, const char* name)
{
    return std::memcmp(p, name, 4) == 0;
}

Verdict format(const uint8_t* p, Header& header)
{
    const uint16_t tag   = two(p);
    const uint16_t align = two(p + 12);
    header.channels      = two(p + 2);
    header.rate          = four(p + 4);
    header.bits          = two(p + 14);
    header.format        = true;
    if (tag != kPlain) {
        return Verdict::Compressed;
    }
    if (header.channels != 1) {
        return Verdict::Channels;
    }
    if (header.bits != 16) {
        return Verdict::Bits;
    }
    if (header.rate < kLowestRate || header.rate > kHighestRate) {
        return Verdict::Rate;
    }
    if (align != 2) {
        return Verdict::BadFormat;
    }
    return Verdict::Plays;
}

// Goes from chunk to chunk until the samples are found. bytes[0] is the byte at `at` in the file.
// Places are counted in 64 bits, so that no size a file may claim makes them wrap round.
Verdict walk(const uint8_t* bytes, size_t length, uint32_t at, uint32_t fileSize, Header& header)
{
    const uint64_t size = fileSize;
    const uint64_t end  = static_cast<uint64_t>(at) + length;
    uint64_t place      = at;
    for (;;) {
        if (place + kChunkHeader > size) {
            return Verdict::TooShort;
        }
        if (place + kChunkHeader > end) {
            header.next = static_cast<uint32_t>(place);
            return Verdict::More;
        }
        const uint8_t* chunk  = bytes + (place - at);
        const uint32_t inside = four(chunk + 4);
        const uint64_t body   = place + kChunkHeader;

        if (named(chunk, "fmt ")) {
            if (inside < kFormatLength) {
                return Verdict::BadFormat;
            }
            if (body + kFormatLength > size) {
                return Verdict::TooShort;
            }
            if (body + kFormatLength > end) {
                header.next = static_cast<uint32_t>(place);
                return Verdict::More;
            }
            const Verdict verdict = format(chunk + kChunkHeader, header);
            if (verdict != Verdict::Plays) {
                return verdict;
            }
        } else if (named(chunk, "data")) {
            if (!header.format) {
                return Verdict::NoFormat;
            }
            header.start = static_cast<uint32_t>(body);
            if (inside > size - body) {
                return Verdict::CutShort;
            }
            header.samples = inside / 2;
            header.bytes   = header.samples * 2;
            return header.samples ? Verdict::Plays : Verdict::NoSamples;
        }
        // A chunk of odd length is followed by one byte that belongs to nothing.
        place = body + inside + (inside & 1);
    }
}

}  // namespace

Verdict read(const uint8_t* bytes, size_t length, uint32_t fileSize, Header& header)
{
    header = Header();
    if (!bytes) {
        length = 0;
    }
    if (length > fileSize) {
        length = fileSize;
    }
    if (length >= 4 && !named(bytes, "RIFF")) {
        return Verdict::NotRiff;
    }
    if (fileSize < kRiffHeader) {
        return Verdict::TooShort;
    }
    if (length < kRiffHeader) {
        return Verdict::More;
    }
    if (!named(bytes + 8, "WAVE")) {
        return Verdict::NotWave;
    }
    return walk(bytes + kRiffHeader, length - kRiffHeader, kRiffHeader, fileSize, header);
}

Verdict readOn(const uint8_t* bytes, size_t length, uint32_t fileSize, Header& header)
{
    if (header.next < kRiffHeader) {
        return read(bytes, length, fileSize, header);
    }
    if (header.next >= fileSize) {
        return Verdict::TooShort;
    }
    if (!bytes) {
        length = 0;
    }
    if (length > fileSize - header.next) {
        length = fileSize - header.next;
    }
    return walk(bytes, length, header.next, fileSize, header);
}

const char* why(Verdict verdict)
{
    switch (verdict) {
        case Verdict::Plays:      return "";
        case Verdict::More:       return "the header goes on";
        case Verdict::TooShort:   return "ends before the samples start";
        case Verdict::NotRiff:    return "not a RIFF file";
        case Verdict::NotWave:    return "not a WAVE file";
        case Verdict::NoFormat:   return "samples before their format";
        case Verdict::BadFormat:  return "format chunk makes no sense";
        case Verdict::Compressed: return "compressed";
        case Verdict::Channels:   return "not one channel";
        case Verdict::Bits:       return "not 16 bit";
        case Verdict::Rate:       return "rate not 8000 to 48000";
        case Verdict::NoSamples:  return "no samples";
        case Verdict::CutShort:   return "fewer samples than promised";
    }
    return "unknown";
}

uint32_t milliseconds(const Header& header)
{
    if (header.rate == 0) {
        return 0;
    }
    return static_cast<uint32_t>(static_cast<uint64_t>(header.samples) * 1000 / header.rate);
}

}  // namespace wav
