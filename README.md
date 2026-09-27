# japan_cardputer

A Japanese-learning travel companion for the M5Stack Cardputer (original, v1.1 and ADV).

The phone translates. This device takes the other job: it catches the Japanese its owner meets and
makes them type it back until it stays. It is generic: nothing in it is tuned to one trip, route or
season.

Status, 27 September 2026: a course of typed cards with sound. Six decks (hiragana, katakana,
numbers, counters, katakana words, signs: 768 cards), taken in that order, with spaced repetition;
what each kanji of a word means; a kana chart; a guide to how Japanese sounds; clips spoken from
the memory card. It runs on a Cardputer ADV and in the simulator, and is checked in both.

## The plan in one table

| Stage | What gets built | Needs |
|---|---|---|
| 0 | Hardware check: board, memory, font sizes, typing, speaker and microphone | the device |
| 1 | Typed cards: a course from kana to signs, in sittings of a few minutes. Done | nothing |
| 2 | Sound: every card spoken, the guide to the sounds. Done. Still to come: numbers by ear, what staff ask, echo | audio clips made on a computer |
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
| `src/files.cpp` | Takes files for the memory card over USB, so that the card can stay in the device |
| `src/sound.cpp` | Plays clips from the memory card, read piece by piece while they play |
| `src/card.cpp` | The memory card |
| `src/hwcheck.cpp` | Hardware check, started by holding G0 while switching on |
| `lib/ui/` | The app: themes, widgets and screens, drawn on any M5GFX canvas |
| `lib/core/` | Decks, marking of answers, spaced repetition, progress, kana and pitch helpers, pure C++ |
| `content/` | What is taught, as plain tables, with the rules they must keep |
| `sim/` | The simulator: the app compiled to WebAssembly, with a screenshot runner |
| `docs/screens/` | Reference pictures of every screen, made by the simulator |
| `lib/romaji/` | Romaji to kana conversion, pure C++, shared by everything that takes typed Japanese |
| `test/` | Unit tests: conversion, marking, spaced repetition, progress, sittings, clip headers |
| `tools/cardputer_screen.py` | Pixel-exact preview of the 240 x 135 screen, drawn with the device's own fonts |
| `tools/concept_screens.py` | The concept screens for every idea, the pronunciation notation and the four looks |
| `tools/romaji_reference.py` | Python mirror of the converter, for content tools and for checking the test vectors |
| `tools/syntax_check.py` | Type check of the firmware without the ESP32 toolchain |
| `tools/wasm_tests.py` | Runs the C++ unit tests as WebAssembly, for machines that cannot start native builds |
| `tools/flash.py` | Downloads the latest cloud build and writes it to the device |
| `tools/build_decks.py` | Checks the tables in `content/` against dictionaries and fonts and compiles them into the firmware |
| `tools/fetch_reference.py` | Fetches the dictionaries and the accent list the checks need |
| `tools/make_audio.py` | Makes the clips for the memory card and measures each one |
| `tools/sd_sync.py` | Makes the memory card in the device hold what a folder holds, over USB |
| `tools/cards_check.py` | Plays the course and sittings over two days, in the simulator or on a device |
| `tools/kana_round_check.py`, `menu_check.py`, `chart_check.py`, `guide_check.py`, `settings_check.py` | Play the other screens the same way, in all four looks |
| `tools/card_folder_check.py` | Checks that everything the app asks of the memory card lies in its one folder |
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

## The course

Nothing is assumed. The course takes its new cards from the first stage that still has some:

| Stage | Decks |
|---|---|
| 1 | Hiragana |
| 2 | Katakana, numbers, counters |
| 3 | Katakana words, signs |

A kana that was never seen is asked first. Typed right at first sight, it counts as known and
comes back after four days; typed wrong or passed with `Tab`, it is taught: the kana large, what
to type, how it sounds. So someone who knows their kana is through the first stage in a few
sittings, and someone who does not is taught them ten at a time.

A word is met on a page of its own before it is asked: how it is read, with the line that shows
where the voice is high, and what each of its kanji means (出口: 出 go out, 口 opening). Where the
characters do not explain the word, the line says what does (交番: 交 alternate, 番 guard), or
the card shows none.

The menu also holds the decks one by one, a kana chart to look a kana up, and a guide of twelve
short pages on how Japanese sounds.

## How a sitting works

A sitting takes what is due first and then new cards: up to ten kana or four words. Answers are
typed in romaji, which turns into kana while typing, and are marked at once: 〇 right, △ nearly
(a long vowel, a small っ, an ん or a voicing mark away), × wrong. What was missed comes back in
the same sitting. Cards that are known come back after one day, then three, eight, twenty and so
on.

The device has no clock. After a day on which cards were answered, the next start asks whether a
new day has begun.

Everything that steers the device is in English, and nothing on the screen is smaller than
16 pixels: the screen measures 1.14 inches, and 12 pixels on it are 1.3 mm. Japanese appears where
it is the thing being learnt, with its meaning beside it.

| Key | What it does |
|---|---|
| `Enter` | answer, next |
| `Tab` | help: first the romaji, then the answer; after a mark, what the card has to say; on the home screen, the menu |
| `/` | hear it again, wherever the answer is in sight |
| `Esc` (`Fn` + `` ` ``) or the button on the edge | back |
| `;` `.` `,` `/` | up, down, left, right in lists, with or without `Fn` |

## Sound and the memory card

The clips are WAV files on the microSD card, one per card and voice, 16 bit, one channel, 16,000
samples a second: about 900 clips and 20 MB a voice. A clip plays when the answer of a card
appears, never while the question is open. Without a card, or with sound switched off in the
settings, everything else works as before.

Everything the app keeps on the card lies in one folder, `/nihongo`, so the card can hold other
things. It must be formatted as FAT32.

The clips are made on a computer and are not part of the repository, because the voices that
speak them have licences of their own:

```
python3 tools/make_audio.py --out card/nihongo/audio --voice f    # macOS: the voice Kyoko
python3 tools/make_audio.py --out card/nihongo/audio --voice m    # macOS: the voice Otoya
python3 tools/sd_sync.py card                                     # card/nihongo/... becomes /nihongo/... on the card
```

`make_audio.py` measures every clip it makes: its length against the beats of the reading, where
the voice drops against the accent the deck gives, silence, level. What it doubts is marked in
`index.tsv` beside the clips. `sd_sync.py` sends over the USB cable what the card does not have
or has differently, checks every file after sending, and can be stopped and started again. The
card stays in the device.

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

The tables in `content/` were written for this project. Readings and meanings were checked
against JMdict, the meanings of single kanji against KANJIDIC (both: Electronic Dictionary Research
and Development Group, CC BY-SA 4.0), and the pitch accents come from the accent list of the
Kanjium project (CC BY-SA 4.0); the tables are therefore shared under CC BY-SA 4.0. The
dictionaries and the accent list themselves are not in the repository: `tools/fetch_reference.py`
fetches them into `local/cache/`.

Sources planned for later stages carry their own terms, recorded in `docs/research/data.md`:
Tatoeba sentences (CC BY 2.0 FR) and KanjiVG stroke data (CC BY-SA 3.0). The fonts come with M5GFX: efont is BSD 3-clause, the gothic and
mincho families fall under the IPA Font License.
