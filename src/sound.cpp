#include "sound.h"

#include <M5Cardputer.h>

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cerrno>
#include <cstdio>

#include "card.h"
#include "wav.h"

namespace {

// Where card.cpp puts the card: the place SD.begin() chooses when it is not given one. The file
// is read with open() and read() and not through cardFiles(), because a File takes 4096 bytes
// from the heap for as long as it is open and looks the name up twice.
const char kMount[] = "/sd";

constexpr size_t kPathLength = 128;
constexpr size_t kWindow     = 96;  // bytes of the header read at a time
constexpr int kWindows       = 4;   // a header that needs more than these is refused
constexpr uint32_t kSector   = 512;

// Of the speaker's eight channels. Beeps take the highest one that is free.
constexpr uint8_t kChannel = 0;

// The speaker does not copy what it is given. It plays one piece and keeps one waiting, so the
// third is always free to be filled.
constexpr size_t kPieces       = 3;
constexpr size_t kPieceSamples = 3072;  // 192 ms at 16000 samples a second, 64 ms at 48000
constexpr size_t kPieceBytes   = kPieceSamples * sizeof(int16_t);

// How long a new clip waits for the one before to let go of its pieces.
constexpr uint32_t kLetGo = 100;  // ms

// The least time between two pieces. The speaker says "one" both for a piece that plays and for
// one it has not yet taken from the queue; after this long it has taken it. No piece but the
// last is shorter than 58 ms, so nothing is lost by waiting.
constexpr uint32_t kTaken = 16;  // ms

// What the speaker makes of a sample, in parts of 65536 of its recorded height:
// 2 x magnification x whole² x channel² / 2^20. The 2 is there because a clip of one channel
// counts as left and right, and the speaker adds the two. The magnification is what M5Unified
// sets for the Cardputer.
constexpr uint32_t kMagnification = 16;
constexpr uint32_t height(uint32_t whole, uint32_t channel)
{
    return static_cast<uint32_t>((2ull * kMagnification * whole * whole * channel * channel) >> 20);
}

// With the whole at 255, a channel at 181 plays a clip at 0.99 of the height it was recorded
// with: anything louder would cut the peaks off. Each step below halves the height (6 dB), so
// volume 3 is a quarter.
constexpr uint8_t kWhole        = 255;
constexpr uint8_t kLoudness[5]  = {45, 64, 90, 128, 181};
constexpr uint8_t kBeepLoudness = 140;  // beeps stay as loud as they were with the whole at 140

static_assert(height(kWhole, kLoudness[4]) <= 65536, "volume 5 cuts the peaks off");
static_assert(height(kWhole, kLoudness[4] + 1) > 65536, "volume 5 could be louder");

// A card that was taken out, or has lost its contact, answers nothing, and every question put
// to it holds loop() up for about a second. After one such answer it is left alone for this
// long: clips are refused without asking it.
constexpr uint32_t kLeftAlone = 10000;  // ms

enum class State : uint8_t {
    Silent,
    Feeding,  // the file is open and has more to give
    Fading,   // all of it is with the speaker
};

int16_t pieces[kPieces][kPieceSamples];
State state      = State::Silent;
int file         = -1;
uint32_t start   = 0;      // where the samples start in the file
uint32_t left    = 0;      // bytes of samples not yet read
uint32_t rate    = 0;
uint32_t since   = 0;      // when the clip was asked for
uint32_t fedAt   = 0;      // when the speaker was given the last piece
size_t turn      = 0;      // the piece to fill next
uint8_t loudness = 0;
uint32_t lostAt  = 0;      // when the card did not answer
bool lost        = false;  // it is left alone for now
bool fresh       = false;  // nothing of this clip has gone to the speaker yet
const char* whyNot = "";
SoundCount count;

void note(uint32_t& longest, uint32_t begun)
{
    const uint32_t took = (micros() - begun + 500) / 1000;
    if (took > longest) {
        longest = took;
    }
}

void closeFile()
{
    if (file >= 0) {
        ::close(file);
        file = -1;
    }
}

// After open(), read() or lseek() said no: whether it was the card that did not answer, and not
// the file that was missing or wrong. These are the numbers the file system of the framework
// gives for a card that fails, is not ready, or takes too long.
bool cardSilent()
{
    if (errno != EIO && errno != ENODEV && errno != ETIMEDOUT) {
        return false;
    }
    lost   = true;
    lostAt = millis();
    return true;
}

const char* unread()
{
    return cardSilent() ? "card does not answer" : "cannot be read";
}

// Opens the file and reads its header. Returns why it cannot be played, or "" with the file
// open at its first sample.
const char* openClip(const char* path)
{
    if (!cardReady()) {
        return "no card";
    }
    if (!soundCardAnswers()) {
        return "card does not answer";
    }
    if (!M5Cardputer.Speaker.isEnabled()) {
        return "no speaker";
    }
    if (!path || path[0] != '/') {
        return "no such file";
    }
    char full[kPathLength];
    const int length = std::snprintf(full, sizeof(full), "%s%s", kMount, path);
    if (length < 0 || length >= static_cast<int>(sizeof(full))) {
        return "path too long";
    }
    errno = 0;
    file  = ::open(full, O_RDONLY);
    if (file < 0) {
        return cardSilent() ? "card does not answer" : "no such file";
    }
    struct stat about;
    if (::fstat(file, &about) != 0 || about.st_size < 0) {
        return "cannot be read";
    }
    if (!S_ISREG(about.st_mode)) {
        return "not a file";
    }
    const uint32_t size = static_cast<uint32_t>(about.st_size);

    uint8_t window[kWindow];
    wav::Header header;
    wav::Verdict verdict = wav::Verdict::More;
    for (int i = 0; i < kWindows && verdict == wav::Verdict::More; ++i) {
        if (::lseek(file, static_cast<off_t>(header.next), SEEK_SET) < 0) {
            return unread();
        }
        const ssize_t got = ::read(file, window, sizeof(window));
        if (got < 0) {
            return unread();
        }
        verdict = wav::readOn(window, static_cast<size_t>(got), size, header);
    }
    if (verdict != wav::Verdict::Plays) {
        return wav::why(verdict);
    }
    if (::lseek(file, static_cast<off_t>(header.start), SEEK_SET) < 0) {
        return unread();
    }
    start = header.start;
    left  = header.bytes;
    rate  = header.rate;
    return "";
}

// Reads one piece and hands it to the speaker. `waiting` is what the speaker still holds.
void feed(size_t waiting)
{
    auto& speaker = M5Cardputer.Speaker;
    size_t want   = kPieceBytes;
    if (fresh) {
        want -= start % kSector;  // every later piece then begins with a sector of the card
    }
    if (want > left) {
        want = left;
    }
    int16_t* piece    = pieces[turn];
    errno             = 0;
    const ssize_t got = ::read(file, piece, want);
    if (got < 0) {
        cardSilent();
    }
    const size_t samples = got > 0 ? static_cast<size_t>(got) / sizeof(int16_t) : 0;

    bool taken = false;
    if (samples > 0) {
        if (fresh) {
            speaker.setChannelVolume(kChannel, loudness);
        } else if (waiting == 0) {
            ++count.gaps;
        }
        taken = speaker.playRaw(piece, samples, rate, false, 1, kChannel, fresh);
    }
    if (!taken) {
        // The card was taken out, or the speaker is in other hands.
        closeFile();
        state = fresh ? State::Silent : State::Fading;
        return;
    }
    fresh = false;
    fedAt = millis();
    turn  = (turn + 1) % kPieces;
    left  = (static_cast<size_t>(got) == want) ? left - static_cast<uint32_t>(want) : 0;
    if (left == 0) {
        closeFile();
        state = State::Fading;
    }
}

}  // namespace

