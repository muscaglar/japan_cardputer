#!/usr/bin/env python3
"""Tests for tools/build_decks.py.

    python3 tools/tests/test_build_decks.py            # everything
    python3 tools/tests/test_build_decks.py untypable  # the tests whose name contains a word

Runs the tool on the fixtures in tools/tests/fixtures: one folder per kind of mistake, and the folder
`clean`, which builds. For every folder the findings are compared with the list below, line by line,
so a check that stops firing fails a test, and so does a check that starts firing where it should not.

The C++ that the tool writes is then compiled with Emscripten and run under Node, where it prints
the tables back. Without Emscripten or Node those tests are reported as SKIPPED and the run fails,
unless --allow-skips is given.

Nothing outside build/test_build_decks/ is written.
"""
import os
import re
import shutil
import subprocess
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
ROOT = os.path.dirname(TOOLS)
FIXTURES = os.path.join(TESTS, "fixtures")
FIXTURE_CACHE = os.path.join(FIXTURES, "cache")
REAL_CACHE = os.path.join(ROOT, "local", "cache")
WORK = os.path.join(ROOT, "build", "test_build_decks")
TOOL = os.path.join(TOOLS, "build_decks.py")

sys.path.insert(0, TOOLS)
import build_decks  # noqa: E402
import romaji_reference  # noqa: E402

E = "error"
W = "warning"
SIGNS = "decks/signs.tsv"
BUDDY = "buddy.tsv"
KANJI = "kanji.tsv"
PARTS = "parts.tsv"
GUIDE = "guide.tsv"
OFFLINE_NOTE = "the dictionary checks were skipped"
KANJIDIC_NOTE = "was not compared with KANJIDIC"
# the tables beside the deck folder: file, the word that starts its summary line, what it counts
TABLES = [(BUDDY, "buddy", "line"), (KANJI, "kanji", "row"), (PARTS, "parts", "row"), (GUIDE, "guide", "page")]

