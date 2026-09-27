#!/usr/bin/env python3
"""Renders concept screens for the ideas, pixel-exact at 240x135, as PNG files.

These are sketches of how each idea would look and behave on the device. They are drawn with
the device's own fonts through tools/cardputer_screen.py, so sizes and legibility are real.

Usage: python3 tools/concept_screens.py [output directory]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardputer_screen import HEIGHT, ROOT, WIDTH, Screen, font  # noqa: E402

F10, F12, F14, F16, F24 = "efontJA_10", "efontJA_12", "efontJA_14", "efontJA_16", "efontJA_24"
F12B, F16B, F24B = "efontJA_12_b", "efontJA_16_b", "efontJA_24_b"
G32, G40 = "lgfxJapanGothic_32", "lgfxJapanGothic_40"

# Neutral sketch palette. The real look is a separate choice (see look_* screens below).
BG = (14, 18, 24)
BAR = (27, 42, 74)
INK = (255, 255, 255)
DIM = (150, 160, 175)
FAINT = (70, 80, 95)
ACCENT = (255, 213, 74)
GOOD = (90, 214, 125)
BAD = (255, 107, 107)
WAIT = (255, 167, 38)
PAPER = (250, 247, 238)
SUMI = (24, 24, 28)
SHU = (214, 60, 42)

problems = []


def check(name, screen, *ends):
    for end in ends:
        if end > WIDTH:
            problems.append("%s: text runs to x=%d" % (name, end))
    if screen.missing:
        problems.append("%s: glyphs missing: %s" % (name, "".join(screen.missing)))


def shell(title, right="", bar=BAR, bg=BG, ink=INK):
    s = Screen(bg)
    s.fill_rect(0, 0, WIDTH, 14, bar)
    s.text(4, 1, title, F12, ink)
    if right:
        s.text(WIDTH - 4, 1, right, F12, ink, align="right")
    return s


def footer(s, text, color=DIM):
    s.hline(0, HEIGHT - 15, WIDTH, FAINT)
    return s.text(4, HEIGHT - 13, text, F12, color)[0]


def catcher():
    s = shell("ひろう  word catcher", "京都駅 14:32")
    a = s.text(6, 18, "かいさつ", F16, GOOD)[0]
    s.text(a + 1, 18, "_", F16, FAINT)
    s.text(WIDTH - 6, 21, "kaisatsu", F12, DIM, align="right")
    s.hline(4, 36, WIDTH - 8, FAINT)
    s.fill_rect(2, 39, WIDTH - 4, 18, (32, 46, 78))
    b = s.text(6, 40, "改札", F16, ACCENT)[0]
    c = s.text(b + 8, 43, "かいさつ  ticket gate", F12, INK)[0]
    d = s.text(6, 60, "改札口", F16, INK)[0]
    e = s.text(d + 8, 63, "かいさつぐち  ticket barrier", F12, DIM)[0]
    f = s.text(6, 80, "開札", F16, INK)[0]
    g = s.text(f + 8, 83, "かいさつ  opening of bids", F12, DIM)[0]
    s.text(6, 102, "1 of 3", F12, FAINT)
    h = footer(s, "Enter ほぞん  Fn+;. えらぶ  Tab カナ")
    check("catcher", s, c, e, g, h)
    return s


def queue():
    s = shell("キュー  90 seconds", "京都 3日目")
    s.text(WIDTH // 2, 20, "おつかれさま！", F16, INK, align="center")
    columns = ((40, "12", "cards", INK), (120, "10", "correct", GOOD), (200, "8", "due tonight", ACCENT))
    ends = []
    for x, number, label, color in columns:
        s.text(x, 44, number, F24B, color, align="center")
        ends.append(s.text(x, 72, label, F12, DIM, align="center")[0])
    s.hline(4, 90, WIDTH - 8, FAINT)
    ends.append(s.text(6, 95, "again soon:", F12, DIM)[0])
    ends.append(s.text(78, 95, "替玉  はっぴゃく  ソ⇔ン", F12, WAIT)[0])
    ends.append(footer(s, "any key: one more round    Tab: menu"))
    check("queue", s, *ends)
    return s


def numbers():
    s = shell("いくら？  numbers by ear", "7/15")
    s.text(6, 18, "レジ", F12, DIM)
    s.round_rect(60, 18, 120, 30, 3, (8, 40, 20))
    s.text(174, 21, "1,880", F24, BAD, align="right")
    s.text(178, 30, "円", F12, BAD)
    s.text(6, 54, "ただしくは", F12, DIM)
    a = s.text(70, 50, "1,280", F24B, GOOD)[0]
    s.text(a + 2, 58, "円", F16, GOOD)
    b = s.text(6, 78, "せん", F16, INK)[0]
    b = s.text(b, 78, "にひゃく", F16, ACCENT)[0]
    b = s.text(b, 78, "はちじゅうえん", F16, INK)[0]
    s.hline(38, 95, 64, ACCENT)
    c = s.text(6, 100, "にひゃく 200  ⇔  はっぴゃく 800", F12, DIM)[0]
    d = footer(s, "Space もう一度  S ゆっくり  Enter 次")
    check("numbers", s, b, c, d)
    return s


def staff_lines():
    s = shell("店員さん", "コンビニ・レジ")
    a = s.text(6, 18, "「レジ袋はご利用ですか？」", F16, INK)[0]
    b = s.text(8, 37, "れじぶくろは ごりようですか", F12, DIM)[0]
    c = s.text(8, 51, "Would you like a bag?", F12, DIM)[0]
    s.hline(4, 67, WIDTH - 8, FAINT)
    s.text(6, 71, "あなた", F12, DIM)
    d = s.text(6, 85, "いいえ、だいじょうぶです", F16, GOOD)[0]
    s.text(d + 4, 85, "〇", F16, GOOD)
    e = s.text(6, 104, "also: ふくろは いりません", F12, DIM)[0]
    f = footer(s, "type  mou ichido  to hear it again")
    check("staff", s, a, b, c, d + 22, e, f)
    return s


def sign_sprint():
    s = shell("看板  signs", "駅 3/10")
    s.round_rect(38, 20, 164, 46, 4, (20, 110, 60))
    s.round_rect(41, 23, 158, 40, 3, (255, 255, 255), fill=False)
    s.text(WIDTH // 2, 27, "精算機", G32, INK, align="center")
    a = s.text(6, 72, "せいさんき", F16, GOOD)[0]
    s.text(a + 1, 72, "_", F16, FAINT)
    s.text(WIDTH - 6, 75, "seisanki", F12, DIM, align="right")
    b = s.text(6, 93, "fare adjustment machine", F12, INK)[0]
    c = s.text(6, 107, "精算 settle up ・ 機 machine", F12, DIM)[0]
    d = footer(s, "Enter こたえる   Tab とばす")
    check("sign", s, a, b, c, d)
    return s


def katakana():
    s = shell("カタカナ  sprint", "0:31")
    s.fill_rect(0, 14, 165, 3, ACCENT)
    s.text(WIDTH // 2, 24, "モーニング", F24, INK, align="center")
    s.text(WIDTH // 2, 50, "セット", F24, INK, align="center")
    x = 40
    for mora, color in (("mo-", GOOD), ("ni", GOOD), ("n", GOOD), ("gu", GOOD), ("se", WAIT), ("t", FAINT), ("to", FAINT)):
        x = s.text(x, 80, mora, F16, color)[0] + 3
    a = s.text(6, 102, "シ⇔ツ 4  ソ⇔ン 2   42 mora/min", F12, DIM)[0]
    b = footer(s, "= breakfast set, not just \"morning\"")
    check("katakana", s, x, a, b)
    return s


def counters():
    s = shell("数え方  say the number", "4/8")
    s.text(WIDTH // 2, 19, "ビール × 3", F24, INK, align="center")
    a = s.text(6, 50, "さんばい", F16, GOOD)[0]
    s.text(a + 4, 50, "〇", F16, GOOD)
    s.text(WIDTH - 6, 53, "also みっつ", F12, DIM, align="right")
    s.hline(4, 70, WIDTH - 8, FAINT)
    s.text(6, 74, "杯", F16, ACCENT)
    b = s.text(28, 74, "1 いっぱい   2 にはい", F12, INK)[0]
    c = s.text(28, 88, "3 さんばい   6 ろっぱい", F12, INK)[0]
    d = s.text(28, 102, "8 はっぱい  10 じゅっぱい", F12, INK)[0]
    e = footer(s, "「ビールを さんばい ください」")
    check("counters", s, a, b, c, d, e)
    return s


def tomorrow():
    s = shell("あしたパック", "3日目  4/18")
    a = s.text(6, 17, "京都 → 奈良", F16, ACCENT)[0]
    s.text(WIDTH - 6, 20, "guess first", F12, DIM, align="right")
    s.text(WIDTH // 2, 37, "烏丸", G32, INK, align="center")
    s.text(6, 74, "あなた", F12, DIM)
    b = s.text(52, 71, "からすまる", F16, BAD)[0]
    s.text(b + 4, 74, "×", F12, BAD)
    s.text(6, 93, "こたえ", F12, DIM)
    c = s.text(52, 90, "からすま", F16, GOOD)[0]
    d = s.text(c + 8, 93, "Kyoto subway line", F12, DIM)[0]
    e = footer(s, "Enter 次へ    あさ もう一度 でてくる")
    check("tomorrow", s, a, b + 10, d, e)
    return s


def diary():
    s = shell("三行日記  diary", "よる 21:40")
    s.text(6, 17, "1", F12, FAINT)
    a = s.text(18, 17, "ひとが おおいでした。", F16, DIM)[0]
    s.text(6, 38, "→", F12, GOOD)
    b = s.text(18, 36, "人が", F16, INK)[0]
    b2 = s.text(b, 36, "多かった", F16B, GOOD)[0]
    b3 = s.text(b2, 36, "です。", F16, INK)[0]
    c = s.text(18, 54, "ひとが おおかったです", F12, DIM)[0]
    s.hline(4, 71, WIDTH - 8, FAINT)
    d = s.text(6, 75, "い-adjective, past tense:", F12, INK)[0]
    e = s.text(6, 89, "多い → 多かった  (not 多いでした)", F12, INK)[0]
    f = s.text(6, 104, "+2 cards for tomorrow", F12, ACCENT)[0]
    g = footer(s, "Enter: retype it from memory   2/3")
    check("diary", s, a, b3, c, d, e, f, g)
    return s


def rehearsal():
    s = shell("稽古  rehearsal", "居酒屋・入口")
    s.text(6, 18, "店", F12, ACCENT)
    a = s.text(24, 18, "いらっしゃいませ！何名様ですか？", F12, INK)[0]
    s.text(6, 34, "私", F12, GOOD)
    b = s.text(24, 34, "ふたりです。", F12, DIM)[0]
    s.text(6, 50, "店", F12, ACCENT)
    c = s.text(24, 50, "カウンター席でもよろしいですか？", F12, INK)[0]
    d = s.text(24, 64, "かうんたーせきでも よろしいですか", F10, FAINT)[0]
    s.hline(4, 80, WIDTH - 8, FAINT)
    s.text(6, 86, "私", F12, GOOD)
    e = s.text(24, 84, "はい、だいじょ", F16, GOOD)[0]
    e = s.text(e, 84, "u", F16, WAIT)[0]
    s.text(e + 1, 84, "_", F16, FAINT)
    f = s.text(6, 104, "あとで: 2 things to fix, 3 new cards", F12, DIM)[0]
    g = footer(s, "Tab ヒント  Fn+Y よみがな  Fn+Q おわる")
    check("rehearsal", s, a, b, c, d, e, f, g)
    return s


def show_card():
    s = Screen(PAPER)
    s.fill_rect(0, 0, WIDTH, 5, SHU)
    a = s.text(8, 12, "えびアレルギーが", F24, SUMI)[0]
    b = s.text(8, 40, "あります。", F24, SUMI)[0]
    c = s.text(8, 72, "これに えびは", F24, SUMI)[0]
    d = s.text(8, 100, "入っていますか？", F24, SUMI)[0]
    check("show_card", s, a, b, c, d)
    return s


def missions():
    s = shell("今日のミッション", "3日目 京都")
    s.text(6, 18, "①", F16, ACCENT)
    a = s.text(26, 18, "駅員さんに聞く", F16, INK)[0]
    b = s.text(26, 37, "「京都行きは何番線ですか」", F12, DIM)[0]
    s.text(6, 54, "②", F16, GOOD)
    c = s.text(26, 54, "おすすめを聞く", F16, DIM)[0]
    s.text(c + 8, 54, "済", F16, GOOD)
    d = s.text(26, 73, "「おすすめは何ですか」", F12, FAINT)[0]
    x = 8
    for index in range(6):
        done = index < 3
        s.round_rect(x, 91, 24, 24, 12, SHU if done else (40, 46, 58), fill=done)
        if done:
            s.text(x + 12, 95, ("東", "箱", "京")[index], F16, PAPER, align="center")
        else:
            s.round_rect(x, 91, 24, 24, 12, FAINT, fill=False)
        x += 30
    s.text(WIDTH - 6, 98, "3/12", F12, DIM, align="right")
    e = footer(s, "R れんしゅう  D できた  S スタンプ帳")
    check("missions", s, a, b, c + 24, d, e)
    return s


def daruma(s, cx, cy, second_eye=False):
    body = (200, 40, 36)
    s.round_rect(cx - 17, cy - 19, 34, 38, 15, body)
    s.round_rect(cx - 12, cy - 13, 24, 19, 8, (250, 240, 225))
    s.fill_rect(cx - 9, cy - 8, 6, 2, SUMI)
    s.fill_rect(cx + 3, cy - 8, 6, 2, SUMI)
    # By custom the daruma's own left eye (on the viewer's right) is painted when the goal is set,
    # and the other one when it is reached.
    s.round_rect(cx + 3, cy - 5, 6, 6, 3, SUMI)
    if second_eye:
        s.round_rect(cx - 9, cy - 5, 6, 6, 3, SUMI)
    else:
        s.round_rect(cx - 9, cy - 5, 6, 6, 3, SUMI, fill=False)
    s.fill_rect(cx - 3, cy + 2, 6, 1, SUMI)
    s.fill_rect(cx - 8, cy + 9, 16, 2, (240, 190, 60))
    s.fill_rect(cx - 6, cy + 13, 12, 2, (240, 190, 60))


def daruma_small(s, cx, cy):
    body = (200, 40, 36)
    s.round_rect(cx - 12, cy - 13, 24, 27, 11, body)
    s.round_rect(cx - 8, cy - 9, 16, 13, 5, (250, 240, 225))
    s.fill_rect(cx - 6, cy - 6, 4, 1, SUMI)
    s.fill_rect(cx + 2, cy - 6, 4, 1, SUMI)
    s.round_rect(cx + 2, cy - 4, 4, 4, 2, SUMI)
    s.round_rect(cx - 6, cy - 4, 4, 4, 2, SUMI, fill=False)
    s.fill_rect(cx - 2, cy + 1, 4, 1, SUMI)
    s.fill_rect(cx - 5, cy + 7, 10, 1, (240, 190, 60))
    s.fill_rect(cx - 4, cy + 10, 8, 1, (240, 190, 60))


def buddy():
    s = shell("3日目  京都", "マナー ● 82%")
    daruma(s, 30, 52)
    s.round_rect(58, 22, 176, 58, 5, (250, 247, 238))
    s.fill_rect(54, 46, 6, 6, (250, 247, 238))
    a = s.text(66, 28, "おはよう！", F16, SUMI)[0]
    b = s.text(66, 46, "今日は京都だね。", F16, SUMI)[0]
    c = s.text(66, 64, "Space: English", F10, (120, 120, 120))[0]
    s.text(6, 86, "きょう", F12, DIM)
    d = s.text(52, 86, "ことば 12 ・ ミッション 2", F12, INK)[0]
    s.text(6, 102, "ひろった", F12, DIM)
    e = s.text(64, 102, "改札  替玉  拝観料", F12, ACCENT)[0]
    f = footer(s, "なにか キーを おすと はじまる")
    check("buddy", s, a, b, c, d, e, f)
    return s


def shadowing():
    s = shell("オウム返し  echo", "2/5")
    a = s.text(6, 18, "まもなく、", F16, DIM)[0]
    b = s.text(a + 2, 18, "2番線に", F16, ACCENT)[0]
    c = s.text(6, 37, "電車が まいります。", F16, DIM)[0]
    d = s.text(6, 56, "まもなく にばんせんに でんしゃが…", F12, FAINT)[0]
    s.text(6, 76, "手本", F12, DIM)
    s.fill_rect(40, 79, 150, 6, (40, 46, 58))
    s.fill_rect(40, 79, 150, 6, GOOD)
    s.text(196, 76, "1.9 s", F12, DIM)
    s.text(6, 92, "あなた", F12, DIM)
    s.fill_rect(46, 95, 144, 6, (40, 46, 58))
    s.fill_rect(46, 95, 96, 6, BAD)
    s.round_rect(196, 92, 10, 10, 5, BAD)
    s.text(210, 92, "REC", F12, BAD)
    e = footer(s, "1 もういちど   2 つぎ   3 もじを かくす")
    check("shadowing", s, b, c, d, e)
    return s


def station_quiz():
    s = shell("駅名  next station", "山手線")
    s.fill_rect(0, 14, WIDTH, 4, (128, 194, 65))
    s.round_rect(30, 24, 180, 50, 4, (250, 250, 250))
    s.fill_rect(30, 62, 180, 6, (128, 194, 65))
    s.text(WIDTH // 2, 28, "御徒町", G32, SUMI, align="center")
    s.text(40, 77, "上野", F12, DIM)
    s.text(200, 77, "秋葉原", F12, DIM, align="right")
    s.text(WIDTH // 2, 77, "◀ ─── ▶", F12, FAINT, align="center")
    a = s.text(6, 95, "おかち", F16, GOOD)[0]
    s.text(a + 1, 95, "_", F16, FAINT)
    s.text(WIDTH - 6, 98, "okachi", F12, DIM, align="right")
    b = footer(s, "アナウンスの前に答えよう  Space 次")
    check("station", s, a, b)
    return s


def menu_decoder():
    s = shell("魚へん  menu decoder", "part: 魚")
    fish = (("鮪", "まぐろ"), ("鯖", "さば"), ("鯛", "たい"), ("鮭", "さけ"),
            ("鰻", "うなぎ"), ("鯵", "あじ"), ("鰤", "ぶり"), ("鰹", "かつお"))
    ends = []
    for index, (kanji, reading) in enumerate(fish):
        column, row = index % 4, index // 4
        x = 4 + column * 59
        y = 18 + row * 48
        selected = index == 6
        if selected:
            s.round_rect(x, y, 56, 45, 3, (32, 46, 78))
        s.text(x + 28, y + 2, kanji, F24, ACCENT if selected else INK, align="center")
        ends.append(s.text(x + 28, y + 29, reading, F12, INK if selected else DIM, align="center")[0])
    ends.append(footer(s, "鰤 ぶり yellowtail  ・ Space ★ ひろう"))
    check("menu", s, *ends)
    return s


def remote():
    s = shell("リモコン  room remote", "エアコン")
    labels = (("1", "運転", "うんてん"), ("2", "停止", "ていし"), ("3", "冷房", "れいぼう"),
              ("4", "暖房", "だんぼう"), ("5", "除湿", "じょしつ"), ("6", "風量", "ふうりょう"))
    ends = []
    for index, (key, kanji, reading) in enumerate(labels):
        column, row = index % 3, index // 3
        x = 5 + column * 78
        y = 19 + row * 50
        selected = index == 2
        s.round_rect(x, y, 74, 46, 4, (30, 90, 160) if selected else (34, 40, 52))
        s.text(x + 4, y + 2, key, F10, DIM)
        s.text(x + 37, y + 6, kanji, F24, INK, align="center")
        ends.append(s.text(x + 37, y + 32, reading, F12, ACCENT if selected else DIM, align="center")[0])
    ends.append(footer(s, "冷房 れいぼう cooling  ・ 送信 ▶▶"))
    check("remote", s, *ends)
    return s


def snapshot():
    s = shell("音のスナップ  sound snapshot", "のこり 5")
    s.round_rect(8, 22, 14, 14, 7, BAD)
    a = s.text(28, 20, "ろくおん中  0:06 / 0:08", F16, INK)[0]
    x = 8
    heights = (6, 12, 20, 9, 26, 31, 18, 8, 14, 28, 34, 22, 10, 6, 16, 25, 30, 12, 7, 19, 27, 15, 9, 5, 11, 21, 29, 17, 8, 4, 0, 0, 0, 0, 0, 0, 0, 0)
    for h in heights:
        if h:
            s.fill_rect(x, 72 - h // 2, 4, h, GOOD if h < 30 else WAIT)
        else:
            s.fill_rect(x, 71, 4, 2, FAINT)
        x += 6
    b = s.text(6, 94, "新大阪駅 ホーム ・ 10:42", F12, DIM)[0]
    c = s.text(6, 108, "こんや Wi-Fi で もじおこし", F12, ACCENT)[0]
    check("snapshot", s, a, b, c)
    return s


# ---------------------------------------------------------------------------------------------
# Pronunciation: written pitch and rhythm, so that it can be studied without sound.
# ---------------------------------------------------------------------------------------------

SMALL_KANA = set("ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ")


def morae(kana):
    """Splits kana into beats: きゃ is one beat; っ, ん and ー are one beat each."""
    out = []
    for ch in kana:
        if ch in SMALL_KANA and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def pitch_heights(count, accent):
    """True for each high beat. accent 0 is flat; accent k means the pitch falls after beat k."""
    if accent == 0:
        return [False] + [True] * (count - 1) if count > 1 else [True]
    if accent == 1:
        return [True] + [False] * (count - 1)
    return [False] + [True] * (accent - 1) + [False] * (count - accent)


def pitch_word(s, x, y, kana, accent, font_name=F16, ink=INK, line=ACCENT, particle="", particle_ink=DIM,
               whispered=(), style="line", low_ink=DIM):
    """Draws kana with its pitch pattern. Returns the x position after the word.

    style "line": a line over the high beats with a hook where the pitch falls.
    style "colour": high beats bright, low beats dim, a slash where the pitch falls.
    style "number": plain kana followed by the accent number in a box.
    whispered: indexes of beats whose vowel is whispered (devoiced), marked with dots underneath.
    """
    f = font(font_name)
    beats = morae(kana)
    high = pitch_heights(len(beats), accent)
    cursor = x
    spans = []
    for index, beat in enumerate(beats):
        width = f.width(beat)
        colour = ink
        if style == "colour":
            colour = line if high[index] else low_ink
        s.text(cursor, y, beat, font_name, colour)
        if index in whispered:
            for dot in range(cursor + 2, cursor + width - 2, 3):
                s.pixel(dot, y + f.height, cs_rgb(particle_ink))
        spans.append((cursor, cursor + width, high[index]))
        cursor += width
        if style == "colour" and accent == index + 1:
            for step in range(5):
                s.pixel(cursor - 1 + step // 2, y + 2 + step, cs_rgb(line))
                s.pixel(cursor + step // 2, y + 2 + step, cs_rgb(line))
            cursor += 4
    word_end = cursor
    if particle:
        particle_high = accent == 0
        colour = particle_ink
        if style == "colour":
            colour = line if particle_high else low_ink
        width = f.width(particle)
        s.text(cursor, y, particle, font_name, colour)
        spans.append((cursor, cursor + width, particle_high))
        cursor += width
    if style == "line":
        top = y - 4
        index = 0
        while index < len(spans):
            if not spans[index][2]:
                index += 1
                continue
            start = spans[index][0]
            while index + 1 < len(spans) and spans[index + 1][2]:
                index += 1
            end = spans[index][1]
            s.fill_rect(start + 1, top, end - start - 1, 2, line)
            if start > x:
                s.fill_rect(start + 1, top, 2, 5, line)      # the rise
            falls = accent != 0 and end <= word_end + 1
            if falls:
                s.fill_rect(end - 2, top, 2, 7, line)        # the fall
            index += 1
    if style == "number":
        s.rect(cursor + 4, y + 2, 13, f.height - 3, line)
        s.text(cursor + 8, y + (f.height - 12) // 2 + 1, str(accent), F12, line)
        cursor += 18
    return cursor


def cs_rgb(color):
    from cardputer_screen import rgb565
    return rgb565(color)


def pron_card():
    s = shell("発音  pronunciation", "5 beats")
    s.text(6, 21, "大丈夫", G32, INK)
    a = pitch_word(s, 112, 25, "だいじょうぶ", 3, F16)
    b = s.text(112, 44, "da·i·jo·o·bu", F12, DIM)[0]
    s.hline(4, 62, WIDTH - 8, FAINT)
    s.text(6, 66, "ぶんで", F12, DIM)
    c = pitch_word(s, 52, 70, "だいじょうぶ", 3, F16)
    c = pitch_word(s, c, 70, "です", 0, F16, line=BG, whispered=(1,), ink=INK)
    s.text(c, 70, "。", F16, INK)
    d = s.text(6, 92, "line = high ・ hook = falls after じょ", F12, DIM)[0]
    e = s.text(6, 105, "dots = whispered: desu sounds “des”", F12, DIM)[0]
    g = footer(s, "Space 聞く  S ゆっくり  R ろくおん")
    check("pron_card", s, a, b, c + 16, d, e, g)
    return s


def pron_option(style, title):
    s = shell(title, "はし × 3")
    rows = (("箸", "はし", 1, "chopsticks"), ("橋", "はし", 2, "bridge"), ("端", "はし", 0, "edge"))
    y = 22
    ends = []
    for kanji, kana, accent, gloss in rows:
        s.text(6, y - 2, kanji, F16, INK)
        ends.append(pitch_word(s, 40, y, kana, accent, F16, particle="が", style=style))
        ends.append(s.text(WIDTH - 6, y + 2, gloss, F12, DIM, align="right")[0])
        y += 24
    s.hline(4, 93, WIDTH - 8, FAINT)
    ends.append(pitch_word(s, 40, 100, "ありがとう", 2, F16, style=style))
    ends.append(s.text(WIDTH - 6, 102, "thank you", F12, DIM, align="right")[0])
    check("pron_" + style, s, *ends)
    return s


def ear_training():
    s = shell("聞き分け  which one?", "6/10")
    s.text(WIDTH // 2, 18, "♪  はし", F16, ACCENT, align="center")
    options = (("1", "箸", "chopsticks", False), ("2", "橋", "bridge", True), ("3", "端", "edge", False))
    ends = []
    for index, (key, kanji, gloss, chosen) in enumerate(options):
        x = 6 + index * 78
        s.round_rect(x, 40, 72, 44, 4, (30, 90, 60) if chosen else (34, 40, 52))
        s.text(x + 4, 42, key, F10, DIM)
        s.text(x + 36, 44, kanji, F24, INK, align="center")
        ends.append(s.text(x + 36, 69, gloss, F12, INK if chosen else DIM, align="center")[0])
    s.text(6, 93, "〇", F16, GOOD)
    a = pitch_word(s, 28, 95, "はし", 2, F16, particle="が")
    ends.append(s.text(a + 10, 96, "rises, falls after し", F12, DIM)[0])
    ends.append(footer(s, "Space もう一度   1 2 3 こたえる"))
    check("ear", s, *ends)
    return s


def echo_pitch():
    s = shell("オウム返し  echo", "2/5")
    a = pitch_word(s, 6, 23, "すみません", 4, F16)
    s.text(a, 23, "、", F16, INK)
    b = pitch_word(s, 6, 47, "えき", 1, F16, particle="は")
    c = pitch_word(s, b + 10, 47, "どこ", 1, F16)
    c = pitch_word(s, c, 47, "です", 1, F16, line=BG, whispered=(1,))
    c = s.text(c, 47, "か。", F16, INK)[0]
    s.text(6, 72, "手本", F12, DIM)
    s.fill_rect(46, 75, 144, 6, GOOD)
    s.text(196, 72, "2.1 s", F12, DIM)
    s.text(6, 88, "あなた", F12, DIM)
    s.fill_rect(46, 91, 144, 6, (40, 46, 58))
    s.fill_rect(46, 91, 84, 6, BAD)
    s.round_rect(196, 88, 10, 10, 5, BAD)
    s.text(210, 88, "REC", F12, BAD)
    d = s.text(6, 104, "then: model → you → model", F12, DIM)[0]
    e = footer(s, "1 もう一度   2 つぎ   3 もじを かくす")
    check("echo_pitch", s, a + 16, c, d, e)
    return s


def evening_check():
    s = shell("発音チェック  evening", "オンライン")
    beats = (("お", GOOD), ("ね", GOOD), ("が", WAIT), ("い", GOOD), ("し", GOOD), ("ま", GOOD), ("す", BAD))
    x = 12
    for beat, colour in beats:
        s.text(x, 20, beat, F24, colour)
        s.fill_rect(x + 2, 46, 20, 3, colour)
        x += 30
    a = s.text(6, 56, "す scored low. Try whispering: “mas”.", F12, INK)[0]
    b = s.text(6, 70, "が scored lower. Listen once more.", F12, DIM)[0]
    s.hline(4, 86, WIDTH - 8, FAINT)
    c = s.text(6, 91, "sounds 84   flow 92   complete 100", F12, ACCENT)[0]
    d = s.text(6, 105, "pitch is not scored by any service", F12, FAINT)[0]
    e = footer(s, "Space 聞く   R もう一度   Enter つぎ")
    check("evening_check", s, x, a, b, c, d, e)
    return s


# ---------------------------------------------------------------------------------------------
# Look directions: the same screen drawn in different styles, for choosing the visual direction.
# ---------------------------------------------------------------------------------------------

def look(name):
    word, reading, gloss, typed = "改札", "かいさつ", "ticket gate", "kaisatsu"
    ends = []
    if name == "eki":  # station signage
        s = Screen((12, 32, 72))
        s.fill_rect(0, 0, WIDTH, 16, (255, 255, 255))
        s.text(4, 2, "ひろう", F12, (12, 32, 72))
        s.text(WIDTH - 4, 2, "京都駅 14:32", F12, (12, 32, 72), align="right")
        s.fill_rect(0, 16, WIDTH, 4, (240, 130, 0))
        s.text(8, 26, word, G32, INK)
        ends.append(s.text(84, 28, reading, F16, INK)[0])
        ends.append(s.text(84, 46, gloss, F12, (190, 205, 235))[0])
        s.fill_rect(8, 66, WIDTH - 16, 1, (255, 255, 255))
        ends.append(s.text(8, 72, "改札口  かいさつぐち", F12, (190, 205, 235))[0])
        ends.append(s.text(8, 86, "開札  かいさつ", F12, (190, 205, 235))[0])
        s.fill_rect(0, HEIGHT - 17, WIDTH, 17, (255, 255, 255))
        ends.append(s.text(6, HEIGHT - 15, "▶ " + typed + "_", F12, (12, 32, 72))[0])
        s.text(WIDTH - 6, HEIGHT - 15, "Enter ほぞん", F12, (240, 130, 0), align="right")
    elif name == "techo":  # paper notebook
        s = Screen(PAPER)
        for y in range(31, HEIGHT, 17):
            s.hline(0, y, WIDTH, (205, 215, 225))
        s.fill_rect(22, 0, 1, HEIGHT, (235, 150, 150))
        s.text(28, 1, "ひろう", F12, (120, 110, 100))
        s.text(WIDTH - 4, 1, "9月30日 京都駅", F12, (120, 110, 100), align="right")
        s.text(28, 17, word, G32, SUMI)
        ends.append(s.text(102, 20, reading, F16, SUMI)[0])
        ends.append(s.text(102, 38, gloss, F12, (90, 90, 100))[0])
        s.round_rect(196, 18, 30, 30, 15, SHU, fill=False)
        s.round_rect(197, 19, 28, 28, 14, SHU, fill=False)
        s.text(211, 25, "拾", F16, SHU, align="center")
        ends.append(s.text(28, 70, "改札口  かいさつぐち", F12, (90, 90, 100))[0])
        ends.append(s.text(28, 87, "開札  かいさつ", F12, (90, 90, 100))[0])
        ends.append(s.text(28, 120, "▶ " + typed + "_", F12, (30, 60, 140))[0])
    elif name == "denkou":  # LED departure board
        s = Screen((0, 0, 0))
        amber, green, red = (255, 170, 0), (60, 230, 90), (255, 60, 40)
        s.text(4, 2, "ひろう", F12, green)
        s.text(WIDTH - 4, 2, "14:32 京都", F12, amber, align="right")
        s.hline(0, 16, WIDTH, (60, 40, 0))
        s.text(6, 22, word, G32, amber)
        ends.append(s.text(82, 24, reading, F16, green)[0])
        ends.append(s.text(82, 42, gloss, F12, amber)[0])
        s.hline(0, 62, WIDTH, (60, 40, 0))
        ends.append(s.text(6, 68, "改札口  かいさつぐち", F12, (170, 110, 0))[0])
        ends.append(s.text(6, 84, "開札  かいさつ", F12, (170, 110, 0))[0])
        s.hline(0, HEIGHT - 18, WIDTH, (60, 40, 0))
        ends.append(s.text(6, HEIGHT - 15, typed + "_", F12, red)[0])
        s.text(WIDTH - 6, HEIGHT - 15, "Enter ほぞん", F12, green, align="right")
    elif name == "rpg":  # retro game windows
        s = Screen((0, 0, 0))
        s.round_rect(2, 2, WIDTH - 4, 70, 4, INK, fill=False)
        s.round_rect(3, 3, WIDTH - 6, 68, 3, INK, fill=False)
        s.fill_rect(12, 0, 46, 6, (0, 0, 0))
        s.text(14, -3, "ひろう", F12, INK)
        s.text(10, 14, "▶", F16, INK)
        s.text(30, 8, word, G32, INK)
        ends.append(s.text(104, 12, reading, F16, INK)[0])
        ends.append(s.text(104, 30, gloss, F12, (160, 200, 255))[0])
        ends.append(s.text(30, 50, "改札口 かいさつぐち ・ 開札", F12, (150, 150, 150))[0])
        s.round_rect(2, 76, WIDTH - 4, 57, 4, INK, fill=False)
        s.round_rect(3, 77, WIDTH - 6, 55, 3, INK, fill=False)
        daruma(s, 28, 106)
        ends.append(s.text(54, 84, "「改札」を ひろった！", F16, INK)[0])
        ends.append(s.text(54, 104, "けいけんち +3", F12, (255, 220, 90))[0])
        s.text(WIDTH - 12, 116, "▼", F12, INK, align="right")
    elif name == "ai":  # indigo and cream
        s = Screen((24, 40, 82))
        cream = (245, 236, 214)
        for x in range(4, WIDTH, 8):
            s.fill_rect(x, 17, 4, 1, cream)
        s.text(6, 2, "ひろう", F12, cream)
        s.text(WIDTH - 6, 2, "京都駅 14:32", F12, (170, 185, 220), align="right")
        s.round_rect(6, 24, WIDTH - 12, 44, 4, cream)
        s.text(14, 30, word, G32, (24, 40, 82))
        ends.append(s.text(90, 30, reading, F16, (24, 40, 82))[0])
        ends.append(s.text(90, 48, gloss, F12, (90, 100, 130))[0])
        ends.append(s.text(10, 74, "改札口  かいさつぐち", F12, (170, 185, 220))[0])
        ends.append(s.text(10, 90, "開札  かいさつ", F12, (170, 185, 220))[0])
        for x in range(4, WIDTH, 8):
            s.fill_rect(x, HEIGHT - 19, 4, 1, cream)
        ends.append(s.text(6, HEIGHT - 15, typed + "_", F12, (255, 200, 120))[0])
        s.text(WIDTH - 6, HEIGHT - 15, "Enter ほぞん", F12, cream, align="right")
    elif name == "tanmatsu":  # terminal
        s = Screen((0, 10, 0))
        g1, g2, g3 = (80, 255, 120), (40, 170, 80), (20, 90, 40)
        s.text(4, 2, "hirou@kyoto-eki:~$ " + typed + "_", F12, g1)
        s.hline(0, 17, WIDTH, g3)
        s.text(6, 22, "1", F12, g3)
        s.text(20, 20, word, F24, g1)
        ends.append(s.text(76, 21, reading, F12, g1)[0])
        ends.append(s.text(76, 34, gloss, F12, g2)[0])
        s.text(6, 54, "2", F12, g3)
        ends.append(s.text(20, 50, "改札口", F16, g2)[0])
        ends.append(s.text(76, 53, "かいさつぐち ticket barrier", F12, g3)[0])
        s.text(6, 74, "3", F12, g3)
        ends.append(s.text(20, 70, "開札", F16, g2)[0])
        ends.append(s.text(76, 73, "かいさつ opening of bids", F12, g3)[0])
        s.hline(0, HEIGHT - 18, WIDTH, g3)
        ends.append(s.text(4, HEIGHT - 15, "[1-3] save  [tab] kana  [esc] back", F12, g2)[0])
    elif name == "washi":  # light, vermilion accents
        s = Screen((253, 250, 243))
        s.fill_rect(0, 0, 6, HEIGHT, SHU)
        s.text(14, 2, "ひろう", F12, SHU)
        s.text(WIDTH - 6, 2, "京都駅 14:32", F12, (130, 120, 110), align="right")
        s.hline(14, 17, WIDTH - 20, (225, 215, 200))
        s.text(14, 22, word, G40, SUMI)
        ends.append(s.text(104, 26, reading, F16, SUMI)[0])
        ends.append(s.text(104, 45, gloss, F12, (110, 100, 95))[0])
        s.hline(14, 68, WIDTH - 20, (225, 215, 200))
        ends.append(s.text(14, 73, "改札口  かいさつぐち", F12, (110, 100, 95))[0])
        ends.append(s.text(14, 89, "開札  かいさつ", F12, (110, 100, 95))[0])
        s.round_rect(12, HEIGHT - 20, WIDTH - 18, 18, 3, (240, 233, 220))
        ends.append(s.text(18, HEIGHT - 17, typed + "_", F12, SUMI)[0])
        s.text(WIDTH - 12, HEIGHT - 17, "Enter ほぞん", F12, SHU, align="right")
    elif name == "yoru":  # quiet dark, one accent
        s = Screen((16, 16, 20))
        s.text(6, 3, "ひろう", F12, (120, 120, 130))
        s.text(WIDTH - 6, 3, "14:32", F12, (120, 120, 130), align="right")
        s.text(8, 24, word, G40, INK)
        ends.append(s.text(98, 28, reading, F16, (255, 140, 105))[0])
        ends.append(s.text(98, 47, gloss, F12, (170, 170, 180))[0])
        ends.append(s.text(8, 76, "改札口  かいさつぐち", F12, (110, 110, 120))[0])
        ends.append(s.text(8, 92, "開札  かいさつ", F12, (110, 110, 120))[0])
        s.fill_rect(8, HEIGHT - 20, WIDTH - 16, 1, (60, 60, 70))
        ends.append(s.text(8, HEIGHT - 16, typed + "_", F12, INK)[0])
    else:
        raise KeyError(name)
    check("look_" + name, s, *ends)
    return s


# ---------------------------------------------------------------------------------------------
# Round two: the four chosen looks, each drawn on three screens.
# ---------------------------------------------------------------------------------------------

class Theme:
    def __init__(self, **values):
        self.__dict__.update(values)


NAVY = (12, 32, 72)
THEMES = {
    "eki": Theme(key="eki", bg=NAVY, ink=INK, dim=(190, 205, 235), faint=(70, 95, 150), accent=(255, 165, 50),
                 good=(130, 235, 160), bad=(255, 135, 125), row=(30, 56, 110), type=(255, 255, 255), left=6, top=24),
    "techo": Theme(key="techo", bg=PAPER, ink=SUMI, dim=(95, 95, 105), faint=(205, 215, 225), accent=SHU,
                   good=(20, 120, 60), bad=(190, 30, 30), row=(255, 238, 160), type=(30, 60, 140), left=28, top=18),
    "rpg": Theme(key="rpg", bg=(0, 0, 0), ink=INK, dim=(160, 160, 160), faint=(90, 90, 90), accent=(255, 220, 90),
                 good=(120, 255, 140), bad=(255, 110, 110), row=(40, 40, 70), type=(255, 255, 255), left=12, top=16),
    "washi": Theme(key="washi", bg=(253, 250, 243), ink=SUMI, dim=(110, 100, 95), faint=(225, 215, 200), accent=SHU,
                   good=(30, 120, 70), bad=(170, 30, 30), row=(244, 232, 214), type=SUMI, left=14, top=20),
}


def window(s, x, y, w, h, title=None, ink=INK):
    s.round_rect(x, y, w, h, 4, ink, fill=False)
    s.round_rect(x + 1, y + 1, w - 2, h - 2, 3, ink, fill=False)
    if title:
        width = font(F12).width(title) + 8
        s.fill_rect(x + 10, y, width, 3, (0, 0, 0))
        s.text(x + 14, y - 5, title, F12, ink)


def themed_frame(t, title, right, footer_left, footer_right=""):
    """Background, header and footer in the theme's manner. Returns the screen."""
    s = Screen(t.bg)
    ends = []
    if t.key == "eki":
        s.fill_rect(0, 0, WIDTH, 16, (255, 255, 255))
        s.text(4, 2, title, F12, NAVY)
        s.text(WIDTH - 4, 2, right, F12, NAVY, align="right")
        s.fill_rect(0, 16, WIDTH, 4, (240, 130, 0))
        s.fill_rect(0, HEIGHT - 17, WIDTH, 17, (255, 255, 255))
        ends.append(s.text(6, HEIGHT - 15, footer_left, F12, NAVY)[0])
        s.text(WIDTH - 6, HEIGHT - 15, footer_right, F12, (200, 95, 0), align="right")
    elif t.key == "techo":
        for y in range(14, HEIGHT, 17):
            s.hline(0, y, WIDTH, t.faint)
        s.fill_rect(22, 0, 1, HEIGHT, (235, 150, 150))
        s.text(28, 1, title, F12, (120, 110, 100))
        s.text(WIDTH - 4, 1, right, F12, (120, 110, 100), align="right")
        ends.append(s.text(28, HEIGHT - 15, footer_left, F12, t.type)[0])
        s.text(WIDTH - 4, HEIGHT - 15, footer_right, F12, (120, 110, 100), align="right")
    elif t.key == "rpg":
        window(s, 2, 5, WIDTH - 4, 86, title)
        width = font(F12).width(right) + 8
        s.fill_rect(WIDTH - 14 - width, 5, width, 3, (0, 0, 0))
        s.text(WIDTH - 18, 0, right, F12, t.dim, align="right")
        window(s, 2, 95, WIDTH - 4, 39)
        daruma_small(s, 22, 114)
        ends.append(s.text(42, 117, footer_left, F12, t.dim)[0])
        s.text(WIDTH - 12, 117, footer_right, F12, t.accent, align="right")
    elif t.key == "washi":
        s.fill_rect(0, 0, 6, HEIGHT, SHU)
        s.text(14, 2, title, F12, SHU)
        s.text(WIDTH - 6, 2, right, F12, (130, 120, 110), align="right")
        s.hline(14, 17, WIDTH - 20, t.faint)
        s.round_rect(12, HEIGHT - 20, WIDTH - 18, 18, 3, (240, 233, 220))
        ends.append(s.text(18, HEIGHT - 17, footer_left, F12, SUMI)[0])
        s.text(WIDTH - 12, HEIGHT - 17, footer_right, F12, SHU, align="right")
    return s, ends


