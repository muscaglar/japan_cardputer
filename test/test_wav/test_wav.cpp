#include <unity.h>

#include <cstring>
#include <string>
#include <vector>

#include "wav.h"

using wav::Header;
using wav::Verdict;

namespace {

typedef std::vector<uint8_t> Bytes;

const char* name(Verdict verdict)
{
    switch (verdict) {
        case Verdict::Plays:      return "Plays";
        case Verdict::More:       return "More";
        case Verdict::TooShort:   return "TooShort";
        case Verdict::NotRiff:    return "NotRiff";
        case Verdict::NotWave:    return "NotWave";
        case Verdict::NoFormat:   return "NoFormat";
        case Verdict::BadFormat:  return "BadFormat";
        case Verdict::Compressed: return "Compressed";
        case Verdict::Channels:   return "Channels";
        case Verdict::Bits:       return "Bits";
        case Verdict::Rate:       return "Rate";
        case Verdict::NoSamples:  return "NoSamples";
        case Verdict::CutShort:   return "CutShort";
    }
    return "?";
}

#define TEST_VERDICT(expected, actual) TEST_ASSERT_EQUAL_STRING(name(expected), name(actual))
#define TEST_VERDICT_MESSAGE(expected, actual, message) \
    TEST_ASSERT_EQUAL_STRING_MESSAGE(name(expected), name(actual), message)

void letters(Bytes& out, const char* four)
{
    out.insert(out.end(), four, four + 4);
}

void number16(Bytes& out, uint32_t value)
{
    out.push_back(static_cast<uint8_t>(value & 0xFF));
    out.push_back(static_cast<uint8_t>((value >> 8) & 0xFF));
}

void number32(Bytes& out, uint32_t value)
{
    number16(out, value & 0xFFFF);
    number16(out, value >> 16);
}

// "RIFF", a size that is put right by finish(), "WAVE".
Bytes riff()
{
    Bytes out;
    letters(out, "RIFF");
    number32(out, 0);
    letters(out, "WAVE");
    return out;
}

struct Format {
    uint32_t tag      = 1;
    uint32_t channels = 1;
    uint32_t rate     = 16000;
    uint32_t bits     = 16;
    int align         = -1;  // -1: as channels and bits demand
    uint32_t length   = 16;  // of the chunk. Longer ones are filled with zeros.
};

void format(Bytes& out, const Format& f = Format())
{
    const uint32_t align = f.align >= 0 ? static_cast<uint32_t>(f.align) : f.channels * f.bits / 8;
    Bytes body;
    number16(body, f.tag);
    number16(body, f.channels);
    number32(body, f.rate);
    number32(body, f.rate * align);
    number16(body, align);
    number16(body, f.bits);
    body.resize(f.length, 0);
    letters(out, "fmt ");
    number32(out, f.length);
    out.insert(out.end(), body.begin(), body.end());
    if (f.length & 1) {
        out.push_back(0);
    }
}

// Any chunk, with the byte that pads an odd length.
void chunk(Bytes& out, const char* id, uint32_t length, bool pad = true)
{
    letters(out, id);
    number32(out, length);
    for (uint32_t i = 0; i < length; ++i) {
        out.push_back(static_cast<uint8_t>('a' + i % 26));
    }
    if (pad && (length & 1)) {
        out.push_back(0);
    }
}

// The header of the samples, saying `claimed` bytes, followed by `present` bytes of them.
void data(Bytes& out, uint32_t claimed, uint32_t present)
{
    letters(out, "data");
    number32(out, claimed);
    for (uint32_t i = 0; i < present; ++i) {
        out.push_back(static_cast<uint8_t>(i));
    }
}

void data(Bytes& out, uint32_t length)
{
    data(out, length, length);
}

Bytes finish(Bytes out)
{
    const uint32_t inside = static_cast<uint32_t>(out.size()) - 8;
    out[4] = static_cast<uint8_t>(inside & 0xFF);
    out[5] = static_cast<uint8_t>((inside >> 8) & 0xFF);
    out[6] = static_cast<uint8_t>((inside >> 16) & 0xFF);
    out[7] = static_cast<uint8_t>((inside >> 24) & 0xFF);
    return out;
}

Bytes plain(uint32_t sampleBytes = 32000, const Format& f = Format())
{
    Bytes out = riff();
    format(out, f);
    data(out, sampleBytes);
    return finish(out);
}

Verdict whole(const Bytes& file, Header& header)
{
    return wav::read(file.data(), file.size(), static_cast<uint32_t>(file.size()), header);
}

Verdict whole(const Bytes& file)
{
    Header header;
    return whole(file, header);
}

// Reads a file as the device does: a window of bytes from the start, then, as long as the
// header goes on, a window from where it says. `hops` counts the windows after the first.
Verdict inWindows(const Bytes& file, size_t window, Header& header, int& hops)
{
    const uint32_t size = static_cast<uint32_t>(file.size());
    hops                = 0;
    Verdict verdict     = wav::read(file.data(), window < file.size() ? window : file.size(), size, header);
    while (verdict == Verdict::More && hops < 64) {
        ++hops;
        const size_t from = header.next;
        if (from >= file.size()) {
            return wav::readOn(nullptr, 0, size, header);
        }
        const size_t left = file.size() - from;
        verdict           = wav::readOn(file.data() + from, window < left ? window : left, size, header);
    }
    return verdict;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_the_plain_header_of_44_bytes()
{
    const Bytes file = plain(32000);
    TEST_ASSERT_EQUAL_UINT(44 + 32000, file.size());

    Header h;
    TEST_VERDICT(Verdict::Plays, whole(file, h));
    TEST_ASSERT_EQUAL_UINT32(44, h.start);
    TEST_ASSERT_EQUAL_UINT32(32000, h.bytes);
    TEST_ASSERT_EQUAL_UINT32(16000, h.samples);
    TEST_ASSERT_EQUAL_UINT32(16000, h.rate);
    TEST_ASSERT_EQUAL_UINT16(1, h.channels);
    TEST_ASSERT_EQUAL_UINT16(16, h.bits);
    TEST_ASSERT_TRUE(h.format);
    TEST_ASSERT_EQUAL_UINT32(1000, wav::milliseconds(h));
}

void test_the_first_bytes_are_enough()
{
    const Bytes file = plain(40000);
    const uint32_t size = static_cast<uint32_t>(file.size());
    for (size_t given = 44; given <= 256; ++given) {
        Header h;
        TEST_VERDICT(Verdict::Plays, wav::read(file.data(), given, size, h));
        TEST_ASSERT_EQUAL_UINT32(44, h.start);
        TEST_ASSERT_EQUAL_UINT32(40000, h.bytes);
    }
    // More bytes than the file holds are not looked at.
    Header h;
    TEST_VERDICT(Verdict::Plays, wav::read(file.data(), file.size() + 1000, size, h));
    TEST_ASSERT_EQUAL_UINT32(40000, h.bytes);
}

void test_rates()
{
    const uint32_t good[] = {8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000};
    for (uint32_t rate : good) {
        Format f;
        f.rate = rate;
        Header h;
        TEST_VERDICT(Verdict::Plays, whole(plain(2 * rate, f), h));
        TEST_ASSERT_EQUAL_UINT32(rate, h.rate);
        TEST_ASSERT_EQUAL_UINT32(1000, wav::milliseconds(h));
    }
    const uint32_t bad[] = {0, 1, 4000, 7999, 48001, 88200, 96000, 0xFFFFFFFF};
    for (uint32_t rate : bad) {
        Format f;
        f.rate = rate;
        Header h;
        TEST_VERDICT(Verdict::Rate, whole(plain(1000, f), h));
        TEST_ASSERT_EQUAL_UINT32(rate, h.rate);
    }
}

void test_a_list_chunk_before_the_samples()
{
    Bytes file = riff();
    format(file);
    chunk(file, "LIST", 26);
    data(file, 5000);
    file = finish(file);

    Header h;
    TEST_VERDICT(Verdict::Plays, whole(file, h));
    TEST_ASSERT_EQUAL_UINT32(12 + 24 + 8 + 26 + 8, h.start);
    TEST_ASSERT_EQUAL_UINT32(5000, h.bytes);
    TEST_ASSERT_EQUAL_UINT32(2500, h.samples);
}

// What afconvert writes, for one: a chunk that fills the header up to 4096 bytes.
void test_a_header_filled_up_to_4096_bytes()
{
    Bytes file = riff();
    format(file);
    chunk(file, "FLLR", 4044);
    data(file, 5526);
    file = finish(file);

    Header h;
    TEST_VERDICT(Verdict::Plays, whole(file, h));
    TEST_ASSERT_EQUAL_UINT32(4096, h.start);
    TEST_ASSERT_EQUAL_UINT32(2763, h.samples);
    TEST_ASSERT_EQUAL_UINT32(172, wav::milliseconds(h));

    // As the device reads it: 96 bytes from the start, 96 from where the header goes on.
    int hops = 0;
    TEST_VERDICT(Verdict::Plays, inWindows(file, 96, h, hops));
    TEST_ASSERT_EQUAL_INT(1, hops);
    TEST_ASSERT_EQUAL_UINT32(4096, h.start);
    TEST_ASSERT_EQUAL_UINT32(5526, h.bytes);
    TEST_ASSERT_EQUAL_UINT32(16000, h.rate);
}

void test_chunks_before_the_format_and_after_the_samples()
{
    Bytes file = riff();
    chunk(file, "JUNK", 28);
    chunk(file, "bext", 602);
    format(file);
    chunk(file, "fact", 4);
    data(file, 800);
    chunk(file, "LIST", 40);
    chunk(file, "id3 ", 101);
    file = finish(file);

    Header h;
    TEST_VERDICT(Verdict::Plays, whole(file, h));
    TEST_ASSERT_EQUAL_UINT32(12 + 36 + 610 + 24 + 12 + 8, h.start);
    TEST_ASSERT_EQUAL_UINT32(800, h.bytes);
}

void test_a_chunk_of_odd_length_with_its_padding_byte()
{
    for (uint32_t length = 0; length <= 9; ++length) {
        Bytes file = riff();
        format(file);
        chunk(file, "note", length);
        data(file, 640);
        file = finish(file);

        Header h;
        TEST_VERDICT(Verdict::Plays, whole(file, h));
        TEST_ASSERT_EQUAL_UINT32(12 + 24 + 8 + length + (length & 1) + 8, h.start);
        TEST_ASSERT_EQUAL_UINT32(0, h.start % 2);
        TEST_ASSERT_EQUAL_UINT32(640, h.bytes);
    }

    // Without the padding byte the next chunk is not where it must be: nothing is played by guessing.
    Bytes file = riff();
    format(file);
    chunk(file, "note", 5, false);
    data(file, 640);
    TEST_ASSERT_TRUE(whole(finish(file)) != Verdict::Plays);
}

void test_a_format_chunk_longer_than_16_bytes()
{
    const uint32_t lengths[] = {18, 40, 17};
    for (uint32_t length : lengths) {
        Format f;
        f.length = length;
        Header h;
        TEST_VERDICT(Verdict::Plays, whole(plain(320, f), h));
        TEST_ASSERT_EQUAL_UINT32(12 + 8 + length + (length & 1) + 8, h.start);
        TEST_ASSERT_EQUAL_UINT32(16000, h.rate);
    }
}

void test_a_format_chunk_that_makes_no_sense()
{
    for (uint32_t length = 0; length < 16; ++length) {
        Format f;
        f.length = length;
        TEST_VERDICT(Verdict::BadFormat, whole(plain(320, f)));
    }
    const int aligns[] = {0, 1, 3, 4};
    for (int align : aligns) {
        Format f;
        f.align = align;
        TEST_VERDICT(Verdict::BadFormat, whole(plain(320, f)));
    }
}

void test_samples_of_no_length()
{
    Header h;
    TEST_VERDICT(Verdict::NoSamples, whole(plain(0), h));
    TEST_ASSERT_EQUAL_UINT32(44, h.start);
    TEST_ASSERT_EQUAL_UINT32(0, h.samples);

    // One byte is not a sample.
    TEST_VERDICT(Verdict::NoSamples, whole(plain(1), h));
    TEST_ASSERT_EQUAL_UINT32(0, h.bytes);
}

void test_half_a_sample_at_the_end_is_left_out()
{
    Header h;
    TEST_VERDICT(Verdict::Plays, whole(plain(5), h));
    TEST_ASSERT_EQUAL_UINT32(2, h.samples);
    TEST_ASSERT_EQUAL_UINT32(4, h.bytes);

    TEST_VERDICT(Verdict::Plays, whole(plain(2), h));
    TEST_ASSERT_EQUAL_UINT32(1, h.samples);
    TEST_ASSERT_EQUAL_UINT32(2, h.bytes);
}

void test_more_samples_promised_than_the_file_holds()
{
    const uint32_t present = 1000;
    const uint32_t claims[] = {1001, 1002, 2000, 40000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFD4, 0xFFFFFFFE, 0xFFFFFFFF};
    for (uint32_t claimed : claims) {
        Bytes file = riff();
        format(file);
        data(file, claimed, present);
        Header h;
        TEST_VERDICT(Verdict::CutShort, whole(finish(file), h));
        TEST_ASSERT_EQUAL_UINT32(44, h.start);
        TEST_ASSERT_EQUAL_UINT32(0, h.bytes);
    }

    // The header alone, as a recorder leaves it that was switched off.
    Bytes file = riff();
    format(file);
    data(file, 32000, 0);
    TEST_VERDICT(Verdict::CutShort, whole(finish(file)));

    // Exactly what was promised plays, and so does a file with something after the samples.
    file = riff();
    format(file);
    data(file, 1000, 1000);
    TEST_VERDICT(Verdict::Plays, whole(finish(file)));
    file.push_back(0);
    file.push_back(0);
    file.push_back(0);
    TEST_VERDICT(Verdict::Plays, whole(finish(file)));
}

void test_headers_cut_off_at_every_length()
{
    const Bytes file = plain(32000);
    for (size_t length = 0; length < 44; ++length) {
        const Bytes cut(file.begin(), file.begin() + static_cast<long>(length));
        const std::string at = "cut off after " + std::to_string(length);
        Header h;
        TEST_VERDICT_MESSAGE(Verdict::TooShort, whole(cut, h), at.c_str());
        TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, h.samples, at.c_str());
    }
    // The whole header and not one sample.
    const Bytes header(file.begin(), file.begin() + 44);
    TEST_VERDICT(Verdict::CutShort, whole(header));
}

void test_headers_with_more_chunks_cut_off_at_every_length()
{
    Bytes file = riff();
    chunk(file, "JUNK", 7);
    format(file);
    chunk(file, "LIST", 26);
    data(file, 100);
    file = finish(file);
    const size_t start = 12 + 16 + 24 + 34 + 8;
    TEST_ASSERT_EQUAL_UINT(start + 100, file.size());

    for (size_t length = 0; length < file.size(); ++length) {
        const Bytes cut(file.begin(), file.begin() + static_cast<long>(length));
        const std::string at = "cut off after " + std::to_string(length);
        const Verdict expected = length < start ? Verdict::TooShort : Verdict::CutShort;
        TEST_VERDICT_MESSAGE(expected, whole(cut), at.c_str());
        for (size_t window = wav::kLeastBytes; window <= 96; window += 7) {
            Header h;
            int hops = 0;
            TEST_VERDICT_MESSAGE(expected, inWindows(cut, window, h, hops), at.c_str());
        }
    }
}

void test_a_file_that_ends_without_samples()
{
    Bytes file = riff();
    TEST_VERDICT(Verdict::TooShort, whole(finish(file)));
    format(file);
    TEST_VERDICT(Verdict::TooShort, whole(finish(file)));
    chunk(file, "LIST", 26);
    TEST_VERDICT(Verdict::TooShort, whole(finish(file)));
}

void test_not_riff()
{
    Bytes file = plain(320);
    const char* const others[] = {"RIFX", "RF64", "riff", "FORM", "OggS", "ID3\x04", "fLaC", "\xFF\xFB\x90\x64"};
    for (const char* other : others) {
        std::memcpy(file.data(), other, 4);
        TEST_VERDICT_MESSAGE(Verdict::NotRiff, whole(file), other);
    }

    const std::string text = "This is a note, not a sound. It is longer than any header of a sound file.";
    const Bytes note(text.begin(), text.end());
    TEST_VERDICT(Verdict::NotRiff, whole(note));

    const Bytes zeros(4096, 0);
    TEST_VERDICT(Verdict::NotRiff, whole(zeros));

    const Bytes ones(4096, 0xFF);
    TEST_VERDICT(Verdict::NotRiff, whole(ones));

    // Known from the first four bytes, however short the file.
    const Bytes five(text.begin(), text.begin() + 5);
    TEST_VERDICT(Verdict::NotRiff, whole(five));
}

void test_nothing_at_all()
{
    Header h;
    h.samples = 7;
    TEST_VERDICT(Verdict::TooShort, wav::read(nullptr, 0, 0, h));
    TEST_ASSERT_EQUAL_UINT32(0, h.samples);
    TEST_VERDICT(Verdict::TooShort, whole(Bytes()));
    TEST_VERDICT(Verdict::TooShort, wav::read(nullptr, 44, 0, h));

    // Nothing was handed over of a file that holds something: that is the caller's to mend.
    TEST_VERDICT(Verdict::More, wav::read(nullptr, 44, 5000, h));
    TEST_ASSERT_EQUAL_UINT32(0, h.next);
}

void test_not_wave()
{
    Bytes file = plain(320);
    const char* const others[] = {"AVI ", "WEBP", "wave", "WAVE"};
    for (const char* other : others) {
        std::memcpy(file.data() + 8, other, 4);
        const bool wave = std::strcmp(other, "WAVE") == 0;
        TEST_VERDICT_MESSAGE(wave ? Verdict::Plays : Verdict::NotWave, whole(file), other);
    }
}

void test_8_bit()
{
    const uint32_t widths[] = {8, 24, 32, 0, 12};
    for (uint32_t bits : widths) {
        Format f;
        f.bits  = bits;
        f.align = static_cast<int>(bits / 8);
        Header h;
        TEST_VERDICT(Verdict::Bits, whole(plain(320, f), h));
        TEST_ASSERT_EQUAL_UINT16(bits, h.bits);
        TEST_ASSERT_EQUAL_UINT32(0, h.samples);
    }
}

void test_two_channels()
{
    const uint32_t counts[] = {2, 0, 6, 65535};
    for (uint32_t channels : counts) {
        Format f;
        f.channels = channels;
        Header h;
        TEST_VERDICT(Verdict::Channels, whole(plain(320, f), h));
        TEST_ASSERT_EQUAL_UINT16(channels, h.channels);
    }
}

void test_compressed()
{
    // 0 unknown, 2 ADPCM, 3 float, 6 A-law, 7 mu-law, 0x11 IMA ADPCM, 0x55 MP3, 0xFFFE says
    // that the form is written further on.
    const uint32_t tags[] = {0, 2, 3, 6, 7, 0x11, 0x55, 0xFFFE, 0xFFFF};
    for (uint32_t tag : tags) {
        Format f;
        f.tag = tag;
        TEST_VERDICT(Verdict::Compressed, whole(plain(320, f)));
    }
    // Wrong in every way: the tag is named.
    Format f;
    f.tag      = 0x55;
    f.channels = 2;
    f.bits     = 8;
    f.rate     = 96000;
    TEST_VERDICT(Verdict::Compressed, whole(plain(320, f)));
    f.tag = 1;
    TEST_VERDICT(Verdict::Channels, whole(plain(320, f)));
    f.channels = 1;
    TEST_VERDICT(Verdict::Bits, whole(plain(320, f)));
}

void test_samples_before_their_format()
{
    Bytes file = riff();
    data(file, 320);
    format(file);
    Header h;
    TEST_VERDICT(Verdict::NoFormat, whole(finish(file), h));
    TEST_ASSERT_EQUAL_UINT32(0, h.samples);
}

void test_sizes_that_would_wrap_round()
{
    // Counted in 32 bits, the chunk after this one would seem to lie at byte 12 again: a walk
    // without end. And with 0xFFFFFFD4 it would seem to lie where the samples really are.
    const uint32_t sizes[] = {0xFFFFFFE0, 0xFFFFFFD4, 0xFFFFFFFF, 0xFFFFFFF8, 0x80000000, 1000000};
    for (uint32_t size : sizes) {
        Bytes file = riff();
        format(file);
        letters(file, "LIST");
        number32(file, size);
        data(file, 320);
        TEST_VERDICT(Verdict::TooShort, whole(finish(file)));
    }
}

void test_the_size_in_the_first_line_is_not_trusted()
{
    Bytes file = plain(320);
    const uint32_t sizes[] = {0, 4, 36, 0xFFFFFFFF};
    for (uint32_t size : sizes) {
        Bytes changed(file.begin(), file.begin() + 4);
        number32(changed, size);
        changed.insert(changed.end(), file.begin() + 8, file.end());
        Header h;
        TEST_VERDICT(Verdict::Plays, whole(changed, h));
        TEST_ASSERT_EQUAL_UINT32(320, h.bytes);
    }
}

void test_a_header_longer_than_the_bytes_given()
{
    Bytes file = riff();
    format(file);
    chunk(file, "LIST", 301);
    data(file, 4000);
    file = finish(file);
    const uint32_t size  = static_cast<uint32_t>(file.size());
    const uint32_t start = 12 + 24 + 8 + 302 + 8;

    Header h;
    TEST_VERDICT(Verdict::More, wav::read(file.data(), 96, size, h));
    TEST_ASSERT_EQUAL_UINT32(12 + 24 + 8 + 302, h.next);
    TEST_ASSERT_TRUE(h.format);
    TEST_ASSERT_EQUAL_UINT32(16000, h.rate);

    TEST_VERDICT(Verdict::Plays, wav::readOn(file.data() + h.next, 96, size, h));
    TEST_ASSERT_EQUAL_UINT32(start, h.start);
    TEST_ASSERT_EQUAL_UINT32(4000, h.bytes);
    TEST_ASSERT_EQUAL_UINT32(16000, h.rate);
}

void test_every_window_tells_the_same()
{
    std::vector<Bytes> files;
    files.push_back(plain(4000));
    {
        Bytes file = riff();
        chunk(file, "JUNK", 28);
        chunk(file, "bext", 603);
        format(file);
        chunk(file, "LIST", 131);
        data(file, 4000);
        files.push_back(finish(file));
    }
    {
        Format f;
        f.length = 40;
        files.push_back(plain(4000, f));
    }
    {
        Format f;
        f.bits = 8;
        Bytes file = riff();
        chunk(file, "JUNK", 90);
        format(file, f);
        data(file, 4000);
        files.push_back(finish(file));
    }
    {
        Bytes file = riff();
        format(file);
        chunk(file, "LIST", 200);
        data(file, 4000, 3999);
        files.push_back(finish(file));
    }
    {
        Bytes file = riff();
        chunk(file, "LIST", 200);
        data(file, 4000);
        format(file);
        files.push_back(finish(file));
    }

    for (size_t i = 0; i < files.size(); ++i) {
        Header expected;
        const Verdict verdict = whole(files[i], expected);
        TEST_ASSERT_TRUE(verdict != Verdict::More);
        for (size_t window = wav::kLeastBytes; window <= 700; ++window) {
            const std::string at = "file " + std::to_string(i) + ", window " + std::to_string(window);
            Header h;
            int hops = 0;
            TEST_VERDICT_MESSAGE(verdict, inWindows(files[i], window, h, hops), at.c_str());
            TEST_ASSERT_EQUAL_UINT32_MESSAGE(expected.start, h.start, at.c_str());
            TEST_ASSERT_EQUAL_UINT32_MESSAGE(expected.bytes, h.bytes, at.c_str());
            TEST_ASSERT_EQUAL_UINT32_MESSAGE(expected.rate, h.rate, at.c_str());
            TEST_ASSERT_EQUAL_UINT16_MESSAGE(expected.bits, h.bits, at.c_str());
            // One window for each chunk before the samples at most.
            TEST_ASSERT_LESS_OR_EQUAL_INT_MESSAGE(4, hops, at.c_str());
            // The device reads four windows of 96 bytes and then gives up.
            if (window >= 96) {
                TEST_ASSERT_LESS_OR_EQUAL_INT_MESSAGE(3, hops, at.c_str());
            }
        }
    }
}

void test_a_window_too_small_asks_for_the_same_place_again()
{
    const Bytes file = plain(4000);
    const uint32_t size = static_cast<uint32_t>(file.size());
    Header h;
    TEST_VERDICT(Verdict::More, wav::read(file.data(), 11, size, h));
    TEST_ASSERT_EQUAL_UINT32(0, h.next);
    TEST_VERDICT(Verdict::More, wav::readOn(file.data(), 35, size, h));
    TEST_ASSERT_EQUAL_UINT32(12, h.next);
    TEST_VERDICT(Verdict::More, wav::readOn(file.data() + 12, 23, size, h));
    TEST_ASSERT_EQUAL_UINT32(12, h.next);
    TEST_VERDICT(Verdict::More, wav::readOn(file.data() + 12, 24, size, h));
    TEST_ASSERT_EQUAL_UINT32(36, h.next);
    TEST_VERDICT(Verdict::More, wav::readOn(file.data() + 36, 7, size, h));
    TEST_ASSERT_EQUAL_UINT32(36, h.next);
    TEST_VERDICT(Verdict::Plays, wav::readOn(file.data() + 36, 8, size, h));
    TEST_ASSERT_EQUAL_UINT32(44, h.start);
    TEST_ASSERT_EQUAL_UINT32(4000, h.bytes);
}

void test_nothing_handed_over_when_reading_on()
{
    const Bytes file = plain(4000);
    const uint32_t size = static_cast<uint32_t>(file.size());
    Header h;
    TEST_VERDICT(Verdict::More, wav::read(file.data(), 36, size, h));
    TEST_ASSERT_EQUAL_UINT32(36, h.next);
    // A length without bytes: nothing is looked at, and the same place is asked for again.
    TEST_VERDICT(Verdict::More, wav::readOn(nullptr, 96, size, h));
    TEST_ASSERT_EQUAL_UINT32(36, h.next);
    TEST_ASSERT_EQUAL_UINT32(0, h.samples);
    TEST_VERDICT(Verdict::Plays, wav::readOn(file.data() + 36, 96, size, h));
    TEST_ASSERT_EQUAL_UINT32(4000, h.bytes);
}

void test_bytes_beyond_the_end_of_the_file_are_not_looked_at()
{
    // The caller's buffer holds what an earlier file left in it.
    const Bytes other = plain(4000);
    const std::string text = "not a sound";
    Bytes stale(text.begin(), text.end());
    stale.resize(96, 0);
    for (uint32_t size = 0; size < 4; ++size) {
        Header h;
        TEST_VERDICT(Verdict::TooShort, wav::read(stale.data(), stale.size(), size, h));
        TEST_VERDICT(Verdict::TooShort, wav::read(other.data(), other.size(), size, h));
    }
    for (uint32_t size = 4; size < 44; ++size) {
        const std::string at = "a file of " + std::to_string(size);
        Header h;
        TEST_VERDICT_MESSAGE(Verdict::NotRiff, wav::read(stale.data(), stale.size(), size, h), at.c_str());
        TEST_VERDICT_MESSAGE(Verdict::TooShort, wav::read(other.data(), other.size(), size, h), at.c_str());
        TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, h.samples, at.c_str());
    }
    // Reading on: the samples seem to be there, but the file ends before them.
    Header h;
    TEST_VERDICT(Verdict::More, wav::read(other.data(), 36, 44, h));
    TEST_VERDICT(Verdict::CutShort, wav::readOn(other.data() + 36, 96, 44, h));
    h        = Header();
    h.format = true;
    h.next   = 36;
    TEST_VERDICT(Verdict::TooShort, wav::readOn(other.data() + 36, 96, 43, h));
    TEST_VERDICT(Verdict::More, wav::read(other.data(), 36, 1044, h));
    TEST_VERDICT(Verdict::CutShort, wav::readOn(other.data() + 36, 96, 1044, h));
    TEST_ASSERT_EQUAL_UINT32(0, h.bytes);
}

