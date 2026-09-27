# Japanese text display and input

Japanese text on the Cardputer is well supported and feasible offline on every documented variant (K132, K132-V11, K132-Adv all list ESP32-S3FN8, 8 MB flash, 240x135 ST7789V2, no PSRAM listed). I read the M5GFX master sources (v0.2.30) directly and parsed the font arrays in memory: the built-in fonts cost 66 KB to 744 KB each, so several fit in the 3.34 MB app slot that PlatformIO's m5stack-stamps3 board uses by default (the Arduino IDE 'M5Cardputer' board defaults to a 1.31 MB app slot, which is tight). Coverage differs sharply: lgfxJapanGothic/Mincho carry 3,487 kanji (all Joyo kanji except the non-BMP form U+20B9F, but only 589 of 3,390 JIS level-2 kanji), whereas efontJA carries all of JIS level 1 and 2 (9,500 CJK glyphs). The screen geometry is the real constraint: 20x11 full-width characters at 12 px, 15x8 at 16 px, 10x5 at 24 px, on a panel of roughly 241 PPI where a 12 px glyph is about 1.3 mm tall. Existing Cardputer projects settle on 12 px for body text (two independent projects) or 24 px (one project). M5GFX decodes UTF-8, wraps per glyph (fine for Japanese, no kinsoku rules), measures with textWidth, and has no vertical writing. Japanese input is proven on this hardware: there are at least three Cardputer projects with romaji-to-kana, two of them with SKK kana-to-kanji conversion (one SD-backed, one from a flash partition). SKK dictionaries are small (S 56 KB, M 144 KB, ML 953 KB, L 4.5 MB in EUC-JP), GPL v2+, and pre-sorted for binary search. Google's transliterate endpoint answered over both HTTP and HTTPS without a key when I tested it today, but its official page states no terms, limits or guarantees. Not settled: measured RAM use of OpenFontRender on a no-PSRAM S3, the baseline firmware size before fonts, and any rigorous minimum-legible-size evidence.

Fact-check: still running when this file was written; treat every statement as unchecked.

## Statements

### jp-01 · not checked

All three documented Cardputer variants list the same MCU, flash and display: ESP32-S3FN8, 8 MB flash, ST7789V2 1.14 inch 240x135, 56 keys (4x14). None of the three spec pages lists PSRAM. SKUs are K132 (original, Stamp-S3), K132-V11 (v1.1, Stamp-S3A), K132-Adv (ADV, Stamp-S3A, adds ES8311 codec, BMI270 IMU, 1750 mAh battery).

- Applies to: Cardputer K132, Cardputer v1.1 K132-V11, Cardputer ADV K132-Adv. Anything newer than ADV was not checked.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs>
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>

### jp-02 · not checked

M5GFX ships two built-in Japanese font families. efontJA comes in 10, 12, 14, 16 and 24 px, each in regular, bold, italic and bold-italic (20 fonts). lgfxJapanMincho, lgfxJapanMinchoP, lgfxJapanGothic and lgfxJapanGothicP come in 8, 12, 16, 20, 24, 28, 32, 36 and 40 px (36 fonts). All are u8g2-format arrays (lgfx::U8g2font).

- Applies to: All variants (library-level, M5GFX master, library.properties version 0.2.30)
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://docs.m5stack.com/ja/arduino/m5gfx/m5gfx_appendix>

### jp-03 · not checked

Flash footprint per built-in font, taken from the declared array lengths in source: efontJA_10 225,686 B; efontJA_12 308,265 B; efontJA_14 383,747 B; efontJA_16 467,155 B; efontJA_24 743,624 B (bold and italic variants are up to about 10 percent larger). lgfxJapanGothic_8 69,135 B; _12 108,977 B; _16 159,271 B; _20 217,424 B; _24 278,669 B; _40 534,168 B. Mincho and the P variants are within a few percent of Gothic at the same size.

- Applies to: All variants (library-level)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>

### jp-04 · not checked