def themed_catcher(key):
    t = THEMES[key]
    s, ends = themed_frame(t, "ひろう", "京都駅 14:32", "kaisatsu_", "Enter ほぞん")
    x, y = t.left, t.top
    if key == "rpg":
        s.text(x, y + 10, "▶", F16, t.ink)
        x += 16
    if key == "techo":
        s.fill_rect(x - 2, 17, 172, 30, t.row)
        s.hline(x - 2, 31, 172, (240, 222, 140))
    if key == "techo":
        s.text(x, 15, "改札", G32, t.ink)
        ends.append(pitch_word(s, x + 76, 19, "かいさつ", 0, F16, ink=t.ink, line=t.accent))
        ends.append(s.text(x + 76, 35, "ticket gate", F12, t.dim)[0])
    else:
        s.text(x, y, "改札", G32, t.ink)
        ends.append(pitch_word(s, x + 76, y + 6, "かいさつ", 0, F16, ink=t.ink, line=t.accent))
        ends.append(s.text(x + 76, y + 24, "ticket gate", F12, t.dim)[0])
    if key == "techo":
        s.round_rect(204, 20, 30, 30, 15, SHU, fill=False)
        s.round_rect(205, 21, 28, 28, 14, SHU, fill=False)
        s.text(219, 27, "拾", F16, SHU, align="center")
    if key in ("eki", "washi"):
        s.hline(t.left, y + 44, WIDTH - t.left - 8, t.ink if key == "eki" else t.faint)
    second = y + 50 if key != "techo" else 70
    third = second + (14 if key != "techo" else 17)
    if key == "rpg":
        second, third = 58, 72
    if key == "techo":
        second, third = 51, 68
    ends.append(s.text(t.left if key != "rpg" else 28, second, "改札口  かいさつぐち", F12, t.dim)[0])
    ends.append(s.text(t.left if key != "rpg" else 28, third, "開札  かいさつ", F12, t.dim)[0])
    if key == "rpg":
        ends.append(s.text(42, 100, "「改札」を みつけた！", F16, t.ink)[0])
    check("round2_catcher_" + key, s, *ends)
    return s


