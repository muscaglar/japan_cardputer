// Sound clips from the memory card, through the speaker or the earphones.
//
// A clip is a WAV file: 16 bit, one channel, 8000 to 48000 samples a second. It is read from the
// card piece by piece while it plays, so its length costs no memory.
#pragma once

#include <cstdint>

// Once at start, after M5Cardputer.begin(). Sets how loud beeps and clips are.
void soundBegin();

// Starts a clip and returns at once. What was playing ends, also when the answer is false.
// path: from the root of the card, for example "/audio/f/signs/sign-eki.wav". volume: 1 to 5.
// false: no card, no such file, or a file that cannot be played. soundWhyNot() says which.
bool soundPlay(const char* path, int volume);

// true from soundPlay() until the speaker has taken the last sample.
bool soundPlaying();

void soundHush();

// Hands the next piece of the clip to the speaker when it has room. Called from loop().
void soundTick();

// Why the last soundPlay() said no, in a few words. Empty if it said yes.
const char* soundWhyNot();

// What happened since the start, for checks on a device, where nobody may be listening.
struct SoundCount {
    uint32_t started     = 0;  // clips
    uint32_t refused     = 0;
    uint32_t gaps        = 0;  // times the speaker had nothing left in the middle of a clip
    uint32_t longestPlay = 0;  // ms that soundPlay() took at most
    uint32_t longestTick = 0;  // ms that soundTick() took at most
};
const SoundCount& soundCount();
