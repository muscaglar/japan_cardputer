# Offline learning data and spaced repetition

Offline Japanese learning data is plentiful and legally usable if an attribution/About screen is built and share-alike is respected: JMdict (218,794 entries; English JSON 11 MB compressed, common-only subset 1.38 MB), JMnedict (743,664), KANJIDIC2 (13,108 kanji), KRADFILE, KanjiVG stroke data (109x109 canvas, fits the 135 px screen height 1:1), Tatoeba sentences (about 117k Japanese-English pairs), tanos.co.uk JLPT lists (CC BY, unofficial) and the Wikivoyage phrasebook (CC BY-SA 4.0). Weak spots: pitch accent (Kanjium is the only convenient set and its provenance is thinly documented; Wadoku is restricted for commercial use; OJAD has no download), audio (small open sets only; Tatoeba Japanese audio is small and often non-commercial), frequency lists (BCCWJ is 'research or educational' only) and textbook-aligned lists (Genki material has been taken down at the publisher's request). On the device side, none of the ESP32-S3 Cardputers (K132, v1.1, ADV) list PSRAM or an RTC chip in M5Stack's docs, and ESP32 time does not survive a power-on reset, so SRS scheduling needs NTP plus a persisted 'last known date' and a user prompt fallback. The proven pattern for big lookups on ESP32 + FAT32 SD is a Mac-built sorted fixed-width index plus a small in-RAM sparse index (used by an ESP32 offline Wikipedia project for ~285k titles with ~7 KB RAM); SQLite on ESP32 works but is unmaintained since mid-2024, has no locking and has out-of-memory reports. FSRS-6 is computable on-device (21 constants, exp and pow only) and default parameters are usable; SM-2 is simpler still. FatFs is not power-loss safe and f_rename cannot overwrite, so review state should be an append-only log with f_sync. For interop, do all Anki package handling on the Mac and exchange plain UTF-8 TSV with the device. I found no existing Cardputer Japanese dictionary or SRS firmware.

Fact-check: done.

## Statements

### data-01 · confirmed

JMdict currently has 218,794 entries (all with English glosses); the jmdict-simplified JSON release 3.6.2+20260921173324 (21 Sep 2026) ships jmdict-eng at about 11 MB compressed, jmdict-eng-common at 1.38 MB, jmdict-examples-eng at 13.5 MB and jmdict-all at 23.9 MB.

- Applies to: All Cardputer variants (content is built on the Mac and stored on microSD)
- Correction: Confirmed as written for release 3.6.2+20260921173324 (published 2026-09-21): 218,794 JMdict entries, all with English glosses (German 129,057; Russian 69,372); assets jmdict-eng 11 MB, jmdict-eng-common 1.38 MB, jmdict-examples-eng 13.5 MB, jmdict-all 23.9 MB (also jmnedict-all 12.8 MB, kanjidic2-en 1.2 MB, kradfile 104 KB, radkfile 131 KB). Sharpening of the point the researcher left open: the 115 / 69 / 146 / 15 MB figures are the 'File size' lines of the release notes, printed next to an 'XML entities' count, so they describe the source XML files, not the JSON. Measured by streaming the archives without saving them: uncompressed JSON is 117.9 MB (jmdict-eng), 16.5 MB (jmdict-eng-common, 22,639 entries), 129.3 MB (jmdict-examples-eng), 167.1 MB (jmnedict-all), 14.8 MB (kanjidic2-en). Applies to all Cardputer variants (Mac-side build).
- Source: <https://github.com/scriptin/jmdict-simplified/releases>
- Source: <https://github.com/scriptin/jmdict-simplified/releases/latest>
- Source: <https://raw.githubusercontent.com/scriptin/jmdict-simplified/master/README.md>
- Source: <https://github.com/scriptin/jmdict-simplified/releases/expanded_assets/3.6.2+20260921173324>

### data-02 · confirmed

JMnedict has 743,664 name entries, KANJIDIC2 covers 13,108 kanji (10,384 with English meanings in the jmdict-simplified build), and KRADFILE/RADKFILE cover 6,355 JIS X 0208 kanji with KRADFILE2/RADKFILE2 adding 5,801 JIS X 0212 kanji.

- Applies to: All Cardputer variants
- Correction: Confirmed (JMnedict 743,664; KANJIDIC2 13,108 with 10,384 English; KRADFILE/RADKFILE 6,355; KRADFILE2/RADKFILE2 5,801, copyright Jim Rose). Sharpening: the EDRDG licence file list names only RADKFILE/KRADFILE, and the KRAD page states no licence for the Jim Rose files, so only the 6,355-kanji pair is clearly under the EDRDG licence. That pair already covers all joyo kanji.
- Source: <https://github.com/scriptin/jmdict-simplified/releases>
- Source: <https://www.edrdg.org/wiki/JMdict-EDICT_Dictionary_Project.html>
- Source: <https://www.edrdg.org/wiki/KANJIDIC_Project.html>
- Source: <https://www.edrdg.org/krad/kradinf.html>
- Source: <https://github.com/scriptin/jmdict-simplified/releases/latest>
- Source: <https://www.edrdg.org/edrdg/licence.html>

### data-03 · confirmed

The EDRDG files (JMdict, JMnedict, KANJIDIC, KRADFILE/RADKFILE) are under Creative Commons Attribution-ShareAlike 4.0, and the EDRDG licence asks software to acknowledge the usage and source of the files in documentation and publicity material, with app-style products showing the acknowledgement on a separate screen such as 'About'.

- Applies to: All Cardputer variants
- Correction: Confirmed (CC BY-SA 4.0; acknowledge usage and source in documentation, publicity material, site; apps on a separate screen such as 'About' or 'Sources'). The licence text adds conditions the claim leaves out: (a) software must also provide copies of, or links to, the documentation and licence files; (b) for apps 'It is not sufficient just to mention it on a start-up/launch page'; (c) section 4 requires 'a procedure for regular updating of the data' and calls failure to keep versions up to date 'a violation of the licence'. The licence covers only the Japanese and English components of JMdict (other-language glosses have separate copyright). KANJIDIC SKIP codes are under Jack Halpern's own CC licence: his page says CC BY-SA 4.0, the EDRDG wiki links CC BY-NC-SA 4.0, an unresolved discrepancy. Treating microcontroller firmware like an app remains an interpretation.
- Source: <https://www.edrdg.org/edrdg/licence.html>
- Source: <https://www.edrdg.org/krad/kradinf.html>
- Source: <https://www.edrdg.org/wiki/KANJIDIC_Project.html>
- Source: <http://www.kanji.org/kanji/dictionaries/skip_permission.htm>

### data-04 · confirmed

KANJIDIC2 carries school grade, stroke count and a frequency rank for the 2,501 most-used kanji, but its JLPT field is the pre-2010 four-level system, not N5 to N1.

- Applies to: All Cardputer variants
- Correction: Confirmed. EDRDG adds a mapping note: old levels 4 and 3 correspond to N5 and N4, old level 2 is split between N2 and N3, old level 1 is N1, so the field cannot separate N2 from N3. The frequency rank comes from Mainichi Shimbun newspaper text and EDRDG calls the ranks of the last few hundred kanji 'quite imprecise'. Grades are G1 to G6 (1,026 kyoiku kanji), G8 (remaining joyo), G9 and G10 (name kanji).
- Source: <https://www.edrdg.org/wiki/KANJIDIC_Project.html>
- Source: <https://en.wikipedia.org/wiki/Ky%C5%8Diku_kanji>

### data-05 · confirmed

Tatoeba has 249,195 Japanese sentences; the ready-made Japanese-English pair file has 117,022 pairs (dated 13 Feb 2026); sentence text is CC BY 2.0 FR (a subset is CC0) and redistribution requires attribution to each sentence owner.

- Applies to: All Cardputer variants
- Correction: Confirmed (249,195 Japanese sentences on the stats page; 117,022 pairs dated 2026-02-13 at manythings.org; CC BY 2.0 FR; attribution to sentence owners when redistributing). Measured from the weekly export of 2026-09-26: jpn_sentences.tsv.bz2 is 3.4 MB (248,918 lines, 16.6 MB uncompressed); jpn_sentences_detailed (with the usernames needed for attribution) 4.5 MB; jpn-eng links 1.5 MB with 232,954 Japanese sentences that have an English translation; median Japanese sentence length 16 characters (180,598 sentences are 20 characters or shorter). The CC0 subset is effectively empty for Japanese: the jpn CC0 file holds 2 sentences, so all Japanese text needs CC BY attribution.
- Source: <https://tatoeba.org/en/stats/sentences_by_language>
- Source: <https://tatoeba.org/en/downloads>
- Source: <https://www.manythings.org/anki/>
- Source: <https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2>
- Source: <https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences_CC0.tsv.bz2>
- Source: <https://downloads.tatoeba.org/exports/per_language/jpn/jpn-eng_links.tsv.bz2>

### data-06 · confirmed

The Tanaka Corpus (about 150,000 edited Japanese-English pairs, now maintained inside Tatoeba under CC BY) is explicitly described by EDRDG as not natural or representative text, so example sentences need filtering before a learner sees them.

- Applies to: All Cardputer variants
- Correction: Confirmed. For sizing: the jmdict-examples-eng build (3.6.2+20260921173324) carries examples on 28,929 of 218,794 entries, with 32,311 example references to 26,269 distinct Tatoeba sentences and a median Japanese sentence length of 19 characters (measured by streaming the release file).
- Source: <https://www.edrdg.org/wiki/Tanaka_Corpus.html>
- Source: <https://raw.githubusercontent.com/scriptin/jmdict-simplified/master/README.md>
- Source: <https://github.com/scriptin/jmdict-simplified/releases/latest>

### data-07 · corrected

There are no official JLPT N5 to N1 vocabulary or kanji lists; the widely used tanos.co.uk lists by Jonathan Waller are unofficial and licensed Creative Commons BY (credit the site), with N5 at roughly 800 words and 100 kanji.

- Applies to: All Cardputer variants
- Correction: No official lists exist (JLPT FAQ) and the tanos lists are CC BY with credit to the site: confirmed. But '~800 words and ~100 kanji' is only the headline on the tanos N5 page. The lists are smaller: the same page says its audio covers 'all the vocabulary needed for level N5 ... (689 words)', and the downloadable N5 kanji list holds 80 kanji (the N4 file adds 166). The N5 kanji file is internally named jlpt_kanji_level_4_base.txt, i.e. it is the pre-2010 level 4 list relabelled. The tanos list pages (/jlpt5/vocab/ and /jlpt5/kanji/) returned HTTP 500 on 2026-09-27, so word counts for N4 to N1 were not checked.
- Source: <https://www.jlpt.jp/e/faq/index.html>
- Source: <https://www.tanos.co.uk/jlpt/sharing/>
- Source: <https://www.tanos.co.uk/jlpt/jlpt5/>
- Source: <https://www.tanos.co.uk/jlpt/jlpt5/kanji/jlpt_kanji_level_5_base.zip>
- Source: <https://www.tanos.co.uk/jlpt/jlpt4/>

### data-08 · confirmed

Textbook-aligned lists carry real takedown risk: the Genki Study Resources Anki decks page was removed at the request of The Japan Times, so Genki or Minna no Nihongo lists should only be loaded from the owner's own notes for personal use, not bundled.

- Applies to: All Cardputer variants
- Correction: Confirmed and stronger than stated: besides the Anki decks page ('This page has been taken down at the request of The Japan Times'), the site's home page now says 'All exercises have been removed at the request of The Japan Times.' No licence grant from either publisher was found. Not legal advice.
- Source: <https://sethclydesdale.github.io/genki-study-resources/help/anki-decks/>
- Source: <https://sethclydesdale.github.io/genki-study-resources/>

### data-09 · confirmed

The Wikivoyage Japanese phrasebook is reusable under CC BY-SA 4.0 with attribution by link to the page, and covers travel sections such as basics, problems, numbers, time, transportation, lodging, money, eating, bars, shopping, driving and authority.

- Applies to: All Cardputer variants
- Correction: Confirmed. The page wikitext is about 88 KB with roughly 717 term or phrase lines. Sections not named in the claim include Colors, On the phone, Family, Typical Japanese expressions, Honorifics and Country names. The Basics section contains a 'Common signs' box (open, closed, entrance, exit, push, pull, toilet, men, women, forbidden, yen in Japanese script with romaji), so a small openly licensed signage list does exist inside the phrasebook.
- Source: <https://en.wikivoyage.org/wiki/Japanese_phrasebook>
- Source: <https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use>
- Source: <https://en.wikivoyage.org/w/index.php?title=Japanese_phrasebook&action=raw>

### data-10 · corrected

Pitch accent data is the weakest-licensed content type: Kanjium offers accent positions for 124,137 words under a stated CC BY-SA 4.0 but does not document where the accent data came from; Wadoku restricts commercial and ad-funded use; OJAD offers no download or licence; UniDic is triple-licensed GPL v2 / LGPL v2.1 / BSD but is a 576 MB or larger morphological dictionary.

- Applies to: All Cardputer variants
- Correction: Kanjium licence (CC BY-SA 4.0) and accents.txt (124,137 lines, 3.2 MB) confirmed, but the README does credit the accent data: 'The pitch accent notation, verb particle data, phonetics, homonyms and other additions ... were provided by Uros O. through his free database.' What is missing is the underlying reference work, so provenance is still unclear. Wadoku (no fee-charging or advertising servers and no commercial software without permission), OJAD (over 9,000 nouns and 3,500 declinable words, no licence or download statement on the home page) and UniDic (GPL v2.0/LGPL v2.1/BSD New; 576 MB to 2.2 GB for version 3.1.0 on the English NINJAL page) confirmed.
- Source: <https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/README.md>
- Source: <https://github.com/mifunetoshiro/kanjium>
- Source: <https://www.wadoku.de/wiki/display/WAD/Wörterbuch+Lizenz>
- Source: <https://www.gavo.t.u-tokyo.ac.jp/ojad/eng/pages/home>
- Source: <https://clrd.ninjal.ac.jp/unidic/en/>
- Source: <https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt>

### data-11 · corrected

KanjiVG stroke-order data is CC BY-SA 3.0 (attribution to Ulrich Apel), describes each stroke as one SVG path in stroke order on a 109x109 canvas, and so fits the 135 px screen height at 1:1 scale without downscaling.

- Applies to: All ESP32-S3 Cardputer variants (240x135 display on K132, v1.1 and ADV)
- Correction: Confirmed: CC BY-SA 3.0 (copyright Ulrich Apel), one path per stroke in stroke order, 109x109 area, which fits the 135 px height at 1:1 on K132, v1.1 and ADV. Corrections: (a) the documentation says paths use 'M/m, C/c, and S/s'; relative commands dominate in the data (measured in release r20260714: M 79,786; c 168,130; C 8,993; s 1,101; m 135; S 91), so a renderer must handle relative cubic Beziers. (b) The latest release is r20260714 (2026-07-14), not r20250816, whose asset sizes are as stated. (c) The r20260714 XML holds 6,703 characters and 79,921 strokes (mean 11.9, maximum 30 per character), 13.8 MB uncompressed. Paths are centre lines to be stroked (files use stroke-width 3, round caps). The file header asks for attribution by stating the use of KanjiVG and linking to its website. No Cardputer implementation was found, so animation practicality remains an inference.
- Source: <https://kanjivg.tagaini.net/files.html>
- Source: <https://kanjivg.tagaini.net/svg-format.html>
- Source: <https://github.com/KanjiVG/kanjivg>
- Source: <https://github.com/KanjiVG/kanjivg/releases/expanded_assets/r20250816>
- Source: <https://kanjivg.tagaini.net/>
- Source: <https://raw.githubusercontent.com/KanjiVG/kanjivg/master/README.md>

### data-12 · confirmed

Openly licensed Japanese audio is limited: Kanji alive provides 10,187 native-speaker recordings of compound words for 1,235 kanji under CC BY 4.0, while Tatoeba has only 6,332 Japanese audio recordings whose licence is chosen per contributor and cannot be reused when the licence field is empty.

- Applies to: All ESP32-S3 Cardputer variants (all have a speaker; ADV adds an ES8311 codec and 3.5 mm output)
- Correction: Confirmed (Kanji alive: 10,187 files for 1,235 kanji, Opus/AAC/Ogg/MP3, 32 kHz mono, CC BY 4.0; Tatoeba audio index: 6,332 Japanese). Sharper figures from the Tatoeba export of 2026-09-26: 6,420 Japanese rows in the audio list, of which 5,111 have an empty licence field (not reusable outside Tatoeba), 1,282 are CC BY-NC 4.0 and only 27 are CC BY 4.0. Hardware note confirmed from docs: all three ESP32-S3 variants have a speaker; only the ADV has the ES8311 codec and a 3.5 mm output.
- Source: <https://github.com/kanjialive/kanji-data-media>
- Source: <https://tatoeba.org/en/audio/index>
- Source: <https://tatoeba.org/en/downloads>
- Source: <https://raw.githubusercontent.com/kanjialive/kanji-data-media/master/README.md>
- Source: <https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences_with_audio.tsv.bz2>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### data-13 · confirmed

M5Stack's documentation for the original Cardputer (K132), Cardputer v1.1 and Cardputer ADV lists an ESP32-S3FN8 with 8 MB flash and lists neither PSRAM nor a real-time clock chip; only the Linux-based CardputerZero (Raspberry Pi CM0, 512 MB RAM) has an RTC (RX8130CE).

- Applies to: Cardputer K132, Cardputer v1.1, Cardputer ADV, CardputerZero
- Correction: Confirmed from the raw docs pages: Cardputer (SKU K132), Cardputer v1.1 (K132-V11) and Cardputer-Adv (K132-Adv) all list 'ESP32-S3FN8' and 'Flash 8MB'; the strings RTC and PSRAM do not occur on any of the three pages or on the Stamp-S3 and Stamp-S3A pages. M5Stack's Arduino docs list an RTC page for many devices but none under 'Cardputer / -Adv'. CardputerZero (SKU C154, Lite C155, marked 'Work in progress') lists Raspberry Pi CM0, 512 MB LPDDR2, 1.9 inch 320x170, RTC RX8130CE. Supporting third-party evidence: the M5OpurSan project reports esptool output on a real ADV ('Features: WiFi, BLE', flash 8MB) and MALLOC_CAP_SPIRAM of 0 at run time; a forum post by felmue says the ADV 'does not have an RTC chip inside'. Conflicting third-party claim: the card_dic-for-cardputer-adv README states 'OPI PSRAM'; this contradicts the primary docs and should be settled on the actual unit with esptool flash_id or ESP.getPsramSize().
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-adv-version-esp32-s3>
- Source: <https://community.m5stack.com/topic/8050/cardputer-adv>

### data-14 · confirmed

On ESP32-S3 the internal RTC timer keeps time through deep sleep and through resets except a power-on reset, so the date is lost whenever the Cardputer is switched off or the battery empties, and the internal RC clock source drifts with temperature.

- Applies to: Cardputer K132, v1.1 and ADV (all ESP32-S3)
- Correction: Confirmed from the ESP-IDF text (RTC timer persists across resets 'with the exception of power-on resets'; the default internal RC oscillator's stability 'is affected by temperature fluctuations'; an external 32 kHz crystal is the documented better option, which the Cardputer docs do not list). On the point left open: M5Stack lists off-state currents of 0.23 uA for the ADV ('Standby Current (Power Switch Set to OFF)'), 0.26 uA for K132 and 0.15 uA for v1.1 ('Sleep Current'). That is consistent with the side switch disconnecting the battery from the SoC, so the RTC timer cannot survive switch-off on battery (inference from the docs, schematic not inspected). With USB connected the ADV keeps running even with the switch OFF (M5OpurSan README, third-party). No numeric drift figure was found.
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/system/system_time.html>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md>

### data-15 · corrected

The Cardputer's microSD slot is wired over SPI (SCK 40, MISO 39, MOSI 14, CS 12) and M5Stack's example opens it at 25 MHz; independent ESP32 benchmarks of SPI-mode SD show sequential reads of roughly 0.4 to 1.7 MB/s, with small unbuffered reads much slower.

- Applies to: Pins verified for Cardputer (K132) docs; assumed but not verified identical on v1.1 and ADV
- Correction: Pins and 25 MHz confirmed, and now verified for all three variants: the K132, v1.1 and ADV pin maps all give microSD CS G12, MOSI G14, CLK G40, MISO G39, and the M5Stack SD example says it applies to 'Cardputer and Cardputer-Adv'. Benchmark corrections (drorgl repo: ESP32 WROVER, SPI at 20 MHz, not a Cardputer): sequential read is 0.78 to 0.83 MB/s with the default 128-byte stdio buffer, 1.25 to 1.38 MB/s with 2,048 bytes and 1.38 to 1.55 MB/s with 4,096 bytes, a gain of 1.7x to 1.9x in SPI mode; the 2x to 3x gain is the SDMMC result, which the Cardputer cannot use. The repo does contain random-read data: a random 512-byte read costs about 0.6 to 1.2 ms (813 to 1,712 reads per second) unbuffered or with the 128-byte buffer, and becomes slower with larger stdio buffers (313 per second at 2,048 bytes, 201 at 4,096). So small reads are not 'much slower'; large stdio buffers help streaming and hurt index seeks. The test file was only 512 KB, so FAT chain walking on large files is not covered. The Schatzmann post shows its numbers only in charts; the 0.4 MB/s figure could not be read from the text.
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/sdcard>
- Source: <https://github.com/drorgl/esp32-sd-card-benchmarks>
- Source: <https://www.pschatzmann.ch/home/2025/03/25/test/>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### data-16 · confirmed

On FAT32 a single file is limited to 2^32 - 1 bytes and a directory to 65,536 32-byte entries, with each long-named file using two or more entries, and large directories are slow; one-file-per-word layouts are therefore a poor fit for a 200k-entry dictionary.

- Applies to: All Cardputer variants using a FAT32 microSD card
- Correction: Confirmed. FatFs: 'Maximum file size: 2^32 - 1 bytes on FAT volume'; Microsoft's official comparison page gives 4 GiB for FAT32. The directory figures (65,536 32-byte entries, 32,767 to 65,534 files with long names, avoid large directories) come from anonymous community answers on Microsoft Q&A, so treat them as supporting evidence. M5Stack's SD example asks for 'a FAT32-formatted microSD card'.
- Source: <http://elm-chan.org/fsw/ff/doc/appnote.html>
- Source: <https://learn.microsoft.com/en-us/answers/questions/2580603/what-is-the-maximum-number-of-files-i-can-place-in>
- Source: <https://learn.microsoft.com/en-us/windows/win32/fileio/filesystem-functionality-comparison>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/sdcard>

### data-17 · corrected

An existing ESP32 project looks up about 285,000 article titles from a FAT32 SD card using a sorted index of fixed 80-byte records plus a sparse in-RAM index of one entry per 64 records (about 7 KB), with LZ4-compressed bodies in 32 MB chunk files; this is a proven template for a JMdict lookup without PSRAM.

- Applies to: All ESP32-S3 Cardputer variants (pattern demonstrated on ESP32 CYD and ESP32-C3 boards, not on a Cardputer)
- Correction: The README is quoted correctly (about 285,000 articles, 80-byte records, sparse index every 64 records, LZ4 per article, 32 MB chunks, FAT32 with 64 KB allocation units, word_index.bin and title_index.bin), but the '~7 KB' RAM figure does not match the code: config.h sets SPARSE_KEY_LEN 12 and SPARSE_STEP_DEFAULT 64, and wiki_db.cpp comments 'For 200 K articles: 3125 x 12 B = ~37 KB on the heap', so 285,000 titles need about 53 KB unless a larger --sparse-step is chosen. For JMdict's roughly 499,000 lookup keys (233,497 kanji forms plus 265,686 kana forms in jmdict-eng) the same design at step 64 would take about 94 KB of heap; use a step of 256 or more, or plain binary search on the card. The pattern is demonstrated on a classic ESP32 CYD and an ESP32-C3, not on a Cardputer; that project runs SD SPI at 48 MHz on a dedicated bus and advises 25 MHz or lower on shared buses. seek-reader (MIT, Xteink X4, ESP32-C3, about 380 KB usable RAM, StarDict .idx/.dict) confirmed. Neither README gives lookup latency.
- Source: <https://github.com/alunmorris/Offline-Wikipedia-ESP32/tree/master>
- Source: <https://github.com/sumegig/seek-reader>
- Source: <https://raw.githubusercontent.com/alunmorris/Offline-Wikipedia-ESP32/master/README.md>
- Source: <https://raw.githubusercontent.com/alunmorris/Offline-Wikipedia-ESP32/master/firmware/src/config.h>
- Source: <https://raw.githubusercontent.com/alunmorris/Offline-Wikipedia-ESP32/master/firmware/src/wiki_db.cpp>
- Source: <https://raw.githubusercontent.com/alunmorris/Offline-Wikipedia-ESP32/master/preprocessor/build_wiki_db.py>

### data-18 · corrected

I found no existing Cardputer or M5Stack firmware that provides an offline Japanese dictionary or spaced-repetition trainer; the closest precedent is a Cardputer ADV Gemini chat firmware that converts romaji to hiragana on-device, shows Japanese with a 12 px font and has no kanji conversion.

- Applies to: Cardputer ADV (the precedent firmware); absence applies to all variants
- Correction: No JMdict-based Japanese-English dictionary firmware and no interval-scheduling (SM-2 or FSRS) trainer for a Cardputer was found, but the 'closest precedent' statement is wrong. Closer precedents exist (all small third-party repos, unreviewed): (1) Mr-xiaotian/WordCardputer: Japanese and English vocabulary trainer for the M5Cardputer with flashcards, dictation using a romaji-to-kana IME, WAV audio from SD, an SQLite word store (siara-cc/Sqlite3Esp32) and proficiency-weighted random review (weight = 6 - score, not time-based); glosses are Chinese; no licence file. (2) kikyujin/M5OpurSan: offline Japanese word processor with kana-kanji conversion from a 927,000-entry, 33.3 MB sorted binary dictionary on microSD, looked up by binary search; developed and tested on Cardputer ADV only (K132 and v1.1 untested); code MIT, dictionary GPL-2.0. (3) Offline dictionaries for Cardputer or ADV with SD indexes: Cardputer_Dictionary (about 100,000 English words), m5_stack_cardputer_dictionary (ECDICT, binary search, favourites), card_dic-for-cardputer-adv (English-Chinese). (4) necobit/Cardputer-TTS: Japanese formant speech from romaji on Cardputer ADV (MIT). (5) mohitagw15856/Inkcards: SM-2 flashcards with an Anki and CSV converter for an ESP32-C3 e-reader (MIT, 'not yet verified on device'). The GeminiCardputerADV_Japanese details (12 px font, konnnitiha example, no kanji conversion, no licence file) are correct, but its README says the binary was not tested on a real device.
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/Mr-xiaotian/WordCardputer>
- Source: <https://raw.githubusercontent.com/Mr-xiaotian/WordCardputer/main/platformio.ini>
- Source: <https://github.com/kikyujin/M5OpurSan>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/opur_editor/opur_dict.c>
- Source: <https://github.com/majharulislamjihad2009-a11y/Cardputer_Dictionary>

### data-19 · corrected

The siara-cc SQLite3 library for ESP32 can read large databases from SD (the author cites about 700 ms for an indexed lookup in a 10-million-row table) but does not implement locking, has had no commits since June 2024 and has user reports of 'out of memory' errors; the README gives no RAM requirement.

- Applies to: All ESP32-S3 Cardputer variants (not tested on a Cardputer)
- Correction: README quotes (about 700 ms for 10 million rows, 'Locking is not implemented', '500 odd kilbytes RAM') and the last commit date (2024-06-12) are confirmed for siara-cc/esp32_arduino_sqlite3_lib. Corrections: (a) issue 7 is closed (2020-03-08, 37 comments) and the maintainer did respond: the cause was heap fragmentation at low memory, the page cache was cut from 64 KB to 32 KB, prepared statements were recommended over sqlite3_exec, 'PRAGMA page_size=512; VACUUM;' was suggested, and he wrote that the library 'still needs around 80k of RAM to work'. So a RAM requirement exists, in the issue rather than the README, and the page-size-512 advice comes from this issue. (b) The sibling ESP-IDF component siara-cc/esp32-idf-sqlite3 merged a fix on 2026-04-05, so the project is not fully dormant. (c) It has been used on a Cardputer: WordCardputer depends on siara-cc/Sqlite3Esp32 and opens /sd/words_study/jp/jp_words.db (third-party, small vocabulary database). The README does not say whether the 700 ms figure was measured over SPI or 4-bit SDMMC; the Cardputer has SPI only.
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib>
- Source: <https://raw.githubusercontent.com/siara-cc/esp32_arduino_sqlite3_lib/master/README.md>
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib/commits/master>
- Source: <https://github.com/siara-cc/esp32_arduino_sqlite3_lib/issues/7>
- Source: <https://www.sqlite.org/malloc.html>
- Source: <https://github.com/siara-cc/esp32-idf-sqlite3>

### data-20 · corrected

FSRS-6 uses 21 parameters and scheduling a card needs only exp and pow with non-integer exponents on a few floats; with the published default parameters it scores log loss 0.3620 versus 0.3460 when optimised per user, so defaults are usable without training.

- Applies to: All ESP32-S3 Cardputer variants
- Correction: Confirmed: FSRS-6 has 21 parameters with exactly the listed defaults, FSRS-5 has 19, FSRS-4.5 has 17, and scheduling needs only exp and pow on a few floats. The benchmark attribution is wrong: in the current srs-benchmark README (9,999 collections, 349,923,850 reviews) FSRS-6 optimised per user scores log loss 0.3460 and RMSE(bins) 0.0653, but the 0.3620 / 0.0910 row is 'FSRS-7 default param.', not FSRS-6. The last README revision that listed 'FSRS-6 default param.' (2026-03-18) gave 0.3664 and 0.0924. Defaults remain usable (better than the AVG baseline at 0.3945, about level with optimised FSRS-4.5 at 0.3625). Additions: FSRS-7 (34 trainable parameters, fractional intervals, a more complex forgetting curve) is now described as the newest version, while fsrs-rs releases are still 6.x (v6.6.2, 2026-08-28). When same-day reviews are scored, FSRS-6 with defaults did worse than the AVG baseline (0.482 against 0.3816 in the 2026-03-18 table), so same-day repeats are better handled with fixed learning steps. The only C entry in awesome-fsrs is rs-fsrs-c, a binding to the Rust scheduler at FSRS v5, so a hand-written scheduler is needed. Expertium's 99.6 percent figure is for 'FSRS-6 (recency)' against Anki SM-2 and carries his own caveat that no fair comparison exists (blog, supporting evidence).
- Source: <https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm>
- Source: <https://github.com/open-spaced-repetition/srs-benchmark>
- Source: <https://expertium.github.io/Benchmark.html>
- Source: <https://github.com/open-spaced-repetition>
- Source: <https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/main/README.md>
- Source: <https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/3451cbbc02fc1fd49378bf25366b177eadd84e82/README.md>

### data-21 · confirmed

SM-2 needs only basic arithmetic per card: intervals of 1 day, then 6 days, then previous interval times the ease factor, with EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02)), a floor of 1.3, and a restart of repetitions when the grade is below 3.