void test_reading_on_beyond_the_end()
{
    const Bytes file = plain(4000);
    const uint32_t size = static_cast<uint32_t>(file.size());
    Header h;
    h.format = true;
    h.next   = size;
    TEST_VERDICT(Verdict::TooShort, wav::readOn(file.data(), 64, size, h));
    h.next = 0xFFFFFFFF;
    TEST_VERDICT(Verdict::TooShort, wav::readOn(file.data(), 64, size, h));
    h.next = size - 4;
    TEST_VERDICT(Verdict::TooShort, wav::readOn(file.data() + size - 4, 64, size, h));
}

void test_every_refusal_has_its_words()
{
    TEST_ASSERT_EQUAL_STRING("", wav::why(Verdict::Plays));
    const Verdict all[] = {Verdict::More,      Verdict::TooShort,   Verdict::NotRiff,  Verdict::NotWave,
                           Verdict::NoFormat,  Verdict::BadFormat,  Verdict::Compressed, Verdict::Channels,
                           Verdict::Bits,      Verdict::Rate,       Verdict::NoSamples,  Verdict::CutShort};
    const size_t count = sizeof(all) / sizeof(all[0]);
    for (size_t i = 0; i < count; ++i) {
        const char* words = wav::why(all[i]);
        TEST_ASSERT_NOT_NULL(words);
        TEST_ASSERT_TRUE_MESSAGE(std::strlen(words) > 0, name(all[i]));
        TEST_ASSERT_TRUE_MESSAGE(std::strlen(words) <= 30, name(all[i]));
        for (size_t j = 0; j < i; ++j) {
            TEST_ASSERT_TRUE_MESSAGE(std::strcmp(words, wav::why(all[j])) != 0, name(all[i]));
        }
    }
}

