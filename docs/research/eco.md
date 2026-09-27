# Software ecosystem and existing apps

Research only; nothing was built or written. All claims below come from pages or source files I opened on 2026-09-27 (GitHub repo pages, raw source files, commit/release Atom feeds, docs.m5stack.com, PlatformIO registry API). The GitHub REST API was rate-limited, so licences were read from repo pages and LICENSE files; "no licence found" means no LICENSE file was visible, not that I confirmed the author's intent. Headline findings: 1. Arduino + M5Cardputer/M5Unified/M5GFX under PlatformIO is the most mature path and the one nearly every relevant existing project uses. One binary runs on the original Cardputer, v1.1 and ADV because M5GFX auto-detects the board at runtime and M5Cardputer picks the keyboard driver from that. M5GFX already bundles Japanese bitmap fonts (kana + about 4,400 to 10,800 glyphs depending on family), so Japanese display is a solved problem in this stack. 2. bmorcelli's Launcher (v2.9.1, MIT, supports Cardputer and ADV) gives a genuine no-computer recovery path: install a .bin from the microSD, from a phone browser over the Launcher WebUI, or by OTA download; hold Enter at boot to get back to the Launcher. M5Burner is desktop-only. 3. Relevant prior art exists and is recent. The three most useful: WordCardputer (Japanese/English flashcards, dictation with romaji-to-kana IME, listening mode, SQLite + WAV on SD; but Chinese glosses and no licence file), M5OpurSan (fully offline Japanese kana-kanji IME with a 927k-word dictionary on SD; MIT code, GPL-2.0 dictionary; verified on ADV only), and several offline SD-card dictionaries (English-Chinese) that prove the binary-index-on-SD lookup pattern. I found no Anki client and no Japanese-English dictionary for the Cardputer. 4. Recommendation: write a fresh Arduino/PlatformIO app, installed through Launcher, borrowing patterns (and MIT code where licensed) rather than forking any single project. No existing project combines English glosses, a real SRS scheduler, a Japanese-English dictionary and a clean licence. 5. Variant caveat: several of the best Japanese-specific projects target the ADV only (ES8311 audio, TCA8418 keyboard). If the device turns out to be a CardputerZero (Linux, Raspberry Pi CM0), none of this facet applies; that is unlikely given the 56-key / 1.14 inch description and its late-2026 shipping.

Fact-check: done.

## Statements

### sw-01 · confirmed

The official M5Cardputer Arduino library supports both the original Cardputer and the Cardputer ADV. ADV support was added in release 1.1.0 (2025-09-05). The newest GitHub tag is 1.2.0 (2026-06-08, adds an Fn key layer); last commit on master was 2026-07-21.

- Applies to: Cardputer (K132), Cardputer v1.1, Cardputer ADV
- Correction: Confirmed as written. Sharpening: 1.2.0 exists only as a GitHub tag and release. Both the PlatformIO registry and the Arduino Library Manager index still list 1.1.1 as the newest installable version. The licence is declared only through SPDX MIT headers in the source files (no LICENSE file; the PlatformIO registry licence field is null). Cardputer v1.1 has no code path of its own and is handled as the original Cardputer.
- Source: <https://github.com/m5stack/M5Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/library.properties>
- Source: <https://github.com/m5stack/M5Cardputer/releases.atom>
- Source: <https://github.com/m5stack/M5Cardputer/commits/master.atom>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/M5Cardputer.cpp>
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5Cardputer>

### sw-02 · confirmed

The PlatformIO registry still serves M5Cardputer 1.1.1, and the 1.2.0 git tag itself still declares version=1.1.1 in library.properties and library.json. So 'm5stack/M5Cardputer' from the registry and the GitHub URL give different keyboard behaviour. A third-party project (CardEX) reports 1.2.0 changed the keyboard API incompatibly.

- Applies to: All ESP32-S3 Cardputer variants (build-time concern)
- Correction: Confirmed, and I diffed the library myself, which the researcher had not. At tag 1.1.1 plain Backspace sets keysState().del, and keys pressed while Fn is held still populate keysState().word. At tag 1.2.0 (Keyboard.cpp is byte-identical to master) plain Backspace sets a new field keysState().backspace, del is set only by Fn+Backspace, and when Fn is held updateKeysState() returns after the Fn layer so word stays empty. 1.2.0 also adds fields esc, f1 to f12, up, down, left, right and a third key-map column. Code written for 1.1.1 that uses status.del for backspace compiles against 1.2.0 but silently stops deleting; code written for 1.2.0 that uses status.backspace does not compile against 1.1.1. The Arduino Library Manager index also tops out at 1.1.1, so 1.2.0 is obtainable only from GitHub. Applies to K132, v1.1 and ADV.
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/1.2.0/library.properties>
- Source: <https://github.com/prokke/CardEX-for-Cardputer-ADV>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/1.1.1/src/utility/Keyboard/Keyboard.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/1.2.0/src/utility/Keyboard/Keyboard.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.h>

### sw-03 · confirmed

Board auto-detection happens at runtime inside M5GFX, not at compile time. It identifies the ST7789 panel on GPIO 33-37, then reads GPIO 8/9 with pull-downs: if both read high (I2C pull-ups present) the board is CardputerADV, otherwise Cardputer. M5Cardputer's Keyboard.begin() then selects a GPIO-matrix reader for Cardputer or a TCA8418 I2C reader for ADV. There is no separate board ID for v1.1, so it is treated as the original Cardputer.

- Applies to: Cardputer (K132), Cardputer v1.1, Cardputer ADV
- Correction: Confirmed. Sharpening: inside the block the order is ST7789 panel ID on GPIO 33 to 37; then GPIO 5 and 6 both high plus I2C devices answering at 0x40 and 0x41 means VAMeter; otherwise GPIO 8 and 9 both high means CardputerADV; otherwise Cardputer. M5Unified then picks speaker, microphone and SD pin mappings per detected board at runtime (ADV has its own speaker and microphone enable callbacks), so one Arduino binary can serve K132, v1.1 and ADV as long as the app uses M5Unified's Speaker and Mic rather than driving the ES8311 codec directly.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/boards.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>

