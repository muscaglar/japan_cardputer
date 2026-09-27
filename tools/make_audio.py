#!/usr/bin/env python3
"""Makes the sound clips of the memory card and checks each of them by measuring.

    python3 tools/make_audio.py                   # makes what is missing or out of date
    python3 tools/make_audio.py --only signs      # one deck; also buddy, guide; may be given twice
    python3 tools/make_audio.py --check           # measures what is there, makes nothing
    python3 tools/make_audio.py --out DIR         # where to write (card/nihongo/audio beside tools/)
    python3 tools/make_audio.py --voice m --say-voice Otoya

Reads content/decks/*.tsv, content/buddy.tsv and, when it is there, content/guide.tsv. Writes

    f/<deck id>/<item id>.wav     one clip per card, saying its reading
    f/buddy/<line id>.wav         what the buddy says
    f/guide/<page id>-<n>.wav     the clips of a guide page, counted from 1
    index.tsv                     one row per clip: what was spoken, by whom, and what was checked

as WAV, 16 bit, one channel, 16000 samples a second. The folder is "f" for the female voice and
"m" for the male one. The tool can be stopped at any time and started again: a clip is made anew
only when its file is missing or when the card, the engine, the voice or the way of making clips
has changed since the row in index.tsv was written.

What is given to the engine
  A word can be written in more than one way. As it is printed (出口) the engine looks it up and
  knows its accent, but it may choose another reading than the card's: 行き is read いき, 小人
  こびと. In kana (でぐち) the sounds are sure, but the engine may take the kana for another word
  with another accent, or for a particle: へ alone is read "e". So every way is spoken and
  measured: the word as printed, the reading in kana as the deck has it, and the reading in
  the other kana, because はつか is read "watsuka" and ハツカ is not.
  A clip made from kana whose length and sounds are right is the measure for the sounds. The
  printed word is used only when its clip sounds the same, and is nearer to the reading of the
  card than to any other reading of that word: those the deck accepts and, when
  local/cache/jmdict_index.json is there, those of the dictionary. Of the ways that are left,
  the one whose pitch fits the accent of the card is kept; where that does not decide, the
  printed word before kana, and the kana of the deck before the other. Where は or へ stands
  inside a reading and the two kana do not sound the same, the katakana is taken.
  Single kana are given in katakana first, which is never read as a particle. Numbers and
  counters are given in both kana and never as printed, because a price tag does not say how
  it is read. The buddy's lines are given as they are written.

What is measured
  length  seconds for each beat of the reading. An empty or cut clip and one that says more or
          less than the card shows here.
  sounds  where the voice stops. k s t h p and the small っ stop it, everything else does not, so
          a reading leaves a pattern. しちにん starts without voice and ななにん with it; へ read as
          "e" has no breath before the vowel. k, t and p at the start show in the silence that
          Kyoko puts before them; from a voice that puts none, as Kyoko (Enhanced), they
          cannot be asked for. How a voice dies away at the end of a clip is not judged.
  same    whether two ways of writing gave the same sounds: the clips are laid over each other,
          stretched where one is slower, and compared band by band in bands so wide that the
          pitch does not show. This finds another word. It does not find one consonant that is
          voiced where it should not be: that is left to "sounds", and to the other readings.
  pitch   the pitch is followed through the clip, and the places are sought where it falls by
          three semitones or more within one beat. An accent k asks for a fall of 4.5 where
          beat k ends, from half a beat before to a beat and a half after, because the engine
          lets the pitch fall late. A word spoken alone always sinks in its last beat, so
          accent 0 and a fall before the last beat cannot be told apart: for those the check
          asks only that the pitch does not fall by 5 before the last beat but one. This voice
          moves its pitch little, and the check is the weakest of all: it finds a word that
          starts high and falls at once, and one that does not fall at all.
  level   the peak is brought to 1 dB under full scale; silence is cut to 40 ms at both ends; a
          clip the engine has clipped is marked.

Verdict, the last word on each row of index.tsv
  ok      every check that could be made was passed
  doubt   length and sounds are right as far as can be measured, but the pitch does not show
          the accent of the card, or the two kana gave clips that sound unlike
  bad     length or sounds are wrong, or the clip is clipped: better left out
  When no way of writing passes, the reading in kana is kept and marked, so that the device can
  leave it out. Measuring is not hearing: "ok" means that nothing wrong was found.

Another engine, another voice
  Write a class like SayEngine with name, identity() and speak(), and list it in ENGINES.
  Everything after speak() is the same for every engine.
  The numbers the checks go by were found with Kyoko, the small voice of macOS, on the 861
  clips of September 2026. With Kyoko (Enhanced) and Otoya (Enhanced) the same checks find
  the same wrong readings, but Otoya breathes so briefly that an h at the start is not
  measured: his clips of は, ひ, ふ, へ and ほ and of words that begin so are marked bad.

Uses only the Python standard library, and the programs say and afconvert of macOS.
"""
import argparse
import array
import hashlib
import json
import math
import operator
import os
import subprocess
import sys
import tempfile
import time
import wave
from concurrent.futures import ProcessPoolExecutor, as_completed

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)

RATE = 16000
FULL = 32767
PEAK = 10 ** (-1.0 / 20)   # 1 dB under full scale
EDGE = 0.040               # silence kept at both ends, in seconds
FADE = 0.004               # the cut edges are faded over this time
HOP = 0.010                # the pitch is measured this often
CARD_FOLDER = "/audio"     # where the device looks
VERSION = 1                # raise it when clips are made in another way: all are then out of date

INDEX_COLUMNS = ["path", "text", "way", "voice", "engine", "ms", "lead", "reading", "accent", "length",
                 "sounds", "same", "pitch", "level", "verdict", "remark", "made-from"]

OK = "ok"
UNSURE = "unsure"
FAIL = "fail"
NONE = "-"

# Length: seconds for one beat. A kana spoken alone is drawn out.
BEAT_SHORTEST = 0.085
BEAT_LONGEST = 0.215
BEAT_LONGEST_ALONE = {1: 0.34, 2: 0.24}
PAUSE = 0.120              # silence inside a line of the buddy that is not counted as speech

# Sounds
ONSET = 0.35               # part of a beat taken by its consonant
GAP_HEARD = 0.020          # a stop of the voice this long answers a consonant that must stop it
LEAD_OF_A_STOP = 0.040     # silence this long before the first sound is the closure of k, t or p
GAP_LONG = 0.070           # a stop this long must be explained by the reading
GAP_REACH = 0.75           # beats by which a stop may lie off its place
GAP_DRIFT = 0.06           # and further off for every beat of the reading

# Same
SAME_MEAN = 2.0            # dB, mean distance of two clips along their best match: the same sounds
SAME_WORST = 4.5           # dB, the worst stretch of 80 ms of them
SAME_OTHER = 3.0           # dB, mean distance from which on the clips say other things
SAME_MARGIN = 0.3          # dB by which the reading of the card must be nearer than another reading
RIVALS = 6                 # other readings of a word that are tried, at most

# Pitch, in semitones
FALL_SURE = 4.5
FALL_SEEN = 3.0
EARLY_SURE = 5.0
EARLY_SEEN = 4.0
SHORT_SURE = 3.5           # a word of two beats
SHORT_SEEN = 3.0
FALL_BEFORE = 0.5          # beats before the end of beat k where the fall may lie
FALL_AFTER = 1.5           # and after it: the engine lets the pitch fall late

# Following the voice
VOICED_FIT = 0.5           # how well a frame must fit itself, shifted by a period, to have a pitch
SHORTEST_FIT = 0.88        # of the periods that fit, the shortest is taken if it fits this well
ROUGH_LOUD = 0.1           # a frame without pitch is voice all the same when it has this part of
ROUGH_CROSSINGS = 0.35     # the loudest energy and crosses zero less often than this, per sample
PITCH_RANGE = {"f": (100.0, 500.0), "m": (60.0, 320.0)}
SAY_VOICES = {"f": "Kyoko", "m": "Otoya"}


class Stop(Exception):
    """The tool cannot go on; the message says why."""