# folder -> (dictionary, exit code, findings, notes)
#   dictionary: False runs with --offline, True with the excerpt in fixtures/cache
#   findings:   (file, line, severity, words the message must contain)
#   notes:      words that one of the notes must contain
CASES = {
    # the table itself
    "header-wrong": (False, 1, [
        (SIGNS, 5, E, "header row must be: id prompt reading accent accepted gloss note level source"),
    ], []),
    "header-missing": (False, 1, [
        (SIGNS, 4, E, "no header row"),
    ], []),
    "empty-file": (False, 1, [
        (SIGNS, 1, E, "the file is empty"),
    ], []),
    "row-of-tabs": (False, 1, [
        (SIGNS, 7, E, "a row without values"),
    ], []),
    "other-files": (False, 0, [
        ("decks/signs-old.txt", 1, W, "not a deck file (*.tsv): left out"),
    ], []),
    "columns": (False, 1, [
        (SIGNS, 7, E, "8 columns, expected 9"),
        (SIGNS, 8, E, "10 columns, expected 9"),
    ], []),
    "names-missing": (False, 1, [
        (SIGNS, 1, E, "no \"# name-ja: ...\" line"),
        (SIGNS, 1, E, "no \"# name-en: ...\" line"),
        (SIGNS, 1, E, "no \"# kind: ...\" line"),
    ], []),
    "names-wrong": (False, 1, [
        (SIGNS, 2, E, "name-ja: 看板 is not kana only"),
        (SIGNS, 4, E, "kind phrase is not one of kana, word, counter, number"),
    ], []),
    "names-twice": (False, 1, [
        (SIGNS, 5, E, "kind is given twice"),
    ], []),
    "names-below-header": (False, 1, [
        (SIGNS, 4, E, "name-en must stand above the header row"),
        (SIGNS, 5, E, "kind must stand above the header row"),
    ], []),
    "stage-wrong": (False, 1, [
        ("decks/counters.tsv", 5, E, "stage \"0\" is not a number from 1 to 9"),
        ("decks/food.tsv", 5, E, "stage \"10\" is not a number from 1 to 9"),
        ("decks/katakana-words.tsv", 5, E, "stage \"1.5\" is not a number from 1 to 9"),
        ("decks/numbers.tsv", 5, E, "stage \"two\" is not a number from 1 to 9"),
        ("decks/replies.tsv", 5, E, "stage \"\" is not a number from 1 to 9"),
        (SIGNS, 6, E, "stage is given twice"),
    ], []),
    "file-name": (False, 1, [
        ("decks/Bad_Name.tsv", 1, E, "the deck id Bad_Name must be lower case"),
    ], []),
    "no-rows": (False, 1, [
        (SIGNS, 1, E, "the deck has no rows"),
    ], []),
    "no-decks": (False, 1, [
        ("decks", 1, E, "no deck files"),
        ("decks/not-a-deck.txt", 1, W, "not a deck file (*.tsv): left out"),
    ], []),
    "edge-spaces": (False, 1, [
        (SIGNS, 6, E, "reading, gloss: spaces at the start or the end"),
    ], []),
    "empty-fields": (False, 1, [
        (SIGNS, 6, E, "prompt is empty"),
        (SIGNS, 7, E, "gloss is empty"),
        (SIGNS, 8, E, "reading is empty"),
    ], []),
    # ids
    "id-format": (False, 1, [
        (SIGNS, 6, E, "id \"Sign-Kippu\" must be lower case letters, digits and hyphens"),
        (SIGNS, 7, E, "id \"sign_deguchi\" must be"),
        (SIGNS, 8, E, "id \"sign--iriguchi\" must be"),
        (SIGNS, 9, E, "id \"\" must be"),
    ], []),
    "id-duplicate": (False, 1, [
        (SIGNS, 7, E, "id sign-deguchi is already used at "
                      "tools/tests/fixtures/id-duplicate/decks/food.tsv:6"),
        (SIGNS, 8, E, "id sign-kippu is already used at tools/tests/fixtures/id-duplicate/decks/signs.tsv:6"),
    ], []),
    "id-disappeared": (False, 1, [
        ("ids.txt", 2, E, "id sign-deguchi was published and has disappeared"),
        ("ids.txt", 4, E, "\"Not An Id\" is not an id"),
    ], []),
    "id-key-clash": (False, 1, [
        (SIGNS, 7, E, "id clash-oc4zgvo has the same key as clash-9utp4"),
    ], []),
    # answers
    "reading-not-kana": (False, 1, [
        (SIGNS, 6, E, "reading: 切符 is not kana only"),
        (SIGNS, 7, E, "reading: deguchi is not kana only"),
        (SIGNS, 8, E, "reading: いり ぐち is not kana only (a space)"),
    ], []),
    "accepted-not-kana": (False, 1, [
        (SIGNS, 6, E, "accepted: 入口 is not kana only"),
        (SIGNS, 7, E, "accepted: kippu is not kana only"),
    ], []),
    "accepted-empty-part": (False, 1, [
        (SIGNS, 6, E, "accepted: an empty answer"),
        (SIGNS, 7, E, "accepted: an empty answer"),
        (SIGNS, 7, W, "accepted: きっぷ is the reading itself"),
    ], []),
    "accepted-twice": (False, 0, [
        (SIGNS, 6, W, "accepted: いりくち is given twice"),
        (SIGNS, 7, W, "accepted: きっぷ is the reading itself"),
    ], []),
    "untypable": (False, 1, [
        (SIGNS, 6, E, "reading: こゝろ cannot be typed"),
        (SIGNS, 7, E, "accepted: こゝろ cannot be typed"),
    ], []),
    "answer-long": (False, 1, [
        ("decks/numbers.tsv", 7, E, "kyuuhyakuhachijuuen is 49 letters long, the device takes 48"),
    ], []),
    "accent-beats": (False, 1, [
        (SIGNS, 6, E, "accent 4 is larger than the 3 beats of でぐち"),
        (SIGNS, 7, E, "accent 3 is larger than the 2 beats of きゃく"),
    ], []),
    "accent-not-a-number": (False, 1, [
        (SIGNS, 6, E, "accent \"x\" is not a number"),
        (SIGNS, 7, E, "accent \"-1\" is not a number"),
        (SIGNS, 8, E, "accent \"0,3\" is not a number"),
        (SIGNS, 9, E, "accent \"01\" is not a number"),
    ], []),
    # what the screen can show
    "glyph-missing": (False, 1, [
        ("decks/kana.tsv", 6, E, "prompt: no glyph for ゖ in efontJA_16, ゖ in efontJA_12"),
        ("decks/kana.tsv", 6, E, "reading: no glyph for ゖ in efontJA_16, ゖ in efontJA_12"),
        (SIGNS, 6, E, "prompt: no glyph for 𠮟 in efontJA_16, 𠮟 in efontJA_12"),
        (SIGNS, 7, E, "note: no glyph for 𠮟"),
        (SIGNS, 8, E, "gloss: no glyph for ✔"),
    ], []),
    "glyph-big-font": (False, 0, [
        (SIGNS, 6, W, "prompt: no glyph for 餃 in lgfxJapanGothic_32, so it is drawn with a smaller font"),
    ], []),
    "gloss-long": (False, 1, [
        (SIGNS, 6, E, "gloss is 33 characters long, at most 32 fit"),
        (SIGNS, 7, E, "gloss is 33 characters long, at most 32 fit"),
    ], []),
    "note-long": (False, 1, [
        (SIGNS, 6, E, "note is 60 letters wide, at most 52 fit"),
        (SIGNS, 7, E, "note is 53 letters wide, at most 52 fit"),
        (SIGNS, 9, E, "note is 54 letters wide, at most 52 fit"),
    ], []),
    "level-wrong": (False, 1, [
        (SIGNS, 6, E, "level \"0\" is not 1, 2 or 3"),
        (SIGNS, 7, E, "level \"4\" is not 1, 2 or 3"),
        (SIGNS, 8, E, "level \"\" is not 1, 2 or 3"),
        (SIGNS, 9, E, "level \"two\" is not 1, 2 or 3"),
    ], []),
    "level-1-kanji": (False, 1, [
        (SIGNS, 6, E, "level 1 is kana only, but the prompt contains kanji (切符)"),
        (SIGNS, 7, E, "level 1 is kana only, but the prompt contains kanji (茶)"),
        (SIGNS, 9, E, "level 1 is kana only, but the prompt contains kanji (〇)"),
    ], []),
    # dictionary and accent list
    "dict-reading": (True, 1, [
        (SIGNS, 6, E, "JMdict does not read 切符 as きつぷ (it has きっぷ)"),
        (SIGNS, 7, E, "JMdict does not read 出口 as でくち (it has でぐち)"),
        (SIGNS, 8, W, "no glyph for 餃 in lgfxJapanGothic_32"),
    ], [
        "signs: 1 accent filled in from the accent list: sign-gyouza 0",
    ]),
    "dict-no-headword": (True, 1, [
        (SIGNS, 6, E, "一日乗車券 is not a JMdict headword, and the source column names no other source"),
        (SIGNS, 7, E, "一日乗車券 is not a JMdict headword, and the source column names no other source"),
        (SIGNS, 8, W, "一日乗車券 is not a JMdict headword: reading and meaning rest on the source alone"),
    ], []),
    "dict-accepted": (True, 0, [
        (SIGNS, 6, W, "accepted: JMdict does not read 入口 as でぐち: it rests on the source alone"),
    ], []),
    "dict-accent-not-listed": (True, 1, [
        (SIGNS, 6, E, "accent 0 is not listed for 出口 read でぐち (the accent list has 1)"),
        (SIGNS, 7, E, "accent 2 is not listed for 結構 read けっこう (the accent list has 0, 3, 1)"),
    ], []),
    "dict-accent-second": (True, 0, [
        ("decks/replies.tsv", 6, W, "accent 2 is listed for 心 read こころ, but the usual one, the first in the accent "
                                    "list, is 3"),
    ], []),
    "dict-accent-no-entry": (True, 1, [
        ("decks/counters.tsv", 6, E, "accent 1, but the accent list has no entry for ビール × 3 read さんぼん"),
        (SIGNS, 6, E, "accent 0, but the accent list has no entry for 精算機 read せいさんき"),
        (SIGNS, 7, E, "accent 1, but the accent list has no entry for でぐち read でぐち"),
    ], []),
    "dict-accent-part-of-speech": (True, 0, [
    ], [
        "replies: 1 accent filled in from the accent list: reply-daijoubu 3",
        "replies: no accent filled in where the accent list gives one per part of speech; the deck has to "
        "say which: reply-kekkou (0, 3, 1)",
    ]),
    "dict-other-kinds": (True, 0, [
    ], []),
    "romaji-help": (True, 0, [
    ], [
        "food: 3 accents filled in from the accent list: food-tsuzuku 0, food-paatii 1, food-koohii 3",
    ]),
    "first-build": (True, 0, [
    ], []),
    # the buddy
    "buddy-mood": (False, 1, [
        (BUDDY, 3, E, "mood \"happy\" is not one of greeting, start, right, streak, wrong, almost, finish, "
                      "back, low-battery, idle"),
        (BUDDY, 4, E, "mood \"\" is not one of"),
    ], []),
    "buddy-ja-not-kana": (False, 1, [
        (BUDDY, 3, E, "ja: 今日も よろしくね。 is not kana only (今日)"),
        (BUDDY, 4, E, "ja: OK！ is not kana only (OK)"),
    ], []),
    "buddy-ja-long": (False, 1, [
        (BUDDY, 3, E, "ja is 16 characters long, at most 15 fit"),
    ], []),
    "buddy-en-long": (False, 1, [
        (BUDDY, 4, E, "en is 35 characters long, at most 34 fit"),
    ], []),
    "buddy-id": (False, 1, [
        (BUDDY, 4, E, "id buddy-greeting-01 is already used at tools/tests/fixtures/buddy-id/buddy.tsv:3"),
        (BUDDY, 5, E, "id \"Buddy 3\" must be lower case"),
        (BUDDY, 6, E, "id sign-kippu is already used at tools/tests/fixtures/buddy-id/decks/signs.tsv:6"),
    ], []),
    "buddy-columns": (False, 1, [
        (BUDDY, 3, E, "3 columns, expected 4"),
        (BUDDY, 4, E, "5 columns, expected 4"),
    ], []),
    "buddy-empty": (False, 1, [
        (BUDDY, 3, E, "ja is empty"),
        (BUDDY, 4, E, "en is empty"),
    ], []),
    "buddy-header": (False, 1, [
        (BUDDY, 2, E, "header row must be: id mood ja en"),
    ], []),
    # what each kanji means
    "kanji-not-one": (False, 1, [
        (KANJI, 5, E, "kanji \"出口\" is not one kanji"),
        (KANJI, 6, E, "kanji \"で\" is not one kanji"),
        (KANJI, 7, E, "kanji \"x\" is not one kanji"),
        (KANJI, 8, E, "kanji \"\" is not one kanji"),
    ], []),
    "kanji-twice": (False, 1, [
        (KANJI, 6, E, "口 is given twice: first in line 4"),
    ], []),
    "kanji-meaning": (False, 1, [
        (KANJI, 3, E, "meaning \"Go out\" must be lower case words with one space or hyphen between them"),
        (KANJI, 5, E, "meaning \"go  in\" must be lower case words"),
        (KANJI, 6, E, "meaning \"not-\" must be lower case words"),
        (KANJI, 7, E, "meaning is empty"),
        (KANJI, 9, E, "meaning \"tobacco smoke\" is 13 letters long, at most 12 fit"),
        (KANJI, 11, E, "meaning \"token 1\" must be lower case words"),
        (SIGNS, 8, W, "常 in 非常口 has no meaning in tools/tests/fixtures/kanji-meaning/kanji.tsv"),
    ], []),
    "kanji-basis": (True, 1, [
        (KANJI, 4, E, "basis \"opening\" is not a KANJIDIC meaning of 口 (mouth)"),
        (KANJI, 5, E, "basis is empty"),
        (KANJI, 6, E, "basis \"Cut\" is not a KANJIDIC meaning of 切 (cut, cutoff, be sharp)"),
        (KANJI, 8, E, "basis \"JMdict: 出口\" names a word without 交"),
        (KANJI, 11, E, "basis \"jmdict: 乗車券\" is not a KANJIDIC meaning of 車 (car)"),
        (KANJI, 12, E, "basis \"JMdict: 一日乗車券\": 一日乗車券 is not a JMdict headword"),
    ], []),
    "kanji-no-row": (False, 0, [
        (SIGNS, 6, W, "口 in 出口 has no meaning in tools/tests/fixtures/kanji-no-row/kanji.tsv"),
        (SIGNS, 8, W, "非 in 非常口 has no meaning in"),
        (SIGNS, 8, W, "常 in 非常口 has no meaning in"),
    ], []),
    "kanji-line-wide": (False, 0, [
        (SIGNS, 7, W, "the meanings of the kanji of 遺失物取扱所 are 60 letters wide, 54 fit: the end will be cut off"),
    ], []),
    "kanji-words": (False, 0, [
        (KANJI, 3, W, "words: 出発 is not a prompt of a deck"),
        (KANJI, 4, W, "words: 入場 is written without 口"),
        (KANJI, 6, W, "words: 禁煙 is not a prompt of a deck"),
        (KANJI, 6, W, "no prompt of a deck is written with 煙: the row is not used"),
        (KANJI, 7, W, "no prompt of a deck is written with 禁: the row is not used"),
    ], []),
    "kanji-header": (False, 1, [
        (KANJI, 2, E, "header row must be: kanji meaning basis words"),
    ], []),
    # the lines about kanji that are written by hand
    "parts-prompt": (False, 1, [
        (PARTS, 4, E, "出入口 is not a prompt of a deck"),
        (PARTS, 5, E, "交番 is given twice: first in line 3"),
        (PARTS, 6, E, "prompt is empty"),
        (PARTS, 7, E, "こうばん is not a prompt of a deck"),
    ], []),
    "parts-kanji": (False, 1, [
        (PARTS, 3, E, "parts: 出 is not a kanji of 入口"),
        (PARTS, 4, E, "parts: 所 is not a kanji of 交番"),
    ], []),
    "parts-long": (False, 1, [
        (PARTS, 4, E, "parts is 55 letters wide, at most 54 fit"),
        (PARTS, 6, E, "parts is 55 letters wide, at most 54 fit"),
    ], []),
    "parts-reason": (False, 1, [
        (PARTS, 3, E, "reason is empty"),
        (PARTS, 4, E, "reason is empty"),
    ], []),
    "parts-glyph": (False, 1, [
        (PARTS, 3, E, "parts: no glyph for ✔ in efontJA_16, ✔ in efontJA_12"),
    ], []),
    "parts-header": (False, 1, [
        (PARTS, 2, E, "header row must be: prompt parts reason"),
    ], []),
    # the guide
    "guide-id": (False, 1, [
        (GUIDE, 4, E, "id \"Guide 2\" must be lower case letters, digits and hyphens"),
        (GUIDE, 5, E, "id guide-vowels is already used at tools/tests/fixtures/guide-id/guide.tsv:3"),
        (GUIDE, 6, E, "id sign-kippu is already used at tools/tests/fixtures/guide-id/decks/signs.tsv:6"),
        (GUIDE, 7, E, "id buddy-greeting-01 is already used at tools/tests/fixtures/guide-id/buddy.tsv:3"),
        (GUIDE, 8, E, "id \"\" must be lower case"),
    ], []),
    "guide-title": (False, 1, [
        (GUIDE, 4, E, "title is 21 letters wide, at most 20 fit"),
        (GUIDE, 5, E, "title is 22 letters wide, at most 20 fit"),
        (GUIDE, 7, E, "title is empty"),
    ], []),
    "guide-line-wide": (False, 1, [
        (GUIDE, 3, E, "the line \"a i u e o do not ever change\" is 28 letters wide, at most 27 fit"),
        (GUIDE, 4, E, "the line \"おばあさん is a grandmother.\" is 28 letters wide, at most 27 fit"),
    ], []),
    "guide-lines": (False, 1, [
        (GUIDE, 4, E, "body has 6 lines, at most 5 fit"),
        (GUIDE, 5, E, "body is empty"),
        (GUIDE, 6, E, "body is empty"),
    ], []),
    "guide-clips": (False, 1, [
        (GUIDE, 3, E, "clips: aiueo is not kana only (aiueo)"),
        (GUIDE, 4, E, "clips: 雨 is not kana only (雨)"),
        (GUIDE, 5, E, "clips: あめ です is not kana only (a space)"),
        (GUIDE, 6, E, "clips: an empty clip"),
        (GUIDE, 7, E, "clips: an empty clip"),
        (GUIDE, 8, W, "clips: あ is given twice"),
    ], []),
    "guide-glyph": (False, 1, [
        (GUIDE, 3, E, "title: no glyph for ✔ in efontJA_16, ✔ in efontJA_12"),
        (GUIDE, 4, E, "body: no glyph for 𠮟 in efontJA_16, 𠮟 in efontJA_12"),
        (GUIDE, 5, E, "clips: no glyph for ゖ in efontJA_16, ゖ in efontJA_12"),
    ], []),
    "guide-header": (False, 1, [
        (GUIDE, 2, E, "header row must be: id title body clips"),
    ], []),
}

