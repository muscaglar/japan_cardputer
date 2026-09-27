// The app running on a computer: compiled with Emscripten, driven from JavaScript.
// The same app code as on the device; only the Platform and the screen are replaced.
#include <emscripten.h>

#include <M5GFX.h>

#include <cstdint>
#include <map>
#include <string>

#include "app.h"

namespace {

EM_JS(void, host_store, (const char* name, const char* text), {
    try {
        if (typeof localStorage !== "undefined") {
            localStorage.setItem("cardputer-sim:" + UTF8ToString(name), UTF8ToString(text));
        }
    } catch (e) {}
});

EM_JS(char*, host_fetch, (const char* name), {
    var value = null;
    try {
        if (typeof localStorage !== "undefined") {
            value = localStorage.getItem("cardputer-sim:" + UTF8ToString(name));
        }
    } catch (e) {}
    if (value === null) {
        return 0;
    }
    return stringToNewUTF8(value);
});

EM_JS(void, host_tone, (int hertz, int milliseconds), {
    if (typeof Module !== "undefined" && Module.onTone) {
        Module.onTone(hertz, milliseconds);
    }
});

class SimPlatform : public ui::Platform {
public:
    uint32_t millis() override { return _now; }
    uint32_t random() override
    {
        // xorshift: the same sequence for the same seed, so that screenshots can be repeated
        _seed ^= _seed << 13;
        _seed ^= _seed >> 17;
        _seed ^= _seed << 5;
        return _seed;
    }
    int batteryPercent() override { return 82; }
    const char* boardName() override { return "Simulator"; }

    bool load(const char* name, std::string& text) override
    {
        const auto found = _files.find(name);
        if (found != _files.end()) {
            text = found->second;
            return true;
        }
        if (!_persist) {
            return false;
        }
        char* stored = host_fetch(name);
        if (!stored) {
            return false;
        }
        text = stored;
        free(stored);
        _files[name] = text;
        return true;
    }
    bool save(const char* name, const std::string& text) override
    {
        _files[name] = text;
        if (_persist) {
            host_store(name, text.c_str());
        }
        return true;
    }
    bool append(const char* name, const std::string& line) override
    {
        std::string text;
        load(name, text);
        text += line;
        text += "\n";
        return save(name, text);
    }
    void tone(int hertz, int milliseconds) override { host_tone(hertz, milliseconds); }

    void advance(uint32_t milliseconds) { _now += milliseconds; }
    void seed(uint32_t value) { _seed = value ? value : 1; }
    void persist(bool on) { _persist = on; }
    void forget() { _files.clear(); }

private:
    std::map<std::string, std::string> _files;
    uint32_t _now  = 0;
    uint32_t _seed = 20260927;
    bool _persist  = false;
};

SimPlatform platform;
ui::App* app = nullptr;
M5Canvas canvas;
uint8_t pixels[ui::kWidth * ui::kHeight * 4];

}  // namespace

extern "C" {

// persist: 1 keeps settings in the browser's storage, 0 keeps them in memory only
EMSCRIPTEN_KEEPALIVE void sim_init(int seed, int persist)
{
    platform.seed(static_cast<uint32_t>(seed));
    platform.persist(persist != 0);
    platform.forget();
    if (!canvas.getBuffer()) {
        canvas.setColorDepth(16);
        canvas.createSprite(ui::kWidth, ui::kHeight);
    }
    delete app;
    app = new ui::App(platform);
    app->begin();
}

// code: a ui::Key::Code. ch: the character for Char keys. mods: 1 Fn, 2 Ctrl, 4 Opt, 8 Alt.
EMSCRIPTEN_KEEPALIVE void sim_key(int code, int ch, int mods)
{
    if (!app) {
        return;
    }
    ui::Key key;
    key.code = static_cast<ui::Key::Code>(code);
    key.ch   = static_cast<char>(ch);
    key.fn   = (mods & 1) != 0;
    key.ctrl = (mods & 2) != 0;
    key.opt  = (mods & 4) != 0;
    key.alt  = (mods & 8) != 0;
    app->key(key);
}

EMSCRIPTEN_KEEPALIVE void sim_advance(int milliseconds)
{
    platform.advance(static_cast<uint32_t>(milliseconds));
    if (app) {
        app->tick();
    }
}

// Draws if anything changed. Returns 1 when the pixels are new.
EMSCRIPTEN_KEEPALIVE int sim_render()
{
    if (!app || !app->draw(canvas)) {
        return 0;
    }
    // The sprite holds 16-bit colour, high byte first, exactly what is sent to the panel.
    // Expanding it here shows what the panel shows.
    const uint8_t* in = static_cast<const uint8_t*>(canvas.getBuffer());
    uint8_t* out      = pixels;
    for (int i = 0; i < ui::kWidth * ui::kHeight; ++i) {
        const unsigned value = (static_cast<unsigned>(in[0]) << 8) | in[1];
        in += 2;
        const unsigned r5 = (value >> 11) & 0x1F;
        const unsigned g6 = (value >> 5) & 0x3F;
        const unsigned b5 = value & 0x1F;
        *out++ = static_cast<uint8_t>((r5 << 3) | (r5 >> 2));
        *out++ = static_cast<uint8_t>((g6 << 2) | (g6 >> 4));
        *out++ = static_cast<uint8_t>((b5 << 3) | (b5 >> 2));
        *out++ = 255;
    }
    return 1;
}

EMSCRIPTEN_KEEPALIVE uint8_t* sim_pixels()
{
    return pixels;
}

EMSCRIPTEN_KEEPALIVE int sim_screen()
{
    return app ? static_cast<int>(app->current()) : -1;
}

// Switching off and on again: the app starts anew, the files stay.
EMSCRIPTEN_KEEPALIVE void sim_restart()
{
    delete app;
    app = new ui::App(platform);
    app->begin();
}

// The state of the app as one line of JSON. The text is valid until the next call.
EMSCRIPTEN_KEEPALIVE const char* sim_info()
{
    static std::string text;
    text = app ? app->describe() : std::string("{}");
    return text.c_str();
}

// what: 0 keeps settings and progress aside, 1 brings them back, 2 forgets all progress.
// Returns 1 when it worked.
EMSCRIPTEN_KEEPALIVE int sim_keep(int what)
{
    if (!app) {
        return 0;
    }
    if (what == 2) {
        app->startFresh();
        return 1;
    }
    return (what == 0 ? app->keepAside() : app->bringBack()) ? 1 : 0;
}

}  // extern "C"
