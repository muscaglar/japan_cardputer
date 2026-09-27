# Software ecosystem and existing apps

Research only; nothing was built or written. All claims below come from pages or source files I opened on 2026-09-27 (GitHub repo pages, raw source files, commit/release Atom feeds, docs.m5stack.com, PlatformIO registry API). The GitHub REST API was rate-limited, so licences were read from repo pages and LICENSE files; "no licence found" means no LICENSE file was visible, not that I confirmed the author's intent. Headline findings: 1. Arduino + M5Cardputer/M5Unified/M5GFX under PlatformIO is the most mature path and the one nearly every relevant existing project uses. One binary runs on the original Cardputer, v1.1 and ADV because M5GFX auto-detects the board at runtime and M5Cardputer picks the keyboard driver from that. M5GFX already bundles Japanese bitmap fonts (kana + about 4,400 to 10,800 glyphs depending on family), so Japanese display is a solved problem in this stack. 2. bmorcelli's Launcher (v2.9.1, MIT, supports Cardputer and ADV) gives a genuine no-computer recovery path: install a .bin from the microSD, from a phone browser over the Launcher WebUI, or by OTA download; hold Enter at boot to get back to the Launcher. M5Burner is desktop-only. 3. Relevant prior art exists and is recent. The three most useful: WordCardputer (Japanese/English flashcards, dictation with romaji-to-kana IME, listening mode, SQLite + WAV on SD; but Chinese glosses and no licence file), M5OpurSan (fully offline Japanese kana-kanji IME with a 927k-word dictionary on SD; MIT code, GPL-2.0 dictionary; verified on ADV only), and several offline SD-card dictionaries (English-Chinese) that prove the binary-index-on-SD lookup pattern. I found no Anki client and no Japanese-English dictionary for the Cardputer. 4. Recommendation: write a fresh Arduino/PlatformIO app, installed through Launcher, borrowing patterns (and MIT code where licensed) rather than forking any single project. No existing project combines English glosses, a real SRS scheduler, a Japanese-English dictionary and a clean licence. 5. Variant caveat: several of the best Japanese-specific projects target the ADV only (ES8311 audio, TCA8418 keyboard). If the device turns out to be a CardputerZero (Linux, Raspberry Pi CM0), none of this facet applies; that is unlikely given the 56-key / 1.14 inch description and its late-2026 shipping.

Fact-check: still running when this file was written; treat every statement as unchecked.

## Statements

### sw-01 · not checked

The official M5Cardputer Arduino library supports both the original Cardputer and the Cardputer ADV. ADV support was added in release 1.1.0 (2025-09-05). The newest GitHub tag is 1.2.0 (2026-06-08, adds an Fn key layer); last commit on master was 2026-07-21.

- Applies to: Cardputer (K132), Cardputer v1.1, Cardputer ADV
- Source: <https://github.com/m5stack/M5Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/library.properties>
- Source: <https://github.com/m5stack/M5Cardputer/releases.atom>
- Source: <https://github.com/m5stack/M5Cardputer/commits/master.atom>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/M5Cardputer.cpp>

### sw-02 · not checked

The PlatformIO registry still serves M5Cardputer 1.1.1, and the 1.2.0 git tag itself still declares version=1.1.1 in library.properties and library.json. So 'm5stack/M5Cardputer' from the registry and the GitHub URL give different keyboard behaviour. A third-party project (CardEX) reports 1.2.0 changed the keyboard API incompatibly.

- Applies to: All ESP32-S3 Cardputer variants (build-time concern)
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/1.2.0/library.properties>
- Source: <https://github.com/prokke/CardEX-for-Cardputer-ADV>

### sw-03 · not checked

Board auto-detection happens at runtime inside M5GFX, not at compile time. It identifies the ST7789 panel on GPIO 33-37, then reads GPIO 8/9 with pull-downs: if both read high (I2C pull-ups present) the board is CardputerADV, otherwise Cardputer. M5Cardputer's Keyboard.begin() then selects a GPIO-matrix reader for Cardputer or a TCA8418 I2C reader for ADV. There is no separate board ID for v1.1, so it is treated as the original Cardputer.