# What the clean fixture must come out as: the decks in the order of the course, then the others by name.
CLEAN_DECKS = ["hiragana", "katakana", "numbers", "counters", "katakana-words", "signs", "food", "replies"]
# food has no "# stage" line
CLEAN_STAGES = {"hiragana": 1, "katakana": 2, "numbers": 2, "counters": 2, "katakana-words": 3, "signs": 3,
                "food": 1, "replies": 9}
CLEAN_ACCENTS = {
    "kata-koohii": 3, "kata-hoteru": 1, "kata-konbini": 0, "kata-paatii": 1, "kata-takushii": 1,
    "sign-deguchi": 1, "sign-iriguchi": 0, "sign-hijouguchi": 2, "sign-kinen": 0, "sign-kippu": 0,
    "sign-kouban": 0, "food-mizu": 0, "food-ocha": 0, "food-gohan": 1, "reply-kekkou": 1, "reply-daijoubu": 3,
}
# these accents are not in the deck: the tool fills them in
CLEAN_FILLED = ["kata-koohii", "kata-konbini", "kata-paatii", "sign-deguchi", "sign-kinen", "sign-kouban",
                "food-mizu", "food-gohan", "reply-daijoubu"]
# The line about the kanji of a prompt. That of 交番 is written in parts.tsv. 大丈夫 has none, because
# parts.tsv says so; the other items have none, because their prompts have no kanji.
CLEAN_PARTS = {
    "num-300-yen": "円 yen", "num-9-ji": "時 hour",
    "sign-deguchi": "出 go out  口 opening", "sign-iriguchi": "入 enter  口 opening",
    "sign-hijouguchi": "非 not  常 usual  口 opening", "sign-kinen": "禁 forbid  煙 smoke",
    "sign-kippu": "切 cut  符 token", "sign-seisanki": "精 exact  算 calculate  機 machine",
    "sign-kouban": "交 take turns  番 watch",
    "food-mizu": "水 water", "food-ocha": "茶 tea", "food-gohan": "飯 meal",
    "reply-kekkou": "結 tie  構 build",
}
CLEAN_ITEMS = 29
KIND_NUMBER = {"kana": 0, "word": 1, "counter": 2, "number": 3}

DUMP = r"""
// Prints the compiled tables back, one line per deck, item, buddy line and page of the guide, fields
// separated by tabs. The lines of a page are printed with | between them, as the table has them.
#include <cstdio>
#include "deck.h"

extern const deck::BuddyLine kBuddyLines[];
extern const size_t kBuddyLineCount;

int main()
{
    for (size_t d = 0; d < deck::count(); ++d) {
        const deck::Deck& k = deck::at(d);
        std::printf("deck\t%s\t%s\t%s\t%u\t%u\t%s\n", k.id, k.nameJa, k.nameEn, static_cast<unsigned>(k.count),
                    static_cast<unsigned>(k.stage), deck::find(k.id) == &k ? "found" : "lost");
        for (unsigned i = 0; i < k.count; ++i) {
            const deck::Item& it = k.items[i];
            std::printf("item\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%u\t%u\t%08x\t%s\n", it.id, it.prompt, it.reading,
                        it.accepted, it.gloss, it.note, it.parts, static_cast<int>(it.accent),
                        static_cast<unsigned>(it.level), static_cast<unsigned>(it.kind),
                        static_cast<unsigned>(deck::key(it.id)), deck::findItem(it.id) == &it ? "found" : "lost");
        }
    }
    for (size_t b = 0; b < kBuddyLineCount; ++b) {
        std::printf("buddy\t%s\t%s\t%s\t%s\n", kBuddyLines[b].id, kBuddyLines[b].mood, kBuddyLines[b].ja,
                    kBuddyLines[b].en);
    }
    for (size_t g = 0; g < deck::guidePageCount(); ++g) {
        const deck::GuidePage& page = deck::guidePage(g);
        std::printf("guide\t%s\t%s\t", page.id, page.title);
        for (const char* p = page.body; *p; ++p) {
            std::putchar(*p == '\n' ? '|' : *p);
        }
        std::printf("\t%s\n", page.clips);
    }
    std::printf("end\t%u\t%u\t%u\n", static_cast<unsigned>(deck::count()), static_cast<unsigned>(kBuddyLineCount),
                static_cast<unsigned>(deck::guidePageCount()));
    return 0;
}
"""


class Failure(Exception):
    pass


def expect(condition, message):
    if not condition:
        raise Failure(message)


def same(got, want, what):
    if got != want:
        raise Failure("%s:\n      got  %r\n      want %r" % (what, got, want))


def run_tool(*arguments):
    """Returns (exit code, output)."""
    result = subprocess.run([sys.executable, TOOL] + list(arguments), capture_output=True, text=True, encoding="utf-8")
    return result.returncode, result.stdout + result.stderr


def findings_of(output):
    found = []
    for line in output.splitlines():
        match = re.match(r"(.+?):(\d+): (error|warning): (.*)\Z", line)
        if match:
            found.append((match.group(1), int(match.group(2)), match.group(3), match.group(4)))
    return found


def notes_of(output):
    return [line[len("note: "):] for line in output.splitlines() if line.startswith("note: ")]


def workspace(name):
    path = os.path.join(WORK, name)
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode, **({} if isinstance(data, bytes) else {"encoding": "utf-8", "newline": ""})) as handle:
        handle.write(data)


def table(path):
    """The rows of a fixture, read without the tool."""
    rows = []
    for line in read(path).split("\n"):
        if line and not line.startswith("#"):
            rows.append(line.split("\t"))
    return rows[1:]


def build_clean(name, *extra):
    """Builds the clean fixture into its own folder. Returns (folder, exit code, output)."""
    work = workspace(name)
    shutil.copy(os.path.join(FIXTURES, "clean", "ids.txt"), os.path.join(work, "ids.txt"))
    code, output = run_tool("--decks", os.path.join(FIXTURES, "clean", "decks"),
                            "--out", os.path.join(work, "deck_data.cpp"), "--ids", os.path.join(work, "ids.txt"), *extra)
    return work, code, output


# ---------------------------------------------------------------------------------------------
# One test per fixture folder
# ---------------------------------------------------------------------------------------------

def check_case(name):
    dictionary, want_code, want_findings, want_notes = CASES[name]
    folder = os.path.join(FIXTURES, name)
    work = workspace("case-" + name)
    out = os.path.join(work, "deck_data.cpp")
    ids = os.path.join(work, "ids.txt")
    arguments = ["--decks", os.path.join(folder, "decks"), "--out", out, "--ids", ids]
    if os.path.exists(os.path.join(folder, "ids.txt")):
        shutil.copy(os.path.join(folder, "ids.txt"), ids)
    ids_before = read(ids) if os.path.exists(ids) else None
    arguments += ["--cache", FIXTURE_CACHE] if dictionary else ["--offline"]
    code, output = run_tool(*arguments)

    prefix = "tools/tests/fixtures/%s/" % name
    got = findings_of(output)
    left = list(got)
    for path, line, severity, words in want_findings:
        # the list of ids is read from the copy in the work folder
        shown = "build/test_build_decks/case-%s/ids.txt" % name if path == "ids.txt" else prefix + path
        hits = [f for f in left if f[0] == shown and f[1] == line and f[2] == severity and words in f[3]]
        expect(hits, "missing: %s:%d: %s: ...%s...\n%s" % (shown, line, severity, words, output))
        left.remove(hits[0])
    expect(not left, "findings that were not expected:\n      " + "\n      ".join("%s:%d: %s: %s" % f for f in left))

    notes = notes_of(output)
    for words in want_notes:
        expect(any(words in note for note in notes), "missing note: %s\n%s" % (words, output))
    same(any(OFFLINE_NOTE in note for note in notes), not dictionary, "the note about --offline")
    unexpected = [n for n in notes if OFFLINE_NOTE not in n and not any(words in n for words in want_notes)]
    expect(not unexpected, "notes that were not expected: %r" % unexpected)

    same(code, want_code, "exit code")
    errors = sum(1 for f in want_findings if f[2] == E)
    warnings = len(want_findings) - errors
    expect(re.search(r"^total: .*, %d errors?, %d warnings?$" % (errors, warnings), output, re.M),
           "the total line does not say %d errors, %d warnings:\n%s" % (errors, warnings, output))
    decks_dir = os.path.join(folder, "decks")
    for file_name in sorted(os.listdir(decks_dir)):
        if not file_name.endswith(".tsv"):
            continue
        mine = [f for f in want_findings if f[0] == "decks/" + file_name]
        deck_errors = sum(1 for f in mine if f[2] == E)
        expect(re.search(r"^%s: \d+ rows?, %d errors?, %d warnings?$"
                         % (re.escape(file_name[:-4]), deck_errors, len(mine) - deck_errors), output, re.M),
               "no summary line for %s with %d errors, %d warnings:\n%s"
               % (file_name, deck_errors, len(mine) - deck_errors, output))
    for file_name, word, unit in TABLES:
        mine = [f for f in want_findings if f[0] == file_name]
        table_errors = sum(1 for f in mine if f[2] == E)
        if os.path.exists(os.path.join(folder, file_name)):
            expect(re.search(r"^%s: \d+ %ss?, %d errors?, %d warnings?$"
                             % (word, unit, table_errors, len(mine) - table_errors), output, re.M),
                   "no summary line for %s with %d errors, %d warnings:\n%s"
                   % (file_name, table_errors, len(mine) - table_errors, output))
        else:
            expect(not re.search(r"^%s: " % word, output, re.M),
                   "a summary line for %s, which the fixture does not have:\n%s" % (file_name, output))

    if want_code == 0:
        expect(os.path.exists(out), "no errors, but the C++ file was not written")
        expect(os.path.exists(ids), "no errors, but the list of ids was not written")
    else:
        expect("nothing written" in output, "the output does not say that nothing was written")
        expect(not os.path.exists(out), "the C++ file was written in spite of errors")
        same(read(ids) if os.path.exists(ids) else None, ids_before, "the list of ids after a failed build")


