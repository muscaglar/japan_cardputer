---
name: verify
description: How to verify changes in this repository by running them - the firmware on a Cardputer, the Python tools in a terminal, and the concept page in a browser.
---

# Verifying cardputer-nihongo

Three surfaces. Drive the one the change reaches.

## 1. Firmware (src/, lib/) - the device

Needs a Cardputer on USB and a machine that can run the ESP32 toolchain.

```
pio run -e cardputer -t upload      # download mode if needed: switch off, hold G0, plug in USB
pio device monitor                  # 115200 baud
```

Observe:

- Serial prints one JSON line at boot: `{"probe":"cardputer-nihongo","board":...,"psramBytes":...}`.
  `board` must be `Cardputer` or `Cardputer ADV`, never `unknown board`.
- `Fn` + `/` walks the pages INFO, FONTS, TYPING, AUDIO; `Fn` + `,` goes back; G0 also advances.
- TYPING: `konnichiha` shows こんにちは, `kitte` shows きって, `ra-men` shows らーめん, Tab switches to katakana.
  Roll two keys quickly: no letter may appear twice.
- FONTS: `,` and `.` change size; the third sample line (餃子 鮪 ...) shows red boxes only in the gothic font.
- AUDIO: `B` beeps; `R` records 3 s and plays it back, and the loudest-sample figure is above 0.
  A figure of 0 means a silent microphone, a known problem on the ADV with some toolchains.

Status on 2026-09-27: this recipe has NOT been exercised yet. No device was connected and the
toolchain could not run on the machine used.

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
an overflow seen there will be on the device too.

`syntax_check.py` must report `FAIL` with file and line when `src/main.cpp` contains a mistake.
To prove it still does, append a bad line, run it, and restore the file.

Gotchas:

- `tools/cardputer_screen.py` needs the M5GFX sources in `.pio/libdeps` (`pio pkg install -e cardputer`).
  The first run parses about 50 MB of font source and caches it in `.pio/fontcache`.
- `syntax_check.py` prints nothing about Xtensa inline assembly on purpose; those errors come from
  parsing ESP-IDF headers with an ARM target and are filtered.

## 3. Concept page (docs/board/) - the browser

```
cd docs/board && python3 -m http.server 8765 --bind 127.0.0.1
```

The built file has no `<html>` wrapper because the publisher adds one, so open it through a small
wrapper page or the published link. Drive it: the status bar starts at `ideas 18/18`, choosing
options changes the text in "Your answers, ready to paste", a reload keeps the choices, Reset
returns to the prefilled picks, and Copy shows "Copied".