Glyph coverage differs a lot between the two families. lgfxJapan* fonts hold 4,425 glyphs (4,427 for P variants) including 3,487 kanji: 2,827 of 2,965 JIS level-1 kanji, only 589 of 3,390 JIS level-2 kanji, and 2,135 of the 2,136 Joyo kanji (the one missing is U+20B9F, outside the 16-bit range; the common form U+53F1 is present). They include all hiragana, all katakana and 63 half-width katakana. efontJA 10 to 16 px hold 10,838 or 10,839 glyphs including 9,500 CJK ideographs, covering 100 percent of JIS level 1 and level 2; efontJA_24 holds 9,801 glyphs (8,784 kanji) and still covers all of JIS level 1 and 2. efontJA has no half-width katakana and lacks the two rare small kana U+3095 and U+3096. efontJA includes macron vowels (U+014D, U+016B) for Hepburn romanisation; lgfxJapan fonts do not.

- Applies to: All variants (library-level)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/ja.map>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip>

### jp-05 · not checked

With PlatformIO's m5stack-stamps3 board the default partition table is default_8MB.csv: two OTA app slots of 0x330000 (3,342,336 B) each plus 1.5 MB SPIFFS. In the Arduino IDE the 'M5Cardputer' board defaults to the 4 MB 'default' scheme with a 1,310,720 B app slot, with an '8M with spiffs' option at 3,342,336 B. So under PlatformIO defaults, three built-in fonts fit with room to spare on paper (efontJA 12+16+24 = 1.52 MB; lgfxJapanGothic 12+16+24 = 0.55 MB), while under the Arduino IDE default a single efontJA font plus Wi-Fi code is likely to overflow.

- Applies to: All variants with 8 MB flash (original, v1.1, ADV)
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/tools/partitions/default_8MB.csv>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/boards.txt>
- Source: <https://zenn.dev/kinako_fusic/articles/ee0e354e36960e>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>

### jp-06 · not checked

The lgfxJapan* fonts are machine-rasterised from IPA and IPAex outline fonts (otf2bdf at 72 dpi, then u8g2 bdfconv with ja.map), including the 8 and 12 px sizes, and fall under the IPA Font License. efontJA derives from the /efont/ bitmap font project and is BSD 3-clause licensed.

- Applies to: All variants (library-level)
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/efont/COPYRIGHT.txt>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>

### jp-07 · not checked

Screen capacity for full-width glyphs on 240x135, using the real line heights in the font headers: 8 px gives 30 columns by 15 lines (lgfxJapanGothic_8 has a 9 px line height); 10 px gives 24 by 13 (efontJA_10); 12 px gives 20 by 11 with efontJA_12, 20 by 10 with lgfxJapanGothic_12 (13 px line height) and 20 by 9 with lgfxJapanGothicP_12 (14 px); 16 px gives 15 by 8 (efontJA_16 and lgfxJapanGothic_16), 15 by 7 with GothicP_16 (19 px); 24 px gives 10 by 5.

- Applies to: All variants (same 240x135 panel)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-08 · not checked

The panel is about 241 pixels per inch (275.4 px diagonal over 1.14 inch), so one pixel is about 0.105 mm. Glyph heights are roughly 0.84 mm at 8 px, 1.05 mm at 10 px, 1.26 mm at 12 px, 1.68 mm at 16 px and 2.52 mm at 24 px.

- Applies to: All variants (same panel size and resolution in the docs)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### jp-09 · not checked

People who display Japanese on a Cardputer choose 12 px for body text in two independent projects and 24 px in a third. GeminiCardputerADV_Japanese uses lgfxJapanGothic_12 everywhere and describes it as a readable 12 px font. cardputer-adv-pocketjs chose Shinonome 12 px for body text and Misaki 8 px for a narrow console area after comparing 12 and 14 px on the real device, and rejected Noto Sans JP because its shapes break when reduced to 1 bit per pixel. CPJapaneseInput uses lgfxJapanGothic_24. I found no controlled test of the smallest size at which complex kanji stay recognisable on this panel.

