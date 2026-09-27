# Content

Everything the device teaches is written here as plain tables and compiled into the firmware by
`tools/build_decks.py`. The tool refuses to build when a row is wrong, so that a mistake is found
on the computer and not on the device.

| File | What it holds | Needed |
|---|---|---|
| `decks/<deck id>.tsv` | the cards, one deck per file | at least one |
| `buddy.tsv` | what the buddy on the home screen says | no |
| `kanji.tsv` | what each kanji of the prompts means | no |
| `parts.tsv` | the line about the kanji of a word, where it is written by hand | no |
| `guide.tsv` | the pages of the guide to how Japanese sounds | no |
| `ids.txt` | every id ever published; written by the tool | written on the first build |

All tables are UTF-8 with Unix line ends, tab separated, with a header row. Lines starting with `#`
are comments. No value starts or ends with a space. Widths are counted in letters: a Japanese
character is as wide as two.

```
python3 tools/build_decks.py --check    # check only
python3 tools/build_decks.py            # check, then write lib/core/deck_data.cpp and content/ids.txt
python3 tools/build_decks.py --offline  # without the dictionaries
```

## Deck files

One file per deck in `content/decks/`, named `<deck id>.tsv`. The comment lines above the header
row carry what belongs to the deck as a whole:

```
# name-ja: かんばん
# name-en: signs
# kind: word
# stage: 3
```

| Line | Meaning | Rules |
|---|---|---|
| `name-ja` | Name of the deck in Japanese | kana and spaces |
| `name-en` | Name of the deck in English | |
| `kind` | What the cards ask | `kana`, `word`, `counter` or `number` |
| `stage` | Place in the course | a number from 1 to 9; 1 when the line is missing |

In the course, new cards come from the lowest stage that still has a card never seen. Decks of one
stage are learnt side by side. A line that starts with the word stage and is written otherwise,
such as `# stage 2` or `# Stage: 2`, is an error: the deck would be of stage 1 without a word.

| Column | Meaning | Rules |
|---|---|---|
| `id` | Stable name of the item | lower case letters, digits and hyphens; unique in the whole content; never reused for another item |
| `prompt` | What is shown | every character must exist in the device's fonts |
| `reading` | The main answer | kana only; hiragana, or katakana for a katakana word |
| `accent` | Pitch accent number of `reading` | 0 flat, k = falls after beat k, empty = unknown. Never a guess. |
| `accepted` | Further right answers | kana, separated by `\|`; empty if none |
| `gloss` | Meaning in English | at most 32 letters wide, so that it fits one line |
| `note` | What a learner needs to know about it | at most 52 letters wide, which is two lines; empty if none |
| `level` | 1, 2 or 3 | 1 kana only; 2 common kanji; 3 anything |
| `source` | Where the reading and meaning were checked | a dictionary name or a URL |

The decks are compiled in the order of the course: hiragana, katakana, numbers, counters,
katakana-words, signs. Any other deck follows, by name.

## buddy.tsv

One row for each thing the buddy can say.

| Column | Meaning | Rules |
|---|---|---|
| `id` | Stable name of the line | as for an item; not the id of an item |
| `mood` | When it is said | one of the ten below |
| `ja` | The line | kana, spaces and the marks 、。！？「」〜・ only; at most 15 characters, spaces included |
| `en` | What it means | at most 34 letters |

Moods: greeting, start, right, streak, wrong, almost, finish, back, low-battery, idle

## kanji.tsv

One row for each kanji of the prompts. From these rows the build puts together the line that a
card shows about its prompt: every kanji of the prompt once, in the order in which they stand, each
with its meaning, two spaces between them. 出口 gets `出 go out  口 opening`. The mark 々, which
repeats the kanji before it, is left out.

| Column | Meaning | Rules |
|---|---|---|
| `kanji` | The kanji | one kanji; once in the table |
| `meaning` | The sense it has in the deck words | lower case words with one space or hyphen between them; at most 12 letters |
| `basis` | What the meaning rests on | a meaning that KANJIDIC gives for the kanji, spelt as it is there; or `JMdict: ` and a JMdict headword written with the kanji, where KANJIDIC lacks the sense |
| `words` | Deck words with the kanji, for the reader | prompts written with the kanji, a space between them; may be empty |

