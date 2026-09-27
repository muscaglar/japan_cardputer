#!/usr/bin/env python3
"""How a number, a price, a clock time and a date are read, in hiragana.

    python3 tools/number_reading.py                          # runs its own checks
    python3 tools/number_reading.py 1280 ¥1280 14:37 4/20    # prints the reading of each
    python3 tools/number_reading.py --fill [deck file]       # writes the readings into the deck
    python3 tools/number_reading.py --verify [deck file]     # exit code 1 when the deck differs

The deck content/decks/numbers.tsv holds prompts, meanings and notes. Its columns reading, accepted
and source are written by --fill from the prompt of each row, never by hand.

Every reading comes as the commonest form and a list of other right forms. A form is offered only
when a source lists it, or when it is a plain chain of parts that a source lists.

Sources
  JMdict      JMdict 3.6.2, the entries for the numerals, 一時 to 二十四時, 一分 to 十分, 三十分,
              一月 to 十二月, 一日 to 三十一日, 千円, 一万円, 午前零時, 午後零時
  NHK         https://www.nhk.or.jp/bunken/research/kotoba/20180501_4.html
              0 to 20 as bare numbers: よん なな きゅう first, し しち く allowed; 0 is れい, or ゼロ
  numerals    https://en.wikipedia.org/wiki/Japanese_numerals
              さんびゃく ろっぴゃく はっぴゃく さんぜん はっせん; 1000 is せん, 10000 is いちまん;
              1000,0000 is いっせんまん; 1500,0000 is せんごひゃくまん or いっせんごひゃくまん;
              zeros inside a number are skipped
  counters    https://en.wikipedia.org/wiki/Japanese_counter_word
              よじ しちじ くじ じゅうよじ じゅうくじ にじゅうよじ, よんぷん じゅうよんぷん, しがつ
              しちがつ くがつ, and the days of the month
  minutes     https://www.tofugu.com/japanese/japanese-counter-fun/
              よんふん しちふん はちふん じっぷん beside the first forms; じゅういっぷん じゅうにふん
  hours       https://www.tofugu.com/japanese/japanese-counter-ji-jikan/
              1 to 24 o'clock, ななじ and じゅうななじ, ごぜん and ごご before the hour, はん
  seven       https://ja.wiktionary.org/wiki/七時    ななじ, said to keep 7 apart from 1
  midnight    https://ja.wiktionary.org/wiki/零時    ゼロじ beside れいじ
  four yen    https://ja.wiktionary.org/wiki/よ      四円 is よえん
  noon        https://www.nao.ac.jp/faq/a0401.html   noon is 午後0時 or 午前12時; after noon, 午後0時
              is the form that misleads least
              https://ja.wikipedia.org/wiki/12時間制  by the ordinance of 1872, 午後12時 is midnight;
              12:20 is written 午後12時20分 all the same

Choices
  - し and く are offered for the bare numbers up to 20 that NHK lists (4, 9, 14, 19), not for
    larger numbers, not inside a number and not in a price.
  - しち is offered for 70, 700 and 7000, which JMdict lists. For 7 before えん it rests on the
    general rule of the counters page (なな and しち both, except with the counters it names), not
    on an entry for 七円. It is not offered before まん, for lack of a source.
  - 1000 is せん. いっせん is offered only in front of まん, although JMdict and the numerals page
    know it for 1000 and 1500 as well.
  - A price of 0 yen is refused: no source gives its reading.
  - 24 o'clock is にじゅうよじ (counters, hours). JMdict has にじゅうよんじ, which is accepted.
  - ぜろじ is accepted for 0 o'clock, but not behind ごぜん or ごご.
  - 12:00 with ごご is ごごれいじ; ごぜんじゅうにじ is accepted (noon). ごごじゅうにじ is not: by the
    ordinance it is midnight.
  - 12:30 with ごご is ごごれいじさんじゅっぷん. ごごじゅうにじさんじゅっぷん is accepted, because it is
    what is commonly said and written, and after noon it can only mean half past twelve.
  - A number printed with zeros in front (007, 0,500) is refused. Times and dates may have them.
  - Days of the month: the first reading of JMdict, and じゅうななにち, にじゅうななにち beside it.
    なぬか, にじゅうにち, にじゅうきゅうにち and the like are in JMdict, where the entry also means
    a number of days. They are not offered for a date.

Uses only the Python standard library.
"""
import calendar
import collections
import itertools
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DECK = os.path.join(ROOT, "content", "decks", "numbers.tsv")
SOURCE = "generated, tools/number_reading.py"
COLUMNS = ["id", "prompt", "reading", "accent", "accepted", "gloss", "note", "level", "source"]

