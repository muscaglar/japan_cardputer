// What the app needs from the machine it runs on. The device and the simulator each provide one.
#pragma once

#include <cstdint>
#include <string>

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

class Platform {
public:
    virtual ~Platform() = default;

    virtual uint32_t millis()      = 0;
    virtual uint32_t random()      = 0;
    virtual int batteryPercent()   = 0;  // -1 when unknown
    virtual const char* boardName() = 0;

    // Small text files that survive a restart: settings and progress.
    virtual bool load(const char* name, std::string& text)         = 0;
    virtual bool save(const char* name, const std::string& text)   = 0;
    virtual bool append(const char* name, const std::string& line) = 0;

    virtual void tone(int hertz, int milliseconds) = 0;
};

}  // namespace ui
