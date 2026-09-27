#!/usr/bin/env python3
"""Tests for tools/make_audio.py.

    python3 tools/tests/test_make_audio.py          # everything
    python3 tools/tests/test_make_audio.py pitch    # the tests whose name contains a word

No test needs a voice. Where the tool would ask a speech engine, the tests give it one of their
own, which makes every beat of a reading from tones and noise: a tone for what has voice, noise
for s and h, silence for k, t, p and the small っ, and a pitch that falls where the accent says.
It reads a printed word as the table READ_AS tells it, which is how a wrong reading is played.

Writes only into build/test_make_audio/.
"""
import array
import math
import os
import random
import shutil
import sys
import wave

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
ROOT = os.path.dirname(TOOLS)
WORK = os.path.join(ROOT, "build", "test_make_audio")

sys.path.insert(0, TOOLS)
import make_audio as ma  # noqa: E402

RATE = ma.RATE
BEAT = 0.15

DECK_HEAD = "id\tprompt\treading\taccent\taccepted\tgloss\tnote\tlevel\tsource"


class Failure(Exception):
    pass


def expect(condition, message):
    if not condition:
        raise Failure(message)


def same(got, want, what):
    if got != want:
        raise Failure("%s: got %r, expected %r" % (what, got, want))


def near(got, want, by, what):
    if abs(got - want) > by:
        raise Failure("%s: got %.3f, expected %.3f to within %.3f" % (what, got, want, by))


# ---------------------------------------------------------------------------------------------
# Sound made by the tests
# ---------------------------------------------------------------------------------------------

FORMANTS = {"a": (800, 1300), "i": (300, 2400), "u": (350, 1400), "e": (500, 2000), "o": (500, 900),
            "n": (250, 1100)}
ROWS = {"a": "あかさたなはまやらわがざだばぱゃぁ", "i": "いきしちにひみりぎじぢびぴぃ", "u": "うくすつぬふむゆるぐずづぶぷゅぅ",
        "e": "えけせてねへめれげぜでべぺぇ", "o": "おこそとのほもよろをごぞどぼぽょぉ", "n": "ん"}


def vowel_of(kana):
    for vowel, row in ROWS.items():
        if kana in row:
            return vowel
    return None


def voice(seconds, pitch, vowel="a", loud=6000.0, phase=None):
    """A voice-like tone: overtones of a pitch, the strongest near the two formants of a vowel.
    pitch is a number of hertz or a function of the time in seconds."""
    state = phase if phase is not None else [0.0]
    out = []
    first, second = FORMANTS[vowel]
    for index in range(int(seconds * RATE)):
        hertz = pitch(index / float(RATE)) if callable(pitch) else pitch
        state[0] += 2 * math.pi * hertz / RATE
        value = 0.0
        number = 1
        while number * hertz < 5000:
            here = number * hertz
            weight = 0.15 + 1 / (1 + ((here - first) / 150.0) ** 2) + 0.7 / (1 + ((here - second) / 200.0) ** 2)
            value += weight * math.sin(number * state[0])
            number += 1
        out.append(loud * value / 3.0)
    return out


def noise(seconds, loud=700.0, seed=1):
    dice = random.Random(seed)
    return [dice.uniform(-loud, loud) for _ in range(int(seconds * RATE))]


def silence(seconds):
    return [0.0] * int(seconds * RATE)


