#!/usr/bin/env python3
"""Python mirror of lib/romaji/romaji.cpp.

Two uses:
  * content tools on the computer can check that a phrase's romaji really types the expected kana
    on the device;
  * on machines that cannot run locally built programs, `python3 tools/romaji_reference.py` runs the
    test vectors from test/test_romaji/test_romaji.cpp against this mirror. That checks the
    conversion rules and the expected values. It does not execute the C++ itself.

The syllable table is read from romaji.cpp so that there is a single copy of it.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CPP = os.path.join(ROOT, "lib", "romaji", "romaji.cpp")
TESTS = os.path.join(ROOT, "test", "test_romaji", "test_romaji.cpp")

MAX_KEY_LENGTH = 4
PUNCTUATION = {",": "、", ".": "。", "?": "？", "!": "！", "[": "「", "]": "」", "~": "〜"}
VOWELS = "aiueo"


def load_table():
    source = open(CPP, encoding="utf-8").read()
    body = source[source.index("const Entry kTable[]"):]
    body = body[:body.index("};")]
    table = dict(re.findall(r'\{"([a-z]+)",\s*"([^"]+)"\}', body))
    if len(table) < 200:
        raise SystemExit("could not read the syllable table from romaji.cpp")
    return table


TABLE = load_table()
PREFIXES = {key[:n] for key in TABLE for n in range(1, len(key))}


def is_letter(c):
    return "a" <= c <= "z"


def convert(text, ime=False, punctuation=True, flush=False):
    """Returns (kana, pending)."""
    s = "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)
    n = len(s)
    out = []
    pending = ""
    i = 0
    while i < n:
        c = s[i]
        has_next = i + 1 < n
        nxt = s[i + 1] if has_next else ""

        if c == "-":
            out.append("ー")
            i += 1
            continue

        if not is_letter(c):
            if punctuation and c in PUNCTUATION:
                out.append(PUNCTUATION[c])
            elif c != "'":
                out.append(c)
            i += 1
            continue

        if c == "n":
            if not has_next:
                if flush:
                    out.append("ん")
                else:
                    pending = "n"
                break
            if nxt == "'":
                out.append("ん")
                i += 2
                continue
            if nxt == "n":
                out.append("ん")
                if ime:
                    i += 2
                    continue
                has_third = i + 2 < n
                third = s[i + 2] if has_third else ""
                if has_third and (third in VOWELS or third == "y"):
                    i += 1
                elif not has_third and not flush:
                    pending = "n"
                    break
                else:
                    i += 2
                continue
            if nxt not in VOWELS and nxt != "y":
                out.append("ん")
                i += 1
                continue
        elif c == "m" and not ime and has_next and nxt in "bpm":
            out.append("ん")
            i += 1
            continue
        elif c not in VOWELS and has_next:
            doubled = nxt == c
            tch = c == "t" and nxt == "c" and i + 2 < n and s[i + 2] == "h"
            if doubled or tch:
                out.append("っ")
                i += 1
                continue

        remaining = n - i
        matched = False
        for length in range(min(remaining, MAX_KEY_LENGTH), 0, -1):
            kana = TABLE.get(s[i:i + length])
            if kana:
                out.append(kana)
                i += length
                matched = True
                break
        if matched:
            continue

        if not flush and remaining < MAX_KEY_LENGTH and s[i:] in PREFIXES:
            pending = s[i:]
            break
        if not flush and remaining == 2 and c == "t" and nxt == "c":
            pending = s[i:]
            break

        out.append(c)
        i += 1

    return "".join(out), pending


def to_katakana(text):
    out = []
    for ch in text:
        cp = ord(ch)
        if 0x3041 <= cp <= 0x3096 or cp in (0x309D, 0x309E):
            cp += 0x60
        out.append(chr(cp))
    return "".join(out)


def unescape(literal):
    # The C++ tests only use plain UTF-8 text and \x escapes for the truncated-input case.
    return literal


def run_test_vectors():
    source = open(TESTS, encoding="utf-8").read()
    checked = 0
    failures = []

    def check(label, got, want):
        nonlocal checked
        checked += 1
        if got != want:
            failures.append("%s: got %r, want %r" % (label, got, want))

    for want, style, given in re.findall(r'TEST_ASSERT_EQUAL_STRING\("([^"\\]*)", (hep|ime)\("([^"\\]*)"\)\.c_str\(\)\)',
                                         source):
        kana, _ = convert(given, ime=(style == "ime"), flush=True)
        check("%s(%s)" % (style, given), kana, want)

    for a_style, a, b_style, b in re.findall(
            r'TEST_ASSERT_EQUAL_STRING\((hep|ime)\("([^"]*)"\)\.c_str\(\), (hep|ime)\("([^"]*)"\)\.c_str\(\)\)', source):
        left, _ = convert(a, ime=(a_style == "ime"), flush=True)
        right, _ = convert(b, ime=(b_style == "ime"), flush=True)
        check("%s == %s" % (a, b), right, left)

    for want, given in re.findall(
            r'TEST_ASSERT_EQUAL_STRING\("([^"\\]*)", romaji::toKatakana\(hep\("([^"\\]*)"\)\)\.c_str\(\)\)', source):
        kana, _ = convert(given, flush=True)
        check("katakana(%s)" % given, to_katakana(kana), want)

    for want, given in re.findall(
            r'TEST_ASSERT_EQUAL_STRING\("([^"\\]*)", romaji::toKatakana\("([^"\\]*)"\)\.c_str\(\)\)', source):
        check("katakana literal(%s)" % given, to_katakana(given), want)

    for given, want_kana, want_pending in re.findall(r'expectLive\("([^"\\]*)", "([^"\\]*)", "([^"\\]*)"\);', source):
        kana, pending = convert(given, flush=False)
        check("live(%s) kana" % given, kana, want_kana)
        check("live(%s) pending" % given, pending, want_pending)

    for want, given, field in re.findall(
            r'TEST_ASSERT_EQUAL_STRING\("([^"\\]*)", romaji::convert\("([^"\\]*)", Options\(\), true\)\.(kana|pending)\.c_str\(\)\)',
            source):
        kana, pending = convert(given, flush=True)
        check("flush(%s).%s" % (given, field), kana if field == "kana" else pending, want)

    for want, given in re.findall(
            r'TEST_ASSERT_EQUAL_STRING\("([^"\\]*)", romaji::convert\("([^"\\]*)", plain, true\)\.kana\.c_str\(\)\)', source):
        kana, _ = convert(given, punctuation=False, flush=True)
        check("plain(%s)" % given, kana, want)

    total_assertions = len(re.findall(r"TEST_ASSERT_EQUAL_STRING", source)) - 2  # two live in the expectLive helper
    total_assertions += 2 * len(re.findall(r"^\s*expectLive\(\"", source, flags=re.M))
    print("syllables in table: %d" % len(TABLE))
    print("test vectors checked: %d of %d assertions in the C++ test file" % (checked, total_assertions))
    for failure in failures:
        print("FAIL " + failure)
    print("result: %s" % ("FAILED (%d)" % len(failures) if failures else "all passed"))
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for word in sys.argv[1:]:
            kana, pending = convert(word, flush=True)
            print("%s -> %s  %s" % (word, kana, to_katakana(kana)))
        sys.exit(0)
    sys.exit(run_test_vectors())
