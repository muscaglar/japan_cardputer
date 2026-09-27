#!/usr/bin/env python3
"""Checks that everything the app asks of the memory card lies in its one folder.

    python3 tools/card_folder_check.py

Plays a card, a kana of the quiz, a page of the guide and a sample from the settings with sound
switched on, in the simulator, and looks at the whole path the app asked for each time.
The folder is ui::kCardFolder in lib/ui/app.h.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def folder():
    source = open(os.path.join(ROOT, "lib", "ui", "app.h"), encoding="utf-8").read()
    found = re.search(r'kCardFolder\s*=\s*"([^"]+)"', source)
    if not found:
        sys.exit("kCardFolder is not in lib/ui/app.h")
    return found.group(1)


def set_setting(sim, row, wanted):
    """From the home screen. wanted: a text the value must start with."""
    sim.open("settings")
    state = sim.info()
    for _ in range(abs(state["rows"].index(row) - state["chosen"])):
        sim.key("Down" if state["rows"].index(row) > state["chosen"] else "Up")
    for _ in range(8):
        state = sim.info()
        if state["values"][state["rows"].index(row)].startswith(wanted):
            break
        sim.key("Right")
    ok = sim.info()["values"][state["rows"].index(row)].startswith(wanted)
    sim.key("Esc")
    sim.key("Esc")
    return ok


def main():
    root = folder()
    items = reader.decks()
    passed, failed = [], []

    def expect(condition, message):
        (passed if condition else failed).append(message)
        if not condition:
            print("FAIL " + message)

    expect(re.fullmatch(r"/[a-z0-9_-]{1,32}", root) is not None, "the folder %s is one plain name" % root)
    sim = Simulator(seed=5)
    try:
        expect(set_setting(sim, "sound", "on"), "sound is switched on")
        asked = []

        def heard(what):
            state = sim.info()
            path = state["playedOnCard"]
            asked.append(path)
            expect(state["plays"] > 0 and path.startswith(root + "/audio/") and path.endswith(".wav") and
                   ".." not in path and "//" not in path,
                   "%s: asks the card for %s" % (what, path or "nothing"))

        sim.sitting("signs")
        for _ in range(12):
            state = sim.info()
            if state.get("cardState") in ("meet", "copy"):
                break
            sim.key("Enter")
        heard("a new card")

        sim.key("Esc")
        sim.key("Esc")
        sim.key("Esc")
        sim.open("kana")
        state = sim.info()
        sim.type(reader.to_romaji(state["kana"]))
        sim.key("Enter")
        heard("the kana quiz")
        sim.key("Esc")

        sim.open("guide")
        sim.type("/")
        heard("the guide")
        sim.key("Esc")
        sim.key("Esc")

        sim.open("chart")
        sim.key("Enter")
        heard("the kana chart")
        sim.key("Esc")
        sim.key("Esc")

        before = sim.info()["plays"]
        sim.open("settings")
        state = sim.info()
        for _ in range(state["rows"].index("volume") - state["chosen"]):
            sim.key("Down")
        sim.key("Right")
        expect(sim.info()["plays"] > before, "changing the volume plays a sample")
        heard("the settings")
        expect(len(set(asked)) >= 4, "the five places asked for different files (%d)" % len(set(asked)))
    finally:
        sim.close()
    print("%d checks passed, %d failed" % (len(passed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