### sw-04 · confirmed

M5Stack's documented PlatformIO configuration for both Cardputer v1.1 and Cardputer ADV uses board = esp32-s3-devkitc-1 (not m5stack-stamps3), platform = espressif32@6.7.0, framework = arduino, build flags -DESP32S3 -DCORE_DEBUG_LEVEL=5 -DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1, and lib_deps pointing at the M5Cardputer GitHub URL. A board definition named m5stack-stamps3 does exist in platform-espressif32 (8MB flash, default_8MB.csv, ARDUINO_USB_MODE=1) but does not set CDC_ON_BOOT.

- Applies to: Cardputer v1.1, Cardputer ADV (identical text on both doc pages); by extension the original Cardputer
- Correction: Confirmed; the identical block is also on the original Cardputer (K132) docs page, so all three pages agree. Sharpening: the environment is [env:m5stack-cardputer] with upload_speed = 1500000, and lib_deps is the unpinned entry 'M5Cardputer=https://github.com/m5stack/M5Cardputer', which resolves to master and therefore to the 1.2.0 keyboard behaviour, not the 1.1.1 behaviour the registry gives. espressif32@6.7.0 was released 2024-05-14 and ships Arduino core 2.0.16 (framework-arduinoespressif32 3.20016, GCC 8.4.0). m5stack-stamps3.json exists at platform tags v6.7.0 and v7.1.3 as well as develop. There is no Cardputer-specific PlatformIO board definition.
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/platformio.ini>
- Source: <https://docs.m5stack.com/en/core/Cardputer>

### sw-05 · confirmed

Current library versions are M5Unified 0.2.23 and M5GFX 0.2.30, both released 2026-09-21, and M5Unified 0.2.23 requires M5GFX >= 0.2.30. Both are MIT licensed and actively maintained (three releases each in the last five weeks).

- Applies to: All ESP32-S3 Cardputer variants
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/library.properties>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/library.properties>
- Source: <https://github.com/m5stack/M5Unified/releases.atom>
- Source: <https://github.com/m5stack/M5GFX/releases.atom>
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5GFX>
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5Unified>

### sw-06 · corrected

M5GFX ships compiled-in Japanese fonts. The IPA-derived lgfxJapanGothic / lgfxJapanMincho families come in sizes 8, 12, 16, 20, 24, 28, 32, 36, 40 px with about 4,425 glyphs each; efontJA comes in 10, 12, 14, 16, 24 px with about 10,838 glyphs (9,801 at 24 px). Flash cost per font: gothic_12 about 109 KB, gothic_16 about 159 KB, gothic_24 about 277 KB; efont_ja_16 about 467 KB, efont_ja_24 about 744 KB. M5GFX also supports runtime-loaded VLW fonts.

- Applies to: All ESP32-S3 Cardputer variants using Arduino/M5GFX
- Correction: Everything is right except one figure: lgfx_font_japan_gothic_24 is 278,669 bytes (about 279 KB); 276,933 bytes is the proportional variant gothic_p_24. Other sizes confirmed: gothic_12 108,977; gothic_16 159,271; efont_ja_16 467,155; efont_ja_24 743,624. Proportional (P) variants come from IPAex fonts and hold 4,427 glyphs; efontJA 14 and 16 px hold 10,839. Coverage, which the researcher left open, measured by parsing the u8g2 glyph tables in the source: lgfxJapanGothic 12, 16 and 24 each hold 3,487 kanji plus all hiragana and katakana, and cover every kanji in a 2,136-entry Joyo list except the variant form U+5265 (the official form U+525D is present); every JLPT N5 to N1 kanji in that list is covered. They hold no macron vowels (U+0101, U+012B, U+016B, U+0113, U+014D), so Hepburn romaji with macrons cannot be drawn with them. efontJA_16 holds 9,500 kanji, covers the whole Joyo list including both variant forms and includes the macron vowels; efontJA_24 holds 8,784 kanji. No built-in font can hold U+20B9F because the format stores 16-bit code points. VLW runtime fonts are supported; the loader allocates 9 bytes of heap per glyph and reads bitmaps from the file at draw time. Applies to all ESP32-S3 variants under Arduino/M5GFX.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl>

### sw-07 · confirmed

ESP-IDF is a supported but heavier path. M5Stack's factory firmware (M5Cardputer-UserDemo, MIT) is an ESP-IDF project: the main branch targets ESP-IDF v4.4.6 for the original Cardputer and a separate CardputerADV branch targets ESP-IDF v5.4.2. The two variants therefore have separate factory firmware builds.

- Applies to: Cardputer (K132) main branch; Cardputer ADV on the CardputerADV branch
- Correction: Confirmed. Sharpening: the last commit on the CardputerADV branch was 2026-06-08; the ADV factory firmware also lists M5Unified and M5GFX among its components.
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer-UserDemo/main/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer-UserDemo/CardputerADV/README.md>
- Source: <https://github.com/m5stack/M5Cardputer-UserDemo/releases.atom>
- Source: <https://github.com/markoblogo/Pocket-OS-Cardputer-ABV>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer-UserDemo/main/LICENSE>
- Source: <https://github.com/m5stack/M5Cardputer-UserDemo/commits/main.atom>

### sw-08 · corrected

