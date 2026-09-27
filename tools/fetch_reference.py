#!/usr/bin/env python3
"""Fetches the dictionary and the accent list that the deck checks read, into local/cache.

    python3 tools/fetch_reference.py            # fetches what is missing
    python3 tools/fetch_reference.py --again    # fetches everything anew
    python3 tools/fetch_reference.py --newest   # the newest of both instead of the fixed versions

  accents.txt         the accent list of the Kanjium project (CC BY-SA 4.0)
  jmdict_index.json   JMdict (EDRDG, CC BY-SA 4.0) from the jmdict-simplified releases, reduced to
                      what the checks need: written form or kana -> readings, meanings, common or not
  kanjidic_index.json KANJIDIC (EDRDG, CC BY-SA 4.0) from the same release: kanji -> meanings,
                      readings, school grade

Neither file goes into the repository. About 12 MB are downloaded, 120 MB unpacked.

The versions are fixed below, so that the same tables always compile into the same firmware.
To move to newer data: fetch with --newest, run tools/build_decks.py, look at what changed in
lib/core/deck_data.cpp, then write the new versions here.
"""
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "local", "cache")
KANJIUM_COMMIT = "8a0cdaa16d64a281a2048de2eee2ec5e3a440fa6"
ACCENTS_SHA256 = "8bd0dd127dab32ceec94cb03ab1ba6b68858ea73421dfa1731af2f373deb4f20"
JMDICT_RELEASE = "3.6.2+20260921173324"

ACCENTS = "https://raw.githubusercontent.com/mifunetoshiro/kanjium/%s/data/source_files/raw/accents.txt"
RELEASES = "https://github.com/scriptin/jmdict-simplified/releases"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "fetch_reference"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.geturl(), response.read()


def fetch_accents(target, newest):
    _, data = fetch(ACCENTS % ("master" if newest else KANJIUM_COMMIT))
    lines = data.decode("utf-8").splitlines()
    if len(lines) < 100000 or lines[0].count("\t") != 2:
        sys.exit("the accent list does not look as expected: %d lines" % len(lines))
    if not newest and hashlib.sha256(data).hexdigest() != ACCENTS_SHA256:
        sys.exit("the accent list is not the one that was fixed: its checksum differs")
    open(target, "wb").write(data)
    print("accents.txt: %d entries" % len(lines))


def fetch_dictionary(target, newest):
    plain = JMDICT_RELEASE
    if newest:
        landed, _ = fetch(RELEASES + "/latest")
        plain = urllib.request.unquote(landed.rsplit("/", 1)[-1])
        if not re.fullmatch(r"[0-9.]+\+[0-9]+", plain):
            sys.exit("unexpected release name: %s" % plain)
    url = "%s/download/%s/jmdict-eng-%s.json.zip" % (RELEASES, urllib.request.quote(plain), plain)
    print("downloading " + url)
    _, data = fetch(url)
    archive = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in archive.namelist() if n.endswith(".json")]
    if len(names) != 1:
        sys.exit("unexpected contents of the archive: %s" % ", ".join(archive.namelist()))
    dictionary = json.loads(archive.read(names[0]).decode("utf-8"))

    index = {}
    for word in dictionary["words"]:
        written = [k["text"] for k in word.get("kanji", [])]
        kana = [k["text"] for k in word.get("kana", [])]
        gloss = [g["text"] for sense in word.get("sense", []) for g in sense.get("gloss", [])][:6]
        common = any(k.get("common") for k in word.get("kanji", []) + word.get("kana", []))
        for form in written + kana:
            index.setdefault(form, []).append({"kana": kana, "gloss": gloss, "common": common})
    json.dump(index, open(target, "w", encoding="utf-8"), ensure_ascii=False)
    print("jmdict_index.json: JMdict %s of %s, %d entries, %d forms" % (
        dictionary.get("version"), dictionary.get("dictDate"), len(dictionary["words"]), len(index)))


def fetch_kanji(target, newest):
    plain = JMDICT_RELEASE
    if newest:
        landed, _ = fetch(RELEASES + "/latest")
        plain = urllib.request.unquote(landed.rsplit("/", 1)[-1])
    url = "%s/download/%s/kanjidic2-en-%s.json.zip" % (RELEASES, urllib.request.quote(plain), plain)
    print("downloading " + url)
    _, data = fetch(url)
    archive = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in archive.namelist() if n.endswith(".json")]
    if len(names) != 1:
        sys.exit("unexpected contents of the archive: %s" % ", ".join(archive.namelist()))
    dictionary = json.loads(archive.read(names[0]).decode("utf-8"))
    index = {}
    for character in dictionary["characters"]:
        groups = character.get("readingMeaning", {}).get("groups", [])
        index[character["literal"]] = {
            "meanings": [m["value"] for g in groups for m in g.get("meanings", []) if m.get("lang") == "en"],
            "on": [r["value"] for g in groups for r in g.get("readings", []) if r.get("type") == "ja_on"],
            "kun": [r["value"] for g in groups for r in g.get("readings", []) if r.get("type") == "ja_kun"],
            "grade": character.get("misc", {}).get("grade"),
            "strokes": (character.get("misc", {}).get("strokeCounts") or [None])[0],
        }
    json.dump(index, open(target, "w", encoding="utf-8"), ensure_ascii=False)
    print("kanjidic_index.json: KANJIDIC %s, %d kanji" % (dictionary.get("version"), len(index)))


def main():
    newest = "--newest" in sys.argv[1:]
    again = newest or "--again" in sys.argv[1:]
    os.makedirs(CACHE, exist_ok=True)
    accents = os.path.join(CACHE, "accents.txt")
    index = os.path.join(CACHE, "jmdict_index.json")
    if again or not os.path.exists(accents):
        fetch_accents(accents, newest)
    else:
        print("accents.txt is there")
    if again or not os.path.exists(index):
        fetch_dictionary(index, newest)
    else:
        print("jmdict_index.json is there")
    kanji = os.path.join(CACHE, "kanjidic_index.json")
    if again or not os.path.exists(kanji):
        fetch_kanji(kanji, newest)
    else:
        print("kanjidic_index.json is there")


if __name__ == "__main__":
    main()
