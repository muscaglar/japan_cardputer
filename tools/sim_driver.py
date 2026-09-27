#!/usr/bin/env python3
"""Plays the app in the simulator from Python and reads the screen back.

Used for checks that need to react to what is on the screen, for example answering a kana round.
The kana on screen is recognised by comparing its pixels with the same glyph drawn by
tools/cardputer_screen.py, which is pixel-exact.

    python3 tools/sim_driver.py            # plays kana rounds in all four looks and reports

Needs the simulator built for Node: python3 sim/build.py
"""
import base64
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardputer_screen import HEIGHT, WIDTH, font  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENS = ["home", "menu", "kana", "settings"]


class Simulator:
    def __init__(self, seed=1):
        self.process = subprocess.Popen(["node", os.path.join(ROOT, "sim", "drive.js")], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, text=True, bufsize=1)
        self.send("init %d" % seed)

    def send(self, line):
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def key(self, name):
        self.send("key " + name)

    def type(self, text):
        self.send("type " + text)

    def fn(self, character):
        self.send("fn " + character)

    def frame(self):
        """Returns (screen name, rows of (r, g, b))."""
        self.send("frame")
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("the simulator stopped")
            if line.startswith("error"):
                raise RuntimeError(line.strip())
            if line.startswith("frame "):
                break
        _, screen, data = line.split(" ", 2)
        raw = base64.b64decode(data)
        rows = [[tuple(raw[(y * WIDTH + x) * 4:(y * WIDTH + x) * 4 + 3]) for x in range(WIDTH)] for y in range(HEIGHT)]
        index = int(screen)
        return (SCREENS[index] if 0 <= index < len(SCREENS) else str(index)), rows

    def close(self):
        try:
            self.send("quit")
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()


def ink_mask(rows, x0, y0, x1, y1, background):
    """Set of (x, y) inside the box whose colour differs from the background."""
    return {(x - x0, y - y0) for y in range(y0, y1) for x in range(x0, x1) if rows[y][x] != background}


def glyph_mask(text, font_name):
    """The pixels of `text` drawn from the top-left corner, as the firmware draws it."""
    f = font(font_name)
    points = set()
    x = 0
    for character in text:
        g = f.glyph(ord(character))
        if g is None:
            return None, 0
        w, h, gx, gy, advance, bitmap = g
        top = f.baseline - gy - h
        for row_index, row in enumerate(bitmap):
            for column_index, ink in enumerate(row):
                if ink:
                    points.add((x + gx + column_index, top + row_index))
        x += advance
    return points, x


def count_colour(rows, predicate, y0=0, y1=HEIGHT):
    return sum(1 for y in range(y0, y1) for x in range(WIDTH) if predicate(rows[y][x]))


if __name__ == "__main__":
    import kana_round_check
    sys.exit(kana_round_check.main())
