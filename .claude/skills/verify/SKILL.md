---
name: verify
description: How to verify changes in this repository by running them - the firmware on a Cardputer, the Python tools in a terminal, and the concept page in a browser.
---

# Verifying cardputer-nihongo

Four surfaces. Drive the one the change reaches.

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
```

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

Exercised on 2026-09-27 on a Cardputer ADV: flash, report (`Cardputer ADV`, no PSRAM, 267 KB
free, 122 GB card mounted). The pages of the hardware check were not yet confirmed by a person.

Gotchas:

- In zsh a pattern without a match aborts the whole command: `ls /dev/cu.usbmodem* /dev/cu.usbserial*`
  prints nothing useful when one of them is absent. Use `ls /dev | grep usbmodem`.
- `pio pkg exec` has no `python` on its path; call PlatformIO's Python by its full path.

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

`python3 tools/kana_round_check.py` plays whole kana rounds in all four looks. It reads each kana off
the screen, answers some right and some wrong on purpose, and checks the marks and the final score.
Use `tools/sim_driver.py` the same way for any check that has to react to what is on the screen.

A CHANGED screen is not a failure by itself: open the new picture, and if it is what was intended,
run `node sim/shots.js` to accept it. Add a scenario to `sim/scenarios.json` for every new screen.

For typing feel and flows, serve the built page and drive it with real key presses:

```
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs/sim
```

The line under the screen names the current screen (home, menu, kana round, settings).

Gotchas:

- Build output lives in `build/`, not `.pio/build/`: PlatformIO empties its folder whenever
  `platformio.ini` changes.
- The browser page is plain JavaScript (`-sWASM=0`). In that build M5GFX `readPixelRGB` lost the
  green channel, so `sim/main.cpp` reads the sprite buffer itself. Do not go back to `readPixelRGB`.

## 4. Concept page (docs/board/) - the browser

```
cd docs/board && python3 -m http.server 8765 --bind 127.0.0.1
```

The built file has no `<html>` wrapper because the publisher adds one, so open it through a small
wrapper page or the published link. Drive it: the status bar starts at `ideas 18/18`, choosing
options changes the text in "Your answers, ready to paste", a reload keeps the choices, Reset
returns to the prefilled picks, and Copy shows "Copied".