- Applies to: GeminiCardputerADV_Japanese and cardputer-adv-pocketjs: Cardputer ADV. CPJapaneseInput: original Cardputer with Stamp-S3. Community projects, not vendor documentation.
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://raw.githubusercontent.com/k-natori/CPJapaneseInput/main/src/main.cpp>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>

### jp-10 · not checked

M5GFX decodes UTF-8 itself and draws only code points up to U+FFFF from fonts; anything above U+FFFF is routed to an optional emoji callback and otherwise drawn as the missing glyph. setTextWrap(true) wraps glyph by glyph when the next glyph would cross the right clip edge, with no word-boundary or Japanese line-breaking (kinsoku) rules. textWidth(string) returns the pixel width using the same decoding. setTextSize takes float scale factors for x and y.

- Applies to: All variants (library-level, M5GFX master)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.hpp>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>

### jp-11 · not checked

M5GFX has no vertical-writing text function, and neither built-in Japanese family contains vertical presentation forms (U+FE10 to FE19, U+FE30 to FE4F both zero glyphs). Vertical text would need per-glyph positioning in application code and would show horizontal forms of the long-vowel mark, brackets and punctuation. OpenFontRender does offer a Layout::Vertical option.

- Applies to: All variants (library-level)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.hpp>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.h>

### jp-12 · not checked

Fonts loaded at run time from SD through M5GFX loadFont default to the VLW format. The loader keeps five per-glyph tables in RAM totalling 9 bytes per glyph and reads each glyph bitmap from the file when drawing. That is about 40 KB of heap for a 4,425-glyph font and about 98 KB for a 10,838-glyph font. The same function also accepts an 'ft_lvgl' type handled by a compact bitmap font class (BFFfont). TrueType loading is compiled in only if a separate TTF header is present, and that header is not in the M5GFX or LovyanGFX master trees.

- Applies to: All variants (library-level). Heap impact matters on every variant because none lists PSRAM.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://zenn.dev/kinako_fusic/articles/ee0e354e36960e>
- Source: <https://github.com/keach/m5stack-tts/issues/91>

### jp-13 · not checked

A full-screen 240x135 sprite costs 64,800 bytes at 16 bits per pixel, 32,400 at 8, 16,200 at 4 (palette) and 4,050 at 1 bit per pixel, allocated from the internal heap when PSRAM is not used.

- Applies to: All variants
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFX_Sprite.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFX_Sprite.inl>

### jp-14 · not checked

Hand-drawn small bitmap fonts with full JIS level 1 and 2 coverage exist and are tiny. Misaki is 8x8 (glyphs drawn inside 7x7), k8x12 is 8x12, both cover JIS level 1 and 2 and are offered as BDF, TTF and PNG under a licence that permits use, copying, modification and distribution including commercially. Shinonome comes in 12, 14 and 16 px and is public domain. Stored as fixed 1-bit cells for all 6,879 JIS X 0208 characters, a Cardputer ADV project reports Misaki 54 KB, k8x12 81 KB, Shinonome 12 at 161 KB, 14 at 188 KB and 16 at 215 KB.

- Applies to: All variants (font data). Size figures measured by a community project on the Cardputer ADV.
- Source: <https://littlelimit.net/misaki.htm>
- Source: <https://littlelimit.net/k8x12.htm>
- Source: <https://littlelimit.net/font.htm>
- Source: <http://openlab.ring.gr.jp/efont/shinonome/>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-15 · not checked

Any u8g2-format font array can be used in M5GFX by wrapping it in lgfx::U8g2font, and u8g2 ships smaller Japanese subsets: u8g2_font_b10_t_japanese1 is 24,806 B (1,283 glyphs), b12_t_japanese1 33,370 B (1,283), b12_t_japanese3 109,530 B (3,870), b16_t_japanese3 156,817 B (3,875), unifont_t_japanese3 149,411 B (3,905). The same bdfconv tool can build a custom subset on the Mac from any BDF font.

- Applies to: All variants (library-level)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://github.com/olikraus/u8g2/wiki/fntgrpunifont>
- Source: <https://raw.githubusercontent.com/olikraus/u8g2/master/tools/font/build/single_font_files/u8g2_font_b12_t_japanese3.c>
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/IPA/README.md>

