# Tests for the deck build

```
python3 tools/tests/test_build_decks.py              # everything
python3 tools/tests/test_build_decks.py accent       # the tests whose name contains a word
python3 tools/tests/test_build_decks.py --allow-skips
```

The script runs `tools/build_decks.py` on the folders in `fixtures/` and compares what it prints
with the list at the top of the script: file, line, error or warning, and the words of the message.
A finding that is missing fails the test, and so does a finding that was not expected.

It writes only into `build/test_build_decks/`.

Two tests need Emscripten and Node: they compile the C++ the tool writes against
`lib/core/deck.h`, run it, and compare every field it prints with the fixture. Two tests need the
dictionary files in `local/cache/`. Where these are missing the tests are skipped, and the run
counts as incomplete unless `--allow-skips` is given. Where only KANJIDIC is missing there, the
two tests leave out what needs it and say so.

## Fixtures

Each folder is laid out like `content/`: deck files in `decks/`, and beside them `buddy.tsv`,
`kanji.tsv`, `parts.tsv`, `guide.tsv` and `ids.txt` where the test needs them. The list of ids is
copied before a test, so the fixture itself is never changed. The tables and their rules are
described in `content/README.md`.

The folder `clean` has no mistakes and builds. Every other folder shows one kind of mistake, and
says so in its first line. The Japanese in the fixtures is real, apart from the mistakes themselves.

