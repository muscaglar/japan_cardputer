#!/usr/bin/env python3
"""Plays whole kana rounds and checks what the app does with the answers.

For every look: answers some questions correctly and some wrongly on purpose, and checks that the
app marks them accordingly and that the score at the end is the number answered correctly.
Also pushes on the edges: Enter on an empty line, a long line, Backspace on nothing, leaving and
coming back in the middle of a round.

    python3 tools/kana_round_check.py                  # in the simulator
    <PlatformIO's python> tools/kana_round_check.py --device [PORT]   # on a Cardputer over USB

The app says which kana it shows (`info`); the pictures are read to see that the kana and the
mark are really drawn. On a device the look is put back to what it was, and the app is left on
its home screen.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

ROUND = 20


def to_katakana(text):
    return "".join(chr(ord(c) + 0x60) if 0x3041 <= ord(c) <= 0x3096 else c for c in text)


def go_home(target):
    for _ in range(4):
        if target.info()["screen"] == 0:
            return True
        target.key("Esc")
    return target.info()["screen"] == 0


def choose_look(target, wanted):
    """From the home screen: sets the look in the settings and comes back."""
    current = target.look()
    target.open("settings")  # the first row is the look
    for _ in range((reader.LOOKS.index(wanted) - reader.LOOKS.index(current)) % len(reader.LOOKS)):
        target.key("Right")
    target.key("Esc")
    target.key("Esc")
    state = target.info()
    return state["screen"] == 0 and state["look"] == wanted


def play(target, look, index, colours, expect, problems):
    target.open("kana")
    state = target.info()
    expect(state["screen"] == 2 and state["kanaState"] == "typing" and state["asked"] == 0,
           "%s: the menu leads to a fresh kana round" % look)

    # Odd looks are played in katakana. The app remembers the script, so look before switching.
    wanted_script = "katakana" if index % 2 == 1 else "hiragana"
    if state["script"] != wanted_script:
        target.type(" ")
    expect(target.info()["script"] == wanted_script, "%s: Space switches to %s" % (look, wanted_script))

    right = 0
    undrawn = 0
    unmarked = 0
    for question in range(ROUND):
        state = target.info()
        kana = state["kana"]
        shown = to_katakana(kana) if wanted_script == "katakana" else kana
        _, rows = target.frame()
        if reader.find_anywhere(rows, colours[look]["ink"], shown, reader.PROMPT_FACES) is None:
            undrawn += 1
            problems.append("FAIL %s: question %d, %s is not drawn" % (look, question + 1, shown))
        if question == 5:
            # pushes: Enter on nothing, Backspace on nothing, too many letters, then the answer
            target.key("Enter")
            target.key("Backspace")
            target.type("qqqqqqqqqqqqqqqq")
            for _ in range(20):
                target.key("Backspace")
            probe = target.info()
            expect(probe["kanaState"] == "typing" and probe["asked"] == state["asked"],
                   "%s: nothing is marked before an answer is given" % look)
        if question == 7:
            target.key("Tab")
            _, rows = target.frame()
            help_text = reader.to_romaji(kana).replace("-", "")
            # at 24 px only: the hints at the bottom are 16 px and may hold the same letters
            expect(reader.find_anywhere(rows, colours[look]["accent"], help_text, [("efontJA_24", 1)]) is not None,
                   "%s: Tab shows the romaji %s" % (look, help_text))
        answer_wrong = (question % 4 == 3)
        target.type(("zu" if kana != "ず" else "a") if answer_wrong else reader.to_romaji(kana))
        target.key("Enter")
        after = target.info()
        want = "wrong" if answer_wrong else "right"
        if after["kanaState"] != want:
            problems.append("FAIL %s: %s answered with %s was marked %s, expected %s" % (
                look, shown, "a wrong reading" if answer_wrong else reader.to_romaji(kana), after["kanaState"], want))
        _, rows = target.frame()
        glyph, colour = ("×", "bad") if answer_wrong else ("〇", "good")
        line = glyph + " " + reader.to_romaji(kana)
        if answer_wrong:
            line += "  not " + ("zu" if kana != "ず" else "a")
        if reader.find_anywhere(rows, colours[look][colour], line, reader.TEXT_FACES) is None:
            unmarked += 1
            problems.append("FAIL %s: the line %r is not drawn" % (look, line))
        if not answer_wrong:
            right += 1
        target.type(" ")   # any key moves on
    expect(undrawn == 0, "%s: every kana was drawn large, in %s" % (look, wanted_script))
    expect(unmarked == 0, "%s: every answer was marked on the screen" % look)

    state = target.info()
    expect(state["kanaState"] == "done" and state["correct"] == right,
           "%s: the round ends with %d right (the app says %d)" % (look, right, state["correct"]))
    _, rows = target.frame()
    expect(reader.find_anywhere(rows, colours[look]["good"], "%d of %d right" % (right, ROUND),
                                reader.TEXT_FACES) is not None,
           "%s: the final screen shows %d of %d right" % (look, right, ROUND))

    target.key("Enter")
    state = target.info()
    expect(state["screen"] == 2 and state["asked"] == 0 and state["kanaState"] == "typing",
           "%s: Enter on the final screen starts another round" % look)
    target.type("k")
    target.key("Esc")
    expect(target.info()["screen"] == 0, "%s: Esc in the middle of a round goes home" % look)
    target.open("kana")
    state = target.info()
    expect(state["screen"] == 2 and state["asked"] == 0 and state["correct"] == 0,
           "%s: coming back starts a clean round" % look)
    target.key("Esc")


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    colours, _ = reader.themes()
    problems = []
    notes = []

    def expect(condition, message):
        (notes if condition else problems).append(("ok   " if condition else "FAIL ") + message)

    if on_device:
        from device_driver import Device
        try:
            device = Device(port)
            before = device.info()
        except RuntimeError as error:
            sys.exit("error: %s" % error)
        try:
            print("device: %s, look %s, %d bytes free, largest block %d" % (
                before["board"], before["look"], before["heapFree"], before["heapLargestBlock"]), flush=True)
            expect(go_home(device), "device: Esc leads to the home screen")
            for look in looks:
                expect(choose_look(device, look), "%s: the look is set and the home screen is back" % look)
                play(device, look, reader.LOOKS.index(look), colours, expect, problems)
                print("%s done" % look, flush=True)
            choose_look(device, before["look"])
            after = device.info()
            expect(after["look"] == before["look"], "device: the look is back to %s" % before["look"])
            expect(after["screen"] == 0, "device: left on the home screen")
            lost = before["heapFree"] - after["heapFree"]
            expect(lost < 8192, "device: memory after the rounds is within 8 KB of before (%d bytes less, "
                                "lowest ever %d)" % (lost, after["heapLowest"]))
        finally:
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=100 + reader.LOOKS.index(look))
            try:
                expect(choose_look(sim, look), "%s: the look is set and the home screen is back" % look)
                play(sim, look, reader.LOOKS.index(look), colours, expect, problems)
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
