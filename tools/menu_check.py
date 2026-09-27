#!/usr/bin/env python3
"""Plays the home screen, the menu, the list of decks and the page of keys, and checks them.

    python3 tools/menu_check.py                           # in the simulator, all four looks
    python3 tools/menu_check.py rpg                       # one look
    <PlatformIO's python> tools/menu_check.py --device    # on a Cardputer over USB

What is checked, in every look:
  home   the buddy, what it says and what that means; the deck the course stands at, how far
         it is seen, the row of boxes with one box for each deck and a line around the one
         being learnt; what the next sitting brings, which is then played and counted; the
         hints at the bottom; Tab opens the menu, Esc and Backspace do nothing, any other key
         starts the course; after a day with answers the next start asks for the day, and only
         Enter and Space answer
  menu   the seven entries under their ids, four rows at a time, each with its number; what the
         rows say at their right end; the mark that shows where the list stands; the arrows go
         round; every number opens its screen; keys that mean nothing do nothing
  decks  every deck in the order of the course with what was seen, of how many, what is due,
         and a bar filled as far as it is seen; the chosen row stays in view; Enter starts a
         sitting from the chosen deck, and the hint says whether it would
  keys   every row of the page; any key leads back

In the simulator, in every look, the course is played to its end: where new cards come from
three decks in turn, when every card was seen and nothing waits, on the day after with more due
than a sitting holds, and with the level lowered so that cards learnt before no longer count.
Once, the memory card is taken out.

The app says what it shows (`info`); the pictures are read to see that it is really drawn. On a
device the owner's settings and progress are kept aside first and put back at the end.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from cardputer_screen import rgb565  # noqa: E402
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

SITTING = 12                        # cards in a sitting at most
FOOTER = 112                        # the hints stand below this line in every look
BUDDY = rgb565((0xC8, 0x28, 0x24))  # the red of the daruma, from lib/ui/widgets.cpp


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
                # nothing else in that colour within the box of the text; on a ground of that
                # colour the count is over after a few points
                inside = 0
                for place in ((x, y) for y in range(top, top + height) for x in range(left, left + w * scale)):
                    if place in seen:
                        inside += 1
                        if inside > len(points):
                            break
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


def play(target, items, deck="", key=None):
    """Plays one sitting with every answer right and ends at home. The sitting is one from the
    deck, or of the course; with a key it is started from the home screen by that key.

    Returns what the sitting held, {"review": cards asked again, "new": cards met for the first
    time}, or None if it did not start or did not lead home.
    """
    if key is None:
        if not target.sitting(deck):
            return None
    else:
        target.key(key)
    met = {}
    for _ in range(200):
        state = target.info()
        if state["screen"] != CARDS:
            break
        card = state.get("card")
        if card and card not in met:
            met[card] = "new" if state.get("cardState") in ("probe", "meet", "copy") else "review"
        item = items.get(card)
        if item is None or state.get("cardState") in ("meet", "marked", "note"):
            target.key("Enter")
        else:
            target.type(reader.to_romaji(item["reading"]))
            target.key("Enter")
    if not met:
        return None
    for _ in range(3):
        if target.info()["screen"] in (CARDS, HOME):
            break
        target.type(" ")
    if not go_home(target):
        return None
    return {kind: sum(1 for value in met.values() if value == kind) for kind in ("review", "new")}


def learn(target, items, deck=""):
    return play(target, items, deck) is not None


def set_level(target, wanted):
    """From the home screen: sets how much the cards ask for (1 to 3) and comes back."""
    target.open("settings")
    target.key("Down")  # the second row
    for _ in range(3):
        if target.info()["level"] == wanted:
            break
        target.key("Right")
    target.key("Up")  # set_look counts on the first row
    go_home(target)
    state = target.info()
    return state["screen"] == HOME and state["level"] == wanted


def counted_by_decks(target):
    """From the home screen: what the list of decks counts, (seen, total, due) for each deck."""
    state = target.info()
    if state["screen"] != HOME or state.get("asksForDay"):
        return []
    target.open("decks")
    decks = target.info()
    go_home(target)
    if decks["screen"] != DECKS:
        return []
    return list(zip(decks["deckSeen"], decks["deckTotal"], decks["deckDue"]))


def in_footer(rows, text):
    """Whether the hint stands at the bottom of the screen, in whatever colour the look gives it."""
    band = rows[FOOTER:]
    return any(find_all(band, colour, text, SMALL) for colour in {pixel for row in band for pixel in row})


def track(rows, colours, x):
    """The mark at the right edge that shows where a list stands, read in the column x: (top
    and length of the track, top and length of the piece that moves). None if there is none.
    """
    shades = (colours["faint"], colours["dim"])
    # the ruled lines of the notebook have the colour of the track, but do not end beside it
    lines = [y for y in range(FOOTER + 8) if rows[y][x] in shades and rows[y][x - 3] not in shades]
    piece = [y for y in range(FOOTER + 8) if rows[y][x] == colours["dim"]]
    if len(lines) < 20 or not piece or piece[-1] - piece[0] + 1 != len(piece):
        return None
    return (lines[0], lines[-1] - lines[0] + 1, piece[0], len(piece))


def check_track(rows, colours, area, shown, count, first, check, said):
    """The mark stands in the last three columns of the content, as long as the part of the
    list that is shown, as far down as the list has moved."""
    found = [track(rows, colours, area[0] + area[2] - 1 - n) for n in range(3)]
    if not check.expect(found[0] is not None and found[0] == found[1] == found[2],
                        said + "a mark at the right edge shows where the list stands"):
        return
    start, height, top, length = found[0]
    check.expect(length == height * shown // count and top == start + (height - length) * first // (count - shown),
                 said + "the mark stands at row %d of %d (from %d, %d long, in a track from %d, %d long)" % (
                     first + 1, count, top, length, start, height))


def boxes(rows, colours, area):
    """The row of boxes on the home screen: (width, filled, left) for each box, and the lines of
    the picture it stands on. None if there is no such row.

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
                runs.append((x - start, filled, start))
            else:
                x += 1
        if len(runs) > 1 and len({run[0] for run in runs}) == 1 and runs[0][0] >= 8:
            found.setdefault(tuple(runs), []).append(y)
    if len(found) != 1:
        return None
    runs, lines = next(iter(found.items()))
    return (list(runs), lines) if len(lines) >= 4 else None