- Applies to: All ESP32-S3 Cardputer variants
- Source: <https://super-memory.com/english/ol/sm2.htm>

### data-22 · confirmed

FatFs (the FAT driver used on ESP32) can lose or cross-link a file if power is cut during a write, recommends f_sync to shrink the risk window, and its f_rename fails with FR_EXIST if the destination exists, so the usual write-temp-then-rename-over trick is not an atomic replace on this platform.

- Applies to: All ESP32-S3 Cardputer variants writing to microSD
- Correction: Confirmed from the FatFs documents. Platform detail: ESP-IDF's FAT VFS rename() calls f_rename directly in v4.4.7, v5.1.4, v5.3.2 and v5.5, so renaming onto an existing file fails there (Arduino-ESP32 2.0.16 is based on ESP-IDF v4.4.7; M5Stack's PlatformIO example pins espressif32@6.7.0). ESP-IDF master adds an optional CONFIG_FATFS_VFS_RENAME_REPLACES_DESTINATION that emulates replacement with f_unlink followed by f_rename: still two steps, not atomic. Arduino File::flush() calls fflush and then fsync, which reaches f_sync, so flushing after each appended record gives the minimised critical section FatFs describes.
- Source: <http://elm-chan.org/fsw/ff/doc/appnote.html>
- Source: <http://elm-chan.org/fsw/ff/doc/rename.html>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/v4.4.7/components/fatfs/vfs/vfs_fat.c>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/v5.5/components/fatfs/vfs/vfs_fat.c>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/master/components/fatfs/vfs/vfs_fat.c>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.17/libraries/FS/src/vfs_api.cpp>

