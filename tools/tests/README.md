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

Two tests need Emscripten and Node: they compile the C++ the tool writes, run it, and compare every
field it prints with the fixture. Two tests need the dictionary files in `local/cache/`. Where
these are missing the tests are skipped, and the run counts as incomplete unless `--allow-skips` is
given.

## Fixtures

Each folder is laid out like `content/`: deck files in `decks/`, and beside them `buddy.tsv` and
`ids.txt` where the test needs them. The list of ids is copied before a test, so the fixture itself
is never changed.

The folder `clean` has no mistakes and builds. Every other folder shows one kind of mistake, and
says so in its first line. The Japanese in the fixtures is real, apart from the mistakes themselves.

| Folder | What it shows |
|---|---|
| `clean` | seven decks of all four kinds, a buddy file and an older list of ids; builds |
| `first-build` | one deck, no buddy file, no list of ids; builds |
| `header-wrong`, `header-missing` | the header row has another column name, or is not there |
| `empty-file` | a deck file with nothing in it |
| `columns`, `row-of-tabs` | a row with 8 columns and one with 10; a row that holds tabs and no values |
| `names-missing`, `names-wrong`, `names-twice` | the `# name-ja`, `# name-en` and `# kind` lines |
| `names-below-header` | name lines that stand below the header row |
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
| `gloss-long`, `note-long` | one letter too many, next to values of exactly the allowed length |
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

More files are made by the script itself, because they are awkward to keep in a repository: a
deck that is not UTF-8, decks with characters that cannot be seen (a zero byte, a zero width
space, a byte order mark in the middle), a folder where a file is expected, and a dictionary that
cannot be read. A deck with Windows or old Mac line ends or with a byte order mark at its start
is built, with a warning.

## The buddy file

`buddy.tsv` has the columns `id`, `mood`, `ja` and `en`.

Moods: greeting, start, right, streak, wrong, almost, finish, back, low-battery, idle

| Column | Rules |
|---|---|
| `id` | lower case letters, digits and hyphens; unique in the file, and not the id of a deck item |
| `mood` | one of the ten above |
| `ja` | kana, spaces and the marks 、。！？「」〜・ only; at most 15 characters, spaces included |
| `en` | at most 34 characters |

## The dictionary excerpt

`fixtures/cache/` holds the entries of the words used in the fixtures, in the format of the files
in `local/cache/`. `jmdict_index.json` is an excerpt of JMdict (Electronic Dictionary Research and
Development Group), `accents.txt` an excerpt of the accent list of the Kanjium project. Both are
shared under CC BY-SA 4.0. A test compares the excerpt with the full files, entry by entry.