def framed(rows, colours, box, lines):
    """Whether a box of the home screen has a line around it."""
    width, _, left = box
    ink = colours["ink"]
    sides = all(rows[y][left - 1] == ink and rows[y][left + width] == ink for y in lines)
    return sides and all(rows[min(lines) - 1][x] == ink and rows[max(lines) + 1][x] == ink
                         for x in range(left, left + width))


def bar_under(rows, colours, left, top):
    """The bar under a row of the decks, which begins under the first letter of the name:
    (width, filled). None if there is none."""
    shades = (colours["faint"], colours["good"])
    for y in range(top + 14, top + 21):
        if rows[y][left - 1] in shades:
            continue  # a ruled line of the notebook
        x = left
        while x < len(rows[0]) and rows[y][x] in shades:
            x += 1
        if x - left >= 100:
            return x - left, sum(1 for at in range(left, x) if rows[y][at] == colours["good"])
    return None


def next_words(state):
    """What the home screen says the next sitting brings, from what the app counts."""
    due, review, new = state["dueToday"], state["nextReview"], state["nextNew"]
    if review and new:
        return "Next: %d to review, %d new" % (review, new)
    if review and due > review:
        return "Next: %d of %d to review" % (review, due)
    if review:
        return "Next: %d to review" % review
    if new:
        return "Next: %d new" % new
    return "Nothing waits today"


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
    decks = counted_by_decks(target)
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
        for (width, _, _), (seen, total) in zip(found[0], steps):
            filled = width * seen // total if total else 0
            wanted.append(max(filled, 2) if seen else 0)
        check.expect([filled for _, filled, _ in found[0]] == wanted,
                     said + "each box is filled as far as its deck is seen (%s, expected %s)" % (
                         [filled for _, filled, _ in found[0]], wanted))
        around = [ids[index] for index, box in enumerate(found[0]) if framed(rows, colours, box, lines)]
        check.expect(around == ([state["course"]] if state["course"] else []),
                     said + "the box of the deck being learnt has a line around it, no other (%s)" % (
                         ", ".join(around) or "none"))

    # what the next sitting brings: counted as the decks count, and no more than a sitting holds
    due, review, new = state["dueToday"], state["nextReview"], state["nextNew"]
    waits = bool(review or new)
    check.expect(due == sum(deck[2] for deck in decks) and review == min(due, SITTING) and review + new <= SITTING,
                 said + "of %d cards due (the decks count %d) %d come next, with %d new" % (
                     due, sum(deck[2] for deck in decks), review, new))
    unseen = sum(total - seen for seen, total in steps)
    check.expect((new > 0) == (unseen > 0 and review < SITTING),
                 said + "new cards come when there are cards not seen (%d) and room for them" % unseen)
    words = next_words(state)
    brings = reader.find_anywhere(rows, colours["ink"] if waits else colours["dim"], words, SMALL)
    check.expect(brings is not None, said + "what a key brings is drawn: %s" % words)
    check.expect(in_footer(rows, "Any key: start") == waits and in_footer(rows, "Tab: menu"),
                 said + "the hints are Tab: menu and, %s, Any key: start" % (
                     "as something waits" if waits else "only when something waits"))

    line = context.buddy.get(state["says"])
    if not check.expect(line is not None, said + "the buddy says one of its lines (%s)" % state["says"]):
        return state
    spoken = reader.find_anywhere(rows, colours["bubbleInk"], line[0], SMALL)
    check.expect(spoken is not None and rows[spoken[1] + 8][spoken[0] - 2] == colours["bubble"],
                 said + "the buddy's line is drawn in its bubble: %s" % line[0])
    red = [x for y in range(FOOTER) for x in range(context.areas[look][0], len(rows[0])) if rows[y][x] == BUDDY]
    check.expect(len(red) > 150 and spoken is not None and max(red) < spoken[0],
                 said + "the buddy stands in front of its line (%d points in its red)" % len(red))
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

    # what the rows say at their right end: in full where there is room, else in short
    def fitting(label, forms):
        room = context.areas[look][2] - 8 - 18 - reader.width(label, "efontJA_24") - 8
        return next((form for form in forms if reader.width(form, "efontJA_16") <= room), "")

    due, new = before["dueToday"], before["nextNew"]
    waits = fitting("Course", ["%d due, %d new" % (due, new), "%d due" % due] if due and new else
                    ["%d due" % due] if due else ["%d new" % new] if new else ["done"])
    check.expect(state["says"][0] == waits, "%s: the course says what waits: %s (%s)" % (look, waits, state["says"][0]))
    seen = sum(seen for seen, _ in before["steps"])
    seen = fitting("Decks", ["%d of %d" % (seen, sum(total for _, total in before["steps"])), "%d" % seen])
    check.expect(state["says"][1] == seen, "%s: the decks say what was seen: %s (%s)" % (look, seen, state["says"][1]))
    silent = "no card" if not before["memoryCard"] else "" if before["sound"] else "sound off"
    check.expect(state["says"][4] == silent, "%s: the sounds say why nothing would be heard: %r (%r)" % (
        look, silent, state["says"][4]))
    check.expect(in_footer(rows, "↑↓ or 1-%d" % len(ids)) and in_footer(rows, "Enter: open"),
                 "%s: the hints of the menu are ↑↓ or 1-%d and Enter: open" % (look, len(ids)))

    # every row, four at a time, with the chosen one in view
    count = len(ids)
    for step in range(count + 1):
        rows, state = picture(target)
        chosen, first = state["chosen"], state["first"]
        check.expect(0 <= first <= chosen < first + MENU_ROWS, "%s: the chosen row %d of the menu is in view" % (
            look, chosen + 1))
        check_track(rows, colours, context.areas[look], MENU_ROWS, count, first, check,
                    "%s, menu at row %d: " % (look, chosen + 1))
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

    # every way in and out; the course opens when it has a card to show
    starts = bool(before["nextReview"] or before["nextNew"])
    for index, (name, label, screen) in enumerate(MENU_ENTRIES):
        if name == "course" and not starts:
            screen = MENU
        go_home(target)
        target.key("Tab")
        target.type(str(index + 1))
        check.expect(target.info()["screen"] == screen, "%s: %d opens %s" % (look, index + 1, label) if screen != MENU
                     else "%s: %d starts no sitting when nothing waits" % (look, index + 1))
        go_home(target)
        target.open(name)
        check.expect(target.info()["screen"] == screen, "%s: Enter on %s opens it" % (look, label) if screen != MENU
                     else "%s: Enter on %s starts no sitting when nothing waits" % (look, label))
    go_home(target)
    target.key("Tab")
    for _ in range(count):
        if target.info()["chosen"] == 1:  # not the course, which may have nothing to start
            break
        target.key("Down")
    chosen = target.info()["chosen"]
    target.key("Right")
    check.expect(chosen == 1 and target.info()["screen"] == MENU_ENTRIES[chosen][2],
                 "%s: Right opens the chosen entry" % look)
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
        check_track(rows, colours, context.areas[look], DECK_ROWS, count, first, check,
                    said + "decks at row %d: " % (chosen + 1))
        waits = state["deckDue"][chosen] > 0 or state["deckSeen"][chosen] < state["deckTotal"][chosen]
        check.expect(in_footer(rows, "↑↓ choose") and in_footer(rows, "Enter: start") == waits and
                     in_footer(rows, "Nothing waits") != waits,
                     said + "the hint for %s is %s" % (context.deck_names[ids[chosen]],
                                                     "Enter: start" if waits else "Nothing waits"))
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
            bar = bar_under(rows, colours, left, top)
            if check.expect(bar is not None and waiting and
                            left + bar[0] == waiting[0][0] + reader.width(str(due), "efontJA_16"),
                            said + "%s has a bar under it, from the name to the end of the row" % name):
                seen_here, total = state["deckSeen"][index], state["deckTotal"][index]
                filled = max(bar[0] * seen_here // total, 2) if seen_here and total else 0
                check.expect(bar[1] == filled, said + "the bar of %s is filled as far as it is seen (%d of %d, "
                             "expected %d)" % (name, bar[1], bar[0], filled))
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
        before = target.info()
        waits = before["deckDue"][index] > 0 or before["deckSeen"][index] < before["deckTotal"][index]
        target.key("Enter")
        state = target.info()
        item = context.items.get(state.get("card"))
        if waits:
            check.expect(state["screen"] == CARDS and item is not None and item["deck"] == deck,
                         "%s: Enter on %s starts a sitting with a card of it (%s)" % (
                             look, context.deck_names[deck], state.get("card")))
        else:
            check.expect(state["screen"] == DECKS, "%s: Enter on %s, where nothing waits, starts no sitting" % (
                look, context.deck_names[deck]))
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
    check.expect(in_footer(rows, "Any key: back"), "%s: the hint of the page of keys is Any key: back" % look)
    for name, press in (("a letter", lambda: target.type("x")), ("Enter", lambda: target.key("Enter")),
                        ("Esc", lambda: target.key("Esc")), ("the button", lambda: target.key("Button"))):
        go_home(target)
        target.open("keys")
        press()
        check.expect(target.info()["screen"] == MENU, "%s: %s on the page of keys leads to the menu" % (look, name))


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
    red = sum(1 for y in range(FOOTER) for x in range(context.areas[look][0], len(rows[0])) if rows[y][x] == BUDDY)
    check.expect(red > 400, "%s: the buddy asks, drawn large (%d points in its red)" % (look, red))
    check.expect(in_footer(rows, "Enter: yes") and in_footer(rows, "Space: no") and
                 not in_footer(rows, "Tab: menu"), "%s: the hints are Enter: yes and Space: no" % look)
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


def check_sitting(target, look, context, check, state, when):
    """Starts the course from the home screen and plays it: it holds what the home screen said."""
    go_home(target)
    held = play(target, context.items, key="Enter")
    said = {"review": state["nextReview"], "new": state["nextNew"]}
    check.expect(held == said, "%s, %s: Enter starts the sitting the home screen named (%s), it holds %s" % (
        look, when, next_words(state), held))


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
    check_sitting(target, look, context, check, state, "at the start")
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
    check.expect(state["dueToday"] > 0 and state["nextNew"] > 0,
                 "%s: what was learnt is due on the next day (%d), and new cards come with it (%d)" % (
                     look, state["dueToday"], state["nextNew"]))
    check_menu(target, look, context, check)
    check_decks(target, look, context, check, "on the next day")
    go_home(target)
    check_sitting(target, look, context, check, target.info(), "on the next day")


def check_whole_course(target, look, context, check):
    """Simulator only: plays the course to its end in one day, and looks at the day after."""
    first, second = context.decks[0], context.decks[1]
    name = context.deck_names[first["id"]]
    target.fresh()
    set_look(target, look)
    for _ in range(40):
        state = target.info()
        if state["course"] != first["id"]:
            break
        learn(target, context.items)
    when = "with %s learnt" % name
    state = check_home(target, look, context, check, when)
    check.expect(state["course"] == second["id"] and state["steps"][0] == [first["cards"], first["cards"]],
                 "%s: with every card of %s seen the course stands at %s" % (
                     look, name, context.deck_names[second["id"]]))
    together = [deck["id"] for deck in context.decks if deck["stage"] == second["stage"]]
    check.expect(len(together) > 1, "%s: new cards now come from %s in turn" % (look, ", ".join(together)))
    check_sitting(target, look, context, check, state, when)
    decks = check_decks(target, look, context, check, when)
    check.expect(decks["deckDue"][0] == 0, "%s: learnt in one day, nothing of %s is due (%d)" % (
        look, name, decks["deckDue"][0]))
    check_decks_keys(target, look, context, check)

    for _ in range(400):
        if not target.info()["course"]:
            break
        learn(target, context.items)
    when = "with every card seen"
    total = sum(deck["cards"] for deck in context.decks)
    state = check_home(target, look, context, check, when)
    check.expect(state["course"] == "" and state["deckSeen"] == state["deckTotal"] == total and
                 next_words(state) == "Nothing waits today",
                 "%s: every card was seen (%d of %d), nothing waits" % (look, state["deckSeen"], total))
    for name, press in (("a letter", lambda: target.type("x")), ("Enter", lambda: target.key("Enter")),
                        ("Space", lambda: target.type(" "))):
        press()
        check.expect(target.info()["screen"] == HOME, "%s, %s: %s starts no sitting" % (look, when, name))
    check_menu(target, look, context, check)
    check_decks(target, look, context, check, when)
    check_decks_keys(target, look, context, check)

    target.restart()
    target.key("Enter")
    when = "on the day after the whole course"
    state = check_home(target, look, context, check, when)
    check.expect(state["dueToday"] > 99 and state["nextReview"] == SITTING and state["nextNew"] == 0,
                 "%s, %s: more is due (%d) than a sitting holds, and the home screen says how much comes next: %s" % (
                     look, when, state["dueToday"], next_words(state)))
    check_menu(target, look, context, check)
    check_decks(target, look, context, check, when)
    check_sitting(target, look, context, check, state, when)

    # with the level lowered, cards above it count nowhere, though some of them are due
    if check.expect(set_level(target, 1), "%s: the cards are set to kana only" % look):
        when = "with kana only"
        lowered = check_home(target, look, context, check, when)
        check.expect(0 < lowered["deckTotal"] < total and lowered["dueToday"] < state["dueToday"] - SITTING,
                     "%s, %s: fewer cards count (%d of %d), and fewer are due (%d)" % (
                         look, when, lowered["deckTotal"], total, lowered["dueToday"]))
        check_menu(target, look, context, check)
        check_decks(target, look, context, check, when)
        check_sitting(target, look, context, check, lowered, when)
        check.expect(set_level(target, 3), "%s: the cards are set to all again" % look)


def check_no_card(target, look, check):
    """Simulator only: the memory card is taken out."""
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
                check_whole_course(sim, look, context, check)
                if index == 0:
                    check_no_card(sim, look, check)
            finally:
                sim.close()

    print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