def test_every_fixture_is_listed():
    folders = sorted(name for name in os.listdir(FIXTURES) if os.path.isdir(os.path.join(FIXTURES, name)))
    same(folders, sorted(list(CASES) + ["cache", "clean"]), "fixture folders and the list in this script")


# ---------------------------------------------------------------------------------------------
# The clean fixture
# ---------------------------------------------------------------------------------------------

def test_clean_builds():
    work, code, output = build_clean("clean", "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    same(findings_of(output), [], "findings")
    lines = output.splitlines()
    summary = ["hiragana: 4 rows, 0 errors, 0 warnings", "katakana: 2 rows, 0 errors, 0 warnings",
               "numbers: 3 rows, 0 errors, 0 warnings", "counters: 2 rows, 0 errors, 0 warnings",
               "katakana-words: 5 rows, 0 errors, 0 warnings", "signs: 8 rows, 0 errors, 0 warnings",
               "food: 3 rows, 0 errors, 0 warnings", "replies: 2 rows, 0 errors, 0 warnings",
               "buddy: 4 lines, 0 errors, 0 warnings", "kanji: 21 rows, 0 errors, 0 warnings",
               "parts: 2 rows, 0 errors, 0 warnings", "guide: 3 pages, 0 errors, 0 warnings"]
    same(lines[:len(summary)], summary, "summary lines")
    expect("total: 8 decks, 29 rows, 0 errors, 0 warnings" in lines, "total line\n" + output)
    expect("wrote build/test_build_decks/clean/deck_data.cpp: 8 decks, 29 items, 4 buddy lines, 3 guide pages"
           in lines, output)
    expect("wrote build/test_build_decks/clean/ids.txt: 29 ids, 26 new" in lines, output)

    notes = notes_of(output)
    filled = " ".join(n for n in notes if "filled in from the accent list" in n)
    same(sorted(re.findall(r"([a-z0-9-]+) (\d+)(?:,|$| )", filled.replace(" filled in from the accent list:", ""))),
         sorted((name, str(CLEAN_ACCENTS[name])) for name in CLEAN_FILLED), "accents reported as filled in")
    same([n for n in notes if "filled in from the accent list" not in n], [], "other notes")

    source = read(os.path.join(work, "deck_data.cpp"))
    expect(source.startswith("// Written by tools/build_decks.py"), "first line")
    head = source[:source.index("#include")]
    for words in ("Do not edit by hand", "JMdict", "KANJIDIC", "Electronic Dictionary Research and", "Kanjium",
                  "CC BY-SA 4.0"):
        expect(words in head, "the comment at the top does not mention: " + words)
    expect(all(line.startswith("//") for line in head.strip().split("\n")), "the top of the file is not all comment")
    same(re.findall(r'^    \{"([a-z-]+)", "[^"]*", "[^"]*", kItems_[a-z_]+, \d+, \d\},$', source, re.M), CLEAN_DECKS,
         "order of the decks")
    for wanted in (
            '    {"sign-deguchi", "出口", "でぐち", "", "exit (\\"way out\\")", "", "出 go out  口 opening", 1, 2, '
            'deck::Kind::Word},',
            '    {"sign-iriguchi", "入口", "いりぐち", "いりくち|はいりぐち", "entrance", "also written 入り口", '
            '"入 enter  口 opening", 0, 2, deck::Kind::Word},',
            '    {"sign-seisanki", "精算機", "せいさんき", "", "fare adjustment machine", "", '
            '"精 exact  算 calculate  機 machine", -1, 3, deck::Kind::Word},',
            # written in parts.tsv: not "交 alternate  番 number", which kanji.tsv would give
            '    {"sign-kouban", "交番", "こうばん", "", "police box", "", "交 take turns  番 watch", 0, 2, '
            'deck::Kind::Word},',
            # parts.tsv gives an empty line
            '    {"reply-daijoubu", "大丈夫", "だいじょうぶ", "", "all right; OK", "", "", 3, 2, deck::Kind::Word},',
            '    {"num-300-yen", "300円", "さんびゃくえん", "", "300 yen", "a typed \\\\ can show as ¥", "円 yen", -1, 2, '
            'deck::Kind::Number},',
            '    {"kana-a", "あ", "あ", "", "a", "", "", -1, 1, deck::Kind::Kana},',
            '    {"count-biiru-3", "ビール × 3", "さんぼん", "みっつ", "three beers", "bottles ほん, any thing つ", "", '
            '-1, 1, deck::Kind::Counter},',
            '    {"hiragana", "ひらがな", "hiragana", kItems_hiragana, 4, 1},',
            '    {"katakana-words", "カタカナご", "katakana words", kItems_katakana_words, 5, 3},',
            '    {"food", "たべもの", "food", kItems_food, 3, 1},',
            '    {"replies", "へんじ", "replies", kItems_replies, 2, 9},',
            '    {"buddy-start-02", "start", "じゅんびは いい？", "Are you ready?\\?"},',
            '    {"guide-vowels", "Five vowels", "a i u e o, always the same.\\nあ い う え お", "あ|い|う|え|お"},',
            '    {"guide-pitch", "Pitch", "Japanese has high and low\\nbeats, not loud and soft.", ""},',
            "extern const deck::Deck kDeckTable[] = {",
            "extern const size_t kDeckTableSize = sizeof(kDeckTable) / sizeof(kDeckTable[0]);",
            "extern const deck::BuddyLine kBuddyLines[] = {",
            "extern const size_t kBuddyLineCount = 4;",
            "extern const deck::GuidePage kGuidePages[] = {",
            "extern const size_t kGuidePageCount = 3;"):
        expect(wanted in source.split("\n"), "line not in the C++ file: " + wanted)
    source.encode("utf-8")
    expect("\t" not in source and "\r" not in source, "tabs or carriage returns in the C++ file")

    ids = [line for line in read(os.path.join(work, "ids.txt")).split("\n") if line and not line.startswith("#")]
    wanted = sorted(row[0] for name in CLEAN_DECKS
                    for row in table(os.path.join(FIXTURES, "clean", "decks", name + ".tsv")))
    same(ids, wanted, "the list of ids")
    same(len(ids), CLEAN_ITEMS, "number of ids")


def test_clean_builds_the_same_twice():
    work, code, output = build_clean("twice", "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code of the first build\n" + output)
    first = read(os.path.join(work, "deck_data.cpp")), read(os.path.join(work, "ids.txt"))
    code, output = run_tool("--decks", os.path.join(FIXTURES, "clean", "decks"),
                            "--out", os.path.join(work, "deck_data.cpp"), "--ids", os.path.join(work, "ids.txt"),
                            "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code of the second build\n" + output)
    expect("ids.txt: %d ids, 0 new" % CLEAN_ITEMS in output, "the second build found new ids:\n" + output)
    same((read(os.path.join(work, "deck_data.cpp")), read(os.path.join(work, "ids.txt"))), first, "the second build")


def test_check_writes_nothing():
    work = workspace("check")
    out = os.path.join(work, "deck_data.cpp")
    ids = os.path.join(work, "ids.txt")
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "clean", "decks"), "--out", out, "--ids", ids,
                            "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    expect("checked only, nothing written" in output, output)
    same(os.listdir(work), [], "files written by --check")
    # without --out and --ids the fixture's own list of ids is read, and still nothing is written
    before = read(os.path.join(FIXTURES, "clean", "ids.txt"))
    listing = sorted(os.listdir(os.path.join(FIXTURES, "clean")))
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "clean", "decks"), "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    same(read(os.path.join(FIXTURES, "clean", "ids.txt")), before, "the fixture's list of ids")
    same(sorted(os.listdir(os.path.join(FIXTURES, "clean"))), listing, "the fixture folder")