### data-23 · confirmed

Anki .apkg and .colpkg files are zip archives around an SQLite collection, and since Anki 2.1.50 the default export stores it as zstd-compressed collection.anki21b (schema v18, Protobuf blobs) beside a decoy collection.anki2; parsing them on the Cardputer is impractical, so conversion belongs on the Mac.

- Applies to: All Cardputer variants
- Correction: Confirmed, now against primary source code as well as the blog: Anki's meta.rs maps package version Legacy1 to collection.anki2, Legacy2 to collection.anki21 (both schema V11) and Latest to collection.anki21b (schema V18, zstd-compressed); export.rs writes a dummy collection.anki2 with a single note for old clients. The manual describes the 'Support older Anki versions' switch but does not name the version; the 2.1.50 date comes from the blog. Doing the conversion on the Mac remains a sound judgement.
- Source: <https://docs.ankiweb.net/exporting.html>
- Source: <https://github.com/ankidroid/Anki-Android/wiki/Database-Structure>
- Source: <https://eikowagenknecht.com/posts/understanding-the-anki-apkg-format/>
- Source: <https://raw.githubusercontent.com/ankitects/anki/main/rslib/src/import_export/package/meta.rs>
- Source: <https://raw.githubusercontent.com/ankitects/anki/main/rslib/src/import_export/package/colpkg/export.rs>

