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
FONTS = [("lgfxJapanGothic_32", 32), ("efontJA_24", 24), ("efontJA_16", 16), ("efontJA_12", 12)]


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
    areas = {}
    block = source[source.index("Area contentArea"):]
    for name, x, y, w, h in re.findall(r"ThemeId::(\w+):\s*return \{(\d+), (\d+), (\d+), (\d+)\}", block):
        areas[name.lower()] = (int(x), int(y), int(w), int(h))
    default = re.search(r"default:\s*return \{(\d+), (\d+), (\d+), (\d+)\}", block)
    for look in LOOKS:
        if look not in areas and default:
            areas[look] = tuple(int(v) for v in default.groups())
    missing = [look for look in LOOKS if look not in colours or look not in areas]
    if missing:
        raise RuntimeError("could not read the looks %s from lib/ui/theme.cpp" % ", ".join(missing))
    return colours, areas


def decks():
    """item id -> {"deck", "prompt", "reading", "accepted": [...], "gloss"} from the deck tables."""
    items = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "decks", "*.tsv"))):
        deck = os.path.splitext(os.path.basename(path))[0]
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
            items[row["id"]] = {
                "deck": deck, "prompt": row["prompt"], "reading": row["reading"], "gloss": row.get("gloss", ""),
                "accepted": [a for a in row.get("accepted", "").split("|") if a],
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
