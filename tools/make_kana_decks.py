#!/usr/bin/env python3
"""Writes the two kana decks, content/decks/hiragana.tsv and katakana.tsv.

The kana are a fixed table, so the decks are made by this program and not typed by hand. What to
type for each kana comes from the converter's own table; how it sounds is said in a few words
below. Katakana that are easily taken for one another say so.

    python3 tools/make_kana_decks.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app_reader as reader  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOWEL_WORD = {"a": "father", "i": "machine", "u": "flute", "e": "bed", "o": "more"}

# The 46 basic kana in their order, with a word of English that comes near.
BASIC = [
    ("あ", "a as in father"), ("い", "i as in machine"), ("う", "u as in flute, lips relaxed"),
    ("え", "e as in bed"), ("お", "o as in more"),
    ("か", "ka as in car"), ("き", "ki as in key"), ("く", "ku as in cool"), ("け", "ke as in kettle"),
    ("こ", "ko as in coat"),
    ("さ", "sa as in salsa"), ("し", "shi as in sheep; there is no si"), ("す", "su as in soup"),
    ("せ", "se as in set"), ("そ", "so as in sort"),
    ("た", "ta as in tar"), ("ち", "chi as in cheese; there is no ti"), ("つ", "tsu as in cats; there is no tu"),
    ("て", "te as in ten"), ("と", "to as in tall"),
    ("な", "na as in nacho"), ("に", "ni as in knee"), ("ぬ", "nu as in noon"), ("ね", "ne as in net"),
    ("の", "no as in north"),
    ("は", "ha as in harp; as topic marker said wa"), ("ひ", "hi as in he"), ("ふ", "fu: a soft f, lips only"),
    ("へ", "he as in hen; as direction marker said e"), ("ほ", "ho as in horn"),
    ("ま", "ma as in mama"), ("み", "mi as in me"), ("む", "mu as in moon"), ("め", "me as in met"),
    ("も", "mo as in more"),
    ("や", "ya as in yard"), ("ゆ", "yu as in you"), ("よ", "yo as in your"),
    ("ら", "ra: a light tap, between r, l and d"), ("り", "ri: a light tap, as in the tt of city"),
    ("る", "ru: a light tap"), ("れ", "re: a light tap"), ("ろ", "ro: a light tap"),
    ("わ", "wa as in watt"), ("を", "o; typed wo; marks the object"), ("ん", "n: a hum; typed nn, or n before a consonant"),
]

VOICED = [
    ("が", "か"), ("ぎ", "き"), ("ぐ", "く"), ("げ", "け"), ("ご", "こ"),
    ("ざ", "さ"), ("じ", "し"), ("ず", "す"), ("ぜ", "せ"), ("ぞ", "そ"),
    ("だ", "た"), ("ぢ", "ち"), ("づ", "つ"), ("で", "て"), ("ど", "と"),
    ("ば", "は"), ("び", "ひ"), ("ぶ", "ふ"), ("べ", "へ"), ("ぼ", "ほ"),
    ("ぱ", "は"), ("ぴ", "ひ"), ("ぷ", "ふ"), ("ぺ", "へ"), ("ぽ", "ほ"),
]
VOICED_NOTE = {
    "じ": "ji as in jeep: し with two dots", "ぢ": "ji, rare; typed di: ち with two dots",
    "づ": "zu, rare; typed du: つ with two dots",
}

COMBINED = ["きゃ", "きゅ", "きょ", "しゃ", "しゅ", "しょ", "ちゃ", "ちゅ", "ちょ", "にゃ", "にゅ", "にょ",
            "ひゃ", "ひゅ", "ひょ", "みゃ", "みゅ", "みょ", "りゃ", "りゅ", "りょ", "ぎゃ", "ぎゅ", "ぎょ",
            "じゃ", "じゅ", "じょ", "びゃ", "びゅ", "びょ", "ぴゃ", "ぴゅ", "ぴょ"]

# Katakana that are taken for one another.
ALIKE = {
    "シ": "shi: strokes rise from the left. ツ tsu falls",
    "ツ": "tsu: strokes fall from the top. シ shi rises",
    "ソ": "so: the long stroke falls. ン n rises",
    "ン": "n: the long stroke rises. ソ so falls",
    "ノ": "no: one stroke. ソ so and ン n have two",
    "ク": "ku: no bar inside. ケ ke and タ ta have one",
    "ケ": "ke: the bar sticks out to the left",
    "タ": "ta: ク ku with a short stroke inside",
    "ウ": "u: a tick on top. ワ wa has none",
    "ワ": "wa: flat on top. ウ u has a tick",
    "フ": "fu: one corner only. ワ wa has a left side",
    "コ": "ko: open to the left. ユ yu has a long base",
    "ユ": "yu: the base is longer than the top",
    "ヨ": "yo: three bars. コ ko has two",
    "チ": "chi: the top stroke slants. テ te is flat",
    "テ": "te: two flat bars. チ chi slants on top",
    "ス": "su: ends open. ヌ nu has a stroke across",
    "ヌ": "nu: ス su with a stroke across",
    "マ": "ma: the dot is inside. ム mu stands on a base",
    "ム": "mu: a base line with a dot. マ ma is a corner",
    "ア": "a: マ ma with a leg down",
}


def katakana(text):
    return "".join(chr(ord(c) + 0x60) if 0x3041 <= ord(c) <= 0x3096 else c for c in text)


def typed(kana):
    roma = reader.to_romaji(kana)
    if kana == "ん":
        roma = "nn"
    return roma


def rows_for(script):
    other = "hiragana" if script == "katakana" else "katakana"
    rows = []

    def shown(kana):
        return katakana(kana) if script == "katakana" else kana

    def add(kana, note, part):
        prompt = shown(kana)
        if script == "katakana":
            # Particles are written in hiragana, so what is said about them stays there.
            sound = "o, rare; typed wo" if kana == "を" else note.split(";")[0]
            note = ALIKE.get(prompt) or "%s; same as %s" % (sound, kana)
        rows.append((part, "%s-%s" % (script, typed(kana)), prompt, prompt, typed(kana), note))

    for kana, note in BASIC:
        add(kana, note, "the 46 basic kana")
    for kana, plain in VOICED:
        roma = typed(kana)
        mark = "a small circle" if kana in "ぱぴぷぺぽ" else "two dots"
        note = VOICED_NOTE.get(kana) or "%s: %s with %s" % (roma, shown(plain), mark)
        if script == "katakana" and kana in VOICED_NOTE:
            note = VOICED_NOTE[kana].replace("し", "シ").replace("ち", "チ").replace("つ", "ツ")
        prompt = shown(kana)
        rows.append(("with two dots or a circle", "%s-%s" % (script, roma), prompt, prompt, roma, note))
    for kana in COMBINED:
        roma = typed(kana)
        note = "%s: %s and a small %s, one beat" % (roma, shown(kana[0]), shown(kana[1]))
        prompt = shown(kana)
        rows.append(("two kana, one beat", "%s-%s" % (script, roma), prompt, prompt, roma, note))
    return rows, other


def write(script, name_ja, name_en, stage):
    rows, _ = rows_for(script)
    lines = [
        "# name-ja: " + name_ja,
        "# name-en: " + name_en,
        "# kind: kana",
        "# stage: %d" % stage,
        "# Written by tools/make_kana_decks.py. Change the program, not this file.",
        "# The gloss is what to type. The note says how it sounds, or, for katakana that are",
        "# taken for one another, how to tell them apart.",
        "\t".join(["id", "prompt", "reading", "accent", "accepted", "gloss", "note", "level", "source"]),
    ]
    part = None
    seen = set()
    for group, item_id, prompt, reading, gloss, note in rows:
        if group != part:
            part = group
            lines.append("# " + group)
        if item_id in seen:
            sys.exit("two kana share the id " + item_id)
        seen.add(item_id)
        if not reader.types_back(reading) and reading not in ("ん", "ン"):
            sys.exit("%s cannot be typed back from %s" % (reading, gloss))
        lines.append("\t".join([item_id, prompt, reading, "", "", gloss, note, "1", "kana table"]))
    path = os.path.join(ROOT, "content", "decks", script + ".tsv")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("%s: %d kana" % (os.path.relpath(path, ROOT), len(rows)))


def main():
    write("hiragana", "ひらがな", "hiragana", 1)
    write("katakana", "カタカナ", "katakana", 2)


if __name__ == "__main__":
    main()
