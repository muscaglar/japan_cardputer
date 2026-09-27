// Device shell: the app from lib/ui on a Cardputer.
//
// Hold the G0 button while switching on to start the hardware check instead of the app.

#include <M5Cardputer.h>
#include <LittleFS.h>
#include <esp_random.h>

#include <algorithm>
#include <string>
#include <vector>

#include "app.h"
#include "console.h"
#include "hwcheck.h"

namespace {

constexpr uint32_t kRepeatDelay    = 450;  // ms before a held Backspace starts repeating
constexpr uint32_t kRepeatInterval = 70;

class DevicePlatform : public ui::Platform {
public:
    void begin() { _storage = LittleFS.begin(true); }

    uint32_t millis() override { return ::millis(); }
    uint32_t random() override { return esp_random(); }
    int batteryPercent() override
    {
        const int level = M5Cardputer.Power.getBatteryLevel();
        return (level >= 0 && level <= 100) ? level : -1;
    }
    const char* boardName() override
    {
        return M5.getBoard() == m5::board_t::board_M5CardputerADV ? "Cardputer ADV" : "Cardputer";
    }

    bool load(const char* name, std::string& text) override
    {
        if (!_storage) {
            return false;
        }
        File file = LittleFS.open(path(name).c_str(), "r");
        if (!file) {
            return false;
        }
        text.clear();
        text.reserve(file.size());
        while (file.available()) {
            char buffer[128];
            const size_t n = file.readBytes(buffer, sizeof(buffer));
            text.append(buffer, n);
        }
        file.close();
        return true;
    }

    bool save(const char* name, const std::string& text) override { return write(name, text, "w"); }

    bool append(const char* name, const std::string& line) override { return write(name, line + "\n", "a"); }

    void tone(int hertz, int milliseconds) override
    {
        M5Cardputer.Speaker.tone(static_cast<float>(hertz), static_cast<uint32_t>(milliseconds));
    }

private:
    static std::string path(const char* name) { return std::string("/") + name; }

    bool write(const char* name, const std::string& text, const char* mode)
    {
        if (!_storage) {
            return false;
        }
        File file = LittleFS.open(path(name).c_str(), mode);
        if (!file) {
            return false;
        }
        const size_t written = file.write(reinterpret_cast<const uint8_t*>(text.data()), text.size());
        file.flush();
        file.close();
        return written == text.size();
    }

    bool _storage = false;
};

DevicePlatform platform;
ui::App app(platform);
M5Canvas canvas(&M5Cardputer.Display);
std::vector<Point2D_t> keysDown;
bool checkingHardware = false;
bool deleteHeld       = false;
uint32_t deleteSince  = 0;
uint32_t deleteLast   = 0;

// Turns one key on the Cardputer into what the app understands. The arrows and Esc are printed
// on ; , . / and ` and need Fn.
ui::Key translate(const KeyValue_t& value, bool fn, bool upper, bool ctrl, bool opt, bool alt)
{
    const uint8_t code = static_cast<uint8_t>(value.value_first);
    ui::Key key;
    key.fn   = fn;
    key.ctrl = ctrl;
    key.opt  = opt;
    key.alt  = alt;
    if (code == KEY_BACKSPACE) {
        key.code = ui::Key::Backspace;
    } else if (code == KEY_ENTER) {
        key.code = ui::Key::Enter;
    } else if (code == KEY_TAB) {
        key.code = ui::Key::Tab;
    } else if (fn && value.value_first == ';') {
        key.code = ui::Key::Up;
    } else if (fn && value.value_first == '.') {
        key.code = ui::Key::Down;
    } else if (fn && value.value_first == ',') {
        key.code = ui::Key::Left;
    } else if (fn && value.value_first == '/') {
        key.code = ui::Key::Right;
    } else if (fn && value.value_first == '`') {
        key.code = ui::Key::Escape;
    } else {
        key.code = ui::Key::Char;
        key.ch   = upper ? value.value_second : value.value_first;
    }
    return key;
}

void readKeys()
{
    const std::vector<Point2D_t>& now      = M5Cardputer.Keyboard.keyList();
    const Keyboard_Class::KeysState& state = M5Cardputer.Keyboard.keysState();
    const bool upper                       = state.shift || M5Cardputer.Keyboard.capslocked();
    bool deleteDown                        = false;

    for (const Point2D_t& position : now) {
        const KeyValue_t value = M5Cardputer.Keyboard.getKeyValue(position);
        const uint8_t code     = static_cast<uint8_t>(value.value_first);
        if (code == KEY_FN || code == KEY_OPT || code == KEY_LEFT_CTRL || code == KEY_LEFT_SHIFT ||
            code == KEY_LEFT_ALT) {
            continue;
        }
        if (code == KEY_BACKSPACE) {
            deleteDown = true;
        }
        if (std::find(keysDown.begin(), keysDown.end(), position) != keysDown.end()) {
            continue;  // still held from before
        }
        app.key(translate(value, state.fn, upper, state.ctrl, state.opt, state.alt));
    }
    keysDown = now;

    // A held Backspace repeats, so that a line can be cleared without hammering the key.
    const uint32_t t = millis();
    if (deleteDown && !deleteHeld) {
        deleteHeld  = true;
        deleteSince = t;
        deleteLast  = t;
    } else if (!deleteDown) {
        deleteHeld = false;
    } else if (t - deleteSince > kRepeatDelay && t - deleteLast > kRepeatInterval) {
        deleteLast = t;
        app.key(ui::Key::of(ui::Key::Backspace));
    }
}

}  // namespace

void setup()
{
    auto cfg = M5.config();
    M5Cardputer.begin(cfg, true);
    Serial.begin(115200);
    M5Cardputer.Display.setRotation(1);
    M5Cardputer.Display.setBrightness(160);
    M5Cardputer.Speaker.setVolume(140);

    M5Cardputer.update();
    checkingHardware = M5Cardputer.BtnA.isPressed();
    if (checkingHardware) {
        hwcheckSetup();
        return;
    }

    platform.begin();
    canvas.setColorDepth(16);
    canvas.createSprite(ui::kWidth, ui::kHeight);
    app.begin();
    Serial.printf("{\"app\":\"japan_cardputer\",\"board\":\"%s\",\"heapFree\":%u,\"heapLargestBlock\":%u}\n",
                  platform.boardName(), static_cast<unsigned>(ESP.getFreeHeap()),
                  static_cast<unsigned>(ESP.getMaxAllocHeap()));
}

void loop()
{
    if (checkingHardware) {
        hwcheckLoop();
        return;
    }

    M5Cardputer.update();
    if (M5Cardputer.BtnA.wasClicked()) {
        app.key(ui::Key::of(ui::Key::Button));
    }
    readKeys();
    consolePoll(app, canvas, platform);
    app.tick();
    if (app.draw(canvas)) {
        canvas.pushSprite(0, 0);
    }
    delay(5);
}
