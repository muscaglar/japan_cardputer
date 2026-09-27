// The header of a WAV file: where the samples start, how many there are and in what form, or why
// the file cannot be played. The device plays one form only: 16 bit, one channel, not compressed,
// 8000 to 48000 samples a second.
// Pure C++, no hardware: the caller reads the bytes and hands them over.
#pragma once

#include <cstddef>
#include <cstdint>

namespace wav {

constexpr uint32_t kLowestRate  = 8000;
constexpr uint32_t kHighestRate = 48000;

// Hand over at least this many bytes at a time, or all that is left of the file.
constexpr size_t kLeastBytes = 32;

enum class Verdict : uint8_t {
    Plays,
    More,        // the header goes on beyond the bytes given: read on at Header::next
    TooShort,    // the file ends before its samples start
    NotRiff,
    NotWave,
    NoFormat,    // the samples come before the chunk that says in what form they are
    BadFormat,   // the format chunk is too short or contradicts itself
    Compressed,  // format tag other than 1
    Channels,    // not one channel
    Bits,        // not 16 bit
    Rate,        // fewer than 8000 or more than 48000 samples a second
    NoSamples,   // the data chunk is empty
    CutShort,    // the header promises more samples than the file holds
};

struct Header {
    uint32_t rate     = 0;  // samples a second
    uint16_t channels = 0;
    uint16_t bits     = 0;  // per sample
    uint32_t start    = 0;  // where the samples start, in bytes from the start of the file
    uint32_t bytes    = 0;  // bytes of whole samples from there
    uint32_t samples  = 0;
    uint32_t next     = 0;      // after More: the place in the file to read on from
    bool format       = false;  // the format chunk has been read
};

// Reads the header from the first `length` bytes of a file of `fileSize` bytes. The header is
// filled in as far as it was read, also when the file is refused.
Verdict read(const uint8_t* bytes, size_t length, uint32_t fileSize, Header& header);

// After More: goes on with `length` bytes read from header.next.
Verdict readOn(const uint8_t* bytes, size_t length, uint32_t fileSize, Header& header);

// In a few words, for a report. Empty for Plays.
const char* why(Verdict verdict);

// How long the samples take to play.
uint32_t milliseconds(const Header& header);

}  // namespace wav
