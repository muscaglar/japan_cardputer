#!/usr/bin/env python3
"""Reads the guide to how Japanese sounds from cover to cover and checks what the app shows.

    python3 tools/guide_check.py                        # in the simulator, all four looks
    python3 tools/guide_check.py techo                  # one look
    python3 tools/guide_check.py --guide FILE           # the app was built from another table
    <PlatformIO's python> tools/guide_check.py --device [PORT]   # on a Cardputer over USB

What is checked, in every look:
  pages  every page of content/guide.tsv is shown with its title and "2/9" in the header and its
         lines in the 16 px font, evenly spaced, inside the content area, with nothing else
         between them
  keys   Right, Enter, Space and Fn with / turn forward; Left, Backspace and , turn back; the first
         and the last page are where turning ends; other keys do nothing; Esc and the button on
         the edge lead to the menu; the page is still open after coming back
  hints  the footer says how to turn, and the two hints keep 8 pixels between them
  sound  with sound off the footer says so and / plays nothing; with sound on / plays the clips
         of the page one after the other and starts again after the last; the footer names what
         was heard; a page without clips plays nothing; without a memory card the footer says so
  empty  an app built without pages says so, and any key leads back

The app says which page it shows (`info`); the pictures are read to see that it is really drawn.
In the simulator every clip is there, and `info` tells what would have been played. On a device
the clips may be missing on the card: then the footer has to say "No clip". On a device the
owner's settings are kept aside first and put back at the end.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402
from sim_driver import Simulator  # noqa: E402

HOME, MENU, GUIDE = 0, 1, 9
FACE = [("efontJA_16", 1)]   # nothing on this screen may be smaller
HINT_WIDTH = 210             # the footer of the look that has the least room
HINT_GAP = 8
MOST_LINES = 5

# The colours drawFrame() in lib/ui/theme.cpp gives to the four texts of the frame.
TITLE = {"techo": "headInk", "eki": "headInk", "rpg": "ink", "washi": "accent"}
COUNT = {"techo": "headInk", "eki": "headInk", "rpg": "dim", "washi": "headInk"}
LEFT = {"techo": "type", "eki": "headInk", "rpg": "dim", "washi": "ink"}
RIGHT = {"techo": "headInk", "eki": "headAccent", "rpg": "accent", "washi": "accent"}

FORWARD = [("Right", lambda t: t.key("Right")), ("Enter", lambda t: t.key("Enter")),
           ("Space", lambda t: t.type(" ")), ("Fn and /", lambda t: t.fn("/"))]
BACK = [("Left", lambda t: t.key("Left")), ("Backspace", lambda t: t.key("Backspace")),
        (",", lambda t: t.type(",")), ("Fn and ,", lambda t: t.fn(","))]
IDLE = [("Tab", lambda t: t.key("Tab")), ("Up", lambda t: t.key("Up")), ("Down", lambda t: t.key("Down")),
        ("a letter", lambda t: t.type("x")), ("a digit", lambda t: t.type("3")), (";", lambda t: t.type(";")),
        (".", lambda t: t.type("."))]


def read_pages(path):
    """The pages as the table gives them: [{"id", "title", "lines": [...], "clips": [...]}]."""
    pages = []
    if not os.path.exists(path):
        return pages
    header = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n").rstrip("\r")
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if header is None:
            header = cells
            continue
        row = dict(zip(header, cells + [""] * len(header)))
        pages.append({"id": row["id"], "title": row["title"], "lines": row["body"].split("|"),
                      "clips": [clip for clip in row["clips"].split("|") if clip]})
    return pages


def band(rows, top, bottom, left=0, right=None):
    """The picture with everything outside the box made colourless, so that a search stays in it."""
    right = len(rows[0]) if right is None else right
    nothing = (-1, -1, -1)
    return [[pixel if top <= y < bottom and left <= x < right else nothing for x, pixel in enumerate(row)]
            for y, row in enumerate(rows)]


def parts(rows, area):
    x, y, w, h = area
    return {"header": band(rows, 0, y), "content": band(rows, y, y + h, x, x + w), "footer": band(rows, y + h, len(rows))}


def head_that_fits(text, room):
    """As fitted() in lib/ui/screens/guide.cpp."""
    if reader.width(text, FACE[0][0]) <= room:
        return text
    while text:
        text = text[:-1]
        if reader.width(text + "…", FACE[0][0]) <= room:
            return text + "…"
    return ""


def hints(pages, index, state, number, heard):
    """What the footer has to say: (left, right)."""
    ahead = index + 1 < len(pages)
    behind = index > 0
    left = "Enter: next" if ahead else "Del: back" if behind else "Esc: menu"
    clips = pages[index]["clips"]
    if not clips:
        return left, ("Del: back" if ahead and behind else "Esc: menu" if behind else "")
    if not state["sound"]:
        return left, "Sound is off"
    if not state["memoryCard"]:
        return left, "No memory card"
    if number == 0:
        return left, "/: hear"
    which = " %d/%d" % (number, len(clips)) if len(clips) > 1 else ""
    if not heard:
        return left, "No clip" + which
    room = HINT_WIDTH - HINT_GAP - reader.width(left, FACE[0][0])
    said = "/: " + clips[number - 1]
    if reader.width(said + which, FACE[0][0]) <= room:
        return left, said + which
    return left, head_that_fits(said, room)


def go_home(target):
    for _ in range(4):
        if target.info()["screen"] == HOME:
            return True
        target.key("Esc")
    return target.info()["screen"] == HOME


def choose_look(target, wanted):
    """From the home screen: sets the look in the settings and comes back."""
    current = target.look()
    target.open("settings")  # the first row is the look
    for _ in range((reader.LOOKS.index(wanted) - reader.LOOKS.index(current)) % len(reader.LOOKS)):
        target.key("Right")
    target.key("Esc")
    target.key("Esc")
    state = target.info()
    return state["screen"] == HOME and state["look"] == wanted


def set_sound(target, look, colours, areas, wanted):
    """From the home screen: switches sound on or off in the settings and comes back.

    The row is found by reading the screen, so that it may stand anywhere in the list. The row
    that was chosen before is chosen again afterwards: other checks count on the first one.
    """
    if target.info()["sound"] == wanted:
        return True
    target.open("settings")
    value = "off" if wanted else "on"
    moved = 0
    found = False
    while True:
        _, rows = target.frame()
        content = parts(rows, areas[look])["content"]
        label = reader.find_anywhere(content, colours[look]["rowInk"], "Sound", FACE)
        shown = reader.find_anywhere(content, colours[look]["accent"], value, FACE)
        found = label is not None and shown is not None and abs(label[1] - shown[1]) <= 2
        if found or moved == 12:
            break
        target.key("Down")
        moved += 1
    if found:
        target.key("Right")
    for _ in range(moved):
        target.key("Up")
    target.key("Esc")
    target.key("Esc")
    state = target.info()
    return state["screen"] == HOME and state["sound"] == wanted


class Reading:
    """Reads the pictures of one look and remembers where the lines of a page stand."""

    def __init__(self, look, colours, areas, expect):
        self.look = look
        self.colours = colours[look]
        self.area = areas[look]
        self.expect = expect
        self.first = None   # the top of the first line
        self.step = None    # from one line to the next
        self.left = None    # where every line starts

    def frame(self, target, what, title, count, left, right):
        """Header and footer. Returns the three parts of the picture."""
        _, rows = target.frame()
        seen = parts(rows, self.area)
        look = self.look
        self.expect(reader.find_anywhere(seen["header"], self.colours[TITLE[look]], title, FACE) is not None,
                    "%s %s: the header shows the title \"%s\"" % (look, what, title))
        if count:
            self.expect(reader.find_anywhere(seen["header"], self.colours[COUNT[look]], count, FACE) is not None,
                        "%s %s: the header shows %s" % (look, what, count))
        at_left = reader.find_anywhere(seen["footer"], self.colours[LEFT[look]], left, FACE)
        self.expect(at_left is not None, "%s %s: the footer says \"%s\"" % (look, what, left))
        if right:
            at_right = reader.find_anywhere(seen["footer"], self.colours[RIGHT[look]], right, FACE)
            self.expect(at_right is not None, "%s %s: the footer says \"%s\"" % (look, what, right))
            if at_left is not None and at_right is not None:
                end = at_left[0] + reader.width(left, FACE[0][0])
                self.expect(end + HINT_GAP <= at_right[0] and
                            at_right[0] + reader.width(right, FACE[0][0]) <= len(rows[0]),
                            "%s %s: the hints keep %d pixels between them (%d)" % (
                                look, what, HINT_GAP, at_right[0] - end))
        else:
            self.expect(not reader.coloured(seen["footer"], self.colours[RIGHT[look]], len(rows[0]) // 2, 0,
                                            len(rows[0]), len(rows)) or RIGHT[look] == LEFT[look],
                        "%s %s: the right half of the footer is empty" % (look, what))
        return seen

    def page(self, target, page, count, left, right):
        what = "page %s" % count
        seen = self.frame(target, what, page["title"], count, left, right)
        x, y, w, h = self.area
        ink = self.colours["ink"]
        self.expect(len(page["lines"]) <= MOST_LINES, "%s %s: no more than %d lines" % (self.look, what, MOST_LINES))
        drawn = 0
        for index, line in enumerate(page["lines"][:MOST_LINES]):
            if not line.strip():
                continue
            found = reader.find_anywhere(seen["content"], ink, line, FACE)
            if not self.expect(found is not None, "%s %s: the line \"%s\" is drawn at 16 px" % (self.look, what, line)):
                continue
            left_edge, top = found[0], found[1]
            points, _ = reader.mask(line, FACE[0][0])
            alone = len(reader.coloured(seen["content"], ink, x, top, x + w, top + 16)) == len(points)
            self.expect(alone, "%s %s: nothing else stands beside \"%s\"" % (self.look, what, line))
            if self.left is None:
                self.left = left_edge
            if self.first is None and index == 0:
                self.first = top
            elif self.step is None and self.first is not None:
                self.step = (top - self.first) // index
            if self.first is not None and (index == 0 or self.step is not None):
                wanted = self.first + index * (self.step or 0)
                self.expect(top == wanted and left_edge == self.left and (self.step is None or self.step >= 17),
                            "%s %s: line %d stands at %d, %d (expected %d, %d)" % (
                                self.look, what, index + 1, left_edge, top, self.left, wanted))
            drawn += 1
        every = reader.coloured(seen["content"], ink, x, y, x + w, y + h)
        wanted = sum(len(reader.mask(line, FACE[0][0])[0]) for line in page["lines"][:MOST_LINES] if line.strip())
        self.expect(len(every) == wanted, "%s %s: the page shows its %d lines and nothing more" % (self.look, what, drawn))


def read_through(target, look, pages, reading, expect):
    """From the first page to the last and back, with every key that turns."""
    total = len(pages)
    for index, page in enumerate(pages):
        state = target.info()
        count = "%d/%d" % (index + 1, total)
        expect(state["screen"] == GUIDE and state["page"] == index + 1 and state["pageId"] == page["id"] and
               state["clips"] == len(page["clips"]) and state["clipNumber"] == 0 and state["clip"] == "",
               "%s: page %s is %s, clips %d, none played (the app says page %s, %s, clips %s)" % (
                   look, count, page["id"], len(page["clips"]), state.get("page"), state.get("pageId"),
                   state.get("clips")))
        left, right = hints(pages, index, state, 0, False)
        reading.page(target, page, count, left, right)
        if index + 1 < total:
            name, press = FORWARD[index % len(FORWARD)]
            press(target)
            expect(target.info()["page"] == index + 2, "%s: %s turns from page %d to page %d" % (
                look, name, index + 1, index + 2))

    for name, press in FORWARD:
        press(target)
        state = target.info()
        expect(state["screen"] == GUIDE and state["page"] == total, "%s: %s on the last page stays there" % (look, name))
    for name, press in IDLE:
        press(target)
        state = target.info()
        expect(state["screen"] == GUIDE and state["page"] == total, "%s: %s does nothing" % (look, name))

    for index in range(total - 1, 0, -1):
        name, press = BACK[index % len(BACK)]
        press(target)
        expect(target.info()["page"] == index, "%s: %s turns back from page %d to page %d" % (
            look, name, index + 1, index))
    for name, press in BACK:
        press(target)
        state = target.info()
        expect(state["screen"] == GUIDE and state["page"] == 1, "%s: %s on the first page stays there" % (look, name))


def turn_to(target, wanted):
    for _ in range(64):
        page = target.info()["page"]
        if page == wanted:
            return True
        target.key("Right" if page < wanted else "Left")
    return False


def listen(target, look, pages, index, reading, expect, note):
    """Plays the clips of one page, once round and one more."""
    page = pages[index]
    total = len(page["clips"])
    count = "%d/%d" % (index + 1, len(pages))
    before = target.info()
    simulated = "plays" in before
    folders = []
    silent = 0
    for press in range(total + 1):
        number = press % total + 1
        target.type("/")
        state = target.info()
        expect(state["screen"] == GUIDE and state["page"] == index + 1 and state["clipNumber"] == number,
               "%s page %s: press %d of / asks for clip %d (the app says %s)" % (
                   look, count, press + 1, number, state.get("clipNumber")))
        if simulated:
            wanted = r"/audio/([fm])/guide/%s-%d\.wav" % (re.escape(page["id"]), number)
            path = re.fullmatch(wanted, state["played"])
            expect(state["heard"] is True and path is not None and state["clip"] == state["played"] and
                   state["plays"] == before["plays"] + press + 1 and state["playedAt"] == state["volume"],
                   "%s page %s: clip %d is played once, as %s at volume %d" % (
                       look, count, number, state["played"], state["volume"]))
            if path:
                folders.append(path.group(1))
        elif state["heard"]:
            expect(re.fullmatch(r"/audio/[fm]/guide/%s-%d\.wav" % (re.escape(page["id"]), number), state["clip"])
                   is not None, "%s page %s: clip %d is played as %s" % (look, count, number, state["clip"]))
        else:
            silent += 1
        left, right = hints(pages, index, state, number, state["heard"])
        reading.frame(target, "page %s after clip %d" % (count, number), page["title"], count, left, right)

    if simulated:
        voice = before["voice"]
        if voice == "both":
            expect(all(a != b for a, b in zip(folders, folders[1:])),
                   "%s page %s: the voices take turns (%s)" % (look, count, " ".join(folders)))
        else:
            expect(set(folders) == {voice[0]}, "%s page %s: the voice is %s (%s)" % (look, count, voice, " ".join(folders)))
    elif silent:
        note("note %s page %s: clips missing on the memory card: %d of %d; the footer said so" % (
            look, count, min(silent, total), total))


def sounds(target, look, pages, reading, colours, areas, expect, note):
    """What / does: with sound off, with sound on, on a page without clips, without a card."""
    with_clips = [i for i, page in enumerate(pages) if page["clips"]]
    without = [i for i, page in enumerate(pages) if not page["clips"]]
    if not with_clips:
        note("note %s: no page has clips: hearing was not checked" % look)
        return
    # the page with the most clips, and the one whose clip needs the most room
    chosen = sorted({max(with_clips, key=lambda i: len(pages[i]["clips"])),
                     max(with_clips, key=lambda i: max(reader.width(clip, FACE[0][0]) for clip in pages[i]["clips"]))})
    first = chosen[0]
    count = "%d/%d" % (first + 1, len(pages))

    def enter(sound):
        target.key("Esc")
        target.key("Esc")
        expect(set_sound(target, look, colours, areas, sound), "%s: sound is switched %s in the settings" % (
            look, "on" if sound else "off"))
        target.open("guide")

    # sound off
    expect(turn_to(target, first + 1), "%s: page %s is reached" % (look, count))
    enter(False)
    state = target.info()
    expect(state["screen"] == GUIDE and state["page"] == first + 1,
           "%s: coming back to the guide opens page %s again" % (look, count))
    target.type("/")
    after = target.info()
    expect(after["page"] == first + 1 and after["clipNumber"] == 0 and after["clip"] == "" and
           after.get("plays") == state.get("plays"), "%s page %s: with sound off / plays nothing" % (look, count))
    left, right = hints(pages, first, after, 0, False)
    reading.frame(target, "page %s with sound off" % count, pages[first]["title"], count, left, right)

    # sound on
    enter(True)
    state = target.info()
    if not state["memoryCard"]:
        target.type("/")
        after = target.info()
        expect(after["clipNumber"] == 0 and after["clip"] == "", "%s page %s: without a memory card / plays nothing" % (
            look, count))
        left, right = hints(pages, first, after, 0, False)
        reading.frame(target, "page %s without a memory card" % count, pages[first]["title"], count, left, right)
        note("note %s: no memory card in the device: hearing was not checked" % look)
        return
    left, right = hints(pages, first, state, 0, False)
    reading.frame(target, "page %s with sound on" % count, pages[first]["title"], count, left, right)
    for index in chosen:
        expect(turn_to(target, index + 1), "%s: page %d/%d is reached" % (look, index + 1, len(pages)))
        listen(target, look, pages, index, reading, expect, note)

    # turning away forgets what was heard
    last = chosen[-1]
    away = last - 1 if last > 0 else last + 1
    if 0 <= away < len(pages):
        turn_to(target, away + 1)
        turn_to(target, last + 1)
        state = target.info()
        expect(state["clipNumber"] == 0 and state["clip"] == "" and state["heard"] is False,
               "%s page %d/%d: after turning away and back no clip counts as played" % (look, last + 1, len(pages)))
        target.type("/")
        expect(target.info()["clipNumber"] == 1, "%s page %d/%d: the first press plays the first clip again" % (
            look, last + 1, len(pages)))

    # a page without clips
    if without:
        index = without[0]
        count = "%d/%d" % (index + 1, len(pages))
        turn_to(target, index + 1)
        state = target.info()
        target.type("/")
        after = target.info()
        expect(after["screen"] == GUIDE and after["page"] == index + 1 and after["clipNumber"] == 0 and
               after.get("plays") == state.get("plays"), "%s page %s: without clips / plays nothing" % (look, count))
        left, right = hints(pages, index, after, 0, False)
        reading.frame(target, "page %s, which has no clips," % count, pages[index]["title"], count, left, right)
    else:
        note("note %s: every page has clips: a page without was not checked" % look)

    # without a memory card: only the simulator can take it out
    if hasattr(target, "card"):
        count = "%d/%d" % (first + 1, len(pages))
        turn_to(target, first + 1)
        target.card(False)
        state = target.info()
        target.type("/")
        after = target.info()
        expect(after["clipNumber"] == state["clipNumber"] and after["clip"] == state["clip"] and
               after["plays"] == state["plays"], "%s page %s: without a memory card / plays nothing" % (look, count))
        left, right = hints(pages, first, after, 0, False)
        reading.frame(target, "page %s without a memory card" % count, pages[first]["title"], count, left, right)
        target.card(True)


def empty(target, look, reading, expect):
    state = target.info()
    expect(state["pages"] == 0 and state["page"] == 0 and state["pageId"] == "" and state["clip"] == "",
           "%s: the app has no pages" % look)
    seen = reading.frame(target, "without pages", "Sounds", "", "Any key: back", "")
    expect(reader.find_anywhere(seen["content"], reading.colours["ink"], "The guide has no pages.", FACE) is not None,
           "%s: the screen says that the guide has no pages" % look)
    target.type("/")
    expect(target.info()["screen"] == MENU, "%s: any key leads back to the menu" % look)
    target.key("Esc")


def play(target, look, pages, colours, areas, expect, note):
    before = target.info()
    target.open("guide")
    state = target.info()
    expect(state["screen"] == GUIDE, "%s: the menu leads to the guide" % look)
    reading = Reading(look, colours, areas, expect)
    if not expect(state.get("pages") == len(pages), "%s: the app has the %d pages of the table (it says %s)" % (
            look, len(pages), state.get("pages"))):
        target.key("Esc")
        target.key("Esc")
        return
    if not pages:
        empty(target, look, reading, expect)
        return

    # The app remembers the page that was open.
    expect(turn_to(target, 1), "%s: the first page is reached" % look)
    read_through(target, look, pages, reading, expect)
    sounds(target, look, pages, reading, colours, areas, expect, note)

    expect(target.info()["screen"] == GUIDE, "%s: the guide is still open" % look)
    target.key("Esc")
    expect(target.info()["screen"] == MENU, "%s: Esc leads to the menu" % look)
    target.key("Esc")
    target.open("guide")
    target.key("Button")
    expect(target.info()["screen"] == MENU, "%s: the button on the edge leads to the menu" % look)
    target.key("Esc")
    expect(set_sound(target, look, colours, areas, before["sound"]), "%s: sound is %s again" % (
        look, "on" if before["sound"] else "off"))


def main():
    arguments = sys.argv[1:]
    on_device = "--device" in arguments
    table = os.path.join(reader.ROOT, "content", "guide.tsv")
    if "--guide" in arguments:
        at = arguments.index("--guide")
        if at + 1 >= len(arguments):
            sys.exit("error: --guide needs a file")
        table = arguments[at + 1]
        del arguments[at:at + 2]
        if not os.path.exists(table):
            sys.exit("error: %s does not exist" % table)
    rest = [a for a in arguments if a != "--device"]
    port = next((a for a in rest if a.startswith("/dev/")), None)
    looks = [a for a in rest if a in reader.LOOKS] or reader.LOOKS

    pages = read_pages(table)
    colours, areas = reader.themes()
    problems = []
    notes = []

    def expect(condition, message):
        (notes if condition else problems).append(("ok   " if condition else "FAIL ") + message)
        return bool(condition)

    def note(message):
        notes.append(message)

    if os.path.exists(table):
        inside = os.path.abspath(table).startswith(reader.ROOT + os.sep)
        print("%d pages in %s" % (len(pages), os.path.relpath(table, reader.ROOT) if inside else table), flush=True)
    else:
        print("no content/guide.tsv: the app is expected to have no pages", flush=True)
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
            kept = expect(device.keep(), "device: settings and progress are kept aside")
            try:
                for look in looks:
                    expect(choose_look(device, look), "%s: the look is set and the home screen is back" % look)
                    play(device, look, pages, colours, areas, expect, note)
                    print("%s done" % look, flush=True)
            finally:
                if kept:
                    expect(device.back(), "device: settings and progress are put back")
            after = device.info()
            expect(after["look"] == before["look"] and after["sound"] == before["sound"],
                   "device: look and sound are as they were (%s, sound %s)" % (
                       before["look"], "on" if before["sound"] else "off"))
            expect(after["screen"] == HOME, "device: left on the home screen")
            lost = before["heapFree"] - after["heapFree"]
            expect(lost < 8192, "device: memory after the guide is within 8 KB of before (%d bytes less, "
                                "lowest ever %d)" % (lost, after["heapLowest"]))
        finally:
            device.close()
    else:
        for look in looks:
            sim = Simulator(seed=200 + reader.LOOKS.index(look))
            try:
                expect(choose_look(sim, look), "%s: the look is set and the home screen is back" % look)
                play(sim, look, pages, colours, areas, expect, note)
            finally:
                sim.close()

    for line in notes:
        print(line)
    for line in problems:
        print(line)
    print("%d checks passed, %d failed" % (sum(1 for line in notes if line.startswith("ok")), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
