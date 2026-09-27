#!/usr/bin/env python3
"""Plays the home screen, the menu, the list of decks and the page of keys, and checks them.

    python3 tools/menu_check.py                           # in the simulator, all four looks
    python3 tools/menu_check.py rpg                       # one look
    <PlatformIO's python> tools/menu_check.py --device    # on a Cardputer over USB

What is checked, in every look:
  home   the deck the course stands at, how far it is seen, the row of boxes with one box for
         each deck, what the next sitting brings, and what the buddy says with its meaning; Tab
         opens the menu, Esc and Backspace do nothing, any other key starts the course; after a
         day with answers the next start asks for the day, and only Enter and Space answer
  menu   the seven entries under their ids, four rows at a time, each with its number; what the
         rows say at their right end; the arrows go round; every number opens its screen; keys
         that mean nothing do nothing
  decks  every deck in the order of the course with what was seen, of how many, and what is
         due; the chosen row stays in view; Enter starts a sitting from the chosen deck
  keys   every row of the page; any key leads back

In the simulator, once: a whole deck is learnt, after which the course stands at the next deck
and the learnt deck has nothing to start; and the memory card is taken out.

The app says what it shows (`info`); the pictures are read to see that it is really drawn. On a
device the owner's settings and progress are kept aside first and put back at the end.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

HOME, MENU, KANA, SETTINGS, CARDS, SUMMARY, KEYS, DECKS, CHART, GUIDE = range(10)

MENU_ENTRIES = [("course", "Course", CARDS), ("decks", "Decks", DECKS), ("kana", "Kana quiz", KANA),
                ("chart", "Kana chart", CHART), ("guide", "Sounds", GUIDE), ("keys", "Keys", KEYS),
                ("settings", "Settings", SETTINGS)]
MENU_ROWS = 4
DECK_ROWS = 5

KEY_ROWS = [("Enter", "answer, next"), ("Tab", "help"), ("/", "hear again"), ("esc", "back (Fn and `)"),
            ("Button", "back (on the edge)"), ("; . , /", "up down left right")]

LARGE = [("efontJA_24", 1)]
SMALL = [("efontJA_16", 1)]


class Check:
    def __init__(self):
        self.passed = []
        self.failed = []

    def expect(self, condition, message):
        (self.passed if condition else self.failed).append(message)
        if not condition:
            print("FAIL " + message, flush=True)
        return condition


def deck_table():
    """The decks as the firmware has them, in the order of the course: id, name, cards, stage."""
    source = open(os.path.join(reader.ROOT, "lib", "core", "deck_data.cpp"), encoding="utf-8").read()
    table = source[source.index("kDeckTable[]"):]
    table = table[:table.index("};")]
    decks = [{"id": i, "name": name, "cards": int(cards), "stage": int(stage)} for i, name, cards, stage in
             re.findall(r'\{"([^"]+)", "[^"]*", "([^"]*)", \w+, (\d+), (\d+)\}', table)]
    if not decks:
        raise RuntimeError("could not read the decks from lib/core/deck_data.cpp")
    return sorted(decks, key=lambda deck: deck["stage"])


def buddy_lines():
    """id -> (what the buddy says, what it means) from content/buddy.tsv."""
    lines = {}
    for line in open(os.path.join(reader.ROOT, "content", "buddy.tsv"), encoding="utf-8"):
        cells = line.rstrip("\n").rstrip("\r").split("\t")
        if line.startswith("#") or len(cells) < 4 or cells[0] == "id":
            continue
        lines[cells[0]] = (cells[2], cells[3])
    return lines


def capitalised(text):
    return text[:1].upper() + text[1:]


def find_all(rows, colour, text, faces):
    """Every place where the text stands in that colour: a list of (left, top).

    As find_anywhere of app_reader, which stops at the first place.
    """
    seen = reader.coloured(rows, colour, 0, 0, len(rows[0]), len(rows))
    places = []
    for font_name, scale in faces:
        points, w = reader.mask(text, font_name)
        if not points:
            continue
        points = reader.scaled(points, scale)
        height = reader.font(font_name).height * scale
        anchor = min(points, key=lambda p: (p[1], p[0]))
        for (sx, sy) in seen:
            left, top = sx - anchor[0], sy - anchor[1]
            if all((x + left, y + top) in seen for (x, y) in points):
                inside = sum(1 for (x, y) in seen if left <= x < left + w * scale and top <= y < top + height)
                if inside == len(points):
                    places.append((left, top))
    return sorted(places, key=lambda place: (place[1], place[0]))


def drawn(rows, colour, text, faces=SMALL):
    return reader.find_anywhere(rows, colour, text, faces) is not None


def picture(target):
    """The picture first: drawing is what brings the list into view, and the app says where it stands."""
    _, rows = target.frame()
    return rows, target.info()


def go_home(target):
    for _ in range(5):
        if target.info()["screen"] == HOME:
            return True
        target.key("Esc")
    return target.info()["screen"] == HOME


def set_look(target, wanted):
    """From the home screen: sets the look in the settings and comes back."""
    current = target.look()
    target.open("settings")  # the first row is the look
    for _ in range((reader.LOOKS.index(wanted) - reader.LOOKS.index(current)) % len(reader.LOOKS)):
        target.key("Right")
    go_home(target)
    state = target.info()
    return state["screen"] == HOME and state["look"] == wanted


def learn(target, items, deck=""):
    """Plays one sitting, from the deck or of the course, with every answer right. Ends at home."""
    if not target.sitting(deck):
        return False
    for _ in range(200):
        state = target.info()
        if state["screen"] != CARDS:
            break
        item = items.get(state.get("card"))
        if item is None or state.get("cardState") in ("meet", "marked", "note"):
            target.key("Enter")
        else:
            target.type(reader.to_romaji(item["reading"]))
            target.key("Enter")
    for _ in range(3):
        if target.info()["screen"] in (CARDS, HOME):
            break
        target.type(" ")
    return go_home(target)


def boxes(rows, colours, area):
    """The row of boxes on the home screen: (width, filled) for each box, and the lines of the
    picture it stands on. None if there is no such row.

    A line of the picture belongs to it when, within the content, what is drawn in the colours
    of the boxes falls into pieces of one width.
    """
    found = {}
    left, top, width, height = area
    for y in range(top, top + height):
        runs = []
        x = left
        while x < left + width:
            if rows[y][x] in (colours["faint"], colours["good"]):
                start = x
                while x < left + width and rows[y][x] in (colours["faint"], colours["good"]):
                    x += 1
                filled = sum(1 for at in range(start, x) if rows[y][at] == colours["good"])
                runs.append((x - start, filled))
            else:
                x += 1
        if len(runs) > 1 and len({run[0] for run in runs}) == 1 and runs[0][0] >= 8:
            found.setdefault(tuple(runs), []).append(y)
    if len(found) != 1:
        return None
    runs, lines = next(iter(found.items()))
    return (list(runs), lines) if len(lines) >= 4 else None


def stands_free(rows, colours, place, text):
    """Whether a line of text stands on the plain ground: nothing else is drawn within its box."""
    if place is None:
        return False
    left, top = place[0], place[1]
    allowed = (colours["bg"], colours["faint"])  # the notebook has ruled lines
    inked = {rows[y][x] for y in range(top, top + 16) for x in range(left, left + reader.width(text, "efontJA_16"))
             if rows[y][x] not in allowed}
    return len(inked) == 1


class Context:
    def __init__(self):
        self.colours, self.areas = reader.themes()
        self.items = reader.decks()
        self.decks = deck_table()
        self.buddy = buddy_lines()
        self.deck_names = {deck["id"]: capitalised(deck["name"]) for deck in self.decks}


def check_home(target, look, context, check, when):
    rows, state = picture(target)
    colours = context.colours[look]
    said = "%s, %s: " % (look, when)
    if not check.expect(state["screen"] == HOME and state["asksForDay"] is False, said + "the home screen is shown"):
        return state

    ids = [deck["id"] for deck in context.decks]
    steps = state["steps"]
    check.expect(len(steps) == len(ids), said + "the course has %d steps, one for each deck (%d)" % (
        len(ids), len(steps)))
    if state["course"]:
        at = ids.index(state["course"])
        name = context.deck_names[state["course"]]
        check.expect([state["deckSeen"], state["deckTotal"]] == steps[at],
                     said + "the figures are those of %s (%d of %d)" % (name, state["deckSeen"], state["deckTotal"]))
    else:
        name = "Every card seen"
    named = reader.find_anywhere(rows, colours["ink"], name, SMALL)
    check.expect(named is not None, said + "the deck of the course is named: %s" % name)
    figures = "%d of %d" % (state["deckSeen"], state["deckTotal"])
    counted = reader.find_anywhere(rows, colours["dim"], figures, SMALL)
    check.expect(counted is not None and named is not None and counted[1] == named[1] and
                 counted[0] >= named[0] + reader.width(name, "efontJA_16") + 8,
                 said + "how far it is seen stands beside the name: %s" % figures)

    found = boxes(rows, colours, context.areas[look])
    lines = found[1] if found else []
    if check.expect(found is not None and len(found[0]) == len(steps),
                    said + "the row has a box for each deck (%s)" % (len(found[0]) if found else "no row")):
        wanted = []
        for (width, _), (seen, total) in zip(found[0], steps):
            filled = width * seen // total if total else 0
            wanted.append(max(filled, 2) if seen else 0)
        check.expect([filled for _, filled in found[0]] == wanted,
                     said + "each box is filled as far as its deck is seen (%s, expected %s)" % (
                         [filled for _, filled in found[0]], wanted))

    due, new = state["due"], state["new"]
    if due and new:
        words = "Next: %d to review, %d new" % (due, new)
    elif due:
        words = "Next: %d to review" % due
    elif new:
        words = "Next: %d new" % new
    else:
        words = "Nothing waits today"
    brings = reader.find_anywhere(rows, colours["ink"] if due or new else colours["dim"], words, SMALL)
    check.expect(brings is not None, said + "what a key brings is drawn: %s" % words)

    line = context.buddy.get(state["says"])
    if not check.expect(line is not None, said + "the buddy says one of its lines (%s)" % state["says"]):
        return state
    spoken = reader.find_anywhere(rows, colours["bubbleInk"], line[0], SMALL)
    check.expect(spoken is not None and rows[spoken[1] + 8][spoken[0] - 2] == colours["bubble"],
                 said + "the buddy's line is drawn in its bubble: %s" % line[0])
    meant = reader.find_anywhere(rows, colours["dim"], line[1], SMALL)
    check.expect(meant is not None, said + "and under it what it means: %s" % line[1])

    # from top to bottom, no line in the way of another, all of it within the content
    if spoken and meant and named and lines and brings:
        _, top, _, height = context.areas[look]
        tops = [spoken[1], meant[1], named[1]]
        check.expect(top <= tops[0] and all(a + 16 <= b for a, b in zip(tops, tops[1:])) and
                     tops[-1] + 16 <= min(lines) and max(lines) < brings[1] and brings[1] + 16 <= top + height,
                     said + "the lines stand one under the other (%s, boxes %d to %d, %d, content %d to %d)" % (
                         tops, min(lines), max(lines), brings[1], top, top + height))
        for place, words_there in ((meant, line[1]), (named, name), (counted, figures), (brings, words)):
            check.expect(stands_free(rows, colours, place, words_there),
                         said + "nothing is drawn across %r" % words_there)
    return state


def check_home_keys(target, look, check):
    for key in ("Esc", "Backspace"):
        target.key(key)
        check.expect(target.info()["screen"] == HOME, "%s: %s on the home screen does nothing" % (look, key))
    target.key("Tab")
    check.expect(target.info()["screen"] == MENU, "%s: Tab on the home screen opens the menu" % look)
    target.key("Tab")
    check.expect(target.info()["screen"] == HOME, "%s: Tab in the menu leads home" % look)
    for name, press in (("a letter", lambda: target.type("x")), ("Enter", lambda: target.key("Enter")),
                        ("Space", lambda: target.type(" "))):
        press()
        state = target.info()
        check.expect(state["screen"] == CARDS and bool(state.get("card")),
                     "%s: %s on the home screen starts the course" % (look, name))
        target.key("Esc")
        check.expect(target.info()["screen"] == HOME, "%s: Esc before the first answer leads home" % look)


def check_menu(target, look, context, check):
    colours = context.colours[look]
    ids = [entry[0] for entry in MENU_ENTRIES]
    go_home(target)
    before = target.info()
    target.key("Tab")
    rows, state = picture(target)
    if not check.expect(state["screen"] == MENU and state.get("menu") == ids,
                        "%s: the menu has the entries %s" % (look, ", ".join(ids))):
        return

    # what the rows say at their right end
    due, new = before["due"], before["new"]
    waits = ("%d due, %d new" % (due, new) if due and new else "%d due" % due if due else
             "%d new" % new if new else "done")
    check.expect(state["says"][0] == waits, "%s: the course says what waits: %s (%s)" % (look, waits, state["says"][0]))
    seen = "%d of %d" % (before["seen"], sum(total for _, total in before["steps"]))
    check.expect(state["says"][1] == seen, "%s: the decks say what was seen: %s (%s)" % (look, seen, state["says"][1]))
    silent = "no card" if not before["memoryCard"] else "" if before["sound"] else "sound off"
    check.expect(state["says"][4] == silent, "%s: the sounds say why nothing would be heard: %r (%r)" % (
        look, silent, state["says"][4]))

    # every row, four at a time, with the chosen one in view
    count = len(ids)
    for step in range(count + 1):
        rows, state = picture(target)
        chosen, first = state["chosen"], state["first"]
        check.expect(0 <= first <= chosen < first + MENU_ROWS, "%s: the chosen row %d of the menu is in view" % (
            look, chosen + 1))
        for index, (_, label, _) in enumerate(MENU_ENTRIES):
            ink = colours["rowInk"] if index == chosen else colours["ink"]
            places = find_all(rows, ink, label, LARGE)
            if not first <= index < first + MENU_ROWS:
                check.expect(not places, "%s: %s is out of view and not drawn" % (look, label))
                continue
            if not check.expect(len(places) == 1, "%s: %s is drawn large, once" % (look, label)):
                continue
            left, top = places[0]
            marked = sum(1 for x in range(len(rows[0])) if rows[top + 12][x] == colours["row"])
            check.expect((marked > 100) == (index == chosen),
                         "%s: %s is %s" % (look, label, "marked as chosen" if index == chosen else "not marked"))
            aside = colours["accent"] if index == chosen else colours["dim"]
            numbers = [place for place in find_all(rows, aside, str(index + 1), SMALL)
                       if place[0] < left and abs(place[1] - top - 5) <= 1]
            check.expect(len(numbers) == 1, "%s: %s has its number %d in front" % (look, label, index + 1))
            says = state["says"][index]
            if says:
                there = [place for place in find_all(rows, aside, says, SMALL)
                         if place[0] > left and abs(place[1] - top - 5) <= 1]
                check.expect(len(there) == 1, "%s: %s says %r at its right end" % (look, label, says))
        target.key("Down")
    check.expect(target.info()["chosen"] == (state["chosen"] + 1) % count, "%s: Down goes round the menu" % look)

    # keys that mean nothing
    for _ in range(count):
        if target.info()["chosen"] == 0:
            break
        target.key("Down")
    target.key("Up")
    check.expect(target.info()["chosen"] == count - 1, "%s: Up on the first row leads to the last" % look)
    target.key("Down")
    target.type("890az")
    state = target.info()
    check.expect(state["screen"] == MENU and state["chosen"] == 0,
                 "%s: numbers without an entry and letters do nothing in the menu" % look)

    # every way in and out
    for index, (name, label, screen) in enumerate(MENU_ENTRIES):
        go_home(target)
        target.key("Tab")
        target.type(str(index + 1))
        check.expect(target.info()["screen"] == screen, "%s: %d opens %s" % (look, index + 1, label))
        go_home(target)
        target.open(name)
        check.expect(target.info()["screen"] == screen, "%s: Enter on %s opens it" % (look, label))
    go_home(target)
    target.key("Tab")
    chosen = target.info()["chosen"]
    target.key("Right")
    check.expect(target.info()["screen"] == MENU_ENTRIES[chosen][2], "%s: Right opens the chosen entry" % look)
    for key in ("Esc", "Backspace", "Left", "Tab"):
        go_home(target)
        target.key("Tab")
        target.key(key)
        check.expect(target.info()["screen"] == HOME, "%s: %s in the menu leads home" % (look, key))


def check_decks(target, look, context, check, when):
    colours = context.colours[look]
    said = "%s, %s: " % (look, when)
    ids = [deck["id"] for deck in context.decks]
    go_home(target)
    level = target.info()["level"]
    target.open("decks")
    rows, state = picture(target)
    if not check.expect(state["screen"] == DECKS and state.get("decks") == ids,
                        said + "the decks stand in the order of the course: %s" % ", ".join(ids)):
        return state
    if level == 3:
        check.expect(state["deckTotal"] == [deck["cards"] for deck in context.decks],
                     said + "every deck counts all its cards %s" % state["deckTotal"])
    check.expect(drawn(rows, colours["headInk"], "seen") and drawn(rows, colours["headInk"], "due"),
                 said + "the columns are named seen and due")

    count = len(ids)
    for step in range(count + 1):
        rows, state = picture(target)
        chosen, first = state["chosen"], state["first"]
        check.expect(0 <= first <= chosen < first + DECK_ROWS, said + "the chosen deck %d is in view" % (chosen + 1))
        for index, deck in enumerate(ids):
            name = context.deck_names[deck]
            if not first <= index < first + DECK_ROWS:
                continue
            ink = colours["rowInk"] if index == chosen else colours["ink"]
            # a name can stand within a longer one: Katakana, Katakana words
            places = [place for place in find_all(rows, ink, name, SMALL)]
            rivals = [other for other in context.deck_names.values() if other != name and other.startswith(name)]
            for rival in rivals:
                taken = find_all(rows, ink, rival, SMALL)
                places = [place for place in places if place not in taken]
            if not check.expect(len(places) == 1, said + "%s is drawn, once" % name):
                continue
            left, top = places[0]
            marked = sum(1 for x in range(len(rows[0])) if rows[top + 8][x] == colours["row"])
            check.expect((marked > 100) == (index == chosen),
                         said + "%s is %s" % (name, "marked as chosen" if index == chosen else "not marked"))
            figures = "%d/%d" % (state["deckSeen"][index], state["deckTotal"][index])
            aside = colours["rowInk"] if index == chosen else colours["dim"]
            seen = [place for place in find_all(rows, aside, figures, SMALL) if place[1] == top and place[0] > left]
            check.expect(len(seen) == 1, said + "%s shows %s" % (name, figures))
            due = state["deckDue"][index]
            aside = colours["accent"] if due else colours["dim"]
            waiting = [place for place in find_all(rows, aside, str(due), SMALL)
                       if place[1] == top and seen and place[0] > seen[0][0] + reader.width(figures, "efontJA_16")]
            check.expect(len(waiting) == 1, said + "%s shows that %d are due" % (name, due))
        target.key("Down")
    check.expect(target.info()["chosen"] == (state["chosen"] + 1) % count, said + "Down goes round the decks")
    return state


def check_decks_keys(target, look, context, check):
    ids = [deck["id"] for deck in context.decks]
    go_home(target)
    target.open("decks")
    for _ in range(len(ids)):
        if target.info()["chosen"] == 0:
            break
        target.key("Down")
    target.key("Up")
    check.expect(target.info()["chosen"] == len(ids) - 1, "%s: Up on the first deck leads to the last" % look)
    target.type("x1 ")
    state = target.info()
    check.expect(state["screen"] == DECKS and state["chosen"] == len(ids) - 1,
                 "%s: letters and numbers do nothing in the decks" % look)
    for key in ("Esc", "Backspace", "Left", "Tab"):
        go_home(target)
        target.open("decks")
        target.key(key)
        check.expect(target.info()["screen"] == MENU, "%s: %s in the decks leads to the menu" % (look, key))

    for index, deck in enumerate(ids):
        go_home(target)
        target.open("decks")
        for _ in range(len(ids)):
            if target.info()["chosen"] == index:
                break
            target.key("Down")
        target.key("Enter")
        state = target.info()
        item = context.items.get(state.get("card"))
        check.expect(state["screen"] == CARDS and item is not None and item["deck"] == deck,
                     "%s: Enter on %s starts a sitting with a card of it (%s)" % (
                         look, context.deck_names[deck], state.get("card")))
    go_home(target)


def check_keys(target, look, context, check):
    colours = context.colours[look]
    go_home(target)
    target.open("keys")
    rows, state = picture(target)
    if not check.expect(state["screen"] == KEYS, "%s: the menu leads to the page of keys" % look):
        return
    for key, does in KEY_ROWS:
        keys = find_all(rows, colours["accent"], key, SMALL)
        # "/" stands in "; . , /" as well
        tops = {top for _, top in find_all(rows, colours["ink"], does, SMALL)}
        check.expect(len(tops) == 1 and any(top in tops for _, top in keys),
                     "%s: the page of keys has the row %s: %s" % (look, key, does))
    target.type("x")
    check.expect(target.info()["screen"] == MENU, "%s: any key on the page of keys leads to the menu" % look)


def check_new_day(target, look, context, check):
    colours = context.colours[look]
    before = target.info()
    target.restart()
    rows, state = picture(target)
    if not check.expect(state["screen"] == HOME and state["asksForDay"] is True and state["look"] == look,
                        "%s: after a day with answers the next start asks for the day" % look):
        return
    check.expect(drawn(rows, colours["bubbleInk"], "New day?", LARGE), "%s: New day? is drawn large" % look)
    check.expect(drawn(rows, colours["bubbleDim"], "あたらしい ひ？"), "%s: and in kana under it" % look)
    name = context.deck_names.get(state["course"], "Every card seen")
    check.expect(drawn(rows, colours["ink"], name), "%s: the deck of the course is named under the question" % look)
    target.type("xq")
    target.key("Tab")
    state = target.info()
    check.expect(state["screen"] == HOME and state["asksForDay"] is True and state["day"] == before["day"],
                 "%s: only an answer ends the question for the day" % look)
    target.type(" ")
    state = target.info()
    check.expect(state["asksForDay"] is False and state["day"] == before["day"], "%s: Space keeps the day" % look)
    target.restart()
    target.key("Enter")
    state = target.info()
    check.expect(state["asksForDay"] is False and state["day"] == before["day"] + 1 and
                 state["answeredToday"] == 0, "%s: Enter starts day %d" % (look, before["day"] + 1))


def check_look(target, look, context, check):
    check.expect(target.fresh(), "%s: progress starts empty" % look)
    check.expect(set_look(target, look), "%s: the look is set, the home screen is back" % look)

    state = check_home(target, look, context, check, "at the start")
    check.expect(state["course"] == context.decks[0]["id"] and state["deckSeen"] == 0,
                 "%s: the course starts at %s with nothing seen" % (look, context.deck_names[context.decks[0]["id"]]))
    check_home_keys(target, look, check)
    check_menu(target, look, context, check)
    check_decks(target, look, context, check, "at the start")
    check_decks_keys(target, look, context, check)
    check_keys(target, look, context, check)

    # a sitting of the course and one from the last deck: two boxes of the course fill
    last = context.decks[-1]["id"]
    check.expect(learn(target, context.items), "%s: a sitting of the course is played" % look)
    check.expect(learn(target, context.items, last), "%s: a sitting from %s is played" % (
        look, context.deck_names[last]))
    state = check_home(target, look, context, check, "after two sittings")
    check.expect(state["steps"][0][0] > 0 and state["steps"][-1][0] > 0 and state["deckSeen"] == state["steps"][0][0],
                 "%s: both sittings count in the course (%s)" % (look, state["steps"]))
    decks = check_decks(target, look, context, check, "after two sittings")
    check.expect(decks["deckSeen"] == [seen for seen, _ in state["steps"]],
                 "%s: the decks show what the home screen counts (%s)" % (look, decks["deckSeen"]))
    go_home(target)

    check_new_day(target, look, context, check)
    state = check_home(target, look, context, check, "on the next day")
    check.expect(state["due"] > 0, "%s: what was learnt is due on the next day (%d)" % (look, state["due"]))
    check_menu(target, look, context, check)
    check_decks(target, look, context, check, "on the next day")
    go_home(target)


def check_whole_deck(target, look, context, check):
    """Simulator only: learns the first deck to its end, all in one day."""
    first, second = context.decks[0], context.decks[1]
    name = context.deck_names[first["id"]]
    target.fresh()
    set_look(target, look)
    for _ in range(40):
        state = target.info()
        if state["course"] != first["id"]:
            break
        learn(target, context.items, first["id"])
    state = check_home(target, look, context, check, "with %s learnt" % name)
    check.expect(state["course"] == second["id"] and state["steps"][0] == [first["cards"], first["cards"]],
                 "%s: with every card of %s seen the course stands at %s" % (
                     look, name, context.deck_names[second["id"]]))
    decks = check_decks(target, look, context, check, "with %s learnt" % name)
    go_home(target)
    target.open("decks")
    for _ in range(len(context.decks)):
        if target.info()["chosen"] == 0:
            break
        target.key("Down")
    if check.expect(decks["deckDue"][0] == 0, "%s: learnt in one day, nothing of %s is due (%d)" % (
            look, name, decks["deckDue"][0])):
        target.key("Enter")
        check.expect(target.info()["screen"] == DECKS, "%s: a deck with nothing to ask starts no sitting" % look)
    go_home(target)

    target.card(False)
    target.key("Tab")
    rows, state = picture(target)
    check.expect(state["says"][4] == "no card", "%s: without the memory card the sounds say so" % look)
    target.card(True)
    go_home(target)


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    context = Context()
    check = Check()
    check.expect(len(context.decks) > 1 and len(context.items) > 100,
                 "decks read: %d decks, %d cards" % (len(context.decks), len(context.items)))

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
                go_home(device)
                check_look(device, look, context, check)
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
        for index, look in enumerate(looks):
            sim = Simulator(seed=40 + reader.LOOKS.index(look))
            try:
                check_look(sim, look, context, check)
                if index == 0:
                    check_whole_deck(sim, look, context, check)
            finally:
                sim.close()

    print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