- Applies to: Cardputer (K132), Cardputer v1.1, Cardputer ADV
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/boards.hpp>

### sw-04 · not checked

M5Stack's documented PlatformIO configuration for both Cardputer v1.1 and Cardputer ADV uses board = esp32-s3-devkitc-1 (not m5stack-stamps3), platform = espressif32@6.7.0, framework = arduino, build flags -DESP32S3 -DCORE_DEBUG_LEVEL=5 -DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1, and lib_deps pointing at the M5Cardputer GitHub URL. A board definition named m5stack-stamps3 does exist in platform-espressif32 (8MB flash, default_8MB.csv, ARDUINO_USB_MODE=1) but does not set CDC_ON_BOOT.

- Applies to: Cardputer v1.1, Cardputer ADV (identical text on both doc pages); by extension the original Cardputer
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/platformio.ini>

### sw-05 · not checked

Current library versions are M5Unified 0.2.23 and M5GFX 0.2.30, both released 2026-09-21, and M5Unified 0.2.23 requires M5GFX >= 0.2.30. Both are MIT licensed and actively maintained (three releases each in the last five weeks).

- Applies to: All ESP32-S3 Cardputer variants
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/library.properties>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/library.properties>
- Source: <https://github.com/m5stack/M5Unified/releases.atom>
- Source: <https://github.com/m5stack/M5GFX/releases.atom>
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5GFX>

### sw-06 · not checked

M5GFX ships compiled-in Japanese fonts. The IPA-derived lgfxJapanGothic / lgfxJapanMincho families come in sizes 8, 12, 16, 20, 24, 28, 32, 36, 40 px with about 4,425 glyphs each; efontJA comes in 10, 12, 14, 16, 24 px with about 10,838 glyphs (9,801 at 24 px). Flash cost per font: gothic_12 about 109 KB, gothic_16 about 159 KB, gothic_24 about 277 KB; efont_ja_16 about 467 KB, efont_ja_24 about 744 KB. M5GFX also supports runtime-loaded VLW fonts.

- Applies to: All ESP32-S3 Cardputer variants using Arduino/M5GFX
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/README.md>

### sw-07 · not checked

ESP-IDF is a supported but heavier path. M5Stack's factory firmware (M5Cardputer-UserDemo, MIT) is an ESP-IDF project: the main branch targets ESP-IDF v4.4.6 for the original Cardputer and a separate CardputerADV branch targets ESP-IDF v5.4.2. The two variants therefore have separate factory firmware builds.

- Applies to: Cardputer (K132) main branch; Cardputer ADV on the CardputerADV branch
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer-UserDemo/main/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer-UserDemo/CardputerADV/README.md>
- Source: <https://github.com/m5stack/M5Cardputer-UserDemo/releases.atom>
- Source: <https://github.com/markoblogo/Pocket-OS-Cardputer-ABV>

### sw-08 · not checked

