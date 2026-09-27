// Hardware check for the Cardputer family (original, v1.1 and ADV).
//
// It answers the questions the real app depends on:
//   1 INFO    which board this is, how much memory it has, battery, SD card
//   2 FONTS   how readable Japanese is at each size on this screen
//   3 TYPING  romaji typed on the keyboard becomes kana as you type
//   4 AUDIO   speaker beep, and a 3 second microphone recording played back
//
// Fn + /  next page        Fn + ,  previous page        G0 button  next page
// The same facts are printed on the USB serial port as one JSON line at boot.

#include <M5Cardputer.h>
#include <SD.h>
#include <SPI.h>

#include <algorithm>
#include <string>
#include <vector>

#include "romaji.h"

namespace {

constexpr int kSdSck  = 40;
constexpr int kSdMiso = 39;
constexpr int kSdMosi = 14;
constexpr int kSdCs   = 12;

constexpr uint32_t kRecordRate    = 16000;
constexpr uint32_t kRecordSeconds = 3;

enum Page { kInfo = 0, kFonts, kTyping, kAudio, kPageCount };

const char* const kPageTitles[kPageCount] = {"INFO", "FONTS", "TYPING", "AUDIO"};

struct FontSample {
    const char* name;
    const lgfx::IFont* font;
};

const FontSample kFontSamples[] = {
    {"efont 12", &fonts::efontJA_12},
    {"efont 16", &fonts::efontJA_16},
    {"gothic 20", &fonts::lgfxJapanGothic_20},
    {"efont 24", &fonts::efontJA_24},
};
constexpr int kFontCount = sizeof(kFontSamples) / sizeof(kFontSamples[0]);

// Each sample line tests something different: an everyday sentence, dense kanji, menu kanji
// (some of which are missing from the smaller gothic font), and katakana.
const char* const kSamples[] = {
    "東京駅はどこですか？",
    "観光案内所 営業時間 禁煙席",
    "餃子 鮪 炙り 鰤 饂飩 蕎麦",
    "チェックイン コンビニ ラーメン",
};
constexpr int kSampleCount = sizeof(kSamples) / sizeof(kSamples[0]);

M5Canvas canvas(&M5Cardputer.Display);

int page         = kInfo;
bool dirty       = true;
int fontIndex    = 1;
bool sdMounted   = false;
bool katakana    = false;
bool imeStyle    = false;
std::string roma;       // letters of the syllables being typed
std::string committed;  // finished kana
std::vector<Point2D_t> keysDown;  // keys held at the previous scan
String audioStatus = "B: beep    R: record 3 s and play";
int audioPeak      = 0;

const char* boardName()
{
    switch (M5.getBoard()) {
        case m5::board_t::board_M5Cardputer:
            return "Cardputer";
        case m5::board_t::board_M5CardputerADV:
            return "Cardputer ADV";
        default:
            return "unknown board";
    }
}

romaji::Options romajiOptions()
{
    romaji::Options options;
    options.nStyle = imeStyle ? romaji::NStyle::Ime : romaji::NStyle::Hepburn;
    return options;
}

std::string shown(const std::string& kana)
{
    return katakana ? romaji::toKatakana(kana) : kana;
}

// Removes the last UTF-8 character.
void popCharacter(std::string& text)
{
    while (!text.empty()) {
        const unsigned char last = static_cast<unsigned char>(text.back());
        text.pop_back();
        if ((last & 0xC0) != 0x80) {
            break;
        }
    }
}

void printBootReport()
{
    Serial.printf(
        "{\"probe\":\"cardputer-nihongo\",\"board\":\"%s\",\"boardId\":%d,\"chip\":\"%s\",\"chipRev\":%d,"
        "\"flashBytes\":%u,\"psramBytes\":%u,\"heapFree\":%u,\"heapLargestBlock\":%u,"
        "\"batteryPercent\":%d,\"batteryMillivolts\":%d,\"sdMounted\":%s,\"sdMegabytes\":%u}\n",
        boardName(), static_cast<int>(M5.getBoard()), ESP.getChipModel(), static_cast<int>(ESP.getChipRevision()),
        static_cast<unsigned>(ESP.getFlashChipSize()), static_cast<unsigned>(ESP.getPsramSize()),
        static_cast<unsigned>(ESP.getFreeHeap()), static_cast<unsigned>(ESP.getMaxAllocHeap()),
        static_cast<int>(M5Cardputer.Power.getBatteryLevel()),
        static_cast<int>(M5Cardputer.Power.getBatteryVoltage()), sdMounted ? "true" : "false",
        sdMounted ? static_cast<unsigned>(SD.cardSize() / (1024ULL * 1024ULL)) : 0U);
}

void drawHeader()
{
    canvas.fillRect(0, 0, canvas.width(), 14, TFT_NAVY);
    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_WHITE);
    canvas.setTextDatum(top_left);
    canvas.setCursor(3, 1);
    canvas.printf("%d/%d %s", page + 1, static_cast<int>(kPageCount), kPageTitles[page]);
    canvas.setTextDatum(top_right);
    canvas.drawString("Fn+/ 次へ", canvas.width() - 3, 1);
    canvas.setTextDatum(top_left);
}

