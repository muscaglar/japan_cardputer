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

CARDS = 4


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

    def sitting(self, deck=""):
        self.sim.sitting(deck)
        self.keys.append("<Sitting:%s>" % deck)

    def menu(self, entry):
        """From the home screen: opens the entry by its number, which does not depend on history."""
        self.key("Tab")
        names = self.sim.info()["menu"]
        self.type(str(names.index(entry) + 1))

    def home(self):
        for _ in range(4):
            if self.sim.info()["screen"] == 0:
                return
            self.key("Esc")

    def info(self):
        return self.sim.info()

    def close(self):
        self.sim.close()


def main():
    items = reader.decks()
    scenarios = []

    def keep(name, recorder):
        if name not in [s["name"] for s in scenarios]:
            scenarios.append({"name": name, "keys": list(recorder.keys)})

    def play(r, look, prefix, plan):
        """Plays the sitting that is open and keeps a picture of every state met for the first time."""
        questions = 0
        probes = 0
        for _ in range(80):
            state = r.info()
            if state["screen"] != CARDS:
                break
            item = items[state["card"]]
            answer = reader.to_romaji(item["reading"])
            kind = state["cardState"]
            keep("%s_%s_%s" % (prefix, kind, look), r)
            if kind in ("meet", "note"):
                r.key("Enter")
            elif kind == "copy":
                if prefix == "card" and look == "techo":
                    r.type(answer[:2])
                    keep("card_typing", r)
                    r.type("zz")
                    r.key("Enter")
                    r.type("zz")
                    r.key("Enter")
                    keep("card_copy_help", r)
                r.type(answer)
                r.key("Enter")
            elif kind == "probe":
                probes += 1
                if probes == 2:
                    r.type("zz")      # not known: it is taught
                    r.key("Enter")
                elif probes == 3:
                    r.key("Tab")      # passed: it is taught as well
                else:
                    r.type(answer)
                    r.key("Enter")
            elif kind == "asking":
                step = plan[questions] if questions < len(plan) else "right"
                questions += 1
                slip = reader.nearly(item["reading"], item["accepted"]) if step == "almost" else None
                if step == "almost" and not slip:
                    step = "wrong"
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
                    keep("%s_help_%s" % (prefix, look), r)
                    r.key("Tab")
                after = r.info()
                keep("%s_%s_%s" % (prefix, after.get("verdict"), look), r)
                if step != "right" and (item.get("note") or item.get("parts")):
                    r.key("Tab")
                    keep("%s_more_%s" % (prefix, look), r)
                    r.key("Esc") if r.info().get("cardState") not in ("note", "marked") else None
                r.type(" ")
            else:  # marked
                r.type(" ")

    for index, look in enumerate(reader.LOOKS):
        r = Recorder()
        try:
            if index:
                r.menu("settings")
                for _ in range(index):
                    r.key("Right")
                keep("settings_" + look, r)
                r.home()
            keep("home_" + look, r)

            # the course begins with kana
            r.type("x")
            play(r, look, "kana", ["right", "wrong"])
            keep("summary_kana_" + look, r)
            r.home()

            # words
            r.sitting("signs")
            play(r, look, "card", ["right", "almost", "wrong", "shown"])
            keep("summary_" + look, r)
            r.home()

            if look == "techo":
                r.restart()
                keep("home_new_day", r)
                r.key("Enter")
                keep("home_day_2", r)
                r.key("Tab")
                keep("menu", r)
                r.key("Up")
                keep("menu_scrolled", r)
                r.home()
                r.menu("decks")
                keep("decks", r)
                r.key("Down")
                r.key("Down")
                keep("decks_chosen", r)
                r.home()
                r.menu("chart")
                keep("chart", r)
                r.key("Right")
                r.key("Down")
                r.type(" ")
                keep("chart_katakana", r)
                r.home()
                r.menu("guide")
                keep("guide", r)
                for _ in range(8):
                    r.key("Right")
                keep("guide_line", r)
                r.home()
                r.menu("keys")
                keep("keys", r)
                r.home()
                r.menu("settings")
                keep("settings_techo", r)
                for _ in range(5):
                    r.key("Down")
                keep("settings_scrolled", r)
                r.home()
            r.menu("kana")
            r.type("k")
            keep("quiz_" + look, r)
            if look == "techo":
                r.key("Tab")
                keep("quiz_help", r)
                r.type("zz")
                r.key("Enter")
                keep("quiz_wrong", r)
        finally:
            r.close()

    text = "[\n" + ",\n".join("  " + json.dumps(s, ensure_ascii=False) for s in scenarios) + "\n]\n"
    open(os.path.join(ROOT, "sim", "scenarios.json"), "w", encoding="utf-8").write(text)
    print("%d scenarios written" % len(scenarios))


if __name__ == "__main__":
    main()
