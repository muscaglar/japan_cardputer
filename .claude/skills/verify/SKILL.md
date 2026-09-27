---
name: verify
description: How to verify changes in this repository by running them - the firmware on a Cardputer, the Python tools in a terminal, and the concept page in a browser.
---

# Verifying cardputer-nihongo

Five surfaces. Drive the one the change reaches.

## 1. Firmware (src/, lib/) - the device

Two routes to get a build onto a Cardputer on USB.

Where the ESP32 compiler runs:

```
pio run -e cardputer -t upload      # download mode if needed: switch off, hold G0, plug in USB
```

Where it does not (the cloud builds every push to main and publishes it as release `latest`):

```
python3 tools/flash.py              # downloads the latest cloud build and writes it
```

Then, with PlatformIO's own Python, which has pyserial (`pio system info`, "Python Executable"):

```
PY=<that python>
$PY tools/serial_report.py                  # restarts the device, prints its report
$PY tools/device_driver.py shot.png         # state of the app, and what is on its screen
$PY tools/kana_round_check.py --device      # plays whole rounds on the device, reads its screen
$PY tools/sd_sync.py card                   # card/nihongo/... becomes /nihongo/... on the memory card
```

Every check of section 3 takes `--device` and plays the same on the device.

Sound and the memory card, over USB: `df`, `ls <folder>`, `crc <path>`, `play <path> [1-5]`,
`hush`. After `play`, `info` tells what the device did: `soundStarted`, `soundRefused`,
`soundGaps` (the speaker ran dry in the middle of a clip: must stay 0), `soundLongestTick` (ms
the card held the device up: about 10). That a clip was played is not yet that it was heard: ask
the person at the device.

The app answers on USB (`src/console.h`): `key`, `type`, `fn`, `frame`, `info`. The picture that
comes back is the buffer sent to the panel, so it shows what the app drew, not what the glass
shows. Keys arrive at the app, not at the keyboard chip. Keyboard, panel, speaker and microphone
still need a person: that is what the hardware check is for.

Observe at start: one JSON line on serial. App: `{"app":"japan_cardputer","board":...}`.
Hardware check (hold G0 while switching on): `{"probe":"cardputer-nihongo","board":...}`.
`board` must be `Cardputer` or `Cardputer ADV`, never `unknown board`.

Hardware check, by a person:

- `Fn` + `/` walks the pages INFO, FONTS, TYPING, AUDIO; `Fn` + `,` goes back; G0 also advances.
- TYPING: `konnichiha` shows こんにちは, `kitte` shows きって, `ra-men` shows らーめん, Tab switches to katakana.
  Roll two keys quickly: no letter may appear twice.
- FONTS: `,` and `.` change size; the third sample line (餃子 鮪 ...) shows red boxes only in the gothic font.
- AUDIO: `B` beeps; `R` records 3 s and plays it back, and the loudest-sample figure is above 0.
  A figure of 0 means a silent microphone, a known problem on the ADV with some toolchains.

Before the first flash of a device, keep its factory firmware:
`pio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32s3 --port PORT read_flash 0x0 0x800000 local/backup/factory.bin`
(about two minutes; `local/` is not tracked).

`$PY tools/console_check.py` asks two hundred times and counts late answers; expect none.

Exercised on 2026-09-27 on a Cardputer ADV: flash, report (`Cardputer ADV`, no PSRAM, 267 KB
free, 122 GB card mounted), console check (200 of 200 prompt), `cards_check.py --device` (567
checks, under two minutes) and `kana_round_check.py --device` (52 checks). The lowest free memory
ever seen was 283 KB. The pages of the hardware check were not yet confirmed by a person.

Exercised again the same day with sound: 24 clips sent over USB and verified (75 KB a second), a
second run sent nothing, six clips played without a gap and were heard by the owner, a file that
is not a clip and a path with `..` were refused. 229 KB stayed free while playing.

What only a person at the device can judge: whether text is large enough to read. On
27 September 2026 the owner found 12 px text too small on the device and controls in kana too
hard; since then nothing is under 16 px and everything that steers is in English. A screen that
looks fine enlarged on a monitor says nothing about that.

Gotchas:

- Open the port with both control lines high (`dtr = rts = True`): lowering them restarts the chip,
  and a pulse on DTR alone leaves it in download mode until `esptool.py ... chip_id` resets it.
- Do not call `reset_input_buffer()`; read what is left instead.
- In zsh a pattern without a match aborts the whole command: `ls /dev/cu.usbmodem* /dev/cu.usbserial*`
  prints nothing useful when one of them is absent. Use `ls /dev | grep usbmodem`.
- `pio pkg exec` has no `python` on its path; call PlatformIO's Python by its full path.
- One program at a time may talk to the device. A check started while `sd_sync.py` runs breaks both.
- `sd_sync.py` refuses links: the folder it is given must hold real files.
- A card may hold more than the device shows. The owner's card carried the system of another
  computer; the device saw only its first partition (510 MB of 122 GB). Read `df` and `ls /`
  before writing, write only under `/nihongo`, and remove nothing you did not put there.
- With the card taken out while the device runs, `df` answers `0 0` and `ls /` says `not there`.
  The card is found again at the next start.

## 2. Tools (tools/, docs/board/) - the terminal