LARGEST = 99999999

# main: the commonest reading. accepted: the other right readings, without main.
Reading = collections.namedtuple("Reading", ["main", "accepted"])


# ---------------------------------------------------------------------------------------------
# Parts. Each entry is a list: the commonest form first, then the other right forms.
# ---------------------------------------------------------------------------------------------

DIGITS = {1: ["いち"], 2: ["に"], 3: ["さん"], 4: ["よん"], 5: ["ご"], 6: ["ろく"], 7: ["なな"], 8: ["はち"],
          9: ["きゅう"]}
# the last digit of a bare number up to 20
DIGITS_ALONE = {**DIGITS, 4: ["よん", "し"], 7: ["なな", "しち"], 9: ["きゅう", "く"]}
# the last digit of a larger bare number
DIGITS_SEVEN = {**DIGITS, 7: ["なな", "しち"]}
# the last digit in front of えん
DIGITS_YEN = {**DIGITS, 4: ["よ"], 7: ["なな", "しち"]}

TENS = {1: ["じゅう"], 2: ["にじゅう"], 3: ["さんじゅう"], 4: ["よんじゅう"], 5: ["ごじゅう"], 6: ["ろくじゅう"],
        7: ["ななじゅう", "しちじゅう"], 8: ["はちじゅう"], 9: ["きゅうじゅう"]}
HUNDREDS = {1: ["ひゃく"], 2: ["にひゃく"], 3: ["さんびゃく"], 4: ["よんひゃく"], 5: ["ごひゃく"],
            6: ["ろっぴゃく"], 7: ["ななひゃく", "しちひゃく"], 8: ["はっぴゃく"], 9: ["きゅうひゃく"]}
THOUSANDS = {1: ["せん"], 2: ["にせん"], 3: ["さんぜん"], 4: ["よんせん"], 5: ["ごせん"], 6: ["ろくせん"],
             7: ["ななせん", "しちせん"], 8: ["はっせん"], 9: ["きゅうせん"]}

ZERO = ["れい", "ぜろ"]

# 1 to 10 in front of じ
HOUR_DIGITS = {1: ["いち"], 2: ["に"], 3: ["さん"], 4: ["よ"], 5: ["ご"], 6: ["ろく"], 7: ["しち", "なな"],
               8: ["はち"], 9: ["く"]}
# 1 to 9 with ふん
MINUTE_DIGITS = {1: ["いっぷん"], 2: ["にふん"], 3: ["さんぷん"], 4: ["よんぷん", "よんふん"], 5: ["ごふん"],
                 6: ["ろっぷん"], 7: ["ななふん", "しちふん"], 8: ["はっぷん", "はちふん"], 9: ["きゅうふん"]}
TEN_MINUTES = ["じゅっぷん", "じっぷん"]
HALF = "はん"
MORNING = "ごぜん"
AFTERNOON = "ごご"

MONTHS = {1: ["いちがつ"], 2: ["にがつ"], 3: ["さんがつ"], 4: ["しがつ"], 5: ["ごがつ"], 6: ["ろくがつ"],
          7: ["しちがつ", "なながつ"], 8: ["はちがつ"], 9: ["くがつ"], 10: ["じゅうがつ"], 11: ["じゅういちがつ"],
          12: ["じゅうにがつ"]}
DAYS = {1: ["ついたち"], 2: ["ふつか"], 3: ["みっか"], 4: ["よっか"], 5: ["いつか"], 6: ["むいか"], 7: ["なのか"],
        8: ["ようか"], 9: ["ここのか"], 10: ["とおか"], 14: ["じゅうよっか"], 17: ["じゅうしちにち", "じゅうななにち"],
        19: ["じゅうくにち"], 20: ["はつか"], 24: ["にじゅうよっか"], 27: ["にじゅうしちにち", "にじゅうななにち"],
        29: ["にじゅうくにち"]}


def spell(slots):
    """Chains the parts. The first form of every part gives the main reading."""
    forms = list(dict.fromkeys("".join(choice) for choice in itertools.product(*slots)))
    return Reading(forms[0], forms[1:])


def forms(reading):
    return [reading.main] + list(reading.accepted)


# ---------------------------------------------------------------------------------------------
# Whole numbers
# ---------------------------------------------------------------------------------------------

def group_slots(value, last_digit, before_man=False):
    """The parts of 1 to 9999."""
    slots = []
    thousands, rest = divmod(value, 1000)
    hundreds, rest = divmod(rest, 100)
    tens, units = divmod(rest, 10)
    if thousands == 1 and before_man:
        slots.append(["いっせん", "せん"] if value == 1000 else ["せん", "いっせん"])
    elif thousands:
        slots.append(THOUSANDS[thousands])
    if hundreds:
        slots.append(HUNDREDS[hundreds])
    if tens:
        slots.append(TENS[tens])
    if units:
        slots.append(last_digit[units])
    return slots