def test_offline_fills_in_nothing():
    work, code, output = build_clean("offline", "--offline")
    same(code, 0, "exit code\n" + output)
    same(findings_of(output), [], "findings")
    expect(any(OFFLINE_NOTE in note for note in notes_of(output)), "no note about --offline")
    expect(not any("filled in" in note and OFFLINE_NOTE not in note for note in notes_of(output)), output)
    source = read(os.path.join(work, "deck_data.cpp"))
    expect('    {"sign-deguchi", "出口", "でぐち", "", "exit (\\"way out\\")", "", "出 go out  口 opening", -1, 2, '
           'deck::Kind::Word},' in source, "offline, the accent of sign-deguchi must stay unknown")
    expect('    {"kata-hoteru", "ホテル", "ホテル", "", "hotel", "", "", 1, 1, deck::Kind::Word},' in source,
           "offline, an accent given by the deck is kept")
    # apart from the accents, the dictionaries change nothing of what is written
    online = read(os.path.join(build_clean("offline-compared", "--cache", FIXTURE_CACHE)[0], "deck_data.cpp"))
    accents = re.compile(r"-?\d+(, \d, deck::Kind::)")
    same([accents.sub(r"?\1", line) for line in source.split("\n")],
         [accents.sub(r"?\1", line) for line in online.split("\n")], "the C++ file without the accents")


def test_offline_checks_what_it_can_of_the_basis():
    """Without the dictionaries a basis is not looked up, but it still has to be there and to fit."""
    code, output = run_tool("--check", "--offline", "--decks", os.path.join(FIXTURES, "kanji-basis", "decks"))
    same(code, 1, "exit code\n" + output)
    shown = "tools/tests/fixtures/kanji-basis/kanji.tsv"
    same(findings_of(output), [
        (shown, 5, E, "basis is empty"),
        (shown, 8, E, "basis \"JMdict: 出口\" names a word without 交"),
    ], "findings")


def test_offline_needs_no_dictionary():
    work = workspace("no-dictionary")
    code, output = run_tool("--check", "--offline", "--decks", os.path.join(FIXTURES, "clean", "decks"),
                            "--cache", os.path.join(work, "nothing-here"))
    same(code, 0, "exit code\n" + output)
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "clean", "decks"),
                            "--cache", os.path.join(work, "nothing-here"))
    same(code, 2, "exit code without a dictionary and without --offline\n" + output)
    expect("jmdict_index.json not found" in output and "--offline" in output, output)


def real_cache():
    """Returns (whether local/cache holds JMdict and the accent list, whether it holds KANJIDIC)."""
    return (all(os.path.exists(os.path.join(REAL_CACHE, name)) for name in ("jmdict_index.json", "accents.txt")),
            os.path.exists(os.path.join(REAL_CACHE, "kanjidic_index.json")))


def test_real_dictionary_agrees_with_the_excerpt():
    dictionary, kanjidic = real_cache()
    if not dictionary:
        return "SKIPPED: local/cache holds no dictionary"
    excerpt, code, output = build_clean("excerpt", "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code with the excerpt\n" + output)
    real, code, real_output = build_clean("real", "--cache", REAL_CACHE)
    same(code, 0, "exit code with the real dictionary\n" + real_output)
    same(read(os.path.join(real, "deck_data.cpp")), read(os.path.join(excerpt, "deck_data.cpp")), "the C++ file")
    same([n for n in notes_of(real_output) if kanjidic or KANJIDIC_NOTE not in n], notes_of(output), "notes")
    # and the mistakes are found in the real dictionary too
    left_out = []
    for name in sorted(CASES):
        if CASES[name][0]:
            if not kanjidic and os.path.exists(os.path.join(FIXTURES, name, KANJI)):
                left_out.append(name)
                continue
            decks = os.path.join(FIXTURES, name, "decks")
            code, real_output = run_tool("--check", "--decks", decks, "--cache", REAL_CACHE)
            _, output = run_tool("--check", "--decks", decks, "--cache", FIXTURE_CACHE)
            same(real_output, output, "output for %s with the real dictionary" % name)
    if left_out:
        return "local/cache holds no KANJIDIC: %s left out" % ", ".join(left_out)
    return None


def test_excerpt_is_a_true_copy():
    """Every entry of the excerpt is in the real files, word for word."""
    import json
    real_index = os.path.join(REAL_CACHE, "jmdict_index.json")
    real_accents = os.path.join(REAL_CACHE, "accents.txt")
    real_kanji = os.path.join(REAL_CACHE, "kanjidic_index.json")
    dictionary, kanjidic = real_cache()
    if not dictionary:
        return "SKIPPED: local/cache holds no dictionary"
    with open(os.path.join(FIXTURE_CACHE, "kanjidic_index.json"), encoding="utf-8") as handle:
        excerpt = json.load(handle)
    expect(excerpt, "the excerpt of KANJIDIC is empty")
    if kanjidic:
        with open(real_kanji, encoding="utf-8") as handle:
            index = json.load(handle)
        for kanji, entry in excerpt.items():
            same(entry, index.get(kanji), "KANJIDIC entry for " + kanji)
    with open(real_index, encoding="utf-8") as handle:
        index = json.load(handle)
    with open(os.path.join(FIXTURE_CACHE, "jmdict_index.json"), encoding="utf-8") as handle:
        excerpt = json.load(handle)
    expect(excerpt, "the excerpt is empty")
    for word, entries in excerpt.items():
        same(entries, index.get(word), "JMdict entry for " + word)
    lines = set(read(real_accents).split("\n"))
    words = set()
    copied = read(os.path.join(FIXTURE_CACHE, "accents.txt")).split("\n")
    for line in copied:
        if line:
            expect(line in lines, "accent line not in the real list: " + line)
            words.add(line.split("\t")[0])
    # no line of a word was left out, which would hide a second accent
    for line in lines:
        if line.split("\t")[0] in words:
            expect(line in copied, "accent line left out: " + line)
    if not kanjidic:
        return "local/cache holds no KANJIDIC: that excerpt was not compared"
    return None


KIPPU = '    {"sign-kippu", "切符", "きっぷ", "", "ticket", "", "%s", 0, 2, deck::Kind::Word},'


def test_without_the_tables_beside_the_decks():
    """A deck folder alone builds: no buddy, no guide, no line about the kanji, stage 1."""
    work = workspace("decks-alone")
    out = os.path.join(work, "deck_data.cpp")
    code, output = run_tool("--decks", os.path.join(FIXTURES, "first-build", "decks"), "--out", out,
                            "--ids", os.path.join(work, "ids.txt"), "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    same(findings_of(output), [], "findings")
    same(notes_of(output), [], "notes")
    for _, word, _ in TABLES:
        expect(not any(line.startswith(word + ":") for line in output.splitlines()),
               "a summary line for %s without such a file" % word)
    source = read(out).split("\n")
    for wanted in (KIPPU % "",
                   '    {"signs", "かんばん", "signs", kItems_signs, 1, 1},',
                   "extern const deck::BuddyLine kBuddyLines[] = {",
                   "extern const size_t kBuddyLineCount = 0;",
                   "extern const deck::GuidePage kGuidePages[] = {",
                   "extern const size_t kGuidePageCount = 0;"):
        expect(wanted in source, "line not in the C++ file: " + wanted)
    expect("ids.txt: 1 id, 1 new" in output, output)
    expect("deck_data.cpp: 1 deck, 1 item, 0 buddy lines, 0 guide pages" in output, output)


def test_tables_named_by_an_option():
    """--buddy, --kanji, --parts and --guide name a file elsewhere."""
    work = workspace("options")
    out = os.path.join(work, "deck_data.cpp")
    write(os.path.join(work, "elsewhere", "meanings.tsv"),
          "kanji\tmeaning\tbasis\twords\n切\tcut\tcut\t切符\n符\ttoken\ttoken\t切符\n")
    write(os.path.join(work, "elsewhere", "by-hand.tsv"),
          "prompt\tparts\treason\n切符\t切 cut  符 token, a slip of paper\tthe token is of paper\n")
    write(os.path.join(work, "elsewhere", "pages.tsv"),
          "id\ttitle\tbody\tclips\nguide-tsu\tThe small っ\tきっぷ has three beats.\tきっぷ\n")
    options = {
        "--buddy": os.path.join(FIXTURES, "clean", "buddy.tsv"),
        "--kanji": os.path.join(work, "elsewhere", "meanings.tsv"),
        "--parts": os.path.join(work, "elsewhere", "by-hand.tsv"),
        "--guide": os.path.join(work, "elsewhere", "pages.tsv"),
    }

    def build(*names):
        arguments = [part for name in names for part in (name, options[name])]
        code, output = run_tool("--decks", os.path.join(FIXTURES, "first-build", "decks"), "--out", out,
                                "--ids", os.path.join(work, "ids.txt"), "--cache", FIXTURE_CACHE, *arguments)
        same(code, 0, "exit code with %s\n%s" % (" ".join(names), output))
        same(findings_of(output), [], "findings with " + " ".join(names))
        for option, (_, word, _) in zip(("--buddy", "--kanji", "--parts", "--guide"), TABLES):
            same(any(line.startswith(word + ":") for line in output.splitlines()), option in names,
                 "whether there is a summary line for %s with %s" % (word, " ".join(names)))
        return read(out).split("\n")

    source = build("--buddy")
    expect("extern const size_t kBuddyLineCount = 4;" in source, "kBuddyLineCount is not 4 with --buddy")
    expect(KIPPU % "" in source, "a line about the kanji without --kanji")
    source = build("--kanji")
    expect(KIPPU % "切 cut  符 token" in source, "the line about the kanji with --kanji")
    # the line written by hand needs no kanji.tsv, and wins over it
    source = build("--parts")
    expect(KIPPU % "切 cut  符 token, a slip of paper" in source, "the line about the kanji with --parts")
    source = build("--kanji", "--parts")
    expect(KIPPU % "切 cut  符 token, a slip of paper" in source, "the line about the kanji with --kanji and --parts")
    source = build("--guide")
    expect("extern const size_t kGuidePageCount = 1;" in source, "kGuidePageCount is not 1 with --guide")
    expect('    {"guide-tsu", "The small っ", "きっぷ has three beats.", "きっぷ"},' in source, "the page of the guide")
    # a table may be absent, but not one that is named
    for option in options:
        code, output = run_tool("--check", "--offline", "--decks", os.path.join(FIXTURES, "first-build", "decks"),
                                option, os.path.join(work, "elsewhere", "nothing.tsv"))
        same(code, 2, "exit code with %s and no such file\n%s" % (option, output))
        expect("build/test_build_decks/options/elsewhere/nothing.tsv not found" in output, output)


def test_without_kanjidic():
    """Where KANJIDIC is not at hand, a note says so, and what is written stays the same."""
    import json
    work = workspace("no-kanjidic")
    cache = os.path.join(work, "cache")
    os.makedirs(cache)
    for name in ("jmdict_index.json", "accents.txt"):
        shutil.copy(os.path.join(FIXTURE_CACHE, name), os.path.join(cache, name))
    decks = os.path.join(FIXTURES, "clean", "decks")
    arguments = ["--decks", decks, "--out", os.path.join(work, "deck_data.cpp"), "--ids", os.path.join(work, "ids.txt")]
    code, output = run_tool("--cache", cache, *arguments)
    same(code, 0, "exit code\n" + output)
    same(findings_of(output), [], "findings")
    same([n for n in notes_of(output) if KANJIDIC_NOTE in n],
         ["tools/tests/fixtures/clean/kanji.tsv was not compared with KANJIDIC: "
          "build/test_build_decks/no-kanjidic/cache/kanjidic_index.json not found"], "the note about KANJIDIC")
    full, code, _ = build_clean("with-kanjidic", "--cache", FIXTURE_CACHE)
    same(read(os.path.join(work, "deck_data.cpp")), read(os.path.join(full, "deck_data.cpp")), "the C++ file")
    # no note where there is no kanji.tsv to compare
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "first-build", "decks"), "--cache", cache)
    same((code, notes_of(output)), (0, []), "exit code and notes without kanji.tsv\n" + output)
    # the mistakes that need KANJIDIC are not found then, the others are
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "kanji-basis", "decks"), "--cache", cache)
    same(code, 1, "exit code for kanji-basis\n" + output)
    same([f[1] for f in findings_of(output)], [5, 8, 12], "lines of the findings for kanji-basis")
    # a file that is there and cannot be read stops the tool
    for text in ("{", "[]", json.dumps({"口": ["mouth"]})):
        write(os.path.join(cache, "kanjidic_index.json"), text)
        code, output = run_tool("--check", "--decks", decks, "--cache", cache)
        same(code, 2, "exit code with a KANJIDIC file that holds %s\n%s" % (text, output))
        expect("kanjidic_index.json cannot be read" in output and "Traceback" not in output, output)