### data-24 · confirmed

Anki imports UTF-8 plain text with tab or comma separators, supports file headers such as #separator, #notetype, #deck, #tags column and #guid column, and updates an existing note (keeping its scheduling) when the first field or GUID matches; this makes TSV the simplest robust exchange format in both directions.

- Applies to: All Cardputer variants
- Correction: Confirmed. Exact wording: file headers need Anki 2.1.54 or later; 'If notes are updated in place, the existing scheduling information on all their cards will be preserved'; 'Notes in Plain Text' export separates fields with tabs and embeds HTML formatting, so the Mac-side converter must strip HTML.
- Source: <https://docs.ankiweb.net/importing/text-files.html>
- Source: <https://docs.ankiweb.net/exporting.html>

### data-25 · confirmed

AnkiConnect is an Anki desktop add-on exposing a local HTTP JSON API (reported as port 8765, bound to 127.0.0.1) that only works while Anki is running; its GitHub repository was archived on 4 Nov 2025 and moved to sourcehut.

- Applies to: Mac-side tooling only
- Correction: Now confirmed from the primary README on sourcehut (reachable with a plain HTTP client on 2026-09-27): the add-on starts 'an HTTP server on port 8765 whenever Anki is launched', binds 'only ... to the 127.0.0.1 IP address' by default (webBindAddress is configurable), and 'Anki must be kept running in the background'. The GitHub repo shows 'archived by the owner on Nov 4, 2025' and its README says it 'has permanently moved to https://git.sr.ht/~foosoft/anki-connect'. Mac-specific note from the same README: App Nap must be disabled for Anki or the API stalls while Anki is in the background.
- Source: <https://github.com/FooSoft/anki-connect>
- Source: <https://git.sr.ht/~foosoft/anki-connect/blob/master/README.md>

