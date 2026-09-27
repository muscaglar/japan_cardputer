#include "console.h"

#include "sound.h"

#include <Arduino.h>

#include <cstring>
#include <string>

#include "files.h"

#if DEVICE_CONSOLE

namespace {

constexpr size_t kLongestLine = 200;

std::string pending;
bool overflowed = false;

// Every answer ends here. The flush matters: without it the last bytes of an answer sometimes
// stayed on the device until the next answer pushed them out.
void reply(const char* line)
{
    Serial.println(line);
    Serial.flush();
}

// Base64 written straight to the serial port in small pieces, so that no large buffer is needed.
class Base64Writer {
public:
    void put(uint8_t byte)
    {
        _group[_held++] = byte;
        if (_held == 3) {
            emit(3);
        }
    }

    void finish()
    {
        if (_held > 0) {
            emit(_held);
        }
        flush();
    }

private:
    void emit(int count)
    {
        static const char kAlphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        const uint32_t v = (static_cast<uint32_t>(_group[0]) << 16) |
                           (static_cast<uint32_t>(count > 1 ? _group[1] : 0) << 8) |
                           static_cast<uint32_t>(count > 2 ? _group[2] : 0);
        _out[_used++] = kAlphabet[(v >> 18) & 63];
        _out[_used++] = kAlphabet[(v >> 12) & 63];
        _out[_used++] = (count > 1) ? kAlphabet[(v >> 6) & 63] : '=';
        _out[_used++] = (count > 2) ? kAlphabet[v & 63] : '=';
        _held = 0;
        if (_used >= sizeof(_out)) {
            flush();
        }
    }

    void flush()
    {
        if (_used > 0) {
            Serial.write(reinterpret_cast<const uint8_t*>(_out), _used);
            _used = 0;
        }
    }