### jp-16 · not checked

OpenFontRender (v1.2.0) renders TrueType from SD or memory through FreeType (default 2.4.12), works with LovyanGFX-style drawers, and is FTL licensed. Its default glyph cache is the minimum setting and its optional render task defaults to a 20,480 byte stack. Its README lists M5Stack Basic, Core2 and Wio Terminal as tested, not the Cardputer, and gives no RAM figure. I found no measurement of its heap use on a no-PSRAM ESP32-S3.

- Applies to: All variants; untested on any Cardputer as far as I could find
- Source: <https://github.com/takkaO/OpenFontRender>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.cpp>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.h>

### jp-17 · not checked

Standard romaji input rules, as implemented in Google's open-source Mozc table (323 rows): n, nn and n-apostrophe all give the moraic n, so a learner must type nn or n' before a vowel or y; a doubled consonant gives small tsu plus the consonant; xtu, ltu and xtsu give a standalone small tsu; x or l prefixes give small kana; the hyphen gives the long-vowel mark; both Hepburn and Nihon-shiki spellings are accepted (shi/si, chi/ti, tsu/tu, fu/hu, ji/zi); di and du give the rarely used voiced chi and tsu kana. Long vowels are typed as spelled in kana (kou, not ko with a macron) and the particles wa, o and e must be typed ha, wo and he.

- Applies to: All variants (software rule set)
- Source: <https://raw.githubusercontent.com/google/mozc/master/src/data/preedit/romanji-hiragana.tsv>
- Source: <https://en.wikipedia.org/wiki/W%C4%81puro_r%C5%8Dmaji>

### jp-18 · not checked

The Cardputer key map has hyphen, apostrophe, comma, period, square brackets and slash as unshifted keys, so the long-vowel mark and n-apostrophe can be typed directly. Arrow keys exist only on the Fn layer (Fn with semicolon, comma, period, slash), and Escape is Fn with backtick.

- Applies to: Original Cardputer, v1.1 and ADV through the M5Cardputer library v1.1.1, which states support for both Cardputer and Cardputer-ADV. The ADV uses a different keyboard controller but the same 4x14 map.
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.h>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/library.properties>

### jp-19 · not checked

Working Japanese input code for the Cardputer already exists. k-natori/CPJapaneseInput (original Cardputer, PlatformIO, M5Cardputer library) does romaji to kana from a 136-line table file and SKK-dictionary kana-to-kanji from a user-supplied UTF-8 dictionary on SD, toggled with Fn+Space, candidates cycled with Space; no licence is stated. Happymc2525/GeminiCardputerADV_Japanese (ADV) does romaji to hiragana only, explicitly without kanji conversion. dj-oyu/cardputer-adv-pocketjs (ADV, ESP-IDF, MIT for its own code) ports an SKK engine in plain C with the dictionary in a memory-mapped flash partition.

- Applies to: CPJapaneseInput: original Cardputer (Stamp-S3). The other two: Cardputer ADV. Community projects.
- Source: <https://github.com/k-natori/CPJapaneseInput>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>
- Source: <https://note.com/njrecalls/n/n1e39e8311951>
- Source: <https://github.com/k-natori/M5JapaneseInput>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-20 · not checked

SKK dictionary sizes in the skk-dev/dict repository today: SKK-JISYO.S 55,683 B in EUC-JP (73,810 B as UTF-8), 3,379 entries; M 144,468 B (194,881), 8,346 entries; ML 952,884 B (1,311,205), 48,750 entries; L 4,489,815 B (6,156,797), 175,791 entries. All four headers state GNU GPL version 2 or later. Entries are pre-sorted in EUC-JP byte order (okuri-ari descending, okuri-nasi ascending), which allows binary search by file seek; after a plain conversion to UTF-8 the okuri-nasi block of M and L is no longer byte-sorted.

- Applies to: All variants (data files)
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.S>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.M>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.ML>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.L>
- Source: <https://github.com/skk-dev/dict>
- Source: <https://note.com/njrecalls/n/n1e39e8311951>

