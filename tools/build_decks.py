#!/usr/bin/env python3
"""Checks the deck files and compiles them into the firmware.

    python3 tools/build_decks.py              # check; without errors, write the two files below
    python3 tools/build_decks.py --check      # check only, write nothing
    python3 tools/build_decks.py --offline    # without the dictionary and the accent list

Reads content/decks/*.tsv and, where they exist, the tables beside that folder:
    buddy.tsv   what the buddy on the home screen says
    kanji.tsv   what each kanji means, for the line of a card that explains its prompt
    parts.tsv   that line written by hand, for the words that kanji.tsv does not explain
    guide.tsv   the pages of the guide to how Japanese sounds
Writes lib/core/deck_data.cpp and content/ids.txt. The format and the rules are described in
content/README.md.

Every finding is printed as "file:line: error: message" or "file:line: warning: message", followed
by one line per deck. The exit code is 0 only when there are no errors: 1 when a deck has one, 2
when the tool could not run. Nothing is written when there is an error.

The dictionary checks need files that are not in the repository, in local/cache/ (or in the
folder given with --cache):
    jmdict_index.json     JMdict as {written form or kana: [{"kana": [...], "gloss": [...]}]}
    accents.txt           the Kanjium accent list: word TAB reading TAB accent numbers
    kanjidic_index.json   KANJIDIC as {kanji: {"meanings": [...]}}. Where it is missing, kanji.tsv
                          is not compared with it, and a note says so.
The glyph checks need the M5GFX sources that PlatformIO downloads (pio pkg install -e cardputer).

Uses only the Python standard library.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import cardputer_screen  # noqa: E402
import romaji_reference  # noqa: E402

COLUMNS = ["id", "prompt", "reading", "accent", "accepted", "gloss", "note", "level", "source"]
BUDDY_COLUMNS = ["id", "mood", "ja", "en"]
KINDS = {"kana": "Kana", "word": "Word", "counter": "Counter", "number": "Number"}
DECK_ORDER = ["hiragana", "katakana", "numbers", "counters", "katakana-words", "signs"]
KANJI_COLUMNS = ["kanji", "meaning", "basis", "words"]
PARTS_FILE_COLUMNS = ["prompt", "parts", "reason"]
GUIDE_COLUMNS = ["id", "title", "body", "clips"]
GUIDE_TITLE_COLUMNS = 20
GUIDE_LINE_COLUMNS = 27
GUIDE_LINES = 5
KANJI_MEANING_LENGTH = 12
PARTS_COLUMNS = 54     # two lines of 27 letters
JMDICT_BASIS = "JMdict: "
MOODS = ["greeting", "start", "right", "streak", "wrong", "almost", "finish", "back", "low-battery", "idle"]

GLOSS_COLUMNS = 32
NOTE_COLUMNS = 52      # two lines of 26 letters; a Japanese character counts as two
BUDDY_JA_LENGTH = 15
BUDDY_EN_LENGTH = 34
MAX_ITEMS = 65535      # Deck::count is 16 bits wide
MAX_ACCENT = 127       # Item::accent is 8 bits wide
LONGEST_ANSWER = 48    # letters the answer line takes: kLongestAnswer in lib/ui/screens/cards.cpp

TEXT_FONTS = ["efontJA_16", "efontJA_12"]          # every character must be in both
PROMPT_FONTS = ["lgfxJapanGothic_32", "efontJA_24"]  # a prompt that needs another font is drawn smaller
MEASURE_FONT = "efontJA_12"
MEASURE_UNIT = 6                                   # pixels per Latin letter in that font

ID_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*\Z")
META_PATTERN = re.compile(r"#\s*(name-ja|name-en|kind|stage)\s*:(.*)\Z")
MEANING_PATTERN = re.compile(r"[a-z]+([ -][a-z]+)*\Z")
BUDDY_PUNCTUATION = "、。！？「」〜・"

LICENCE = [
    "Readings and meanings are checked against JMdict, the meanings of single kanji against",
    "KANJIDIC (both: Electronic Dictionary Research and Development Group, CC BY-SA 4.0). Pitch",
    "accents come from the accent list of the Kanjium project (CC BY-SA 4.0). The decks themselves",
    "are therefore shared under CC BY-SA 4.0.",
]


def stop(message):
    """For what is wrong with the call or the machine, not with the decks."""
    sys.stderr.write("build_decks: %s\n" % message)
    sys.exit(2)


# ---------------------------------------------------------------------------------------------
# Kana
# ---------------------------------------------------------------------------------------------

def is_kana(ch):
    cp = ord(ch)
    return (0x3041 <= cp <= 0x3096 or 0x30A1 <= cp <= 0x30FA or cp == 0x30FC or
            cp in (0x309D, 0x309E, 0x30FD, 0x30FE))


def is_kanji(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF or
            0x20000 <= cp <= 0x323AF or ch in "々〆〇")


def to_hiragana(text):
    """Katakana to hiragana, as kana::toHiragana does it."""
    out = []
    for ch in text:
        cp = ord(ch)
        if 0x30A1 <= cp <= 0x30F6 or cp in (0x30FD, 0x30FE):
            cp -= 0x60
        out.append(chr(cp))
    return "".join(out)


def beat_count(text):
    """Number of beats, as kana::beats counts them: a small kana belongs to the beat before it."""
    count = 0
    for ch in to_hiragana(text):
        if ch in "ぁぃぅぇぉゃゅょゎ" and count:
            continue
        count += 1
    return count


TEXTBOOK = ("shi", "chi", "tsu", "fu", "ji", "sha", "shu", "sho", "she", "cha", "chu", "cho", "che",
            "ja", "ju", "jo", "je")


def preference(roma):
    """Lower is better. As preference() in lib/romaji/romaji.cpp: the textbook spelling wins, and
    the keyboard shortcuts that start with x, l, q or c lose."""
    score = len(roma)
    if roma[0] in "xlq" or (roma[0] == "c" and roma[1:2] != "h"):
        score += 100
    if roma in TEXTBOOK:
        score -= 50
    return score


def _spellings():
    """kana -> the romaji to type it with, chosen as romaji::spelling chooses it."""
    best = {}
    for roma, kana in romaji_reference.TABLE.items():
        if kana not in best or preference(roma) < preference(best[kana]):
            best[kana] = roma
    return best


SPELLINGS = _spellings()
SMALL_TSU = "xtsu"


def typing_romaji(kana):
    """Returns (romaji, problem). The romaji types `kana` on the device; problem is None then.

    Follows kana::toRomaji in lib/core/kana.cpp: the spelling of every kana comes from the
    converter's table, a doubled consonant stands for っ, n' for ん before a vowel or y. Differs
    where that rendering would not type the same kana: ー is a hyphen, っ before m is typed xtsu,
    and ん before ん is n'. What comes out is typed back and compared, so a mistake here shows as
    an error and never as a wrong answer on the device.
    """
    text = to_hiragana(kana)
    tokens = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "っんー":
            tokens.append((ch, ""))
            i += 1
            continue
        pair = text[i:i + 2]
        if len(pair) == 2 and pair in SPELLINGS:
            tokens.append(("syllable", SPELLINGS[pair]))
            i += 2
        elif ch in SPELLINGS:
            tokens.append(("syllable", SPELLINGS[ch]))
            i += 1
        else:
            return None, "%s cannot be typed" % kana[i]

    out = []
    for k, (kind, roma) in enumerate(tokens):
        after_kind, after = tokens[k + 1] if k + 1 < len(tokens) else ("", "")
        if kind == "ー":
            out.append("-")
        elif kind == "ん":
            out.append("n")
        elif kind == "っ":
            # mm and nn are read as ん, and a vowel cannot be doubled
            if after_kind == "syllable" and after[0] not in "aiueonm":
                out.append("t" if after.startswith("ch") else after[0])
            else:
                out.append(SMALL_TSU)
        else:
            out.append(roma)
    for k in range(len(out) - 1):
        # n before a vowel, y or another n would be read as the start of the next syllable
        if tokens[k][0] == "ん" and (tokens[k + 1][0] == "ん" or out[k + 1][0] in "aiueoy"):
            out[k] = "n'"
    romaji = "".join(out)
    typed, _ = romaji_reference.convert(romaji, flush=True)
    if typed != text:
        return romaji, "%s types %s" % (romaji, typed)
    return romaji, None


# ---------------------------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------------------------

def load_fonts():
    try:
        for name in TEXT_FONTS + PROMPT_FONTS:
            cardputer_screen.font(name)
    except SystemExit as problem:
        stop("the glyph checks need the device fonts. %s" % problem)


def missing_glyphs(text, font_name):
    font = cardputer_screen.font(font_name)
    return "".join(dict.fromkeys(ch for ch in text if not font.has(ch)))


def columns(text):
    """Width in Latin letters: a Japanese character is as wide as two."""
    font = cardputer_screen.font(MEASURE_FONT)
    total = 0
    for ch in text:
        advance = font.advance(ch) if font.has(ch) else font.max_width
        total += (advance + MEASURE_UNIT - 1) // MEASURE_UNIT
    return total


# ---------------------------------------------------------------------------------------------
# Dictionary and accent list
# ---------------------------------------------------------------------------------------------

class Reference:
    def __init__(self, folder):
        index_path = os.path.join(folder, "jmdict_index.json")
        accent_path = os.path.join(folder, "accents.txt")
        for path in (index_path, accent_path):
            if not os.path.exists(path):
                stop("%s not found. Put it there, or run with --offline to skip the dictionary checks."
                     % display(path))
        try:
            with open(index_path, encoding="utf-8") as handle:
                self.index = json.load(handle)
            with open(accent_path, encoding="utf-8") as handle:
                accent_lines = handle.read().split("\n")
        except (OSError, ValueError) as problem:
            stop("the dictionary in %s cannot be read: %s" % (display(folder), problem))
        self.accent_list = {}
        for line in accent_lines:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) != 3:
                continue
            word, reading, numbers = parts
            values = []
            for token in numbers.split(","):
                match = re.fullmatch(r"(?:\([^()]*\))*(\d+)", token.strip())
                if match:
                    values.append(int(match.group(1)))
            if values:
                self.accent_list.setdefault(word, []).append((reading, values, "(" in numbers))

    def readings(self, word):
        """Every reading JMdict gives for the headword, in hiragana. None when it is no headword."""
        entries = self.index.get(word)
        if not entries:
            return None
        found = []
        for entry in entries:
            for reading in entry.get("kana", []):
                found.append(to_hiragana(reading))
        return list(dict.fromkeys(found))

    def accents(self, word, reading):
        """(numbers, depends on the part of speech) for exactly this word with this reading, or None.

        A word written in kana has an empty reading in the list: it is its own reading. Readings are
        compared in hiragana, because the script does not change how a word is said.
        """
        wanted = to_hiragana(reading)
        numbers = []
        tagged = False
        for listed, values, has_tags in self.accent_list.get(word, []):
            if to_hiragana(listed if listed else word) == wanted:
                numbers += values
                tagged = tagged or has_tags
        if not numbers:
            return None
        return list(dict.fromkeys(numbers)), tagged


# ---------------------------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------------------------

def display(path):
    path = os.path.abspath(path)
    if path.startswith(ROOT + os.sep):
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    return path


def printable(text):
    """Names what cannot be seen (U+000D, U+200B, U+3000), so that a finding stays on one line."""
    return "".join(ch if ch == " " or unicodedata.category(ch)[0] not in "CZ" else "U+%04X" % ord(ch)
                   for ch in text)


class Findings:
    def __init__(self):
        self.found = []    # (path, line, text)
        self.counts = {}   # path -> [errors, warnings]
        self.notes = []

    def _add(self, path, line, severity, message):
        text = "%s:%d: %s: %s" % (display(path), line, severity, printable(message))
        self.found.append((path, line, text))
        self.counts.setdefault(path, [0, 0])[0 if severity == "error" else 1] += 1

    def lines(self):
        """In the order in which the files were first mentioned, then by line."""
        order = {}
        for path, _, _ in self.found:
            order.setdefault(path, len(order))
        return [text for _, _, text in sorted(self.found, key=lambda f: (order[f[0]], f[1]))]

    def error(self, path, line, message):
        self._add(path, line, "error", message)

    def warning(self, path, line, message):
        self._add(path, line, "warning", message)

    def note(self, message):
        self.notes.append(message)

    def errors(self, path=None):
        if path is not None:
            return self.counts.get(path, [0, 0])[0]
        return sum(c[0] for c in self.counts.values())

    def warnings(self, path=None):
        if path is not None:
            return self.counts.get(path, [0, 0])[1]
        return sum(c[1] for c in self.counts.values())


def plural(count, word):
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def fnv1a(text):
    """deck::key in lib/core/deck.cpp."""
    value = 2166136261
    for byte in text.encode("utf-8"):
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


# ---------------------------------------------------------------------------------------------
# Reading the tables
# ---------------------------------------------------------------------------------------------

def read_table(path, wanted, findings):
    """Returns (names, rows). names: {"name-ja": (text, line), ...} from the comments above the
    header row. rows: [(line number, fields)]; fields is None for a row that cannot be used.
    Returns (names, None) when there is no table in the file, (None, None) when it cannot be read."""
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            text = handle.read()
    except UnicodeDecodeError as problem:
        line = problem.object.count(b"\n", 0, problem.start) + 1
        findings.error(path, line, "not UTF-8: %s" % problem.reason)
        return None, None
    except OSError as problem:
        findings.error(path, 1, "cannot be read: %s" % problem.strerror)
        return None, None

    if text.startswith("\ufeff"):
        findings.warning(path, 1, "byte order mark at the start of the file; save it as UTF-8 without one")
        text = text[1:]
    if not text.strip():
        findings.error(path, 1, "the file is empty")
        return None, None
    lines = re.split("\r\n|\r|\n", text)
    if "\r" in text:
        first = len(re.split("\r\n|\r|\n", text[:text.index("\r")]))
        findings.warning(path, first, "the line ends with a carriage return; save the file with Unix line ends")
    if lines[-1] == "":
        lines.pop()

    names = {}
    rows = []
    header_seen = False
    for number, line in enumerate(lines, 1):
        name = META_PATTERN.match(line)
        if line.startswith("#") and not name:
            continue
        hidden = "".join(dict.fromkeys(ch for ch in line if ch != "\t" and
                                       unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp")))
        if hidden:
            findings.error(path, number, "invisible character %s; remove it" % " ".join(hidden))
            line = "".join(ch for ch in line if ch not in hidden)
            name = META_PATTERN.match(line)
        if name:
            key, value = name.group(1), name.group(2).strip()
            if key in names:
                findings.error(path, number, "%s is given twice" % key)
            else:
                names[key] = (value, number)
                if header_seen:
                    findings.error(path, number, "%s must stand above the header row" % key)
            continue
        if not line.strip(" "):
            continue
        fields = line.split("\t")
        if not header_seen:
            header_seen = True
            if fields != wanted:
                findings.error(path, number, "header row must be: %s" % " ".join(wanted))
                return names, None
            continue
        if not line.strip():
            findings.error(path, number, "a row without values; remove it")
            rows.append((number, None))
            continue
        if len(fields) != len(wanted):
            findings.error(path, number, "%s, expected %d" % (plural(len(fields), "column"), len(wanted)))
            rows.append((number, None))
            continue
        edges = [wanted[i] for i, field in enumerate(fields) if field != field.strip()]
        if edges:
            findings.error(path, number, "%s: spaces at the start or the end" % ", ".join(edges))
            fields = [field.strip() for field in fields]
        rows.append((number, fields))
    if not header_seen:
        findings.error(path, max(1, len(lines)), "no header row")
        return names, None
    return names, rows


class Item:
    def __init__(self, line, fields):
        self.line = line
        (self.id, self.prompt, self.reading, accent, self.accepted, self.gloss, self.note, level,
         self.source) = fields
        self.accent_text = accent
        self.level_text = level
        self.accent = -1
        self.level = 0
        self.parts = ""


class Deck:
    def __init__(self, path):
        self.path = path
        self.id = os.path.basename(path)[:-len(".tsv")]
        self.name_ja = ""
        self.name_en = ""
        self.kind = ""
        self.stage = 1
        self.items = []
        self.rows = 0
        self.complete = False  # every row of the file became an item


def check_text(findings, path, line, field, text, prompt=False):
    """Every character must exist in the fonts that draw running text."""
    parts = []
    for name in TEXT_FONTS:
        missing = missing_glyphs(text, name)
        if missing:
            parts.append("%s in %s" % (missing, name))
    if parts:
        findings.error(path, line, "%s: no glyph for %s" % (field, ", ".join(parts)))
        return
    if prompt:
        for name in PROMPT_FONTS:
            missing = missing_glyphs(text, name)
            if missing:
                findings.warning(path, line, "%s: no glyph for %s in %s, so it is drawn with a smaller font"
                                 % (field, missing, name))


def check_kana_answer(findings, path, line, field, text):
    """Kana only, and typable. Returns True when both hold."""
    if not text:
        findings.error(path, line, "%s is empty" % field)
        return False
    other = "".join(dict.fromkeys(ch for ch in text if not is_kana(ch)))
    if other:
        shown = "a space" if other.isspace() else other
        findings.error(path, line, "%s: %s is not kana only (%s)" % (field, text, shown))
        return False
    romaji, problem = typing_romaji(text)
    if problem:
        findings.error(path, line, "%s: %s cannot be typed: %s" % (field, text, problem))
        return False
    if len(romaji) > LONGEST_ANSWER:
        findings.error(path, line, "%s: %s cannot be typed: %s is %d letters long, the device takes %d"
                       % (field, text, romaji, len(romaji), LONGEST_ANSWER))
        return False
    return True


def read_deck(path, findings, seen_ids):
    deck = Deck(path)
    if not ID_PATTERN.match(deck.id):
        findings.error(path, 1, "file name: the deck id %s must be lower case letters, digits and hyphens" % deck.id)
    names, rows = read_table(path, COLUMNS, findings)
    if names is None:
        return deck

    for key in ("name-ja", "name-en", "kind"):
        if key not in names:
            findings.error(path, 1, "no \"# %s: ...\" line above the header row" % key)
        elif not names[key][0]:
            findings.error(path, names[key][1], "%s is empty" % key)
    deck.name_ja = names.get("name-ja", ("", 1))[0]
    deck.name_en = names.get("name-en", ("", 1))[0]
    deck.kind = names.get("kind", ("", 1))[0]
    if deck.name_ja:
        line = names["name-ja"][1]
        other = "".join(dict.fromkeys(ch for ch in deck.name_ja if not is_kana(ch) and ch != " "))
        if other:
            findings.error(path, line, "name-ja: %s is not kana only (%s)" % (deck.name_ja, other))
        check_text(findings, path, line, "name-ja", deck.name_ja)
    if deck.name_en:
        check_text(findings, path, names["name-en"][1], "name-en", deck.name_en)
    if deck.kind and deck.kind not in KINDS:
        findings.error(path, names["kind"][1], "kind %s is not one of %s" % (deck.kind, ", ".join(KINDS)))
    if "stage" in names:
        if names["stage"][0] in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            deck.stage = int(names["stage"][0])
        else:
            findings.error(path, names["stage"][1], "stage \"%s\" is not a number from 1 to 9" % names["stage"][0])

    if rows is None:
        return deck
    deck.rows = len(rows)
    if not rows:
        findings.error(path, 1, "the deck has no rows")
    if len(rows) > MAX_ITEMS:
        findings.error(path, rows[MAX_ITEMS][0], "more than %d rows" % MAX_ITEMS)

    for line, fields in rows:
        if fields is None:
            continue
        item = Item(line, fields)
        check_item(deck, item, findings, seen_ids)
        deck.items.append(item)
    deck.complete = len(deck.items) == len(rows)
    return deck


def check_item(deck, item, findings, seen_ids):
    path, line = deck.path, item.line

    if not ID_PATTERN.match(item.id):
        findings.error(path, line, "id \"%s\" must be lower case letters, digits and hyphens" % item.id)
    elif item.id in seen_ids:
        first_path, first_line = seen_ids[item.id]
        findings.error(path, line, "id %s is already used at %s:%d" % (item.id, display(first_path), first_line))
    else:
        seen_ids[item.id] = (path, line)

    if not item.prompt:
        findings.error(path, line, "prompt is empty")
    else:
        check_text(findings, path, line, "prompt", item.prompt, prompt=True)

    reading_is_kana = check_kana_answer(findings, path, line, "reading", item.reading)
    if reading_is_kana:
        check_text(findings, path, line, "reading", item.reading)

    if item.accepted:
        answers = item.accepted.split("|")
        if "" in answers:
            findings.error(path, line, "accepted: an empty answer, remove the stray |")
        for k, answer in enumerate(answers):
            if answer and check_kana_answer(findings, path, line, "accepted", answer):
                check_text(findings, path, line, "accepted", answer)
            if answer and answer == item.reading:
                findings.warning(path, line, "accepted: %s is the reading itself" % answer)
            elif answer and answer in answers[:k]:
                findings.warning(path, line, "accepted: %s is given twice" % answer)

    if item.accent_text:
        if not re.fullmatch(r"0|[1-9][0-9]*", item.accent_text):
            findings.error(path, line, "accent \"%s\" is not a number; leave it empty when unknown"
                           % item.accent_text)
        elif reading_is_kana and int(item.accent_text) > beat_count(item.reading):
            findings.error(path, line, "accent %s is larger than the %s of %s"
                           % (item.accent_text, plural(beat_count(item.reading), "beat"), item.reading))
        elif int(item.accent_text) > MAX_ACCENT:
            findings.error(path, line, "accent %s is larger than %d" % (item.accent_text, MAX_ACCENT))
        else:
            item.accent = int(item.accent_text)

    if not item.gloss:
        findings.error(path, line, "gloss is empty")
    else:
        check_text(findings, path, line, "gloss", item.gloss)
        width = columns(item.gloss)
        if width > GLOSS_COLUMNS:
            findings.error(path, line, "gloss is %d characters long, at most %d fit" % (width, GLOSS_COLUMNS))

    if item.note:
        check_text(findings, path, line, "note", item.note)
        width = columns(item.note)
        if width > NOTE_COLUMNS:
            findings.error(path, line, "note is %d letters wide, at most %d fit (a Japanese character counts as 2)"
                           % (width, NOTE_COLUMNS))

    if item.level_text not in ("1", "2", "3"):
        findings.error(path, line, "level \"%s\" is not 1, 2 or 3" % item.level_text)
    else:
        item.level = int(item.level_text)
        kanji = "".join(dict.fromkeys(ch for ch in item.prompt if is_kanji(ch)))
        if item.level == 1 and kanji:
            findings.error(path, line, "level 1 is kana only, but the prompt contains kanji (%s)" % kanji)


def check_against_dictionary(deck, reference, findings):
    """The checks that need JMdict and the accent list."""
    path = deck.path
    filled = []
    undecided = []
    for item in deck.items:
        line = item.line
        if not item.prompt or not item.reading or not all(is_kana(ch) for ch in item.reading):
            continue

        if deck.kind == "word":
            readings = reference.readings(item.prompt)
            if readings is None:
                if item.source.strip().lower() in ("", "jmdict"):
                    findings.error(path, line, "%s is not a JMdict headword, and the source column names no "
                                   "other source" % item.prompt)
                else:
                    findings.warning(path, line, "%s is not a JMdict headword: reading and meaning rest on the "
                                     "source alone" % item.prompt)
            else:
                for answer in item.accepted.split("|"):
                    if answer and all(is_kana(ch) for ch in answer) and to_hiragana(answer) not in readings:
                        findings.warning(path, line, "accepted: JMdict does not read %s as %s: it rests on the "
                                         "source alone" % (item.prompt, answer))
                if to_hiragana(item.reading) not in readings:
                    findings.error(path, line, "JMdict does not read %s as %s (it has %s)"
                                   % (item.prompt, item.reading, ", ".join(readings)))
                    continue

        listed = reference.accents(item.prompt, item.reading)
        if item.accent_text:
            if item.accent < 0:
                continue  # already reported
            if listed is None:
                findings.error(path, line, "accent %d, but the accent list has no entry for %s read %s"
                               % (item.accent, item.prompt, item.reading))
            elif item.accent not in listed[0]:
                findings.error(path, line, "accent %d is not listed for %s read %s (the accent list has %s)"
                               % (item.accent, item.prompt, item.reading,
                                  ", ".join(str(n) for n in listed[0])))
            elif item.accent != listed[0][0] and not listed[1]:
                findings.warning(path, line, "accent %d is listed for %s read %s, but the usual one, the first "
                                 "in the accent list, is %d" % (item.accent, item.prompt, item.reading, listed[0][0]))
        elif listed is not None and deck.kind == "word":
            numbers, tagged = listed
            if tagged:
                undecided.append("%s (%s)" % (item.id, ", ".join(str(n) for n in numbers)))
            elif numbers[0] > beat_count(item.reading):
                findings.warning(path, line, "the accent list gives %d for %s, more than its beats: not filled in"
                                 % (numbers[0], item.reading))
            else:
                item.accent = numbers[0]
                filled.append("%s %d" % (item.id, item.accent))
    if filled:
        findings.note("%s: %s filled in from the accent list: %s"
                      % (deck.id, plural(len(filled), "accent"), ", ".join(filled)))
    if undecided:
        findings.note("%s: no accent filled in where the accent list gives one per part of speech; the deck "
                      "has to say which: %s" % (deck.id, ", ".join(undecided)))


# ---------------------------------------------------------------------------------------------
# What each kanji means
# ---------------------------------------------------------------------------------------------

def read_kanjidic(cache_dir, kanji_path, findings):
    """Returns {kanji: {"meanings": [...]}}, or None with a note where the file is not at hand."""
    index_path = os.path.join(cache_dir, "kanjidic_index.json")
    if not os.path.exists(index_path):
        findings.note("%s was not compared with KANJIDIC: %s not found"
                      % (display(kanji_path), display(index_path)))
        return None
    try:
        with open(index_path, encoding="utf-8") as handle:
            known = json.load(handle)
    except (OSError, ValueError) as problem:
        stop("%s cannot be read: %s" % (display(index_path), problem))
    if not isinstance(known, dict) or not all(isinstance(entry, dict) for entry in known.values()):
        stop("%s cannot be read: it is not a table of kanji" % display(index_path))
    return known


def read_kanji(path, findings, kanjidic, reference, prompts):
    """content/kanji.tsv. Returns ({kanji: meaning}, number of rows).

    kanjidic and reference are None where the dictionaries are not at hand: what the basis column
    names is then not looked up. prompts: every prompt of the decks, or None when a deck could not
    be read to its end: the table is then not compared with the decks. The meanings are None when
    the file holds no table that can be read. Either way one finding says what is wrong, and not
    one for every row that depends on it.
    """
    _, rows = read_table(path, KANJI_COLUMNS, findings)
    if rows is None:
        return None, 0
    meanings = {}
    seen = {}
    in_prompts = set(ch for prompt in prompts or [] for ch in prompt)
    for number, fields in rows:
        if fields is None:
            continue
        kanji, meaning, basis, words = fields
        if len(kanji) != 1 or not is_kanji(kanji):
            findings.error(path, number, "kanji \"%s\" is not one kanji" % kanji)
            continue
        if kanji in seen:
            findings.error(path, number, "%s is given twice: first in line %d" % (kanji, seen[kanji]))
            continue
        seen[kanji] = number
        check_text(findings, path, number, "kanji", kanji)

        if not meaning:
            findings.error(path, number, "meaning is empty")
        else:
            meanings[kanji] = meaning
            if len(meaning) > KANJI_MEANING_LENGTH:
                findings.error(path, number, "meaning \"%s\" is %d letters long, at most %d fit"
                               % (meaning, len(meaning), KANJI_MEANING_LENGTH))
            if not MEANING_PATTERN.match(meaning):
                findings.error(path, number, "meaning \"%s\" must be lower case words with one space or "
                               "hyphen between them" % meaning)

        if not basis:
            findings.error(path, number, "basis is empty")
        elif basis.startswith(JMDICT_BASIS):
            word = basis[len(JMDICT_BASIS):]
            if kanji not in word:
                findings.error(path, number, "basis \"%s\" names a word without %s" % (basis, kanji))
            elif reference is not None and reference.readings(word) is None:
                findings.error(path, number, "basis \"%s\": %s is not a JMdict headword" % (basis, word))
        elif kanjidic is not None:
            listed = kanjidic.get(kanji, {}).get("meanings", [])
            if basis not in listed:
                findings.error(path, number, "basis \"%s\" is not a KANJIDIC meaning of %s (%s)"
                               % (basis, kanji, ", ".join(listed[:8]) or "none listed"))

        for word in [w for w in words.split(" ") if w]:
            if kanji not in word:
                findings.warning(path, number, "words: %s is written without %s" % (word, kanji))
            elif prompts is not None and word not in prompts:
                findings.warning(path, number, "words: %s is not a prompt of a deck" % word)
        if prompts is not None and kanji not in in_prompts:
            findings.warning(path, number, "no prompt of a deck is written with %s: the row is not used" % kanji)
    return meanings, len(rows)


def read_parts(path, findings, prompts):
    """content/parts.tsv: the line of a word written by hand, where the one put together from
    kanji.tsv would not explain it. Returns ({prompt: line}, number of rows). The line may be empty:
    the card then shows none. prompts: as for read_kanji."""
    _, rows = read_table(path, PARTS_FILE_COLUMNS, findings)
    lines = {}
    seen = {}
    for number, fields in rows or []:
        if fields is None:
            continue
        prompt, parts, reason = fields
        if not prompt:
            findings.error(path, number, "prompt is empty")
            continue
        if prompt in seen:
            findings.error(path, number, "%s is given twice: first in line %d" % (prompt, seen[prompt]))
            continue
        seen[prompt] = number
        lines[prompt] = parts
        if prompts is not None and prompt not in prompts:
            findings.error(path, number, "%s is not a prompt of a deck" % prompt)
        if parts:
            check_text(findings, path, number, "parts", parts)
            foreign = "".join(dict.fromkeys(ch for ch in parts if is_kanji(ch) and ch not in prompt))
            if foreign:
                findings.error(path, number, "parts: %s is not a kanji of %s" % (foreign, prompt))
            width = columns(parts)
            if width > PARTS_COLUMNS:
                findings.error(path, number, "parts is %d letters wide, at most %d fit (a Japanese character "
                               "counts as 2)" % (width, PARTS_COLUMNS))
        if not reason:
            findings.error(path, number, "reason is empty")
    return lines, len(rows or [])


def add_parts(decks, meanings, written, kanji_path, findings):
    """Gives every item the line that says what the kanji of its prompt mean: the one written by
    hand where there is one, otherwise put together from the meanings.

    meanings is None without kanji.tsv: only the lines written by hand are given then.
    """
    unknown = {}
    for deck in decks:
        for item in deck.items:
            if item.prompt in written:
                item.parts = written[item.prompt]
                continue
            kanji = list(dict.fromkeys(ch for ch in item.prompt if is_kanji(ch)))
            if not kanji or meanings is None:
                continue
            for ch in kanji:
                if ch not in meanings:
                    unknown.setdefault(ch, (deck.path, item.line, item.prompt))
            item.parts = "  ".join("%s %s" % (ch, meanings[ch]) for ch in kanji if ch in meanings)
            if columns(item.parts) > PARTS_COLUMNS:
                findings.warning(deck.path, item.line, "the meanings of the kanji of %s are %d letters wide, "
                                 "%d fit: the end will be cut off" % (item.prompt, columns(item.parts), PARTS_COLUMNS))
    for ch, (path, line, prompt) in unknown.items():
        findings.warning(path, line, "%s in %s has no meaning in %s" % (ch, prompt, display(kanji_path)))


# ---------------------------------------------------------------------------------------------
# The guide to how Japanese sounds
# ---------------------------------------------------------------------------------------------

class GuidePage:
    def __init__(self, line, fields):
        self.line = line
        self.id, self.title, body, self.clips = fields
        self.lines = body.split("|")


def read_guide(path, findings, used_ids):
    """content/guide.tsv: one page per row. In body, | starts a new line. Returns (pages, number of
    rows). used_ids: {id: (path, line)} of the decks and the buddy."""
    _, rows = read_table(path, GUIDE_COLUMNS, findings)
    pages = []
    seen = {}
    for number, fields in rows or []:
        if fields is None:
            continue
        page = GuidePage(number, fields)
        pages.append(page)
        if not ID_PATTERN.match(page.id):
            findings.error(path, number, "id \"%s\" must be lower case letters, digits and hyphens" % page.id)
        elif page.id in seen or page.id in used_ids:
            first_path, first_line = used_ids.get(page.id) or (path, seen[page.id])
            findings.error(path, number, "id %s is already used at %s:%d"
                           % (page.id, display(first_path), first_line))
        else:
            seen[page.id] = number

        if not page.title:
            findings.error(path, number, "title is empty")
        else:
            check_text(findings, path, number, "title", page.title)
            if columns(page.title) > GUIDE_TITLE_COLUMNS:
                findings.error(path, number, "title is %d letters wide, at most %d fit (a Japanese character "
                               "counts as 2)" % (columns(page.title), GUIDE_TITLE_COLUMNS))

        if not any(page.lines):
            findings.error(path, number, "body is empty")
        if len(page.lines) > GUIDE_LINES:
            findings.error(path, number, "body has %d lines, at most %d fit" % (len(page.lines), GUIDE_LINES))
        for text in page.lines:
            check_text(findings, path, number, "body", text)
            if columns(text) > GUIDE_LINE_COLUMNS:
                findings.error(path, number, "the line \"%s\" is %d letters wide, at most %d fit "
                               "(a Japanese character counts as 2)" % (text, columns(text), GUIDE_LINE_COLUMNS))

        if page.clips:
            clips = page.clips.split("|")
            if "" in clips:
                findings.error(path, number, "clips: an empty clip, remove the stray |")
            for k, clip in enumerate(clips):
                other = "".join(dict.fromkeys(ch for ch in clip if not is_kana(ch)))
                if other:
                    shown = "a space" if other.isspace() else other
                    findings.error(path, number, "clips: %s is not kana only (%s)" % (clip, shown))
                elif clip:
                    check_text(findings, path, number, "clips", clip)
                if clip and clip in clips[:k]:
                    findings.warning(path, number, "clips: %s is given twice" % clip)
    return pages, len(rows or [])


# ---------------------------------------------------------------------------------------------
# The buddy
# ---------------------------------------------------------------------------------------------

class BuddyLine:
    def __init__(self, line, fields):
        self.line = line
        self.id, self.mood, self.ja, self.en = fields


def read_buddy(path, findings, deck_ids):
    """deck_ids: {id: (path, line)} of the decks, because an id is unique in the whole content."""
    _, rows = read_table(path, BUDDY_COLUMNS, findings)
    lines = []
    seen = {}
    for number, fields in rows or []:
        if fields is None:
            continue
        entry = BuddyLine(number, fields)
        lines.append(entry)

        if not ID_PATTERN.match(entry.id):
            findings.error(path, number, "id \"%s\" must be lower case letters, digits and hyphens" % entry.id)
        elif entry.id in seen or entry.id in deck_ids:
            first_path, first_line = deck_ids.get(entry.id) or (path, seen[entry.id])
            findings.error(path, number, "id %s is already used at %s:%d"
                           % (entry.id, display(first_path), first_line))
        else:
            seen[entry.id] = number

        if entry.mood not in MOODS:
            findings.error(path, number, "mood \"%s\" is not one of %s" % (entry.mood, ", ".join(MOODS)))

        if not entry.ja:
            findings.error(path, number, "ja is empty")
        else:
            other = "".join(dict.fromkeys(ch for ch in entry.ja
                                          if not is_kana(ch) and ch != " " and ch not in BUDDY_PUNCTUATION))
            if other:
                findings.error(path, number, "ja: %s is not kana only (%s)" % (entry.ja, other))
            else:
                check_text(findings, path, number, "ja", entry.ja)
            if len(entry.ja) > BUDDY_JA_LENGTH:
                findings.error(path, number, "ja is %d characters long, at most %d fit"
                               % (len(entry.ja), BUDDY_JA_LENGTH))

        if not entry.en:
            findings.error(path, number, "en is empty")
        else:
            check_text(findings, path, number, "en", entry.en)
            if len(entry.en) > BUDDY_EN_LENGTH:
                findings.error(path, number, "en is %d characters long, at most %d fit"
                               % (len(entry.en), BUDDY_EN_LENGTH))
    return lines, len(rows or [])


# ---------------------------------------------------------------------------------------------
# The list of published ids
# ---------------------------------------------------------------------------------------------

def read_ids(path, findings):
    """Returns {id: line number}."""
    published = {}
    if not os.path.exists(path):
        return published
    try:
        with open(path, encoding="utf-8-sig") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as problem:
        findings.error(path, 1, "cannot be read: %s" % (getattr(problem, "strerror", None) or "not UTF-8"))
        return published
    for number, line in enumerate(lines, 1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if not ID_PATTERN.match(text):
            findings.error(path, number, "\"%s\" is not an id" % text)
        elif text not in published:
            published[text] = number
    return published


def ids_text(ids):
    lines = [
        "# Every id ever published, one per line. Written by tools/build_decks.py.",
        "# Progress files on the devices refer to these ids, so an id listed here has to stay in the decks",
        "# and keep its meaning.",
    ]
    return "\n".join(lines + sorted(ids)) + "\n"


# ---------------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------------

def literal(text):
    """A C++ string literal. UTF-8 is written as it is, a line break as \\n."""
    out = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    while "??" in out:
        out = out.replace("??", "?\\?")  # no trigraphs
    return '"' + out + '"'


def ordered(decks):
    def rank(deck):
        if deck.id in DECK_ORDER:
            return (0, DECK_ORDER.index(deck.id), "")
        return (1, 0, deck.id)
    return sorted(decks, key=rank)


def source_text(decks, buddy, guide=()):
    out = ["// Written by tools/build_decks.py from the tables in content/.",
           "// Do not edit by hand: change the tables and run the tool again.",
           "//"]
    out += ["// " + line for line in LICENCE]
    out += ['#include "deck.h"', "", "namespace {", ""]
    for deck in decks:
        out.append("const deck::Item %s[] = {" % array_name(deck))
        for item in deck.items:
            out.append("    {%s, %s, %s, %s, %s, %s, %s, %d, %d, deck::Kind::%s}," % (
                literal(item.id), literal(item.prompt), literal(item.reading), literal(item.accepted),
                literal(item.gloss), literal(item.note), literal(item.parts), item.accent, item.level,
                KINDS[deck.kind]))
        out += ["};", ""]
    out += ["}  // namespace", "", "extern const deck::Deck kDeckTable[] = {"]
    for deck in decks:
        out.append("    {%s, %s, %s, %s, %d, %d}," % (literal(deck.id), literal(deck.name_ja), literal(deck.name_en),
                                                      array_name(deck), len(deck.items), deck.stage))
    out += ["};", "extern const size_t kDeckTableSize = sizeof(kDeckTable) / sizeof(kDeckTable[0]);", ""]

    out.append("extern const deck::BuddyLine kBuddyLines[] = {")
    for entry in buddy:
        out.append("    {%s, %s, %s, %s}," % (literal(entry.id), literal(entry.mood), literal(entry.ja),
                                              literal(entry.en)))
    if not buddy:
        out.append('    {"", "", "", ""},  // an array cannot be empty; the count below is 0')
    out += ["};", "extern const size_t kBuddyLineCount = %d;" % len(buddy), ""]

    out.append("extern const deck::GuidePage kGuidePages[] = {")
    for page in guide:
        out.append("    {%s, %s, %s, %s}," % (literal(page.id), literal(page.title),
                                              literal("\n".join(page.lines)), literal(page.clips)))
    if not guide:
        out.append('    {"", "", "", ""},  // an array cannot be empty; the count below is 0')
    out += ["};", "extern const size_t kGuidePageCount = %d;" % len(guide), ""]
    return "\n".join(out)


def array_name(deck):
    return "kItems_" + deck.id.replace("-", "_")


def write(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as problem:
        stop("%s cannot be written: %s" % (display(path), problem.strerror))


# ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Checks the deck files and compiles them into the firmware.")
    parser.add_argument("--check", action="store_true", help="check only, write nothing")
    parser.add_argument("--offline", action="store_true", help="skip the checks that need the dictionary")
    parser.add_argument("--decks", metavar="DIR", help="folder with the deck files (content/decks)")
    parser.add_argument("--out", metavar="FILE", help="the C++ file to write (lib/core/deck_data.cpp)")
    parser.add_argument("--ids", metavar="FILE", help="the list of published ids (ids.txt next to the deck folder)")
    parser.add_argument("--buddy", metavar="FILE", help="the buddy's lines (buddy.tsv next to the deck folder)")
    parser.add_argument("--kanji", metavar="FILE", help="what each kanji means (kanji.tsv next to the deck folder)")
    parser.add_argument("--parts", metavar="FILE", help="the lines about kanji that are written by hand (parts.tsv "
                                                        "next to the deck folder)")
    parser.add_argument("--guide", metavar="FILE", help="the guide to the sounds (guide.tsv next to the deck folder)")
    parser.add_argument("--cache", metavar="DIR", help="folder with jmdict_index.json, accents.txt and "
                                                       "kanjidic_index.json (local/cache)")
    args = parser.parse_args()

    if args.decks and not args.check and not (args.out and args.ids):
        stop("with --decks, say where to write with --out and --ids, or use --check")

    decks_dir = os.path.abspath(args.decks or os.path.join(ROOT, "content", "decks"))
    content_dir = os.path.dirname(decks_dir)
    out_path = os.path.abspath(args.out or os.path.join(ROOT, "lib", "core", "deck_data.cpp"))
    ids_path = os.path.abspath(args.ids or os.path.join(content_dir, "ids.txt"))
    buddy_path = os.path.abspath(args.buddy or os.path.join(content_dir, "buddy.tsv"))
    kanji_path = os.path.abspath(args.kanji or os.path.join(content_dir, "kanji.tsv"))
    parts_path = os.path.abspath(args.parts or os.path.join(content_dir, "parts.tsv"))
    guide_path = os.path.abspath(args.guide or os.path.join(content_dir, "guide.tsv"))
    cache_dir = os.path.abspath(args.cache or os.path.join(ROOT, "local", "cache"))

    if not os.path.isdir(decks_dir):
        stop("%s is not a folder" % display(decks_dir))
    # a table beside the decks may be absent, but not one that was asked for by name
    for named in (args.buddy, args.kanji, args.parts, args.guide):
        if named and not os.path.exists(named):
            stop("%s not found" % display(named))
    load_fonts()

    findings = Findings()
    names = sorted(name for name in os.listdir(decks_dir) if not name.startswith("."))
    paths = [os.path.join(decks_dir, name) for name in names if name.endswith(".tsv")]
    for name in names:
        if not name.endswith(".tsv"):
            findings.warning(os.path.join(decks_dir, name), 1, "not a deck file (*.tsv): left out")
    if not paths:
        findings.error(decks_dir, 1, "no deck files (*.tsv)")

    seen_ids = {}
    decks = [read_deck(path, findings, seen_ids) for path in paths]

    # Dictionary and accent list
    reference = None
    if args.offline:
        findings.note("the dictionary checks were skipped (--offline): readings and accents are as the decks "
                      "give them, and no accent was filled in")
    elif any(deck.items for deck in decks):
        reference = Reference(cache_dir)
        for deck in ordered(decks):
            check_against_dictionary(deck, reference, findings)

    # Ids
    published = read_ids(ids_path, findings)
    for name, number in published.items():
        if name not in seen_ids:
            findings.error(ids_path, number, "id %s was published and has disappeared from the decks" % name)
    keys = {}
    for name in list(published) + list(seen_ids):
        other = keys.setdefault(fnv1a(name), name)
        if other != name:
            where, number = seen_ids.get(name) or (ids_path, published[name])
            findings.error(where, number, "id %s has the same key as %s (deck::key, %08x): rename the newer one"
                           % (name, other, fnv1a(name)))
    new_ids = [name for name in seen_ids if name not in published]

    # The buddy
    buddy = []
    buddy_rows = 0
    has_buddy = os.path.exists(buddy_path)
    if has_buddy:
        buddy, buddy_rows = read_buddy(buddy_path, findings, seen_ids)

    # The guide
    guide = []
    guide_rows = 0
    has_guide = os.path.exists(guide_path)
    if has_guide:
        used = dict(seen_ids)
        for entry in buddy:
            used.setdefault(entry.id, (buddy_path, entry.line))
        guide, guide_rows = read_guide(guide_path, findings, used)

    # What the kanji of a prompt mean
    prompts = None
    if decks and all(deck.complete for deck in decks):
        prompts = set(item.prompt for deck in decks for item in deck.items)
    meanings = None
    kanji_rows = 0
    has_kanji = os.path.exists(kanji_path)
    if has_kanji:
        kanjidic = None if args.offline else read_kanjidic(cache_dir, kanji_path, findings)
        meanings, kanji_rows = read_kanji(kanji_path, findings, kanjidic, reference, prompts)
    written = {}
    parts_rows = 0
    has_parts = os.path.exists(parts_path)
    if has_parts:
        written, parts_rows = read_parts(parts_path, findings, prompts)
    add_parts(decks, meanings, written, kanji_path, findings)

    for line in findings.lines():
        print(line)
    for deck in ordered(decks):
        print("%s: %s, %s, %s" % (deck.id, plural(deck.rows, "row"), plural(findings.errors(deck.path), "error"),
                                  plural(findings.warnings(deck.path), "warning")))
    if has_buddy:
        print("buddy: %s, %s, %s" % (plural(buddy_rows, "line"), plural(findings.errors(buddy_path), "error"),
                                     plural(findings.warnings(buddy_path), "warning")))
    if has_kanji:
        print("kanji: %s, %s, %s" % (plural(kanji_rows, "row"), plural(findings.errors(kanji_path), "error"),
                                     plural(findings.warnings(kanji_path), "warning")))
    if has_parts:
        print("parts: %s, %s, %s" % (plural(parts_rows, "row"), plural(findings.errors(parts_path), "error"),
                                     plural(findings.warnings(parts_path), "warning")))
    if has_guide:
        print("guide: %s, %s, %s" % (plural(guide_rows, "page"), plural(findings.errors(guide_path), "error"),
                                     plural(findings.warnings(guide_path), "warning")))
    for note in findings.notes:
        print("note: " + note)
    print("total: %s, %s, %s, %s" % (plural(len(decks), "deck"), plural(sum(deck.rows for deck in decks), "row"),
                                     plural(findings.errors(), "error"), plural(findings.warnings(), "warning")))

    if findings.errors():
        print("nothing written")
        return 1
    if args.check:
        print("checked only, nothing written")
        return 0
    write(out_path, source_text(ordered(decks), buddy, guide))
    write(ids_path, ids_text(set(published) | set(seen_ids)))
    print("wrote %s: %s, %s, %s, %s" % (display(out_path), plural(len(decks), "deck"),
                                        plural(sum(len(deck.items) for deck in decks), "item"),
                                        plural(len(buddy), "buddy line"), plural(len(guide), "guide page")))
    print("wrote %s: %s, %d new" % (display(ids_path), plural(len(set(published) | set(seen_ids)), "id"),
                                   len(new_ids)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