def test_a_deck_that_cannot_be_read_is_reported_once():
    """The tables beside the decks are then not compared with the decks: every row would be a finding."""
    work = workspace("deck-unread")
    for name in (KANJI, PARTS):
        shutil.copy(os.path.join(FIXTURES, "clean", name), os.path.join(work, name))
    shown = "build/test_build_decks/deck-unread/decks/signs.tsv"
    good = read(os.path.join(FIXTURES, "clean", "decks", "signs.tsv"))
    for text, line, words in ((good.replace("\tprompt\t", "\tword\t"), 6, "header row must be"),
                              (good.replace("\t出口\t", "\t出口\t\t"), 7, "10 columns, expected 9"),
                              ("", 1, "the file is empty")):
        write(os.path.join(work, "decks", "signs.tsv"), text)
        code, output = run_tool("--check", "--offline", "--decks", os.path.join(work, "decks"))
        same(code, 1, "exit code\n" + output)
        found = findings_of(output)
        same([f[:3] for f in found], [(shown, line, E)], "findings\n" + output)
        expect(words in found[0][3], output)
    # and with the deck as it should be, the tables are compared with it: most of their rows are of other decks
    write(os.path.join(work, "decks", "signs.tsv"), good)
    code, output = run_tool("--check", "--offline", "--decks", os.path.join(work, "decks"))
    same(code, 1, "exit code with the deck as it should be\n" + output)
    same([f[3] for f in findings_of(output) if f[2] == E], ["大丈夫 is not a prompt of a deck"], "errors")
    same(len([f for f in findings_of(output) if "the row is not used" in f[3]]), 7, "rows that are not used")


def test_fixture_folder_is_never_the_default_target():
    code, output = run_tool("--decks", os.path.join(FIXTURES, "clean", "decks"), "--offline")
    same(code, 2, "exit code without --out and --ids\n" + output)
    expect("--out and --ids" in output, output)


def test_not_utf8():
    work = workspace("not-utf8")
    good = read(os.path.join(FIXTURES, "first-build", "decks", "signs.tsv")).encode("utf-8")
    write(os.path.join(work, "decks", "signs.tsv"), good.replace("きっぷ".encode("utf-8"), "きっぷ".encode("shift_jis")))
    code, output = run_tool("--check", "--offline", "--decks", os.path.join(work, "decks"))
    same(code, 1, "exit code\n" + output)
    found = findings_of(output)
    same(len(found), 1, "number of findings\n" + output)
    same(found[0][:3], ("build/test_build_decks/not-utf8/decks/signs.tsv", 6, E), "where the finding is")
    expect("not UTF-8" in found[0][3], output)


def test_windows_line_ends_and_byte_order_mark():
    """In the decks and in every table beside them."""
    work = workspace("crlf")
    names = ["decks/katakana.tsv", "decks/signs.tsv", "decks/replies.tsv", BUDDY, KANJI, PARTS, GUIDE]
    for name in names:
        text = read(os.path.join(FIXTURES, "clean", name))
        if name == KANJI:
            # only the kanji of these three decks
            text = "".join(line + "\n" for line in text.split("\n") if line and line[0] not in "円時水茶飯")
        write(os.path.join(work, name), "\ufeff" + text.replace("\n", "\r\n"))
    out = os.path.join(work, "deck_data.cpp")
    code, output = run_tool("--decks", os.path.join(work, "decks"), "--out", out,
                            "--ids", os.path.join(work, "ids.txt"), "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    same(sorted(f[:3] + (f[3].split(";")[0],) for f in findings_of(output)),
         sorted(("build/test_build_decks/crlf/" + name, 1, W, words) for name in names
                for words in ("byte order mark at the start of the file", "the line ends with a carriage return")),
         "findings")
    source = read(out)
    expect("\r" not in source and "\ufeff" not in source, "carriage return or byte order mark in the C++ file")
    for wanted in (
            '    {"kana-kata-shi", "シ", "シ", "", "shi", "not ツ (tsu)", "", -1, 1, deck::Kind::Kana},',
            '    {"sign-kippu", "切符", "きっぷ", "", "ticket", "", "切 cut  符 token", 0, 2, deck::Kind::Word},',
            '    {"sign-kouban", "交番", "こうばん", "", "police box", "", "交 take turns  番 watch", 0, 2, '
            'deck::Kind::Word},',
            '    {"katakana", "カタカナ", "katakana", kItems_katakana, 2, 2},',
            '    {"replies", "へんじ", "replies", kItems_replies, 2, 9},',
            '    {"buddy-right-01", "right", "せいかい！", "Correct!"},',
            '    {"guide-pitch", "Pitch", "Japanese has high and low\\nbeats, not loud and soft.", ""},'):
        expect(wanted in source.split("\n"), "line not in the C++ file: %s\n%s" % (wanted, source))


def test_old_line_ends():
    """A carriage return alone ends a line too."""
    work = workspace("cr")
    text = read(os.path.join(FIXTURES, "first-build", "decks", "signs.tsv"))
    write(os.path.join(work, "decks", "signs.tsv"), text.replace("\n", "\r"))
    out = os.path.join(work, "deck_data.cpp")
    code, output = run_tool("--decks", os.path.join(work, "decks"), "--out", out,
                            "--ids", os.path.join(work, "ids.txt"), "--offline")
    same(code, 0, "exit code\n" + output)
    same([f[:3] for f in findings_of(output)], [("build/test_build_decks/cr/decks/signs.tsv", 1, W)], "findings")
    expect(KIPPU % "" in read(out).split("\n"), read(out))


def test_invisible_characters():
    """They are named, the finding stays on one line, and nothing is written."""
    work = workspace("invisible")
    text = read(os.path.join(FIXTURES, "first-build", "decks", "signs.tsv"))
    text = text.replace("# kind", "\ufeff# kind").replace("ticket", "tic\u200bket\x00")
    text += "sign-deguchi\t出口\tでぐち\t\t\texit\tway\u3000out\u00a0\u2028here\t2\tJMdict\n"
    write(os.path.join(work, "decks", "signs.tsv"), text)
    out = os.path.join(work, "deck_data.cpp")
    code, output = run_tool("--decks", os.path.join(work, "decks"), "--out", out,
                            "--ids", os.path.join(work, "ids.txt"), "--offline")
    same(code, 1, "exit code\n" + output)
    expect(not os.path.exists(out), "the C++ file was written in spite of errors")
    shown = "build/test_build_decks/invisible/decks/signs.tsv"
    same(findings_of(output), [
        (shown, 4, E, "invisible character U+FEFF; remove it"),
        (shown, 6, E, "invisible character U+200B U+0000; remove it"),
        (shown, 7, E, "invisible character U+2028; remove it"),
        (shown, 7, E, "note: no glyph for U+00A0 in efontJA_16, U+00A0 in efontJA_12"),
    ], "findings")
    for line in output.splitlines():
        expect(re.match(r"(\S+:\d+: (error|warning): |signs: |note: |total: |nothing written$)", line),
               "a line that is no finding: %r" % line)
        expect(build_decks.printable(line) == line, "a character that cannot be seen in: %r" % line)


