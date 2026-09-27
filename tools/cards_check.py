#!/usr/bin/env python3
"""Plays sittings over two days and checks what the app does with the answers.

    python3 tools/cards_check.py                          # in the simulator, all four looks
    python3 tools/cards_check.py techo                    # one look
    <PlatformIO's python> tools/cards_check.py --device   # on a Cardputer over USB

What is checked, in every look:
  day 1  four new cards are shown with their answer and want it typed; a wrong copy costs
         nothing; each comes back in the same sitting as a question; a right answer is marked 〇,
         a near miss △, a wrong one ×, a card given up →; what was missed comes back again;
         the end shows right / asked
  start  after a restart the app asks whether a new day has begun
  day 2  what was learnt on day 1 is due and is asked before anything new

The app says which card it shows (`info`); the pictures are read to see that the card and the
mark are really drawn. On a device the owner's settings and progress are kept aside first and
put back at the end.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

MARKS = {"right": ("〇", "good"), "almost": ("△", "wait"), "wrong": ("×", "bad"), "shown": ("→", "dim")}


class Check:
    def __init__(self):
        self.passed = []
        self.failed = []

    def expect(self, condition, message):
        (self.passed if condition else self.failed).append(message)
        if not condition:
            print("FAIL " + message, flush=True)
        return condition


def prompt_font(rows, look, colours, areas, prompt):
    """The font in which the prompt is drawn at the top of the card, or None if it is not there."""
    ax, ay, aw, _ = areas[look]
    centre = ax + aw // 2
    for name, _height in reader.FONTS:
        w = reader.width(prompt, name)
        if reader.mask(prompt, name)[0] is None:
            continue
        if reader.find_text(rows, colours[look]["ink"], prompt, name, centre - w // 2, ay + 1) is not None:
            return name
    return None


def mark_drawn(rows, look, colours, areas, font_name, reading, verdict):
    """Whether the mark for the verdict stands in front of the reading."""
    ax, ay, aw, _ = areas[look]
    centre = ax + aw // 2
    glyph, colour = MARKS[verdict]
    line = "efontJA_16" if reader.width(reading, "efontJA_16") + 24 <= aw else "efontJA_12"
    mark_width = reader.width(glyph, line) + 4
    left = centre - (mark_width + reader.width(reading, line)) // 2
    top = ay + 1 + reader.font(font_name).height + 6 + 1
    return reader.find_text(rows, colours[look][colour], glyph, line, left, top, slack=3) is not None


def score_drawn(rows, look, colours, areas, right, asked):
    ax, ay, aw, _ = areas[look]
    centre = ax + aw // 2
    text = "%d / %d" % (right, asked)
    top = ay + (4 if look == "rpg" else 24)
    left = centre - 40 - reader.width(text, "efontJA_24") // 2
    return reader.find_text(rows, colours[look]["good"], text, "efontJA_24", left, top, slack=2) is not None


def set_look(target, wanted):
    """From the home screen."""
    current = target.look()
    target.open("settings")
    for _ in range((reader.LOOKS.index(wanted) - reader.LOOKS.index(current)) % len(reader.LOOKS)):
        target.key("Right")
    target.key("Esc")
    target.key("Esc")
    return target.look() == wanted and target.info()["screen"] == 0


def play_sitting(target, look, items, colours, areas, check, day, plan):
    """Answers every card of a sitting. `plan` names what to do with the n-th question asked."""
    asked = 0
    right = 0
    questions = 0
    met = []
    introduced = set()
    verdicts = []
    tried_wrong_copy = False
    for _ in range(80):
        state = target.info()
        if state["screen"] != 4:
            break
        item = items.get(state["card"])
        if not check.expect(item is not None, "%s day %d: the card %s is in the decks" % (look, day, state["card"])):
            target.key("Esc")
            break
        met.append((state["card"], state["cardState"]))
        _, rows = target.frame()
        drawn = prompt_font(rows, look, colours, areas, item["prompt"])
        check.expect(drawn is not None, "%s day %d: %s is drawn as %s" % (look, day, state["card"], item["prompt"]))
        answer = reader.to_romaji(item["reading"])

        if state["cardState"] == "introduce":
            introduced.add(state["card"])
            if not tried_wrong_copy:
                tried_wrong_copy = True
                target.type("zu")
                target.key("Enter")
                after = target.info()
                check.expect(after["card"] == state["card"] and after["cardState"] == "introduce" and
                             after["answeredToday"] == state["answeredToday"],
                             "%s day %d: a wrong copy of a new card costs nothing and the card stays" % (look, day))
            target.type(answer)
            target.key("Enter")
            asked += 1
            right += 1
            after = target.info()
            check.expect(after["answeredToday"] == state["answeredToday"] + 1,
                         "%s day %d: %s copied, the answer counts" % (look, day, state["card"]))
            continue

        step = plan[questions] if questions < len(plan) else "right"
        questions += 1
        slip = reader.nearly(item["reading"], item["accepted"]) if step == "almost" else None
        if step == "almost" and slip is None:
            step = "wrong"
        if step == "right":
            target.type(answer)
            target.key("Enter")
        elif step == "almost":
            target.type(reader.to_romaji(slip[0]))
            target.key("Enter")
        elif step == "wrong":
            target.type("zzz")
            target.key("Enter")
        else:
            target.key("Tab")
        want = {"right": "right", "almost": "almost", "wrong": "wrong", "shown": "shown"}[step]
        after = target.info()
        asked += 1
        right += 1 if want == "right" else 0
        verdicts.append(want)
        ok = check.expect(after.get("cardState") == "marked" and after.get("verdict") == want,
                          "%s day %d: %s answered %s is marked %s (the app says %s)" % (
                              look, day, state["card"], step + (" by " + slip[1] if slip else ""), want,
                              after.get("verdict")))
        if ok and drawn:
            _, rows = target.frame()
            check.expect(mark_drawn(rows, look, colours, areas, drawn, item["reading"], want),
                         "%s day %d: the mark %s stands before %s" % (look, day, MARKS[want][0], item["reading"]))
        target.type(" ")
    return {"asked": asked, "right": right, "met": met, "introduced": introduced, "verdicts": verdicts}


def check_look(target, look, items, colours, areas, check):
    check.expect(target.fresh(), "%s: progress starts empty" % look)
    check.expect(set_look(target, look), "%s: the look is set, the home screen is back" % look)
    state = target.info()
    check.expect(state["due"] == 0 and state["new"] == 4 and state["day"] == 1,
                 "%s: day 1 starts with nothing due and four new cards (%d due, %d new)" % (
                     look, state["due"], state["new"]))

    # day 1
    target.type("x")
    check.expect(target.info()["screen"] == 4, "%s: a key on the home screen starts a sitting" % look)
    played = play_sitting(target, look, items, colours, areas, check, 1, ["right", "almost", "wrong", "shown"])
    check.expect(len(played["introduced"]) == 4, "%s day 1: four new cards were introduced (%d)" % (
        look, len(played["introduced"])))
    asked_again = {card for card, state in played["met"] if state == "asking"}
    check.expect(played["introduced"] <= asked_again,
                 "%s day 1: every new card came back as a question in the same sitting" % look)
    for wanted in ("right", "almost", "wrong", "shown"):
        if wanted == "almost" and "almost" not in played["verdicts"]:
            continue  # no card of this sitting allowed a near miss
        check.expect(wanted in played["verdicts"], "%s day 1: an answer marked %s was seen" % (look, wanted))
    missed = [card for (card, state), verdict in zip([m for m in played["met"] if m[1] == "asking"], played["verdicts"])
              if verdict != "right"]
    counts = {card: sum(1 for c, s in played["met"] if c == card and s == "asking") for card in missed}
    check.expect(all(n >= 2 for n in counts.values()),
                 "%s day 1: what was missed came back in the same sitting (%s)" % (look, counts))

    state = target.info()
    check.expect(state["screen"] == 5, "%s day 1: the sitting ends on the summary" % look)
    _, rows = target.frame()
    check.expect(score_drawn(rows, look, colours, areas, played["right"], played["asked"]),
                 "%s day 1: the summary shows %d / %d" % (look, played["right"], played["asked"]))
    check.expect(state["answeredToday"] == played["asked"] and state["seen"] == 4,
                 "%s day 1: %d answers counted, four cards seen (%d, %d)" % (
                     look, played["asked"], state["answeredToday"], state["seen"]))
    learnt = state["learnt"]
    target.type(" ")
    check.expect(target.info()["screen"] == 0, "%s day 1: a key on the summary leads home" % look)

    # the next start
    target.restart()
    state = target.info()
    check.expect(state["screen"] == 0 and state.get("asksForDay") is True and state["seen"] == 4 and
                 state["look"] == look,
                 "%s: after a restart the look and the progress are kept and the app asks for the day" % look)
    target.type(" ")
    state = target.info()
    check.expect(state["day"] == 1 and state.get("asksForDay") is False, "%s: Space keeps the day" % look)
    target.restart()
    target.key("Enter")
    state = target.info()
    check.expect(state["day"] == 2 and state["answeredToday"] == 0, "%s: Enter starts day 2" % look)
    check.expect(state["due"] >= learnt and learnt >= 1,
                 "%s day 2: what was learnt on day 1 is due (%d learnt, %d due)" % (look, learnt, state["due"]))

    # day 2
    due = state["due"]
    target.type("x")
    played = play_sitting(target, look, items, colours, areas, check, 2, [])
    first = [state for _, state in played["met"][:due]]
    check.expect(len(first) == due and all(s == "asking" for s in first),
                 "%s day 2: the %d cards that are due are asked before anything new" % (look, due))
    check.expect(len(played["introduced"]) == 4, "%s day 2: four more new cards follow" % look)
    state = target.info()
    check.expect(state["screen"] == 5 and state["seen"] == 8, "%s day 2: eight cards seen in all (%d)" % (
        look, state["seen"]))
    target.type(" ")


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    colours, areas = reader.themes()
    items = reader.decks()
    check = Check()
    check.expect(len(items) > 100, "decks read: %d cards" % len(items))

    if on_device:
        from device_driver import Device
        try:
            device = Device(port)
            before = device.info()
        except RuntimeError as error:
            sys.exit("error: %s" % error)
        print("device: %s, look %s, day %d, %d cards seen, %d bytes free" % (
            before["board"], before["look"], before["day"], before["seen"], before["heapFree"]), flush=True)
        if not device.keep():
            device.close()
            sys.exit("error: the device could not keep its progress aside; nothing was changed")
        try:
            for look in looks:
                for _ in range(4):
                    if device.info()["screen"] == 0:
                        break
                    device.key("Esc")
                check_look(device, look, items, colours, areas, check)
                print("%s done" % look, flush=True)
        finally:
            restored = device.back()
            after = device.info()
            check.expect(restored and after["look"] == before["look"] and after["day"] == before["day"] and
                         after["seen"] == before["seen"],
                         "device: settings and progress are back as they were (look %s, day %d, %d seen)" % (
                             after["look"], after["day"], after["seen"]))
            check.expect(after["heapLowest"] > 100000,
                         "device: never less than 100 KB of memory free (lowest %d)" % after["heapLowest"])
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=11)
            try:
                check_look(sim, look, items, colours, areas, check)
            finally:
                sim.close()

    print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
