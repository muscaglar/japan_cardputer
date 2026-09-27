#!/usr/bin/env python3
"""Walks through the kana chart and checks what the app shows at every kana.

    python3 tools/chart_check.py                          # in the simulator, all four looks
    python3 tools/chart_check.py rpg                      # one look
    <PlatformIO's python> tools/chart_check.py --device   # on a Cardputer over USB

What is checked, in every look:
  table   every kana of the deck has one place in the chart, and the chart has no other
  learn   a few kana are answered in a sitting first, so that some were met and most were not
  walk    from the first kana to the last with the key for right: the app names each kana, what
          to type and the page; the picture shows the kana large, what to type, the note in
          full, "met" or "new", and the three rows of the page as a grid with the mark on the
          chosen kana, a bar under each kana that was met, and nothing where the table has gaps;
          on every page the hints in header and footer, with room between them
  glance  the other script, of which no kana was met, at a few kana of every part
  edges   the mark stops at the four ends; up and down keep their column across the gaps of the
          ya and wa rows; Tab goes from part to part; Space changes the script and keeps the
          place; leaving and coming back keeps both
  keys    several hundred keys chosen by chance, the keys for sound among them, compared after
          each one with the rules written down here
  sound   Enter and / ask for the clip of the chosen kana, in either script, and do not move the
          mark; with sound off, or without a memory card, the screen says so in place of the
          note and nothing is played

The hiragana chart is walked in the first and third look, the katakana chart in the others.
That every note fits its two lines is worked out for both scripts in all four looks.
On a device the owner's settings and progress are kept aside first and put back at the end.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from cardputer_screen import HEIGHT, WIDTH, font  # noqa: E402
from sim_driver import SCREENS, Simulator  # noqa: E402

CHART = SCREENS.index("chart")
MENU = SCREENS.index("menu")
CARDS = SCREENS.index("cards")
HOME = SCREENS.index("home")

# The table as the textbooks print it, each kana named by what is typed for it.
ROWS = [
    ("basic", ["a", "i", "u", "e", "o"]),
    ("basic", ["ka", "ki", "ku", "ke", "ko"]),
    ("basic", ["sa", "shi", "su", "se", "so"]),
    ("basic", ["ta", "chi", "tsu", "te", "to"]),
    ("basic", ["na", "ni", "nu", "ne", "no"]),
    ("basic", ["ha", "hi", "fu", "he", "ho"]),
    ("basic", ["ma", "mi", "mu", "me", "mo"]),
    ("basic", ["ya", None, "yu", None, "yo"]),
    ("basic", ["ra", "ri", "ru", "re", "ro"]),
    ("basic", ["wa", None, None, None, "wo"]),
    ("basic", ["nn", None, None, None, None]),
    ("dots", ["ga", "gi", "gu", "ge", "go"]),
    ("dots", ["za", "ji", "zu", "ze", "zo"]),
    ("dots", ["da", "di", "du", "de", "do"]),
    ("dots", ["ba", "bi", "bu", "be", "bo"]),
    ("dots", ["pa", "pi", "pu", "pe", "po"]),
    ("pairs", ["kya", "kyu", "kyo", None, None]),
    ("pairs", ["sha", "shu", "sho", None, None]),
    ("pairs", ["cha", "chu", "cho", None, None]),
    ("pairs", ["nya", "nyu", "nyo", None, None]),
    ("pairs", ["hya", "hyu", "hyo", None, None]),
    ("pairs", ["mya", "myu", "myo", None, None]),
    ("pairs", ["rya", "ryu", "ryo", None, None]),
    ("pairs", ["gya", "gyu", "gyo", None, None]),
    ("pairs", ["ja", "ju", "jo", None, None]),
    ("pairs", ["bya", "byu", "byo", None, None]),
    ("pairs", ["pya", "pyu", "pyo", None, None]),
]
PARTS = ["basic", "dots", "pairs"]
COLUMNS = 5
ON_A_PAGE = 3     # rows of the table
NOTE_LINES = 2
LEARN = 7         # kana to meet before the walk
KEYS_BY_CHANCE = 300
GLANCE = ["a", "yu", "wo", "nn", "ji", "po", "kya", "sho", "pyo"]   # and the kana with the longest note
HINT_GAP = 8      # pixels between two hints on one line: the width of a letter

LARGE = [("lgfxJapanGothic_32", 2), ("efontJA_24", 2), ("lgfxJapanGothic_32", 1), ("efontJA_16", 2)]
SMALL = [("efontJA_16", 1)]
TYPED = [("efontJA_24", 1)]


def first_row(part):
    return next(index for index, (name, _) in enumerate(ROWS) if name == part)


def pages_of(part):
    return (sum(1 for name, _ in ROWS if name == part) + ON_A_PAGE - 1) // ON_A_PAGE


def page_of(row):
    """The page of a row, counted from 1. No page holds rows of two parts."""
    part = ROWS[row][0]
    before = sum(pages_of(name) for name in PARTS[:PARTS.index(part)])
    return before + (row - first_row(part)) // ON_A_PAGE + 1


def rows_on_page_of(row):
    part = ROWS[row][0]
    start = first_row(part) + (row - first_row(part)) // ON_A_PAGE * ON_A_PAGE
    return [r for r in range(start, start + ON_A_PAGE) if r < len(ROWS) and ROWS[r][0] == part]


PAGES = sum(pages_of(part) for part in PARTS)


def has(row, column):
    return 0 <= row < len(ROWS) and 0 <= column < COLUMNS and ROWS[row][1][column] is not None


def nearest(row, wanted):
    for away in range(COLUMNS):
        for column in (wanted - away, wanted + away):
            if has(row, column):
                return column
    return None


class Mark:
    """Where the mark should be after each key, by the rules of the chart."""

    def __init__(self, row=0, column=0, script="hiragana"):
        self.row = row
        self.column = column
        self.wanted = column
        self.script = script

    def press(self, key):
        if key in ("Up", "Down"):
            step = -1 if key == "Up" else 1
            if 0 <= self.row + step < len(ROWS):
                self.row += step
                self.column = nearest(self.row, self.wanted)
        elif key in ("Left", "Right"):
            step = -1 if key == "Left" else 1
            column = self.column + step
            while 0 <= column < COLUMNS and not has(self.row, column):
                column += step
            if 0 <= column < COLUMNS:
                self.column = self.wanted = column
            elif 0 <= self.row + step < len(ROWS):
                # in reading order: on in the next row, back to the end of the row before
                self.row += step
                self.column = self.wanted = nearest(self.row, 0 if step > 0 else COLUMNS - 1)
        elif key == "Tab":
            part = PARTS[(PARTS.index(ROWS[self.row][0]) + 1) % len(PARTS)]
            self.row = first_row(part)
            self.column = nearest(self.row, self.wanted)
        elif key == "Space":
            self.script = "katakana" if self.script == "hiragana" else "hiragana"

    def typed(self):
        return ROWS[self.row][1][self.column]


# How a key of the model is pressed. The bare keys ; , . move the mark as the arrows do; the
# bare / is the key for sound here, so that right needs the arrow, or / with Fn.
WAYS = {
    "Up": [("key", "Up"), ("type", ";"), ("fn", ";")],
    "Down": [("key", "Down"), ("type", "."), ("fn", ".")],
    "Left": [("key", "Left"), ("type", ","), ("fn", ",")],
    "Right": [("key", "Right"), ("fn", "/")],
    "Tab": [("key", "Tab")],
    "Space": [("type", " ")],
    "Sound": [("key", "Enter"), ("type", "/")],
    "nothing": [("type", "q"), ("type", "5"), ("type", "-"), ("type", "A")],
}


def press(target, way):
    kind, what = way
    if kind == "key":
        target.key(what)
    elif kind == "fn":
        target.fn(what)
    else:
        target.type(what)


def places(rows, colour, text, faces, box):
    """Every place inside the box where exactly the pixels of the text have that colour.

    box: (left, top, right, bottom). Returns a list of (left, top, width, height).
    """
    seen = reader.coloured(rows, colour, box[0], box[1], box[2], box[3])
    found = []
    for font_name, scale in faces:
        points, advance = reader.mask(text, font_name)
        if not points:
            continue
        points = reader.scaled(points, scale)
        width = advance * scale
        height = font(font_name).height * scale
        anchor = min(points, key=lambda p: (p[1], p[0]))
        for (sx, sy) in seen:
            left, top = sx - anchor[0], sy - anchor[1]
            if all((x + left, y + top) in seen for (x, y) in points):
                inside = sum(1 for (x, y) in seen if left <= x < left + width and top <= y < top + height)
                if inside == len(points):
                    found.append((left, top, width, height))
    return found


def in_any_colour(rows, text, box):
    """As places(), for a text whose colour depends on the look: every colour in the box is tried."""
    seen = {}
    for y in range(max(0, box[1]), min(len(rows), box[3])):
        for x in range(max(0, box[0]), min(len(rows[0]), box[2])):
            seen[rows[y][x]] = seen.get(rows[y][x], 0) + 1
    ground = max(seen, key=seen.get) if seen else None
    found = []
    for colour in seen:
        if colour != ground:
            found += places(rows, colour, text, SMALL, box)
    return found


def count(rows, colour, box):
    return len(reader.coloured(rows, colour, box[0], box[1], box[2], box[3]))


def wrapped(text, width):
    """The lines of the text, broken at spaces as the app breaks them."""
    lines = []
    line = ""
    for word in text.split(" "):
        longer = word if not line else line + " " + word
        if line and reader.width(longer, "efontJA_16") > width:
            lines.append(line)
            line = word
        else:
            line = longer
    return lines + ([line] if line else [])


def title_colour(colours, look):
    return colours[look]["accent"] if look == "washi" else colours[look]["headInk"]


class Check:
    def __init__(self):
        self.passed = []
        self.failed = []

    def expect(self, condition, message):
        (self.passed if condition else self.failed).append(message)
        if not condition:
            print("FAIL " + message, flush=True)
        return condition


def go_home(target):
    for _ in range(5):
        if target.info()["screen"] == HOME:
            return True
        target.key("Esc")
    return target.info()["screen"] == HOME


SETTINGS = ("look", "romaji", "sound", "volume", "voice", "textbookN", "level")


def settings_of(state, but=None):
    return tuple(state.get(name) for name in SETTINGS if name != but)


def set_setting(target, name, wanted):
    """From the home screen. Finds the row of the settings that changes it by trying, and changes nothing else.

    The settings open on the row they were left on, which may be any row.
    """
    before = target.info()
    if before[name] == wanted:
        return True
    target.open("settings")
    for _ in range(12):
        target.key("Right")
        after = target.info()
        if after[name] != before[name]:
            for _ in range(8):
                if target.info()[name] == wanted:
                    break
                target.key("Right")
            break
        if settings_of(after) != settings_of(before):
            target.key("Left")   # the row of another setting: back to what it was
        target.key("Down")
    go_home(target)
    after = target.info()
    return after[name] == wanted and settings_of(after, but=name) == settings_of(before, but=name)


def set_look(target, wanted):
    return set_setting(target, "look", wanted)


def set_sound(target, wanted):
    return set_setting(target, "sound", wanted)


def learn(target, script, items, wanted):
    """Answers kana of the deck in a sitting until `wanted` were met. Returns their ids."""
    met = set()
    if not target.sitting(script):
        return met
    for _ in range(12 * wanted):
        state = target.info()
        if state["screen"] != CARDS or len(met) >= wanted:
            break
        kind = state.get("cardState")
        if kind in ("probe", "asking", "copy") and state.get("card") in items:
            target.type(items[state["card"]]["gloss"])
            target.key("Enter")
            if target.info()["seen"] > state["seen"]:
                met.add(state["card"])
        elif kind in ("marked", "note"):
            target.type(" ")
        else:
            target.key("Enter")
    go_home(target)
    return met


def to_start(target, script):
    """Inside the chart: to the first kana, in the script wanted."""
    for _ in range(len(ROWS) + 2):
        target.key("Up")
    for _ in range(COLUMNS + 1):
        target.key("Left")
    if target.info()["script"] != script:
        target.type(" ")
    return target.info()


def agrees(state, mark, kana):
    typed = mark.typed()
    item = kana[mark.script][typed]
    return (state["screen"] == CHART and state["script"] == mark.script and state["row"] == mark.row and
            state["column"] == mark.column and state["types"] == typed and state["kana"] == item["prompt"] and
            state["item"] == item["id"] and state["page"] == page_of(mark.row) and state["pages"] == PAGES and
            state["part"] == ROWS[mark.row][0])


def said(state):
    return "%s %s at row %s column %s, page %s of %s" % (state.get("script"), state.get("kana"), state.get("row"),
                                                        state.get("column"), state.get("page"), state.get("pages"))


def hints(rows, colours, look, area, mark):
    """What is wrong with the hints around the chart. An empty list when nothing is."""
    wrong = []
    head = (0, 0, WIDTH, area[1])
    foot = (0, area[1] + area[3], WIDTH, HEIGHT)
    title = "%s %d/%d" % (mark.script.capitalize(), page_of(mark.row), PAGES)
    other = "Space: " + ("ア" if mark.script == "hiragana" else "あ")
    lines = [(title, places(rows, title_colour(colours, look), title, SMALL, head), other,
              in_any_colour(rows, other, head))]
    lines.append(("Enter: sound", in_any_colour(rows, "Enter: sound", foot), "Tab: more",
                  in_any_colour(rows, "Tab: more", foot)))
    for left, at_left, right, at_right in lines:
        for text, found in ((left, at_left), (right, at_right)):
            if len(found) != 1:
                wrong.append("the hint %r is drawn %d times" % (text, len(found)))
        if len(at_left) == 1 and len(at_right) == 1 and at_right[0][0] - (at_left[0][0] + at_left[0][2]) < HINT_GAP:
            wrong.append("%r and %r have less than %d px between them" % (left, right, HINT_GAP))
    return wrong


def look_at(rows, look, colours, area, mark, kana, met):
    """What is wrong with the picture of the chart. An empty list when nothing is."""
    wrong = []
    c = colours[look]
    item = kana[mark.script][mark.typed()]
    x0, y0, x1 = area[0], area[1], area[0] + area[2]
    note_top = area[1] + area[3] - NOTE_LINES * 16
    above = (x0, y0, x1, note_top)
    below = (x0, note_top, x1, area[1] + area[3])

    title = "%s %d/%d" % (mark.script.capitalize(), page_of(mark.row), PAGES)
    if not places(rows, title_colour(colours, look), title, SMALL, (0, 0, WIDTH, y0)):
        wrong.append("the title %r is not in the header" % title)

    large = places(rows, c["ink"], item["prompt"], LARGE, above)
    if len(large) != 1:
        wrong.append("%s is drawn large %d times" % (item["prompt"], len(large)))
    elif large[0][3] < (32 if ROWS[mark.row][0] == "pairs" else 48):
        wrong.append("%s is only %d px high" % (item["prompt"], large[0][3]))
    if len(places(rows, c["accent"], item["gloss"], TYPED, above)) != 1:
        wrong.append("what to type, %r, is not drawn at 24 px" % item["gloss"])
    word, other = ("met", "new") if item["id"] in met else ("new", "met")
    if len(places(rows, c["good" if word == "met" else "dim"], word, SMALL, above)) != 1:
        wrong.append("the word %r is not drawn" % word)
    if places(rows, c["good" if other == "met" else "dim"], other, SMALL, above):
        wrong.append("the word %r is drawn" % other)

    lines = wrapped(item["note"], area[2] - 4)
    if len(lines) > NOTE_LINES:
        wrong.append("the note needs %d lines: %r" % (len(lines), item["note"]))
    tops = []
    for line in lines[:NOTE_LINES]:
        found = places(rows, c["ink"], line, SMALL, below)
        if len(found) != 1:
            wrong.append("the line %r of the note is not drawn" % line)
        else:
            tops.append(found[0][1])
    if tops != sorted(set(tops)):
        wrong.append("the lines of the note lie on each other")

    # the rows of the page, as a grid
    lefts = {}
    drawn = 0
    table_right = x1
    if len(large) == 1:
        table_right = large[0][0]
    grid = (x0, y0, table_right, note_top)
    last_top = None
    for row in rows_on_page_of(mark.row):
        row_top = None
        last_left = None
        for column in range(COLUMNS):
            typed = ROWS[row][1][column]
            if typed is None:
                continue
            cell = kana[mark.script][typed]
            chosen = (row == mark.row and column == mark.column)
            known = cell["id"] in met
            colour = c["rowInk"] if chosen else c["ink"] if known else c["dim"]
            found = places(rows, colour, cell["prompt"], SMALL, grid)
            if len(found) != 1:
                wrong.append("%s is drawn %d times in the table" % (cell["prompt"], len(found)))
                continue
            drawn += 1
            left, top, width, height = found[0]
            if row_top is None:
                row_top = top
                if last_top is not None and top < last_top + height:
                    wrong.append("the row of %s lies on the row above" % cell["prompt"])
            elif top != row_top:
                wrong.append("%s is not in line with its row" % cell["prompt"])
            if last_left is not None and left < last_left + width:
                wrong.append("%s lies on the kana left of it" % cell["prompt"])
            last_left = left
            if lefts.setdefault(column, left) != left:
                wrong.append("%s is not in line with its column" % cell["prompt"])
            marked = count(rows, c["row"], (left, top, left + width, top + height))
            if chosen and marked < width * height // 3:
                wrong.append("the mark is not on %s" % cell["prompt"])
            if not chosen and marked:
                wrong.append("a mark is on %s, which is not chosen" % cell["prompt"])
            bar = count(rows, c["good"], (left, top + height, left + width, top + height + 2))
            if known and bar < width // 2:
                wrong.append("%s was met and has no bar under it" % cell["prompt"])
            if not known and bar:
                wrong.append("%s was not met and has a bar under it" % cell["prompt"])
        last_top = row_top if row_top is not None else last_top
    # nothing else of the table may be there: every other kana of the script is looked for,
    # but for those that are one half of a pair on this page
    if drawn:
        on_page = [kana[mark.script][typed]["prompt"] for row in rows_on_page_of(mark.row)
                   for typed in ROWS[row][1] if typed]
        strangers = [cell["prompt"] for cell in kana[mark.script].values()
                     if not any(cell["prompt"] in prompt for prompt in on_page) and any(
                         places(rows, c[name], cell["prompt"], SMALL, grid) for name in ("ink", "dim"))]
        if strangers:
            wrong.append("kana of other pages are in the table: %s" % " ".join(strangers))
    return wrong


def walk(target, look, script, colours, area, kana, met, check):
    state = to_start(target, script)
    mark = Mark(script=script)
    check.expect(agrees(state, mark, kana),
                 "%s: up and left to the end lead to the first kana (%s)" % (look, said(state)))

    unnamed = []
    undrawn = []
    flags = []
    visited = []
    pages = set()
    hinted = set()
    unhinted = []
    while True:
        state = target.info()
        item = kana[script][mark.typed()]
        visited.append(state.get("item"))
        pages.add(state.get("page"))
        if not agrees(state, mark, kana):
            unnamed.append("%s: expected %s, the app says %s" % (look, item["prompt"], said(state)))
        if state.get("met") != (item["id"] in met):
            flags.append(item["prompt"])
        _, rows = target.frame()
        for problem in look_at(rows, look, colours, area, mark, kana, met):
            undrawn.append("%s %s: %s" % (look, item["prompt"], problem))
        if state.get("page") not in hinted:
            hinted.add(state.get("page"))
            for problem in hints(rows, colours, look, area, mark):
                unhinted.append("%s %s: %s" % (look, item["prompt"], problem))
        before = (mark.row, mark.column)
        mark.press("Right")
        if (mark.row, mark.column) == before:
            break
        target.key("Right")
    for line in unnamed[:8] + undrawn[:8] + unhinted[:8]:
        print("     " + line, flush=True)
    expected = [kana[script][typed]["id"] for _, row in ROWS for typed in row if typed]
    check.expect(visited == expected, "%s: the key for right leads through all %d %s in the order of the table "
                                      "(%d visited)" % (look, len(expected), script, len(visited)))
    check.expect(not unnamed, "%s: the app names every kana, what to type, its row, column and page (%d wrong)" % (
        look, len(unnamed)))
    check.expect(pages == set(range(1, PAGES + 1)), "%s: the walk showed the pages 1 to %d" % (look, PAGES))
    check.expect(not undrawn, "%s: every kana is drawn large with what to type, its note, and its page of the "
                              "table with mark, bars and gaps (%d problems)" % (look, len(undrawn)))
    check.expect(not flags, "%s: the %d kana met say so, the others do not (wrong: %s)" % (
        look, len(met), " ".join(flags) or "none"))
    check.expect(not unhinted and len(hinted) == PAGES,
                 "%s: on each of the %d pages the header names script and page and the key for the other script, "
                 "the footer the keys for sound and for more, with room between them (%d problems)" % (
                     look, PAGES, len(unhinted)))
    return mark


def glance(target, look, script, colours, area, kana, met, check):
    """The script that was not walked, at a few kana of every part. None of its kana was met."""
    longest = max(kana[script], key=lambda typed: len(kana[script][typed]["note"]))
    wanted = set(GLANCE) | {longest}
    to_start(target, script)
    mark = Mark(script=script)
    problems = []
    looked = set()
    while True:
        if mark.typed() in wanted:
            state = target.info()
            item = kana[script][mark.typed()]
            if not agrees(state, mark, kana) or state.get("met"):
                problems.append("%s: expected %s, not met, the app says %s, met %s" % (
                    look, item["prompt"], said(state), state.get("met")))
            _, rows = target.frame()
            for problem in look_at(rows, look, colours, area, mark, kana, met) + hints(rows, colours, look, area, mark):
                problems.append("%s %s: %s" % (look, item["prompt"], problem))
            looked.add(mark.typed())
        before = (mark.row, mark.column)
        mark.press("Right")
        if (mark.row, mark.column) == before:
            break
        target.key("Right")
    for line in problems[:8]:
        print("     " + line, flush=True)
    check.expect(not problems and looked == wanted,
                 "%s: in %s, of which nothing was met, %d kana of every part are drawn as they should be, the one "
                 "with the longest note among them (%d problems)" % (look, script, len(looked), len(problems)))


def edges(target, look, script, kana, check):
    def after(mark, keys, message):
        for key in keys:
            mark.press(key)
            press(target, WAYS[key][0])
        state = target.info()
        check.expect(agrees(state, mark, kana), "%s: %s (%s)" % (look, message, said(state)))
        return state

    other = "katakana" if script == "hiragana" else "hiragana"
    last = len(ROWS) - 1
    mark = Mark(row=last, column=2, script=script)
    after(mark, ["Right", "Down", "Right"], "at the last kana right and down change nothing")
    check.expect((mark.row, mark.column) == (last, 2), "%s: the rules keep the mark on the last kana" % look)
    to_start(target, script)
    mark = Mark(script=script)
    after(mark, ["Left", "Up", "Left"], "at the first kana left and up change nothing")
    check.expect((mark.row, mark.column) == (0, 0), "%s: the rules keep the mark on the first kana" % look)

    after(mark, ["Right"] + ["Down"] * 6, "down the column of i as far as mi")
    state = after(mark, ["Down"], "the ya row has no yi: the mark goes to ya")
    check.expect(state["types"] == "ya", "%s: from mi, down leads to ya (%s)" % (look, state["types"]))
    state = after(mark, ["Down"], "below the gap the mark is back in the column of i")
    check.expect(state["types"] == "ri", "%s: from ya, down leads to ri (%s)" % (look, state["types"]))
    state = after(mark, ["Down", "Down"], "through wa to the n that stands alone")
    check.expect(state["types"] == "nn", "%s: the row after wa holds n alone (%s)" % (look, state["types"]))
    state = after(mark, ["Down"], "down from n leads into the part with dots, to the column of i")
    check.expect(state["types"] == "gi" and state["part"] == "dots",
                 "%s: below n comes gi (%s)" % (look, state["types"]))
    state = after(mark, ["Left", "Left"], "left of the first kana of a row is the last of the row before")
    check.expect(state["types"] == "nn", "%s: left of ga is n (%s)" % (look, state["types"]))
    state = after(mark, ["Left", "Left"], "and left of wo, across the gaps, wa")
    check.expect(state["types"] == "wa", "%s: left of wo is wa (%s)" % (look, state["types"]))

    state = after(mark, ["Tab"], "Tab leads to the part with dots")
    check.expect(state["part"] == "dots" and state["row"] == first_row("dots"), "%s: Tab shows the first row with "
                 "dots (%s)" % (look, said(state)))
    state = after(mark, ["Tab"], "Tab leads to the pairs")
    check.expect(state["part"] == "pairs" and state["row"] == first_row("pairs"), "%s: Tab shows the first row of "
                 "pairs (%s)" % (look, said(state)))
    state = after(mark, ["Tab"], "Tab leads back to the basic kana")
    check.expect(state["part"] == "basic" and state["row"] == 0, "%s: Tab after the pairs shows the first row "
                 "again (%s)" % (look, said(state)))

    after(mark, ["Down"] * 17 + ["Right"], "down and right to a pair")
    here = target.info()
    state = after(mark, ["Space"], "Space changes the script and keeps the place")
    check.expect(state["script"] == other and (state["row"], state["column"], state["page"]) ==
                 (here["row"], here["column"], here["page"]) and state["types"] == here["types"] and
                 state["kana"] != here["kana"],
                 "%s: Space turns %s into %s on the same page" % (look, here["kana"], state["kana"]))
    target.key("Esc")
    check.expect(target.info()["screen"] == MENU, "%s: Esc leads to the menu" % look)
    target.key("Enter")
    state = target.info()
    check.expect(agrees(state, mark, kana), "%s: coming back from the menu finds script and place as they were "
                                            "(%s)" % (look, said(state)))
    target.key("Backspace")
    check.expect(target.info()["screen"] == MENU, "%s: Backspace leads to the menu too" % look)
    target.key("Enter")
    after(mark, ["Space"], "Space changes the script back")
    for way in WAYS["nothing"]:
        press(target, way)
    check.expect(agrees(target.info(), mark, kana), "%s: keys without a meaning change nothing" % look)
    return mark


def by_chance(target, look, mark, kana, check, seed):
    chooser = random.Random(seed)
    names = ["Up", "Down", "Left", "Right"] * 3 + ["Tab", "Space", "Sound", "nothing"]
    wrong = []
    for index in range(KEYS_BY_CHANCE):
        name = chooser.choice(names)
        way = chooser.choice(WAYS[name])
        mark.press(name)
        press(target, way)
        state = target.info()
        if not agrees(state, mark, kana):
            wrong.append("key %d, %s as %s %r: expected %s at row %d column %d, the app says %s" % (
                index + 1, name, way[0], way[1], mark.typed(), mark.row, mark.column, said(state)))
            break
    for line in wrong:
        print("     " + line, flush=True)
    check.expect(not wrong, "%s: %d keys chosen by chance, the arrows also as ; , . and with Fn, the keys for "
                            "sound among them, left the mark where the rules put it" % (look, KEYS_BY_CHANCE))


def sound(target, look, colours, area, kana, check, in_simulator):
    c = colours[look]
    below = (area[0], area[1] + area[3] - NOTE_LINES * 16, area[0] + area[2], area[1] + area[3])

    def message(text):
        """Whether the screen says so where the note was, and the note is not under it."""
        _, rows = target.frame()
        return len(places(rows, c["bad"], text, SMALL, below)) == 1 and count(rows, c["ink"], below) == 0

    def note_drawn(item):
        _, rows = target.frame()
        return all(len(places(rows, c["ink"], line, SMALL, below)) == 1 for line in wrapped(item["note"], area[2] - 4))

    go_home(target)
    check.expect(set_sound(target, False), "%s: the sound is switched off in the settings" % look)
    target.open("chart")
    here = target.info()
    item = kana[here["script"]][here["types"]]
    for name, way in (("Enter", ("key", "Enter")), ("/", ("type", "/"))):
        press(target, way)
        state = target.info()
        check.expect(state["heard"] == "sound off" and state.get("plays", 0) == here.get("plays", 0) and
                     state["item"] == here["item"],
                     "%s: with sound off %s plays nothing and the mark stays (heard %r)" % (look, name, state["heard"]))
        check.expect(message("Sound is off in Settings"), "%s: after %s the screen says that the sound is off, in "
                     "place of the note" % (look, name))
        target.type("q")
        check.expect(target.info()["heard"] == "" and note_drawn(item),
                     "%s: the next key brings the note of %s back" % (look, item["prompt"]))

    go_home(target)
    check.expect(set_sound(target, True), "%s: the sound is switched on in the settings" % look)
    target.open("chart")
    state = target.info()
    check.expect(state["item"] == here["item"] and state["sound"] is True,
                 "%s: back in the chart, still on %s" % (look, item["prompt"]))
    for name, way in (("Enter", ("key", "Enter")), ("/", ("type", "/"))):
        before = target.info()
        press(target, way)
        state = target.info()
        check.expect(state["item"] == here["item"], "%s: %s does not move the mark" % (look, name))
        if in_simulator:
            clips = ["/audio/%s/%s/%s.wav" % (voice, here["script"], item["id"]) for voice in "fm"]
            check.expect(state["heard"] == "played" and state["plays"] == before["plays"] + 1 and
                         state["played"] in clips and state["playedAt"] == state["volume"],
                         "%s: %s plays the clip of %s (%s, heard %r)" % (look, name, item["prompt"], state["played"],
                                                                       state["heard"]))
            check.expect(note_drawn(item), "%s: the note stays while the clip plays" % look)
        else:
            # what the memory card of this device holds is not known here
            check.expect(state["heard"] in ("played", "no clip", "no card"),
                         "%s: %s asks for the clip of %s (heard %r)" % (look, name, item["prompt"], state["heard"]))
            if state["heard"] != "played":
                text = "No memory card" if state["heard"] == "no card" else "No sound for this kana"
                check.expect(message(text), "%s: the screen says %r" % (look, text))
    if in_simulator:
        target.key("Right")
        moved = target.info()
        target.key("Enter")
        state = target.info()
        check.expect(state["played"].endswith("/%s.wav" % moved["item"]) and moved["item"] != here["item"],
                     "%s: after a step to the right the clip is that of %s" % (look, moved["kana"]))
        target.type(" ")
        turned = target.info()
        target.type("/")
        state = target.info()
        check.expect(turned["script"] != moved["script"] and turned["types"] == moved["types"] and
                     state["played"] in ["/audio/%s/%s/%s.wav" % (voice, turned["script"], turned["item"])
                                         for voice in "fm"] and state["plays"] == turned["plays"] + 1,
                     "%s: after Space the clip is that of %s, from the folder of %s (%s)" % (
                         look, turned["kana"], turned["script"], state["played"]))
        target.card(False)
        before = target.info()
        target.key("Enter")
        state = target.info()
        check.expect(state["heard"] == "no card" and state["plays"] == before["plays"],
                     "%s: without a memory card nothing is played (heard %r)" % (look, state["heard"]))
        check.expect(message("No memory card"), "%s: and the screen says that the card is missing" % look)
        target.card(True)
    go_home(target)
    check.expect(set_sound(target, False), "%s: the sound is switched off again" % look)


def check_look(target, look, colours, areas, items, kana, check, in_simulator):
    script = "katakana" if reader.LOOKS.index(look) % 2 else "hiragana"
    check.expect(target.fresh(), "%s: progress starts empty" % look)
    check.expect(set_look(target, look), "%s: the look is set, the home screen is back" % look)
    met = learn(target, script, items, LEARN)
    state = target.info()
    check.expect(len(met) == LEARN and state["seen"] == LEARN and state["screen"] == HOME,
                 "%s: %d %s were met in a sitting (%d, the app has seen %d)" % (
                     look, LEARN, script, len(met), state["seen"]))

    target.open("chart")
    check.expect(target.info()["screen"] == CHART, "%s: the menu leads to the chart" % look)
    glance(target, look, "katakana" if script == "hiragana" else "hiragana", colours, areas[look], kana, met, check)
    walk(target, look, script, colours, areas[look], kana, met, check)
    mark = edges(target, look, script, kana, check)   # goes on from the last kana, where the walk ended
    by_chance(target, look, mark, kana, check, 40 + reader.LOOKS.index(look))
    sound(target, look, colours, areas[look], kana, check, in_simulator)


def table_of(items, check):
    """script -> what is typed -> the kana. Checks that chart and decks hold the same kana."""
    kana = {}
    for script in ("hiragana", "katakana"):
        in_deck = {item_id: item for item_id, item in items.items() if item["deck"] == script}
        kana[script] = {}
        for _, row in ROWS:
            for typed in row:
                item = in_deck.get("%s-%s" % (script, typed)) if typed else None
                if item:
                    kana[script][typed] = dict(item, id="%s-%s" % (script, typed))
        in_chart = sum(1 for _, row in ROWS for typed in row if typed)
        check.expect(len(kana[script]) == in_chart == len(in_deck),
                     "table: the chart has %d places, %d of them hold a kana of the deck %s, which has %d" % (
                         in_chart, len(kana[script]), script, len(in_deck)))
        check.expect(all(item["gloss"] == typed for typed, item in kana[script].items()),
                     "table: every kana of %s stands where what is typed for it says" % script)
    return kana


def notes_fit(kana, areas, check):
    """The walk shows each script in two looks only, and the looks differ in width."""
    for look in reader.LOOKS:
        long = [item["prompt"] for script in sorted(kana) for item in kana[script].values()
                if len(wrapped(item["note"], areas[look][2] - 4)) > NOTE_LINES]
        check.expect(not long, "table: in the look %s the note of every kana of both scripts fits %d lines "
                               "(too long: %s)" % (look, NOTE_LINES, " ".join(long) or "none"))


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    colours, areas = reader.themes()
    items = reader.decks()
    check = Check()
    kana = table_of(items, check)
    notes_fit(kana, areas, check)
    if check.failed:
        print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
        return 1
    assert HEIGHT > max(area[1] + area[3] for area in areas.values())

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
                check_look(device, look, colours, areas, items, kana, check, False)
                print("%s done" % look, flush=True)
        finally:
            restored = device.back()
            after = device.info()
            check.expect(restored and settings_of(after) == settings_of(before) and after["day"] == before["day"] and
                         after["seen"] == before["seen"],
                         "device: settings and progress are back as they were (look %s, sound %s, day %d, %d seen)" % (
                             after["look"], after["sound"], after["day"], after["seen"]))
            check.expect(after["heapLowest"] > 100000,
                         "device: never less than 100 KB of memory free (lowest %d)" % after["heapLowest"])
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=60 + reader.LOOKS.index(look))
            try:
                check_look(sim, look, colours, areas, items, kana, check, True)
            finally:
                sim.close()

    for line in check.passed:
        print("ok   " + line)
    for line in check.failed:
        print("FAIL " + line)
    print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