UIFlow2 (M5Stack's MicroPython firmware, MIT) has dedicated board builds for both Cardputer and CardputerADV; latest release is 2.5.3 (2026-09-11). Whether the Cardputer build exposes a usable built-in Japanese font to the display API is not settled: the efontJA_24 binding in the source is compiled only for BOARD_ID 25, while the Cardputer board (BOARD_ID 14) sets an LVGL Japanese font flag but has LVGL disabled.

- Applies to: Cardputer (K132)/v1.1 and Cardputer ADV
- Correction: Release facts are right: 2.5.3 on 2026-09-11, MIT, separate builds M5STACK_Cardputer (BOARD_ID 14) and M5STACK_CardputerADV (BOARD_ID 24). The font conclusion is wrong. The BOARD_ID == 25 branch serves one other board only. In the #else branch used by both Cardputer builds, the display module's font table exposes AlibabaSansJA24 and its alias EFontJA24 whenever FONT_ALIBABASANS_JA24 is 1, and both Cardputer board files set it to 1. The flags reach the table through a generated header mpconfigboard_fonts.h. The font is fonts/AlibabaSans_JP24.c, a 24 px 1-bpp font wrapped for M5GFX and compiled inside the M5Unified component; it does not depend on the MicroPython LVGL module, so MICROPY_PY_LVGL 0 does not disable it, and TINY_FONT is not set for these boards. Its generation range lists 4,217 code points including 3,395 kanji. So the source indicates UIFlow2 on Cardputer and ADV can draw Japanese, at one size only (24 px, roughly 10 full-width characters by 5 lines on 240x135). Not tested on hardware.
- Source: <https://github.com/m5stack/uiflow-micropython>
- Source: <https://github.com/m5stack/uiflow-micropython/releases.atom>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/components/M5Unified/mpy_m5gfx.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/boards/M5STACK_Cardputer/mpconfigboard.cmake>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/LICENSE>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/boards/M5STACK_CardputerADV/mpconfigboard.cmake>

### sw-09 · confirmed

CircuitPython has an official board build for the original Cardputer (stable 10.3.1) but I found no dedicated Cardputer ADV board: circuitpython.org/board/m5stack_cardputer_adv returns 404 and the CircuitPython source tree has only m5stack_cardputer and m5stack_cardputer_ros, with no TCA8418 reference in the board files I checked.

- Applies to: Cardputer (K132) / v1.1 supported; Cardputer ADV apparently not
- Correction: Confirmed. Sharpening: circuitpython.org/downloads lists only m5stack_cardputer and m5stack_cardputer_ros; the main source tree has only those two board directories; the m5stack_cardputer board files contain no TCA8418 reference and set no PSRAM size. 11.0.0-alpha.1 builds also exist for m5stack_cardputer.
- Source: <https://circuitpython.org/board/m5stack_cardputer/>
- Source: <https://circuitpython.org/board/m5stack_cardputer_adv/>
- Source: <https://github.com/adafruit/circuitpython/tree/main/ports/espressif/boards>
- Source: <https://circuitpython.org/downloads>
- Source: <https://raw.githubusercontent.com/adafruit/circuitpython/main/ports/espressif/boards/m5stack_cardputer/mpconfigboard.mk>

### sw-10 · confirmed

MicroHydra (GPL-3.0) is a MicroPython app launcher where any .py, .mpy or package folder dropped into /apps on flash or on the microSD becomes an app, so apps can be edited or replaced by swapping files on the SD with no reflash. Stable release is v2.5.1 (2026-03-27); ADV support is only 'partial' and only in v2.6-preview (2026-03-30), which is also the date of the last commit.

- Applies to: Cardputer (K132)/v1.1 fully; Cardputer ADV partial (preview release)
- Source: <https://github.com/echo-lalia/MicroHydra>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra/main/README.md>
- Source: <https://github.com/echo-lalia/MicroHydra/releases.atom>
- Source: <https://github.com/echo-lalia/MicroHydra/tree/main/devices>
- Source: <https://github.com/echo-lalia/MicroHydra/commits/main.atom>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra/main/LICENSE>

### sw-11 · confirmed

MicroHydra can display Japanese, but only through a built-in 8x8 pixel UTF-8 fallback font (a 524,288-byte file, consistent with 65,536 code points at 8 bytes each). Eight pixels is too coarse to render most kanji legibly, so MicroHydra is a poor fit for kanji study without writing a custom font renderer.

- Applies to: Cardputer (K132)/v1.1 and ADV under MicroHydra
- Correction: Confirmed. Sharpening: when a larger bitmap font is active MicroHydra integer-scales the same 8x8 glyph (scale = font height // 8), which adds size but no detail. lib/kanji does not exist in current MicroHydra main (src/lib holds audio, display, easing, hydra, sdcard, userinput, battlevel.py and zipextractor.py), so the KanjiReader app cannot run unmodified on v2.x. The legibility judgement remains an untested inference.
- Source: <https://raw.githubusercontent.com/wiki/echo-lalia/MicroHydra/Display.md>
- Source: <https://github.com/echo-lalia/MicroHydra/tree/main/src/font>
- Source: <https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/KanjiReader>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra-Apps/main/app-source/KanjiReader/KanjiReader.py>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra/main/src/font/utf8_8x8.bin>
- Source: <https://raw.githubusercontent.com/echo-lalia/MicroHydra/main/src/lib/display/displaycore.py>

### sw-12 · confirmed

bmorcelli's Launcher (MIT) supports Cardputer and Cardputer ADV in a single build and can install firmware three ways without a computer: from a .bin on the microSD, by OTA download over Wi-Fi from online catalogues (M5Burner / LauncherHub / GitHub links), and via a WebUI where a phone browser uploads a .bin. Latest release is 2.9.1 (2026-09-04); last commit 2026-09-17. The README on main already documents an unreleased 2.10.0.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Correction: Confirmed; release 2.9.1 has a single Cardputer asset, Launcher-m5stack-cardputer.bin. Sharpening: the wiki lists two further install routes, a direct URL saved as a Favorite and a serial command, and the WebUI file manager lets a phone upload ordinary files to the SD card as well as firmware. Launcher is itself built with the pioarduino platform on ESP-IDF 5.5 libraries.
- Source: <https://github.com/bmorcelli/Launcher>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/boards/m5stack-cardputer/platformio.ini>
- Source: <https://github.com/bmorcelli/Launcher/releases.atom>
- Source: <https://github.com/bmorcelli/Launcher/wiki/Obtaining-binaries-to-launch>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Explaining-the-project.md>

### sw-13 · confirmed

With Launcher installed, switching between Launcher and a custom app is done at power-on: Launcher shows a boot screen, pressing Enter opens the Launcher menu, and doing nothing boots the installed app. Since 2.7.0 several firmwares can be installed side by side and since 2.8.0 a keyboard key can be bound to a binary. Launcher itself occupies a protected 0x150000 (about 1.3 MB) partition at 0x10000 on the 8 MB flash, leaving roughly 6.5 MB for apps plus their data partitions.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Correction: Confirmed. Sharpening: auto-boot into the app applies when the 'Boot to Launcher' setting is disabled; the space left after Launcher and its coredump partition is 0x690000 bytes (6,881,280 bytes, 6.56 MiB); Launcher's partition has subtype 'test' and the wiki calls it a protected app partition; on a keyboard device the boot screen also accepts a digit to fast-boot an installed app.
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/support_files/custom_8Mb.csv>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Explaining-the-project.md>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/boards/m5stack-cardputer/platformio.ini>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Home.md>

### sw-14 · confirmed

Launcher's README recommends an SDHC card of 32 GB or less, formatted FAT32 with an MBR partition table; exFAT and larger cards are supported since 2.8.0 but smaller cards are still recommended.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV when using Launcher
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md>

### sw-15 · confirmed

M5Burner is a desktop application (Windows, macOS, Linux) that flashes over USB. It cannot update the device without a computer. Its firmware catalogue is, however, reachable from the device itself through Launcher's OTA menu.

- Applies to: All ESP32-S3 Cardputer variants
- Correction: Confirmed. Sharpening: the docs page names the downloads M5Burner_Windows, M5Burner_MacOS and M5Burner_Linux without stating CPU architecture. Launcher's README says OTA installs from 'M5Burner or GitHub links' while its wiki says the OTA list is served by LauncherHub; whether every M5Burner entry is mirrored there was not verified. The M5Burner catalogue itself is publicly readable as JSON and had 687 entries in its cardputer category when fetched.
- Source: <https://docs.m5stack.com/en/uiflow/m5burner/intro>
- Source: <https://raw.githubusercontent.com/bmorcelli/Launcher/main/README.md>
- Source: <https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Functionalities-explained.md>
- Source: <https://m5burner-api.m5stack.com/api/firmware>

### sw-16 · confirmed

Bruce (AGPL-3.0, latest release 1.16.1 on 2026-08-11) supports Cardputer and Cardputer ADV and can be launched from Launcher, but it is an offensive-security toolkit with no language-learning function. It is not a useful base for this project.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Correction: Confirmed. Sharpening: github.com/pr3y/Bruce now redirects to github.com/BruceDevices/firmware.
- Source: <https://github.com/pr3y/Bruce>
- Source: <https://github.com/pr3y/Bruce/releases.atom>
- Source: <https://github.com/BruceDevices/firmware>
- Source: <https://raw.githubusercontent.com/pr3y/Bruce/main/README.md>
- Source: <https://raw.githubusercontent.com/pr3y/Bruce/main/LICENSE>

### sw-17 · confirmed

WordCardputer is the closest existing project to the goal: a vocabulary trainer for M5Cardputer with Japanese and English decks, flashcard mode with 1-5 proficiency scores, dictation mode with a romaji-to-kana IME, a listening mode that plays per-word WAV audio from SD, statistics, SQLite storage and a Wi-Fi web panel for importing JSON decks. It displays Japanese (kana and kanji fields). Limitations: glosses and README are in Chinese, scheduling is weighted-random (weight = 6 - score) rather than interval-based spaced repetition, and the repo has no LICENSE file. Last commit 2026-09-01.

- Applies to: Written for M5Cardputer using the M5Cardputer library; ADV compatibility not stated in the README
- Correction: Confirmed. Sharpening: the README does not mention ADV anywhere; the build takes m5stack/M5Cardputer from the registry, so it is written against the 1.1.1 keyboard API (it uses Del for delete and Fn as a plain key).
- Source: <https://github.com/Mr-xiaotian/WordCardputer>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/README.md>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://github.com/Mr-xiaotian/WordCardputer/commits/main.atom>

### sw-18 · confirmed

M5OpurSan is a fully offline Japanese word processor with a kana-kanji conversion engine that runs on the device: romaji to kana, Space for kanji candidates, backed by a 927,000-entry, 33.3 MB dictionary file on the microSD built from alt-cannadic and ipadic. Conversion is word-level, not phrase-level. Code is MIT; everything under dict/ (including the dictionary binary) is GPL-2.0. The author tested only on ADV and says the original / v1.1 'may work' but is unverified. Last commit 2026-08-25.

- Applies to: Cardputer ADV (verified by author); Cardputer K132 / v1.1 unverified
- Correction: Confirmed. Sharpening: the dictionary maps kana to kanji only and carries no English glosses, so it is an input method, not a bilingual dictionary; the README adds that ipadic is under the NAIST licence and that the input buffer of the conversion front end is 32 characters.
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md>
- Source: <https://github.com/kikyujin/M5OpurSan/commits/main.atom>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/LICENSE>

### sw-19 · confirmed

Offline SD-card dictionaries already run on the Cardputer, proving the lookup pattern, but every one I found is English-Chinese or English-only, not Japanese-English. Examples: rabchang/m5_stack_cardputer_dictionary (MIT, ADV, binary index on SD with on-device binary search, prefix suggestions, favourites; last commit 2026-08-23); gwz999-gwz/card_dic-for-cardputer-adv (no licence found; dictionary and font both on SD, 32 MB dictionary not held in RAM; last commit 2026-06-29); patrick091210-arch/CardputerADVdictionary (Apache-2.0, English; last commit 2026-04-06); rberenguel/m5cardputer-de-en-translator (MIT, German-English via SQLite on SD using WikDict data; last commit 2024-07-02).

- Applies to: Mostly Cardputer ADV; the de-en translator targets the original Cardputer
- Correction: Confirmed for all four repositories (existence, licence, last commit date, behaviour). Sharpening: two more exist and are also English or ASCII only: majharulislamjihad2009-a11y/Cardputer_Dictionary (offline English, about 100,000 words on SD, no licence file, last commit 2026-08-10) and an M5Burner entry 'Dictionary' by tabozen (JSONL, ASCII only). card_dic builds with OPI PSRAM flags and recommends a FAT32 card of 64 GB or more, which conflicts with Launcher's advice of 32 GB or less.
- Source: <https://github.com/rabchang/m5_stack_cardputer_dictionary>
- Source: <https://github.com/gwz999-gwz/card_dic-for-cardputer-adv>
- Source: <https://github.com/patrick091210-arch/CardputerADVdictionary>
- Source: <https://github.com/rberenguel/m5cardputer-de-en-translator>
- Source: <https://raw.githubusercontent.com/rabchang/m5_stack_cardputer_dictionary/main/README.md>
- Source: <https://raw.githubusercontent.com/rabchang/m5_stack_cardputer_dictionary/main/LICENSE>

### sw-20 · confirmed

Online Japanese-capable chat and translation firmwares exist. GeminiCardputerADV_Japanese (ADV, no licence file, last commit 2026-09-13) is a Gemini chat client with a 12 px Japanese font and romaji-to-hiragana input but no kanji conversion; its README says the bundled binary was not tested on real hardware and that TLS certificate verification is skipped. CardputerOS by urazalievf (MIT, last commit 2026-08-25) has a Translate app covering 15 languages that renders kana and Chinese using an embedded efont, plus notes, voice-to-text and seven AI backends; its README describes the original Cardputer and does not mention ADV.

- Applies to: GeminiCardputerADV_Japanese: Cardputer ADV. CardputerOS: Cardputer (StampS3); ADV not mentioned
- Correction: Confirmed. Sharpening: CardputerOS docs/hardware.md names its target as 'M5Stack Cardputer v1.1, the StampS3 version' and states PSRAM 'none on stock StampS3'. GeminiCardputerADV_Japanese pins M5Cardputer to commit f1392858 (master of 2026-07-20, so the 1.2.0 keyboard API) and builds on espressif32@6.7.0.
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/README.md>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/platformio.ini>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese/commits/master.atom>

### sw-21 · corrected

On-device Japanese speech synthesis exists for the ADV: necobit/Cardputer-TTS takes romaji, converts to hiragana and speaks it offline using the ESP32FormantTTS library (formant synthesis). No licence file was detected on either repo; last commits 2026-03-15. Formant synthesis produces robotic speech, so it is not a good pronunciation model for a learner; pre-generated audio files are the pattern WordCardputer uses instead.

- Applies to: Cardputer ADV (README names ES8311 DAC and TCA8418 keyboard)
- Correction: necobit/Cardputer-TTS has no LICENSE file, but its README has a licence section that says MIT. necobit/ESP32FormantTTS has neither a LICENSE file nor any licence statement, so the library the app depends on grants no reuse rights. The default branch of both is master; last commits 2026-03-15. The engine accepts hiragana only, exposes a single global pitch (ttsSetPitch, 50 to 400 Hz) and documents no pitch-accent handling, which supports the judgement that it is not a good pronunciation model. ADV only, because the app drives the ES8311 codec directly.
- Source: <https://github.com/necobit/Cardputer-TTS>
- Source: <https://github.com/necobit/ESP32FormantTTS>
- Source: <https://raw.githubusercontent.com/necobit/Cardputer-TTS/master/README.md>
- Source: <https://github.com/necobit/Cardputer-TTS/commits/master.atom>
- Source: <https://raw.githubusercontent.com/necobit/ESP32FormantTTS/master/README.md>
- Source: <https://raw.githubusercontent.com/necobit/ESP32FormantTTS/master/library.properties>

### sw-22 · confirmed

Reader, audio-player and recorder firmwares exist but none of the ones I opened renders Japanese text. cardputer-books (ADV; reader for TXT/EPUB/FB2 plus an MP3 audiobook player; last commit 2026-09-23) ships a PT Sans font for Russian and English and uses RSVP word-by-word display, which depends on spaces between words. Pocket OS (MIT, ESP-IDF, v0.3.0-rc2, last commit 2026-09-17) offers MP3 music, TXT books and voice notes with a Mac companion. mp3-player-winamp-cardputer-adv (ADV, last commit 2026-03-01) plays MP3 from SD and warns that ESP8266Audio 2.x is incompatible and 1.9.7 must be used. matia6170/cardputer-voice-recorder (no licence found, last commit 2026-09-17) records 16 kHz mono WAV to SD and serves files over a Wi-Fi access point.

- Applies to: cardputer-books, Pocket OS, winamp player: Cardputer ADV. Voice recorder: 'M5Stack Cardputer' (variant not specified)
- Correction: Confirmed. Sharpening: the winamp README gives the reason for the pin: ESP8266Audio 2.x needs the ESP-IDF 5 I2S API, which Arduino cores built on ESP-IDF 4.4 lack, and that is the core the documented PlatformIO recipe installs. The winamp player carries an MIT LICENSE file. cardputer-books offers separate install and update binaries and asks Launcher to create a 2 MB data partition.
- Source: <https://github.com/summerduck/cardputer-books>
- Source: <https://raw.githubusercontent.com/summerduck/cardputer-books/main/reader/README.md>
- Source: <https://github.com/markoblogo/Pocket-OS-Cardputer-ABV>
- Source: <https://github.com/AndyAiCardputer/mp3-player-winamp-cardputer-adv>
- Source: <https://github.com/matia6170/cardputer-voice-recorder>
- Source: <https://raw.githubusercontent.com/summerduck/cardputer-books/main/README.md>

### sw-23 · corrected

I found no Anki client, no .apkg importer and no interval-based spaced-repetition app for the Cardputer or a close M5Stack sibling. The nearest are WordCardputer (weighted random), CineVocab (MIT, ADV, English vocabulary from film subtitles with daily quotas and a review queue; last commit 2026-09-07) and a phonics flashcard toy for M5Stack PaperColor (MIT) whose cards, pictures and narration are all pre-generated on the host.

- Applies to: All Cardputer variants (negative finding)
- Correction: Still true: no Anki client, no .apkg importer and no true interval-scheduling app (SM-2 or FSRS style) for any Cardputer variant. My repository searches for cardputer with anki (0 results), flashcard (WordCardputer only), kanji (M5OpurSan only) and vocabulary (WordCardputer, CineVocab), the curated awesome-m5stack-cardputer list, and a keyword scan of the 687-entry cardputer category of the M5Burner catalogue found nothing else. But the list of nearest projects on M5Stack siblings was incomplete. (1) DrDavidDa/PaperColor-Desk-Terminal (MIT, M5Stack PaperColor, last commit 2026-09-14) advertises an 'Anki spaced-repetition algorithm'; its code keeps a three-state card status with lastReviewedEpoch and cooldownUntilEpoch (mastered means a 3-day cooldown), persisted in NVS and on SD, with a host script converting Anki Markdown to JSON. It is time-based but is not SM-2 and not an Anki client. (2) micokonsep/flipcard-papers3 (M5Stack PaperS3, no licence file, last commit 2025-08-20) is a JSON-driven language-learning flashcard app that names Japanese as a supported content language and draws all card text as pre-rendered PNG images. (3) saurav2107/PaperOS (MIT, last commit 2026-09-21) includes JSON flashcard decks. CineVocab (MIT, ADV, last commit 2026-09-07, built on M5Cardputer 1.2.x) and the phonics toy are as stated.
- Source: <https://github.com/search?q=cardputer+anki&type=repositories>
- Source: <https://github.com/search?q=cardputer+flashcard&type=repositories>
- Source: <https://github.com/topics/cardputer-adv>
- Source: <https://github.com/redredred777/CineVocab>
- Source: <https://github.com/jparkhill/m5stack_epaper_color_phonics>
- Source: <https://github.com/DrDavidDa/PaperColor-Desk-Terminal>

### sw-24 · confirmed

Cardputer-Adv-Radiko (MIT source; the prebuilt binary is a GPLv3 combined work) turns an ADV into a receiver for radiko, the Japan-only internet radio service, and shows the current programme name in Japanese. It works only from a Japanese IP address, and the author warns that use should stay within radiko's terms (listening to your own area; no area spoofing, no redistribution). Last commit 2026-08-27.

- Applies to: Cardputer ADV only (ES8311 codec)
- Correction: Confirmed. Sharpening: the README states the ADV has no PSRAM and that the firmware therefore disables HE-AAC SBR; the GPLv3 component is the arduino-libhelix decoder, which the repository does not bundle.
- Source: <https://github.com/NAKADANobuhiro/Cardputer-Adv-Radiko>
- Source: <https://raw.githubusercontent.com/NAKADANobuhiro/Cardputer-Adv-Radiko/main/README.md>
- Source: <https://raw.githubusercontent.com/NAKADANobuhiro/Cardputer-Adv-Radiko/main/LICENSE>
- Source: <https://github.com/NAKADANobuhiro/Cardputer-Adv-Radiko/commits/main.atom>

### sw-25 · confirmed

SQLite on the microSD is a proven storage option on this hardware: two independent Cardputer projects (WordCardputer and the de-en translator) use siara-cc's Sqlite3Esp32 library (Apache-2.0). The library's last commit was 2024-06-12, and the translator author had to drop large tables and add indexes to get usable query speed.

- Applies to: All ESP32-S3 Cardputer variants using Arduino
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://github.com/rberenguel/m5cardputer-de-en-translator>
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib/commits/master.atom>
- Source: <https://raw.githubusercontent.com/siara-cc/esp32_arduino_sqlite3_lib/master/LICENSE>
- Source: <https://raw.githubusercontent.com/siara-cc/esp32_arduino_sqlite3_lib/master/library.properties>

### sw-26 · confirmed

M5Stack documentation lists the SoC of the Cardputer, v1.1 and ADV as ESP32-S3FN8 with 8 MB flash and lists no PSRAM. Community sources disagree with each other: CardputerOS states 'no PSRAM', while card_dic's README claims 'OPI PSRAM' and WordCardputer builds with -DBOARD_HAS_PSRAM. Designs should assume no PSRAM (only internal RAM, about 320 KB nominal) until checked on the actual device.

- Applies to: Cardputer (K132), v1.1, Cardputer ADV
- Correction: Confirmed and strengthened. M5Stack's own firmware treats both variants as having no PSRAM: UIFlow2's M5STACK_Cardputer and M5STACK_CardputerADV board configs include no SPIRAM sdkconfig (M5STACK_CoreS3 includes sdkconfig.spiram_sx) and name the MCU ESP32-S3-FN8; CircuitPython's m5stack_cardputer board sets no PSRAM size while m5stack_cores3 sets 8 MB; the Stamp-S3 and Stamp-S3A docs list ESP32-S3FN8 with 8 MB flash. Two developers with hardware say the same: the Radiko README for the ADV and CardputerOS docs/hardware.md for v1.1. card_dic's 'OPI PSRAM' and WordCardputer's -DBOARD_HAS_PSRAM are build settings, not evidence of hardware. I could not machine-read Espressif's datasheet table, so the part-number decoding itself is not confirmed from Espressif.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/boards/M5STACK_Cardputer/mpconfigboard.h>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>
- Source: <https://github.com/gwz999-gwz/card_dic-for-cardputer-adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>

### sw-27 · corrected

The CardputerZero, announced 2026-05-26, is a different class of device: it runs Linux on a Raspberry Pi Compute Module 0, with a 1.9 inch display and a 46-key keyboard. None of the ESP32 frameworks, launchers or apps in this report apply to it. Secondary reports say shipping starts November 2026, so the owner is unlikely to have one today.

- Applies to: CardputerZero / CardputerZero Lite only
- Correction: Nothing found wrong, but one part is unverified. Confirmed from M5Stack's announcement (dated May 26, 2026; post timestamp 2026-05-27 +08:00): CardputerZero is a Linux handheld built on Raspberry Pi Compute Module 0 with a quad-core Cortex-A53, 1.9 inch display and 46-key keyboard, sold in a full and a Lite version and launched on Kickstarter. None of the ESP32 frameworks, launchers or apps apply to it. The announcement gives no shipping date. I could not verify the November 2026 figure: Kickstarter returned HTTP 403 and the CNX Software article of 2026-05-25 (press, secondary) gives prices but no delivery date. Treat the shipping date as unverified.
- Source: <https://shop.m5stack.com/blogs/news/m5stack-launches-cardputerzero-a-pocket-sized-linux-computer-for-makers-and-developers>
- Source: <https://www.cnx-software.com/2026/05/25/cardputerzero-a-raspberry-pi-cm0-pocket-computer-for-makers/>
- Source: <https://www.kickstarter.com/projects/m5stack/cardputerzero>

### sw-28 · corrected

Writing a fresh Arduino/PlatformIO app is a better path than forking any single existing project. Reasons: the closest functional match (WordCardputer) has no licence, Chinese glosses and no true SRS; the best Japanese input engine (M5OpurSan) is an editor rather than a trainer, is ADV-verified only and carries a GPL-2.0 dictionary; the dictionaries hold no Japanese data; MicroHydra renders kanji at 8x8 and has only preview-level ADV support; readers lack Japanese fonts. The pieces that are safely reusable are MIT-licensed: M5OpurSan's IME code, rabchang's binary-index dictionary approach, and the M5GFX fonts.

- Applies to: All ESP32-S3 Cardputer variants
- Correction: The recommendation to write a fresh Arduino/PlatformIO app is supported by the evidence, with these corrections. (1) The M5GFX Japanese fonts are not MIT: the converted IPA fonts are under the IPA Font License v1.0 and efont under a 3-clause BSD licence; only M5GFX's own code is MIT. (2) M5OpurSan's MIT code is only useful with its dictionary, which is GPL-2.0 (alt-cannadic) plus NAIST-licensed ipadic data; it is also a kana-to-kanji input dictionary with no English glosses. (3) MicroHydra's 8x8 limit holds, but UIFlow2 does expose a 24 px Japanese font on both Cardputer builds, so a MicroPython route is less closed than stated. (4) Reference designs the researcher missed exist on sibling devices: PaperColor-Desk-Terminal (MIT; card-state persistence and cooldown scheduling) and flipcard-papers3 (no licence; pre-rendered PNG text). (5) WordCardputer has no licence, so it can be studied but not copied. (6) A fresh app built on M5Cardputer and M5Unified can be one binary for K132, v1.1 and ADV, which a fork of any ADV-only project would not be.
- Source: <https://github.com/Mr-xiaotian/WordCardputer>
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://github.com/rabchang/m5_stack_cardputer_dictionary>
- Source: <https://github.com/echo-lalia/MicroHydra>
- Source: <https://github.com/m5stack/M5GFX>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/README.md>

## Found by the fact-check

- Version-pinning trap (K132, v1.1, ADV). M5Stack's documented PlatformIO recipe uses the unpinned entry 'M5Cardputer=https://github.com/m5stack/M5Cardputer', which resolves to master and so to the 1.2.0 keyboard API, while 'm5stack/M5Cardputer' from the PlatformIO registry and the Arduino Library Manager both give 1.1.1. My diff shows the two are not interchangeable: in 1.1.1 Backspace sets keysState().del; in 1.2.0 it sets keysState().backspace, del needs Fn+Backspace, and word is empty while Fn is held. Existing projects are split (WordCardputer on 1.1.1, CineVocab and GeminiCardputerADV_Japanese on 1.2.x), so any borrowed input code must match the pinned version. Pin by tag or commit. Sources: https://docs.m5stack.com/en/core/Cardputer-Adv , https://raw.githubusercontent.com/m5stack/M5Cardputer/1.1.1/src/utility/Keyboard/Keyboard.cpp , https://raw.githubusercontent.com/m5stack/M5Cardputer/1.2.0/src/utility/Keyboard/Keyboard.cpp , https://downloads.arduino.cc/libraries/library_index.json.gz
- Built-in font coverage is good enough for study content, with one gap (all variants, Arduino/M5GFX). Parsing the glyph tables shows lgfxJapanGothic 12/16/24 cover all kana, 3,487 kanji, every JLPT N5 to N1 kanji and 2,135 of 2,136 Joyo list entries (only the variant form U+5265 is absent; the official form U+525D is present). They have no macron vowels, so romaji must be written without macrons or drawn with efontJA, which has them and 9,500 kanji at 16 px for 467 KB. Content pipelines should normalise U+5265 to U+525D and avoid U+20B9F. On 240x135 a 16 px font gives about 15 full-width characters by 8 lines, 24 px about 10 by 5, 12 px about 20 by 11 (my arithmetic). Sources: https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c , https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji-jouyou.json
- One binary can serve all three ESP32-S3 variants. M5GFX detects Cardputer versus ADV at runtime and M5Unified maps speaker, microphone and SD pins per board (SD is SCK 40, MOSI 14, MISO 39, CS 12 on both; ADV gets its own codec enable callbacks). Projects that drive the ES8311 directly (Cardputer-TTS, Cardputer-Adv-Radiko, the winamp player) are ADV-only for that reason. This matters because the owner's variant is unknown. Sources: https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp
- The documented toolchain is old and that constrains libraries (all variants). espressif32@6.7.0 dates from 2024-05-14 and ships Arduino core 2.0.16; even the current official platform 7.1.3 (2026-09-11) still ships Arduino core 2.0.17, so Arduino core 3.x needs the community pioarduino platform, which is what Launcher uses. Consequence reported by a project author (community source): ESP8266Audio 2.x does not build on this core and 1.9.7 must be pinned. ESP8266Audio is GPL-3.0, so linking it for MP3 makes the binary GPL-3.0; playing WAV through M5Unified's MIT speaker class avoids that. Default partition scheme default_8MB.csv gives two app slots of 0x330000 bytes (3.34 MB) each. Sources: https://raw.githubusercontent.com/platformio/platform-espressif32/v6.7.0/platform.json , https://raw.githubusercontent.com/platformio/platform-espressif32/v7.1.3/platform.json , https://raw.githubusercontent.com/AndyAiCardputer/mp3-player-winamp-cardputer-adv/main/README.md , https://raw.githubusercontent.com/earlephilhower/ESP8266Audio/master/LICENSE , https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.16/tools/partitions/default_8MB.csv
- RAM budget facts for a no-PSRAM device. Compiled-in u8g2 fonts cost flash only. A VLW font loaded at runtime costs 9 bytes of heap per glyph (about 27 KB for 3,000 glyphs, 63 KB for 7,000) and reads each glyph bitmap from the file when drawing. Community measurements from a developer on Cardputer v1.1 (secondary source): mounting the SD card costs about 29 KB of heap, a TLS handshake needs about 40 KB of contiguous heap, and the largest practical audio buffer is about 5 seconds of 16 kHz mono. This favours compiled-in fonts, streaming audio from SD and keeping online features optional. Sources: https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl , https://raw.githubusercontent.com/urazalievf/cardputer/main/docs/hardware.md
- Launcher practicalities for fixing things on a trip (K132, v1.1, ADV). Launcher must be flashed over USB before leaving; after that a phone can upload a new .bin or content files through the WebUI (default login admin / launcher), or Launcher can install from a direct URL saved as a Favorite, so firmware built by a hosted CI job could be pulled over a hotspot without the Mac. The file to install is .pio/build/<env>/firmware.bin. Inference, not tested: a normal 'pio run -t upload' writes the app at 0x10000, which is exactly where Launcher lives, so USB uploads replace Launcher; to keep it, install builds through Launcher instead. Sources: https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Home.md , https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Functionalities-explained.md , https://raw.githubusercontent.com/wiki/bmorcelli/Launcher/Obtaining-binaries-to-launch.md , https://raw.githubusercontent.com/bmorcelli/Launcher/main/support_files/custom_8Mb.csv
- Ready-made Japanese dictionary data exists in the exact format an existing Cardputer project already uses. WikDict publishes ja-en.sqlite3 (5.5 MB), en-ja.sqlite3 (9.4 MB) and ja.sqlite3 (55.7 MB), last modified 2026-06-23, under Creative Commons BY-SA; the German-English Cardputer translator reads the same WikDict SQLite format after dropping a view and adding an index. That project does not draw Japanese, so the font still has to be changed. Sources: https://download.wikdict.com/dictionaries/sqlite/2/ , https://www.wikdict.com/page/download , https://raw.githubusercontent.com/rberenguel/m5cardputer-de-en-translator/main/README.md
- A font-free rendering pattern is already proven on an M5Stack sibling. flipcard-papers3 (M5Stack PaperS3) draws every piece of card text as a PNG prepared on the host, and names Japanese as a supported content language. On the Cardputer the same pattern would let the Mac pre-render items the built-in fonts cannot show well, such as large kanji, furigana or stroke-order diagrams. No licence file, so it is a pattern to copy, not code. Source: https://raw.githubusercontent.com/micokonsep/flipcard-papers3/main/README.md
- UIFlow2 can draw Japanese on both Cardputer builds, contrary to the researcher's reading, but only with one 24 px font (names AlibabaSansJA24 and EFontJA24, 3,395 kanji in its generation range). That makes a MicroPython prototype possible, with about 5 lines of text per screen. Not tested on hardware. Sources: https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/cmodules/m5unified/m5unified_gfx.c , https://raw.githubusercontent.com/m5stack/uiflow-micropython/master/m5stack/components/M5Unified/fonts/AlibabaSans_JP24.c
- Which variant the owner probably has. On 2026-09-27 the official store titles the original kit '[EOL] M5Stack Cardputer Kit w/ M5StampS3' and marks it out of stock, while the Cardputer ADV is in stock at 29.90 USD. A recently bought unit is therefore more likely an ADV, but this is an inference and the owner should confirm. Sources: https://shop.m5stack.com/products/m5stack-cardputer-kit-w-m5stamps3 , https://shop.m5stack.com/products/m5stack-cardputer-adv-version-esp32-s3
- Wi-Fi caveat for tethering, reported by a project author (community source, not verified by me): the ESP32-S3 is 2.4 GHz only and can hang during authentication against access points in mixed WPA2/WPA3 transition mode; the author's fix was to set the router to WPA2-Personal AES only. Phone hotspots may not offer that setting, which is another reason to design the study features to work fully offline. Source: https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md

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
