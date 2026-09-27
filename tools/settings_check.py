#!/usr/bin/env python3
"""Plays the settings, and the sound of the kana quiz that they steer.

For every look: walks through the seven rows and reads the picture to see that the chosen row is
in sight, that the rows out of sight are not drawn and that ▲ and ▼ say where there is more;
changes every row forth and back; switches off and on again to see that what was set is kept;
listens to what is played after a change of volume or voice; and answers kana with the sound on
and off. Also pushes on the edges: past the first and the last row, past the quietest and the
loudest, keys that mean nothing, the memory card taken out.

    python3 tools/settings_check.py                  # in the simulator
    <PlatformIO's python> tools/settings_check.py --device [PORT]   # on a Cardputer over USB

The simulator tells what the app would have played. A device does not, so there the check of
what is heard is left out. On a device the owner's settings are kept aside first and put back at
the end, and the app is left on its home screen.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

ROWS = ["look", "cards", "romaji", "sound", "volume", "voice", "typing"]
LABELS = {"look": "Look", "cards": "Cards", "romaji": "Romaji", "sound": "Sound", "volume": "Volume",
          "voice": "Voice", "typing": "Typing ん"}
VISIBLE = 5
LOUDEST = 5
SAMPLE = "/audio/%s/hiragana/hiragana-a.wav"
FACE16 = [("efontJA_16", 1)]

# What a row stands for in the account the app gives of itself, and the values it goes through.
FIELD = {"look": "look", "cards": "level", "romaji": "romaji", "sound": "sound", "volume": "volume",
         "voice": "voice", "typing": "textbookN"}
TURNS = {"look": reader.LOOKS, "cards": [1, 2, 3], "romaji": ["peek", "always", "never"], "sound": [False, True],
         "voice": ["both", "female", "male"], "typing": [True, False]}
USUAL = {"cards": 3, "romaji": "peek", "sound": False, "volume": 3, "voice": "both", "typing": True}


def look_names():
    """look -> its name in English, from lib/ui/theme.cpp."""
    source = open(os.path.join(reader.ROOT, "lib", "ui", "theme.cpp"), encoding="utf-8").read()
    return dict(re.findall(r'\{ThemeId::\w+, "(\w+)", "[^"]*", "([^"]*)",', source))


def kana_items():
    """(deck, prompt) -> item id, for the two kana decks."""
    return {(item["deck"], item["prompt"]): name for name, item in reader.decks().items()
            if item["deck"] in ("hiragana", "katakana")}


def to_katakana(text):
    return "".join(chr(ord(c) + 0x60) if 0x3041 <= ord(c) <= 0x3096 else c for c in text)


def shown_values(state, names):
    """What the seven rows should say, from what the app says is set."""
    sound = "off" if not state["sound"] else "on" if state["memoryCard"] else "on, no card"
    return [names[state["look"]], {1: "kana only", 2: "easy kanji too", 3: "all"}[state["level"]],
            {"peek": "with Tab", "always": "always", "never": "never"}[state["romaji"]], sound,
            "%d of %d" % (state["volume"], LOUDEST), state["voice"],
            "minna = みんな" if state["textbookN"] else "minnna = みんな"]


def header_colours(look, colours):
    """The colours drawFrame() gives the title, the text on the right of it, and the hint on the
    right of the footer."""
    c = colours[look]
    title = {"techo": c["headInk"], "eki": c["headInk"], "rpg": c["ink"], "washi": c["accent"]}[look]
    right = c["dim"] if look == "rpg" else c["headInk"]
    hint = {"techo": c["headInk"], "eki": c["headAccent"], "rpg": c["accent"], "washi": c["accent"]}[look]
    return title, right, hint


def find16(rows, colour, text):
    return reader.find_anywhere(rows, colour, text, FACE16)


def plays(state):
    """How many clips were played so far. None where the machine does not tell."""
    return state.get("plays")


def let_time_pass(target):
    if hasattr(target, "send"):
        target.send("wait 50")
    else:
        time.sleep(0.2)


def go_home(target):
    for _ in range(5):
        if target.info()["screen"] == 0:
            return True
        target.key("Esc")
    return target.info()["screen"] == 0


def go_to_row(target, row):
    """In the settings: moves to the row of that id by the shorter way. Returns the state there."""
    state = target.info()
    steps = ROWS.index(row) - state["chosen"]
    for _ in range(abs(steps)):
        target.key("Down" if steps > 0 else "Up")
    return target.info()


def set_row(target, row, wanted):
    """In the settings: sets one row to the value wanted. Returns whether it is set."""
    state = go_to_row(target, row)
    for _ in range(8):
        now = state[FIELD[row]]
        if now == wanted:
            return True
        if row == "volume":
            target.key("Right" if now < wanted else "Left")
        else:
            target.key("Right")
        state = target.info()
    return state[FIELD[row]] == wanted


def set_all(target, values):
    """From the home screen: sets the rows named, and comes back to the home screen."""
    target.open("settings")
    done = all([set_row(target, row, wanted) for row, wanted in values.items()])
    target.key("Esc")
    target.key("Esc")
    return done and target.info()["screen"] == 0


def in_sight_after(first, chosen):
    """The row at the top of the screen once the chosen row was brought into sight."""
    if chosen < first:
        return chosen
    if chosen >= first + VISIBLE:
        return chosen - VISIBLE + 1
    return first


def read_list(rows, look, colours, names, state):
    """Compares the picture of the settings with the state. Returns what is wrong, as sentences."""
    wrong = []
    c = colours[look]
    chosen, first = state["chosen"], state["first"]
    values = shown_values(state, names)
    title, right, _ = header_colours(look, colours)

    if find16(rows, title, "Settings") is None:
        wrong.append("the title Settings is not drawn")
    place = "%d/%d" % (chosen + 1, len(ROWS))
    if find16(rows, right, place) is None:
        wrong.append("%s is not drawn in the header" % place)

    tops = []
    edges = set()
    for index, row in enumerate(ROWS):
        label = LABELS[row]
        is_chosen = (index == chosen)
        found = find16(rows, c["rowInk"] if is_chosen else c["ink"], label)
        if not (first <= index < first + VISIBLE):
            if found is not None or find16(rows, c["ink"], label) is not None:
                wrong.append("%s is drawn although it is out of sight" % label)
            continue
        if found is None:
            wrong.append("%s is not drawn" % label)
            continue
        left, top = found[0], found[1]
        tops.append(top)
        lit = (rows[top + 8][left - 2] == c["row"])
        if lit != is_chosen:
            wrong.append("%s is %s" % (label, "not marked as chosen" if is_chosen else "marked as chosen"))
        value = find16(rows, c["accent"] if is_chosen else c["dim"], values[index])
        if value is None:
            wrong.append("%s does not show %r" % (label, values[index]))
            continue
        if value[1] != top:
            wrong.append("%r is not on the line of %s" % (values[index], label))
        edges.add(value[0] + reader.width(values[index], "efontJA_16"))
        if left + reader.width(label, "efontJA_16") + 8 > value[0]:
            wrong.append("%s and %r run into each other" % (label, values[index]))

    if len(tops) == VISIBLE:
        steps = {b - a for a, b in zip(tops, tops[1:])}
        if len(steps) != 1 or min(steps) < 17:
            wrong.append("the rows are not evenly apart, or too close: %s" % tops)
    if len(edges) > 1:
        wrong.append("the values do not end at the same place: %s" % sorted(edges))

    for glyph, wanted, line in (("▲", first > 0, 0), ("▼", first + VISIBLE < len(ROWS), VISIBLE - 1)):
        found = find16(rows, c["dim"], glyph)
        if wanted and found is None:
            wrong.append("%s is missing although there is more" % glyph)
        elif not wanted and found is not None:
            wrong.append("%s is drawn although there is no more" % glyph)
        elif wanted and len(tops) == VISIBLE:
            if found[1] != tops[line]:
                wrong.append("%s is not on the %s row in sight" % (glyph, "first" if line == 0 else "last"))
            if edges and found[0] < max(edges):
                wrong.append("%s is drawn over a value" % glyph)
    return wrong


def walk(target, look, colours, names, expect):
    """Through the rows and around both ends, reading every picture."""
    target.open("settings")
    state = target.info()
    expect(state["screen"] == 3 and state.get("rows") == ROWS and state.get("visible") == VISIBLE,
           "%s: the settings say their rows: %s" % (look, ", ".join(state.get("rows", []))))
    expect(state.get("chosen") == 0 and state.get("first") == 0, "%s: they open at the first row" % look)
    expect(state.get("values") == shown_values(state, names),
           "%s: the values they say are what is set: %s" % (look, ", ".join(state.get("values", []))))

    wrong = []
    lost = 0
    first = 0
    # down past the last row, then up past the first
    for key, count in (("Down", len(ROWS) + 2), ("Up", len(ROWS) + 3)):
        for _ in range(count):
            _, rows = target.frame()
            wrong += ["row %d, %s" % (state["chosen"] + 1, w) for w in read_list(rows, look, colours, names, state)]
            before = state["chosen"]
            target.key(key)
            state = target.info()
            wanted = (before + (1 if key == "Down" else -1)) % len(ROWS)
            first = in_sight_after(first, wanted)
            if state["chosen"] != wanted or state["first"] != first:
                lost += 1
                wrong.append("%s from row %d led to row %d with row %d at the top, expected row %d and %d" % (
                    key, before + 1, state["chosen"] + 1, state["first"] + 1, wanted + 1, first + 1))
    for line in wrong:
        expect(False, "%s: %s" % (look, line))
    expect(not wrong, "%s: on the way down and up every picture showed the rows in sight, the chosen one "
                      "marked, ▲ and ▼ where there is more" % look)
    expect(lost == 0, "%s: past the last row comes the first, past the first the last" % look)

    # keys that mean nothing here
    before = target.info()
    target.type("x5 ")
    after = target.info()
    expect(after == before, "%s: letters, digits and Space change nothing" % look)

    target.key("Down")
    target.key("Down")
    target.key("Esc")
    expect(target.info()["screen"] == 1, "%s: Esc leads back to the menu" % look)
    target.key("Esc")
    target.open("settings")
    state = target.info()
    expect(state["chosen"] == 0 and state["first"] == 0, "%s: opened again, they start at the first row" % look)
    target.key("Tab")
    expect(target.info()["screen"] == 1, "%s: Tab leads back to the menu too" % look)
    target.key("Esc")


def change(target, look, colours, names, expect, restart):
    """Every row forth and back, then off and on again."""
    target.open("settings")
    for row in ROWS:
        state = go_to_row(target, row)
        start = state[FIELD[row]]
        if row == "volume":
            continue
        turns = TURNS[row]
        seen = []
        drawn = True
        for press in range(len(turns)):
            target.key("Enter" if press == 0 else "Right")
            state = target.info()
            seen.append(state[FIELD[row]])
            _, rows = target.frame()
            if read_list(rows, state["look"], colours, names, state):
                drawn = False
                expect(False, "%s: %s set to %s: %s" % (look, LABELS[row], seen[-1], "; ".join(
                    read_list(rows, state["look"], colours, names, state))))
        at = turns.index(start)
        wanted = [turns[(at + 1 + i) % len(turns)] for i in range(len(turns))]
        expect(seen == wanted, "%s: Enter and → take %s through %s" % (look, LABELS[row], ", ".join(map(str, seen))))
        expect(drawn, "%s: every value of %s is drawn as it is set" % (look, LABELS[row]))
        target.key("Left")
        expect(target.info()[FIELD[row]] == turns[at - 1], "%s: ← takes %s the other way" % (look, LABELS[row]))
        target.key("Right")

    # the volume stops at both ends
    state = go_to_row(target, "volume")
    heard = []
    for _ in range(LOUDEST + 1):
        target.key("Left")
        heard.append(target.info()["volume"])
    quietest = target.info()
    _, rows = target.frame()
    expect(quietest["volume"] == 1 and heard[-2:] == [1, 1] and not read_list(rows, look, colours, names, quietest),
           "%s: ← stops at volume 1, and the row says 1 of %d" % (look, LOUDEST))
    for _ in range(LOUDEST + 1):
        target.key("Right")
    loudest = target.info()
    _, rows = target.frame()
    expect(loudest["volume"] == LOUDEST and not read_list(rows, look, colours, names, loudest),
           "%s: → stops at volume %d, and the row says %d of %d" % (look, LOUDEST, LOUDEST, LOUDEST))

    unusual = {"cards": 2, "romaji": "always", "sound": True, "volume": 4, "voice": "male", "typing": False}
    expect(all([set_row(target, row, wanted) for row, wanted in unusual.items()]),
           "%s: every row can be set to something unusual" % look)
    if restart:
        target.restart()
        expect(go_home(target), "%s: after off and on the home screen is there" % look)
        state = target.info()
        kept = {row: state[FIELD[row]] for row in unusual}
        expect(kept == unusual and state["look"] == look,
               "%s: after off and on everything is as it was set: %s" % (look, kept))
        target.open("settings")
    expect(all([set_row(target, row, wanted) for row, wanted in USUAL.items()]),
           "%s: and every row can be set back" % look)
    target.key("Esc")
    target.key("Esc")


def samples(target, look, colours, names, expect):
    """What is heard after a change of volume or voice. Only where the machine tells what it played."""
    target.open("settings")
    go_to_row(target, "volume")
    before = target.info()
    target.key("Right")
    state = target.info()
    expect(state["volume"] == 4 and plays(state) == plays(before), "%s: with the sound off a change of volume "
                                                                     "is silent" % look)
    set_row(target, "sound", True)
    go_to_row(target, "volume")

    def press(key, row_field, wanted, folder, volume, what):
        before = target.info()
        target.key(key)
        state = target.info()
        expect(state[row_field] == wanted and plays(state) == plays(before) + 1 and
               state["played"] == SAMPLE % folder and state["playedAt"] == volume,
               "%s: %s (%s at volume %d, %d played)" % (look, what, state["played"], state["playedAt"],
                                                         plays(state) - plays(before)))

    press("Right", "volume", 5, "f", 5, "one step louder is heard at once, louder")
    press("Right", "volume", 5, "f", 5, "at the loudest → changes nothing and lets it be heard again")
    press("Left", "volume", 4, "f", 4, "with both voices set, the volume is heard in one voice at every step")
    let_time_pass(target)
    expect(plays(target.info()) == plays(before) + 3, "%s: a change of volume is one clip, no second follows" % look)

    go_to_row(target, "voice")
    press("Right", "voice", "female", "f", 4, "female is heard in the woman's voice")
    press("Enter", "voice", "male", "m", 4, "male is heard in the man's voice")
    go_to_row(target, "volume")
    press("Left", "volume", 3, "m", 3, "with the man's voice set, the volume is heard in his voice")
    go_to_row(target, "voice")
    before = target.info()
    press("Right", "voice", "both", "f", 3, "both starts with the woman's voice")
    target.frame()
    state = target.info()
    expect(plays(state) == plays(before) + 2 and state["played"] == SAMPLE % "m",
           "%s: and the man's voice follows when hers has finished" % look)
    press("Left", "voice", "male", "m", 3, "← from both is male, heard in the man's voice")
    before = target.info()
    target.key("Right")
    target.key("Up")
    target.frame()
    let_time_pass(target)
    state = target.info()
    expect(state["voice"] == "both" and plays(state) == plays(before) + 1 and state["played"] == SAMPLE % "f",
           "%s: a key pressed meanwhile keeps the second voice from starting" % look)

    # without a memory card
    if hasattr(target, "card"):
        target.card(False)
        before = target.info()
        _, rows = target.frame()
        wrong = read_list(rows, look, colours, names, before)
        expect(before["values"][ROWS.index("sound")] == "on, no card" and not wrong,
               "%s: with the card out the row Sound says: on, no card %s" % (look, "; ".join(wrong)))
        expect(find16(rows, colours[look]["dim"], "on, no card") is not None,
               "%s: on, no card is on the screen" % look)
        target.key("Left")
        target.key("Down")
        target.key("Right")
        target.frame()
        state = target.info()
        expect(state["volume"] == 2 and state["voice"] == "female" and plays(state) == plays(before),
               "%s: with the card out volume and voice change in silence" % look)
        target.card(True)
        _, rows = target.frame()
        state = target.info()
        expect(state["values"][ROWS.index("sound")] == "on" and
               find16(rows, colours[look]["dim"], "on, no card") is None,
               "%s: with the card in again the row says: on" % look)
    target.key("Esc")
    target.key("Esc")


def answer(target, right):
    """Answers the kana on the screen. Returns (state before, state after)."""
    before = target.info()
    kana = before["kana"]
    target.type(reader.to_romaji(kana) if right else ("zu" if kana != "ず" else "a"))
    target.key("Enter")
    return before, target.info()


def clip_of(state, items, folder):
    deck = state["script"]
    prompt = to_katakana(state["kana"]) if deck == "katakana" else state["kana"]
    return "/audio/%s/%s/%s.wav" % (folder, deck, items[(deck, prompt)])


def kana_quiz(target, look, colours, items, expect):
    """The kana is heard after the answer, not before; / lets it be heard again."""
    _, _, hint = header_colours(look, colours)
    told = plays(target.info()) is not None

    expect(set_all(target, {"sound": True, "volume": 2, "voice": "female"}),
           "%s: sound on, volume 2, the woman's voice" % look)
    target.open("kana")
    if target.info()["script"] != "hiragana":
        target.type(" ")
    start = target.info()
    target.key("Tab")
    target.type("k/")
    target.key("Right")
    target.frame()
    for _ in range(9):
        target.key("Backspace")
    state = target.info()
    expect(state["kanaState"] == "typing" and state["heard"] is False and plays(state) == plays(start),
           "%s: before the answer nothing is heard, whatever is pressed" % look)

    before, state = answer(target, True)
    can_hear = state["heard"]
    if told:
        expect(state["kanaState"] == "right" and state["heard"] is True and plays(state) == plays(before) + 1 and
               state["played"] == clip_of(before, items, "f") and state["playedAt"] == 2,
               "%s: after the answer %s is heard: %s at volume %d" % (look, before["kana"], state["played"],
                                                                     state["playedAt"]))
    if can_hear:
        _, rows = target.frame()
        expect(find16(rows, hint, "/: again") is not None, "%s: the footer says / plays it again" % look)
        for key in ("/", "Right"):
            before = target.info()
            if key == "/":
                target.type(key)
            else:
                target.key(key)
            state = target.info()
            expect(state["kanaState"] == "right" and state["asked"] == before["asked"] and
                   (not told or (plays(state) == plays(before) + 1 and state["played"] == before["played"])),
                   "%s: %s lets it be heard again and stays on the answer" % (look, key if key == "/" else "→"))
    else:
        expect(not told, "%s: the memory card has no clip of this kana, so / is not tried" % look)
    target.type("a")
    state = target.info()
    expect(state["kanaState"] == "typing" and state["asked"] == 1 and state["heard"] is False,
           "%s: another key leads to the next kana" % look)

    # katakana, answered wrongly
    target.type(" ")
    before, state = answer(target, False)
    if told:
        expect(state["kanaState"] == "wrong" and state["heard"] is True and
               state["played"] == clip_of(before, items, "f") and "/katakana/" in state["played"],
               "%s: a wrong answer is followed by the kana too, in katakana from that deck: %s" % (
                   look, state["played"]))
    target.type("a")
    target.type(" ")
    expect(target.info()["script"] == "hiragana", "%s: Space switches back to hiragana" % look)
    target.key("Esc")

    # both voices: they take turns, and the settings have not taken one
    expect(set_all(target, {"voice": "both"}), "%s: both voices" % look)
    target.open("kana")
    before, state = answer(target, True)
    if told:
        first = state["played"]
        target.type("/")
        second = target.info()["played"]
        expect({first, second} == {clip_of(before, items, "f"), clip_of(before, items, "m")},
               "%s: with both voices / brings the other voice: %s, then %s" % (look, first, second))
        if hasattr(target, "card"):
            expect(first == clip_of(before, items, "f"),
                   "%s: what was heard in the settings took no turn: the woman's voice is first" % look)
    target.key("Esc")

    # without sound
    expect(set_all(target, {"sound": False}), "%s: sound off" % look)
    target.open("kana")
    before, state = answer(target, True)
    _, rows = target.frame()
    expect(state["kanaState"] == "right" and state["heard"] is False and plays(state) == plays(before),
           "%s: with the sound off the answer is marked in silence" % look)
    expect(find16(rows, hint, "/: again") is None, "%s: and the footer does not offer /" % look)
    target.type("/")
    state = target.info()
    expect(state["kanaState"] == "typing" and state["asked"] == 1, "%s: / is then a key like any other" % look)
    target.key("Esc")

    if hasattr(target, "card"):
        expect(set_all(target, {"sound": True}), "%s: sound on" % look)
        target.card(False)
        target.open("kana")
        before, state = answer(target, True)
        expect(state["heard"] is False and plays(state) == plays(before),
               "%s: with the card out the answer is marked in silence" % look)
        target.card(True)
        target.key("Esc")
        expect(set_all(target, {"sound": False}), "%s: sound off again" % look)


def choose_look(target, wanted):
    return set_all(target, {"look": wanted}) and target.info()["look"] == wanted


def play(target, look, colours, names, items, expect, restart):
    expect(choose_look(target, look), "%s: the look is set and the home screen is back" % look)
    expect(set_all(target, USUAL), "%s: the rows are set to what a new device has" % look)
    walk(target, look, colours, names, expect)
    change(target, look, colours, names, expect, restart)
    if plays(target.info()) is not None:
        samples(target, look, colours, names, expect)
        expect(set_all(target, USUAL), "%s: the rows are set back" % look)
    kana_quiz(target, look, colours, items, expect)
    expect(go_home(target), "%s: the home screen is back" % look)


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    colours, _ = reader.themes()
    names = look_names()
    items = kana_items()
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
        kept = False
        try:
            print("device: %s, look %s, %d bytes free, largest block %d" % (
                before["board"], before["look"], before["heapFree"], before["heapLargestBlock"]), flush=True)
            if plays(before) is None:
                print("device: it does not tell what it plays, so what is heard is not checked", flush=True)
            expect(go_home(device), "device: Esc leads to the home screen")
            kept = device.keep()
            expect(kept, "device: settings and progress are kept aside")
            if kept:
                for index, look in enumerate(looks):
                    play(device, look, colours, names, items, expect, restart=(index == 0))
                    print("%s done" % look, flush=True)
        finally:
            if kept:
                expect(device.back(), "device: settings and progress are put back")
                after = device.info()
                same = all(after[FIELD[row]] == before[FIELD[row]] for row in ROWS)
                expect(same, "device: every setting is as it was before (look %s, volume %d, voice %s)" % (
                    after["look"], after["volume"], after["voice"]))
                expect(go_home(device), "device: left on the home screen")
                lost = before["heapFree"] - after["heapFree"]
                expect(lost < 8192, "device: memory afterwards is within 8 KB of before (%d bytes less, "
                                    "lowest ever %d)" % (lost, after["heapLowest"]))
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=300 + reader.LOOKS.index(look))
            try:
                play(sim, look, colours, names, items, expect, restart=True)
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
