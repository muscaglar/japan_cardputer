#!/usr/bin/env python3
"""Plays whole kana rounds, reading each kana off the screen.

For every look: answers some questions correctly and some wrongly on purpose, and checks that the
app marks them accordingly and that the score at the end is the number answered correctly.
Also pushes on the edges: Enter on an empty line, a long line, Backspace on nothing, leaving and
coming back in the middle of a round.

    python3 tools/kana_round_check.py                  # in the simulator
    <PlatformIO's python> tools/kana_round_check.py --device [PORT]   # on a Cardputer over USB

On a device the look is put back to what it was, and the app is left on its home screen.
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


def recognise(rows, look, hiragana):
    """Which kana is drawn large in the middle of the content area.

    Returns (the kana in hiragana, "hiragana" or "katakana"), or (None, None).
    """
    ax, ay, aw, _ = AREAS[look]
    top = ay + (0 if look == "rpg" else 4)
    height = font(BIG).height
    # Only pixels in the text colour count: the notebook look has ruled lines behind the kana.
    seen = {(x, y - top) for y in range(top, top + height) for x in range(ax, ax + aw)
            if rows[y][x] == INK[look]}
    for kana in hiragana:
        for script, shown in (("hiragana", kana), ("katakana", to_katakana(kana))):
            mask, width = glyph_mask(shown, BIG)
            if mask is None:
                continue
            left = ax + aw // 2 - width // 2
            if {(x + left, y) for (x, y) in mask} == seen:
                return kana, script
    return None, None


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


def go_home(target):
    for _ in range(4):
        screen, _ = target.frame()
        if screen == "home":
            return True
        target.key("Esc")
    return target.frame()[0] == "home"


def start_round(target):
    target.open("kana")


def choose_look(target, current, wanted):
    """From the home screen: sets the look in the settings and comes back."""
    target.open("settings")  # the first row is the look
    for _ in range((LOOKS.index(wanted) - LOOKS.index(current)) % len(LOOKS)):
        target.key("Right")
    target.key("Esc")
    target.key("Esc")
    screen, _ = target.frame()
    return screen


def play(target, look, index, table, expect, problems):
    hiragana = list(table)
    start_round(target)
    screen, rows = target.frame()
    expect(screen == "kana", "%s: the menu leads to the kana round" % look)

    # Odd looks are played in katakana. The app remembers the script, so look before switching.
    wanted_script = "katakana" if index % 2 == 1 else "hiragana"
    _, script = recognise(rows, look, hiragana)
    if script is not None and script != wanted_script:
        target.key("Tab")

    right = 0
    unread = 0
    for question in range(20):
        screen, rows = target.frame()
        kana, script = recognise(rows, look, hiragana)
        if kana is None:
            unread += 1
            target.type("zz")
            target.key("Enter")
            target.key("Enter")
            continue
        if script != wanted_script:
            problems.append("FAIL %s: question %d is in %s, expected %s" % (look, question + 1, script, wanted_script))
        answer_wrong = (question % 4 == 3)
        if question == 5:
            # pushes: Enter on nothing, Backspace on nothing, too many letters, then the answer
            target.key("Enter")
            target.key("Backspace")
            target.type("qqqqqqqqqqqqqqqq")
            for _ in range(20):
                target.key("Backspace")
            _, probe = target.frame()
            expect(result_of(probe, look) == "none", "%s: nothing is marked before an answer is given" % look)
        target.type("zu" if answer_wrong and kana != "ず" else ("a" if answer_wrong else table[kana]))
        target.key("Enter")
        _, rows = target.frame()
        got = result_of(rows, look)
        want = "wrong" if answer_wrong else "right"
        if got != want:
            problems.append("FAIL %s: %s answered with %s was marked %s, expected %s" % (
                look, kana, "a wrong reading" if answer_wrong else table[kana], got, want))
        if not answer_wrong:
            right += 1
        target.type(" ")   # any key moves on
    expect(unread == 0, "%s: every kana on screen was recognised in %s (%d not)" % (look, wanted_script, unread))

    screen, rows = target.frame()
    ax, ay, aw, _ = AREAS[look]
    score_mask, score_width = glyph_mask("%d / 20" % right, "efontJA_24")
    left = ax + aw // 2 - score_width // 2
    top = ay + 28
    seen = {(x, y - top) for y in range(top, top + 24) for x in range(ax, ax + aw) if is_green(rows[y][x])}
    expect({(x + left, y) for (x, y) in score_mask} == seen, "%s: the final screen shows %d / 20" % (look, right))

    target.key("Enter")
    screen, _ = target.frame()
    expect(screen == "kana", "%s: Enter on the final screen starts another round" % look)
    target.type("k")
    target.key("Esc")
    screen, _ = target.frame()
    expect(screen == "home", "%s: Esc in the middle of a round goes home" % look)
    start_round(target)
    screen, rows = target.frame()
    expect(screen == "kana" and result_of(rows, look) == "none", "%s: coming back starts a clean round" % look)
    target.key("Esc")


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    port = None
    if on_device:
        rest = [a for a in arguments if a != "--device"]
        port = rest[0] if rest else None

    table = kana_table()
    problems = []
    notes = []

    def expect(condition, message):
        (notes if condition else problems).append(("ok   " if condition else "FAIL ") + message)

    expect(len(table) >= 100, "kana known to the check: %d" % len(table))

    if on_device:
        from device_driver import Device
        try:
            device = Device(port)
            device.info()
        except RuntimeError as error:
            sys.exit("error: %s" % error)
        try:
            before = device.info()
            print("device: %s, look %s, %d bytes free, largest block %d" % (
                before["board"], before["look"], before["heapFree"], before["heapLargestBlock"]))
            expect(go_home(device), "device: Esc leads to the home screen")
            current = before["look"]
            for index, look in enumerate(LOOKS):
                screen = choose_look(device, current, look)
                current = look
                expect(screen == "home" and device.look() == look, "%s: the look is set and the home screen is back" % look)
                play(device, look, index, table, expect, problems)
            choose_look(device, current, before["look"])
            after = device.info()
            expect(after["look"] == before["look"], "device: the look is back to %s" % before["look"])
            expect(after["screen"] == 0, "device: left on the home screen")
            lost = before["heapFree"] - after["heapFree"]
            expect(lost < 8192, "device: memory after four rounds is within 8 KB of before (%d bytes less, lowest ever %d)" % (
                lost, after["heapLowest"]))
        finally:
            device.close()
    else:
        for index, look in enumerate(LOOKS):
            sim = Simulator(seed=100 + index)
            try:
                screen = choose_look(sim, "techo", look)
                expect(screen == "home", "%s: back on the home screen after choosing the look" % look)
                play(sim, look, index, table, expect, problems)
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