### data-26 · corrected

Known-word data can be pulled from WaniKani through its official API (bearer token, 60 requests per minute, assignments carry srs_stage) and from jpdb through a 'Export vocabulary reviews (.json)' button in settings; I found no official export for Duolingo or Bunpro, only third-party scripts and extensions.

- Applies to: Mac-side tooling only
- Correction: WaniKani (Authorization: Bearer token, 60 requests per minute, assignments with SRS stages 0 to 9, free accounts limited to level 3) and the jpdb 'Export vocabulary reviews (.json)' button (per a third-party add-on README) are confirmed. The Duolingo statement needs a caveat: Duolingo operates an official 'Data Vault' that 'allows you to download all of your personal data stored by Duolingo' (login required); whether it contains a usable learned-words list could not be checked. The Bunpro statement could not be verified either way (web search budget was exhausted; guessed API URLs returned 404).
- Source: <https://docs.api.wanikani.com/20170710/>
- Source: <https://github.com/llvtt/jpdb_anki_import>
- Source: <https://raw.githubusercontent.com/llvtt/jpdb_anki_import/main/README.md>
- Source: <https://drive-thru.duolingo.com/>

### data-27 · confirmed

The Anki manual's rule of thumb is that 20 new cards a day leads to roughly 200 reviews a day, and FSRS parameter optimisation is not worthwhile below a few hundred reviews; a short trip will therefore run on default parameters and needs a low new-card limit to keep daily reviews small.

