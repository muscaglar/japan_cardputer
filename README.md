# japan_cardputer

A Japanese-learning travel companion for the M5Stack Cardputer (original, v1.1 and ADV).

The phone translates. This device takes the other job: it catches the Japanese its owner meets and
makes them type it back until it stays. It is generic: nothing in it is tuned to one trip, route or
season.

Status, 27 September 2026: typed cards work. Four decks (signs, katakana words, counters, numbers,
about 560 cards), sittings with spaced repetition, a kana round, four looks. The hardware check has
run on a Cardputer ADV; the app runs in the simulator and is checked there end to end.

## The plan in one table

| Stage | What gets built | Needs |
|---|---|---|
| 0 | Hardware check: board, memory, font sizes, typing, speaker and microphone | the device |
| 1 | Typed cards: sittings of a few minutes, signs, katakana words, counters, numbers, kana | nothing |
| 2 | Sound: numbers by ear, what staff ask, the pronunciation line, echo | audio clips made on a computer |
| 3 | Your own words: word catcher with offline dictionary, day packs, station names, missions, show cards, the buddy | an itinerary, optional |
| 4 | Evening, online: three-line diary and rehearsal with Claude, a pronunciation check through a speech-scoring service, sound snapshot | phone hotspot |
| 5 | Extras: menu decoder, room remote | |

Pronunciation comes in three layers: a written line on every card (beats, pitch, whispered vowels,
optional romaji), audio clips prepared on a computer, and record-and-compare with the microphone.

## What is in the repository

| Path | Contents |
|---|---|
| `src/main.cpp` | Device shell: keyboard, screen, storage and sound for the app |
| `src/console.cpp` | Lets a computer on USB press keys and read the screen, for checks on a real device |
| `src/hwcheck.cpp` | Hardware check, started by holding G0 while switching on |
| `lib/ui/` | The app: themes, widgets and screens, drawn on any M5GFX canvas |
| `lib/core/` | Decks, marking of answers, spaced repetition, progress, kana and pitch helpers, pure C++ |
| `content/` | What is taught, as plain tables, with the rules they must keep |
| `sim/` | The simulator: the app compiled to WebAssembly, with a screenshot runner |
| `docs/screens/` | Reference pictures of every screen, made by the simulator |
| `lib/romaji/` | Romaji to kana conversion, pure C++, shared by everything that takes typed Japanese |
| `test/test_romaji/` | Unit tests for the conversion rules |
| `tools/cardputer_screen.py` | Pixel-exact preview of the 240 x 135 screen, drawn with the device's own fonts |
| `tools/concept_screens.py` | The concept screens for every idea, the pronunciation notation and the four looks |
| `tools/romaji_reference.py` | Python mirror of the converter, for content tools and for checking the test vectors |
| `tools/syntax_check.py` | Type check of the firmware without the ESP32 toolchain |
| `tools/wasm_tests.py` | Runs the C++ unit tests as WebAssembly, for machines that cannot start native builds |
| `tools/flash.py` | Downloads the latest cloud build and writes it to the device |
| `tools/build_decks.py` | Checks the deck tables against dictionary and fonts and compiles them into the firmware |
| `tools/cards_check.py` | Plays sittings over two days, in the simulator or on a device, and checks the result |
| `tools/kana_round_check.py` | Plays whole kana rounds the same way |
| `tools/device_driver.py` | Presses keys and reads the screen of a device over USB |
| `tools/serial_report.py` | Restarts a device and prints its report |
| `tools/wait_for_build.py` | Waits until the cloud has built a commit |
| `docs/concepts/` | Rendered concept screens (PNG, three times device size) |
| `docs/board/` | The concept board page and its generator |
| `docs/research/` | Research notes with sources, each statement fact-checked |

## Hardware check

Hold the G0 button while switching the device on.

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

## How a sitting works

A sitting takes what is due first and then up to four new cards. A new card shows its answer and
asks the learner to type it, after a page with its note where it has one; a little later it comes
back as a question. Answers are typed in romaji, which turns into kana while typing, and are
marked at once: 〇 right, △ nearly (a long vowel, a small っ, an ん or a voicing mark away),
× wrong. What was missed comes back in the same sitting. Cards that are known come back after one
day, then three, eight, twenty and so on.

The device has no clock. After a day on which cards were answered, the next start asks whether a
new day has begun.

Everything that steers the device is in English, and nothing on the screen is smaller than
16 pixels: the screen measures 1.14 inches, and 12 pixels on it are 1.3 mm. Japanese appears where
it is the thing being learnt, with its meaning beside it.

| Key | What it does |
|---|---|
| `Enter` | answer, next |
| `Tab` | help: first the romaji, then the answer; after a mark, the note; on the home screen, the menu |
| `Esc` (`Fn` + `` ` ``) or the button on the edge | back |
| `;` `.` `,` `/` | up, down, left, right in lists, with or without `Fn` |

## The simulator

The app is written against a small `Platform` interface, so the same code runs on the device and,
compiled with Emscripten, in a browser or under Node. The pixels are drawn by M5GFX itself with the
device's fonts.

```
python3 sim/build.py --page      # build/sim/sim.js for Node, docs/sim/cardputer-simulator.html for a browser
node sim/shots.js                # plays the key sequences in sim/scenarios.json, writes docs/screens/*.png
node sim/shots.js --check        # the same, compared with docs/screens
```

Open `docs/sim/cardputer-simulator.html` in a browser and type. Arrow keys are the arrows printed on
`;` `,` `.` `/`, Option or Alt is `Fn`, Esc goes back.

## Working without a device or a compiler

```
python3 tools/concept_screens.py                 # renders every concept screen into docs/concepts
python3 tools/romaji_reference.py konnichiha shimbashi "ko-hi- wo kudasai"
pio run -e cardputer -t compiledb                # writes compile_commands.json, runs no compiler
python3 tools/syntax_check.py                    # type-checks src/ and lib/ with the system clang
python3 tools/wasm_tests.py                      # runs the C++ unit tests as WebAssembly under Node
python3 docs/board/build_board.py                # rebuilds the concept board page
```

The screen preview decodes the same u8g2 font data the firmware links, with the same algorithm, so
what it draws is what the panel shows. It needs the M5GFX sources that PlatformIO downloads
(`pio pkg install -e cardputer`).

The C++ unit tests run with `pio test -e native`, or as WebAssembly with `tools/wasm_tests.py`.

The preview was checked against M5GFX itself, compiled to WebAssembly: a test screen came out
identical in all 32,400 pixels.

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

The decks in `content/` were written for this project. Their readings and meanings were checked
against JMdict (Electronic Dictionary Research and Development Group, CC BY-SA 4.0) and their pitch
accents come from the accent list of the Kanjium project (CC BY-SA 4.0); the decks are therefore
shared under CC BY-SA 4.0. The dictionary and the accent list themselves are not in the repository:
`tools/build_decks.py` reads them from `local/cache/`.

Sources planned for later stages carry their own terms, recorded in `docs/research/data.md`:
Tatoeba sentences (CC BY 2.0 FR) and KanjiVG stroke data (CC BY-SA 3.0). The fonts come with M5GFX: efont is BSD 3-clause, the gothic and
mincho families fall under the IPA Font License.
