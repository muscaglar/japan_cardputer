// What the app needs from the machine it runs on. The device and the simulator each provide one.
#pragma once

#include <cstdint>
#include <string>

#include "storage.h"

namespace ui {

struct Key {
    enum Code : uint8_t { None, Char, Enter, Backspace, Tab, Up, Down, Left, Right, Escape, Button };

    Code code = None;
    char ch   = 0;  // for Char: the character typed, with Shift applied
    bool fn   = false;
    bool ctrl = false;
    bool opt  = false;
    bool alt  = false;

    static Key character(char c)
    {
        Key k;
        k.code = Char;
        k.ch   = c;
        return k;
    }
    static Key of(Code code)
    {
        Key k;
        k.code = code;
        return k;
    }
};

// Storage (settings and progress) comes from core::Storage.
class Platform : public core::Storage {
public:
    virtual uint32_t millis()       = 0;
    virtual uint32_t random()       = 0;
    virtual int batteryPercent()    = 0;  // -1 when unknown
    virtual const char* boardName() = 0;

    virtual void tone(int hertz, int milliseconds) = 0;

    // Sound from the memory card. A path names a WAV file (16 bit, one channel) from the root
    // of the card, for example "/audio/f/signs/sign-eki.wav". Playing does not block: the
    // sound runs on while the app goes on.
    virtual bool hasCard()                          = 0;  // a memory card is in and can be read
    virtual bool play(const char* path, int volume) = 0;  // volume 1 to 5. false: no such file
    virtual bool playing()                          = 0;
    virtual void hush()                             = 0;  // stops what is playing
};

}  // namespace ui