- Applies to: All Cardputer variants
- Correction: Confirmed (both quotes are in the Anki manual). Two cautions on the inference: the 200 reviews per day figure is what to 'expect' when 'consistently learning 20 new cards a day', a steady-state estimate that a two or three week trip will not reach; and 'less than a few hundred' reviews is listed as a reason FSRS may perform poorly, not as a hard minimum. No source was found for how many cards a traveller completes per day.
- Source: <https://docs.ankiweb.net/deck-options.html>

### data-28 · confirmed

The BCCWJ word frequency list from NINJAL is published as 'free for use for research or educational purposes', which is not an open licence, and the gokan-dataset shows that JLPT-levelled example sentences can be derived by tagging Tatoeba sentences with word levels rather than from any natively graded sentence corpus.

- Applies to: All Cardputer variants
- Correction: Confirmed (BCCWJ lists are 'free for use for research or educational purposes', version 1.0; gokan-dataset counts 35,814 words, 2,300 kanji, 755 grammar points, 31,355 sentence sets). Additions: gokan's own licence table marks its JPDB frequency data and KKLC data as 'See their terms' or 'See that repository', so the compiled set is not cleanly open; and its one-JSON-file-per-word layout (tens of thousands of files in one directory) should be repacked before it goes on a FAT32 card.
- Source: <https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html>
- Source: <https://github.com/gokan-dev/gokan-dataset>
- Source: <https://raw.githubusercontent.com/gokan-dev/gokan-dataset/main/README.md>