    uint8_t _group[3] = {0, 0, 0};
    int _held         = 0;
    char _out[64];
    size_t _used = 0;
};

void sendFrame(ui::App& app, M5Canvas& canvas)
{
    if (app.draw(canvas)) {
        canvas.pushSprite(0, 0);
    }
    const uint8_t* pixels = static_cast<const uint8_t*>(canvas.getBuffer());
    const int count       = ui::kWidth * ui::kHeight;
    Serial.printf("#frame %d %d %d ", static_cast<int>(app.current()), ui::kWidth, ui::kHeight);
    if (!pixels) {
        reply("");
        return;
    }
    Base64Writer out;
    int i = 0;
    while (i < count) {
        const uint8_t high = pixels[i * 2];
        const uint8_t low  = pixels[i * 2 + 1];
        int run            = 1;
        while (i + run < count && run < 255 && pixels[(i + run) * 2] == high && pixels[(i + run) * 2 + 1] == low) {
            ++run;
        }
        out.put(static_cast<uint8_t>(run));
        out.put(high);
        out.put(low);
        i += run;
    }
    out.finish();
    reply("");
}

void sendInfo(ui::App& app, ui::Platform& platform)
{
    // the app's own account, with what only the device knows added at the end
    std::string text = app.describe();
    if (!text.empty() && text.back() == '}') {
        text.pop_back();
    }
    Serial.printf("#info %s,\"board\":\"%s\",\"battery\":%d,\"heapFree\":%u,\"heapLargestBlock\":%u,"
                  "\"heapLowest\":%u,\"uptimeMs\":%lu",
                  text.c_str(), platform.boardName(), platform.batteryPercent(),
                  static_cast<unsigned>(ESP.getFreeHeap()), static_cast<unsigned>(ESP.getMaxAllocHeap()),
                  static_cast<unsigned>(ESP.getMinFreeHeap()), static_cast<unsigned long>(millis()));
    // Sound, for checks where nobody listens: what was started, refused, and how long it held the device up.
    const SoundCount& sound = soundCount();
    Serial.printf(",\"soundPlaying\":%s,\"soundWhyNot\":\"%s\",\"soundStarted\":%u,\"soundRefused\":%u,"
                  "\"soundGaps\":%u,\"soundLongestPlay\":%u,\"soundLongestTick\":%u}",
                  soundPlaying() ? "true" : "false", soundWhyNot(), static_cast<unsigned>(sound.started),
                  static_cast<unsigned>(sound.refused), static_cast<unsigned>(sound.gaps),
                  static_cast<unsigned>(sound.longestPlay), static_cast<unsigned>(sound.longestTick));
    reply("");
}

bool namedKey(const std::string& name, ui::Key& key)
{
    static const struct {
        const char* name;
        ui::Key::Code code;
    } kNames[] = {
        {"Enter", ui::Key::Enter}, {"Backspace", ui::Key::Backspace}, {"Tab", ui::Key::Tab},
        {"Up", ui::Key::Up},       {"Down", ui::Key::Down},           {"Left", ui::Key::Left},
        {"Right", ui::Key::Right}, {"Esc", ui::Key::Escape},          {"Button", ui::Key::Button},
    };
    for (const auto& entry : kNames) {
        if (name == entry.name) {
            key = ui::Key::of(entry.code);
            return true;
        }
    }
    return false;
}

// Returns true if the app was given a key.
bool carryOut(const std::string& line, ui::App& app, M5Canvas& canvas, ui::Platform& platform)
{
    const size_t space        = line.find(' ');
    const std::string command = line.substr(0, space);
    const std::string rest    = (space == std::string::npos) ? std::string() : line.substr(space + 1);

    if (command == "frame") {
        sendFrame(app, canvas);
        return false;
    }
    if (command == "info") {
        sendInfo(app, platform);
        return false;
    }
    if (command == "keep" || command == "back") {
        const bool ok = (command == "keep") ? app.keepAside() : app.bringBack();
        reply(ok ? "#done 1" : "#done 0");
        return true;
    }
    if (command == "fresh") {
        // Refused unless progress was kept aside first, so that a slip cannot cost what was learnt.
        std::string kept;
        if (!platform.load("settings.bak", kept) || kept.empty()) {
            reply("#error keep first");
            return false;
        }
        app.startFresh();
        reply("#done 1");
        return true;
    }
    if (command == "sitting") {
        const deck::Deck* deck = rest.empty() ? nullptr : deck::find(rest.c_str());
        if (!rest.empty() && !deck) {
            reply("#done 0");
            return false;
        }
        app.startSitting(deck);
        reply("#done 1");
        return true;
    }
    if (command == "play") {
        // play <path> [volume]: a clip from the memory card, without the app deciding anything
        const size_t gap   = rest.find(' ');
        const std::string path = rest.substr(0, gap);
        const int volume   = (gap == std::string::npos) ? 3 : atoi(rest.c_str() + gap + 1);
        if (soundPlay(path.c_str(), volume >= 1 && volume <= 5 ? volume : 3)) {
            reply("#ok");
        } else {
            Serial.printf("#error %s", soundWhyNot());
            reply("");
        }
        return false;
    }
    if (command == "hush") {
        soundHush();
        reply("#ok");
        return false;
    }
    if (command == "restart") {
        reply("#ok");
        delay(100);
        ESP.restart();
        return false;
    }
    if (command == "key") {
        ui::Key key;
        if (!namedKey(rest, key)) {
            reply("#error unknown key");
            return false;
        }
        app.key(key);
        reply("#ok");
        return true;
    }
    if (command == "fn") {
        if (rest.size() != 1) {
            reply("#error fn takes one character");
            return false;
        }
        ui::Key key = ui::Key::character(rest[0]);
        key.fn      = true;
        app.key(key);
        reply("#ok");
        return true;
    }
    if (command == "type") {
        for (char c : rest) {
            if (c >= ' ' && c < 127) {
                app.key(ui::Key::character(c));
            }
        }
        reply("#ok");
        return !rest.empty();
    }
    if (filesCarryOut(command, rest, reply)) {
        return false;
    }
    reply("#error unknown command");
    return false;
}

}  // namespace

bool consolePoll(ui::App& app, M5Canvas& canvas, ui::Platform& platform)
{
    bool pressed = false;
    while (Serial.available() > 0) {
        const int c = Serial.read();
        if (c < 0) {
            break;
        }
        if (c == '\r') {
            continue;
        }
        if (c != '\n') {
            if (pending.size() < kLongestLine) {
                pending.push_back(static_cast<char>(c));
            } else {
                overflowed = true;  // the rest of an overlong line is dropped, and so is the line
            }
            continue;
        }
        if (overflowed) {
            reply("#error line too long");
        } else if (pending.empty()) {
            reply("#");  // an empty line is a knock: it is answered, and pushes out what was waiting
        } else {
            pressed = carryOut(pending, app, canvas, platform) || pressed;
        }
        pending.clear();
        overflowed = false;
    }
    return pressed;
}

#else

bool consolePoll(ui::App&, M5Canvas&, ui::Platform&)
{
    return false;
}

#endif