| Folder | What it shows |
|---|---|
| `clean` | eight decks of all four kinds with every table beside them and an older list of ids; one deck has no stage; one word has its line in `parts.tsv`, two have none there, one by the word `EMPTY` and one by an empty value; a page of the guide has two clips that are spelt alike; builds |
| `first-build` | one deck and nothing beside it; builds |
| `header-wrong`, `header-missing` | the header row has another column name, or is not there |
| `empty-file` | a deck file with nothing in it |
| `columns`, `row-of-tabs` | a row with 8 columns and one with 10; a row that holds tabs and no values |
| `names-missing`, `names-wrong`, `names-twice` | the `# name-ja`, `# name-en` and `# kind` lines |
| `names-below-header` | name lines that stand below the header row |
| `stage-wrong` | a stage that is not a number from 1 to 9: 0, 10, 1.5, a word, nothing; a stage given twice; a line that was meant to give the stage and is not read: no colon, a capital letter, an equals sign |
| `file-name` | a deck file whose name is not a deck id |
| `no-decks`, `no-rows` | a folder without deck files, a deck without rows |
| `other-files` | a file in the deck folder that is not a deck: warning, because it is left out |
| `edge-spaces`, `empty-fields` | a space before or after a value; an empty prompt, reading or gloss |
| `id-format`, `id-duplicate` | ids that are not well formed; an id used twice, in one deck and in two |
| `id-disappeared` | an id in `ids.txt` that no deck has any more |
| `id-key-clash` | two ids that `deck::key` turns into the same number |
| `reading-not-kana`, `accepted-not-kana` | kanji, Latin letters or a space in an answer |
| `accepted-empty-part` | a stray `|`, which would make the empty answer right |
| `accepted-twice` | an accepted answer given twice, or the same as the reading: warning |
| `untypable` | kana that no romaji produces on the device (こゝろ) |
| `answer-long` | a price whose reading takes 49 letters, one more than the answer line takes, next to one of 48 |
| `accent-beats`, `accent-not-a-number` | an accent larger than the number of beats; an accent that is no number |
| `glyph-missing` | characters that `efontJA_16` and `efontJA_12` lack: error |
| `glyph-big-font` | a prompt character that `lgfxJapanGothic_32` lacks: warning |
| `gloss-long`, `note-long` | one letter too many, next to values of exactly the allowed width, in English and in Japanese |
| `level-wrong`, `level-1-kanji` | a level that is not 1, 2 or 3; kanji in a level 1 prompt |
| `dict-reading` | a reading JMdict does not have for the word |
| `dict-no-headword` | a word JMdict does not have: error with the source `JMdict` or none, warning with another |
| `dict-accepted` | an accepted answer that JMdict does not have for the word: warning |
| `dict-accent-not-listed` | an accent that the accent list does not give for the word |
| `dict-accent-second` | an accent that the accent list gives, but not as the first one: warning; none where the accent depends on the part of speech |
| `dict-accent-no-entry` | an accent for a word, a kana spelling and a counter that the accent list does not have |
| `dict-accent-part-of-speech` | a word whose accent depends on the part of speech: none is filled in |
| `dict-other-kinds` | kana cards whose prompt is also a word in the accent list: none is filled in |
| `romaji-help` | readings with づ, ティ and ー, which are typed du, thi and with a hyphen; builds |
| `buddy-mood`, `buddy-ja-not-kana`, `buddy-ja-long`, `buddy-en-long` | one rule of the buddy file each |
| `buddy-id`, `buddy-columns`, `buddy-empty`, `buddy-header` | the table of the buddy file |
| `kanji-not-one` | a row of `kanji.tsv` for a word, a kana, a Latin letter and nothing |
| `kanji-twice` | a kanji with two rows |
| `kanji-meaning` | a meaning with a capital letter, two spaces, a hyphen at its end or a digit; one of 13 letters next to one of 12; none, which also leaves a card without it: warning |
| `kanji-basis` | a basis that KANJIDIC does not give for the kanji, or spells otherwise; none; a word without the kanji; a word that JMdict lacks |
| `kanji-no-row` | kanji of prompts without a row: warning, once for each kanji |
| `kanji-line-wide` | a card whose line is 60 letters wide, next to one of 54: warning |
| `kanji-words` | `words` that are no prompts or lack the kanji; rows of kanji that no prompt has: warning |
| `parts-prompt` | a row of `parts.tsv` for what is no prompt, for a reading, for nothing; a prompt with two rows |
| `parts-kanji` | a line that names a kanji the prompt does not have |
| `parts-long` | a line of 55 letters next to one of 54, in English and with kana |
| `parts-piece` | a piece of 28 letters next to one of 27; pieces three and four spaces apart |
| `parts-no-line` | a line that names no character of its prompt: `empty`, a hyphen, the meaning alone; next to `EMPTY`, which stands for no line |
| `parts-reason` | no reason, with a line and without one |
| `parts-glyph` | a line with a character the fonts lack |
| `guide-id` | ids of `guide.tsv` that are not well formed, used twice, or used by an item or a line of the buddy |
| `guide-title` | a title of 21 letters next to one of 20, with and without kana; no title |
| `guide-line-wide` | a line of 28 letters next to one of 27, with and without kana |
| `guide-lines` | six lines next to five; no body; a body of bars alone |
| `guide-clips` | clips in Latin letters, in kanji, with a space; a stray bar; next to two clips that are spelt alike, which is no mistake |
| `guide-glyph` | a title, a body and a clip with a character the fonts lack |
| `kanji-header`, `parts-header`, `guide-header` | another column name in the header row of each table |

More files are made by the script itself, because they are awkward to keep in a repository: a
deck that is not UTF-8, decks with characters that cannot be seen (a zero byte, a zero width
space, a byte order mark in the middle), a folder where a file is expected, dictionaries that
cannot be read, and tables that are named by an option. Decks and tables with Windows or old Mac
line ends or with a byte order mark at their start are built, with a warning.

A deck that cannot be read is one finding: the tables beside the decks are then not compared with
the prompts, because every row of theirs would be another.

## The buddy file

Moods: greeting, start, right, streak, wrong, almost, finish, back, low-battery, idle

A test compares this line, and the same line in `content/README.md`, with the moods the tool
takes. Another looks for every column of every table in `content/README.md`.

## The dictionary excerpt

`fixtures/cache/` holds the entries of the words and kanji used in the fixtures, in the format of
the files in `local/cache/`. `jmdict_index.json` is an excerpt of JMdict, `kanjidic_index.json` an
excerpt of KANJIDIC (both: Electronic Dictionary Research and Development Group), `accents.txt` an
excerpt of the accent list of the Kanjium project. All three are shared under CC BY-SA 4.0. A test
compares the excerpt with the full files, entry by entry.
