// The app: settings, the screens and the routing of keys between them. Portable: it draws on a
// canvas and talks to the machine only through Platform.
#pragma once

#include <memory>
#include <string>

#include "platform.h"
#include "theme.h"

namespace ui {

enum class RomajiMode : uint8_t { Peek, Always, Never, Count };

struct Settings {
    ThemeId theme     = ThemeId::Techo;
    RomajiMode romaji = RomajiMode::Peek;
    bool textbookN    = true;   // minna -> みんな. Off: as on a PC, minnna -> みんな
    bool sound        = false;  // the speaker stays silent unless switched on
    int dayNumber     = 1;
};

enum class ScreenId : uint8_t { Home, Menu, Kana, Settings, Count };

class App;

class Screen {
public:
    virtual ~Screen() = default;
    virtual void enter(App&) {}
    virtual void key(App&, const Key&) {}
    virtual void tick(App&) {}
    virtual void draw(App&, Canvas&) = 0;
};

class App {
public:
    explicit App(Platform& platform);
    ~App();

    void begin();
    void key(const Key& key);
    void tick();
    bool draw(Canvas& canvas);  // draws only when something changed; true if it drew

    Platform& platform() { return _platform; }
    Settings& settings() { return _settings; }
    const Theme& theme() const { return ui::theme(_settings.theme); }
    void saveSettings();

    void show(ScreenId id);
    ScreenId current() const { return _current; }
    void invalidate() { _dirty = true; }

private:
    void loadSettings();

    Platform& _platform;
    Settings _settings;
    std::unique_ptr<Screen> _screens[static_cast<size_t>(ScreenId::Count)];
    ScreenId _current = ScreenId::Home;
    bool _dirty       = true;
};

// Arrow keys are printed on ; , . / and need Fn on the device. Screens that take no text accept
// the bare keys too, so that the menu can be worked with one thumb.
Key::Code navigation(const Key& key);

}  // namespace ui