The build warns, and builds all the same, where:

- a kanji of a prompt has no row: the line of that card then lacks it
- the line of a card is too wide: at most 54 letters fit, which is two lines, and what is more
  will be cut off
- `words` names what is no prompt, or a row is of a kanji that no prompt has

## parts.tsv

One row for each word whose line is written by hand. It takes the place of the line from
`kanji.tsv`, for a word whose characters are used for their sound, and for a word that one meaning
for each kanji does not explain: 交番 is not "alternate" and "number".

| Column | Meaning | Rules |
|---|---|---|
| `prompt` | The word | the prompt of an item, as it is written there; once in the table |
| `parts` | The line to show | pieces with two spaces between them; every kanji in it is a kanji of the prompt; at most 54 letters wide, and each piece at most 27; `EMPTY` or nothing for a card that is to show no line |
| `reason` | Why the line from `kanji.tsv` will not do | not empty |

A row holds for every item with that prompt. The kanji of such a word need no row in `kanji.tsv`.

The card breaks the line only where two spaces stand, and a line of the screen holds 27 letters:
a piece that is wider would be cut off. `自由 freedom  席 seat` has two pieces. The line names at
least one character of the prompt; the word `EMPTY`, in capitals, is the only other thing it may
hold, and is never shown.

## guide.tsv

One row for each page of the guide, in the order in which they are shown.

| Column | Meaning | Rules |
|---|---|---|
| `id` | Stable name of the page | as for an item; not the id of an item or of a line of the buddy |
| `title` | Heading of the page | at most 20 letters wide |
| `body` | The text | lines separated by `\|`; at most 5 lines, each at most 27 letters wide; not empty |
| `clips` | What can be heard on the page | kana, separated by `\|`; empty if nothing |

A clip is known by its page and its place in the row, not by its kana. The same kana may
therefore stand twice, for two words that are spelt alike and differ in pitch: `はし\|はし`.

## What the build checks

In every table:

- the header row names the columns above, in that order, and every row has as many values
- the file is UTF-8 and holds no character that cannot be seen
- no value starts or ends with a space
- every character exists in the fonts that draw it, `efontJA_16` and `efontJA_12`. A prompt whose
  characters are not all in the large fonts builds with a warning: it is drawn smaller.
- lengths and widths fit the screen, as given in the tables above

In the decks:

- ids are well formed and unique, no two ids give the same key in the progress files, and no id
  has disappeared since the last build (`content/ids.txt` lists every id ever published)
- every `reading` and `accepted` answer is kana and can be typed: its romaji, fed to the
  converter, gives the same kana back, and is not longer than the answer line
- `accent` is a number, and not larger than the number of beats
- a prompt of level 1 has no kanji

Against the dictionaries, unless `--offline` is given:

- a prompt of a deck of the kind `word` is a JMdict headword, and JMdict reads it as `reading`
  says. A word that JMdict lacks needs another source in the `source` column, and builds with a
  warning.
- an `accent` is one that the accent list gives for the word with this reading. Where a deck of
  the kind `word` gives none and the list gives one, the build fills it in and says so.
- a `basis` in `kanji.tsv` is a meaning that KANJIDIC gives for the kanji, or names a JMdict
  headword

The dictionaries are not in the repository. `tools/fetch_reference.py` puts JMdict and the accent
list into `local/cache/`. The build reads KANJIDIC from `local/cache/kanjidic_index.json`, a table
of the form `{"口": {"meanings": ["mouth"]}}`; where that file is missing, it says so in a note
and leaves that comparison out.

`tools/tests/` holds one small example of every mistake named here, and a test that the build
finds it.

## Licences

Readings and meanings are checked against JMdict, the meanings of single kanji against KANJIDIC
(both: Electronic Dictionary Research and Development Group, CC BY-SA 4.0). Pitch accents come
from the accent list of the Kanjium project (CC BY-SA 4.0). The tables here are therefore shared
under CC BY-SA 4.0.