def number_slots(value, last_digit):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%r is not a whole number" % (value,))
    if not 0 <= value <= LARGEST:
        raise ValueError("%d is outside 0 to %d" % (value, LARGEST))
    if value == 0:
        return [ZERO]
    man, low = divmod(value, 10000)
    slots = []
    if man:
        slots += group_slots(man, DIGITS, before_man=True) + [["まん"]]
    if low:
        slots += group_slots(low, last_digit)
    return slots


def number(value):
    """A whole number from 0 to 99,999,999."""
    alone = isinstance(value, int) and 0 <= value <= 20
    return spell(number_slots(value, DIGITS_ALONE if alone else DIGITS_SEVEN))


def yen(value):
    """A price in yen, from 1 to 99,999,999."""
    if value == 0:
        raise ValueError("no source gives the reading of 0 yen")
    return spell(number_slots(value, DIGITS_YEN) + [["えん"]])


# ---------------------------------------------------------------------------------------------
# Clock times
# ---------------------------------------------------------------------------------------------

def hour_forms(value):
    """0 to 24 o'clock."""
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 24:
        raise ValueError("%r is not an hour from 0 to 24" % (value,))
    if value == 0:
        return ["れいじ", "ぜろじ"]
    if value == 24:
        return ["にじゅうよじ", "にじゅうよんじ"]
    tens, units = divmod(value, 10)
    slots = []
    if tens:
        slots.append(TENS[tens])
    if units:
        slots.append(HOUR_DIGITS[units])
    return forms(spell(slots + [["じ"]]))


def minute_forms(value):
    """1 to 59 minutes."""
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 59:
        raise ValueError("%r is not a minute from 1 to 59" % (value,))
    tens, units = divmod(value, 10)
    if units == 0:
        return forms(spell([DIGITS[tens] if tens > 1 else [""], TEN_MINUTES]))
    return forms(spell(([TENS[tens]] if tens else []) + [MINUTE_DIGITS[units]]))


def check_time(hour, minute):
    hour_forms(hour)
    if isinstance(minute, bool) or not isinstance(minute, int) or not 0 <= minute <= 59:
        raise ValueError("%r is not a minute from 0 to 59" % (minute,))


def minute_slot(minute, half=True):
    if minute == 0:
        return [""]
    return minute_forms(minute) + ([HALF] if minute == 30 and half else [])


def clock24(hour, minute):
    """A time as the timetable prints it, 0:00 to 24:59. はん is among the accepted forms."""
    check_time(hour, minute)
    return spell([hour_forms(hour), minute_slot(minute)])


def clock12(hour, minute):
    """The same time with ごぜん or ごご, 0:00 to 23:59. Noon and after is ごごれいじ."""
    check_time(hour, minute)
    if hour == 24:
        raise ValueError("24 o'clock has no twelve hour form here")
    half = AFTERNOON if hour >= 12 else MORNING
    if hour % 12:
        hours = hour_forms(hour % 12)
    elif hour == 12 and minute:
        hours = ["れいじ", "じゅうにじ"]  # after noon ごごじゅうにじ… is accepted, see Choices
    else:
        # with ごぜん and ごご only れいじ is offered for 0: JMdict has 午前零時 and 午後零時 so
        hours = ["れいじ"]
    return spell([[half], hours, minute_slot(minute)])


def clock(hour, minute):
    """What the deck takes: the 24 hour form first, then every other form of both kinds."""
    answers = forms(clock24(hour, minute))
    if hour != 24:
        answers += forms(clock12(hour, minute))
    if hour == 12 and minute == 0:
        answers.append(MORNING + "じゅうにじ")  # noon
    answers = list(dict.fromkeys(answers))
    return Reading(answers[0], answers[1:])


# ---------------------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------------------

