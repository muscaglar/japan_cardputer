#!/usr/bin/env python3
"""Reads the app's screens: what is drawn where, in which colour.

Shared by the checks that play the app in the simulator or on a device. Colours and areas are
taken from lib/ui/theme.cpp, the decks from content/decks, so that nothing is written down twice.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardputer_screen import font, rgb565  # noqa: E402
import romaji_reference  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKS = ["techo", "eki", "rpg", "washi"]
FIELDS = ["bg", "ink", "dim", "faint", "accent", "good", "bad", "wait", "row", "rowInk", "type", "bubble",
          "bubbleInk", "bubbleDim"]


def themes():
    """look -> {field: (r, g, b) as the 16-bit panel shows it}, and look -> content area."""
    source = open(os.path.join(ROOT, "lib", "ui", "theme.cpp"), encoding="utf-8").read()
    named = {name: int(value, 16) for name, value in re.findall(r"constexpr uint32_t (k\w+)\s*=\s*0x([0-9A-Fa-f]{6})u", source)}
    colours = {}
    for key, body in re.findall(r'\{ThemeId::\w+, "(\w+)", "[^"]*", "[^"]*",(.*?)\},', source, re.S):
        values = []
        for token in re.findall(r"0x[0-9A-Fa-f]{6}u|k[A-Z]\w+", body):
            value = named[token] if token in named else int(token[2:8], 16)
            values.append(rgb565(((value >> 16) & 255, (value >> 8) & 255, value & 255)))
        colours[key] = dict(zip(FIELDS, values))
    # text that a screen writes into the header: headerInk() and headerAccent() in theme.cpp
    for key, plain, accent in (("techo", 0x786E64, None), ("eki", named["kNavy"], 0xC85F00),
                               ("rpg", None, None), ("washi", 0x82786E, None)):
        def shown(value):
            return rgb565(((value >> 16) & 255, (value >> 8) & 255, value & 255))
        colours[key]["headInk"] = shown(plain) if plain is not None else colours[key]["ink"]
        colours[key]["headAccent"] = shown(accent) if accent is not None else colours[key]["accent"]
    areas = {}
    block = source[source.index("Area contentArea"):]
    block = block[:block.index("\n}")]
    box = r"Area\{(\d+), (\d+), (\d+), (\d+)\}"
    for name, x, y, w, h in re.findall(r"ThemeId::(\w+):\s*return header \? " + box, block):
        areas[name.lower()] = (int(x), int(y), int(w), int(h))
    default = re.search(r"default:\s*return header \? " + box, block)
    for look in LOOKS:
        if look not in areas and default:
            areas[look] = tuple(int(v) for v in default.groups())
    missing = [look for look in LOOKS if look not in colours or look not in areas]
    if missing:
        raise RuntimeError("could not read the looks %s from lib/ui/theme.cpp" % ", ".join(missing))
    return colours, areas


def is_kanji(character):
    """As tools/build_decks.py decides it."""
    code = ord(character)
    return (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0xF900 <= code <= 0xFAFF or
            0x20000 <= code <= 0x323AF or character in "々〆〇")


def kanji_meanings():
    """kanji -> what it means, from content/kanji.tsv. Empty if the table is not there."""
    meanings = {}
    path = os.path.join(ROOT, "content", "kanji.tsv")
    if not os.path.exists(path):
        return meanings
    header = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n").rstrip("\r")
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if header is None:
            header = cells
            continue
        row = dict(zip(header, cells))
        if row.get("kanji") and row.get("meaning"):
            meanings.setdefault(row["kanji"], row["meaning"])
    return meanings


def compiled_parts():
    """item id -> the line about its kanji as it was compiled into lib/core/deck_data.cpp, where the
    table of single kanji and the table of words with a line of their own have both had their say."""
    path = os.path.join(ROOT, "lib", "core", "deck_data.cpp")
    found = {}
    if not os.path.exists(path):
        return found
    text = r'"((?:[^"\\]|\\.)*)"'
    row = re.compile(r"^\s*\{" + ", ".join([text] * 7) + r", -?\d+, \d+, deck::Kind::\w+\},\s*$")
    for line in open(path, encoding="utf-8"):
        match = row.match(line)
        if match:
            cells = [c.replace('\\"', '"').replace("\\\\", "\\") for c in match.groups()]
            found[cells[0]] = cells[6]
    return found


def parts_of(prompt, meanings):
    """The line that says what each kanji of the prompt means, as tools/build_decks.py writes it."""
    kanji = list(dict.fromkeys(c for c in prompt if is_kanji(c)))
    return "  ".join("%s %s" % (c, meanings[c]) for c in kanji if c in meanings)


def decks():
    """item id -> what the deck tables say about it: "deck", "deckName", "kind" (kana, word, counter,
    number), "prompt", "reading", "accepted": [...], "gloss", "note", "parts", "level"."""
    items = {}
    meanings = kanji_meanings()
    compiled = compiled_parts()
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "decks", "*.tsv"))):
        deck = os.path.splitext(os.path.basename(path))[0]
        header = None
        about = {}
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n").rstrip("\r")
            named = re.match(r"#\s*(name-ja|name-en|kind|stage)\s*:(.*)\Z", line)
            if named and header is None:
                about[named.group(1)] = named.group(2).strip()
            if not line.strip() or line.startswith("#"):
                continue
            cells = line.split("\t")
            if header is None:
                header = cells
                continue
            row = dict(zip(header, cells))
            items[row["id"]] = {
                "deck": deck, "prompt": row["prompt"], "reading": row["reading"], "gloss": row.get("gloss", ""),
                "note": row.get("note", ""),
                "accepted": [a for a in row.get("accepted", "").split("|") if a],
                "deckName": about.get("name-en", deck), "kind": about.get("kind", "word"),
                "parts": compiled[row["id"]] if row["id"] in compiled else parts_of(row["prompt"], meanings),
                "level": int(row["level"]) if row.get("level", "").isdigit() else 0,
            }
    return items


def mask(text, font_name):
    """Pixels of the text drawn from the top-left corner, and its width. None if a glyph is missing."""
    f = font(font_name)
    points = set()
    x = 0
    for character in text:
        g = f.glyph(ord(character))
        if g is None:
            return None, 0
        w, h, gx, gy, advance, bitmap = g
        top = f.baseline - gy - h
        for row_index, row in enumerate(bitmap):
            for column_index, ink in enumerate(row):
                if ink:
                    points.add((x + gx + column_index, top + row_index))
        x += advance
    return points, x


def width(text, font_name):
    return mask(text, font_name)[1]


def coloured(rows, colour, x0, y0, x1, y1):
    return {(x, y) for y in range(max(0, y0), min(len(rows), y1)) for x in range(max(0, x0), min(len(rows[0]), x1))
            if rows[y][x] == colour}


def find_text(rows, colour, text, font_name, left, top, slack=0):
    """Whether the text is drawn in that colour with its top-left corner at (left, top).

    With slack, positions up to that many pixels higher or lower count too. Returns the top
    that matched, or None. Pixels of the same colour next to the text, within its box, make it fail.
    """
    points, w = mask(text, font_name)
    if points is None:
        return None
    height = font(font_name).height
    for dy in sorted(range(-slack, slack + 1), key=abs):
        seen = coloured(rows, colour, left, top + dy, left + w, top + dy + height)
        if seen == {(x + left, y + top + dy) for (x, y) in points}:
            return top + dy
    return None


def scaled(points, scale):
    if scale == 1:
        return set(points)
    return {(x * scale + dx, y * scale + dy) for (x, y) in points for dx in range(scale) for dy in range(scale)}


_COUNTED = []   # (rows, colour, pixels of that colour, how many of them lie above and left of each point)


def _counted(rows, colour):
    """The pixels of that colour, and a table that tells in one step how many lie in a box.
    Kept for the last pictures, because a check asks one picture for many texts."""
    for kept_rows, kept_colour, seen, sums in _COUNTED:
        if kept_rows is rows and kept_colour == colour:
            return seen, sums
    seen = set()
    sums = [[0] * (len(rows[0]) + 1)]
    for y, row in enumerate(rows):
        above = sums[-1]
        line = [0] * (len(row) + 1)
        along = 0
        for x, pixel in enumerate(row):
            if pixel == colour:
                along += 1
                seen.add((x, y))
            line[x + 1] = above[x + 1] + along
        sums.append(line)
    _COUNTED.append((rows, colour, seen, sums))
    del _COUNTED[:-12]
    return seen, sums


def find_anywhere(rows, colour, text, faces, skip_top=0):
    """Looks for the text in that colour anywhere on the screen.

    faces: (font name, scale) pairs to try. Returns (left, top, font name, scale) of the first
    place, from the top, where exactly the pixels of the text are in that colour, and no other
    pixel of that colour lies within the box of the text. None if it is nowhere.

    skip_top leaves that many rows at the top of the box out of the comparison, for text that
    something may be drawn over there, as the hooks of the pitch line are over a reading.
    """
    seen, sums = _counted(rows, colour)
    high, wide = len(rows), len(rows[0])
    places = sorted(seen, key=lambda p: (p[1], p[0]))
    for font_name, scale in faces:
        points, w = mask(text, font_name)
        if not points:
            continue
        points = {(x, y) for (x, y) in scaled(points, scale) if y >= skip_top}
        if not points:
            continue
        height = font(font_name).height * scale
        width_px = w * scale
        anchor = min(points, key=lambda p: (p[1], p[0]))
        for (sx, sy) in places:
            left, top = sx - anchor[0], sy - anchor[1]
            x0, x1 = max(0, left), min(wide, left + width_px)
            y0, y1 = max(0, top + skip_top), min(high, top + height)
            if x0 >= x1 or y0 >= y1:
                continue
            if sums[y1][x1] - sums[y0][x1] - sums[y1][x0] + sums[y0][x0] != len(points):
                continue
            if all((x + left, y + top) in seen for (x, y) in points):
                return left, top, font_name, scale
    return None


PROMPT_FACES = [("lgfxJapanGothic_32", 2), ("efontJA_24", 2), ("lgfxJapanGothic_32", 1), ("efontJA_16", 2),
                ("efontJA_24", 1), ("efontJA_16", 1)]
TEXT_FACES = [("efontJA_24", 1), ("efontJA_16", 1)]


def fit_face(text, room, tallest):
    """The face fitFace() in lib/ui/theme.cpp chooses: (font name, scale). The largest of at most
    `tallest` pixels that has every character and keeps the text within `room` pixels."""
    for font_name, scale in PROMPT_FACES[:-1]:
        if font(font_name).height * scale > tallest:
            continue
        points, w = mask(text, font_name)
        if points is not None and w * scale <= room:
            return font_name, scale
    return PROMPT_FACES[-1]


def lines_of(pieces, separator, room, font_name="efontJA_16"):
    """The pieces in lines of at most `room` pixels, broken only between pieces, as the card
    screen breaks a note between words and the meanings of kanji between kanji."""
    lines = []
    line = ""
    for piece in pieces:
        longer = line + separator + piece if line else piece
        if line and width(longer, font_name) > room:
            lines.append(line)
            line = piece
        else:
            line = longer
    if line:
        lines.append(line)
    return lines


def hiragana(text):
    return "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in text)


_SPELLING = None


def _spellings():
    """kana unit -> romaji, chosen as lib/romaji/romaji.cpp chooses it."""
    global _SPELLING
    if _SPELLING is None:
        textbook = {"shi", "chi", "tsu", "fu", "ji", "sha", "shu", "sho", "she", "cha", "chu", "cho", "che", "ja", "ju",
                    "jo", "je"}
        best = {}
        for roma, kana in romaji_reference.TABLE.items():
            score = len(roma)
            if roma[0] in "xlq" or (roma[0] == "c" and roma[1:2] != "h"):
                score += 100
            if roma in textbook:
                score -= 50
            if kana not in best or score < best[kana][0]:
                best[kana] = (score, roma)
        _SPELLING = {kana: roma for kana, (score, roma) in best.items()}
    return _SPELLING


def to_romaji(kana):
    """What to type for the kana, as lib/core/kana.cpp shows it. The long mark is typed as a hyphen."""
    table = _spellings()
    text = hiragana(kana)
    small = "ぁぃぅぇぉゃゅょゎ"
    pieces = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in "っんー":
            pieces.append((c, None))
            i += 1
            continue
        if i + 1 < len(text) and text[i + 1] in small and text[i:i + 2] in table:
            pieces.append((None, table[text[i:i + 2]]))
            i += 2
            continue
        pieces.append((None, table.get(c, c)))
        i += 1
    out = ""
    for index, (mark, roma) in enumerate(pieces):
        following = pieces[index + 1][1] if index + 1 < len(pieces) and pieces[index + 1][0] is None else None
        if mark == "ー":
            out += "-"
        elif mark == "ん":
            out += "n'" if following and following[0] in "aiueoy" else "n"
        elif mark == "っ":
            if not following or following[0] in "aiueon":
                out += "xtsu"
            else:
                out += "t" if following.startswith("ch") else following[0]
        else:
            out += roma
    return out


def romaji_as_shown(kana):
    """The romaji the device shows for the kana: as to_romaji, with the long mark as a vowel."""
    out = ""
    for c in to_romaji(kana):
        if c == "-":
            vowels = [v for v in out if v in "aiueo"]
            out += vowels[-1] if vowels else "-"
        else:
            out += c
    return out


def types_back(kana):
    """Whether typing to_romaji(kana) on the device gives the kana."""
    typed, _ = romaji_reference.convert(to_romaji(kana), punctuation=False, flush=True)
    return typed == hiragana(kana)


def nearly(reading, accepted):
    """A slip a learner would make: (what to type as kana, kind of slip), or None if none can be made."""
    text = hiragana(reading)
    taken = {hiragana(a) for a in accepted} | {text}
    candidates = []
    if "っ" in text:
        candidates.append((text.replace("っ", "", 1), "small tsu"))
    if "ー" in text:
        candidates.append((text.replace("ー", "", 1), "long vowel"))
    if text.endswith("ん") and len(text) > 1:
        candidates.append((text[:-1], "n"))
    for plain, voiced in zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"):
        if text.startswith(plain):
            candidates.append((voiced + text[1:], "voicing"))
        elif text.startswith(voiced):
            candidates.append((plain + text[1:], "voicing"))
    for candidate, kind in candidates:
        if candidate and candidate not in taken and types_back(candidate):
            return candidate, kind
    return None
