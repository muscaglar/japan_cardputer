#!/usr/bin/env python3
"""Plays whole kana rounds in the simulator, reading each kana off the screen.

For every look: answers some questions correctly and some wrongly on purpose, and checks that the
app marks them accordingly and that the score at the end is the number answered correctly.
Also pushes on the edges: Enter on an empty line, a long line, Backspace on nothing, leaving and
coming back in the middle of a round.

    python3 tools/kana_round_check.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardputer_screen import WIDTH, font, rgb565  # noqa: E402
from sim_driver import Simulator, glyph_mask  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIG = "lgfxJapanGothic_32"

# where each look starts its content, as in lib/ui/theme.cpp
AREAS = {"techo": (28, 16, 208, 102), "eki": (6, 24, 228, 92), "rpg": (12, 14, 216, 74), "washi": (14, 20, 220, 94)}
LOOKS = ["techo", "eki", "rpg", "washi"]
# main text colour of each look, as in lib/ui/theme.cpp, rounded as the 16-bit panel rounds it
INK = {"techo": rgb565((0x18, 0x18, 0x1C)), "eki": rgb565((255, 255, 255)), "rpg": rgb565((255, 255, 255)),
       "washi": rgb565((0x18, 0x18, 0x1C))}


def kana_table():
    """kana -> romaji, read from the screen's own list and the converter's table."""
    source = open(os.path.join(ROOT, "lib", "ui", "screens", "kana.cpp"), encoding="utf-8").read()
    listed = re.findall(r'"([ぁ-ゖ]{1,2})"', source)
    table_source = open(os.path.join(ROOT, "lib", "romaji", "romaji.cpp"), encoding="utf-8").read()
    pairs = re.findall(r'\{"([a-z]+)",\s*"([^"]+)"\}', table_source)
    romaji = {}
    for roma, kana in pairs:
        romaji.setdefault(kana, roma)
    romaji["ん"] = "nn"
    return {k: romaji[k] for k in dict.fromkeys(listed) if k in romaji}


def to_katakana(text):
    return "".join(chr(ord(c) + 0x60) if 0x3041 <= ord(c) <= 0x3096 else c for c in text)


def recognise(rows, look, candidates):
    """Which kana is drawn large in the middle of the content area."""
    ax, ay, aw, _ = AREAS[look]
    top = ay + (0 if look == "rpg" else 4)
    height = font(BIG).height
    # Only pixels in the text colour count: the notebook look has ruled lines behind the kana.
    seen = {(x, y - top) for y in range(top, top + height) for x in range(ax, ax + aw)
            if rows[y][x] == INK[look]}
    for kana in candidates:
        mask, width = glyph_mask(kana, BIG)
        if mask is None:
            continue
        left = ax + aw // 2 - width // 2
        if {(x + left, y) for (x, y) in mask} == seen:
            return kana
    return None


def is_green(c):
    return c[1] > c[0] + 40 and c[1] > c[2] + 20


def is_red(c):
    return c[0] > c[1] + 60 and c[0] > c[2] + 60


def result_of(rows, look):
    ax, ay, aw, _ = AREAS[look]
    top = ay + (0 if look == "rpg" else 4) + 38
    green = sum(1 for y in range(top, top + 16) for x in range(ax, ax + aw) if is_green(rows[y][x]))
    red = sum(1 for y in range(top, top + 16) for x in range(ax, ax + aw) if is_red(rows[y][x]))
    if green > 20 and green > red:
        return "right"
    if red > 20 and red > green:
        return "wrong"
    return "none"


def choose_look(sim, index):
    sim.key("Tab")      # menu
    sim.key("Down")
    sim.key("Enter")    # settings, first row is the look
    for _ in range(index):
        sim.key("Right")
    sim.key("Esc")
    sim.key("Esc")
    screen, _ = sim.frame()
    return screen


def main():
    table = kana_table()
    hiragana = list(table)
    problems = []
    notes = []

    def expect(condition, message):
        (notes if condition else problems).append(("ok   " if condition else "FAIL ") + message)

    expect(len(table) >= 100, "kana known to the check: %d" % len(table))

    for index, look in enumerate(LOOKS):
        sim = Simulator(seed=100 + index)
        try:
            screen = choose_look(sim, index)
            expect(screen == "home", "%s: back on the home screen after choosing the look" % look)
            sim.type("x")
            screen, rows = sim.frame()
            expect(screen == "kana", "%s: a key on the home screen starts the round" % look)

            right = 0
            unread = 0
            katakana = (index % 2 == 1)
            if katakana:
                sim.key("Tab")
            for question in range(20):
                screen, rows = sim.frame()
                candidates = [to_katakana(k) for k in hiragana] if katakana else hiragana
                shown = recognise(rows, look, candidates)
                if shown is None:
                    unread += 1
                    sim.type("zz")
                    sim.key("Enter")
                    sim.key("Enter")
                    continue
                kana = hiragana[candidates.index(shown)]
                answer_wrong = (question % 4 == 3)
                if question == 5:
                    # pushes: Enter on nothing, Backspace on nothing, too many letters, then the answer
                    sim.key("Enter")
                    sim.key("Backspace")
                    sim.type("qqqqqqqqqqqqqqqq")
                    for _ in range(20):
                        sim.key("Backspace")
                    _, probe = sim.frame()
                    expect(result_of(probe, look) == "none", "%s: nothing is marked before an answer is given" % look)
                sim.type("zu" if answer_wrong and kana != "ず" else ("a" if answer_wrong else table[kana]))
                sim.key("Enter")
                _, rows = sim.frame()
                got = result_of(rows, look)
                want = "wrong" if answer_wrong else "right"
                if got != want:
                    problems.append("FAIL %s: %s answered with %s was marked %s, expected %s" % (
                        look, shown, "a wrong reading" if answer_wrong else table[kana], got, want))
                if not answer_wrong:
                    right += 1
                sim.type(" ")   # any key moves on
            expect(unread == 0, "%s: every kana on screen was recognised (%d not)" % (look, unread))

            screen, rows = sim.frame()
            ax, ay, aw, _ = AREAS[look]
            score_mask, score_width = glyph_mask("%d / 20" % right, "efontJA_24")
            left = ax + aw // 2 - score_width // 2
            top = ay + 28
            seen = {(x, y - top) for y in range(top, top + 24) for x in range(ax, ax + aw) if is_green(rows[y][x])}
            expect({(x + left, y) for (x, y) in score_mask} == seen,
                   "%s: the final screen shows %d / 20" % (look, right))

            sim.key("Enter")
            screen, _ = sim.frame()
            expect(screen == "kana", "%s: Enter on the final screen starts another round" % look)
            sim.type("k")
            sim.key("Esc")
            screen, _ = sim.frame()
            expect(screen == "home", "%s: Esc in the middle of a round goes home" % look)
            sim.type("k")
            screen, rows = sim.frame()
            expect(screen == "kana" and result_of(rows, look) == "none", "%s: coming back starts a clean round" % look)
        finally:
            sim.close()

    for line in notes:
        print(line)
    for line in problems:
        print(line)
    print("%d checks passed, %d failed" % (len(notes), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