### jp-21 · not checked

SD-backed or flash-backed dictionary lookup without loading the dictionary into RAM is practical and has been done. M5JapaneseInput stores the file offset of each first kana and seeks into the dictionary on SD because the whole file would not fit in heap; the same author reports the Cardputer port behaves almost identically. The pocketjs project instead preprocesses the dictionary on a PC into an indexed image in a 2 MiB flash partition: S becomes 116,991 B, M 303,297 B, ML 1,949,758 B, and L (8.07 MB) does not fit. Its engine state is about 1.5 KB of RAM per session.

- Applies to: SD approach: M5Stack Basic and original Cardputer. Flash-partition approach: Cardputer ADV. Both should carry over to any 8 MB variant.
- Source: <https://note.com/njrecalls/n/n1e39e8311951>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-22 · not checked

The lgfxJapan fonts cannot display every SKK conversion candidate. Kanji used in the dictionaries but absent from the lgfxJapan glyph set: 139 of 2,969 for SKK-JISYO.S, 164 of 3,031 for M, 1,327 of 4,587 for ML and 2,936 of 6,352 for L; in L, 2,921 entries have a first candidate containing a missing glyph. All kanji in all four dictionaries are inside JIS X 0208, so efontJA, Shinonome, Misaki and k8x12 cover them fully.

- Applies to: All variants (library and data level)
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/ja.map>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.L>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.ML>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-23 · not checked

Google's kana-to-kanji web endpoint (www.google.com/transliterate with langpair=ja-Hira|ja and text=hiragana) responded without any key over both plain HTTP and HTTPS when tested on 2026-09-27, returning a JSON array of segments each with up to five candidates. Commas in the text control segmentation. The official developer page documents the request and response only and states nothing about terms of use, rate limits, keys or availability.

- Applies to: All variants when online (hotspot or hotel Wi-Fi)
- Source: <https://www.google.co.jp/ime/cgiapi.html>
- Source: <http://www.google.com/transliterate?langpair=ja-Hira|ja&text=%E3%81%AB%E3%81%BB%E3%82%93%E3%81%94>
- Source: <https://scrapbox.io/villagepump/Google%E6%97%A5%E6%9C%AC%E8%AA%9E%E5%85%A5%E5%8A%9BAPI>

### jp-24 · not checked

Yahoo! Japan's kana-kanji conversion API has been called from an M5Stack over HTTPS POST with JSON and requires an application ID sent in the User-Agent header.

- Applies to: Demonstrated on M5Stack CoreS3 with CardKB, not on a Cardputer
- Source: <https://qiita.com/kowloon/items/de7538f7f0340406a718>

## What this means for the design

