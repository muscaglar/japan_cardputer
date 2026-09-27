#!/usr/bin/env python3
"""Writes sim/scenarios.json: the key sequences that lead to every screen worth a reference picture.

The sequences are found by playing the app in the simulator and asking it where it is, so that
they stay right when decks or flows change. Run it after such a change, then `node sim/shots.js`.

    python3 sim/make_scenarios.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402


class Recorder:
    """A simulator that remembers the keys it was given, in the words of scenarios.json."""

    def __init__(self):
        self.sim = Simulator(seed=1)
        self.keys = []

    def key(self, name):
        self.sim.key(name)
        self.keys.append("<%s>" % name)

    def type(self, text):
        self.sim.type(text)
        self.keys.append(text)

    def restart(self):
        self.sim.restart()
        self.keys.append("<Restart>")

    def menu(self, entry):
        """From the home screen: opens the entry by its number, which does not depend on history."""
        self.key("Tab")
        names = self.sim.info()["menu"]
        self.type(str(names.index(entry) + 1))

    def info(self):
        return self.sim.info()

    def close(self):
        self.sim.close()


def main():
    items = reader.decks()
    scenarios = []

    def keep(name, recorder):
        scenarios.append({"name": name, "keys": list(recorder.keys)})

    for index, look in enumerate(reader.LOOKS):
        r = Recorder()
        try:
            if index:
                r.menu("settings")
                for _ in range(index):
                    r.key("Right")
                keep("settings_" + look, r)
                r.key("Esc")
                r.key("Esc")
            keep("home_" + look, r)
            r.type("x")
            wanted = ["right", "almost", "wrong", "shown"]
            seen = set()
            questions = 0
            for _ in range(80):
                state = r.info()
                if state["screen"] != 4:
                    break
                item = items[state["card"]]
                answer = reader.to_romaji(item["reading"])
                kind = state["cardState"]
                if kind == "meet":
                    if "meet" not in seen:
                        seen.add("meet")
                        keep("card_meet_" + look, r)
                    r.key("Enter")
                elif kind == "copy":
                    if "copy" not in seen:
                        seen.add("copy")
                        keep("card_new_" + look, r)
                        if look == "techo":
                            r.type(answer[:2])
                            keep("card_typing", r)
                            r.type("zz")
                            r.key("Enter")
                            r.type("zz")
                            r.key("Enter")
                            keep("card_copy_help", r)
                    r.type(answer)
                    r.key("Enter")
                else:
                    step = wanted[questions] if questions < len(wanted) else "right"
                    questions += 1
                    slip = reader.nearly(item["reading"], item["accepted"]) if step == "almost" else None
                    if step == "almost" and not slip:
                        step = "wrong"
                    if "asking" not in seen:
                        seen.add("asking")
                        keep("card_asking_" + look, r)
                    if step == "right":
                        r.type(answer)
                        r.key("Enter")
                    elif step == "almost":
                        r.type(reader.to_romaji(slip[0]))
                        r.key("Enter")
                    elif step == "wrong":
                        r.type("zzz")
                        r.key("Enter")
                    else:
                        r.key("Tab")
                        if look == "techo":
                            keep("card_help", r)
                        r.key("Tab")
                    if step not in seen:
                        seen.add(step)
                        keep("card_%s_%s" % (step, look), r)
                        if step != "right" and item.get("note") and "note" not in seen:
                            seen.add("note")
                            r.key("Tab")
                            keep("card_note_" + look, r)
                    r.type(" ")
            keep("summary_" + look, r)
            r.type(" ")
            if look == "techo":
                r.restart()
                keep("home_new_day", r)
                r.key("Enter")
                keep("home_day_2", r)
                r.key("Tab")
                keep("menu", r)
                r.key("Up")
                keep("menu_scrolled", r)
                r.key("Esc")
                r.menu("settings")
                r.key("Down")
                keep("settings_techo", r)
                r.key("Esc")
                r.key("Esc")
                r.menu("keys")
                keep("keys", r)
                r.key("Esc")
                r.key("Esc")
            r.menu("kana")
            r.type("k")
            keep("kana_" + look, r)
            if look == "techo":
                r.key("Tab")
                keep("kana_help", r)
                r.type("zz")
                r.key("Enter")
                keep("kana_wrong", r)
        finally:
            r.close()

    names = [s["name"] for s in scenarios]
    if len(names) != len(set(names)):
        sys.exit("two scenarios share a name: " + ", ".join(sorted(n for n in set(names) if names.count(n) > 1)))
    text = "[\n" + ",\n".join("  " + json.dumps(s, ensure_ascii=False) for s in scenarios) + "\n]\n"
    open(os.path.join(ROOT, "sim", "scenarios.json"), "w", encoding="utf-8").write(text)
    print("%d scenarios written" % len(scenarios))


if __name__ == "__main__":
    main()
