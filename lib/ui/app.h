// The app: settings, the screens and the routing of keys between them. Portable: it draws on a
// canvas and talks to the machine only through Platform.
#pragma once

#include <memory>
#include <string>

#include "platform.h"
#include "progress.h"
#include "session.h"
#include "theme.h"

namespace ui {

enum class RomajiMode : uint8_t { Peek, Always, Never, Count };
enum class Voice : uint8_t { Both, Female, Male, Count };  // Both: they take turns

struct Settings {
    ThemeId theme     = ThemeId::Techo;
    RomajiMode romaji = RomajiMode::Peek;
    bool textbookN    = true;   // minna -> みんな. Off: as on a PC, minnna -> みんな
    bool sound        = false;  // the speaker stays silent unless switched on
    int volume        = 3;      // 1 to 5
    Voice voice       = Voice::Both;
    int dayNumber     = 1;      // the device has no clock: the owner confirms each new day
    int answeredToday = 0;      // answers given on this day number
    int level         = 3;      // 1 kana only, 2 kanji of the first school years too, 3 everything
};

enum class ScreenId : uint8_t { Home, Menu, Kana, Settings, Cards, Summary, Keys, Decks, Chart, Guide, Count };

// How far a deck is learnt, counting the cards within the level that is set.
struct DeckProgress {
    int total  = 0;
    int seen   = 0;  // answered at least once
    int learnt = 0;  // past the learning stage
    int due    = 0;  // waiting today
};

// What happened in the sitting that is running or has just ended.
struct Sitting {
    const deck::Deck* deck = nullptr;  // nullptr: every deck
    int asked              = 0;
    int right              = 0;
    int introduced         = 0;        // cards met for the first time
};

class App;

class Screen {
public:
    virtual ~Screen() = default;
    virtual void enter(App&) {}
    virtual void key(App&, const Key&) {}
    virtual void tick(App&) {}
    virtual void draw(App&, Canvas&) = 0;
    // For checks run from a computer: adds fields to the JSON account of the app, each written
    // as ,"name":value
    virtual void describe(std::string&) const {}
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

    // Cards. A sitting takes its cards from one deck, or from all of them when deck is nullptr.
    void startSitting(const deck::Deck* deck);
    // A sitting of the course: what is due from every deck, and new cards from the lowest
    // stage that still has unseen ones, so that kana come before words.
    void startCourse();
    // The deck the course takes its new cards from now. nullptr when every card was seen.
    const deck::Deck* courseDeck() const;
    DeckProgress progressOf(const deck::Deck& deck) const;

    // Sound. speak() plays the clip of a card if sound is on, the memory card is in and has it:
    // "/audio/<f or m>/<deck id>/<item id>.wav", the voice as set. speakFile() plays any file
    // under the same conditions. Both return whether something is playing now.
    bool speak(const deck::Deck* deck, const deck::Item* item);
    bool speakFile(const char* path);
    // "f" or "m": the folder of the voice whose turn it is, for a screen that builds a path
    // itself, as in "/audio/" + voiceFolder() + "/guide/guide-vowels-1.wav".
    const char* voiceFolder();
    void endSitting();  // keeps what was learnt; called when the sitting is over or left
    session::Queue& queue() { return _queue; }
    progress::Store& store() { return _store; }
    Sitting& sitting() { return _sitting; }
    uint16_t today() const { return static_cast<uint16_t>(_settings.dayNumber); }
    void startNewDay();

    // Cards waiting today, and new ones a sitting would bring, over all decks.
    int dueToday() const;
    int newAvailable() const;

    // For checks run from a computer. describe() gives the state as one line of JSON.
    // keepAside() copies settings and progress to spare files; bringBack() puts them back and
    // loads them, so that a check leaves the owner's progress as it found it.
    std::string describe() const;
    bool keepAside();
    bool bringBack();
    void startFresh();  // forgets all progress and starts at day 1; the look and the rest stay

private:
    void loadSettings();

    Platform& _platform;
    Settings _settings;
    progress::Store _store;
    session::Queue _queue;
    Sitting _sitting;
    bool _maleNext = false;  // whose turn it is when the voices take turns
    std::unique_ptr<Screen> _screens[static_cast<size_t>(ScreenId::Count)];
    ScreenId _current = ScreenId::Home;
    bool _dirty       = true;
};

// Arrow keys are printed on ; , . / and need Fn on the device. Screens that take no text accept
// the bare keys too, so that the menu can be worked with one thumb.
Key::Code navigation(const Key& key);

}  // namespace ui