void drawInfo()
{
    canvas.setFont(&fonts::efontJA_16);
    canvas.setTextColor(TFT_YELLOW);
    canvas.setCursor(4, 18);
    canvas.print(boardName());

    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_WHITE);
    int y = 38;
    const int step = 14;

    canvas.setCursor(4, y);
    canvas.printf("%s rev %d   flash %u MB", ESP.getChipModel(), static_cast<int>(ESP.getChipRevision()),
                  static_cast<unsigned>(ESP.getFlashChipSize() / (1024U * 1024U)));
    y += step;

    canvas.setCursor(4, y);
    if (ESP.getPsramSize() > 0) {
        canvas.printf("PSRAM %u MB", static_cast<unsigned>(ESP.getPsramSize() / (1024U * 1024U)));
    } else {
        canvas.print("PSRAM なし (none)");
    }
    y += step;

    canvas.setCursor(4, y);
    canvas.printf("heap %u KB free, block %u KB", static_cast<unsigned>(ESP.getFreeHeap() / 1024U),
                  static_cast<unsigned>(ESP.getMaxAllocHeap() / 1024U));
    y += step;

    canvas.setCursor(4, y);
    canvas.printf("battery %d%%  %d mV%s", static_cast<int>(M5Cardputer.Power.getBatteryLevel()),
                  static_cast<int>(M5Cardputer.Power.getBatteryVoltage()),
                  M5Cardputer.Power.isCharging() == m5::Power_Class::is_charging ? "  charging" : "");
    y += step;

    canvas.setCursor(4, y);
    if (sdMounted) {
        canvas.printf("SD card %u MB", static_cast<unsigned>(SD.cardSize() / (1024ULL * 1024ULL)));
    } else {
        canvas.print("SD card なし (none found)");
    }
    y += step;

    canvas.setTextColor(TFT_LIGHTGREY);
    canvas.setCursor(4, y);
    canvas.print("R: read again");
}

void drawFonts()
{
    const FontSample& sample = kFontSamples[fontIndex];

    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_YELLOW);
    canvas.setCursor(4, 16);
    canvas.printf("%s   , . で変更 (%d/%d)", sample.name, fontIndex + 1, kFontCount);

    canvas.setFont(sample.font);
    canvas.setTextColor(TFT_WHITE);
    canvas.setTextWrap(false);
    const int lineHeight = canvas.fontHeight() + 2;
    int y = 31;
    for (int i = 0; i < kSampleCount && y + lineHeight <= canvas.height() + 2; ++i) {
        canvas.setCursor(2, y);
        canvas.print(kSamples[i]);
        y += lineHeight;
    }
}

void drawTyping()
{
    const romaji::Result live = romaji::convert(roma, romajiOptions(), false);

    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_YELLOW);
    canvas.setCursor(4, 16);
    canvas.printf("Tab:%s  Fn+N:%s", katakana ? "カタカナ" : "ひらがな", imeStyle ? "nn=ん (PC)" : "textbook n");

    canvas.setFont(&fonts::efontJA_24);
    canvas.setTextWrap(true);
    canvas.setCursor(2, 32);
    canvas.setTextColor(TFT_WHITE);
    canvas.print(shown(committed).c_str());
    canvas.setTextColor(TFT_GREEN);
    canvas.print(shown(live.kana).c_str());
    canvas.setTextColor(TFT_ORANGE);
    canvas.print(live.pending.c_str());
    canvas.setTextColor(TFT_DARKGREY);
    canvas.print("_");
    canvas.setTextWrap(false);

    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_LIGHTGREY);
    canvas.setCursor(4, canvas.height() - 14);
    if (roma.empty() && committed.empty()) {
        canvas.print("try: konnichiha  ra-men  kippu");
    } else {
        canvas.printf("> %s", roma.c_str());
    }
}

