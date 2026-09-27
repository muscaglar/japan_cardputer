# japan_cardputer

A Japanese-learning travel companion for the M5Stack Cardputer (original, v1.1 and ADV).

The phone translates. This device takes the other job: it catches the Japanese met on a trip and
makes its owner type it back until it stays.

Status, 27 September 2026: design stage. The firmware in `src/` is a hardware check, not the app.
It has been type-checked against the real headers but has not yet been built or run on a device.

## The plan in one table

| Stage | What gets built | Needs |
|---|---|---|
| 0 | Hardware check: board, memory, font sizes, typing, speaker and microphone | the device |
| 1 | Typed cards: the 90-second queue, signs, katakana sprint, counters | microSD card |
| 2 | Sound: numbers by ear, what staff ask, the pronunciation line, echo | audio clips made on a computer |
| 3 | Your own words: word catcher with offline dictionary, daily packs, station names, missions, show cards, the buddy | itinerary |
| 4 | Evening, online: three-line diary, rehearsal and pronunciation check through Claude, sound snapshot | phone hotspot |
| 5 | Extras: menu decoder, room remote | |

Pronunciation comes in three layers: a written line on every card (beats, pitch, whispered vowels,
optional romaji), audio clips prepared before the trip, and record-and-compare with the microphone.

## What is in the repository

| Path | Contents |
|---|---|
| `src/main.cpp` | Hardware check firmware |
| `lib/romaji/` | Romaji to kana conversion, pure C++, shared by everything that takes typed Japanese |
| `test/test_romaji/` | Unit tests for the conversion rules |
| `tools/cardputer_screen.py` | Pixel-exact preview of the 240 x 135 screen, drawn with the device's own fonts |
| `tools/concept_screens.py` | The concept screens for every idea, the pronunciation notation and the four looks |
| `tools/romaji_reference.py` | Python mirror of the converter, for content tools and for checking the test vectors |
| `tools/syntax_check.py` | Type check of the firmware without the ESP32 toolchain |
| `docs/concepts/` | Rendered concept screens (PNG, three times device size) |
| `docs/board/` | The concept board page and its generator |
| `docs/research/` | Research notes with sources, each statement fact-checked |

## Hardware check

| Page | What it tells us |
|---|---|
| 1 INFO | Board (Cardputer or Cardputer ADV), flash, PSRAM, free heap, battery, SD card |
| 2 FONTS | The same Japanese sample text at 12, 16, 20 and 24 px, to choose a reading size |
| 3 TYPING | Romaji typed on the keyboard turns into kana as you type |
| 4 AUDIO | Speaker beep, then a 3 second microphone recording played back |

Keys: `Fn` + `/` next page, `Fn` + `,` previous page, the G0 button also moves to the next page.
On the typing page `Tab` switches hiragana and katakana, `Fn` + `N` switches how `nn` is read.

At boot the device prints one JSON line on the USB serial port with the same facts as page 1.

```
pio run -e cardputer -t upload
pio device monitor
```

To enter download mode if the upload cannot connect: switch the device off, hold G0, plug in USB.

## Working without a device or a compiler

```
python3 tools/concept_screens.py                 # renders every concept screen into docs/concepts
python3 tools/romaji_reference.py konnichiha shimbashi "ko-hi- wo kudasai"
pio run -e cardputer -t compiledb                # writes compile_commands.json, runs no compiler
python3 tools/syntax_check.py                    # type-checks src/ and lib/ with the system clang
python3 docs/board/build_board.py                # rebuilds the concept board page
```

The screen preview decodes the same u8g2 font data the firmware links, with the same algorithm, so
what it draws is what the panel shows. It needs the M5GFX sources that PlatformIO downloads
(`pio pkg install -e cardputer`).

The C++ unit tests run with `pio test -e native` on a machine that can run locally built programs.

## Fonts

Measured from M5GFX 0.2.30:

| Font | Flash | Kanji | Note |
|---|---|---|---|
| `efontJA_12` | 301 KB | 9,500 | full JIS level 1 and 2 |
| `efontJA_16` | 456 KB | 9,500 | full JIS level 1 and 2 |
| `efontJA_24` | 726 KB | 8,784 | full JIS level 1 and 2 |
| `lgfxJapanGothic_16` | 155 KB | 3,487 | lacks menu kanji such as 餃 鮪 炙 鰤 |

The efont family is used for anything that shows dictionary or menu text.

## Data and licences

No dictionary or audio data is in the repository yet. The sources planned for the content build
carry their own terms, recorded in `docs/research/data.md`: the EDRDG dictionary files (CC BY-SA 4.0,
with an acknowledgement screen and regular updates required), Tatoeba sentences (CC BY 2.0 FR) and
KanjiVG stroke data (CC BY-SA 3.0). The fonts come with M5GFX: efont is BSD 3-clause, the gothic and
mincho families fall under the IPA Font License.
