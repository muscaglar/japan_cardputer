#!/usr/bin/env python3
"""Plays sittings over two days and checks what the card screen does, shows and says.

    python3 tools/cards_check.py                          # in the simulator, all four looks
    python3 tools/cards_check.py techo                    # one look
    python3 tools/cards_check.py --every-card rpg         # meets every card of every deck in one look
    <PlatformIO's python> tools/cards_check.py --device   # on a Cardputer over USB

What is checked, in every look:
  course  from a fresh start the first sitting asks hiragana one after the other. A kana typed
          right at first sight is marked and not taught. One typed wrong, or passed with Tab, is
          taught on a page with what to type and how it sounds, then typed, and comes back as a
          question in the same sitting
  words   a sitting from the signs: a new card is met with what each of its kanji means, then
          typed; a wrong copy costs nothing; Tab shows the romaji; each card comes back as a
          question; a right answer is marked 〇, a near miss △, a wrong one ×, a card given
          up →; Tab after the mark leads to what the card has to say; what was missed comes
          back; the end shows how many were right
  day 2   after a restart the app asks whether a new day has begun; what was learnt is due and
          is asked before anything new
  pages   a card from the numbers that has a note, one that has nothing to say, and a sign with
          meanings and a note, which take two pages or share one
  sound   the clip of a card is played when the card is met and with every mark, and again
          with the key /; never while a question is open; not at all when sound is off or the
          memory card is out, and then the hint for / is not shown either
  edges   Enter and Backspace on nothing, a line longer than fits, Esc in the middle

The app says which card it shows and what it played (`info`); the pictures are read to see that
what should be drawn is drawn. On a device the owner's settings and progress are kept aside
first and put back at the end. A device that does not tell what it played is checked without
the counts of clips.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

HOME, CARDS, SUMMARY = 0, 4, 5
FONT16, FONT24 = "efontJA_16", "efontJA_24"
MARKS = {"right": ("〇", "good"), "almost": ("△", "wait"), "wrong": ("×", "bad"), "shown": ("→", "dim")}
# the colours drawFrame() in lib/ui/theme.cpp gives the two hints in the footer
FOOT_LEFT = {"techo": "type", "eki": "headInk", "rpg": "dim", "washi": "ink"}
FOOT_RIGHT = {"techo": "headInk", "eki": "headAccent", "rpg": "accent", "washi": "accent"}
LONGEST_ANSWER = 48   # kLongestAnswer in lib/ui/screens/cards.cpp
LINES_ON_PAGE = 2     # kLinesOnPage
LINES_BY_KANA = 3     # kLinesByKana
WIDEST_KANA = 100     # kWidestKana
GAP_BY_KANA = 10      # kGapByKana
MARK_ROOM = 30        # kMarkRoom


class Check:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.notes = []

    def expect(self, condition, message):
        (self.passed if condition else self.failed).append(message)
        if not condition:
            print("FAIL " + message, flush=True)
        return bool(condition)

    def note(self, message):
        if message not in self.notes:
            self.notes.append(message)
            print("note " + message, flush=True)


class Table:
    """What a check of one look works with."""

    def __init__(self, target, look, items, colours, areas, check):
        self.target = target
        self.look = look
        self.items = items
        self.colours = colours[look]
        self.area = areas[look]
        self.check = check
        self.where = look
        # The simulator pretends a memory card that holds every clip. A real one may lack some.
        self.every_clip = hasattr(target, "card")

    def expect(self, condition, message):
        return self.check.expect(condition, "%s: %s" % (self.where, message))

    def picture(self):
        return self.target.frame()[1]


# ---------------------------------------------------------------------------------------------
# What a card should look like
# ---------------------------------------------------------------------------------------------

def is_kana(item):
    return item["kind"] == "kana"


def what_to_type(item):
    """A kana card says it itself. For a word it is the romaji of the reading."""
    return item["gloss"] if is_kana(item) else reader.to_romaji(item["reading"])


def wrong_letters(item):
    return "a" if what_to_type(item) in ("zu", "du") else "zu"


def column(area, item):
    """Where the text beside a kana stands: columnOf() in lib/ui/screens/cards.cpp."""
    x, y, w, h = area
    face = reader.fit_face(item["prompt"], WIDEST_KANA, 64)
    left = x + 4
    start = left + reader.width(item["prompt"], face[0]) * face[1] + GAP_BY_KANA
    return {"face": face, "kana": left, "x": start, "width": x + w - 2 - start, "top": y + (2 if h < 92 else 6)}


def beats(kana):
    """As kana::beats() in lib/core/kana.cpp: a small kana belongs to the one before it."""
    out = []
    for character in kana:
        if character in "ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ" and out:
            out[-1] += character
        else:
            out.append(character)
    return out


def reading_lines(area, reading):
    """The reading as the card draws it: readingLines() in lib/ui/screens/cards.cpp.
    Returns (font name, lines)."""
    if reader.width(reading, FONT24) + MARK_ROOM <= area[2]:
        return FONT24, [reading]
    pieces = beats(reading)
    if reader.width(reading, FONT16) + MARK_ROOM <= area[2] or len(pieces) < 2:
        return FONT16, [reading]
    at = (len(pieces) + 1) // 2
    while at + 1 < len(pieces) and pieces[at] in ("ん", "ン", "っ", "ッ", "ー"):
        at += 1
    return FONT16, ["".join(pieces[:at]), "".join(pieces[at:])]


def pages_of(area, item):
    """The pages of a card: layOut() in lib/ui/screens/cards.cpp. Each page is
    {"parts": [lines], "note": [lines]}."""
    if is_kana(item):
        room = column(area, item)["width"]
        most = LINES_BY_KANA
        parts = []
    else:
        room = area[2] - 4
        most = 1 if len(reading_lines(area, item["reading"])[1]) > 1 else LINES_ON_PAGE
        parts = reader.lines_of([p for p in item["parts"].split("  ") if p], "  ", room)
    note = reader.lines_of([w for w in item["note"].split(" ") if w], " ", room)
    pages = [{"parts": parts[i:i + most], "note": []} for i in range(0, len(parts), most)]
    if pages and note and len(pages[-1]["parts"]) + len(note) <= most:
        pages[-1]["note"] = note
        note = []
    pages += [{"parts": [], "note": note[i:i + most]} for i in range(0, len(note), most)]
    return pages


def says(page):
    return "parts+note" if page["parts"] and page["note"] else "parts" if page["parts"] else "note"


def clip_of(item_id, item):
    return r"/audio/[fm]/%s/%s\.wav\Z" % (re.escape(item["deck"]), re.escape(item_id))


def tells_sound(state):
    return "plays" in state


def can_hear(state):
    return bool(state["sound"] and state["memoryCard"])


# ---------------------------------------------------------------------------------------------
# Reading the picture
# ---------------------------------------------------------------------------------------------

def drawn(rows, colour, text, faces=((FONT16, 1),)):
    return reader.find_anywhere(rows, colour, text, list(faces))


def prompt_drawn(table, rows, item):
    if is_kana(item):
        where = column(table.area, item)
        found = drawn(rows, table.colours["ink"], item["prompt"], [where["face"]])
        return found is not None and found[0] == where["kana"]
    return drawn(rows, table.colours["ink"], item["prompt"], reader.PROMPT_FACES) is not None


def mark_drawn(table, rows, verdict):
    glyph, colour = MARKS[verdict]
    return drawn(rows, table.colours[colour], glyph, reader.TEXT_FACES) is not None


def typing_answer_drawn(table, rows, item):
    """On a kana card: what to type, at 24 px, beside the kana."""
    found = drawn(rows, table.colours["ink"], item["gloss"], [(FONT24, 1)])
    return found is not None and found[0] >= column(table.area, item)["x"]


def reading_drawn(table, rows, item):
    """Every line of the reading, at its size. The hooks of the pitch line reach three rows into
    the kana, in their own colour."""
    font_name, lines = reading_lines(table.area, item["reading"])
    return all(reader.find_anywhere(rows, table.colours["ink"], line, [(font_name, 1)], skip_top=3) is not None
               for line in lines)


def page_drawn(table, rows, page):
    """Every line of the page: the kanji standing out, their meanings and the note in plain ink.
    Returns what is missing."""
    missing = []
    for line in page["parts"]:
        for unit in line.split("  "):
            # one kanji, or several that form a word inside the word, then what they mean
            kanji, _, meaning = unit.partition(" ")
            found = drawn(rows, table.colours["accent"], kanji)
            if found is None:
                missing.append(kanji)
            elif reader.find_text(rows, table.colours["ink"], meaning, FONT16,
                                  found[0] + reader.width(kanji + " ", FONT16), found[1]) is None:
                missing.append(meaning)
    for line in page["note"]:
        if drawn(rows, table.colours["ink"], line) is None:
            missing.append(line)
    return missing


def hint_drawn(table, rows, text, right=True):
    colour = table.colours[(FOOT_RIGHT if right else FOOT_LEFT)[table.look]]
    found = drawn(rows, colour, text)
    return found is not None and found[1] > 110


def top_drawn(table, rows, text, standing_out=False):
    found = drawn(rows, table.colours["headAccent" if standing_out else "headInk"], text)
    return found is not None and found[1] < 8


def score_drawn(table, rows, right, asked):
    return drawn(rows, table.colours["good"], "%d of %d right" % (right, asked), reader.TEXT_FACES) is not None


# ---------------------------------------------------------------------------------------------
# Steering
# ---------------------------------------------------------------------------------------------

def go_home(target):
    for _ in range(6):
        if target.info()["screen"] == HOME:
            return True
        target.key("Esc")
    return target.info()["screen"] == HOME


def set_look(target, wanted):
    """From the home screen."""
    current = target.look()
    target.open("settings")
    for _ in range((reader.LOOKS.index(wanted) - reader.LOOKS.index(current)) % len(reader.LOOKS)):
        target.key("Right")
    target.key("Esc")
    target.key("Esc")
    return target.look() == wanted and target.info()["screen"] == HOME


def set_sound(target, on):
    """From the home screen. The row is found by trying: Right on a row changes its value, Left
    puts it back, so that nothing else is left changed."""
    if target.info()["sound"] != on:
        target.open("settings")
        for _ in range(12):
            target.key("Right")
            if target.info()["sound"] == on:
                break
            target.key("Left")
            target.key("Down")
        target.key("Esc")
        target.key("Esc")
    state = target.info()
    return state["sound"] == on and state["screen"] == HOME


# ---------------------------------------------------------------------------------------------
# Sound
# ---------------------------------------------------------------------------------------------

def expect_said(table, before, after, card, when):
    """One clip more, that of the card. Where there can be no sound: none."""
    if not tells_sound(after):
        table.check.note("the device does not tell what it plays: the counts of clips are left out")
        return
    item = table.items[card]
    if can_hear(after) and not table.every_clip and after["plays"] == before["plays"]:
        table.check.note("the memory card has no clip of %s" % card)
    elif can_hear(after):
        table.expect(after["plays"] == before["plays"] + 1 and re.match(clip_of(card, item), after["played"]),
                     "%s is said %s (%d clips more, the last %s)" % (
                         card, when, after["plays"] - before["plays"], after["played"] or "none"))
        table.expect(after["playedAt"] == after["volume"],
                     "%s is said at the volume that is set (%s, set %s)" % (card, after["playedAt"], after["volume"]))
    else:
        table.expect(after["plays"] == before["plays"], "nothing is said %s, for there can be no sound" % when)


def expect_silent(table, before, after, when):
    if tells_sound(after):
        table.expect(after["plays"] == before["plays"],
                     "nothing is said %s (%d clips)" % (when, after["plays"] - before["plays"]))


def check_hearing(table, state, rows, right_hint=None):
    """The answer can be seen: the hint for / is there if and only if there can be sound and no
    other hint needs the room, and the key says the card again."""
    card = state["card"]
    table.expect(state["hears"] == can_hear(state), "%s %s: the key / %s" % (
        card, state["cardState"], "says the card" if can_hear(state) else "is a key like any other"))
    wanted = right_hint if right_hint is not None else ("/: hear" if can_hear(state) else "")
    if wanted:
        table.expect(hint_drawn(table, rows, wanted), "%s %s: the hint \"%s\" is drawn" % (
            card, state["cardState"], wanted))
    if wanted != "/: hear":
        table.expect(not hint_drawn(table, rows, "/: hear"), "%s %s: no hint for / %s" % (
            card, state["cardState"], "beside \"%s\"" % wanted if wanted else "without sound"))
    if can_hear(state):
        table.target.type("/")
        after = table.target.info()
        table.expect(after["card"] == card and after["cardState"] == state["cardState"] and
                     after["page"] == state["page"] and after["typed"] == state["typed"],
                     "%s %s: the key / changes nothing on the screen" % (card, state["cardState"]))
        expect_said(table, state, after, card, "again with the key /")
        return after
    return state


def expect_quiet_question(table, before, after):
    """If the key has opened a question, it has opened it without a sound."""
    if after["screen"] == CARDS and after["cardState"] in ("probe", "asking"):
        expect_silent(table, before, after, "when the question for %s opens" % after["card"])


def check_open_question(table, state):
    """A question is open: the key / must not be heard, nor typed."""
    table.target.type("/")
    table.target.key("Right")
    after = table.target.info()
    table.expect(after["card"] == state["card"] and after["cardState"] == state["cardState"] and
                 after["typed"] == 0 and after["hears"] is False,
                 "%s %s: the key / does nothing while the question is open" % (state["card"], state["cardState"]))
    expect_silent(table, state, after, "for the key / while %s is asked" % state["card"])


# ---------------------------------------------------------------------------------------------
# One sitting
# ---------------------------------------------------------------------------------------------

class Played:
    def __init__(self):
        self.asked = 0
        self.right = 0
        self.met = []          # (card, state) in the order they came
        self.first = set()     # cards seen for the first time
        self.taught = set()
        self.known = set()     # kana typed right at first sight
        self.verdicts = []     # (card, verdict)
        self.two_pages = set()
        self.shared_page = set()
        self.no_pages = set()


def read_pages(table, state, item, turn):
    """The pages of the card, one after the other; `turn` names the key that turns them.
    Leaves the last page open. Returns the last state."""
    card = state["card"]
    expected = pages_of(table.area, item)
    table.expect(state["pages"] == len(expected) and state["page"] == 1,
                 "%s: %d pages, the first is open (the app says page %s of %s)" % (
                     card, len(expected), state["page"], state["pages"]))
    for number, page in enumerate(expected, 1):
        rows = table.picture()
        table.expect(state["says"] == says(page) and state["cut"] is False,
                     "%s page %d shows %s, nothing cut off (the app says %s, cut %s)" % (
                         card, number, says(page), state["says"], state["cut"]))
        missing = page_drawn(table, rows, page)
        table.expect(not missing, "%s page %d: %s drawn%s" % (
            card, number, " and ".join(filter(None, ["the meanings of the kanji" if page["parts"] else "",
                                                     "the note" if page["note"] else ""])),
            " (missing: %s)" % ", ".join(missing) if missing else ""))
        table.expect(prompt_drawn(table, rows, item), "%s page %d: %s is drawn" % (card, number, item["prompt"]))
        if is_kana(item):
            table.expect(typing_answer_drawn(table, rows, item),
                         "%s page %d: what to type, %s, stands beside the kana at 24 px" % (
                             card, number, item["gloss"]))
        else:
            table.expect(reading_drawn(table, rows, item), "%s page %d: the reading %s is drawn" % (
                card, number, item["reading"]))
        last = (number == len(expected))
        if state["cardState"] == "meet":
            table.expect(hint_drawn(table, rows, "Enter: go on" if last else "Enter: more", right=False),
                         "%s page %d: the hint says that Enter %s" % (
                             card, number, "goes on" if last else "brings more"))
            state = check_hearing(table, state, rows)
        elif last:
            state = check_hearing(table, state, rows)
        else:
            following = expected[number]
            hint = ("Tab: more" if page["parts"] else "Tab: kanji") if following["parts"] else (
                "Tab: more" if page["note"] else "Tab: note")
            state = check_hearing(table, state, rows, hint)
        if not last:
            table.target.key(turn)
            state = table.target.info()
            table.expect(state["card"] == card and state["page"] == number + 1,
                         "%s: %s turns to page %d" % (card, turn, number + 1))
    return state


def after_mark(table, state, item, verdict):
    """The card is marked: the mark, the answer, what Tab and / do, then on to the next card."""
    card = state["card"]
    target = table.target
    rows = table.picture()
    table.expect(mark_drawn(table, rows, verdict), "the mark %s is on the screen for %s" % (MARKS[verdict][0], card))
    table.expect(prompt_drawn(table, rows, item), "%s marked: %s is drawn" % (card, item["prompt"]))
    if is_kana(item):
        table.expect(typing_answer_drawn(table, rows, item), "%s marked: what to type, %s, is drawn" % (
            card, item["gloss"]))
        table.expect(top_drawn(table, rows, item["deckName"].capitalize()),
                     "%s marked: the line at the top names the deck" % card)
    elif verdict in ("right", "shown"):
        table.expect(reading_drawn(table, rows, item), "%s marked: the reading %s is drawn" % (card, item["reading"]))
    expected = pages_of(table.area, item)
    first_hint = None
    if expected:
        first_hint = "Tab: kanji" if expected[0]["parts"] else "Tab: note"
    state = check_hearing(table, state, rows, first_hint)
    if not expected:
        table.expect(state["pages"] == 0, "%s has nothing more to say (%s pages)" % (card, state["pages"]))
        target.key("Tab")
        after = target.info()
        table.expect(after["screen"] != CARDS or after["cardState"] != "note",
                     "%s: Tab after the mark goes on, for there is no page to show" % card)
        expect_quiet_question(table, state, after)
        return
    target.key("Tab")
    state = target.info()
    if not table.expect(state["cardState"] == "note" and state["card"] == card and state["verdict"] == verdict,
                        "Tab after the mark shows what %s has to say (the app says %s)" % (card, state["cardState"])):
        return
    rows = table.picture()
    table.expect(mark_drawn(table, rows, verdict), "%s: the mark stays on the pages" % card)
    state = read_pages(table, state, item, "Tab")
    before = state
    target.type(" ")
    after = target.info()
    table.expect(after["screen"] != CARDS or after["cardState"] != "note" or after["card"] != card,
                 "%s: a key on its last page goes on" % card)
    expect_quiet_question(table, before, after)


def start_sitting(table, deck=None):
    """Starts a sitting from the deck, or the course from the home screen. A sitting that starts
    with a question starts without a sound. Returns whether the cards are there."""
    target = table.target
    before = target.info()
    if deck is None:
        target.type("x")
    elif not target.sitting(deck):
        return False
    after = target.info()
    expect_quiet_question(table, before, after)
    return after["screen"] == CARDS


def play_sitting(table, day, probes=(), questions=(), stop_after=None):
    """Plays every card of the sitting that is open. `probes` names what to do with the n-th kana
    asked at first sight (right, wrong, pass), `questions` with the questions in turn (right,
    almost, wrong, shown), a near miss waiting for a card that allows one; after the end of a
    list everything is answered right."""
    target = table.target
    played = Played()
    probed = 0
    waiting = list(questions)
    tried_wrong_copy = False
    tried_help = False
    table.where = "%s day %d" % (table.look, day)
    for _ in range(200):
        state = target.info()
        if state["screen"] != CARDS:
            break
        if stop_after is not None and len(played.met) >= stop_after:
            break
        card = state["card"]
        item = table.items.get(card)
        if not table.expect(item is not None, "the card %s is in the decks" % card):
            target.key("Esc")
            break
        kind = state["cardState"]
        played.met.append((card, kind))
        answer = what_to_type(item)

        if kind == "probe":
            step = probes[probed] if probed < len(probes) else "right"
            probed += 1
            played.first.add(card)
            rows = table.picture()
            table.expect(is_kana(item) and prompt_drawn(table, rows, item),
                         "%s is asked at first sight, drawn as %s at the left, as large as fits" % (
                             card, item["prompt"]))
            table.expect(top_drawn(table, rows, "Do you know it?") and hint_drawn(table, rows, "Tab: no") and
                         hint_drawn(table, rows, "Enter: answer", right=False),
                         "%s at first sight: the question and both hints are drawn" % card)
            check_open_question(table, state)
            if step == "right":
                target.type(answer)
                typing = target.info()
                expect_silent(table, state, typing, "while %s is typed" % card)
                table.expect(drawn(table.picture(), table.colours["type"], answer + "_", reader.TEXT_FACES),
                             "%s: the letters typed, %s, are drawn" % (card, answer))
                target.key("Enter")
                after = target.info()
                played.asked += 1
                played.right += 1
                played.known.add(card)
                played.verdicts.append((card, "right"))
                if table.expect(after.get("cardState") == "marked" and after.get("verdict") == "right" and
                                after["card"] == card and after["answeredToday"] == state["answeredToday"] + 1,
                                "%s typed right at first sight is marked right and counts (the app says %s, %s)" % (
                                    card, after.get("cardState"), after.get("verdict"))):
                    expect_said(table, typing, after, card, "with its mark")
                    after_mark(table, after, item, "right")
                else:
                    target.type(" ")
                continue
            if step == "wrong":
                target.type(wrong_letters(item))
                target.key("Enter")
            else:
                target.key("Tab")
            after = target.info()
            table.expect(after["card"] == card and after["cardState"] == "meet" and
                         after["answeredToday"] == state["answeredToday"],
                         "%s %s at first sight is taught, and nothing is counted (the app says %s)" % (
                             card, "typed wrong" if step == "wrong" else "passed with Tab", after["cardState"]))
            expect_said(table, state, after, card, "when it is met")
            played.met.pop()   # the page that follows is looked at in the next round
            played.met.append((card, "probe"))
            continue

        if kind == "meet":
            if card not in played.first:
                played.first.add(card)
                # a word is said when it is met; a kana was said when its question was closed
                if tells_sound(state) and can_hear(state):
                    table.expect(re.match(clip_of(card, item), state["played"]),
                                 "%s was said when it was met (the last clip is %s)" % (
                                     card, state["played"] or "none"))
            played.taught.add(card)
            expected = pages_of(table.area, item)
            if len(expected) > 1:
                played.two_pages.add(card)
            if expected and expected[0]["parts"] and expected[0]["note"]:
                played.shared_page.add(card)
            rows = table.picture()
            if is_kana(item):
                table.expect(top_drawn(table, rows, item["deckName"].capitalize()),
                             "%s: the line at the top names the deck" % card)
            state = read_pages(table, state, item, "Enter")
            before = state
            target.key("Enter")
            after = target.info()
            table.expect(after["card"] == card and after["cardState"] == "copy",
                         "Enter leads from the last page of %s to typing it" % card)
            expect_silent(table, before, after, "when the page of %s gives way to typing it" % card)
            played.met.pop()
            played.met.append((card, "meet"))
            played.met.append((card, "copy"))
            state = after
            kind = "copy"

        if kind == "copy":
            if card not in played.first:
                played.first.add(card)
                played.no_pages.add(card)
                table.expect(state["pages"] == 0 and not pages_of(table.area, item),
                             "%s has nothing to say and is typed at once (%s pages)" % (card, state["pages"]))
                if tells_sound(state) and can_hear(state):
                    table.expect(re.match(clip_of(card, item), state["played"]),
                                 "%s was said when it was met (the last clip is %s)" % (
                                     card, state["played"] or "none"))
            played.taught.add(card)
            rows = table.picture()
            table.expect(prompt_drawn(table, rows, item), "%s to be typed: %s is drawn" % (card, item["prompt"]))
            if is_kana(item):
                table.expect(typing_answer_drawn(table, rows, item),
                             "%s to be typed: what to type, %s, stands beside the kana" % (card, item["gloss"]))
            else:
                table.expect(reading_drawn(table, rows, item), "%s to be typed: the reading is drawn" % card)
            table.expect(hint_drawn(table, rows, "Type it + Enter", right=False),
                         "%s to be typed: the hint says so" % card)
            if not tried_wrong_copy:
                tried_wrong_copy = True
                target.type(wrong_letters(item))
                target.key("Enter")
                after = target.info()
                table.expect(after["card"] == card and after["cardState"] == "copy" and after["typed"] == 0 and
                             after["answeredToday"] == state["answeredToday"],
                             "a wrong copy of %s costs nothing and the card stays" % card)
                expect_silent(table, state, after, "for a wrong copy")
                rows = table.picture()
                if is_kana(item):
                    table.expect(drawn(rows, table.colours["wait"], "Look again"),
                                 "after a wrong copy \"Look again\" is drawn under the line")
                else:
                    table.expect(top_drawn(table, rows, "Look again, then type", standing_out=True),
                                 "after a wrong copy the line at the top says \"Look again, then type\"")
                state = after
            elif not tried_help and not is_kana(item) and state["romaji"] == "peek":
                tried_help = True
                table.expect(hint_drawn(table, rows, "Tab: help"), "%s to be typed: the hint for Tab is drawn" % card)
                target.key("Tab")
                after = target.info()
                rows = table.picture()
                shown = reader.romaji_as_shown(item["reading"])
                table.expect(after["romajiShown"] is True and after["cardState"] == "copy",
                             "Tab on a new card asks for the romaji")
                table.expect(top_drawn(table, rows, shown, standing_out=True),
                             "the romaji %s is on the screen" % shown)
                expect_silent(table, state, after, "for the romaji")
                state = after
            if is_kana(item) or state["romajiShown"] or state["romaji"] == "never":
                state = check_hearing(table, state, rows if state["typed"] == 0 else table.picture())
            target.type(answer)
            if is_kana(item):
                table.expect(drawn(table.picture(), table.colours["type"], answer + "_", reader.TEXT_FACES),
                             "%s: the letters typed, %s, are drawn" % (card, answer))
            before = target.info()
            target.key("Enter")
            played.asked += 1
            played.right += 1
            after = target.info()
            table.expect(after["answeredToday"] == state["answeredToday"] + 1 and
                         (after["screen"] != CARDS or after["card"] != card),
                         "%s copied, the answer counts and the next card comes" % card)
            if after["screen"] == CARDS and after["cardState"] in ("meet", "copy"):
                expect_said(table, before, after, after["card"], "when it is met")
            else:
                expect_silent(table, before, after, "after %s was copied" % card)
            continue

        if not table.expect(kind == "asking", "%s is asked (the app says %s)" % (card, kind)):
            target.key("Esc")
            break
        # a near miss waits for a card that allows one
        slip = None if is_kana(item) else reader.nearly(item["reading"], item["accepted"])
        step = next((s for s in waiting if s != "almost" or slip), "right")
        if step in waiting:
            waiting.remove(step)
        rows = table.picture()
        table.expect(prompt_drawn(table, rows, item), "%s is asked, drawn as %s" % (card, item["prompt"]))
        ask = "What sound is it?" if is_kana(item) else (
            "How do you say it?" if item["kind"] in ("counter", "number") else "How is it read?")
        if state["romaji"] != "always":
            table.expect(top_drawn(table, rows, ask), "%s: the line at the top asks \"%s\"" % (card, ask))
        table.expect(hint_drawn(table, rows, "Enter: answer", right=False), "%s: the hint for Enter is drawn" % card)
        check_open_question(table, state)
        typed = None
        if step == "right":
            typed = answer
        elif step == "almost":
            typed = reader.to_romaji(slip[0])
        elif step == "wrong":
            typed = "zzz"
        if typed is not None:
            target.type(typed)
            before = target.info()
            expect_silent(table, state, before, "while the answer to %s is typed" % card)
            target.key("Enter")
        else:
            target.key("Tab")   # the romaji
            before = target.info()
            expect_silent(table, state, before, "for the romaji of %s" % card)
            if state["romaji"] == "peek":
                shown = item["gloss"] if is_kana(item) else reader.romaji_as_shown(item["reading"])
                table.expect(before["romajiShown"] is True and before["cardState"] == "asking" and
                             top_drawn(table, table.picture(), shown, standing_out=True),
                             "Tab on the question for %s shows the romaji %s" % (card, shown))
                target.key("Tab")   # the answer
        after = target.info()
        played.asked += 1
        played.right += 1 if step == "right" else 0
        played.verdicts.append((card, step))
        if table.expect(after.get("cardState") == "marked" and after.get("verdict") == step and
                        after["answeredToday"] == state["answeredToday"] + 1,
                        "%s answered %s is marked %s (the app says %s)" % (
                            card, step + (" by " + slip[1] if step == "almost" else ""), step, after.get("verdict"))):
            expect_said(table, before, after, card, "with its mark")
            if is_kana(item) and step == "wrong":
                table.expect(drawn(table.picture(), table.colours["dim"], "You typed " + typed),
                             "%s marked wrong: \"You typed %s\" is drawn" % (card, typed))
            after_mark(table, after, item, step)
        else:
            target.type(" ")
    return played


def check_summary(table, played, introduced):
    state = table.target.info()
    if not table.expect(state["screen"] == SUMMARY, "the sitting ends on the summary (screen %d)" % state["screen"]):
        return state
    rows = table.picture()
    table.expect(score_drawn(table, rows, played.right, played.asked),
                 "the summary shows %d of %d right" % (played.right, played.asked))
    line = "%d new   %d to repeat" % (introduced, state["due"])
    table.expect(drawn(rows, table.colours["ink"], line), "the summary shows \"%s\"" % line)
    return state


def came_back(played, cards):
    """How often each of the cards was asked as a question."""
    return {card: sum(1 for c, s in played.met if c == card and s == "asking") for card in cards}


# ---------------------------------------------------------------------------------------------
# The parts of the check
# ---------------------------------------------------------------------------------------------

def check_course(table):
    target = table.target
    state = target.info()
    table.where = table.look
    table.expect(state["due"] == 0 and state["new"] == 10 and state["day"] == 1 and state["course"] == "hiragana",
                 "day 1 starts with nothing due and ten new kana of the hiragana (%d due, %d new, %s)" % (
                     state["due"], state["new"], state["course"]))
    table.expect(start_sitting(table), "a key on the home screen starts a sitting")
    played = play_sitting(table, 1, probes=["right", "wrong", "pass", "right"], questions=["wrong"])
    kinds = {table.items[card]["deck"] for card, _ in played.met if card in table.items}
    table.expect(kinds == {"hiragana"} and len(played.first) == 10,
                 "the first sitting asks ten hiragana and nothing else (%d cards of %s)" % (
                     len(played.first), ", ".join(sorted(kinds))))
    first_ten = [card for card, state in played.met if state == "probe"]
    table.expect(len(first_ten) == 10 and len(set(first_ten)) == 10, "each of them is asked at first sight, once")
    table.expect(len(played.known) == 8 and len(played.taught) == 2,
                 "eight were known at first sight, two were taught (%d, %d)" % (len(played.known), len(played.taught)))
    seen_taught = {card for card, state in played.met if state in ("meet", "copy")}
    table.expect(not (played.known & seen_taught) and all(n == 0 for n in came_back(played, played.known).values()),
                 "what was known at first sight was not taught and did not come back")
    for card in sorted(played.taught):
        order = [state for c, state in played.met if c == card]
        table.expect(order[:4] == ["probe", "meet", "copy", "asking"],
                     "%s was asked, taught, typed and then came back as a question (%s)" % (card, ", ".join(order)))
    missed = [card for card, verdict in played.verdicts if verdict != "right"]
    table.expect(missed and all(n >= 2 for n in came_back(played, missed).values()),
                 "what was missed came back in the same sitting (%s)" % came_back(played, missed))
    state = check_summary(table, played, 10)
    table.expect(state["answeredToday"] == played.asked and state["seen"] == 10,
                 "%d answers counted, ten cards seen (%d, %d)" % (played.asked, state["answeredToday"], state["seen"]))
    target.type(" ")
    table.expect(target.info()["screen"] == HOME, "a key on the summary leads home")
    return played


def check_words(table):
    target = table.target
    table.where = table.look
    seen = target.info()["seen"]
    table.expect(start_sitting(table, "signs"), "a sitting from the signs starts")
    played = play_sitting(table, 1, questions=["right", "almost", "wrong", "shown"])
    table.expect(len(played.first) == 4 and all(table.items[c]["deck"] == "signs" for c in played.first),
                 "four new signs were met (%d)" % len(played.first))
    with_something = {c for c in played.first if table.items[c]["parts"] or table.items[c]["note"]}
    table.expect(with_something == {c for c, s in played.met if s == "meet"},
                 "those with something to say were met on a page first (%d of 4), the others typed at once"
                 % len(with_something))
    asked_again = {card for card, state in played.met if state == "asking"}
    table.expect(played.first <= asked_again, "every new card came back as a question in the same sitting")
    seen_verdicts = {verdict for _, verdict in played.verdicts}
    for wanted in ("right", "almost", "wrong", "shown"):
        table.expect(wanted in seen_verdicts, "an answer marked %s was seen" % wanted)
    missed = [card for card, verdict in played.verdicts if verdict != "right"]
    table.expect(missed and all(n >= 2 for n in came_back(played, missed).values()),
                 "what was missed came back in the same sitting (%s)" % came_back(played, missed))
    state = check_summary(table, played, 4)
    table.expect(state["seen"] == seen + 4, "four more cards seen (%d)" % state["seen"])
    target.type(" ")
    return played


def check_next_day(table):
    target = table.target
    table.where = table.look
    before = target.info()
    learnt = before["learnt"]
    target.restart()
    state = target.info()
    table.expect(state["screen"] == HOME and state.get("asksForDay") is True and state["seen"] == before["seen"] and
                 state["look"] == table.look and state["sound"] == before["sound"],
                 "after a restart look, sound and progress are kept and the app asks for the day")
    target.type(" ")
    state = target.info()
    table.expect(state["day"] == 1 and state.get("asksForDay") is False, "Space keeps the day")
    target.restart()
    target.key("Enter")
    state = target.info()
    table.expect(state["day"] == 2 and state["answeredToday"] == 0, "Enter starts day 2")
    due = state["due"]
    table.expect(1 <= due < 12 and learnt >= due,
                 "day 2: what was learnt on day 1 and is not known for longer is due (%d learnt, %d due)" % (
                     learnt, due))
    expect_silent(table, before, state, "at the start of a day")

    table.expect(start_sitting(table), "a key on the home screen starts the sitting of day 2")
    played = play_sitting(table, 2)
    # Two cards of one deck rarely follow each other, so a new kana may come between two signs
    # that are due: what is due comes first, not all of it before anything new.
    old = [card for card, state in played.met if state == "asking" and card not in played.first]
    table.expect(len(set(old)) == due and played.met[0][1] == "asking",
                 "the %d cards that are due are asked, one of them first (%d, first %s)" % (
                     due, len(set(old)), played.met[0][1]))
    before_new = [state for _, state in played.met[:due]].count("asking")
    table.expect(before_new >= due - 2, "and nearly all of them before anything new (%d of %d)" % (before_new, due))
    table.expect(len(played.first) == 12 - due and all(table.items[c]["deck"] == "hiragana" for c in played.first),
                 "%d new hiragana follow, which fills the sitting (%d)" % (12 - due, len(played.first)))
    state = check_summary(table, played, len(played.first))
    table.expect(state["seen"] == 14 + len(played.first), "%d cards seen in all (%d)" % (
        14 + len(played.first), state["seen"]))
    target.type(" ")


def check_pages(table):
    """Cards with a note only, with nothing to say, and with meanings and a note."""
    target = table.target
    table.where = table.look
    table.expect(start_sitting(table, "numbers"), "a sitting from the numbers starts")
    played = play_sitting(table, 2)
    noted = [c for c in played.first if table.items[c]["note"] and not table.items[c]["parts"]]
    table.expect(noted and set(noted) <= {c for c, s in played.met if s == "meet"},
                 "numbers with a note were met on a page with it (%s)" % ", ".join(sorted(noted)))
    table.expect(played.no_pages, "a number with nothing to say was typed at once (%s)" % ", ".join(
        sorted(played.no_pages)))
    check_summary(table, played, len(played.first))
    target.type(" ")

    two = set()
    shared = set()
    for _ in range(8):
        if two and shared:
            break
        if not start_sitting(table, "signs"):
            break
        played = play_sitting(table, 2)
        two |= played.two_pages
        shared |= played.shared_page
        target.type(" ")
    table.where = table.look
    table.expect(two, "a sign whose meanings and note take two pages was met (%s)" % ", ".join(sorted(two)))
    table.expect(shared, "a sign whose meanings and note share a page was met (%s)" % ", ".join(sorted(shared)))


def check_without_sound(table, why):
    """A few cards with no sound to be had: nothing is said, no hint for /, and / is any key."""
    target = table.target
    table.where = "%s, %s" % (table.look, why)
    before = target.info()
    table.expect(not can_hear(before), "there can be no sound")
    table.expect(start_sitting(table, "katakana-words"), "a sitting from the katakana words starts")
    played = play_sitting(table, 2, questions=["wrong", "right"], stop_after=9)
    table.where = "%s, %s" % (table.look, why)
    table.expect(len(played.met) >= 9 and any(s == "asking" for _, s in played.met),
                 "cards were met, typed and asked (%d)" % len(played.met))
    state = target.info()
    if tells_sound(state):
        table.expect(state["plays"] == before["plays"], "nothing at all was said (%d clips)" % (
            state["plays"] - before["plays"]))
    # a marked card: the key / goes on like any other
    for _ in range(20):
        state = target.info()
        if state["screen"] != CARDS or state["cardState"] == "asking":
            break
        if state["cardState"] == "copy":
            target.type(what_to_type(table.items[state["card"]]))
        target.key("Enter")
    if table.expect(state["screen"] == CARDS and state["cardState"] == "asking", "a question is open"):
        target.type(what_to_type(table.items[state["card"]]))
        target.key("Enter")
        marked = target.info()
        target.type("/")
        after = target.info()
        table.expect(marked["cardState"] == "marked" and
                     (after["screen"] != CARDS or after["card"] != marked["card"] or after["cardState"] != "marked"),
                     "after the mark the key / goes on like any other")
    go_home(target)


def check_edges(table):
    target = table.target
    table.where = "%s, edges" % table.look
    table.expect(start_sitting(table, "counters"), "a sitting from the counters starts")
    for _ in range(6):
        state = target.info()
        if state["cardState"] == "copy":
            break
        target.key("Enter")
    if not table.expect(state["cardState"] == "copy", "a card is to be typed"):
        go_home(target)
        return
    card = state["card"]
    target.key("Enter")
    target.key("Backspace")
    target.type(" ")
    after = target.info()
    table.expect(after["card"] == card and after["cardState"] == "copy" and after["typed"] == 0 and
                 after["answeredToday"] == state["answeredToday"],
                 "Enter, Backspace and Space on an empty line do nothing")
    target.type("q" * 60)
    after = target.info()
    table.expect(after["typed"] == LONGEST_ANSWER and after["cardState"] == "copy",
                 "a line takes %d letters and no more (%d)" % (LONGEST_ANSWER, after["typed"]))
    rows = table.picture()
    table.expect(prompt_drawn(table, rows, table.items[card]) and hint_drawn(table, rows, "Type it + Enter", False),
                 "with the longest line the card and the hints are still drawn")
    for _ in range(LONGEST_ANSWER + 5):
        target.key("Backspace")
    after = target.info()
    table.expect(after["typed"] == 0 and after["card"] == card, "Backspace empties the line and stops there")
    target.key("Esc")
    after = target.info()
    table.expect(after["screen"] == HOME and after["answeredToday"] == state["answeredToday"],
                 "Esc before any answer leads home and nothing is counted")
    expect_silent(table, state, after, "for all that")

    table.expect(target.sitting("counters"), "the sitting starts again")
    state = target.info()
    table.expect(state["card"] == card, "and brings the same card, which was not learnt (%s)" % state["card"])
    for _ in range(6):
        state = target.info()
        if state["cardState"] == "copy":
            break
        target.key("Enter")
    target.type(what_to_type(table.items[card]))
    target.key("Enter")
    target.key("Button")
    after = target.info()
    table.expect(after["screen"] == SUMMARY and after["answeredToday"] == state["answeredToday"] + 1,
                 "the button on the edge after one answer leads to the summary")
    rows = table.picture()
    table.expect(score_drawn(table, rows, 1, 1), "which shows 1 of 1 right")
    target.key("Esc")
    table.expect(target.info()["screen"] == HOME, "and from there a key leads home")


def check_look(target, look, items, colours, areas, check):
    table = Table(target, look, items, colours, areas, check)
    table.expect(target.fresh(), "progress starts empty")
    table.expect(set_look(target, look), "the look is set, the home screen is back")
    table.expect(set_sound(target, True), "sound is switched on")
    if hasattr(target, "card"):
        target.card(True)
    check_course(table)
    check_words(table)
    check_next_day(table)
    check_pages(table)
    check_edges(table)
    table.where = look
    table.expect(set_sound(target, False), "sound is switched off")
    check_without_sound(table, "sound off")
    if hasattr(target, "card"):
        table.where = look
        table.expect(set_sound(target, True), "sound is switched on again")
        target.card(False)
        check_without_sound(table, "memory card out")
        target.card(True)
    else:
        check.note("the memory card of a device stays where it is: taking it out is checked in the simulator")


def check_every_card(target, look, items, colours, areas, check):
    """Meets every card of every deck and looks at each of its pages."""
    table = Table(target, look, items, colours, areas, check)
    table.expect(target.fresh(), "progress starts empty")
    table.expect(set_look(target, look), "the look is set, the home screen is back")
    table.expect(set_sound(target, False), "sound is switched off")
    met = set()
    for deck in sorted({item["deck"] for item in items.values()}):
        wanted = {card for card, item in items.items() if item["deck"] == deck}
        for _ in range(len(wanted)):
            if wanted <= met or not target.sitting(deck):
                break
            before = len(met)
            for _ in range(200):
                state = target.info()
                if state["screen"] != CARDS:
                    break
                card = state["card"]
                item = items[card]
                table.where = "%s %s" % (look, card)
                if state["cardState"] == "probe":
                    target.key("Tab")
                elif state["cardState"] == "meet":
                    met.add(card)
                    state = read_pages(table, state, item, "Enter")
                    target.key("Enter")
                elif state["cardState"] == "copy":
                    if card not in met:
                        met.add(card)
                        table.expect(not pages_of(table.area, item) and state["cut"] is False,
                                     "nothing to say, and it is typed at once")
                        table.expect(prompt_drawn(table, table.picture(), item), "%s is drawn" % item["prompt"])
                    target.type(what_to_type(item))
                    target.key("Enter")
                elif state["cardState"] == "asking":
                    target.type(what_to_type(item))
                    target.key("Enter")
                    marked = target.info()
                    table.expect(marked.get("verdict") == "right", "typed as the card says, it is marked right (%s)" % (
                        marked.get("verdict")))
                    target.type(" ")
                else:
                    target.type(" ")
            target.type(" ")
            go_home(target)
            if len(met) == before:
                break
        table.where = "%s %s" % (look, deck)
        table.expect(wanted <= met, "every card was met (%d of %d)" % (len(wanted & met), len(wanted)))
        print("%s %s: %d cards" % (look, deck, len(wanted & met)), flush=True)


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    every_card = "--every-card" in arguments
    rest = [a for a in arguments if a not in ("--device", "--every-card")]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS
    unknown = [a for a in rest if a not in reader.LOOKS and a != port]
    if unknown:
        sys.exit("error: %s is neither a look (%s) nor a port" % (", ".join(unknown), ", ".join(reader.LOOKS)))
    part = check_every_card if every_card else check_look

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
                go_home(device)
                part(device, look, items, colours, areas, check)
                print("%s done" % look, flush=True)
        finally:
            restored = device.back()
            after = device.info()
            check.expect(restored and after["look"] == before["look"] and after["day"] == before["day"] and
                         after["seen"] == before["seen"] and after["sound"] == before["sound"],
                         "device: settings and progress are back as they were (look %s, day %d, %d seen, sound %s)" % (
                             after["look"], after["day"], after["seen"], "on" if after["sound"] else "off"))
            check.expect(after["heapLowest"] > 100000,
                         "device: never less than 100 KB of memory free (lowest %d)" % after["heapLowest"])
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=11)
            try:
                part(sim, look, items, colours, areas, check)
            finally:
                sim.close()

    print("%d checks passed, %d failed" % (len(check.passed), len(check.failed)))
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