## Found by the fact-check

- Prior art exists on the actual hardware, so the project does not start from zero. WordCardputer (https://github.com/Mr-xiaotian/WordCardputer) is a Japanese and English flashcard, dictation and listening trainer for the M5Cardputer with a romaji-to-kana IME, WAV audio on SD and an SQLite word store (Chinese glosses, score-weighted review rather than interval scheduling, no licence file). M5OpurSan (https://github.com/kikyujin/M5OpurSan) does offline kana-kanji conversion on a Cardputer ADV from a 927,000-entry 33.3 MB sorted binary dictionary on microSD using plain binary search (code MIT, dictionary GPL-2.0, tested on ADV only). Both are third-party and unreviewed.
- The EDRDG licence has an update obligation that affects the build pipeline: section 4 requires 'a procedure for regular updating of the data from the most recent versions available' and says failure to keep versions up to date 'is a violation of the licence'. A Mac-side rebuild script plus a visible data date on the About screen would address it. Source: https://www.edrdg.org/edrdg/licence.html
- A useful dictionary fits without the SD card. Measured from jmdict-simplified 3.6.2+20260921173324 (https://github.com/scriptin/jmdict-simplified/releases/latest): the common subset has 22,639 entries and packs to about 1.9 MB as headword, reading and glosses; the full English set packs to about 16.5 MB with roughly 499,000 lookup keys. A Cardputer ADV firmware already ships an offline dictionary in flash with about 3 MB for the app and about 5 MB for LittleFS on the 8 MB chip (third-party: https://github.com/redredred777/CineVocab). Applies to K132, v1.1 and ADV, which all have 8 MB flash.
- Tatoeba publishes a ready-made sentence-to-dictionary index, which removes the need for a morphological analyser: jpn_indices.tar.bz2 (2.9 MB, 150,075 sentence pairs) gives for each sentence the JMdict headword, reading, sense number and surface form of every word, and marks checked examples with '~' (26,450 sentences carry at least one mark). It supports both example selection and lookup of inflected forms. Sources: https://tatoeba.org/en/downloads and https://downloads.tatoeba.org/exports/jpn_indices.tar.bz2
- Index reads and streaming reads want opposite buffer settings on SPI SD. In the ESP32 benchmark at https://github.com/drorgl/esp32-sd-card-benchmarks a random 512-byte read takes about 0.6 to 1.2 ms unbuffered or with the default 128-byte stdio buffer, but 3 to 5 ms with a 2,048 or 4,096-byte buffer, while sequential reads gain 1.7x to 1.9x from the larger buffer. A binary search over 499,000 keys is about 19 probes, so lookups should take tens of milliseconds. Measured on an ESP32 WROVER at 20 MHz, not on a Cardputer.
- Heap is tighter than the 300 KB planning figure once Wi-Fi is on. Notes from a project running on a real Cardputer ADV (third-party: https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/CLAUDE.md) report about 320 KB internal RAM in total, about 50 KB taken by the Wi-Fi stack, 45 to 50 KB needed for a TLS handshake, and 32 KB for a full-screen 8-bit canvas against 4 KB at 1 bit. The SQLite library maintainer states it 'still needs around 80k of RAM to work' (https://github.com/siara-cc/esp32_arduino_sqlite3_lib/issues/7). SQLite, HTTPS and a deep-colour canvas are unlikely to coexist.
- Timekeeping has a supported hardware fix and a variant-dependent software fix. M5Stack sells Unit RTC (SKU U126, HYM8563, I2C 0x51, coin cell, Grove plug: https://docs.m5stack.com/en/unit/UNIT%20RTC) and M5Unified has a config flag 'external_rtc' described as 'use Unit RTC' (https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.hpp); whether it works on the Cardputer Grove pins G2/G1 was not verified. Keeping the device asleep instead of switched off preserves the RTC timer, but M5OpurSan reports that only the ADV wakes reliably on any key (TCA8418 keyboard controller), while K132 and v1.1 scan the key matrix from the CPU (third-party: https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/README.md).
- FSRS-6 is no longer the newest version and the default-parameter numbers differ by version. The srs-benchmark README now lists FSRS-7 (34 trainable parameters, fractional intervals) with 'FSRS-7 default param.' at log loss 0.3620, while FSRS-6 with defaults scored 0.3664 and, when same-day reviews were scored, 0.482, worse than the constant-average baseline at 0.3816. For a device that repeats cards within the same day, fixed learning steps plus FSRS-6 for day-level intervals is the safer design. Sources: https://github.com/open-spaced-repetition/srs-benchmark and https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/3451cbbc02fc1fd49378bf25366b177eadd84e82/README.md
- Known words can leave Anki without any SQLite or package parsing: the Anki browser search supports 'prop:ivl>=10' style filters and, with FSRS enabled, 'prop:s>21' (https://docs.ankiweb.net/searching.html); the selected notes can then be exported as 'Notes in Plain Text' (https://docs.ankiweb.net/exporting.html). A Mac-side script is only needed if interval values themselves must be carried over.
- A power-safe review log needs no special library: in arduino-esp32 File::flush() calls fflush and then fsync, which reaches FatFs f_sync (https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.17/libraries/FS/src/vfs_api.cpp). An append-only log flushed after each review, with state rebuilt from the log at start-up, avoids the non-atomic rename problem on FAT.
- Openly reusable Japanese audio on Tatoeba is far smaller than the headline count: of 6,420 Japanese rows in the 2026-09-26 export, 5,111 have no licence (not reusable), 1,282 are CC BY-NC 4.0 and 27 are CC BY 4.0 (https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences_with_audio.tsv.bz2). On-device synthesis avoids audio licensing: ESP32FormantTTS speaks hiragana by formant synthesis and has a Cardputer ADV application (https://github.com/necobit/ESP32FormantTTS and https://github.com/necobit/Cardputer-TTS, third-party, robotic voice). The neural sanoTTS-jp reports 211 KB of static RAM and non-MIT model weights and was verified only on M5Stack CoreS3, so it is unlikely to fit a Cardputer (https://github.com/ayutaz/sanoTTS-jp).
- KanjiVG is small enough to repack for the card or flash: release r20260714 holds 6,703 characters and 79,921 strokes made of about 178,000 cubic Bezier segments, 94 percent of them written as relative 'c' commands (measured from https://github.com/KanjiVG/kanjivg/releases/download/r20260714/kanjivg-20260714.xml.gz). Converting on the Mac to absolute fixed-point control points would give roughly 1 MB for the whole set (estimate) and removes SVG parsing from the firmware.

## What this means for the design

- Do all heavy lifting on the Mac: parse jmdict-simplified JSON, KANJIDIC2, KanjiVG and Tatoeba there and emit compact binary files for the SD card. The device should never parse JSON, XML, SVG or Anki packages.
- Build the dictionary as a few large files, not many small ones: one sorted fixed-width key index per search key type (kana reading, kanji headword, lower-cased English gloss word), each record holding a normalised key prefix plus a byte offset, with a sparse index of every 64th key held in RAM and an entries blob addressed by offset. Keep every file far below 4 GB and keep directories to tens of entries.
- Normalise search keys on the Mac (katakana to hiragana, long-vowel and small-kana handling, romaji to kana table) so the device does only romaji-to-kana conversion and a byte-wise binary search. Expect the user to type romaji on the 56-key keyboard; on-device kanji conversion has no precedent on this hardware.
- Ship two dictionary tiers: the 'common' JMdict subset (1.38 MB compressed JSON source) for fast default lookups and travel decks, and the full 218,794-entry set as a second index. Treat JMnedict (743,664 names) as optional; it is mainly useful for place and station names.
- Read the SD card with a 2 to 4 KB buffer and sector-aligned reads; aim for a lookup to cost one sparse-index hit in RAM plus one or two SD reads. Measure actual seek latency on the owner's card during the first device test, because no source gave a figure for the Cardputer.
- Prefer the custom index over SQLite for the read-only dictionary. If SQLite is wanted for convenience, restrict it to read-only queries on a Mac-built database with a small page size and bounded cache, and do not use it for review state.
- Pre-render stroke order on the Mac: flatten KanjiVG bezier paths to short polylines at the target size (109 px fits 1:1 beside a 131 px wide text column on the 240x135 screen) and store per-kanji stroke lists in one packed file with an offset table. Limit to the kanji the learner needs (for example 2,136 joyo kanji) to keep the file small.
- Store review state as an append-only log of fixed-size records (card id, timestamp or day number, grade, checksum) with f_sync after each review or small batch. Rebuild card state in RAM or into a snapshot at boot, keep the previous snapshot until the new one is verified, and never rely on rename-over-existing.
- Implement the scheduler as a small hand-written module. FSRS-6 with default parameters is feasible (21 float constants, exp and pow); SM-2 is a fallback if simplicity matters more. Keep the raw log so the Mac can re-run any scheduler later or optimise FSRS parameters after the trip.
- Schedule by day number, not wall-clock seconds. On boot, take time from NTP when Wi-Fi is available; otherwise use the last timestamp persisted on SD as a floor, show it and let the user confirm or correct the date. Never let the clock go backwards relative to the newest log record.
- Interop flow: on the Mac, export known words from Anki (TSV of notes, or a script reading the collection for intervals), WaniKani API or jpdb JSON into one TSV that marks words as known or due; after the trip, export the device's new and looked-up words as UTF-8 TSV with a stable GUID column and a tag column for Anki import.
- Include an About or Credits screen and a LICENCES file on the SD card naming EDRDG (JMdict, KANJIDIC, KRADFILE) with the project URLs, KanjiVG and Ulrich Apel, Tatoeba with per-sentence contributor attribution retained in the data file, tanos.co.uk, Wikivoyage with the page URL, and Kanji alive if its audio is used. Share-alike applies to the derived data files if they are ever redistributed.
- Treat pitch accent as optional and label its source; use Kanjium only with the caveat that provenance is thin, and avoid Wadoku or OJAD data if there is any chance of sharing the firmware with ads or for money.
- For audio, the realistic open option is the Kanji alive word recordings (Opus or MP3, 32 kHz mono); pre-convert to a format the device can decode cheaply. Full sentence audio under an open licence is scarce, so text-to-speech generated on the Mac before the trip is the practical route if sentence audio is wanted.
- Do not bundle Genki or Minna no Nihongo lists. Offer a generic 'import my own TSV deck' path so the owner can load lists they typed or exported themselves.
- Filter example sentences on the Mac: keep short sentences whose words are all within the learner's level (using tanos JLPT lists and JMdict priority tags) and cap the number per headword; the Tanaka-derived pool is known to contain unnatural sentences.
- Keep the daily load small by default (for example a cap on new cards and on total reviews per session) because 20 new cards a day grows to about 200 reviews a day, which is unrealistic while travelling.

## Not settled

- Exact free heap on each Cardputer variant under Arduino or ESP-IDF with display, keyboard, SD and Wi-Fi active; the 300 KB figure in the brief was not verified from a source.
- Whether the ESP32-S3FN8 in all three ESP32 variants truly has no PSRAM and whether any has a 32.768 kHz crystal; docs omit both but I did not inspect schematics.
- Whether the Cardputer power switch fully cuts power to the Stamp module on each variant (which decides if time survives 'off'), and how long deep sleep can hold time on the battery.
- Real per-seek and per-read latency of SPI-mode microSD on a Cardputer; published ESP32 benchmarks report throughput, not lookup latency.
- Whether the microSD pins and 25 MHz SPI setting documented for the original Cardputer are identical on v1.1 and ADV.
- Uncompressed sizes of the jmdict-simplified JSON files and the exact meaning of the 115 MB, 69 MB, 146 MB and 15 MB figures shown on the release page.
- Total number of characters in KanjiVG and whether kana are included; the pages opened did not give a count.
- Original source and licence chain of the Kanjium pitch accent data.
- Whether the accent type field is present in the UniDic 3.1.0 downloads and how it could be reduced to a word list small enough for the device.
- Entry counts for tanos.co.uk N4 to N1 vocabulary and kanji lists, and availability in CSV rather than DOC, PDF or Anki.
- AnkiConnect's current port, action list and licence from its primary README (sourcehut returned HTTP 502).
- Whether Duolingo or Bunpro offer any official export in 2026; only third-party tools appeared in search results.
- Legal status of redistributing a bare textbook vocabulary list; only a takedown notice was found, not a legal ruling or publisher policy.
- Whether the EDRDG licence's smartphone 'About screen' wording is intended to cover microcontroller firmware; following it is the safe reading.
- Whether the siara-cc SQLite library builds cleanly against the current Arduino-ESP32 and PlatformIO toolchains given no commits since June 2024.
- An openly licensed frequency list suitable for ranking JMdict entries; BCCWJ is restricted to research or education and jpdb-derived list licences were not checked.