# ---------------------------------------------------------------------------------------------
# Kana
# ---------------------------------------------------------------------------------------------

SMALL = "ぁぃぅぇぉゃゅょゎ"
VOICELESS = "かきくけこさしすせそたちつてとはひふへほぱぴぷぺぽ"
BREATHED = "はひふへほ"                 # h between vowels often keeps the voice
WHISPERED = "きくしすちつひふぴぷ"        # i and u between voiceless consonants lose the voice
CLOSED = "かきくけこたてとぱぴぷぺぽ"     # k, t and p begin with silence


def is_kana(ch):
    cp = ord(ch)
    return 0x3041 <= cp <= 0x3096 or 0x30A1 <= cp <= 0x30FA or cp == 0x30FC


def is_kanji(ch):
    cp = ord(ch)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF or ch in "々〆"


def to_hiragana(text):
    return "".join(chr(ord(ch) - 0x60) if 0x30A1 <= ord(ch) <= 0x30F6 else ch for ch in text)


def to_katakana(text):
    return "".join(chr(ord(ch) + 0x60) if 0x3041 <= ord(ch) <= 0x3096 else ch for ch in text)


def morae(text):
    """The beats of a text in hiragana, a small kana with the beat before it. None stands where
    words are apart: at a space or a mark."""
    out = []
    for ch in to_hiragana(text):
        if not is_kana(ch):
            if out and out[-1] is not None:
                out.append(None)
        elif ch in SMALL and out and out[-1] is not None:
            out[-1] += ch
        else:
            out.append(ch)
    while out and out[-1] is None:
        out.pop()
    return out


def beat_count(text):
    return sum(1 for beat in morae(text) if beat is not None)


def speakable(text):
    """True for a word as it is printed: kanji and kana, nothing else."""
    return bool(text) and all(is_kana(ch) or is_kanji(ch) for ch in text)


def expected_gaps(text, sentence=False):
    """Where the reading stops the voice: [(from, to, must)] in beats from the start. must is
    False where the voice may stop or go on: a whispered vowel, a pause between the words of
    a line, and h after the first beat, which is often voiced and, written は or へ, may be
    a particle."""
    beats = morae(text)
    gaps = []
    at = 0
    for index, beat in enumerate(beats):
        if beat is None:
            if sentence:
                gaps.append((at, at, False))
            continue
        after = beats[index + 1] if index + 1 < len(beats) else None
        head = beat[0]
        if head == "っ":
            gaps.append((at, at + 1, after is not None and after[0] in VOICELESS))
        elif head in VOICELESS:
            gaps.append((at, at + ONSET, index == 0 or head not in BREATHED))
            if beat in WHISPERED and (after is None or after[0] in VOICELESS or after[0] == "っ"):
                gaps.append((at + ONSET, at + 1, False))
        at += 1
    return gaps


# ---------------------------------------------------------------------------------------------
# What is to be spoken
# ---------------------------------------------------------------------------------------------

class Clip:
    """One clip that the memory card must hold."""

    def __init__(self, voice, folder, name, kind, reading, accent, texts, sure=0, others=()):
        self.voice = voice
        self.folder = folder        # deck id, "buddy" or "guide"
        self.name = name
        self.kind = kind            # kana, word, counter, number, line
        self.reading = reading      # the kana that must be heard
        self.accent = accent        # None where the card gives none
        self.texts = texts          # [(way, text)]: what the engine may be given, the best first
        self.sure = sure            # which of them is the reading as the deck has it
        self.others = list(others)  # other readings of the printed word, which must not be heard

    @property
    def path(self):
        return "%s/%s/%s/%s.wav" % (CARD_FOLDER, self.voice, self.folder, self.name)

    @property
    def beats(self):
        return beat_count(self.reading)

    @property
    def sentence(self):
        return self.kind == "line"


def clip_file(out_dir, path):
    """The file of a clip on this computer. path is the path on the memory card."""
    return os.path.join(out_dir, *path[len(CARD_FOLDER):].strip("/").split("/"))