void drawAudio()
{
    canvas.setFont(&fonts::efontJA_16);
    canvas.setTextColor(TFT_WHITE);
    canvas.setCursor(4, 22);
    canvas.print("スピーカーとマイク");

    canvas.setFont(&fonts::efontJA_12);
    canvas.setTextColor(TFT_YELLOW);
    canvas.setCursor(4, 48);
    canvas.print(audioStatus);

    canvas.setTextColor(TFT_WHITE);
    canvas.setCursor(4, 68);
    canvas.printf("loudest sample: %d / 32767", audioPeak);
    const int barWidth = (canvas.width() - 8) * audioPeak / 32767;
    canvas.drawRect(4, 86, canvas.width() - 8, 12, TFT_DARKGREY);
    canvas.fillRect(4, 86, barWidth, 12, audioPeak > 28000 ? TFT_RED : TFT_GREEN);

    canvas.setTextColor(TFT_LIGHTGREY);
    canvas.setCursor(4, 106);
    canvas.print("speak about 20 cm from the device");
}

void draw()
{
    canvas.fillSprite(TFT_BLACK);
    drawHeader();
    switch (page) {
        case kInfo:   drawInfo();   break;
        case kFonts:  drawFonts();  break;
        case kTyping: drawTyping(); break;
        case kAudio:  drawAudio();  break;
        default: break;
    }
    canvas.pushSprite(0, 0);
    dirty = false;
}

void showAudioStatus(const char* text)
{
    audioStatus = text;
    draw();
}

void beep()
{
    showAudioStatus("beep");
    M5Cardputer.Speaker.tone(880, 150);
    delay(180);
    M5Cardputer.Speaker.tone(1320, 250);
    delay(280);
    showAudioStatus("B: beep    R: record 3 s and play");
}

void recordAndPlay()
{
    const size_t samples = kRecordRate * kRecordSeconds;
    int16_t* buffer = static_cast<int16_t*>(heap_caps_malloc(samples * sizeof(int16_t), MALLOC_CAP_8BIT));
    if (!buffer) {
        showAudioStatus("not enough memory to record");
        return;
    }
    memset(buffer, 0, samples * sizeof(int16_t));

    // The microphone and the speaker cannot run at the same time.
    M5Cardputer.Speaker.end();
    M5Cardputer.Mic.begin();
    showAudioStatus("recording: speak now");

    const bool accepted = M5Cardputer.Mic.record(buffer, samples, kRecordRate);
    const uint32_t deadline = millis() + (kRecordSeconds * 1000U) + 2000U;
    while (accepted && M5Cardputer.Mic.isRecording() && millis() < deadline) {
        delay(10);
    }
    M5Cardputer.Mic.end();

    audioPeak = 0;
    for (size_t i = 0; i < samples; ++i) {
        const int value = buffer[i] < 0 ? -static_cast<int>(buffer[i]) : buffer[i];
        if (value > audioPeak) {
            audioPeak = value > 32767 ? 32767 : value;
        }
    }

    M5Cardputer.Speaker.begin();
    M5Cardputer.Speaker.setVolume(200);
    if (accepted) {
        showAudioStatus("playing back");
        M5Cardputer.Speaker.playRaw(buffer, samples, kRecordRate, false, 1, 0);
        while (M5Cardputer.Speaker.isPlaying()) {
            delay(10);
        }
        showAudioStatus("done.  B: beep   R: record again");
    } else {
        showAudioStatus("microphone did not start");
    }
    heap_caps_free(buffer);
}

void changePage(int delta)
{
    page  = (page + delta + kPageCount) % kPageCount;
    dirty = true;
}

// Keys that went down since the previous scan. Comparing key positions instead of counting
// pressed keys means rolling from one key to the next never types a letter twice.
struct KeyPress {
    std::string chars;
    bool del   = false;
    bool enter = false;
    bool tab   = false;
    bool fn    = false;
    bool any   = false;
};