All run with the system Python and need no compiler.

```
python3 tools/romaji_reference.py konnichiha shimbashi "kin'en"   # conversion as the device does it
python3 tools/cardputer_screen.py /tmp/fonts                      # font sample screens as PNG
python3 tools/concept_screens.py                                  # writes docs/concepts, exit 1 if text overflows
pio run -e cardputer -t compiledb && python3 tools/syntax_check.py
python3 docs/board/build_board.py                                 # writes docs/board/cardputer-nihongo.html
```

Open a rendered PNG and look at it. The renderer decodes the real device fonts, so a wrong glyph or
an overflow seen there will be on the device too. It was compared with M5GFX itself, compiled to
WebAssembly, on 2026-09-27: all 32,400 pixels of a test screen were identical.

C++ that cannot be started as a native program can still be executed as WebAssembly under Node:

```
python3 tools/wasm_tests.py            # the unit tests under test/, compiled with Emscripten
```

Emscripten from Homebrew needs `EMSDK_PYTHON` pointing at a Python of 3.10 or later (the script sets
it) and a `.emscripten` file in its `libexec` folder naming its own `llvm/bin` and `binaryen`.

`syntax_check.py` must report `FAIL` with file and line when `src/main.cpp` contains a mistake.
To prove it still does, append a bad line, run it, and restore the file.

Gotchas:

- `tools/cardputer_screen.py` needs the M5GFX sources in `.pio/libdeps` (`pio pkg install -e cardputer`).
  The first run parses about 50 MB of font source and caches it in `.pio/fontcache`.
- `syntax_check.py` prints nothing about Xtensa inline assembly on purpose; those errors come from
  parsing ESP-IDF headers with an ARM target and are filtered.

## 3. The app in the simulator (lib/ui, lib/core, sim/) - Node and the browser

The real app code with the real graphics library, compiled with Emscripten.

```
python3 sim/build.py --page
node sim/shots.js --check          # every scenario against docs/screens; prints CHANGED with a path
```

`python3 tools/cards_check.py` plays the course from a fresh start and sittings over two days in
all four looks: kana asked before they are taught, new words with what their kanji mean,
questions, the four marks, the summary, a restart, the question for the new day, what is due on
day 2, and what was played when. It asks the app which card it shows (`info`) and reads the
picture to see that card and mark are drawn. On a device it keeps the owner's progress aside and
puts it back.

One check per screen, all built the same way: `menu_check.py` (home, menu, decks),
`chart_check.py`, `guide_check.py`, `settings_check.py` (with the kana quiz), and
`card_folder_check.py`, which looks at the whole path of every clip the app asks for. The
simulator has no sound: it pretends a memory card that holds every clip and remembers what the
app asked for (`played`, `plays`, `playedAt` in `info`).

`python3 tools/kana_round_check.py` plays whole kana rounds in all four looks. It reads each kana off
the screen, answers some right and some wrong on purpose, and checks the marks and the final score.
Use `tools/sim_driver.py` the same way for any check that has to react to what is on the screen.

After a change to flows or decks, `python3 sim/make_scenarios.py` finds the key sequences anew by
playing the app. The page for the browser runs another build (plain JavaScript); check it against
the same pictures with `SIM_JS=build/sim/sim_plain.js node sim/shots.js --check`.

A CHANGED screen is not a failure by itself: open the new picture, and if it is what was intended,
run `node sim/shots.js` to accept it. Add a scenario to `sim/scenarios.json` for every new screen.

For typing feel and flows, serve the built page and drive it with real key presses:

```
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs/sim
```

The line under the screen names the current screen.

Gotchas:

- Build output lives in `build/`, not `.pio/build/`: PlatformIO empties its folder whenever
  `platformio.ini` changes.
- The browser page is plain JavaScript (`-sWASM=0`). In that build M5GFX `readPixelRGB` lost the
  green channel, so `sim/main.cpp` reads the sprite buffer itself. Do not go back to `readPixelRGB`.

## 4. Content (content/, tools/build_decks.py) - the terminal

```
python3 tools/fetch_reference.py        # once: dictionaries and accent list into local/cache
python3 tools/build_decks.py --check    # every row against format, fonts, typing and dictionaries
python3 tools/build_decks.py            # and writes lib/core/deck_data.cpp and content/ids.txt
python3 tools/tests/test_build_decks.py # one fixture per kind of mistake
python3 tools/make_audio.py --check --out card/nihongo/audio   # measures the clips that are there
```

Two people writing tables for the same tool can agree on everything but one word: a table said
`EMPTY` where the tool expected an empty field, and six cards would have shown the word. Read
the compiled `lib/core/deck_data.cpp` after a change to a table or the tool, not only the count
of errors.

After a change to a table, build the simulator again and play the cards: a deck that checks clean
can still be dull or wrong in ways only a reader sees.

## 5. Concept page (docs/board/) - the browser

```
cd docs/board && python3 -m http.server 8765 --bind 127.0.0.1
```

The built file has no `<html>` wrapper because the publisher adds one, so open it through a small
wrapper page or the published link. Drive it: the status bar starts at `ideas 18/18`, choosing
options changes the text in "Your answers, ready to paste", a reload keeps the choices, Reset
returns to the prefilled picks, and Copy shows "Copied".