void soundBegin()
{
    // The speaker itself starts with the first sound: until then the amplifier stays off.
    M5Cardputer.Speaker.setVolume(kWhole);
    M5Cardputer.Speaker.setAllChannelVolume(kBeepLoudness);
}

bool soundPlay(const char* path, int volume)
{
    const uint32_t begun = micros();
    soundHush();
    whyNot = openClip(path);
    const bool plays = (whyNot[0] == '\0');
    if (plays) {
        const int level = volume < 1 ? 1 : (volume > 5 ? 5 : volume);
        loudness        = kLoudness[level - 1];
        state           = State::Feeding;
        fresh           = true;
        since           = millis();
        ++count.started;
    } else {
        closeFile();
        ++count.refused;
    }
    note(count.longestPlay, begun);
    return plays;
}

bool soundPlaying()
{
    if (state == State::Fading && M5Cardputer.Speaker.isPlaying(kChannel) == 0) {
        state = State::Silent;
    }
    return state != State::Silent;
}

void soundHush()
{
    closeFile();
    left  = 0;
    state = State::Silent;
    M5Cardputer.Speaker.stop(kChannel);
}

void soundTick()
{
    if (state == State::Silent) {
        return;
    }
    const size_t waiting = M5Cardputer.Speaker.isPlaying(kChannel);
    if (state == State::Fading) {
        if (waiting == 0) {
            state = State::Silent;
        }
        return;
    }
    // A new clip starts when the speaker has let go of every piece of the one before. Later
    // pieces follow as soon as none is waiting behind the one that plays: asking the speaker
    // to take one earlier would hold up everything until it has room.
    const uint32_t now = millis();
    if (fresh ? (waiting != 0 && now - since < kLetGo) : (waiting >= 2 || now - fedAt < kTaken)) {
        return;
    }
    const uint32_t begun = micros();
    feed(waiting);
    note(count.longestTick, begun);
}

bool soundCardAnswers()
{
    if (lost && millis() - lostAt >= kLeftAlone) {
        lost = false;
    }
    return !lost;
}

const char* soundWhyNot()
{
    return whyNot;
}

const SoundCount& soundCount()
{
    return count;
}
