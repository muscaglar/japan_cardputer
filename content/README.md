# Content

Everything the device teaches is written here as plain tables and compiled into the firmware by
`tools/build_decks.py`. The tool refuses to build when a row is wrong, so that a mistake is found
on the computer and not on the device.

## Deck files

One file per deck in `content/decks/`, named `<deck id>.tsv`, UTF-8, tab separated, with a header
row. Lines starting with `#` are comments. The first comment lines carry the deck's names:

```
# name-ja: かんばん
# name-en: signs
# kind: word
```

| Column | Meaning | Rules |
|---|---|---|
| `id` | Stable name of the item | lower case letters, digits and hyphens; unique in the whole content; never reused for another item |
| `prompt` | What is shown | every character must exist in the device's fonts |
| `reading` | The main answer | kana only; hiragana, or katakana for a katakana word |
| `accent` | Pitch accent number of `reading` | 0 flat, k = falls after beat k, empty = unknown. Never a guess. |
| `accepted` | Further right answers | kana, separated by `|`; empty if none |
| `gloss` | Meaning in English | at most 32 characters, so that it fits one line |
| `note` | One line shown with the result | at most 38 characters of English or 19 of Japanese; empty if none |
| `level` | 1, 2 or 3 | 1 kana only; 2 common kanji; 3 anything |
| `source` | Where the reading and meaning were checked | a dictionary name or a URL |

## What the build checks

- every `reading` and `accepted` answer can be typed: its romaji, fed to the converter, gives the
  same kana back
- `accent` is not larger than the number of beats
- every character of `prompt`, `reading` and `note` exists in the font that will draw it
- ids are unique and well formed, and no id has disappeared since the last build
  (`content/ids.txt` lists every id ever published)
- lengths fit the screen

## Licences

Readings and meanings are checked against JMdict (Electronic Dictionary Research and Development
Group, CC BY-SA 4.0). Pitch accents come from the accent list of the Kanjium project
(CC BY-SA 4.0). The decks themselves are therefore shared under CC BY-SA 4.0.