def themed_sign(key):
    t = THEMES[key]
    s, ends = themed_frame(t, "看板", "駅 3/10", "Space 聞く", "Enter つぎ")
    if key == "eki":
        s.round_rect(34, 26, 172, 46, 4, (255, 255, 255))
        s.fill_rect(34, 62, 172, 5, (240, 130, 0))
        s.text(WIDTH // 2, 28, "精算機", G32, NAVY, align="center")
        base = 78
    elif key == "techo":
        s.fill_rect(56, 20, 140, 45, PAPER)
        s.rect(56, 20, 140, 45, SUMI)
        s.rect(58, 22, 136, 41, SUMI)
        s.text(126, 26, "精算機", G32, SUMI, align="center")
        base = 73
    elif key == "rpg":
        s.text(WIDTH // 2, 14, "精算機", G32, t.ink, align="center")
        base = 54
    else:
        s.text(WIDTH // 2, 22, "精算機", G40, t.ink, align="center")
        base = 70
    width = font(F16).width("せいさんき")
    start = (WIDTH - width) // 2 - 10
    end = pitch_word(s, start, base, "せいさんき", 3, F16, ink=t.good, line=t.accent)
    s.text(end + 6, base, "〇", F16, t.good)
    ends.append(end + 22)
    gloss_y = base + 19
    if key == "techo":
        gloss_y = 104
    ends.append(s.text(WIDTH // 2, gloss_y, "fare adjustment machine", F12, t.dim, align="center")[0])
    if key == "rpg":
        ends.append(s.text(42, 100, "せいかい！", F16, t.good)[0])
        ends.append(s.text(126, 103, "けいけんち +3", F12, t.accent)[0])
    check("round2_sign_" + key, s, *ends)
    return s


def themed_home(key):
    t = THEMES[key]
    s, ends = themed_frame(t, "3日目  京都", "マナー ● 82%", "なにか キーを おすと はじまる")
    if key == "rpg":
        s.text(14, 18, "ことば 12", F12, t.ink)
        s.text(14, 34, "ミッション 2", F12, t.ink)
        s.text(14, 50, "スタンプ 3/12", F12, t.ink)
        ends.append(s.text(124, 18, "ひろった", F12, t.dim)[0])
        ends.append(s.text(124, 34, "改札  替玉", F12, t.accent)[0])
        ends.append(s.text(124, 50, "拝観料", F12, t.accent)[0])
        s.fill_rect(14, 72, 150, 6, t.faint)
        s.fill_rect(14, 72, 96, 6, t.good)
        ends.append(s.text(172, 68, "Lv 3", F12, t.ink)[0])
        ends.append(s.text(42, 101, "おはよう！今日は京都だね。", F12, t.ink)[0])
        check("round2_home_" + key, s, *ends)
        return s
    left = t.left
    top = t.top + (2 if key != "techo" else 4)
    daruma(s, left + 20, top + 26)
    bubble = (255, 255, 255) if key == "eki" else t.row
    s.round_rect(left + 48, top, WIDTH - left - 56, 50, 5, bubble)
    s.fill_rect(left + 44, top + 22, 6, 6, bubble)
    ink = NAVY if key == "eki" else SUMI
    ends.append(s.text(left + 56, top + 6, "おはよう！", F16, ink)[0])
    ends.append(s.text(left + 56, top + 25, "今日は京都だね。", F16, ink)[0])
    row = top + 58 if key != "techo" else 87
    ends.append(s.text(left, row, "ことば 12 ・ ミッション 2", F12, t.ink)[0])
    ends.append(s.text(left, row + (15 if key != "techo" else 17), "ひろった", F12, t.dim)[0])
    ends.append(s.text(left + 58, row + (15 if key != "techo" else 17), "改札  替玉  拝観料", F12, t.accent)[0])
    check("round2_home_" + key, s, *ends)
    return s


ROUND_TWO = ["eki", "techo", "rpg", "washi"]


IDEAS = [
    ("catcher", catcher), ("queue", queue), ("numbers", numbers), ("staff", staff_lines), ("sign", sign_sprint),
    ("katakana", katakana), ("counters", counters), ("tomorrow", tomorrow), ("diary", diary),
    ("rehearsal", rehearsal), ("show_card", show_card), ("missions", missions), ("buddy", buddy), ("shadowing", shadowing),
    ("station", station_quiz), ("menu", menu_decoder), ("snapshot", snapshot), ("remote", remote),
]
LOOKS = ["eki", "techo", "denkou", "rpg", "ai", "tanmatsu", "washi", "yoru"]
PRONUNCIATION = [
    ("pron_card", pron_card),
    ("pron_line", lambda: pron_option("line", "A  line and hook")),
    ("pron_colour", lambda: pron_option("colour", "B  bright is high")),
    ("pron_number", lambda: pron_option("number", "C  accent number")),
    ("ear", ear_training), ("echo_pitch", echo_pitch), ("evening_check", evening_check),
]


def render_all(out, scale=3):
    """Writes every screen as a PNG. scale enlarges each device pixel; 1 is the panel's true 240x135."""
    written = []
    for name, build in IDEAS:
        written.append(build().save(os.path.join(out, "idea_%s.png" % name), scale))
    for name in LOOKS:
        written.append(look(name).save(os.path.join(out, "look_%s.png" % name), scale))
    for name, build in PRONUNCIATION:
        written.append(build().save(os.path.join(out, "%s.png" % name), scale))
    for key in ROUND_TWO:
        written.append(themed_catcher(key).save(os.path.join(out, "round2_%s_catcher.png" % key), scale))
        written.append(themed_sign(key).save(os.path.join(out, "round2_%s_sign.png" % key), scale))
        written.append(themed_home(key).save(os.path.join(out, "round2_%s_home.png" % key), scale))
    return written


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "concepts")
    files = render_all(target)
    print("%d screens written to %s" % (len(files), target))
    for line in problems:
        print("CHECK " + line)
    sys.exit(1 if problems else 0)