UIFlow2 (M5Stack's MicroPython firmware, MIT) has dedicated board builds for both Cardputer and CardputerADV; latest release is 2.5.3 (2026-09-11). Whether the Cardputer build exposes a usable built-in Japanese font to the display API is not settled: the efontJA_24 binding in the source is compiled only for BOARD_ID 25, while the Cardputer board (BOARD_ID 14) sets an LVGL Japanese font flag but has LVGL disabled.

- Applies to: Cardputer (K132)/v1.1 and Cardputer ADV
- Source: <https://github.com/m5stack/uiflow-micropython>
- Source: <https://github.com/m5stack/uiflow-micropython/releases.atom>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/components/M5Unified/mpy_m5gfx.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/boards/M5STACK_Cardputer/mpconfigboard.cmake>

### sw-09 · not checked

CircuitPython has an official board build for the original Cardputer (stable 10.3.1) but I found no dedicated Cardputer ADV board: circuitpython.org/board/m5stack_cardputer_adv returns 404 and the CircuitPython source tree has only m5stack_cardputer and m5stack_cardputer_ros, with no TCA8418 reference in the board files I checked.

- Applies to: Cardputer (K132) / v1.1 supported; Cardputer ADV apparently not
- Source: <https://circuitpython.org/board/m5stack_cardputer/>
- Source: <https://circuitpython.org/board/m5stack_cardputer_adv/>
- Source: <https://github.com/adafruit/circuitpython/tree/main/ports/espressif/boards>

### sw-10 · not checked

MicroHydra (GPL-3.0) is a MicroPython app launcher where any .py, .mpy or package folder dropped into /apps on flash or on the microSD becomes an app, so apps can be edited or replaced by swapping files on the SD with no reflash. Stable release is v2.5.1 (2026-03-27); ADV support is only 'partial' and only in v2.6-preview (2026-03-30), which is also the date of the last commit.

- Applies to: Cardputer (K132)/v1.1 fully; Cardputer ADV partial (preview release)
- Source: <https://github.com/echo-lalia/MicroHydra>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra/main/README.md>
- Source: <https://github.com/echo-lalia/MicroHydra/releases.atom>
- Source: <https://github.com/echo-lalia/MicroHydra/tree/main/devices>

### sw-11 · not checked

MicroHydra can display Japanese, but only through a built-in 8x8 pixel UTF-8 fallback font (a 524,288-byte file, consistent with 65,536 code points at 8 bytes each). Eight pixels is too coarse to render most kanji legibly, so MicroHydra is a poor fit for kanji study without writing a custom font renderer.

- Applies to: Cardputer (K132)/v1.1 and ADV under MicroHydra
- Source: <https://raw.githubusercontent.com/wiki/echo-lalia/MicroHydra/Display.md>
- Source: <https://github.com/echo-lalia/MicroHydra/tree/main/src/font>
- Source: <https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/KanjiReader>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra-Apps/main/app-source/KanjiReader/KanjiReader.py>

### sw-12 · not checked

bmorcelli's Launcher (MIT) supports Cardputer and Cardputer ADV in a single build and can install firmware three ways without a computer: from a .bin on the microSD, by OTA download over Wi-Fi from online catalogues (M5Burner / LauncherHub / GitHub links), and via a WebUI where a phone browser uploads a .bin. Latest release is 2.9.1 (2026-09-04); last commit 2026-09-17. The README on main already documents an unreleased 2.10.0.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Source: <https://github.com/bmorcelli/Launcher>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/boards/m5stack-cardputer/platformio.ini>
- Source: <https://github.com/bmorcelli/Launcher/releases.atom>
- Source: <https://github.com/bmorcelli/Launcher/wiki/Obtaining-binaries-to-launch>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Explaining-the-project.md>

### sw-13 · not checked

With Launcher installed, switching between Launcher and a custom app is done at power-on: Launcher shows a boot screen, pressing Enter opens the Launcher menu, and doing nothing boots the installed app. Since 2.7.0 several firmwares can be installed side by side and since 2.8.0 a keyboard key can be bound to a binary. Launcher itself occupies a protected 0x150000 (about 1.3 MB) partition at 0x10000 on the 8 MB flash, leaving roughly 6.5 MB for apps plus their data partitions.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/support_files/custom_8Mb.csv>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Explaining-the-project.md>

### sw-14 · not checked

Launcher's README recommends an SDHC card of 32 GB or less, formatted FAT32 with an MBR partition table; exFAT and larger cards are supported since 2.8.0 but smaller cards are still recommended.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV when using Launcher
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://github.com/kikyujin/M5OpurSan>

### sw-15 · not checked

M5Burner is a desktop application (Windows, macOS, Linux) that flashes over USB. It cannot update the device without a computer. Its firmware catalogue is, however, reachable from the device itself through Launcher's OTA menu.

- Applies to: All ESP32-S3 Cardputer variants
- Source: <https://docs.m5stack.com/en/uiflow/m5burner/intro>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>

### sw-16 · not checked

Bruce (AGPL-3.0, latest release 1.16.1 on 2026-08-11) supports Cardputer and Cardputer ADV and can be launched from Launcher, but it is an offensive-security toolkit with no language-learning function. It is not a useful base for this project.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Source: <https://github.com/pr3y/Bruce>
- Source: <https://github.com/pr3y/Bruce/releases.atom>

### sw-17 · not checked

WordCardputer is the closest existing project to the goal: a vocabulary trainer for M5Cardputer with Japanese and English decks, flashcard mode with 1-5 proficiency scores, dictation mode with a romaji-to-kana IME, a listening mode that plays per-word WAV audio from SD, statistics, SQLite storage and a Wi-Fi web panel for importing JSON decks. It displays Japanese (kana and kanji fields). Limitations: glosses and README are in Chinese, scheduling is weighted-random (weight = 6 - score) rather than interval-based spaced repetition, and the repo has no LICENSE file. Last commit 2026-09-01.

- Applies to: Written for M5Cardputer using the M5Cardputer library; ADV compatibility not stated in the README
- Source: <https://github.com/Mr-xiaotian/WordCardputer>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/README.md>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://github.com/Mr-xiaotian/WordCardputer/commits/main.atom>

### sw-18 · not checked

M5OpurSan is a fully offline Japanese word processor with a kana-kanji conversion engine that runs on the device: romaji to kana, Space for kanji candidates, backed by a 927,000-entry, 33.3 MB dictionary file on the microSD built from alt-cannadic and ipadic. Conversion is word-level, not phrase-level. Code is MIT; everything under dict/ (including the dictionary binary) is GPL-2.0. The author tested only on ADV and says the original / v1.1 'may work' but is unverified. Last commit 2026-08-25.

- Applies to: Cardputer ADV (verified by author); Cardputer K132 / v1.1 unverified
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md>
- Source: <https://github.com/kikyujin/M5OpurSan/commits/main.atom>

### sw-19 · not checked

Offline SD-card dictionaries already run on the Cardputer, proving the lookup pattern, but every one I found is English-Chinese or English-only, not Japanese-English. Examples: rabchang/m5_stack_cardputer_dictionary (MIT, ADV, binary index on SD with on-device binary search, prefix suggestions, favourites; last commit 2026-08-23); gwz999-gwz/card_dic-for-cardputer-adv (no licence found; dictionary and font both on SD, 32 MB dictionary not held in RAM; last commit 2026-06-29); patrick091210-arch/CardputerADVdictionary (Apache-2.0, English; last commit 2026-04-06); rberenguel/m5cardputer-de-en-translator (MIT, German-English via SQLite on SD using WikDict data; last commit 2024-07-02).

- Applies to: Mostly Cardputer ADV; the de-en translator targets the original Cardputer
- Source: <https://github.com/rabchang/m5_stack_cardputer_dictionary>
- Source: <https://github.com/gwz999-gwz/card_dic-for-cardputer-adv>
- Source: <https://github.com/patrick091210-arch/CardputerADVdictionary>
- Source: <https://github.com/rberenguel/m5cardputer-de-en-translator>

### sw-20 · not checked

Online Japanese-capable chat and translation firmwares exist. GeminiCardputerADV_Japanese (ADV, no licence file, last commit 2026-09-13) is a Gemini chat client with a 12 px Japanese font and romaji-to-hiragana input but no kanji conversion; its README says the bundled binary was not tested on real hardware and that TLS certificate verification is skipped. CardputerOS by urazalievf (MIT, last commit 2026-08-25) has a Translate app covering 15 languages that renders kana and Chinese using an embedded efont, plus notes, voice-to-text and seven AI backends; its README describes the original Cardputer and does not mention ADV.

- Applies to: GeminiCardputerADV_Japanese: Cardputer ADV. CardputerOS: Cardputer (StampS3); ADV not mentioned
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>

### sw-21 · not checked

On-device Japanese speech synthesis exists for the ADV: necobit/Cardputer-TTS takes romaji, converts to hiragana and speaks it offline using the ESP32FormantTTS library (formant synthesis). No licence file was detected on either repo; last commits 2026-03-15. Formant synthesis produces robotic speech, so it is not a good pronunciation model for a learner; pre-generated audio files are the pattern WordCardputer uses instead.

- Applies to: Cardputer ADV (README names ES8311 DAC and TCA8418 keyboard)
- Source: <https://github.com/necobit/Cardputer-TTS>
- Source: <https://github.com/necobit/ESP32FormantTTS>

### sw-22 · not checked

Reader, audio-player and recorder firmwares exist but none of the ones I opened renders Japanese text. cardputer-books (ADV; reader for TXT/EPUB/FB2 plus an MP3 audiobook player; last commit 2026-09-23) ships a PT Sans font for Russian and English and uses RSVP word-by-word display, which depends on spaces between words. Pocket OS (MIT, ESP-IDF, v0.3.0-rc2, last commit 2026-09-17) offers MP3 music, TXT books and voice notes with a Mac companion. mp3-player-winamp-cardputer-adv (ADV, last commit 2026-03-01) plays MP3 from SD and warns that ESP8266Audio 2.x is incompatible and 1.9.7 must be used. matia6170/cardputer-voice-recorder (no licence found, last commit 2026-09-17) records 16 kHz mono WAV to SD and serves files over a Wi-Fi access point.

- Applies to: cardputer-books, Pocket OS, winamp player: Cardputer ADV. Voice recorder: 'M5Stack Cardputer' (variant not specified)
- Source: <https://github.com/summerduck/cardputer-books>
- Source: <https://raw.githubusercontent.com/summerduck/cardputer-books/main/reader/README.md>
- Source: <https://github.com/markoblogo/Pocket-OS-Cardputer-ABV>
- Source: <https://github.com/AndyAiCardputer/mp3-player-winamp-cardputer-adv>
- Source: <https://github.com/matia6170/cardputer-voice-recorder>

### sw-23 · not checked

I found no Anki client, no .apkg importer and no interval-based spaced-repetition app for the Cardputer or a close M5Stack sibling. The nearest are WordCardputer (weighted random), CineVocab (MIT, ADV, English vocabulary from film subtitles with daily quotas and a review queue; last commit 2026-09-07) and a phonics flashcard toy for M5Stack PaperColor (MIT) whose cards, pictures and narration are all pre-generated on the host.

- Applies to: All Cardputer variants (negative finding)
- Source: <https://github.com/search?q=cardputer+anki&type=repositories>
- Source: <https://github.com/search?q=cardputer+flashcard&type=repositories>
- Source: <https://github.com/topics/cardputer-adv>
- Source: <https://github.com/redredred777/CineVocab>
- Source: <https://github.com/jparkhill/m5stack_epaper_color_phonics>

### sw-24 · not checked

Cardputer-Adv-Radiko (MIT source; the prebuilt binary is a GPLv3 combined work) turns an ADV into a receiver for radiko, the Japan-only internet radio service, and shows the current programme name in Japanese. It works only from a Japanese IP address, and the author warns that use should stay within radiko's terms (listening to your own area; no area spoofing, no redistribution). Last commit 2026-08-27.

- Applies to: Cardputer ADV only (ES8311 codec)
- Source: <https://github.com/NAKADANobuhiro/Cardputer-Adv-Radiko>
- Source: <https://raw.githubusercontent.com/NAKADANobuhiro/Cardputer-Adv-Radiko/main/README.md>
- Source: <https://raw.githubusercontent.com/NAKADANobuhiro/Cardputer-Adv-Radiko/main/LICENSE>

### sw-25 · not checked

SQLite on the microSD is a proven storage option on this hardware: two independent Cardputer projects (WordCardputer and the de-en translator) use siara-cc's Sqlite3Esp32 library (Apache-2.0). The library's last commit was 2024-06-12, and the translator author had to drop large tables and add indexes to get usable query speed.

- Applies to: All ESP32-S3 Cardputer variants using Arduino
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://github.com/rberenguel/m5cardputer-de-en-translator>

### sw-26 · not checked

M5Stack documentation lists the SoC of the Cardputer, v1.1 and ADV as ESP32-S3FN8 with 8 MB flash and lists no PSRAM. Community sources disagree with each other: CardputerOS states 'no PSRAM', while card_dic's README claims 'OPI PSRAM' and WordCardputer builds with -DBOARD_HAS_PSRAM. Designs should assume no PSRAM (only internal RAM, about 320 KB nominal) until checked on the actual device.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/boards/M5STACK_Cardputer/mpconfigboard.h>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>
- Source: <https://github.com/gwz999-gwz/card_dic-for-cardputer-adv>

### sw-27 · not checked

The CardputerZero, announced 2026-05-26, is a different class of device: it runs Linux on a Raspberry Pi Compute Module 0, with a 1.9 inch display and a 46-key keyboard. None of the ESP32 frameworks, launchers or apps in this report apply to it. Secondary reports say shipping starts November 2026, so the owner is unlikely to have one today.

- Applies to: CardputerZero / CardputerZero Lite only
- Source: <https://shop.m5stack.com/blogs/news/m5stack-launches-cardputerzero-a-pocket-sized-linux-computer-for-makers-and-developers>

### sw-28 · not checked

Writing a fresh Arduino/PlatformIO app is a better path than forking any single existing project. Reasons: the closest functional match (WordCardputer) has no licence, Chinese glosses and no true SRS; the best Japanese input engine (M5OpurSan) is an editor rather than a trainer, is ADV-verified only and carries a GPL-2.0 dictionary; the dictionaries hold no Japanese data; MicroHydra renders kanji at 8x8 and has only preview-level ADV support; readers lack Japanese fonts. The pieces that are safely reusable are MIT-licensed: M5OpurSan's IME code, rabchang's binary-index dictionary approach, and the M5GFX fonts.

- Applies to: All ESP32-S3 Cardputer variants
- Source: <https://github.com/Mr-xiaotian/WordCardputer>
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://github.com/rabchang/m5_stack_cardputer_dictionary>
- Source: <https://github.com/echo-lalia/MicroHydra>
- Source: <https://github.com/m5stack/M5GFX>

## What this means for the design

- Build on Arduino + M5Cardputer/M5Unified/M5GFX with PlatformIO, using M5Stack's documented recipe (board esp32-s3-devkitc-1, espressif32@6.7.0, USB CDC flags) plus board_build.partitions = default_8MB.csv. One binary will then run on the original, v1.1 and ADV thanks to runtime auto-detection, which removes most of the variant risk for display and keyboard.
- Pin M5Cardputer to a specific git commit or tag in lib_deps rather than floating. The registry (1.1.1) and GitHub master (1.2.0 behaviour) differ in keyboard handling, and a silent change mid-project would break input.
- Install bmorcelli's Launcher first, before the trip, and treat it as the recovery layer. Ship the app as a plain firmware.bin. Before leaving, copy the current build plus at least one known-good older build and a Launcher .bin onto the microSD so a bad update can be rolled back with no computer.
- For updates during the trip, the workable no-computer routes are: (a) download a .bin on the phone and upload it through Launcher's WebUI over the phone hotspot, or (b) have Launcher fetch it by OTA. Change the WebUI's default admin/launcher login before using hotel Wi-Fi.
- Keep all content (decks, dictionary, audio, phrasebook, progress) as files on the microSD, not compiled into firmware. Then content fixes on the trip need only a file swap via WebUI, not a reflash, and the firmware stays small.
- Use M5GFX's built-in Japanese fonts. On a 240x135 screen, 16 px gives about 15 full-width characters by 8 lines and 24 px about 10 by 5. Budget roughly 160 KB of flash for a 16 px Gothic and 280 KB for a 24 px one; a large 32-40 px font for single-kanji study costs another 400-535 KB. All fit within the roughly 6.5 MB left beside Launcher.
- Check glyph coverage on the Mac: run every character in the generated decks and dictionary against the chosen font's glyph list (about 4,425 for lgfxJapanGothic, about 10,838 for efontJA) and either switch font or substitute for missing kanji. Rare kanji in place names and menus are the likely gaps.
- Pre-compute on the Mac: a Japanese-English dictionary converted to a sorted binary file plus index (or a trimmed, indexed SQLite file) keyed by kana and by kanji; deck files with English glosses; per-word and per-phrase audio as 16 kHz mono WAV; and any example sentences. The device should only do lookups and playback.
- Assume no PSRAM. Never load a whole dictionary or deck into RAM; stream from SD with binary search or indexed queries, and keep audio playback streaming. This matches how the existing Cardputer dictionaries work.
- Implement real interval-based spaced repetition in the app since nothing existing provides it. Store review state in a small file on SD and write it atomically (write to a temp file, then rename) so a flat battery mid-session does not corrupt progress.
- Spaced repetition needs the date. Sync time by NTP whenever Wi-Fi is available and design the scheduler to degrade safely (for example session-count based) when the clock is unknown. Whether the variant has a battery-backed clock is a hardware-facet question.
- For typed answers, romaji-to-kana input is straightforward and already implemented in three projects. Full kana-kanji conversion is available from M5OpurSan under MIT, but its dictionary is GPL-2.0 and 33 MB; using it is fine for a personal device, and matters only if the firmware is later published.
- Prefer pre-generated native-quality audio over on-device synthesis for anything the learner will imitate. On-device formant TTS is only suitable as a fallback for arbitrary typed text.
- Treat online features (LLM chat, translation, conversation practice) as an optional layer that works only when tethered. Keep the API key in a config file on SD, not in firmware, and do not copy the pattern of skipping TLS certificate checks on hotel Wi-Fi.
- Avoid MicroHydra, CircuitPython and UIFlow2 as the main platform for this project: MicroHydra's Japanese rendering is 8x8 and its ADV support is preview-only; CircuitPython has no ADV board; UIFlow2's Japanese font availability on Cardputer is unconfirmed. They remain fine for quick experiments.
- Do not fork WordCardputer or copy its code without the author's permission, since it has no licence. Its feature set and SD layout are still a good design reference.
- If the device is an ADV, more becomes possible: better audio through the ES8311 codec and headphone jack (useful for listening practice in public), plus existing ADV-only apps such as the radiko receiver. If it is an original or v1.1, plan for speaker-only audio and test microphone features early.
- Use a microSD of 32 GB or less, formatted FAT32 with an MBR partition table. This is what Launcher and M5OpurSan both recommend and avoids the most common card failures.

## Not settled

- Does the device have PSRAM? M5Stack docs list none, CardputerOS says none, but two community projects assume it. Needs a one-line check on the real device (ESP.getPsramSize()).
- Does M5Cardputer 1.2.0 really break existing keyboard code as CardEX reports? I did not diff 1.1.1 against 1.2.0.
- How many Joyo and JLPT kanji are missing from the 4,425-glyph lgfxJapanGothic set? Not checked; needs a script on the Mac.
- Does UIFlow2's Cardputer firmware expose any built-in Japanese font to the display API? Source reading was inconclusive and I did not run it.
- Do M5OpurSan and WordCardputer run correctly on the original Cardputer / v1.1? M5OpurSan's author tested ADV only; WordCardputer does not state which variants it was tested on.
- How fast is dictionary lookup in practice on this hardware for a full Japanese-English dictionary (about 200k+ entries) using a binary index versus SQLite? Existing projects prove feasibility for English-Chinese but publish no timings.
- Does Launcher's WebUI upload work reliably when the Cardputer and phone are connected through an iPhone or Android personal hotspot (client isolation varies by phone)? Not documented.
- What app-partition size does Launcher create for a custom firmware with no data partition, and does it preserve an app's NVS settings across an app update? The wiki describes dynamic partitioning but not these specifics.
- Licences for several repos (card_dic, Cardputer-TTS, ESP32FormantTTS, cardputer-voice-recorder, cardputer-books) could not be confirmed because the GitHub API was rate-limited and no licence showed on the repo page.
- CardputerZero shipping date (November 2026) came from press snippets, not from an M5Stack page I opened.
- Dictionary data licensing (for example JMdict/EDICT terms) and audio-generation options belong to another facet and were not researched here.