def read_table(path, columns):
    """The rows of a table as dictionaries, and the values of its "# name: value" lines."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as problem:
        raise Stop("%s cannot be read: %s" % (display(path), problem))
    names = {}
    header = None
    rows = []
    for number, line in enumerate(lines, 1):
        if number == 1 and line.startswith(chr(0xFEFF)):
            line = line[1:]
        if line.startswith("#"):
            key, colon, value = line[1:].partition(":")
            if colon and header is None:
                names[key.strip()] = value.strip()
            continue
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if header is None:
            header = fields
            missing = [name for name in columns if name not in header]
            if missing:
                raise Stop("%s:%d: the header row lacks %s" % (display(path), number, ", ".join(missing)))
            continue
        if len(fields) != len(header):
            raise Stop("%s:%d: %d columns, expected %d" % (display(path), number, len(fields), len(header)))
        row = dict(zip(header, fields))
        row["line"] = number
        rows.append(row)
    if header is None:
        raise Stop("%s: no header row" % display(path))
    return rows, names


def ways_of_writing(kind, prompt, reading):
    """([(way, text)], index of the reading as the deck has it): what the engine may be given
    for a reading, the way to be preferred first. A line of the buddy is given as it is: in
    the other kana its particles would be no particles any more."""
    hiragana = any(0x3041 <= ord(ch) <= 0x3096 for ch in reading)
    if len(morae(reading)) == 1:
        texts = [("katakana", to_katakana(reading))]
        if to_hiragana(reading) != texts[0][1]:
            texts.append(("hiragana", to_hiragana(reading)))
        return texts, 0
    texts = []
    if kind == "word" and speakable(prompt) and any(is_kanji(ch) for ch in prompt):
        texts.append(("word", prompt))
    sure = len(texts)
    texts.append(("kana", reading))
    other = to_katakana(reading) if hiragana else to_hiragana(reading)
    if kind != "line" and other != reading:
        texts.append(("katakana" if hiragana else "hiragana", other))
    return texts, sure


def other_readings(word, reading, accepted, dictionary):
    """The readings a printed word has beside the reading of the card."""
    found = [part for part in accepted.split("|") if part]
    for entry in (dictionary or {}).get(word, []):
        found += entry.get("kana", [])
    out = []
    for kana in found:
        if (kana and all(is_kana(ch) for ch in kana) and to_hiragana(kana) != to_hiragana(reading)
                and to_hiragana(kana) not in [to_hiragana(other) for other in out]):
            out.append(kana)
    return out[:RIVALS]


def read_dictionary(cache_dir):
    """{written form: [{"kana": [...]}]} from jmdict_index.json, None when it is not there."""
    path = os.path.join(cache_dir, "jmdict_index.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as problem:
        raise Stop("%s cannot be read: %s" % (display(path), problem))


def deck_clips(path, voice, dictionary=None):
    rows, names = read_table(path, ["id", "prompt", "reading", "accent"])
    deck = os.path.basename(path)[:-len(".tsv")]
    kind = names.get("kind", "word")
    clips = []
    for row in rows:
        where = "%s:%d" % (display(path), row["line"])
        if not row["id"] or not row["reading"]:
            raise Stop("%s: id or reading is empty" % where)
        if any(not is_kana(ch) for ch in row["reading"]):
            raise Stop("%s: the reading %s is not kana only" % (where, row["reading"]))
        accent = None
        if row["accent"]:
            if not row["accent"].isdigit() or int(row["accent"]) > beat_count(row["reading"]):
                raise Stop("%s: the accent %s does not fit the reading" % (where, row["accent"]))
            accent = int(row["accent"])
        texts, sure = ways_of_writing(kind, row["prompt"], row["reading"])
        others = []
        if texts[0][0] == "word":
            others = other_readings(row["prompt"], row["reading"], row.get("accepted", ""), dictionary)
        clips.append(Clip(voice, deck, row["id"], kind, row["reading"], accent, texts, sure, others))
    return clips


def buddy_clips(path, voice):
    rows, _ = read_table(path, ["id", "ja"])
    clips = []
    for row in rows:
        if not row["id"] or not beat_count(row["ja"]):
            raise Stop("%s:%d: id or ja is empty" % (display(path), row["line"]))
        clips.append(Clip(voice, "buddy", row["id"], "line", row["ja"], None, [("kana", row["ja"])]))
    return clips


def guide_clips(path, voice):
    rows, _ = read_table(path, ["id", "clips"])
    clips = []
    for row in rows:
        for number, text in enumerate([part for part in row["clips"].split("|") if part.strip()], 1):
            text = text.strip()
            if any(not is_kana(ch) for ch in text):
                raise Stop("%s:%d: the clip %s is not kana only" % (display(path), row["line"], text))
            texts, sure = ways_of_writing("word", text, text)
            clips.append(Clip(voice, "guide", "%s-%d" % (row["id"], number), "word", text, None, texts, sure))
    return clips


def all_clips(content_dir, voice, only=(), dictionary=None):
    """Every clip the content asks for, in the order of index.tsv."""
    decks_dir = os.path.join(content_dir, "decks")
    if not os.path.isdir(decks_dir):
        raise Stop("%s is not a folder" % display(decks_dir))
    clips = []
    folders = []
    for name in sorted(os.listdir(decks_dir)):
        if name.endswith(".tsv") and not name.startswith("."):
            folders.append(name[:-len(".tsv")])
            clips += deck_clips(os.path.join(decks_dir, name), voice, dictionary)
    for folder, reader in (("guide", guide_clips), ("buddy", buddy_clips)):
        if folder in folders:
            raise Stop("a deck cannot be called %s: that folder holds other clips" % folder)
        path = os.path.join(content_dir, folder + ".tsv")
        if os.path.exists(path):
            folders.append(folder)
            clips += reader(path, voice)
    unknown = [name for name in only if name not in folders]
    if unknown:
        raise Stop("--only %s: there is no such deck. There are: %s" % (unknown[0], ", ".join(folders)))
    seen = {}
    for clip in clips:
        if clip.path in seen:
            raise Stop("two clips would be written to %s" % clip.path)
        seen[clip.path] = clip
    if only:
        clips = [clip for clip in clips if clip.folder in only]
    return clips


# ---------------------------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------------------------

def read_wav(path):
    """The samples of a clip. Anything but 16 bit, one channel, 16000 a second is refused."""
    try:
        with wave.open(path, "rb") as handle:
            form = (handle.getnchannels(), handle.getsampwidth() * 8, handle.getframerate())
            data = handle.readframes(handle.getnframes())
    except (OSError, EOFError, wave.Error) as problem:
        raise Stop("%s is not a sound file: %s" % (display(path), problem))
    if form != (1, 16, RATE):
        raise Stop("%s has %d channel(s), %d bit, %d samples a second" % ((display(path),) + form))
    samples = array.array("h")
    samples.frombytes(data[:len(data) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


def write_wav(path, samples):
    """Writes through a second file, so that a clip is whole or not there."""
    data = array.array("h", samples)
    if sys.byteorder == "big":
        data.byteswap()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    part = path + ".part"
    with wave.open(part, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(data.tobytes())
    os.replace(part, path)


def levels(samples, size):
    """Root mean square of every stretch of size samples."""
    out = []
    for start in range(0, len(samples) - size + 1, size):
        part = samples[start:start + size]
        out.append(math.sqrt(sum(map(operator.mul, part, part)) / float(size)))
    return out


def sound_span(samples):
    """(first, last + 1) of the samples that are not silence, None for a silent clip. Sound is
    what stays within 46 dB of the loudest 5 ms for 15 ms or more: a click is not sound."""
    size = RATE // 200
    loud = levels(samples, size)
    top = max(loud) if loud else 0.0
    if top < 50.0:
        return None
    limit = max(top * 0.005, 8.0)
    marks = [value >= limit for value in loud]

    def first_run(flags):
        for index in range(len(flags) - 2):
            if flags[index] and flags[index + 1] and flags[index + 2]:
                return index
        return None

    first = first_run(marks)
    last = first_run(marks[::-1])
    if first is None or last is None:
        return None
    return first * size, min(len(samples), (len(marks) - last) * size)


def without_start_noise(samples):
    """The samples without the faint noise with which the engine begins a clip. It is taken
    for that noise when it stays under 1.5 % of the loudest 5 ms and is followed, within 60 ms
    of the start, by 20 ms of silence: before k, t and p, whose silence it would hide."""
    size = RATE // 200
    loud = levels(samples[:RATE], size)
    top = max(levels(samples, size) or [0.0])
    silence = max(top * 0.001, 4.0)
    for index in range(min(12, len(loud) - 4)):
        if loud[index] >= top * 0.015:
            break
        if max(loud[index:index + 4]) < silence:
            return array.array("h", [0] * (index * size)) + samples[index * size:]
    return samples


def clipped(samples):
    """How many samples lie in flat tops: three or more in a row at the highest value."""
    top = max(abs(min(samples)), max(samples)) if len(samples) else 0
    if top < 1000:
        return 0
    count = 0
    run = 0
    for value in samples:
        if abs(value) >= top - 1:
            run += 1
        else:
            if run >= 3:
                count += run
            run = 0
    return count + (run if run >= 3 else 0)


def trim(samples, span):
    """The sound with EDGE seconds before and after it. What was there is kept and faded in and
    out; where the file had less, silence is added."""
    edge = int(EDGE * RATE)
    fade = int(FADE * RATE)
    first, last = span
    start = max(0, first - edge)
    end = min(len(samples), last + edge)
    body = [float(value) for value in samples[start:end]]
    for index in range(min(fade, len(body))):
        body[index] *= index / float(fade)
        body[-1 - index] *= index / float(fade)
    return [0.0] * (edge - (first - start)) + body + [0.0] * (edge - (end - last))


def level(samples):
    """The samples as 16 bit numbers, the highest of them at PEAK."""
    top = max(abs(value) for value in samples) if samples else 0.0
    gain = PEAK * FULL / top if top else 0.0
    return array.array("h", [int(round(value * gain)) for value in samples])


def prepare(raw):
    """(samples, facts) of a clip as the engine gave it: trimmed and levelled. samples is None
    for a silent clip."""
    facts = {"clipped": clipped(raw), "peak": max(abs(min(raw)), max(raw)) if len(raw) else 0}
    raw = without_start_noise(raw)
    span = sound_span(raw)
    if span is None:
        return None, facts
    facts["lead"] = span[0] / float(RATE)
    facts["tail"] = (len(raw) - span[1]) / float(RATE)
    return level(trim(raw, span)), facts


# ---------------------------------------------------------------------------------------------
# Pitch
# ---------------------------------------------------------------------------------------------

_TAPS = []


def halve(samples):
    """Every second sample, after a low-pass at 3.5 kHz."""
    if not _TAPS:
        count, cutoff = 31, 0.22
        middle = (count - 1) / 2.0
        for index in range(count):
            x = index - middle
            value = 2 * cutoff if x == 0 else math.sin(2 * math.pi * cutoff * x) / (math.pi * x)
            _TAPS.append(value * (0.54 - 0.46 * math.cos(2 * math.pi * index / (count - 1))))
        total = sum(_TAPS)
        _TAPS[:] = [value / total for value in _TAPS]
    half = len(_TAPS) // 2
    padded = [0.0] * half + [float(value) for value in samples] + [0.0] * half
    count = len(_TAPS)
    return [sum(map(operator.mul, _TAPS, padded[index:index + count])) for index in range(0, len(samples), 2)]


def pitch_track(samples, low=100.0, high=500.0):
    """[(state, hertz)] every HOP seconds: state is "v" voice with a pitch, "r" rough voice,
    "u" sound without voice, "s" silence. The frame at index i looks at the 30 ms or more that
    start at i * HOP: 20 ms or two of the longest periods, and the longest period again.

    Each frame is laid over itself, shifted by every period between 1/high and 1/low, and the
    shift at which it fits itself best is its period. Of several that fit, the shortest is
    taken, which keeps the tracker from the octave below.

    A voice that creaks, or whose pitch slides fast, does not fit itself and has no pitch that
    could be given. It is loud and low like a vowel, where s and h are faint or hiss: that
    is the rough voice. It counts as voice, and its pitch as not known."""
    rate = RATE // 2
    data = halve(samples)
    window = int(max(0.020, 2.0 / low) * rate)
    step = int(HOP * rate)
    shortest = max(2, int(rate / high))
    longest = int(rate / low) + 1
    need = window + longest + 2
    data += [0.0] * need
    multiply = operator.mul

    frames = []
    loudest = 0.0
    for start in range(0, len(data) - need, step):
        part = data[start:start + need]
        mean = sum(part) / need
        part = [value - mean for value in part]
        head = part[:window]
        energy = sum(map(multiply, head, head))
        frames.append((part, head, energy))
        loudest = max(loudest, energy)

    track = []
    for part, head, energy in frames:
        if energy <= loudest * 0.0002:
            track.append(("s", 0.0))
            continue
        squares = [value * value for value in part]
        power = sum(squares[shortest - 1:shortest - 1 + window])
        scores = {}
        for shift in range(shortest - 1, longest + 2):
            if shift > shortest - 1:
                power += squares[shift + window - 1] - squares[shift - 1]
            scores[shift] = (sum(map(multiply, head, part[shift:shift + window])) / math.sqrt(energy * power)
                             if power > 0 else 0.0)
        best = max(scores[shift] for shift in range(shortest, longest + 1))
        period = None
        if best >= VOICED_FIT and energy > loudest * 0.002:
            for shift in range(shortest, longest + 1):
                score = scores[shift]
                if score >= SHORTEST_FIT * best and score >= scores[shift - 1] and score >= scores[shift + 1]:
                    period = shift
                    break
        if period is None:
            crossings = sum(1 for index in range(1, window) if (head[index - 1] < 0) != (head[index] < 0))
            rough = energy >= loudest * ROUGH_LOUD and crossings < ROUGH_CROSSINGS * window
            track.append(("r" if rough else "u", 0.0))
            continue
        before, here, after = scores[period - 1], scores[period], scores[period + 1]
        bend = before - 2 * here + after
        track.append(("v", rate / (period + (0.5 * (before - after) / bend if bend else 0.0))))
    return tidy_track(track)


def tidy_track(track):
    """Takes out what cannot be voice: runs shorter than 30 ms. The pitch of a frame that lies
    more than seven semitones from the frames around it is a mistake: the frame is voice, its
    pitch is not known."""
    track = list(track)
    index = 0
    while index < len(track):
        if track[index][0] not in "vr":
            index += 1
            continue
        end = index
        while end < len(track) and track[end][0] in "vr":
            end += 1
        if end - index < 3:
            track[index:end] = [("u", 0.0)] * (end - index)
        index = end
    out = list(track)
    for index, (state, hertz) in enumerate(track):
        if state != "v":
            continue
        near = sorted(value for kind, value in track[max(0, index - 6):index + 7] if kind == "v")
        if abs(12 * math.log(hertz / near[len(near) // 2], 2)) > 7:
            out[index] = ("r", 0.0)
    return out


class Heard:
    """What was measured in a clip that is trimmed already."""

    def __init__(self, samples, voice="f"):
        low, high = PITCH_RANGE[voice]
        self.samples = samples
        self.track = pitch_track(samples, low, high)
        span = sound_span(samples) or (0, len(samples))
        self.first = span[0] / float(RATE)
        self.last = span[1] / float(RATE)
        self.seconds = len(samples) / float(RATE)

    @property
    def sound(self):
        """Seconds from the first sound to the last."""
        return self.last - self.first

    def frames(self):
        """[(seconds since the first sound, state, hertz)] of the frames that hold sound."""
        out = []
        for index, (state, hertz) in enumerate(self.track):
            start = index * HOP
            if start + 0.030 > self.first and start < self.last:
                out.append((start + 0.015 - self.first, state, hertz))
        return out

    def gaps(self):
        """[(from, to)] in seconds since the first sound: where there is no voice."""
        out = []
        start = None
        frames = self.frames()
        for when, state, _ in frames:
            if state not in "vr" and start is None:
                start = when - HOP / 2
            elif state in "vr" and start is not None:
                out.append((max(0.0, start), when - HOP / 2))
                start = None
        if start is not None and frames:
            out.append((max(0.0, start), frames[-1][0] + HOP / 2))
        return out

    def pauses(self):
        """Seconds of silence inside the clip that are too long to be part of a word."""
        total = 0.0
        run = 0
        for _, state, _ in self.frames():
            if state == "s":
                run += 1
                continue
            if run * HOP >= PAUSE:
                total += run * HOP
            run = 0
        return total

    def contour(self):
        """(seconds of the first value, [semitones every HOP]): the pitch against its middle
        value, drawn through the stretches without voice and smoothed over 50 ms. None when
        there is too little voice."""
        frames = self.frames()
        voiced = [index for index, frame in enumerate(frames) if frame[1] == "v"]
        if len(voiced) < 5:
            return None
        values = sorted(frames[index][2] for index in voiced)
        middle = values[len(values) // 2]
        tones = {index: 12 * math.log(frames[index][2] / middle, 2) for index in voiced}
        line = []
        for position, index in enumerate(voiced):
            line.append(tones[index])
            if position + 1 < len(voiced):
                after = voiced[position + 1]
                for between in range(index + 1, after):
                    part = (between - index) / float(after - index)
                    line.append(tones[index] + (tones[after] - tones[index]) * part)
        smooth = []
        for index in range(len(line)):
            part = line[max(0, index - 2):index + 3]
            smooth.append(sum(part) / len(part))
        return frames[voiced[0]][0], smooth


def falls(heard, beats):
    """[(beats since the first sound, semitones)] of the falls of the pitch, one entry for each.
    At every HOP the pitch half a beat before is compared with the pitch half a beat after. A
    fall is where that difference is FALL_SEEN or more and larger than anywhere within half
    a beat; it lies in the middle of the stretch that comes within a fifth of that value."""
    found = heard.contour()
    if found is None or not beats:
        return []
    start, line = found
    beat = heard.sound / beats
    reach = max(3, int(round(0.5 * beat / HOP)))
    drops = [line[max(0, index - reach)] - line[min(len(line) - 1, index + reach)] for index in range(len(line))]
    out = []
    index = 0
    while index < len(drops):
        here = drops[index]
        if here < FALL_SEEN or here < max(drops[max(0, index - reach):index + reach + 1]):
            index += 1
            continue
        low = high = index
        while low > 0 and drops[low - 1] >= 0.8 * here:
            low -= 1
        while high + 1 < len(drops) and drops[high + 1] >= 0.8 * here:
            high += 1
        out.append(((start + 0.5 * (low + high) * HOP) / beat, here))
        index = high + 1
    return out


# ---------------------------------------------------------------------------------------------
# Spectrum
# ---------------------------------------------------------------------------------------------

SPECTRUM = 512
# Hertz. Every band is 700 Hz wide or wider and laid half over the next, so that it always holds
# two or more overtones of a voice and does not change with the pitch.
BAND_EDGES = [150, 500, 850, 1200, 1550, 1900, 2300, 2750, 3250, 3800, 4400, 5100, 5900, 6800, 7800]
QUIET = 50.0               # dB under the loudest band of the clip where silence lies
_TABLES = {}


def tables():
    if not _TABLES:
        bits = SPECTRUM.bit_length() - 1
        _TABLES["order"] = [int(format(index, "0%db" % bits)[::-1], 2) for index in range(SPECTRUM)]
        _TABLES["cos"] = [math.cos(2 * math.pi * k / SPECTRUM) for k in range(SPECTRUM // 2)]
        _TABLES["sin"] = [-math.sin(2 * math.pi * k / SPECTRUM) for k in range(SPECTRUM // 2)]
        size = int(0.025 * RATE)
        _TABLES["window"] = [0.5 - 0.5 * math.cos(2 * math.pi * index / (size - 1)) for index in range(size)]
        bins = [int(round(edge * SPECTRUM / float(RATE))) for edge in BAND_EDGES]
        _TABLES["bands"] = [(bins[index], bins[index + 2]) for index in range(len(bins) - 2)]
    return _TABLES


def power_spectrum(frame):
    """The power in each of the first SPECTRUM / 2 + 1 frequencies of a frame."""
    table = tables()
    cos, sin = table["cos"], table["sin"]
    frame = list(frame) + [0.0] * (SPECTRUM - len(frame))
    real = [frame[index] for index in table["order"]]
    imag = [0.0] * SPECTRUM
    size = 2
    while size <= SPECTRUM:
        half = size // 2
        step = SPECTRUM // size
        for start in range(0, SPECTRUM, size):
            k = 0
            for low in range(start, start + half):
                high = low + half
                a = real[high] * cos[k] - imag[high] * sin[k]
                b = real[high] * sin[k] + imag[high] * cos[k]
                real[high] = real[low] - a
                imag[high] = imag[low] - b
                real[low] += a
                imag[low] += b
                k += step
        size *= 2
    return [real[index] ** 2 + imag[index] ** 2 for index in range(SPECTRUM // 2 + 1)]


def colours(samples):
    """For every HOP of the sound its colour: how the loudness is spread over the bands, in dB
    about their mean, and as the last value half that mean. The quieter a frame, the less its
    colour counts: in silence there is none."""
    table = tables()
    window = table["window"]
    span = sound_span(samples) or (0, len(samples))
    step = int(HOP * RATE)
    rows = []
    for start in range(span[0], max(span[0] + 1, span[1] - len(window) // 2), step):
        part = samples[start:start + len(window)]
        power = power_spectrum([value * window[index] for index, value in enumerate(part)])
        rows.append([sum(power[low:high]) / (high - low) for low, high in table["bands"]])
    top = max(max(row) for row in rows) if rows else 0.0
    if top <= 0:
        return []
    floor = top * 10 ** (-QUIET / 10)
    out = []
    for row in rows:
        decibels = [10 * math.log10(max(value, floor) / top) for value in row]
        mean = sum(decibels) / len(decibels)
        weight = max(0.0, min(1.0, (mean + QUIET) / 25.0))
        out.append([(value - mean) * weight for value in decibels] + [0.5 * mean])
    return out


def distance(one, other):
    """(mean, worst) distance in dB between two clips given as colours(). The clips are laid
    over each other so that the sum of the distances is smallest; one may run up to twice as
    fast as the other. worst is the mean of the worst 80 ms. None when they cannot be laid over
    each other at all."""
    if not one or not other:
        return None
    rows, columns = len(one), len(other)
    if rows > 2 * columns + 8 or columns > 2 * rows + 8:
        return None
    reach = max(8, abs(rows - columns) + max(rows, columns) // 4)
    far = float("inf")
    size = len(one[0])

    def apart(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / size)

    cost = [[far] * columns for _ in range(rows)]
    step = [[None] * columns for _ in range(rows)]
    local = [[0.0] * columns for _ in range(rows)]
    for row in range(rows):
        middle = row * columns // rows
        for column in range(max(0, middle - reach), min(columns, middle + reach + 1)):
            here = apart(one[row], other[column])
            local[row][column] = here
            if row == 0 and column == 0:
                cost[row][column] = here
                continue
            best = far
            for back in ((1, 1), (1, 0), (0, 1)):
                r, c = row - back[0], column - back[1]
                if r >= 0 and c >= 0 and cost[r][c] < best:
                    best = cost[r][c]
                    step[row][column] = back
            cost[row][column] = best + here
    if cost[-1][-1] == far:
        return None
    path = []
    row, column = rows - 1, columns - 1
    while True:
        path.append(local[row][column])
        back = step[row][column]
        if back is None:
            break
        row, column = row - back[0], column - back[1]
    path.reverse()
    mean = sum(path) / len(path)
    width = min(8, len(path))
    worst = max(sum(path[index:index + width]) / width for index in range(len(path) - width + 1))
    return mean, worst


# ---------------------------------------------------------------------------------------------
# The checks. Each gives (mark, number or word): ok, unsure, fail, or - when it cannot be made.
# ---------------------------------------------------------------------------------------------

def beat_length(heard, beats, sentence=False):
    """Seconds for one beat. Between the words of a line the pauses are left out."""
    return (heard.sound - (heard.pauses() if sentence else 0.0)) / beats


def check_length(heard, beats, sentence=False):
    if not beats:
        return NONE, ""
    each = beat_length(heard, beats, sentence)
    longest = BEAT_LONGEST_ALONE.get(beats, BEAT_LONGEST)
    return (OK if BEAT_SHORTEST <= each <= longest else FAIL), "%.3f" % each


def check_sounds(heard, reading, sentence=False, lead=0.0, closes=False):
    """Compares where the voice stops with where the reading stops it. lead is the silence the
    engine put before the first sound, in seconds. closes says that the voice is known to put
    silence before k, t and p: 45 ms or more, and before nothing else more than 25.

    The start of a clip is known to the millisecond, so the first sound is judged on its own.
    Further on, the beats are only about as long as one another: there a stop of the voice may
    lie GAP_REACH beats from its place, and a little more in a long reading. At the end a
    voice dies away as it likes: what follows the last voice is not judged.

    From a voice that does not put silence before them, k, t and p at the start cannot be
    asked for: it goes from the burst to the vowel within 15 ms, and nothing is left to
    measure."""
    beats = beat_count(reading)
    if not beats:
        return NONE, ""
    beat = beat_length(heard, beats, sentence)
    if beat <= 0:
        return FAIL, "empty"
    reach = GAP_REACH + GAP_DRIFT * beats
    if sentence:
        reach += heard.pauses() / beat
    wanted = expected_gaps(reading, sentence)
    found = [(start / beat, end / beat, end - start) for start, end in heard.gaps()]

    closed = morae(reading)[0][0] in CLOSED
    if lead >= LEAD_OF_A_STOP and not closed:
        return FAIL, "k, t or p at the start"
    first = found[0][2] if found and found[0][0] * beat <= 0.030 else 0.0
    if wanted and wanted[0][0] == 0:
        if wanted[0][2] and first < GAP_HEARD and not (closed and (lead >= LEAD_OF_A_STOP or not closes)):
            return FAIL, "voice at beat 1"
        wanted = wanted[1:] if wanted[0][1] < 1 else wanted
    elif first >= GAP_LONG:
        return FAIL, "no voice at beat 1"

    for start, end, must in wanted:
        if must and not any(length >= GAP_HEARD and low < end + reach and high > start - reach
                            for low, high, length in found):
            return FAIL, "voice at beat %d" % (int(start) + 1)
    wanted = expected_gaps(reading, sentence)
    if found and found[-1][1] * beat >= heard.sound - 0.030 and found[-1][0] > 0:
        found = found[:-1]
    for low, high, length in found:
        if length >= GAP_LONG and not any(low < end + reach and high > start - reach for start, end, _ in wanted):
            return FAIL, "no voice at beat %d" % (int((low + high) / 2) + 1)
    return OK, ""


def check_pitch(heard, beats, accent):
    """Compares the falls of the pitch with the accent of the card. An accent of 1 to two less
    than the number of beats asks for a fall where beat k ends. Every other accent, 0 and the
    two last beats, asks that there is no fall before the last beat but one."""
    if accent is None or beats < 2:
        return NONE, ""
    if heard.contour() is None:
        return UNSURE, "no voice"
    found = falls(heard, beats)
    wanted = 1 <= accent <= beats - 2
    if beats == 2:
        wanted = accent == 1
        sure, seen = SHORT_SURE, SHORT_SEEN
    elif wanted:
        found = [fall for fall in found if accent - FALL_BEFORE <= fall[0] <= accent + FALL_AFTER]
        sure, seen = FALL_SURE, FALL_SEEN
    else:
        found = [fall for fall in found if 0.5 <= fall[0] <= beats - 1.5]
        sure, seen = EARLY_SURE, EARLY_SEEN
    where, fall = max(found or [(0.0, 0.0)], key=lambda pair: pair[1])
    note = "%.1f at %.1f" % (fall, where) if fall else "no fall"
    if wanted:
        return (OK if fall >= sure else UNSURE if fall >= seen else FAIL), note
    return (FAIL if fall >= sure else UNSURE if fall >= seen else OK), note


def check_same(one, measure, rivals=()):
    """Compares a clip with the clip that is sure to have the right sounds, both given as
    colours(). rivals: [(reading, colours)] of other readings, none of which may be nearer."""
    found = distance(one, measure)
    if found is None:
        return FAIL, "lengths"
    mean, worst = found
    mark = OK if mean <= SAME_MEAN and worst <= SAME_WORST else FAIL if mean > SAME_OTHER else UNSURE
    note = "%.1f/%.1f" % (mean, worst)
    for reading, other in rivals:
        rival = distance(one, other)
        if rival is None or mark == FAIL:
            continue
        if rival[0] + SAME_MARGIN < mean:
            mark, note = FAIL, "%s, read %s %.1f" % (note, reading, rival[0])
        elif rival[0] < mean + SAME_MARGIN and mark == OK:
            mark, note = UNSURE, "%s, or %s %.1f" % (note, reading, rival[0])
    return mark, note


def check_level(samples, facts):
    if facts.get("clipped"):
        return FAIL, "clipped %d" % facts["clipped"]
    top = max(abs(min(samples)), max(samples))
    return (OK if abs(top - PEAK * FULL) <= 2 else FAIL), "%.1f" % (20 * math.log10(top / float(FULL)))


def check_edges(heard):
    """The silence before and after the sound, which must be EDGE long, to 10 ms."""
    lead = heard.first
    tail = heard.seconds - heard.last
    return (OK if abs(lead - EDGE) <= 0.010 and abs(tail - EDGE) <= 0.010 else FAIL), "%.3f+%.3f" % (lead, tail)


class Try:
    """One way of writing, spoken and measured."""

    def __init__(self, clip, way, text, raw, closes=False):
        self.way = way
        self.text = text
        self.samples, self.facts = prepare(raw)
        self.marks = {"length": (FAIL, "silent"), "sounds": (NONE, ""), "pitch": (NONE, ""),
                      "level": (FAIL, "silent"), "same": (NONE, "")}
        self.proved = True
        self.left_out = ""
        self.spectrum = None
        if self.samples is None:
            return
        heard = Heard(self.samples, clip.voice)
        self.marks["length"] = check_length(heard, clip.beats, clip.sentence)
        self.marks["sounds"] = check_sounds(heard, clip.reading, clip.sentence, self.facts["lead"], closes)
        self.marks["pitch"] = check_pitch(heard, clip.beats, clip.accent)
        self.marks["level"] = check_level(self.samples, self.facts)

    @property
    def ms(self):
        return int(round(len(self.samples) * 1000.0 / RATE)) if self.samples is not None else 0

    def right_sounds(self):
        return all(self.marks[name][0] == OK for name in ("length", "sounds", "level"))

    def verdict(self):
        if not self.right_sounds():
            return "bad"
        return "doubt" if self.marks["pitch"][0] == FAIL or not self.proved else "ok"

    def colours(self):
        if self.spectrum is None:
            self.spectrum = colours(self.samples)
        return self.spectrum

    def failing(self):
        """The first check that keeps this way from being used, as words."""
        for name in ("length", "sounds", "level", "same"):
            if self.marks[name][0] not in (OK, NONE) or (name == "same" and self.left_out):
                return ("%s %s %s" % (name, mark_text(self.marks[name]), self.left_out)).strip()
        return ""


def may_hold_a_particle(text):
    """True for kana in which は or へ stands after the first letter: the engine may read them
    wa and e, as it reads the particles. In katakana it never does."""
    return any(ch in "はへ" for ch in text[1:])


def compare(clip, tries, rivals):
    """Finds the measure for the sounds, sets the mark "same" of the ways of writing, and gives
    the measure. rivals: [(reading, samples)] of the other readings of the printed word.

    The measure is the first way in kana whose length and sounds are right; if there is none,
    the reading as the deck has it. Two ways in kana that are right are compared with each
    other. If they are not the same and only the first may hold a particle, the second is the
    measure and the first is left out."""
    kana = [one for one in tries if one.way != "word" and one.right_sounds()]
    measure = kana[0] if kana else tries[clip.sure]
    if len(kana) > 1:
        mark = check_same(kana[1].colours(), kana[0].colours())
        kana[0].marks["same"] = kana[1].marks["same"] = mark
        if mark[0] != OK and may_hold_a_particle(kana[0].text) and not may_hold_a_particle(kana[1].text):
            measure = kana[1]
            kana[0].left_out = "and may hold a particle"
    if measure.samples is not None:
        others = [(reading, colours(samples)) for reading, samples in rivals if samples is not None]
        for one in tries:
            if one.way == "word" and one.samples is not None:
                one.marks["same"] = check_same(one.colours(), measure.colours(), others)
    return measure


PITCH_RANK = {OK: 0, NONE: 1, UNSURE: 1, FAIL: 2}


def choose(tries, measure):
    """(the way of writing to keep, remark), with the measure that compare() gave. A way of
    writing can be kept when its length and sounds are right and it sounds the same as the
    measure. Of those the best in pitch is kept, and of equals the one that comes first. It
    is not proved, and so in doubt, when no kana was right to compare it with, or when the
    measure is written in hiragana and the katakana, which is read letter by letter, seemed
    right and sounds like something else."""
    if measure.right_sounds():
        good = [one for one in tries if one is measure or (
            one.right_sounds() and not one.left_out and one.marks["same"][0] == OK)]
    else:
        good = [one for one in tries if one.right_sounds()]
    kept = min(good, key=lambda one: (PITCH_RANK[one.marks["pitch"][0]], tries.index(one))) if good else measure
    remarks = []
    if good and not measure.right_sounds():
        kept.proved = False
        remarks.append("not proved, no kana was right")
    for one in tries:
        if one is kept:
            continue
        if one not in good:
            remarks.append("%s: %s" % (one.text, one.failing()))
            if (one.way != "word" and one.right_sounds() and one.marks["same"][0] == FAIL
                    and to_katakana(measure.text) != measure.text):
                kept.proved = False
        elif PITCH_RANK[one.marks["pitch"][0]] > PITCH_RANK[kept.marks["pitch"][0]]:
            remarks.append("%s: pitch %s" % (one.text, mark_text(one.marks["pitch"])))
    return kept, "; ".join(remarks)


# ---------------------------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------------------------

class Engine:
    """Something that can speak. speak() writes what it says as WAV, 16 bit, one channel,
    16000 samples a second; identity() names engine and voice for index.tsv, where a change of
    it makes every clip out of date. It begins with the name of the engine and a stroke."""
    name = ""

    @classmethod
    def add_arguments(cls, parser):
        pass

    @classmethod
    def closes(cls, identity):
        """True when the voice of this identity puts silence before k, t and p at the start
        of a clip. The check of the sounds then asks for it."""
        return False

    def __init__(self, voice, options):
        self.voice = voice

    def identity(self):
        return self.name

    def ready(self):
        """None, or why the engine cannot speak."""
        return None

    def speak(self, text, path):
        raise NotImplementedError


class SayEngine(Engine):
    """The speech of macOS: say writes AIFF, afconvert turns it into the WAV wanted."""
    name = "say"

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--say-voice", metavar="NAME",
                            help="the voice of macOS to use (%s)" % ", ".join(
                                "%s for %s" % (name, voice) for voice, name in sorted(SAY_VOICES.items())))
        parser.add_argument("--say-rate", metavar="WORDS", type=int,
                            help="speed in words a minute, as say -r takes it (the voice's own)")

    def __init__(self, voice, options):
        Engine.__init__(self, voice, options)
        self.say_voice = options.get("say_voice") or SAY_VOICES[voice]
        self.rate = options.get("say_rate")

    def identity(self):
        return "say/%s%s" % (self.say_voice, "/%d" % self.rate if self.rate else "")

    @classmethod
    def closes(cls, identity):
        """The small voices do, as Kyoko. Those with a word in brackets after the name, as
        Kyoko (Enhanced), do not."""
        return "(" not in identity

    def ready(self):
        try:
            listed = subprocess.run(["say", "-v", "?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, timeout=60).stdout
            subprocess.run(["afconvert", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        except (OSError, subprocess.SubprocessError) as problem:
            return "say and afconvert of macOS are needed: %s" % problem
        japanese = []
        for line in listed.splitlines():
            name, _, rest = line.partition("#")
            words = name.split()
            if len(words) >= 2 and words[-1] == "ja_JP":
                japanese.append(" ".join(words[:-1]))
        if self.say_voice not in japanese:
            return ("the voice %s is not installed. Japanese voices here: %s. More are added in the system "
                    "settings under spoken content" % (self.say_voice, ", ".join(japanese) or "none"))
        return None

    def speak(self, text, path):
        aiff = path + ".aiff"
        command = ["say", "-v", self.say_voice] + (["-r", str(self.rate)] if self.rate else [])
        try:
            for step in (command + ["-o", aiff, text],
                         ["afconvert", "-f", "WAVE", "-d", "LEI16@%d" % RATE, "-c", "1", aiff, path]):
                done = subprocess.run(step, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True, timeout=120)
                if done.returncode:
                    raise Stop("%s failed on %s: %s" % (step[0], text, done.stderr.strip() or done.returncode))
        except (OSError, subprocess.SubprocessError) as problem:
            raise Stop("%s could not be spoken: %s" % (text, problem))
        finally:
            if os.path.exists(aiff):
                os.remove(aiff)


ENGINES = {SayEngine.name: SayEngine}


# ---------------------------------------------------------------------------------------------
# index.tsv
# ---------------------------------------------------------------------------------------------

INDEX_HEAD = [
    "# The sound clips in this folder, written by tools/make_audio.py. Do not change by hand.",
    "# path: on the memory card. text: what the engine was given. ms: length of the clip.",
    "# lead: ms of silence the engine put before the sound and that were cut: k, t and p show so.",
    "# way: word as printed, kana as the deck has the reading, katakana or hiragana the other kana.",
    "# length, sounds, same, pitch, level: ok, unsure, fail, or - where the check could not be made,",
    "#   and what was measured: seconds a beat; the beat that is wrong; dB between this clip and the",
    "#   clip of another way in kana, mean/worst; semitones of the fall and the beat where it lies;",
    "#   dB of the peak.",
    "# verdict: ok, doubt (the accent may be another), bad (better left out).",
    "# remark: the ways of writing that were not kept, and why.",
]


def made_from(clip, engine_identity):
    """A short sum of everything a clip is made from."""
    parts = [str(VERSION), engine_identity, clip.reading, "" if clip.accent is None else str(clip.accent)]
    parts += ["%s=%s" % pair for pair in clip.texts] + ["sure=%d" % clip.sure] + clip.others
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def read_index(path):
    """{path on the card: row} of an index file. Empty when there is none, and when it was
    written with other columns: every clip is then made anew."""
    if not os.path.exists(path):
        return {}
    rows, _ = read_table(path, [])
    if rows and any(name not in rows[0] for name in INDEX_COLUMNS):
        print("%s has other columns than this tool writes: it is written anew" % display(path))
        return {}
    return {row["path"]: row for row in rows}


def write_index(path, rows, order):
    """rows: {path on the card: row}. order: the paths of the content; other rows follow."""
    known = [name for name in order if name in rows]
    seen = set(known)
    others = sorted(name for name in rows if name not in seen)
    lines = INDEX_HEAD + ["\t".join(INDEX_COLUMNS)]
    for name in known + others:
        lines.append("\t".join(str(rows[name].get(column, "")) for column in INDEX_COLUMNS))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    part = path + ".part"
    with open(part, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(part, path)


def mark_text(mark):
    return (mark[0] + " " + mark[1]).strip()


def row_of(clip, kept, remark, engine_identity):
    row = {"path": clip.path, "text": kept.text, "way": kept.way, "voice": clip.voice, "engine": engine_identity,
           "ms": kept.ms, "lead": int(round(kept.facts["lead"] * 1000)), "reading": clip.reading,
           "accent": "" if clip.accent is None else clip.accent, "verdict": kept.verdict(), "remark": remark,
           "made-from": made_from(clip, engine_identity)}
    for name in ("length", "sounds", "same", "pitch", "level"):
        row[name] = mark_text(kept.marks[name])
    return row


# ---------------------------------------------------------------------------------------------
# Making and checking
# ---------------------------------------------------------------------------------------------

def make_clip(clip, engine, out_dir):
    """Speaks a clip in every way of writing, keeps the best and gives its row for the index."""
    with tempfile.TemporaryDirectory(prefix="make_audio_") as work:
        def spoken(name, text):
            path = os.path.join(work, name + ".wav")
            engine.speak(text, path)
            return read_wav(path)

        closes = engine.closes(engine.identity())
        tries = [Try(clip, way, text, spoken("way%d" % number, text), closes)
                 for number, (way, text) in enumerate(clip.texts)]
        rivals = []
        if len(tries) > 1:
            rivals = [(reading, prepare(spoken("other%d" % number, reading))[0])
                      for number, reading in enumerate(clip.others)]
    kept, remark = choose(tries, compare(clip, tries, rivals))
    if kept.samples is None:
        raise Stop("%s: the engine gave a silent clip for %s" % (clip.path, kept.text))
    write_wav(clip_file(out_dir, clip.path), kept.samples)
    return row_of(clip, kept, remark, engine.identity())


def make_job(job):
    """make_clip for a worker process, which is handed plain values only."""
    clip, engine_name, options, out_dir = job
    try:
        return clip.path, make_clip(clip, ENGINES[engine_name](clip.voice, options), out_dir), None
    except Stop as problem:
        return clip.path, None, str(problem)


def measure_file(clip, path, lead, closes):
    """The marks of a clip that lies on the disk, as far as the file shows them. lead is what
    the index says of the silence that was cut away before the sound, in seconds; closes,
    whether the voice puts silence before k, t and p."""
    samples = read_wav(path)
    if not len(samples) or sound_span(samples) is None:
        return {"length": (FAIL, "silent")}, 0
    heard = Heard(samples, clip.voice)
    marks = {"length": check_length(heard, clip.beats, clip.sentence),
             "sounds": check_sounds(heard, clip.reading, clip.sentence, lead, closes),
             "pitch": check_pitch(heard, clip.beats, clip.accent),
             "level": check_level(samples, {"clipped": clipped(samples)}),
             "edges": check_edges(heard)}
    return marks, int(round(len(samples) * 1000.0 / RATE))


def check_job(job):
    clip, row, out_dir = job
    try:
        lead = int(row["lead"]) / 1000.0 if row["lead"].isdigit() else 0.0
        engine = ENGINES.get(row["engine"].split("/")[0], Engine)
        marks, ms = measure_file(clip, clip_file(out_dir, clip.path), lead, engine.closes(row["engine"]))
    except Stop as problem:
        return clip.path, [str(problem)]
    wrong = []
    if str(ms) != str(row["ms"]):
        wrong.append("is %d ms long, the index says %s" % (ms, row["ms"]))
    for name in ("length", "sounds", "pitch", "level"):
        if name in marks and mark_text(marks[name]) != row[name]:
            wrong.append("%s is \"%s\", the index says \"%s\"" % (name, mark_text(marks[name]), row[name]))
    if "edges" in marks and marks["edges"][0] != OK:
        wrong.append("silence at the ends is %s s" % marks["edges"][1])
    return clip.path, wrong


def display(path):
    try:
        relative = os.path.relpath(path, ROOT)
    except ValueError:
        return path
    return path if relative.startswith("..") else relative


def plural(count, word):
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def up_to_date(clip, rows, engine_identity, out_dir):
    row = rows.get(clip.path)
    return (row is not None and row["made-from"] == made_from(clip, engine_identity) and
            os.path.exists(clip_file(out_dir, clip.path)))


def run(jobs, function, workers):
    """Gives the results of function(job) as they come, from worker processes or, with one
    worker, from this one."""
    if workers <= 1 or len(jobs) <= 1:
        for job in jobs:
            yield function(job)
        return
    with ProcessPoolExecutor(workers) as pool:
        waiting = [pool.submit(function, job) for job in jobs]
        try:
            for future in as_completed(waiting):
                yield future.result()
        except BaseException:
            for future in waiting:
                future.cancel()
            raise


def summary(clips, rows, out_dir):
    """Lines that say what the index holds for these clips."""
    lines = []
    folders = []
    for clip in clips:
        if clip.folder not in folders:
            folders.append(clip.folder)
    total = 0
    lines.append("%-16s %6s %6s %6s %6s %8s" % ("folder", "clips", "ok", "doubt", "bad", "MB"))
    sums = [0, 0, 0, 0, 0.0]
    for folder in folders:
        mine = [rows[clip.path] for clip in clips if clip.folder == folder and clip.path in rows]
        size = 0
        for row in mine:
            path = clip_file(out_dir, row["path"])
            size += os.path.getsize(path) if os.path.exists(path) else 0
        counts = [sum(1 for row in mine if row["verdict"] == verdict) for verdict in ("ok", "doubt", "bad")]
        lines.append("%-16s %6d %6d %6d %6d %8.2f" % ((folder, len(mine)) + tuple(counts) + (size / 1e6,)))
        sums = [sums[0] + len(mine)] + [sums[i + 1] + counts[i] for i in range(3)] + [sums[4] + size / 1e6]
        total += sum(int(row["ms"]) for row in mine)
    lines.append("%-16s %6d %6d %6d %6d %8.2f" % (("all",) + tuple(sums)))
    lines.append("")
    lines.append("%-16s %6s %6s %6s %6s" % ("check", "ok", "unsure", "fail", "-"))
    mine = [rows[clip.path] for clip in clips if clip.path in rows]
    for name in ("length", "sounds", "same", "pitch", "level"):
        counts = [sum(1 for row in mine if (row[name].split() or [""])[0] == mark)
                  for mark in (OK, UNSURE, FAIL, NONE)]
        lines.append("%-16s %6d %6d %6d %6d" % ((name,) + tuple(counts)))
    lines.append("")
    lines.append("%.1f minutes of sound" % (total / 60000.0))
    return lines


def main(arguments=None):
    parser = argparse.ArgumentParser(description="Makes the sound clips of the memory card and checks them.")
    parser.add_argument("--out", metavar="DIR", help="the folder audio of the memory card (card/nihongo/audio)")
    parser.add_argument("--content", metavar="DIR", help="the folder with decks/, buddy.tsv and guide.tsv (content)")
    parser.add_argument("--only", metavar="NAME", action="append", default=[],
                        help="a deck id, buddy or guide; may be given more than once")
    parser.add_argument("--voice", choices=sorted(PITCH_RANGE), default="f", help="f female, m male (f)")
    parser.add_argument("--engine", choices=sorted(ENGINES), default=SayEngine.name, help="what speaks (say)")
    parser.add_argument("--check", action="store_true", help="measure the clips that are there, make nothing")
    parser.add_argument("--again", action="store_true", help="make clips anew even when they are up to date")
    parser.add_argument("--tidy", action="store_true",
                        help="remove the clips of this voice that the content does not ask for any more")
    parser.add_argument("--cache", metavar="DIR",
                        help="folder with jmdict_index.json, for the other readings of a word (local/cache)")
    parser.add_argument("--jobs", metavar="N", type=int, default=8, help="clips made at the same time (8)")
    for engine in ENGINES.values():
        engine.add_arguments(parser)
    args = parser.parse_args(arguments)

    try:
        return work(args)
    except Stop as problem:
        print("make_audio: %s" % problem, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nstopped. What is made is kept; start again to make the rest.", file=sys.stderr)
        return 130


def work(args):
    out_dir = os.path.abspath(args.out or os.path.join(ROOT, "card", "nihongo", "audio"))
    content_dir = os.path.abspath(args.content or os.path.join(ROOT, "content"))
    index_path = os.path.join(out_dir, "index.tsv")
    dictionary = read_dictionary(os.path.abspath(args.cache or os.path.join(ROOT, "local", "cache")))
    everything = all_clips(content_dir, args.voice, (), dictionary)
    clips = all_clips(content_dir, args.voice, args.only, dictionary)
    if dictionary is None:
        print("no dictionary: of the other readings of a word, only those the decks accept are tried")
    del dictionary
    engine = ENGINES[args.engine](args.voice, vars(args))
    rows = read_index(index_path)
    order = [clip.path for clip in everything]
    workers = max(1, args.jobs)
    mine = "%s/%s/" % (CARD_FOLDER, args.voice)
    left = sorted(name for name in rows if name.startswith(mine) and name not in set(order)
                  and (not args.only or name[len(mine):].split("/")[0] in args.only))

    if args.check:
        return check(clips, rows, left, out_dir, workers)

    if args.tidy:
        for path in left:
            if os.path.exists(clip_file(out_dir, path)):
                os.remove(clip_file(out_dir, path))
            del rows[path]
            print("removed %s" % path)

    todo = [clip for clip in clips if args.again or not up_to_date(clip, rows, engine.identity(), out_dir)]
    print("%s, %d up to date, %d to make with %s" % (plural(len(clips), "clip"), len(clips) - len(todo),
                                                  len(todo), engine.identity()))
    failed = []
    started = time.time()
    if todo:
        problem = engine.ready()
        if problem:
            raise Stop(problem)
        jobs = [(clip, args.engine, vars(args), out_dir) for clip in todo]
        done = 0
        written = time.time()
        try:
            for path, row, problem in run(jobs, make_job, workers):
                done += 1
                if problem:
                    failed.append(path)
                    rows.pop(path, None)
                    print("FAIL   %s" % problem)
                    continue
                rows[path] = row
                if row["verdict"] != "ok":
                    print("%-6s %s  %s  %s" % (row["verdict"], path, row["text"], describe(row)))
                if time.time() - written > 2:
                    write_index(index_path, rows, order)
                    written = time.time()
                if done % 50 == 0:
                    print("       %d of %d" % (done, len(todo)))
                sys.stdout.flush()
        finally:
            write_index(index_path, rows, order)
    elif args.tidy:
        write_index(index_path, rows, order)

    print("")
    print("\n".join(summary(clips, rows, out_dir)))
    if todo:
        print("made %s in %.0f s" % (plural(len(todo) - len(failed), "clip"), time.time() - started))
    print("index: %s" % display(index_path))
    if failed:
        print("%s could not be made" % plural(len(failed), "clip"), file=sys.stderr)
        return 1
    return 0


def describe(row):
    """The checks of a row that did not pass, and its remark."""
    parts = ["%s %s" % (name, row[name]) for name in ("length", "sounds", "same", "pitch", "level")
             if str(row[name]).split()[:1] not in ([OK], [NONE])]
    if row["remark"]:
        parts.append(row["remark"])
    return "; ".join(parts)


def check(clips, rows, left, out_dir, workers):
    """Measures the clips that are there and compares them with the index. left: the paths in
    the index that the content does not ask for any more."""
    missing = []
    stale = []
    jobs = []
    for clip in clips:
        row = rows.get(clip.path)
        if row is None or not os.path.exists(clip_file(out_dir, clip.path)):
            missing.append(clip.path)
        elif row["made-from"] != made_from(clip, row["engine"]):
            stale.append(clip.path)
        else:
            jobs.append((clip, row, out_dir))
    differing = 0
    for path, wrong in sorted(run(jobs, check_job, workers)):
        for line in wrong:
            print("%s: %s" % (path, line))
        differing += 1 if wrong else 0
    for path in missing:
        print("%s: missing" % path)
    for path in stale:
        print("%s: out of date, the card or the way of making clips has changed" % path)
    for path in left:
        print("%s: the content does not ask for it any more (--tidy removes it)" % path)
    print("")
    print("\n".join(summary(clips, rows, out_dir)))
    print("%s measured: %d as the index says, %d differing, %d missing, %d out of date" % (
        plural(len(jobs), "clip"), len(jobs) - differing, differing, len(missing), len(stale)))
    return 1 if differing or missing or stale else 0


if __name__ == "__main__":
    sys.exit(main())