- Build with PlatformIO using board m5stack-stamps3 (default_8MB.csv, 3.34 MB app slot) rather than the Arduino IDE default, which gives only a 1.31 MB app slot. If OTA or a launcher is not needed, a custom single-app partition table frees several more MB for fonts or an embedded dictionary.
- Pick fonts by the learner's level. For kana plus Joyo kanji study, lgfxJapanGothic 12, 16 and 24 together cost about 0.55 MB and cover every Joyo kanji in its usual form. For a general dictionary, SKK candidates, place names or personal names, use efontJA (all of JIS level 1 and 2) or a Shinonome, k8x12 or Misaki subset built on the Mac, because lgfxJapan fonts miss 2,801 of the 3,390 JIS level-2 kanji.
- Plan screens around 12 px for dense reading (20 columns by 10 or 11 lines) and 24 px for the character being studied (10 by 5). A flashcard layout that fits: one 24 px headword line, one 12 px reading line, and four to six 12 px lines for meaning and example. Treat 8 px as kana-and-digits only (status bar, furigana), not for kanji.
- Furigana above kanji is affordable at 16 px body plus 8 px ruby (about 25 px per row, 5 rows of 15 characters) or 24 px body plus 10 or 12 px ruby (3 rows of 10). A simpler and more legible alternative on this screen is a key that toggles the whole line between kanji and kana, or a dedicated reading line under the headword.
- Do line breaking in application code: M5GFX wraps per glyph, which is acceptable for Japanese, but it has no kinsoku rules, so pre-wrap text on the Mac at 20 or 15 full-width columns (keeping small kana, long-vowel marks and closing punctuation off line starts) and store the wrapped lines on the SD card.
- Pre-compute on the Mac everything that costs RAM or CPU on the device: convert dictionaries to UTF-8, re-sort them by UTF-8 bytes or build an offset index, strip candidates whose kanji are not in the chosen font, and generate furigana readings and romaji for every card so the device never has to analyse Japanese text.
- Avoid loading large VLW fonts from SD (9 bytes of heap per glyph, 40 to 100 KB for full Japanese sets, plus SD seeks for every glyph) and avoid TrueType rendering as the primary path on a device with no PSRAM; linked-in bitmap fonts cost zero heap. Keep OpenFontRender for an optional large single-kanji display only if a test shows it fits.
- Do not use vertical writing; neither M5GFX nor the built-in fonts support it and the screen is only 135 px tall.
- For Japanese typing practice, romaji-to-kana is a small table (the Mozc table is 323 rows; one Cardputer project uses 136) and works fully offline. Make the engine teach the learner the input conventions: nn or n' before vowels, ha/wo/he for particles, ou and uu for long vowels, hyphen for the katakana long mark.
- For kana-to-kanji, make offline SKK-style conversion the baseline with SKK-JISYO.M or ML on SD or in a flash partition (L is 4.5 MB raw and 8 MB indexed, too large for flash but fine on SD with an index), and treat Google transliterate as an optional online enhancement with a fallback, since it has no published terms or guarantees. SKK dictionaries are GPL v2 or later, which matters only if the firmware or card image is redistributed.
- Anything above U+FFFF will not render (M5GFX treats it as emoji), so normalise content on the Mac, for example replace U+20B9F with U+53F1, and strip or replace emoji and variation selectors.
- Draw through a sprite to avoid flicker: a full-screen 16-bit sprite is 65 KB, which is affordable once, but a 4-bit palette sprite (16 KB) or per-line sprites leave more heap for Wi-Fi and TLS.
- Arrow keys need the Fn modifier on the Cardputer, so use Space, Enter, Tab and number keys for candidate selection and card grading rather than arrows.

## Not settled

- How large is a baseline Cardputer firmware (M5Cardputer, M5Unified, Wi-Fi, HTTPS client, SD) before fonts? I did not build anything, so the headroom in the 3.34 MB slot is an estimate.
- What is the smallest pixel size at which dense kanji stay recognisable on this exact panel? Evidence is limited to three projects' choices (12 px twice, 24 px once); there is no controlled comparison, and efontJA versus lgfxJapanGothic versus Shinonome at 12 px has not been compared on a Cardputer in any source I found.
- How much heap does OpenFontRender with a Japanese TTF need on an ESP32-S3 without PSRAM, and how fast is it from SD? No source gave numbers.
- What is the BFFfont ('ft_lvgl') format in M5GFX exactly, and is it a better SD-loadable option than VLW? I saw the class in the header but found no documentation and did not test it.
- SD dictionary lookup latency on a Cardputer (seek plus scan) is not published anywhere I found.
- Google transliterate: no terms, quota or lifetime are published. Whether sustained use from a device is tolerated is unknown. The Yahoo alternative's official terms could not be read (HTTP 403).
- Whether any Cardputer variant newer than the ADV exists with PSRAM or more flash was not checked in this facet; the three documented variants are identical for display, flash and MCU.
- M+ bitmap fonts, FONTX2 files and BDF loading from SD were not verified. M5GFX's BDFfont class takes in-memory tables, and I found no SD loader for BDF or FONTX2 in M5GFX.
- Licences are not stated for k-natori/CPJapaneseInput, k-natori/M5JapaneseInput or Happymc2525/GeminiCardputerADV_Japanese, so reusing their code beyond reading it for ideas is unclear.