def faded(samples, seconds=0.008):
    count = min(int(seconds * RATE), len(samples) // 2)
    samples = list(samples)
    for index in range(count):
        samples[index] *= index / float(count)
        samples[-1 - index] *= index / float(count)
    return samples


def shorts(samples):
    return array.array("h", [int(max(-32767, min(32767, round(value)))) for value in samples])


def pitch_of(beat, beats, accent):
    """Hertz of a beat, counted from 1, in a word with an accent."""
    high, low = 260.0, 185.0
    if accent is None or accent == 0:
        value = 230.0 if beat == 1 else high
    elif beat <= accent:
        value = high if beat > 1 or accent == 1 else 230.0
    else:
        value = low
    return value * (1 - 0.01 * beat)


def speech(reading, accent=None):
    """What the engine of the tests says for a reading in kana. Like the speech of macOS it
    begins at once, but for k, t and p, before which it is silent for 80 ms."""
    beats = [beat for beat in ma.morae(reading) if beat is not None]
    out = silence(0.002)
    phase = [0.0]
    vowel = "a"
    for number, beat in enumerate(beats, 1):
        hertz = pitch_of(number, len(beats), accent)
        head = beat[0]
        vowel = vowel_of(beat[-1]) or vowel
        if head == "っ":
            out += silence(BEAT)
        elif head in ma.CLOSED:
            closure = 0.08 if number == 1 else 0.06
            out += silence(closure) + noise(0.015, 1500.0, number)
            out += faded(voice(BEAT - 0.075, hertz, vowel, phase=phase))
        elif head in ma.VOICELESS:
            out += faded(noise(0.09, 700.0, number)) + faded(voice(BEAT - 0.09, hertz, vowel, phase=phase))
        else:
            out += faded(voice(BEAT, hertz, vowel, phase=phase), 0.004)
    return shorts(out + silence(0.2))


READ_AS = {"出口": ("でぐち", 1), "行き": ("いき", 0), "大人": ("おとな", 0), "小人": ("こびと", 0),
           "禁煙": ("きんえん", 1), "でぐち": ("でぐち", 0), "デグチ": ("でぐち", 1), "へ": ("え", 0),
           "じゅうはちじ": ("じゅうわちじ", None)}
ACCENTS = {"おとな": 0, "きんえん": 2, "キンエン": 0, "ビール": 1, "びーる": 0}


class TestEngine(ma.Engine):
    """Speaks with tones. It counts what it was asked for, and can be told to stop."""
    name = "tones"
    asked = []
    stop_at = None

    def identity(self):
        return "tones/1"

    @classmethod
    def closes(cls, identity):
        return True

    def speak(self, text, path):
        TestEngine.asked.append(text)
        if TestEngine.stop_at is not None and len(TestEngine.asked) >= TestEngine.stop_at:
            raise KeyboardInterrupt()
        reading, accent = READ_AS.get(text, (text, ACCENTS.get(text)))
        save(path, speech(reading, accent))


def save(path, samples, rate=RATE, channels=1, width=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(width)
        handle.setframerate(rate)
        handle.writeframes(samples.tobytes() if width == 2 else bytes(len(samples)))


def heard(samples):
    ready, facts = ma.prepare(shorts(samples))
    return ma.Heard(ready, "f"), facts


# ---------------------------------------------------------------------------------------------
# Content made by the tests
# ---------------------------------------------------------------------------------------------

SIGNS = ["# name-ja: かんばん", "# name-en: signs", "# kind: word", DECK_HEAD,
         "sign-deguchi\t出口\tでぐち\t1\t\texit\t\t2\tJMdict",
         "sign-yuki\t行き\tゆき\t0\tいき\tbound for\t\t2\tJMdict",
         "sign-otona\t大人\tおとな\t0\tだいにん\tadult\t\t2\tJMdict",
         "sign-shounin\t小人\tしょうにん\t0\tこども\tchild\t\t2\tJMdict",
         "sign-kin-en\t禁煙\tきんえん\t0\t\tno smoking\t\t3\tJMdict",
         "sign-oshiri\tおしり\tおしり\t\t\tbottom\t\t1\tJMdict"]
WORDS = ["# name-ja: カタカナご", "# name-en: katakana words", "# kind: word", DECK_HEAD,
         "kata-biiru\tビール\tビール\t1\t\tbeer\t\t1\tJMdict"]
KANA = ["# name-ja: ひらがな", "# name-en: hiragana", "# kind: kana", DECK_HEAD,
        "hiragana-a\tあ\tあ\t\t\ta\t\t1\t", "hiragana-he\tへ\tへ\t\t\the\t\t1\t",
        "hiragana-kya\tきゃ\tきゃ\t\t\tkya\t\t1\t"]
NUMBERS = ["# name-ja: すうじ", "# name-en: numbers", "# kind: number", DECK_HEAD,
           "num-yen-100\t¥100\tひゃくえん\t\t\t100 yen\t\t1\tnumber_reading",
           "num-time-1800\t18:00\tじゅうはちじ\t\t\t6 pm\t\t1\tnumber_reading",
           "num-date-0120\t1/20\tいちがつはつか\t\t\t20 January\t\t1\tnumber_reading"]
BUDDY = ["# What the buddy says.", "id\tmood\tja\ten",
         "buddy-greeting-01\tgreeting\tこんにちは！\tHello!",
         "buddy-start-01\tstart\tさあ、 はじめよう。\tLet us begin."]
GUIDE = ["id\ttitle\tbody\tclips", "guide-vowels\tFive vowels\ta i u e o\tあ|い|う",
         "guide-long\tLong and short\tobasan, obaasan\tおばさん|おばあさん", "guide-none\tNothing to hear\ttext\t"]


def content(name, guide=False, signs=SIGNS):
    """A folder like content/, made anew."""
    folder = os.path.join(WORK, name, "content")
    shutil.rmtree(os.path.join(WORK, name), ignore_errors=True)
    os.makedirs(os.path.join(folder, "decks"))
    files = {"decks/signs.tsv": signs, "decks/katakana-words.tsv": WORDS, "decks/hiragana.tsv": KANA,
             "decks/numbers.tsv": NUMBERS, "buddy.tsv": BUDDY}
    if guide:
        files["guide.tsv"] = GUIDE
    for path, lines in files.items():
        write(os.path.join(folder, path), "\n".join(lines) + "\n")
    return folder


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def tool(name, *arguments):
    """Runs the tool in this process with the engine of the tests. Gives (exit code, what it
    printed, what the engine was asked to say)."""
    ma.ENGINES[TestEngine.name] = TestEngine
    TestEngine.asked = []
    lines = []

    class Catch:
        def write(self, text):
            lines.append(text)

        def flush(self):
            pass

    keep = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = Catch()
    try:
        code = ma.main(["--engine", TestEngine.name, "--jobs", "1", "--cache", os.path.join(WORK, name, "none"),
                        "--content", os.path.join(WORK, name, "content"),
                        "--out", os.path.join(WORK, name, "audio")] + list(arguments))
    finally:
        sys.stdout, sys.stderr = keep
        TestEngine.stop_at = None
    return code, "".join(lines), list(TestEngine.asked)


def index_of(name):
    return ma.read_index(os.path.join(WORK, name, "audio", "index.tsv"))


# ---------------------------------------------------------------------------------------------
# Kana
# ---------------------------------------------------------------------------------------------

def test_beats():
    for text, count in (("あ", 1), ("きゃ", 1), ("でぐち", 3), ("きって", 3), ("コーヒー", 4), ("しんかんせん", 6),
                        ("ティッシュ", 3), ("また あえたね。", 6), ("さあ、 はじめよう。", 7), ("ぁ", 1), ("", 0)):
        same(ma.beat_count(text), count, "beats of " + text)
    same(ma.morae("きょうは なに？"), ["きょ", "う", "は", None, "な", "に"], "morae with a space and a mark")
    same(ma.to_katakana("でぐち"), "デグチ", "katakana")
    same(ma.to_hiragana("コーヒー"), "こーひー", "hiragana keeps the long mark")


def test_where_a_reading_stops_the_voice():
    same(ma.expected_gaps("ななにん"), [], "no voiceless sound in ななにん")
    same(ma.expected_gaps("あさ"), [(1, 1 + ma.ONSET, True)], "s in あさ, whose last vowel is not whispered")
    same(ma.expected_gaps("です"), [(1, 1 + ma.ONSET, True), (1 + ma.ONSET, 2, False)], "the u of です may be whispered")
    same(ma.expected_gaps("きって"), [(0, ma.ONSET, True), (ma.ONSET, 1, False), (1, 2, True), (2, 2 + ma.ONSET, True)],
         "きって")
    same(ma.expected_gaps("ベッド"), [(1, 2, False)], "a small っ before a voiced sound may keep the voice")
    same(ma.expected_gaps("ごはん"), [(1, 1 + ma.ONSET, False)], "h inside a word may keep the voice")
    same(ma.expected_gaps("はし")[0], (0, ma.ONSET, True), "h at the start must be heard")
    gaps = ma.expected_gaps("これは いい？", True)
    same(gaps, [(0, ma.ONSET, True), (2, 2 + ma.ONSET, False), (3, 3, False)],
         "in a line は at the end of a word may be the particle, and a space may be a pause")


# ---------------------------------------------------------------------------------------------
# Reading the content
# ---------------------------------------------------------------------------------------------

def test_the_decks_are_read():
    folder = content("decks")
    clips = ma.all_clips(folder, "f")
    same([clip.path for clip in clips],
         ["/audio/f/hiragana/hiragana-a.wav", "/audio/f/hiragana/hiragana-he.wav", "/audio/f/hiragana/hiragana-kya.wav",
          "/audio/f/katakana-words/kata-biiru.wav", "/audio/f/numbers/num-yen-100.wav",
          "/audio/f/numbers/num-time-1800.wav", "/audio/f/numbers/num-date-0120.wav",
          "/audio/f/signs/sign-deguchi.wav", "/audio/f/signs/sign-yuki.wav", "/audio/f/signs/sign-otona.wav",
          "/audio/f/signs/sign-shounin.wav", "/audio/f/signs/sign-kin-en.wav", "/audio/f/signs/sign-oshiri.wav",
          "/audio/f/buddy/buddy-greeting-01.wav", "/audio/f/buddy/buddy-start-01.wav"], "paths")
    by_name = {clip.name: clip for clip in clips}
    exit_ = by_name["sign-deguchi"]
    same((exit_.reading, exit_.accent, exit_.beats, exit_.kind), ("でぐち", 1, 3, "word"), "the card of 出口")
    same(exit_.texts, [("word", "出口"), ("kana", "でぐち"), ("katakana", "デグチ")], "ways of writing 出口")
    same(exit_.sure, 1, "the sure way of 出口")
    same(by_name["sign-yuki"].others, ["いき"], "other readings of 行き")
    same(by_name["sign-oshiri"].texts, [("kana", "おしり"), ("katakana", "オシリ")], "a word in kana")
    same(by_name["sign-oshiri"].accent, None, "no accent")
    same(by_name["kata-biiru"].texts, [("kana", "ビール"), ("hiragana", "びーる")], "a katakana word")
    same(by_name["hiragana-he"].texts, [("katakana", "ヘ"), ("hiragana", "へ")], "a single kana")
    same(by_name["hiragana-he"].sure, 0, "katakana is the sure way of a single kana")
    same(by_name["num-yen-100"].texts, [("kana", "ひゃくえん"), ("katakana", "ヒャクエン")], "a number")
    same(by_name["num-yen-100"].kind, "number", "kind of a number")
    line = by_name["buddy-start-01"]
    same((line.texts, line.sentence, line.beats), ([("kana", "さあ、 はじめよう。")], True, 7), "a line of the buddy")
    same([clip.path for clip in ma.all_clips(folder, "m", ["buddy"])],
         ["/audio/m/buddy/buddy-greeting-01.wav", "/audio/m/buddy/buddy-start-01.wav"], "the male voice, one folder")


def test_the_dictionary_gives_other_readings():
    dictionary = {"行き": [{"kana": ["いき", "ゆき"]}], "小人": [{"kana": ["しょうにん"]}, {"kana": ["こびと", "しょうじん"]}],
                  "開く": [{"kana": ["ひらく", "ヒラく"]}, {"kana": ["あく"]}]}
    same(ma.other_readings("行き", "ゆき", "いき", dictionary), ["いき"], "no reading twice")
    same(ma.other_readings("小人", "しょうにん", "こども", dictionary), ["こども", "こびと", "しょうじん"], "小人")
    same(ma.other_readings("開く", "ひらく", "", dictionary), ["あく"], "the reading itself in katakana is left out")
    same(ma.other_readings("出口", "でぐち", "", None), [], "without a dictionary")
    many = {"小": [{"kana": ["こ", "お", "ささ", "さざ", "さ", "ちい", "しょう", "ちっ"]}]}
    same(len(ma.other_readings("小", "しょう", "", many)), ma.RIVALS, "no more than RIVALS")


def test_the_guide_is_taken_up_when_it_is_there():
    without = ma.all_clips(content("guide-0"), "f")
    expect(not any(clip.folder == "guide" for clip in without), "guide clips without a guide file")
    clips = [clip for clip in ma.all_clips(content("guide-1", guide=True), "f") if clip.folder == "guide"]
    same([(clip.path, clip.reading) for clip in clips],
         [("/audio/f/guide/guide-vowels-1.wav", "あ"), ("/audio/f/guide/guide-vowels-2.wav", "い"),
          ("/audio/f/guide/guide-vowels-3.wav", "う"), ("/audio/f/guide/guide-long-1.wav", "おばさん"),
          ("/audio/f/guide/guide-long-2.wav", "おばあさん")], "guide clips")
    same(clips[0].texts, [("katakana", "ア"), ("hiragana", "あ")], "a single kana of the guide")
    same(clips[3].texts, [("kana", "おばさん"), ("katakana", "オバサン")], "a word of the guide")


def test_mistakes_in_the_content_stop_the_tool():
    cases = [("sign-x\t出口\tdeguchi\t1\t\texit\t\t2\tJMdict", "not kana only"),
             ("sign-x\t出口\tでぐち\t4\t\texit\t\t2\tJMdict", "does not fit"),
             ("sign-x\t出口\tでぐち\tone\t\texit\t\t2\tJMdict", "does not fit"),
             ("sign-x\t出口\t\t1\t\texit\t\t2\tJMdict", "empty"),
             ("sign-x\t出口\tでぐち\t1\texit", "columns"),
             ("kata-biiru\tビール\tビール\t1\t\tbeer\t\t1\tJMdict", None)]
    for row, words in cases:
        folder = content("mistake", signs=SIGNS[:4] + [row])
        try:
            ma.all_clips(folder, "f")
        except ma.Stop as problem:
            expect(words and words in str(problem), "%r gave \"%s\"" % (row, problem))
        else:
            expect(words is None, "%r was taken" % row)
    try:
        ma.all_clips(content("mistake"), "f", ["sings"])
    except ma.Stop as problem:
        expect("no such deck" in str(problem) and "signs" in str(problem), str(problem))
    else:
        raise Failure("--only with a deck that is not there was taken")


def test_the_real_content_is_read():
    folder = os.path.join(ROOT, "content")
    clips = ma.all_clips(folder, "f")
    rows = 0
    for name in os.listdir(os.path.join(folder, "decks")):
        if name.endswith(".tsv"):
            lines = [line for line in read(os.path.join(folder, "decks", name)).splitlines()
                     if line.strip() and not line.startswith("#")]
            rows += len(lines) - 1
    same(sum(1 for clip in clips if clip.folder not in ("buddy", "guide")), rows, "one clip for every card")
    same(len(set(clip.path for clip in clips)), len(clips), "every clip has a path of its own")
    for clip in clips:
        expect(clip.beats >= 1, "%s has no beats" % clip.path)
        expect(clip.texts[clip.sure][0] in ("kana", "katakana"), "%s: the sure way is %s" % (clip.path, clip.texts))
        expect(all(text for _, text in clip.texts), "%s has an empty text" % clip.path)


def test_paths():
    clip = ma.Clip("m", "signs", "sign-eki", "word", "えき", 1, [("kana", "えき")])
    same(clip.path, "/audio/m/signs/sign-eki.wav", "path on the card")
    same(ma.clip_file(os.path.join("x", "audio"), clip.path), os.path.join("x", "audio", "m", "signs", "sign-eki.wav"),
         "file on this computer")


# ---------------------------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------------------------

def test_wav_files():
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(WORK, "wav", "round.wav")
    samples = shorts([0, 1, -1, 32767, -32768 + 1, 1234])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ma.write_wav(path, samples)
    same(list(ma.read_wav(path)), list(samples), "what was written")
    same(os.path.getsize(path), 44 + 2 * len(samples), "a plain header of 44 bytes")
    expect(not os.path.exists(path + ".part"), "the second file was left behind")
    for name, rate, channels, width in (("rate", 22050, 1, 2), ("stereo", RATE, 2, 2), ("bytes", RATE, 1, 1)):
        other = os.path.join(WORK, "wav", name + ".wav")
        save(other, shorts([0] * 64), rate, channels, width)
        try:
            ma.read_wav(other)
        except ma.Stop:
            continue
        raise Failure("a file with %d Hz, %d channels, %d bytes was read" % (rate, channels, width))
    write(os.path.join(WORK, "wav", "text.wav"), "not a sound")
    try:
        ma.read_wav(os.path.join(WORK, "wav", "text.wav"))
    except ma.Stop:
        return
    raise Failure("a text file was read as sound")


def test_silence_is_cut_to_40_ms():
    tone = faded(voice(0.5, 220.0))
    for before, after in ((0.3, 0.2), (0.0, 0.0), (0.01, 0.5), (1.0, 0.003)):
        ready, facts = ma.prepare(shorts(silence(before) + tone + silence(after)))
        span = ma.sound_span(ready)
        near(span[0] / float(RATE), 0.040, 0.006, "silence before, from %.3f s" % before)
        near((len(ready) - span[1]) / float(RATE), 0.040, 0.006, "silence after, from %.3f s" % after)
        near(len(ready) / float(RATE), 0.58, 0.012, "length")
        near(facts["lead"], before, 0.006, "what was cut away before")
        same(ma.check_edges(ma.Heard(ready))[0], ma.OK, "the check of the ends")


def test_a_weak_start_and_end_are_kept():
    breath = faded(noise(0.08, 120.0))
    ready, _ = ma.prepare(shorts(silence(0.2) + breath + voice(0.3, 220.0) + breath + silence(0.2)))
    near(len(ready) / float(RATE), 0.08 + 0.3 + 0.08 + 0.08, 0.015, "length with the breath at both ends")


def test_a_click_is_not_sound():
    click = [0.0] * 40 + [3000.0, -3000.0, 2000.0] + [0.0] * 40
    ready, facts = ma.prepare(shorts(click + silence(0.3) + faded(voice(0.3, 220.0)) + silence(0.3) + click))
    near(len(ready) / float(RATE), 0.38, 0.012, "length without the clicks")
    expect(max(abs(v) for v in ready[:int(0.030 * RATE)]) < 200, "the click is still before the sound")


def test_the_noise_at_the_start_is_taken_out():
    start = noise(0.03, 40.0)
    ready, facts = ma.prepare(shorts(start + silence(0.08) + faded(voice(0.3, 220.0)) + silence(0.1)))
    near(facts["lead"], 0.11, 0.006, "the silence before the sound, the noise being none")
    near(len(ready) / float(RATE), 0.38, 0.012, "length")
    same(max(abs(v) for v in ready[:int(0.030 * RATE)]), 0, "what is left of the noise")
    # A breath that leads into the sound is no such noise.
    ready, facts = ma.prepare(shorts(noise(0.06, 40.0) + faded(voice(0.3, 220.0)) + silence(0.1)))
    near(facts["lead"], 0.0, 0.006, "a weak start without silence after it is kept")


def test_a_silent_clip():
    ready, facts = ma.prepare(shorts(silence(0.5)))
    same(ready, None, "samples of a silent clip")
    ready, facts = ma.prepare(shorts(noise(0.5, 3.0)))
    same(ready, None, "samples of a clip that only hisses")
    same(ma.prepare(shorts([]))[0], None, "samples of an empty clip")


def test_every_clip_gets_the_same_peak():
    wanted = int(round(ma.PEAK * 32767))
    near(20 * math.log10(wanted / 32767.0), -1.0, 0.01, "the peak in dB")
    for loud in (300.0, 3000.0, 12000.0):
        ready, facts = ma.prepare(shorts(silence(0.1) + faded(voice(0.3, 220.0, loud=loud)) + silence(0.1)))
        near(max(abs(min(ready)), max(ready)), wanted, 1, "peak of a clip made with %d" % loud)
        same(ma.check_level(ready, facts), (ma.OK, "-1.0"), "the check of the level")


def test_clipping_is_found():
    clean = shorts(faded(voice(0.3, 220.0, loud=6000.0)))
    same(ma.clipped(clean), 0, "flat tops in a clean tone")
    top = 0.6 * max(clean)
    cut = shorts([max(-top, min(top, value)) for value in clean])
    expect(ma.clipped(cut) > 100, "flat tops in a clipped tone: %d" % ma.clipped(cut))
    ready, facts = ma.prepare(cut)
    same(ma.check_level(ready, facts)[0], ma.FAIL, "the check of the level of a clipped clip")
    expect(ma.clipped(ready) > 100, "flat tops are still found after levelling: %d" % ma.clipped(ready))


# ---------------------------------------------------------------------------------------------
# Pitch
# ---------------------------------------------------------------------------------------------

def test_the_pitch_of_a_tone_is_found():
    for hertz in (110.0, 150.0, 220.0, 261.6, 330.0, 440.0):
        track = ma.pitch_track(shorts(silence(0.1) + faded(voice(0.4, hertz)) + silence(0.1)))
        found = [value for state, value in track if state == "v"]
        expect(35 <= len(found) <= 44, "%d Hz: %d frames with voice in 0.4 s" % (hertz, len(found)))
        for value in found[2:-2]:
            near(12 * math.log(value / hertz, 2), 0.0, 0.25, "semitones off at %d Hz" % hertz)
    low = ma.pitch_track(shorts(faded(voice(0.4, 80.0))), *ma.PITCH_RANGE["m"])
    found = [value for state, value in low if state == "v"]
    expect(len(found) > 30, "80 Hz in the range of the male voice: %d frames" % len(found))
    near(sorted(found)[len(found) // 2], 80.0, 1.5, "80 Hz in the range of the male voice")


def test_silence_and_noise_have_no_pitch():
    tone = faded(voice(0.2, 220.0))
    track = ma.pitch_track(shorts(tone + silence(0.2) + noise(0.2, 900.0) + tone))
    states = "".join(state for state, _ in track)
    expect("v" not in states[24:56], "voice found in silence and noise: %s" % states)
    expect(states[24:36].count("s") >= 10, "silence not found: %s" % states)
    expect(states[44:56].count("u") >= 10, "noise not found: %s" % states)
    expect(states[2:16].count("v") >= 13 and states[64:76].count("v") >= 11, "voice not found: %s" % states)


def test_where_the_voice_stops():
    found, _ = heard(faded(voice(0.3, 220.0)) + silence(0.1) + faded(voice(0.3, 220.0)) + noise(0.08, 600.0)
                     + faded(voice(0.2, 200.0)) + silence(0.2))
    gaps = [gap for gap in found.gaps() if gap[1] - gap[0] >= 0.03]
    same(len(gaps), 2, "stops of the voice in %s" % found.gaps())
    near(gaps[0][0], 0.30, 0.03, "start of the first stop")
    near(gaps[0][1], 0.40, 0.03, "end of the first stop")
    near(gaps[1][0], 0.70, 0.03, "start of the second stop")
    near(gaps[1][1], 0.78, 0.03, "end of the second stop")
    near(found.sound, 0.98, 0.02, "seconds of sound")


def falling(seconds, high, low, at, over=0.03):
    def pitch(when):
        if when <= at - over / 2:
            return high
        if when >= at + over / 2:
            return low
        return high + (low - high) * (when - (at - over / 2)) / over
    return faded(voice(seconds, pitch))


def test_a_tone_that_falls_after_a_third_is_found_to_fall_there():
    found, _ = heard(silence(0.1) + falling(0.9, 260.0, 185.0, 0.3) + silence(0.1))
    falls = ma.falls(found, 6)
    same(len(falls), 1, "falls in %s" % falls)
    near(falls[0][0], 2.0, 0.2, "the beat after which it falls")
    near(falls[0][1], 12 * math.log(260.0 / 185.0, 2), 0.4, "semitones of the fall")
    same(ma.check_pitch(found, 6, 2)[0], ma.OK, "accent 2 of 6 beats")
    same(ma.check_pitch(found, 6, 1)[0], ma.OK, "accent 1: the fall may come a beat late")
    same(ma.check_pitch(found, 6, 4)[0], ma.FAIL, "accent 4")
    same(ma.check_pitch(found, 6, 0)[0], ma.FAIL, "accent 0")
    same(ma.check_pitch(found, 6, 6)[0], ma.FAIL, "accent 6, which falls after the word")
    same(ma.check_pitch(found, 6, None), (ma.NONE, ""), "a card without accent")


def test_a_fall_is_found_through_a_stop_of_the_voice():
    found, _ = heard(silence(0.1) + faded(voice(0.28, 260.0)) + silence(0.09) + faded(voice(0.53, 185.0))
                     + silence(0.1))
    falls = ma.falls(found, 6)
    same(len(falls), 1, "falls in %s" % falls)
    near(falls[0][0], 2.2, 0.35, "the beat after which it falls")
    same(ma.check_pitch(found, 6, 2)[0], ma.OK, "accent 2 of 6 beats")


def test_a_flat_tone_and_the_sinking_of_the_last_beat():
    flat, _ = heard(silence(0.1) + faded(voice(0.6, lambda when: 240.0 - 20.0 * when)) + silence(0.1))
    same(ma.falls(flat, 4), [], "falls of a tone that sinks by a semitone")
    same(ma.check_pitch(flat, 4, 0)[0], ma.OK, "accent 0 on a flat tone")
    same(ma.check_pitch(flat, 4, 1)[0], ma.FAIL, "accent 1 on a flat tone")
    same(ma.check_pitch(flat, 4, 2)[0], ma.FAIL, "accent 2 on a flat tone")
    sinking, _ = heard(silence(0.1) + falling(0.6, 250.0, 180.0, 0.5) + silence(0.1))
    same(ma.check_pitch(sinking, 4, 0)[0], ma.OK, "accent 0: a fall in the last beat is how a word ends")
    same(ma.check_pitch(sinking, 4, 3)[0], ma.OK, "accent 3 of 4 cannot be told from accent 0")
    same(ma.check_pitch(sinking, 4, 1)[0], ma.FAIL, "accent 1 when the pitch falls in the last beat only")
    early, _ = heard(silence(0.1) + falling(0.6, 250.0, 180.0, 0.17) + silence(0.1))
    same(ma.check_pitch(early, 4, 0)[0], ma.FAIL, "accent 0 when the pitch falls after the first beat")
    same(ma.check_pitch(early, 4, 1)[0], ma.OK, "accent 1 when the pitch falls after the first beat")


def test_words_of_two_beats():
    fall, _ = heard(silence(0.1) + falling(0.3, 250.0, 190.0, 0.15) + silence(0.1))
    same(ma.check_pitch(fall, 2, 1)[0], ma.OK, "accent 1 on a fall")
    same(ma.check_pitch(fall, 2, 0)[0], ma.FAIL, "accent 0 on a fall")
    rise, _ = heard(silence(0.1) + falling(0.3, 200.0, 240.0, 0.15) + silence(0.1))
    same(ma.check_pitch(rise, 2, 1)[0], ma.FAIL, "accent 1 on a rise")
    same(ma.check_pitch(rise, 2, 0)[0], ma.OK, "accent 0 on a rise")
    same(ma.check_pitch(rise, 1, 1), (ma.NONE, ""), "a single beat has no accent to hear")


# ---------------------------------------------------------------------------------------------
# The checks on speech made by the tests
# ---------------------------------------------------------------------------------------------

def tried(reading, said, accent=None, said_accent=None, kind="word"):
    clip = ma.Clip("f", "x", "x", kind, reading, accent, [("kana", reading)])
    return ma.Try(clip, "kana", reading, speech(said, accent if said_accent is None else said_accent))


def test_the_length_tells_a_cut_clip():
    same(tried("しんかんせん", "しんかんせん").marks["length"][0], ma.OK, "the whole word")
    near(float(tried("しんかんせん", "しんかんせん").marks["length"][1]), BEAT, 0.02, "seconds a beat")
    same(tried("しんかんせん", "しん").marks["length"][0], ma.FAIL, "a third of the word")
    same(tried("えき", "えきのみなみぐち").marks["length"][0], ma.FAIL, "four times the word")
    clip = ma.Clip("f", "x", "x", "word", "えき", 1, [("kana", "えき")])
    silent = ma.Try(clip, "kana", "えき", shorts(silence(0.5)))
    same((silent.marks["length"], silent.verdict()), ((ma.FAIL, "silent"), "bad"), "a silent clip")


def test_pauses_between_the_words_of_a_line_are_not_speech():
    clip = ma.Clip("f", "buddy", "x", "line", "まあ、 いいよ。", None, [("kana", "まあ、 いいよ。")])
    samples = speech("まあ")[:-int(0.2 * RATE)] + shorts(silence(0.3)) + speech("いいよ")
    one = ma.Try(clip, "kana", clip.reading, samples)
    same(one.marks["length"][0], ma.OK, "length of a line with a pause: %s" % (one.marks["length"],))
    near(float(one.marks["length"][1]), BEAT, 0.025, "seconds a beat, the pause left out")
    same(one.marks["sounds"], (ma.OK, ""), "sounds of a line with a pause")
    word = ma.Clip("f", "x", "x", "word", "まあいいよ", None, [("kana", "まあいいよ")])
    same(ma.Try(word, "kana", word.reading, samples).marks["sounds"][0], ma.FAIL, "the same pause inside a word")


def test_the_sounds_tell_another_reading():
    for reading in ("しちにん", "ななにん", "きって", "でぐち", "かたみち", "おとな", "ビール", "はし", "あ", "へ", "きゃ"):
        same(tried(reading, reading).marks["sounds"], (ma.OK, ""), "sounds of " + reading)
    wrong = [("しちにん", "ななにん", "voice at beat 1"), ("ななにん", "しちにん", "no voice at beat 1"),
             ("へ", "え", "voice at beat 1"), ("はし", "わし", "voice at beat 1"),
             ("しょうにん", "こびと", "k, t or p at the start"), ("おおもり", "だいせい", "no voice at beat 3"),
             ("でぐち", "てぐち", "k, t or p at the start"), ("おとな", "おんな", "voice at beat 2"),
             ("あし", "はし", "no voice at beat 1")]
    for reading, said, words in wrong:
        mark = tried(reading, said).marks["sounds"]
        expect(mark[0] == ma.FAIL and words in mark[1], "%s said as %s: %s" % (reading, said, mark))


def test_what_the_sounds_cannot_tell():
    """Where the voice stops is all that "sounds" knows. These pass, and are here so that whoever
    makes the check sharper sees what it gains."""
    for reading, said in (("かど", "かと"), ("きて", "きって"), ("みなみ", "みなに"), ("ゆき", "いき")):
        same(tried(reading, said).marks["sounds"], (ma.OK, ""), "%s said as %s" % (reading, said))


def test_a_voice_that_creaks_is_voice():
    dice = random.Random(7)
    steps = [dice.choice((85.0, 100.0, 125.0, 150.0)) for _ in range(200)]
    creak = faded(voice(0.3, lambda when: steps[int(when / 0.006)]))
    track = ma.pitch_track(shorts(faded(voice(0.2, 220.0)) + creak + silence(0.1) + noise(0.2, 2500.0)))
    states = "".join(state for state, _ in track)
    expect(states[22:48].count("r") + states[22:48].count("v") >= 24, "the creak is not voice: %s" % states)
    expect(states[22:48].count("r") >= 8, "the creak has a pitch: %s" % states)
    expect(states[62:78].count("u") >= 15, "loud noise is voice: %s" % states)
    found, _ = heard(faded(voice(0.2, 220.0)) + creak + faded(voice(0.2, 180.0)) + silence(0.1))
    same([gap for gap in found.gaps() if gap[1] - gap[0] > 0.03], [], "stops of the voice in a creak")
    same(ma.check_sounds(found, "あおい")[0], ma.OK, "a word that creaks in the middle")


def test_how_a_voice_dies_away_is_not_judged():
    breath = faded(noise(0.12, 500.0))
    word = faded(voice(0.15, 230.0)) + faded(voice(0.15, 200.0, "e"))
    found, _ = heard(word + breath + silence(0.1))
    expect(found.gaps() and found.gaps()[-1][1] - found.gaps()[-1][0] > 0.08, "no breath at the end: %s" % found.gaps())
    same(ma.check_sounds(found, "あめ"), (ma.OK, ""), "a breath after the last voice")
    found, _ = heard(faded(voice(0.15, 230.0)) + breath + faded(voice(0.15, 200.0, "e")) + silence(0.1))
    same(ma.check_sounds(found, "あめ")[0], ma.FAIL, "the same breath in the middle")
    found, _ = heard(faded(voice(0.15, 230.0)) + faded(voice(0.15, 200.0, "e")) + silence(0.1))
    same(ma.check_sounds(found, "あす")[0], ma.FAIL, "s at the end must still be heard")


def test_the_silence_before_a_stop_counts_as_its_sound():
    clip = ma.Clip("f", "x", "x", "word", "かな", None, [("kana", "かな")])
    samples = shorts(silence(0.1) + noise(0.01, 1500.0) + faded(voice(0.13, 230.0)) + faded(voice(0.15, 230.0), 0.004)
                     + silence(0.1))
    found = ma.Heard(ma.prepare(samples)[0], "f")
    same(ma.check_sounds(found, "かな", False, 0.100, True), (ma.OK, ""), "with the silence the engine put before it")
    same(ma.check_sounds(found, "かな", False, 0.0, True)[0], ma.FAIL, "without it, from a voice that would put it")
    same(ma.check_sounds(found, "かな", False, 0.0, False), (ma.OK, ""), "without it, from a voice that does not")
    same(ma.check_sounds(found, "あな", False, 0.100), (ma.FAIL, "k, t or p at the start"), "when no stop is read")
    same(ma.check_sounds(found, "さな", False, 0.0, False)[0], ma.FAIL, "s must be heard from every voice")
    same(ma.Try(clip, "kana", "かな", samples).marks["sounds"], (ma.OK, ""), "as the tool does it")


def test_the_pitch_of_speech():
    same(tried("でぐち", "でぐち", 1).marks["pitch"][0], ma.OK, "でぐち with accent 1")
    same(tried("でぐち", "でぐち", 1, 0).marks["pitch"][0], ma.FAIL, "でぐち said flat")
    same(tried("おとな", "おとな", 0).marks["pitch"][0], ma.OK, "おとな said flat")
    same(tried("おとな", "おとな", 0, 1).marks["pitch"][0], ma.FAIL, "おとな said with accent 1")
    same(tried("しんかんせん", "しんかんせん", 3).marks["pitch"][0], ma.OK, "しんかんせん with accent 3")
    same(tried("しんかんせん", "しんかんせん", 3, 1).marks["pitch"][0], ma.FAIL, "しんかんせん said with accent 1")
    same(tried("しんかんせん", "しんかんせん", 3, 0).marks["pitch"][0], ma.FAIL, "しんかんせん said flat")
    same(tried("ひゃくえん", "ひゃくえん").marks["pitch"], (ma.NONE, ""), "a card without accent")


def test_two_clips_are_compared():
    def colours(reading, accent=None):
        return ma.colours(ma.prepare(speech(reading, accent))[0])

    same(ma.distance(colours("でぐち"), colours("でぐち")), (0.0, 0.0), "a clip against itself")
    mean, worst = ma.distance(colours("でぐち", 1), colours("でぐち", 0))
    expect(mean <= 1.0 and worst <= 2.5, "the same word with another accent: %.1f/%.1f" % (mean, worst))
    same(ma.check_same(colours("でぐち", 1), colours("でぐち", 0))[0], ma.OK, "the same word with another accent")
    for one, other in (("しょうにん", "こびと"), ("ゆき", "いき"), ("おとな", "だいにん"), ("あ", "い"), ("きんえん", "きつえん")):
        mark = ma.check_same(colours(one), colours(other))
        expect(mark[0] != ma.OK, "%s against %s: %s" % (one, other, mark))
    same(ma.check_same(colours("あ"), colours("あいうえおかきくけこさしすせそ")), (ma.FAIL, "lengths"), "a clip ten times as long")
    same(ma.distance([], colours("あ")), None, "nothing against a clip")


def test_another_reading_that_is_nearer_is_found():
    def colours(reading, accent=None):
        return ma.colours(ma.prepare(speech(reading, accent))[0])

    said = colours("だついしょ", 0)
    measure = colours("だついじょ", 0)
    mark = ma.check_same(said, measure, [("だついしょ", colours("だついしょ", 1))])
    expect(mark[0] == ma.FAIL and "read だついしょ" in mark[1], "だついしょ for だついじょ: %s" % (mark,))
    mark = ma.check_same(colours("だついじょ", 1), measure, [("だついしょ", colours("だついしょ", 0))])
    same(mark[0], ma.OK, "だついじょ for だついじょ: %s" % (mark,))


def fake(way, text, length=ma.OK, sounds=ma.OK, same_=ma.NONE, pitch=ma.NONE):
    clip = ma.Clip("f", "x", "x", "word", "あ", None, [(way, text)])
    one = ma.Try(clip, way, text, shorts(silence(0.1)))
    one.samples = shorts([0])
    one.marks = {"length": (length, ""), "sounds": (sounds, "x"), "same": (same_, "1.0/2.0"), "pitch": (pitch, "p"),
                 "level": (ma.OK, "-1.0")}
    return one


def chosen(*tries):
    right = [one for one in tries if one.way != "word" and one.right_sounds()]
    measure = right[0] if right else [one for one in tries if one.way == "kana"][0]
    kept, remark = ma.choose(list(tries), measure)
    return kept.text, kept.verdict(), remark


def test_which_way_of_writing_is_kept():
    same(chosen(fake("word", "出口", same_=ma.OK, pitch=ma.OK), fake("kana", "でぐち", pitch=ma.OK)),
         ("出口", "ok", ""), "both right: the printed word")
    same(chosen(fake("word", "出口", same_=ma.OK), fake("kana", "でぐち")), ("出口", "ok", ""), "no accent on the card")
    same(chosen(fake("word", "出口", same_=ma.OK, pitch=ma.FAIL), fake("kana", "でぐち", pitch=ma.OK)),
         ("でぐち", "ok", "出口: pitch fail p"), "the pitch decides")
    same(chosen(fake("word", "出口", same_=ma.OK, pitch=ma.UNSURE), fake("kana", "でぐち", pitch=ma.FAIL)),
         ("出口", "ok", "でぐち: pitch fail p"), "unsure is better than fail")
    same(chosen(fake("word", "出口", same_=ma.FAIL, pitch=ma.OK), fake("kana", "でぐち", pitch=ma.FAIL)),
         ("でぐち", "doubt", "出口: same fail 1.0/2.0"), "a printed word that was read in another way is never kept")
    same(chosen(fake("word", "出口", same_=ma.UNSURE, pitch=ma.OK), fake("kana", "でぐち", pitch=ma.OK)),
         ("でぐち", "ok", "出口: same unsure 1.0/2.0"), "nor one of which that is not sure")
    same(chosen(fake("word", "出口", sounds=ma.FAIL, same_=ma.OK), fake("kana", "でぐち")),
         ("でぐち", "ok", "出口: sounds fail x"), "nor one with the wrong sounds")
    same(chosen(fake("word", "出口", same_=ma.FAIL, pitch=ma.OK), fake("kana", "でぐち", pitch=ma.FAIL),
                fake("katakana", "デグチ", same_=ma.OK, pitch=ma.OK)),
         ("デグチ", "ok", "出口: same fail 1.0/2.0; でぐち: pitch fail p"), "the other kana, when its pitch is better")
    same(chosen(fake("kana", "でぐち", pitch=ma.FAIL), fake("katakana", "デグチ", same_=ma.UNSURE, pitch=ma.OK)),
         ("でぐち", "doubt", "デグチ: same unsure 1.0/2.0"), "the other kana must sound the same as well")
    same(chosen(fake("kana", "コース"), fake("hiragana", "こーす", same_=ma.FAIL)),
         ("コース", "ok", "こーす: same fail 1.0/2.0"), "katakana is not in doubt when hiragana sounds unlike")
    same(chosen(fake("word", "出口", same_=ma.OK, pitch=ma.FAIL), fake("kana", "でぐち", pitch=ma.FAIL),
                fake("katakana", "デグチ", same_=ma.OK, pitch=ma.FAIL)),
         ("出口", "doubt", ""), "no pitch is right: the first, in doubt")
    same(chosen(fake("kana", "はつか", sounds=ma.FAIL), fake("katakana", "ハツカ")),
         ("ハツカ", "ok", "はつか: sounds fail x"), "the kana of the deck was read wrong: the other kana is the measure")
    same(chosen(fake("word", "二十日", same_=ma.OK), fake("kana", "はつか", sounds=ma.FAIL, same_=ma.FAIL),
                fake("katakana", "ハツカ")),
         ("二十日", "ok", "はつか: sounds fail x"), "and the printed word is compared with that")
    same(chosen(fake("kana", "でぐち"), fake("katakana", "デグチ", same_=ma.FAIL)),
         ("でぐち", "doubt", "デグチ: same fail 1.0/2.0"), "two kana that seem right and sound unlike: in doubt")
    same(chosen(fake("word", "出口", same_=ma.OK, sounds=ma.FAIL), fake("kana", "でぐち", length=ma.FAIL)),
         ("でぐち", "bad", "出口: sounds fail x"), "nothing is right: the reading in kana, marked bad")
    same(chosen(fake("word", "出口", same_=ma.FAIL, pitch=ma.OK), fake("kana", "でぐち", sounds=ma.FAIL)),
         ("出口", "doubt", "not proved, no kana was right; でぐち: sounds fail x"),
         "no kana is right: the printed word, if it passes, is kept in doubt")
    left = fake("kana", "じゅうはちじ", same_=ma.UNSURE)
    left.left_out = "and may hold a particle"
    same(chosen(fake("katakana", "ジュウハチジ", same_=ma.UNSURE), left),
         ("ジュウハチジ", "ok", "じゅうはちじ: same unsure 1.0/2.0 and may hold a particle"), "kana that was left out")


# ---------------------------------------------------------------------------------------------
# index.tsv
# ---------------------------------------------------------------------------------------------

def test_the_index_is_read_as_it_was_written():
    path = os.path.join(WORK, "index", "index.tsv")
    shutil.rmtree(os.path.dirname(path), ignore_errors=True)
    same(ma.read_index(path), {}, "an index that is not there")
    rows = {}
    for name in ("b", "a", "c"):
        rows["/audio/f/x/%s.wav" % name] = dict((column, "") for column in ma.INDEX_COLUMNS)
        rows["/audio/f/x/%s.wav" % name].update({"path": "/audio/f/x/%s.wav" % name, "text": "出口", "ms": 510,
                                                "pitch": "ok 5.2 at 1.3", "remark": "でぐち: pitch fail 1.0 at 2.0",
                                                "accent": 1, "same": "-"})
    ma.write_index(path, rows, ["/audio/f/x/c.wav", "/audio/f/x/a.wav"])
    lines = [line for line in read(path).splitlines() if not line.startswith("#")]
    same(lines[0].split("\t"), ma.INDEX_COLUMNS, "the header row")
    same([line.split("\t")[0][-5] for line in lines[1:]], ["c", "a", "b"], "the order of the content, then the rest")
    back = ma.read_index(path)
    same(sorted(back), sorted(rows), "paths")
    row = back["/audio/f/x/a.wav"]
    same((row["text"], row["ms"], row["pitch"], row["remark"], row["accent"], row["same"], row["sounds"]),
         ("出口", "510", "ok 5.2 at 1.3", "でぐち: pitch fail 1.0 at 2.0", "1", "-", ""), "a row")
    for column in ("path", "text", "voice", "engine", "ms", "verdict"):
        expect(column in ma.INDEX_COLUMNS, "the index has no column " + column)
    write(path, "path\ttext\n/audio/f/x/a.wav\t出口\n")
    lines = []
    keep = sys.stdout
    sys.stdout = type("Catch", (), {"write": lambda self, text: lines.append(text), "flush": lambda self: None})()
    try:
        same(ma.read_index(path), {}, "an index with other columns")
    finally:
        sys.stdout = keep
    expect("other columns" in "".join(lines), "nothing was said about the other columns")


def test_what_a_clip_is_made_from():
    def clip(**changes):
        values = dict(voice="f", folder="signs", name="sign-deguchi", kind="word", reading="でぐち", accent=1,
                      texts=[("word", "出口"), ("kana", "でぐち")], sure=1, others=["てぐち"])
        values.update(changes)
        return ma.Clip(**values)

    first = ma.made_from(clip(), "say/Kyoko")
    same(first, ma.made_from(clip(), "say/Kyoko"), "the same clip twice")
    same(len(first), 12, "length of the sum")
    for what, other in (("reading", clip(reading="でくち")), ("accent", clip(accent=0)), ("no accent", clip(accent=None)),
                        ("text", clip(texts=[("word", "出囗"), ("kana", "でぐち")])),
                        ("ways", clip(texts=[("kana", "でぐち")], sure=0)), ("other readings", clip(others=[]))):
        expect(ma.made_from(other, "say/Kyoko") != first, "another %s gives the same sum" % what)
    expect(ma.made_from(clip(), "say/Otoya") != first, "another voice gives the same sum")
    expect(ma.made_from(clip(), "say/Kyoko/150") != first, "another speed gives the same sum")
    same(ma.made_from(clip(name="other", folder="x"), "say/Kyoko"), first, "the name does not count")
    keep = ma.VERSION
    ma.VERSION = keep + 1
    try:
        expect(ma.made_from(clip(), "say/Kyoko") != first, "another way of making clips gives the same sum")
    finally:
        ma.VERSION = keep


def test_the_engine_of_macos_names_itself():
    same(ma.SayEngine("f", {}).identity(), "say/Kyoko", "the female voice")
    same(ma.SayEngine("m", {}).identity(), "say/Otoya", "the male voice")
    same(ma.SayEngine("m", {"say_voice": "Hattori", "say_rate": 150}).identity(), "say/Hattori/150", "a voice by name")
    same([ma.SayEngine.closes(name) for name in ("say/Kyoko", "say/Kyoko/150", "say/Kyoko (Enhanced)")],
         [True, True, False], "voices that put silence before k, t and p")
    same(ma.Engine.closes("other/voice"), False, "an engine of which nothing is known")
    expect(set(ma.SAY_VOICES) == set(ma.PITCH_RANGE) == {"f", "m"}, "voices: %s" % sorted(ma.SAY_VOICES))
    expect(ma.ENGINES["say"] is ma.SayEngine, "say is not listed")


# ---------------------------------------------------------------------------------------------
# The whole tool, with the engine of the tests
# ---------------------------------------------------------------------------------------------

def test_a_whole_run():
    content("run", guide=True)
    code, said, asked = tool("run")
    same(code, 0, "exit code\n" + said)
    rows = index_of("run")
    same(len(rows), 20, "rows in the index")
    expect("20 clips, 0 up to date, 20 to make with tones/1" in said, said)
    for path, row in rows.items():
        file = ma.clip_file(os.path.join(WORK, "run", "audio"), path)
        expect(os.path.exists(file), "%s is not there" % path)
        with wave.open(file, "rb") as handle:
            same((handle.getnchannels(), handle.getsampwidth(), handle.getframerate()), (1, 2, 16000), path)
            same(str(int(round(handle.getnframes() / 16.0))), row["ms"], "ms of " + path)
        same(os.path.getsize(file), 44 + 32 * int(row["ms"]), "bytes of " + path)
        same((row["voice"], row["engine"], row["level"]), ("f", "tones/1", "ok -1.0"), path)
        same(row["length"].split()[0], ma.OK, "length of " + path)
    files = []
    for folder, _, names in os.walk(os.path.join(WORK, "run", "audio")):
        files += [name for name in names]
    same(sorted(name for name in files if not name.endswith(".wav")), ["index.tsv"], "files that are no clips")
    same(len(files), 21, "files")

    def row(name):
        return [rows[path] for path in rows if path.endswith("/" + name + ".wav")][0]

    exit_ = row("sign-deguchi")
    same((exit_["text"], exit_["way"], exit_["reading"], exit_["accent"], exit_["verdict"]),
         ("出口", "word", "でぐち", "1", "ok"), "出口, which the engine reads right and with its accent")
    same(exit_["pitch"].split()[0], ma.OK, "pitch of 出口")
    same(exit_["same"].split()[0], ma.OK, "出口 against でぐち")
    expect("でぐち: pitch fail" in exit_["remark"], "remark of 出口: " + exit_["remark"])
    bound = row("sign-yuki")
    same((bound["text"], bound["way"], bound["verdict"]), ("ゆき", "kana", "ok"), "行き, which the engine reads いき")
    expect("行き: same fail" in bound["remark"] and "read いき" in bound["remark"], "remark of 行き: " + bound["remark"])
    child = row("sign-shounin")
    same((child["text"], child["verdict"]), ("しょうにん", "ok"), "小人, which the engine reads こびと")
    expect("小人: " in child["remark"], "remark of 小人: " + child["remark"])
    same(row("sign-otona")["text"], "大人", "大人, which the engine reads right")
    smoke = row("sign-kin-en")
    same((smoke["text"], smoke["way"], smoke["verdict"]), ("キンエン", "katakana", "ok"),
         "禁煙, which has the right pitch in katakana only")
    beer = row("kata-biiru")
    same((beer["text"], beer["way"], beer["pitch"].split()[0]), ("ビール", "kana", ma.OK), "ビール")
    letter = row("hiragana-he")
    same((letter["text"], letter["way"], letter["verdict"]), ("ヘ", "katakana", "ok"), "へ, which is read e in hiragana")
    expect("へ: sounds fail" in letter["remark"], "remark of へ: " + letter["remark"])
    same(row("hiragana-kya")["lead"], "80", "the silence before きゃ")
    same(row("hiragana-a")["lead"], "0", "the silence before あ")
    same((row("num-yen-100")["text"], row("num-yen-100")["pitch"], row("num-yen-100")["same"]),
         ("ひゃくえん", "-", "ok 0.0/0.0"), "a number, which sounds the same in both kana")
    same(row("buddy-greeting-01")["same"], "-", "a line of the buddy is written in one way only")
    hour = row("num-time-1800")
    same((hour["text"], hour["way"], hour["verdict"]), ("ジュウハチジ", "katakana", "ok"),
         "じゅうはちじ, in which the engine reads は as the particle")
    expect("じゅうはちじ: same" in hour["remark"] and "may hold a particle" in hour["remark"],
           "remark of じゅうはちじ: " + hour["remark"])
    date = row("num-date-0120")
    same((date["text"], date["way"], date["same"].split()[0], date["remark"]), ("いちがつはつか", "kana", ma.OK, ""),
         "いちがつはつか, which the engine reads right in both kana")
    same(row("buddy-start-01")["text"], "さあ、 はじめよう。", "a line of the buddy")
    same(row("guide-long-2")["text"], "おばあさん", "a clip of the guide")
    same([name for name in asked if name in ("いき", "こども", "だいにん")], ["いき", "だいにん", "こども"],
         "other readings that were spoken")
    expect("folder" in said and "signs" in said and "minutes of sound" in said, "no summary:\n" + said)


def test_nothing_is_made_twice():
    content("twice")
    tool("twice")
    code, said, asked = tool("twice")
    same((code, asked), (0, []), "a second run")
    expect("15 clips, 15 up to date, 0 to make" in said, said)
    before = read(os.path.join(WORK, "twice", "audio", "index.tsv"))

    folder = os.path.join(WORK, "twice", "content")
    write(os.path.join(folder, "decks", "signs.tsv"), "\n".join(SIGNS).replace("おしり\tおしり", "おしり\tおけつ") + "\n")
    code, said, asked = tool("twice")
    same((code, asked), (0, ["おけつ", "オケツ"]), "after a reading has changed")
    same(index_of("twice")["/audio/f/signs/sign-oshiri.wav"]["reading"], "おけつ", "the new reading in the index")

    write(os.path.join(folder, "decks", "signs.tsv"), "\n".join(SIGNS).replace("きんえん\t0", "きんえん\t1") + "\n")
    code, said, asked = tool("twice")
    same(sorted(set(asked)), ["おしり", "きんえん", "オシリ", "キンエン", "禁煙"],
         "after an accent has changed, and a reading back")
    smoke = index_of("twice")["/audio/f/signs/sign-kin-en.wav"]
    same((smoke["text"], smoke["accent"]), ("禁煙", "1"), "the clip that fits the new accent")

    os.remove(os.path.join(WORK, "twice", "audio", "f", "hiragana", "hiragana-a.wav"))
    code, said, asked = tool("twice")
    same((code, asked), (0, ["ア", "あ"]), "after a clip was lost")

    write(os.path.join(folder, "decks", "signs.tsv"), "\n".join(SIGNS) + "\n")
    tool("twice")
    same(read(os.path.join(WORK, "twice", "audio", "index.tsv")), before, "the index, with the first content again")
    code, said, asked = tool("twice", "--again", "--only", "numbers")
    same((code, asked[:2], len(asked)), (0, ["ひゃくえん", "ヒャクエン"], 6), "--again")


def test_one_deck_only():
    content("only", guide=True)
    code, said, asked = tool("only", "--only", "hiragana", "--only", "guide")
    same(code, 0, "exit code\n" + said)
    same(sorted(path.split("/")[3] for path in index_of("only")), ["guide"] * 5 + ["hiragana"] * 3, "folders made")
    code, said, asked = tool("only", "--only", "buddy")
    same(sorted(path.split("/")[3] for path in index_of("only")), ["buddy"] * 2 + ["guide"] * 5 + ["hiragana"] * 3,
         "the rows of the first run are kept")
    code, said, asked = tool("only", "--only", "nothing")
    same(code, 2, "exit code for a deck that is not there")
    expect("no such deck" in said, said)
    code, said, asked = tool("only")
    same(len(index_of("only")), 20, "rows after a run for everything")
    order = [line.split("\t")[0].split("/")[3] for line in read(os.path.join(WORK, "only", "audio", "index.tsv"))
             .splitlines() if line.startswith("/")]
    same(order, ["hiragana"] * 3 + ["katakana-words"] + ["numbers"] * 3 + ["signs"] * 6 + ["guide"] * 5 + ["buddy"] * 2,
         "the order of the index")


def test_stopped_and_started_again():
    content("stop")
    TestEngine.stop_at = 9
    code, said, asked = tool("stop")
    same(code, 130, "exit code of a run that was stopped\n" + said)
    done = index_of("stop")
    expect(3 <= len(done) < 15, "rows after the stop: %d" % len(done))
    for path in done:
        expect(os.path.exists(ma.clip_file(os.path.join(WORK, "stop", "audio"), path)), path + " is in the index only")
    left = []
    for folder, _, names in os.walk(os.path.join(WORK, "stop", "audio")):
        left += [name for name in names if not name.endswith(".wav") and name != "index.tsv"]
    same(left, [], "files that were left half made")
    code, said, asked = tool("stop")
    same(code, 0, "exit code of the second run\n" + said)
    expect("15 clips, %d up to date, %d to make" % (len(done), 15 - len(done)) in said, said)
    same(len(index_of("stop")), 15, "rows after the second run")
    content("whole")
    tool("whole")
    same(read(os.path.join(WORK, "stop", "audio", "index.tsv")),
         read(os.path.join(WORK, "whole", "audio", "index.tsv")), "the index of a run in two parts and of a run in one")


def test_check_measures_what_is_there():
    content("check", guide=True)
    code, said, asked = tool("check", "--check")
    same((code, asked), (1, []), "--check before anything is made")
    expect(said.count(": missing") == 20, said)
    expect(not os.path.exists(os.path.join(WORK, "check", "audio")), "--check has made the folder")
    tool("check")
    before = read(os.path.join(WORK, "check", "audio", "index.tsv"))
    code, said, asked = tool("check", "--check")
    same((code, asked), (0, []), "--check on a fresh run\n" + said)
    expect("20 clips measured: 20 as the index says, 0 differing, 0 missing, 0 out of date" in said, said)
    code, said, asked = tool("check", "--check", "--only", "signs")
    expect("6 clips measured: 6 as the index says" in said, said)

    audio = os.path.join(WORK, "check", "audio", "f")
    os.remove(os.path.join(audio, "buddy", "buddy-start-01.wav"))
    whole = ma.read_wav(os.path.join(audio, "signs", "sign-otona.wav"))
    ma.write_wav(os.path.join(audio, "signs", "sign-otona.wav"), whole[:len(whole) // 2])
    quiet = [value // 2 for value in ma.read_wav(os.path.join(audio, "signs", "sign-oshiri.wav"))]
    ma.write_wav(os.path.join(audio, "signs", "sign-oshiri.wav"), array.array("h", quiet))
    write(os.path.join(audio, "hiragana", "hiragana-a.wav"), "no sound")
    save(os.path.join(audio, "guide", "guide-vowels-1.wav"), speech("あ"), rate=8000)
    folder = os.path.join(WORK, "check", "content")
    write(os.path.join(folder, "buddy.tsv"), "\n".join(BUDDY).replace("こんにちは", "こんばんは") + "\n")
    code, said, asked = tool("check", "--check")
    same((code, asked), (1, []), "--check after the clips were spoilt")
    for words in ("buddy-start-01.wav: missing", "buddy-greeting-01.wav: out of date",
                  "sign-otona.wav: is ", "sign-otona.wav: silence at the ends",
                  "sign-oshiri.wav: level is \"fail -7.0\"",
                  "hiragana-a.wav is not a sound file", "guide-vowels-1.wav has 1 channel(s), 16 bit, 8000 samples",
                  "18 clips measured: 14 as the index says, 4 differing, 1 missing, 1 out of date"):
        expect(words in said, "\"%s\" is not in:\n%s" % (words, said))
    same(read(os.path.join(WORK, "check", "audio", "index.tsv")), before, "--check has changed the index")


def test_clips_that_are_not_asked_for_any_more():
    content("tidy", guide=True)
    tool("tidy")
    os.remove(os.path.join(WORK, "tidy", "content", "guide.tsv"))
    code, said, asked = tool("tidy")
    same((code, asked, len(index_of("tidy"))), (0, [], 20), "a run without the guide keeps its clips")
    code, said, asked = tool("tidy", "--check")
    same(code, 0, "--check when only clips too many are there\n" + said)
    same(said.count("the content does not ask for it any more"), 5, "clips too many that --check names")
    code, said, asked = tool("tidy", "--tidy", "--only", "signs")
    same((code, len(index_of("tidy"))), (0, 20), "--tidy for another deck")
    code, said, asked = tool("tidy", "--tidy")
    same((code, asked, len(index_of("tidy"))), (0, [], 15), "--tidy")
    same(said.count("removed /audio/f/guide/"), 5, "clips removed")
    same(os.listdir(os.path.join(WORK, "tidy", "audio", "f", "guide")), [], "files of the guide")
    expect(os.path.exists(os.path.join(WORK, "tidy", "audio", "f", "signs", "sign-deguchi.wav")), "a clip was lost")


def test_an_engine_that_fails():
    class Broken(TestEngine):
        def speak(self, text, path):
            if text == "ヒャクエン":
                raise ma.Stop("the voice has gone")
            TestEngine.speak(self, text, path)

    content("broken")
    keep = TestEngine
    ma.ENGINES[TestEngine.name] = Broken
    lines = []
    out = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = type("Catch", (), {"write": lambda self, text: lines.append(text),
                                                 "flush": lambda self: None})()
    try:
        code = ma.main(["--engine", "tones", "--jobs", "1", "--cache", os.path.join(WORK, "broken", "none"),
                        "--content", os.path.join(WORK, "broken", "content"),
                        "--out", os.path.join(WORK, "broken", "audio")])
    finally:
        sys.stdout, sys.stderr = out
        ma.ENGINES[TestEngine.name] = keep
    said = "".join(lines)
    same(code, 1, "exit code when a clip could not be made\n" + said)
    expect("the voice has gone" in said and "1 clip could not be made" in said, said)
    same(len(index_of("broken")), 14, "rows of the clips that were made")

    class Absent(TestEngine):
        def ready(self):
            return "there is no voice here"

    ma.ENGINES[TestEngine.name] = Absent
    sys.stdout = sys.stderr = type("Catch", (), {"write": lambda self, text: lines.append(text),
                                                 "flush": lambda self: None})()
    try:
        code = ma.main(["--engine", "tones", "--jobs", "1", "--cache", os.path.join(WORK, "broken", "none"),
                        "--content", os.path.join(WORK, "broken", "content"),
                        "--out", os.path.join(WORK, "broken", "audio")])
    finally:
        sys.stdout, sys.stderr = out
        ma.ENGINES[TestEngine.name] = keep
    same(code, 2, "exit code when the engine is not ready")
    expect("there is no voice here" in "".join(lines), "".join(lines))


def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    tests = [(name[len("test_"):].replace("_", " "), function) for name, function in sorted(globals().items())
             if name.startswith("test_") and callable(function)]
    if arguments:
        tests = [t for t in tests if any(word in t[0] for word in arguments)]
    if not tests:
        sys.exit("no test matches " + " ".join(arguments))

    os.makedirs(WORK, exist_ok=True)
    failed = []
    for name, function in tests:
        try:
            function()
        except Failure as failure:
            failed.append(name)
            print("FAIL  %s\n      %s" % (name, failure))
            continue
        print("ok    %s" % name)

    print("%d test%s: %d passed, %d failed" % (len(tests), "" if len(tests) == 1 else "s",
                                               len(tests) - len(failed), len(failed)))
    if failed:
        sys.exit("FAILED: " + ", ".join(failed))


if __name__ == "__main__":
    main()