def month_forms(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 12:
        raise ValueError("%r is not a month" % (value,))
    return list(MONTHS[value])


def day_forms(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 31:
        raise ValueError("%r is not a day of the month" % (value,))
    if value in DAYS:
        return list(DAYS[value])
    return [number(value).main + "にち"]


def date(month, day):
    """A day of the year, as 4/20 on a ticket: month first."""
    month_forms(month)
    day_forms(day)
    if day > calendar.monthrange(2024, month)[1]:  # 2024 was a leap year, so 2/29 is a date
        raise ValueError("month %d has no day %d" % (month, day))
    return spell([month_forms(month), day_forms(day)])


# ---------------------------------------------------------------------------------------------
# Prompts as they are printed
# ---------------------------------------------------------------------------------------------

PRICE = re.compile(r"[¥￥]\s*([0-9][0-9,]*)\Z|([0-9][0-9,]*)\s*円\Z")
TIME = re.compile(r"([0-9]{1,2})[:：]([0-9]{2})\Z")
DATE = re.compile(r"([0-9]{1,2})/([0-9]{1,2})\Z|([0-9]{1,2})月([0-9]{1,2})日\Z")
NUMBER = re.compile(r"[0-9][0-9,]*\Z")


def digits(text):
    parts = text.split(",")
    if len(parts) > 1 and (not 1 <= len(parts[0]) <= 3 or any(len(part) != 3 for part in parts[1:])):
        raise ValueError("%s: the commas do not stand between groups of three digits" % text)
    if len(text) > 1 and text.startswith("0"):
        raise ValueError("%s: a number is not printed with zeros in front" % text)
    return int("".join(parts))


def kind_of(text):
    text = text.strip()
    if PRICE.match(text):
        return "yen"
    if TIME.match(text):
        return "time"
    if DATE.match(text):
        return "date"
    if NUMBER.match(text):
        return "number"
    return None


def read(text):
    """The reading of a prompt: 1280 or 1,280, ¥1,280 or 1280円, 14:37, 4/20 or 4月20日."""
    text = text.strip()
    match = PRICE.match(text)
    if match:
        return yen(digits(match.group(1) or match.group(2)))
    match = TIME.match(text)
    if match:
        return clock(int(match.group(1)), int(match.group(2)))
    match = DATE.match(text)
    if match:
        found = [int(group) for group in match.groups() if group is not None]
        return date(found[0], found[1])
    if NUMBER.match(text):
        return number(digits(text))
    raise ValueError("%s is not a number, a price, a time or a date" % text)


# ---------------------------------------------------------------------------------------------
# Typing
# ---------------------------------------------------------------------------------------------

def converter():
    sys.path.insert(0, TOOLS)
    import romaji_reference
    return romaji_reference


def typing(kana, reference=None):
    """The romaji that types `kana` on the device: っ doubles the consonant, ん before a vowel or
    y takes an apostrophe. Raises ValueError when the converter gives something else back."""
    reference = reference or converter()
    spellings = {}
    for roma, syllable in reference.TABLE.items():
        # Hepburn where the converter's table offers a choice, otherwise the first spelling in it
        rank = 0 if roma.startswith(("sh", "ch", "j", "ts", "f")) else 2 if roma[0] in "clx" else 1
        if syllable not in spellings or rank < spellings[syllable][0]:
            spellings[syllable] = (rank, roma)
    tokens = []
    i = 0
    while i < len(kana):
        if kana[i] in "っん":
            tokens.append(kana[i])
            i += 1
        elif kana[i:i + 2] in spellings and len(kana[i:i + 2]) == 2:
            tokens.append(spellings[kana[i:i + 2]][1])
            i += 2
        elif kana[i] in spellings:
            tokens.append(spellings[kana[i]][1])
            i += 1
        else:
            raise ValueError("%s in %s cannot be typed" % (kana[i], kana))
    out = ""
    for k, token in enumerate(tokens):
        after = tokens[k + 1] if k + 1 < len(tokens) else ""
        if token == "ん":
            out += "n'" if after == "ん" or after[:1] in tuple("aiueoy") else "n"
        elif token == "っ":
            if not after or after in "っん" or after[0] in "aiueonm":
                raise ValueError("the っ in %s cannot be typed by doubling" % kana)
            out += "t" if after.startswith("ch") else after[0]
        else:
            out += token
    typed, _ = reference.convert(out, flush=True)
    if typed != kana:
        raise ValueError("%s types %s, not %s" % (out, typed, kana))
    return out


# ---------------------------------------------------------------------------------------------
# The deck
# ---------------------------------------------------------------------------------------------

def deck_rows(path):
    """Yields (line number, line, fields). fields is None for comments, the header and empty lines."""
    with open(path, encoding="utf-8", newline="") as handle:
        lines = handle.read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    header_seen = False
    for number_, line in enumerate(lines, 1):
        line = line.rstrip("\r")
        if line.startswith("#") or not line.strip():
            yield number_, line, None
            continue
        fields = line.split("\t")
        if not header_seen:
            header_seen = True
            if fields != COLUMNS:
                raise ValueError("%s:%d: the header row must be: %s" % (shown(path), number_, " ".join(COLUMNS)))
            yield number_, line, None
            continue
        if len(fields) != len(COLUMNS):
            raise ValueError("%s:%d: %d columns, expected %d" % (shown(path), number_, len(fields), len(COLUMNS)))
        yield number_, line, fields


def shown(path):
    path = os.path.abspath(path)
    if path.startswith(ROOT + os.sep):
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    return path


def generated(fields):
    reading = read(fields[1])
    out = list(fields)
    out[2] = reading.main
    out[4] = "|".join(reading.accepted)
    out[8] = SOURCE
    return out


def fill(path):
    out = []
    changed = rows = 0
    for number_, line, fields in deck_rows(path):
        if fields is None:
            out.append(line)
            continue
        try:
            fresh = generated(fields)
        except ValueError as problem:
            raise ValueError("%s:%d: %s" % (shown(path), number_, problem))
        rows += 1
        changed += fresh != fields
        out.append("\t".join(fresh))
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(out) + "\n")
    print("%s: %d rows, %d changed" % (shown(path), rows, changed))
    return 0


def differences(path):
    """One line for every row whose readings are not the ones this program gives."""
    found = []
    rows = 0
    for number_, _, fields in deck_rows(path):
        if fields is None:
            continue
        rows += 1
        try:
            fresh = generated(fields)
        except ValueError as problem:
            found.append("%s:%d: %s" % (shown(path), number_, problem))
            continue
        for column in (2, 4, 8):
            if fresh[column] != fields[column]:
                found.append("%s:%d: %s of %s is %s, generated is %s"
                             % (shown(path), number_, COLUMNS[column], fields[1], fields[column] or "empty",
                                fresh[column] or "empty"))
    return rows, found


def verify(path):
    rows, found = differences(path)
    for line in found:
        print(line)
    print("%s: %d rows, %d differences" % (shown(path), rows, len(found)))
    return 1 if found else 0


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------

J = "JMdict"
N = "NHK"
W = "numerals"
C = "counters"
M = "minutes"
H = "hours"

# (kind, value, main reading, other forms that must be accepted, source). Each line was compared
# with the source named. Where JMdict lists しち before なな, the order here follows NHK.
KNOWN = [
    ("number", 0, "れい", ["ぜろ"], N),
    ("number", 1, "いち", [], N),
    ("number", 2, "に", [], N),
    ("number", 3, "さん", [], N),
    ("number", 4, "よん", ["し"], N),
    ("number", 5, "ご", [], N),
    ("number", 6, "ろく", [], N),
    ("number", 7, "なな", ["しち"], N),
    ("number", 8, "はち", [], N),
    ("number", 9, "きゅう", ["く"], N),
    ("number", 10, "じゅう", [], N),
    ("number", 11, "じゅういち", [], N),
    ("number", 12, "じゅうに", [], N),
    ("number", 13, "じゅうさん", [], N),
    ("number", 14, "じゅうよん", ["じゅうし"], N),
    ("number", 15, "じゅうご", [], N),
    ("number", 16, "じゅうろく", [], N),
    ("number", 17, "じゅうなな", ["じゅうしち"], N),
    ("number", 18, "じゅうはち", [], N),
    ("number", 19, "じゅうきゅう", ["じゅうく"], N),
    ("number", 20, "にじゅう", [], N),
    ("number", 25, "にじゅうご", [], J),
    ("number", 26, "にじゅうろく", [], J),
    ("number", 27, "にじゅうなな", ["にじゅうしち"], J),
    ("number", 28, "にじゅうはち", [], J),
    ("number", 29, "にじゅうきゅう", [], J),
    ("number", 30, "さんじゅう", [], J),
    ("number", 40, "よんじゅう", [], J),
    ("number", 50, "ごじゅう", [], J),
    ("number", 60, "ろくじゅう", [], J),
    ("number", 70, "ななじゅう", ["しちじゅう"], J),
    ("number", 80, "はちじゅう", [], J),
    ("number", 90, "きゅうじゅう", [], J),
    ("number", 100, "ひゃく", [], J),
    ("number", 108, "ひゃくはち", [], J),
    ("number", 151, "ひゃくごじゅういち", [], W),
    ("number", 200, "にひゃく", [], J),
    ("number", 300, "さんびゃく", [], J),
    ("number", 302, "さんびゃくに", [], W),
    ("number", 400, "よんひゃく", [], J),
    ("number", 469, "よんひゃくろくじゅうきゅう", [], W),
    ("number", 500, "ごひゃく", [], J),
    ("number", 600, "ろっぴゃく", [], J),
    ("number", 700, "ななひゃく", ["しちひゃく"], J),
    ("number", 800, "はっぴゃく", [], J),
    ("number", 900, "きゅうひゃく", [], J),
    ("number", 1000, "せん", [], J),
    ("number", 2025, "にせんにじゅうご", [], W),
    ("number", 3000, "さんぜん", [], J),
    ("number", 4000, "よんせん", [], J),
    ("number", 4002, "よんせんに", [], W),
    ("number", 7000, "ななせん", ["しちせん"], J),
    ("number", 8000, "はっせん", [], J),
    ("number", 10000, "いちまん", [], J),
    ("number", 84000, "はちまんよんせん", [], J),
    ("number", 100000, "じゅうまん", [], J),
    ("number", 800000, "はちじゅうまん", [], J),
    ("number", 1000000, "ひゃくまん", [], J),
    ("number", 5000000, "ごひゃくまん", [], J),
    ("number", 8000000, "はっぴゃくまん", [], J),
    ("number", 10000000, "いっせんまん", ["せんまん"], J),
    ("number", 15000000, "せんごひゃくまん", ["いっせんごひゃくまん"], W),
    ("yen", 1, "いちえん", [], J),
    ("yen", 4, "よえん", [], "four yen"),
    ("yen", 100, "ひゃくえん", [], J),
    ("yen", 1000, "せんえん", [], J),
    ("yen", 10000, "いちまんえん", [], J),
    ("hour", 0, "れいじ", ["ぜろじ"], J),
    ("hour", 1, "いちじ", [], J),
    ("hour", 2, "にじ", [], J),
    ("hour", 3, "さんじ", [], J),
    ("hour", 4, "よじ", [], J),
    ("hour", 5, "ごじ", [], J),
    ("hour", 6, "ろくじ", [], J),
    ("hour", 7, "しちじ", ["ななじ"], J),
    ("hour", 8, "はちじ", [], J),
    ("hour", 9, "くじ", [], J),
    ("hour", 10, "じゅうじ", [], J),
    ("hour", 11, "じゅういちじ", [], J),
    ("hour", 12, "じゅうにじ", [], J),
    ("hour", 13, "じゅうさんじ", [], J),
    ("hour", 14, "じゅうよじ", [], J),
    ("hour", 15, "じゅうごじ", [], J),
    ("hour", 16, "じゅうろくじ", [], J),
    ("hour", 17, "じゅうしちじ", ["じゅうななじ"], J),
    ("hour", 18, "じゅうはちじ", [], J),
    ("hour", 19, "じゅうくじ", [], J),
    ("hour", 20, "にじゅうじ", [], J),
    ("hour", 21, "にじゅういちじ", [], J),
    ("hour", 22, "にじゅうにじ", [], J),
    ("hour", 23, "にじゅうさんじ", [], J),
    ("hour", 24, "にじゅうよじ", ["にじゅうよんじ"], H),
    ("minute", 1, "いっぷん", [], J),
    ("minute", 2, "にふん", [], J),
    ("minute", 3, "さんぷん", [], J),
    ("minute", 4, "よんぷん", ["よんふん"], J),
    ("minute", 5, "ごふん", [], J),
    ("minute", 6, "ろっぷん", [], J),
    ("minute", 7, "ななふん", ["しちふん"], J),
    ("minute", 8, "はっぷん", ["はちふん"], J),
    ("minute", 9, "きゅうふん", [], J),
    ("minute", 10, "じゅっぷん", ["じっぷん"], J),
    ("minute", 11, "じゅういっぷん", [], M),
    ("minute", 12, "じゅうにふん", [], M),
    ("minute", 14, "じゅうよんぷん", [], C),
    ("minute", 24, "にじゅうよんぷん", [], C),
    ("minute", 30, "さんじゅっぷん", ["さんじっぷん"], J),
    ("time12", "0:00", "ごぜんれいじ", [], J),
    ("time12", "12:00", "ごごれいじ", [], J),
    ("month", 1, "いちがつ", [], J),
    ("month", 2, "にがつ", [], J),
    ("month", 3, "さんがつ", [], J),
    ("month", 4, "しがつ", [], J),
    ("month", 5, "ごがつ", [], J),
    ("month", 6, "ろくがつ", [], J),
    ("month", 7, "しちがつ", ["なながつ"], J),
    ("month", 8, "はちがつ", [], J),
    ("month", 9, "くがつ", [], J),
    ("month", 10, "じゅうがつ", [], J),
    ("month", 11, "じゅういちがつ", [], J),
    ("month", 12, "じゅうにがつ", [], J),
    ("day", 1, "ついたち", [], J),
    ("day", 2, "ふつか", [], J),
    ("day", 3, "みっか", [], J),
    ("day", 4, "よっか", [], J),
    ("day", 5, "いつか", [], J),
    ("day", 6, "むいか", [], J),
    ("day", 7, "なのか", [], J),
    ("day", 8, "ようか", [], J),
    ("day", 9, "ここのか", [], J),
    ("day", 10, "とおか", [], J),
    ("day", 11, "じゅういちにち", [], J),
    ("day", 12, "じゅうににち", [], J),
    ("day", 13, "じゅうさんにち", [], J),
    ("day", 14, "じゅうよっか", [], J),
    ("day", 15, "じゅうごにち", [], J),
    ("day", 16, "じゅうろくにち", [], J),
    ("day", 17, "じゅうしちにち", ["じゅうななにち"], J),
    ("day", 18, "じゅうはちにち", [], J),
    ("day", 19, "じゅうくにち", [], J),
    ("day", 20, "はつか", [], J),
    ("day", 21, "にじゅういちにち", [], J),
    ("day", 22, "にじゅうににち", [], J),
    ("day", 23, "にじゅうさんにち", [], J),
    ("day", 24, "にじゅうよっか", [], J),
    ("day", 25, "にじゅうごにち", [], J),
    ("day", 26, "にじゅうろくにち", [], J),
    ("day", 27, "にじゅうしちにち", ["にじゅうななにち"], J),
    ("day", 28, "にじゅうはちにち", [], J),
    ("day", 29, "にじゅうくにち", [], J),
    ("day", 30, "さんじゅうにち", [], J),
    ("day", 31, "さんじゅういちにち", [], J),
]

# (prompt, main reading, every accepted form in order). Chains of the parts above: no source has
# these whole, they guard the way the parts are put together.
CHAINED = [
    ("1,280", "せんにひゃくはちじゅう", []),
    ("¥1,280", "せんにひゃくはちじゅうえん", []),
    ("¥980", "きゅうひゃくはちじゅうえん", []),
    ("¥12,000", "いちまんにせんえん", []),
    ("¥1,005", "せんごえん", []),
    ("¥10,080", "いちまんはちじゅうえん", []),
    ("¥14", "じゅうよえん", []),
    ("¥9", "きゅうえん", []),
    ("¥770", "ななひゃくななじゅうえん",
     ["ななひゃくしちじゅうえん", "しちひゃくななじゅうえん", "しちひゃくしちじゅうえん"]),
    ("¥70,000", "ななまんえん", []),
    ("¥3,600", "さんぜんろっぴゃくえん", []),
    ("¥8,800", "はっせんはっぴゃくえん", []),
    ("¥10,000,000", "いっせんまんえん", ["せんまんえん"]),
    ("¥99,999,999", "きゅうせんきゅうひゃくきゅうじゅうきゅうまんきゅうせんきゅうひゃくきゅうじゅうきゅうえん", []),
    ("14:37", "じゅうよじさんじゅうななふん",
     ["じゅうよじさんじゅうしちふん", "ごごにじさんじゅうななふん", "ごごにじさんじゅうしちふん"]),
    ("9:04", "くじよんぷん", ["くじよんふん", "ごぜんくじよんぷん", "ごぜんくじよんふん"]),
    ("9:00", "くじ", ["ごぜんくじ"]),
    ("9:30", "くじさんじゅっぷん",
     ["くじさんじっぷん", "くじはん", "ごぜんくじさんじゅっぷん", "ごぜんくじさんじっぷん", "ごぜんくじはん"]),
    ("0:05", "れいじごふん", ["ぜろじごふん", "ごぜんれいじごふん"]),
    ("12:15", "じゅうにじじゅうごふん", ["ごごれいじじゅうごふん", "ごごじゅうにじじゅうごふん"]),
    ("12:00", "じゅうにじ", ["ごごれいじ", "ごぜんじゅうにじ"]),
    ("12:30", "じゅうにじさんじゅっぷん",
     ["じゅうにじさんじっぷん", "じゅうにじはん", "ごごれいじさんじゅっぷん", "ごごれいじさんじっぷん", "ごごれいじはん",
      "ごごじゅうにじさんじゅっぷん", "ごごじゅうにじさんじっぷん", "ごごじゅうにじはん"]),
    ("0:00", "れいじ", ["ぜろじ", "ごぜんれいじ"]),
    ("29", "にじゅうきゅう", []),
    ("104", "ひゃくよん", []),
    ("1,004", "せんよん", []),
    ("107", "ひゃくなな", ["ひゃくしち"]),
    ("19:10", "じゅうくじじゅっぷん",
     ["じゅうくじじっぷん", "ごごしちじじゅっぷん", "ごごしちじじっぷん", "ごごななじじゅっぷん", "ごごななじじっぷん"]),
    ("23:59", "にじゅうさんじごじゅうきゅうふん", ["ごごじゅういちじごじゅうきゅうふん"]),
    ("4/20", "しがつはつか", []),
    ("8/1", "はちがつついたち", []),
    ("7/7", "しちがつなのか", ["なながつなのか"]),
    ("9/19", "くがつじゅうくにち", []),
    ("4月20日", "しがつはつか", []),
    ("1280円", "せんにひゃくはちじゅうえん", []),
]

REFUSED = ["", "abc", "¥0", "¥100,000,000", "100000000", "25:00", "12:60", "2/30", "4/31", "13/1", "0/5", "5/0",
           "1,28", "-5", "1.5", "¥007", "¥0,500", "0123", "9:4", "24:60"]


def is_hiragana(text):
    return bool(text) and all(0x3041 <= ord(ch) <= 0x3096 for ch in text)


def known_forms(kind, value):
    if kind == "number":
        return forms(number(value))
    if kind == "yen":
        return forms(yen(value))
    if kind == "hour":
        return hour_forms(value)
    if kind == "minute":
        return minute_forms(value)
    if kind == "month":
        return month_forms(value)
    if kind == "day":
        return day_forms(value)
    if kind == "time12":
        hour, minute = value.split(":")
        return forms(clock12(int(hour), int(minute)))
    raise ValueError(kind)


def every_reading():
    """Every form of every time and date, and of a spread of numbers and prices."""
    values = set(range(0, 1200)) | set(range(1200, 20001, 7)) | set(range(20000, LARGEST, 99991)) | {LARGEST}
    values |= {10 ** k for k in range(8)} | {d * 10 ** k for d in range(1, 10) for k in range(8)}
    for value in sorted(values):
        yield number(value)
        if value:
            yield yen(value)
    for hour in range(25):
        for minute in range(60):
            yield clock(hour, minute)
    for month in range(1, 13):
        for day in range(1, calendar.monthrange(2024, month)[1] + 1):
            yield date(month, day)


def run_checks():
    passed = 0

    for kind, value, main, others, source in KNOWN:
        got = known_forms(kind, value)
        assert got[0] == main, "%s %s: got %s, %s has %s" % (kind, value, got[0], source, main)
        for other in others:
            assert other in got[1:], "%s %s: %s is not accepted" % (kind, value, other)
        passed += 1
    known = passed
    print("known readings, compared with their sources: %d of %d passed" % (passed, len(KNOWN)))

    passed = 0
    for prompt, main, accepted in CHAINED:
        got = read(prompt)
        assert got.main == main, "%s: got %s, expected %s" % (prompt, got.main, main)
        assert list(got.accepted) == accepted, "%s: accepted %s, expected %s" % (prompt, got.accepted, accepted)
        passed += 1
    chained = passed
    print("chained readings: %d of %d passed" % (passed, len(CHAINED)))

    passed = 0
    for prompt in REFUSED:
        try:
            read(prompt)
        except ValueError:
            passed += 1
        else:
            assert False, "%r was not refused" % prompt
    refused = passed
    print("refused prompts: %d of %d passed" % (passed, len(REFUSED)))

    reference = converter()
    readings = answers = 0
    for reading in every_reading():
        listed = forms(reading)
        assert len(set(listed)) == len(listed), "%s is listed twice" % reading.main
        for answer in listed:
            assert is_hiragana(answer), "%s is not hiragana only" % answer
            typing(answer, reference)
            answers += 1
        readings += 1
    print("typing: %d forms of %d readings are hiragana only and typable on the device" % (answers, readings))

    rows = 0
    if os.path.exists(DECK):
        rows, found = differences(DECK)
        assert not found, "\n".join(found)
        print("%s: the readings of all %d rows are the generated ones" % (shown(DECK), rows))
    else:
        print("%s: not there, not checked" % shown(DECK))

    print("result: all passed (%d known, %d chained, %d refused, %d typed, %d deck rows)"
          % (known, chained, refused, answers, rows))
    return 0


# ---------------------------------------------------------------------------------------------

def main(arguments):
    if not arguments:
        return run_checks()
    if arguments[0] in ("--fill", "--verify"):
        if len(arguments) > 2:
            sys.exit("number_reading: %s takes one file" % arguments[0])
        path = arguments[1] if len(arguments) == 2 else DECK
        try:
            return fill(path) if arguments[0] == "--fill" else verify(path)
        except (OSError, ValueError) as problem:
            sys.exit("number_reading: %s" % problem)
    failed = 0
    for argument in arguments:
        try:
            reading = read(argument)
        except ValueError as problem:
            print("%s: %s" % (argument, problem))
            failed = 1
            continue
        print("%s -> %s  %s" % (argument, reading.main, typing(reading.main)))
        for other in reading.accepted:
            print("%s    %s  %s" % (" " * len(argument), other, typing(other)))
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