def test_file_that_cannot_be_read():
    work = workspace("unreadable")
    shutil.copytree(os.path.join(FIXTURES, "first-build", "decks"), os.path.join(work, "decks"))
    os.makedirs(os.path.join(work, "decks", "folder.tsv"))
    os.makedirs(os.path.join(work, "ids.txt"))
    code, output = run_tool("--check", "--offline", "--decks", os.path.join(work, "decks"))
    same(code, 1, "exit code\n" + output)
    same(findings_of(output), [
        ("build/test_build_decks/unreadable/decks/folder.tsv", 1, E, "cannot be read: Is a directory"),
        ("build/test_build_decks/unreadable/ids.txt", 1, E, "cannot be read: Is a directory"),
    ], "findings")
    # what cannot be written stops the tool, with a message and without a trace
    code, output = run_tool("--offline", "--decks", os.path.join(FIXTURES, "first-build", "decks"),
                            "--out", os.path.join(work, "decks"), "--ids", os.path.join(work, "new-ids.txt"))
    same(code, 2, "exit code\n" + output)
    expect("cannot be written" in output and "Traceback" not in output, output)
    expect(not os.path.exists(os.path.join(work, "new-ids.txt")), "the list of ids was written")


def test_dictionary_that_cannot_be_read():
    work = workspace("bad-dictionary")
    write(os.path.join(work, "jmdict_index.json"), "{")
    write(os.path.join(work, "accents.txt"), "")
    code, output = run_tool("--check", "--decks", os.path.join(FIXTURES, "first-build", "decks"), "--cache", work)
    same(code, 2, "exit code\n" + output)
    expect("cannot be read" in output and "Traceback" not in output, output)


def test_ids_are_kept_when_a_deck_grows():
    """An id that was published stays in the list, and a new one is added to it."""
    work = workspace("grows")
    decks = os.path.join(work, "decks")
    shutil.copytree(os.path.join(FIXTURES, "first-build", "decks"), decks)
    arguments = ["--decks", decks, "--out", os.path.join(work, "deck_data.cpp"), "--ids", os.path.join(work, "ids.txt"),
                 "--offline"]
    code, output = run_tool(*arguments)
    same(code, 0, "exit code of the first build\n" + output)
    with open(os.path.join(decks, "signs.tsv"), "a", encoding="utf-8", newline="") as handle:
        handle.write("sign-deguchi\t出口\tでぐち\t\t\texit\t\t2\tJMdict\n")
    code, output = run_tool(*arguments)
    same(code, 0, "exit code of the second build\n" + output)
    expect("ids.txt: 2 ids, 1 new" in output, output)
    # the first item is renamed: its old id has disappeared
    text = read(os.path.join(decks, "signs.tsv")).replace("sign-kippu\t", "sign-ticket\t")
    write(os.path.join(decks, "signs.tsv"), text)
    before = read(os.path.join(work, "ids.txt"))
    code, output = run_tool(*arguments)
    same(code, 1, "exit code after renaming an id\n" + output)
    expect("id sign-kippu was published and has disappeared" in output, output)
    same(read(os.path.join(work, "ids.txt")), before, "the list of ids after the failed build")


# ---------------------------------------------------------------------------------------------
# The parts, called directly
# ---------------------------------------------------------------------------------------------

def test_typing_romaji():
    wanted = {
        "きんえん": "kin'en", "ほんや": "hon'ya", "しんばし": "shinbashi", "こんにちは": "konnichiha",
        "あんない": "annai", "さんねん": "sannen", "きっぷ": "kippu", "まっちゃ": "matcha", "ざっし": "zasshi",
        "いっち": "itchi", "らーめん": "ra-men", "コーヒー": "ko-hi-", "とうきょう": "toukyou",
        "つづく": "tsuduku", "はなぢ": "hanadi", "を": "wo", "パーティー": "pa-thi-", "ファミレス": "famiresu",
        "ウィスキー": "wisuki-", "チェック": "chekku", "ジェット": "jetto", "じゃ": "ja", "しゃしん": "shashin",
        "ぎゅうにゅう": "gyuunyuu", "あっ": "axtsu", "んん": "n'n", "ヴ": "vu", "んっや": "n'yya",
        "せんえん": "sen'en", "かく": "kaku", "こころ": "kokoro", "カフェ": "kafe", "っま": "xtsuma",
    }
    for kana, romaji in wanted.items():
        got, problem = build_decks.typing_romaji(kana)
        same((got, problem), (romaji, None), "romaji for " + kana)
        typed, pending = romaji_reference.convert(romaji, flush=True)
        same((typed, pending), (build_decks.to_hiragana(kana), ""), "what %s types" % romaji)
    for kana in ("こゝろ", "ヷ", "いすゞ"):
        got, problem = build_decks.typing_romaji(kana)
        expect(problem and "cannot be typed" in problem, "%s should not be typable, got %r" % (kana, got))


def test_romaji_is_typed_back_and_compared():
    """With the spelling the device shows for づ, the check has to notice that another kana comes out."""
    right = build_decks.SPELLINGS["づ"]
    same(right, "du", "spelling of づ")
    build_decks.SPELLINGS["づ"] = "zu"
    try:
        same(build_decks.typing_romaji("つづく"), ("tsuzuku", "tsuzuku types つずく"), "つづく typed as tsuzuku")
    finally:
        build_decks.SPELLINGS["づ"] = right
    same(build_decks.typing_romaji("つづく"), ("tsuduku", None), "つづく typed as tsuduku")


def test_everything_the_converter_makes_can_be_typed():
    """Every kana the converter's table can produce, alone and next to っ, ん and ー."""
    syllables = sorted(set(romaji_reference.TABLE.values()))
    expect(len(syllables) > 150, "the converter's table was not read")
    count = 0
    for syllable in syllables:
        for before in ("", "っ", "ん", "あ", "っっ", "んっ"):
            for after in ("", "ー", "ん", "っ", "あ", "や", "な", "ま"):
                kana = before + syllable + after
                romaji, problem = build_decks.typing_romaji(kana)
                expect(problem is None, "%s: %s" % (kana, problem))
                expect(re.fullmatch(r"[a-z'-]+", romaji), "%s: romaji %r" % (kana, romaji))
                count += 1
    return "%d kana strings" % count


def test_beats():
    for kana, beats in {"でぐち": 3, "きゃく": 2, "きっぷ": 3, "コーヒー": 4, "ん": 1, "しんかんせん": 6,
                        "パーティー": 4, "ひじょうぐち": 5, "ゃ": 1}.items():
        same(build_decks.beat_count(kana), beats, "beats of " + kana)


def test_spellings_are_the_textbook_ones():
    """As romaji::spelling chooses them: a shortcut that starts with c, q, x or l only where there is no other."""
    for kana, romaji in {"し": "shi", "ち": "chi", "つ": "tsu", "ふ": "fu", "じ": "ji", "せ": "se", "か": "ka",
                         "く": "ku", "こ": "ko", "しゃ": "sha", "ちぇ": "che", "じょ": "jo", "ぢ": "di", "づ": "du",
                         "てぃ": "thi", "ふぁ": "fa", "うぃ": "wi", "を": "wo"}.items():
        same(build_decks.SPELLINGS[kana], romaji, "spelling of " + kana)
    for kana, romaji in build_decks.SPELLINGS.items():
        same(romaji_reference.convert(romaji, flush=True), (kana, ""), "what %s types" % romaji)


def test_key_is_fnv1a():
    same(build_decks.fnv1a(""), 0x811C9DC5, "key of the empty string")
    same(build_decks.fnv1a("a"), 0xE40C292C, "key of a")
    same(build_decks.fnv1a("foobar"), 0xBF9CF968, "key of foobar")
    same(build_decks.fnv1a("clash-9utp4"), build_decks.fnv1a("clash-oc4zgvo"), "the two ids of id-key-clash")


def test_string_literals():
    same(build_decks.literal('a "b" c'), '"a \\"b\\" c"', "double quotes")
    same(build_decks.literal("a\\b"), '"a\\\\b"', "backslash")
    same(build_decks.literal("\\300"), '"\\\\300"', "backslash before digits")
    same(build_decks.literal("出口"), '"出口"', "UTF-8")
    same(build_decks.literal("what???"), '"what?\\?\\?"', "question marks")


def test_columns_and_kanji():
    same(build_decks.columns("exit"), 4, "columns of exit")
    same(build_decks.columns("でぐち"), 6, "columns of でぐち")
    same(build_decks.columns("also written 入り口"), 19, "columns of a mixed note")
    for ch in "出口々𠮟":
        expect(build_decks.is_kanji(ch), ch + " is kanji")
    for ch in "でグーa1 ×":
        expect(not build_decks.is_kanji(ch), ch + " is not kanji")
    for ch in "あんゔァヶーゝ":
        expect(build_decks.is_kana(ch), ch + " is kana")
    for ch in "出a 、。！":
        expect(not build_decks.is_kana(ch), ch + " is not kana")


def test_moods_are_the_documented_ten():
    same(len(build_decks.MOODS), 10, "number of moods")
    for path in (os.path.join(TESTS, "README.md"), os.path.join(ROOT, "content", "README.md")):
        documented = re.search(r"^Moods: (.*)$", read(path), re.M)
        expect(documented, "%s has no line starting with \"Moods: \"" % build_decks.display(path))
        same([m.strip(" `.") for m in documented.group(1).split(",")], build_decks.MOODS,
             "moods in " + build_decks.display(path))