KeyPress readNewKeys()
{
    KeyPress press;
    const std::vector<Point2D_t>& now         = M5Cardputer.Keyboard.keyList();
    const Keyboard_Class::KeysState& state    = M5Cardputer.Keyboard.keysState();
    const bool upper                          = state.shift || M5Cardputer.Keyboard.capslocked();
    press.fn                                  = state.fn;

    for (const Point2D_t& key : now) {
        if (std::find(keysDown.begin(), keysDown.end(), key) != keysDown.end()) {
            continue;
        }
        const KeyValue_t value = M5Cardputer.Keyboard.getKeyValue(key);
        const uint8_t code     = static_cast<uint8_t>(value.value_first);
        if (code == KEY_FN || code == KEY_OPT || code == KEY_LEFT_CTRL || code == KEY_LEFT_SHIFT ||
            code == KEY_LEFT_ALT) {
            continue;
        }
        if (code == KEY_BACKSPACE) {
            press.del = true;
        } else if (code == KEY_ENTER) {
            press.enter = true;
        } else if (code == KEY_TAB) {
            press.tab = true;
        } else {
            press.chars.push_back(upper ? value.value_second : value.value_first);
        }
        press.any = true;
    }
    keysDown = now;
    return press;
}

void commitTyping()
{
    committed += romaji::convert(roma, romajiOptions(), true).kana;
    roma.clear();
}

void handleTypingKeys(const KeyPress& press)
{
    if (press.tab) {
        katakana = !katakana;
    }
    if (press.del) {
        if (!roma.empty()) {
            roma.pop_back();
        } else {
            popCharacter(committed);
        }
    }
    for (char c : press.chars) {
        if (c == ' ') {
            commitTyping();
        } else {
            roma.push_back(c);
        }
    }
    if (press.enter) {
        if (roma.empty()) {
            committed.clear();
        } else {
            commitTyping();
        }
    }
    // Move finished syllables out of the live buffer so it stays short.
    if (roma.size() > 24) {
        const romaji::Result live = romaji::convert(roma, romajiOptions(), false);
        committed += live.kana;
        roma = live.pending;
    }
}

void handleKeys(const KeyPress& press)
{
    if (press.fn) {
        for (char c : press.chars) {
            if (c == '/' || c == '?') {
                changePage(+1);
            } else if (c == ',' || c == '<') {
                changePage(-1);
            } else if ((c == 'n' || c == 'N') && page == kTyping) {
                imeStyle = !imeStyle;
            }
        }
        dirty = true;
        return;
    }

    switch (page) {
        case kInfo:
            for (char c : press.chars) {
                if (c == 'r' || c == 'R') {
                    printBootReport();
                }
            }
            break;
        case kFonts:
            for (char c : press.chars) {
                if (c == '.' || c == '/') {
                    fontIndex = (fontIndex + 1) % kFontCount;
                } else if (c == ',' || c == ';') {
                    fontIndex = (fontIndex + kFontCount - 1) % kFontCount;
                }
            }
            break;
        case kTyping:
            handleTypingKeys(press);
            break;
        case kAudio:
            for (char c : press.chars) {
                if (c == 'b' || c == 'B') {
                    beep();
                } else if (c == 'r' || c == 'R') {
                    recordAndPlay();
                }
            }
            break;
        default:
            break;
    }
    dirty = true;
}

}  // namespace

void setup()
{
    auto cfg = M5.config();
    M5Cardputer.begin(cfg, true);
    Serial.begin(115200);

    M5Cardputer.Display.setRotation(1);
    M5Cardputer.Display.setBrightness(160);
    canvas.setColorDepth(16);
    canvas.createSprite(M5Cardputer.Display.width(), M5Cardputer.Display.height());

    SPI.begin(kSdSck, kSdMiso, kSdMosi, kSdCs);
    sdMounted = SD.begin(kSdCs, SPI, 25000000) && SD.cardType() != CARD_NONE;

    M5Cardputer.Speaker.setVolume(160);

    delay(300);
    printBootReport();
    draw();
}

void loop()
{
    M5Cardputer.update();

    if (M5Cardputer.BtnA.wasClicked()) {
        changePage(+1);
    }
    const KeyPress press = readNewKeys();
    if (press.any) {
        handleKeys(press);
    }
    if (dirty) {
        draw();
    }

    // Battery and heap change slowly; refresh the info page every two seconds.
    static uint32_t lastRefresh = 0;
    if (page == kInfo && millis() - lastRefresh > 2000) {
        lastRefresh = millis();
        dirty       = true;
    }
    delay(5);
}