void test_how_long_it_plays()
{
    Header h;
    TEST_ASSERT_EQUAL_UINT32(0, wav::milliseconds(h));
    h.rate    = 16000;
    h.samples = 24000;
    TEST_ASSERT_EQUAL_UINT32(1500, wav::milliseconds(h));
    h.rate    = 8000;
    h.samples = 0x7FFFFFFF;  // no wrapping on the way
    TEST_ASSERT_EQUAL_UINT32(268435455, wav::milliseconds(h));
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_the_plain_header_of_44_bytes);
    RUN_TEST(test_the_first_bytes_are_enough);
    RUN_TEST(test_rates);
    RUN_TEST(test_a_list_chunk_before_the_samples);
    RUN_TEST(test_a_header_filled_up_to_4096_bytes);
    RUN_TEST(test_chunks_before_the_format_and_after_the_samples);
    RUN_TEST(test_a_chunk_of_odd_length_with_its_padding_byte);
    RUN_TEST(test_a_format_chunk_longer_than_16_bytes);
    RUN_TEST(test_a_format_chunk_that_makes_no_sense);
    RUN_TEST(test_samples_of_no_length);
    RUN_TEST(test_half_a_sample_at_the_end_is_left_out);
    RUN_TEST(test_more_samples_promised_than_the_file_holds);
    RUN_TEST(test_headers_cut_off_at_every_length);
    RUN_TEST(test_headers_with_more_chunks_cut_off_at_every_length);
    RUN_TEST(test_a_file_that_ends_without_samples);
    RUN_TEST(test_not_riff);
    RUN_TEST(test_nothing_at_all);
    RUN_TEST(test_not_wave);
    RUN_TEST(test_8_bit);
    RUN_TEST(test_two_channels);
    RUN_TEST(test_compressed);
    RUN_TEST(test_samples_before_their_format);
    RUN_TEST(test_sizes_that_would_wrap_round);
    RUN_TEST(test_the_size_in_the_first_line_is_not_trusted);
    RUN_TEST(test_a_header_longer_than_the_bytes_given);
    RUN_TEST(test_every_window_tells_the_same);
    RUN_TEST(test_a_window_too_small_asks_for_the_same_place_again);
    RUN_TEST(test_nothing_handed_over_when_reading_on);
    RUN_TEST(test_bytes_beyond_the_end_of_the_file_are_not_looked_at);
    RUN_TEST(test_reading_on_beyond_the_end);
    RUN_TEST(test_every_refusal_has_its_words);
    RUN_TEST(test_how_long_it_plays);
    return UNITY_END();
}