def test_readme_describes_every_table():
    """content/README.md has a section for each table, with a row for each column and the limits the tool keeps."""
    text = read(os.path.join(ROOT, "content", "README.md"))
    sections = dict((part.split("\n", 1)[0].strip(), part) for part in text.split("\n## ")[1:])
    tables = {
        "Deck files": (build_decks.COLUMNS, [build_decks.GLOSS_COLUMNS, build_decks.NOTE_COLUMNS]),
        "buddy.tsv": (build_decks.BUDDY_COLUMNS, [build_decks.BUDDY_JA_LENGTH, build_decks.BUDDY_EN_LENGTH]),
        "kanji.tsv": (build_decks.KANJI_COLUMNS, [build_decks.KANJI_MEANING_LENGTH, build_decks.PARTS_COLUMNS]),
        "parts.tsv": (build_decks.PARTS_FILE_COLUMNS, [build_decks.PARTS_COLUMNS]),
        "guide.tsv": (build_decks.GUIDE_COLUMNS, [build_decks.GUIDE_TITLE_COLUMNS, build_decks.GUIDE_LINES,
                                                  build_decks.GUIDE_LINE_COLUMNS]),
    }
    for title, (columns, limits) in tables.items():
        expect(title in sections, "content/README.md has no section \"%s\"" % title)
        rows = re.findall(r"^\| `([a-z-]+)` \|", sections[title], re.M)
        names = ["name-ja", "name-en", "kind", "stage"] if title == "Deck files" else []
        same(rows, names + columns, "the rows of the tables in the section \"%s\"" % title)
        for limit in limits:
            expect(re.search(r"at most %d\b" % limit, sections[title]),
                   "the section \"%s\" does not say: at most %d" % (title, limit))
    for kind in build_decks.KINDS:
        expect("`%s`" % kind in sections["Deck files"], "the section on deck files does not name the kind " + kind)
    expect(", ".join(build_decks.DECK_ORDER) in " ".join(sections["Deck files"].split()),
           "the section on deck files does not give the order of the decks")
    for words in ("JMdict", "KANJIDIC", "Electronic Dictionary Research and Development", "Kanjium", "CC BY-SA 4.0"):
        expect(words in " ".join(sections["Licences"].split()), "the licences do not mention: " + words)


# ---------------------------------------------------------------------------------------------
# The C++
# ---------------------------------------------------------------------------------------------

def emscripten():
    """Returns (environment, None) or (None, why not)."""
    if not shutil.which("em++"):
        return None, "Emscripten (em++) is not installed"
    if not shutil.which("node"):
        return None, "Node is not installed"
    import wasm_tests  # sets EMSDK_PYTHON where Emscripten needs a newer Python than the system's
    return wasm_tests.environment(), None


def compiler(arguments, env):
    result = subprocess.run(["em++"] + arguments, env=env, capture_output=True, text=True)
    noise = ("cache:INFO", "system_libs:INFO", "ports:INFO", "shared:INFO")
    text = "\n".join(line for line in (result.stdout + result.stderr).splitlines() if not line.startswith(noise))
    return result.returncode, text


def test_cpp_is_valid():
    env, why = emscripten()
    if env is None:
        return "SKIPPED: " + why
    include = "-I" + os.path.join(ROOT, "lib", "core")
    checked = 0
    for name, extra in (("clean", ["--cache", FIXTURE_CACHE]), ("offline", ["--offline"])):
        work, code, output = build_clean("cpp-" + name, *extra)
        same(code, 0, "exit code\n" + output)
        for standard in ("gnu++17", "c++11"):
            code, text = compiler(["-std=" + standard, "-fsyntax-only", "-Wall", "-Wextra", "-Wtrigraphs", "-Werror",
                                   include, os.path.join(work, "deck_data.cpp")], env)
            same((code, text), (0, ""), "em++ -std=%s -fsyntax-only on the %s build" % (standard, name))
            checked += 1
    # without buddy and guide the two arrays hold one empty entry, and with warnings the file is written too
    for name in ("first-build", "kanji-no-row", "kanji-line-wide"):
        work = workspace("cpp-" + name)
        out = os.path.join(work, "deck_data.cpp")
        code, output = run_tool("--decks", os.path.join(FIXTURES, name, "decks"), "--out", out,
                                "--ids", os.path.join(work, "ids.txt"), "--offline")
        same(code, 0, "exit code\n" + output)
        for standard in ("gnu++17", "c++11"):
            code, text = compiler(["-std=" + standard, "-fsyntax-only", "-Wall", "-Wextra", "-Wtrigraphs",
                                   "-Werror", include, out], env)
            same((code, text), (0, ""), "em++ -std=%s -fsyntax-only on the build of %s" % (standard, name))
            checked += 1
    # the file must define what lib/core/deck.cpp asks for
    asked = re.findall(r"^extern const ([^;]+);$", read(os.path.join(ROOT, "lib", "core", "deck.cpp")), re.M)
    expect(len(asked) >= 4, "lib/core/deck.cpp no longer names what it takes from deck_data.cpp")
    for name in asked:
        expect("extern const %s = " % name in read(out), "deck_data.cpp does not define: " + name)
    # the compiler does find a mistake in such a file
    broken = os.path.join(work, "broken.cpp")
    write(broken, read(out).replace("deck::Kind::Word}", "deck::Kind::Verb}"))
    code, text = compiler(["-std=gnu++17", "-fsyntax-only", include, broken], env)
    expect(code != 0 and "Verb" in text, "the compiler accepted a file with a mistake:\n" + text)
    return "%d files checked" % checked


def test_cpp_holds_what_the_decks_say():
    """Compiles the output with lib/core/deck.cpp, runs it under Node and compares every field."""
    env, why = emscripten()
    if env is None:
        return "SKIPPED: " + why
    work, code, output = build_clean("cpp-run", "--cache", FIXTURE_CACHE)
    same(code, 0, "exit code\n" + output)
    write(os.path.join(work, "dump.cpp"), DUMP)
    program = os.path.join(work, "dump.js")
    code, text = compiler(["-std=gnu++17", "-O0", "-Wall", "-Wextra", "-I" + os.path.join(ROOT, "lib", "core"),
                           os.path.join(work, "dump.cpp"), os.path.join(work, "deck_data.cpp"),
                           os.path.join(ROOT, "lib", "core", "deck.cpp"), "-o", program], env)
    same((code, text), (0, ""), "compiling the dump program")
    result = subprocess.run(["node", program], env=env, capture_output=True)
    same(result.returncode, 0, "exit code of the dump program: " + result.stderr.decode("utf-8", "replace"))
    got = result.stdout.decode("utf-8").split("\n")

    want = []
    items = 0
    with_parts = []
    for name in CLEAN_DECKS:
        path = os.path.join(FIXTURES, "clean", "decks", name + ".tsv")
        names = dict(re.findall(r"^# (name-ja|name-en|kind|stage): (.*)$", read(path), re.M))
        rows = table(path)
        same(int(names.get("stage", 1)), CLEAN_STAGES[name], "stage of %s in the fixture and in this script" % name)
        want.append("deck\t%s\t%s\t%s\t%d\t%d\tfound" % (name, names["name-ja"], names["name-en"], len(rows),
                                                         CLEAN_STAGES[name]))
        for row in rows:
            accent = CLEAN_ACCENTS.get(row[0], -1)
            if row[3]:
                same(int(row[3]), accent, "accent of %s in the fixture and in this script" % row[0])
            else:
                same(row[0] in CLEAN_FILLED, accent >= 0, "whether %s is filled in" % row[0])
            if row[0] in CLEAN_PARTS:
                with_parts.append(row[0])
            want.append("item\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%d\t%08x\tfound" % (
                row[0], row[1], row[2], row[4], row[5], row[6], CLEAN_PARTS.get(row[0], ""), accent, row[7],
                KIND_NUMBER[names["kind"]], build_decks.fnv1a(row[0])))
            items += 1
    same(sorted(with_parts), sorted(CLEAN_PARTS), "the items that have a line about their kanji")
    buddy = table(os.path.join(FIXTURES, "clean", BUDDY))
    for row in buddy:
        want.append("buddy\t" + "\t".join(row))
    guide = table(os.path.join(FIXTURES, "clean", GUIDE))
    for row in guide:
        want.append("guide\t" + "\t".join(row))
    want += ["end\t%d\t%d\t%d" % (len(CLEAN_DECKS), len(buddy), len(guide)), ""]
    same(len(got), len(want), "number of lines printed")
    for got_line, want_line in zip(got, want):
        same(got_line, want_line, "line printed by the compiled tables")
    return "%d decks, %d items, %d buddy lines, %d pages of the guide read back" % (len(CLEAN_DECKS), items,
                                                                                   len(buddy), len(guide))


# ---------------------------------------------------------------------------------------------

def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow_skips = "--allow-skips" in sys.argv[1:]
    tests = [("fixture " + name, lambda name=name: check_case(name)) for name in sorted(CASES)]
    tests += [(name[len("test_"):].replace("_", " "), function) for name, function in sorted(globals().items())
              if name.startswith("test_") and callable(function)]
    if arguments:
        tests = [t for t in tests if any(word in t[0] for word in arguments)]
    if not tests:
        sys.exit("no test matches " + " ".join(arguments))

    os.makedirs(WORK, exist_ok=True)
    failed = []
    skipped = []
    for name, function in tests:
        try:
            remark = function()
        except Failure as failure:
            failed.append(name)
            print("FAIL  %s\n      %s" % (name, failure))
            continue
        if remark and remark.startswith("SKIPPED"):
            skipped.append(name)
            print("skip  %s (%s)" % (name, remark[len("SKIPPED: "):]))
        else:
            print("ok    %s%s" % (name, " (%s)" % remark if remark else ""))

    print("%d test%s: %d passed, %d failed, %d skipped" % (len(tests), "" if len(tests) == 1 else "s",
                                                           len(tests) - len(failed) - len(skipped), len(failed),
                                                           len(skipped)))
    if failed:
        sys.exit("FAILED: " + ", ".join(failed))
    if skipped and not allow_skips:
        sys.exit("INCOMPLETE: skipped " + ", ".join(skipped))


if __name__ == "__main__":
    main()
