# Japanese text display and input

Japanese text on the Cardputer is well supported and feasible offline on every documented variant (K132, K132-V11, K132-Adv all list ESP32-S3FN8, 8 MB flash, 240x135 ST7789V2, no PSRAM listed). I read the M5GFX master sources (v0.2.30) directly and parsed the font arrays in memory: the built-in fonts cost 66 KB to 744 KB each, so several fit in the 3.34 MB app slot that PlatformIO's m5stack-stamps3 board uses by default (the Arduino IDE 'M5Cardputer' board defaults to a 1.31 MB app slot, which is tight). Coverage differs sharply: lgfxJapanGothic/Mincho carry 3,487 kanji (all Joyo kanji except the non-BMP form U+20B9F, but only 589 of 3,390 JIS level-2 kanji), whereas efontJA carries all of JIS level 1 and 2 (9,500 CJK glyphs). The screen geometry is the real constraint: 20x11 full-width characters at 12 px, 15x8 at 16 px, 10x5 at 24 px, on a panel of roughly 241 PPI where a 12 px glyph is about 1.3 mm tall. Existing Cardputer projects settle on 12 px for body text (two independent projects) or 24 px (one project). M5GFX decodes UTF-8, wraps per glyph (fine for Japanese, no kinsoku rules), measures with textWidth, and has no vertical writing. Japanese input is proven on this hardware: there are at least three Cardputer projects with romaji-to-kana, two of them with SKK kana-to-kanji conversion (one SD-backed, one from a flash partition). SKK dictionaries are small (S 56 KB, M 144 KB, ML 953 KB, L 4.5 MB in EUC-JP), GPL v2+, and pre-sorted for binary search. Google's transliterate endpoint answered over both HTTP and HTTPS without a key when I tested it today, but its official page states no terms, limits or guarantees. Not settled: measured RAM use of OpenFontRender on a no-PSRAM S3, the baseline firmware size before fonts, and any rigorous minimum-legible-size evidence.

Fact-check: done.

## Statements

### jp-01 · confirmed

All three documented Cardputer variants list the same MCU, flash and display: ESP32-S3FN8, 8 MB flash, ST7789V2 1.14 inch 240x135, 56 keys (4x14). None of the three spec pages lists PSRAM. SKUs are K132 (original, Stamp-S3), K132-V11 (v1.1, Stamp-S3A), K132-Adv (ADV, Stamp-S3A, adds ES8311 codec, BMI270 IMU, 1750 mAh battery).

- Applies to: Cardputer K132, Cardputer v1.1 K132-V11, Cardputer ADV K132-Adv. Anything newer than ADV was not checked.
- Correction: Confirmed for K132 (original), K132-V11 (v1.1) and K132-Adv (ADV). Sharpening: M5Stack's own Cardputer-family comparison data lists exactly these three SKUs, all ESP32-S3FN8, 8MB, 1.14 inch 240x135 ST7789V2, with no PSRAM row; the key-scan IC is 74HC138 on K132 and K132-V11 and TCA8418RTWR on K132-Adv. Absence of PSRAM on the ADV is also confirmed on real hardware by a second community project (M5OpurSan: esptool reports 'Features: WiFi, BLE', 8MB flash, and MALLOC_CAP_SPIRAM stays 0 even with BOARD_HAS_PSRAM set). The Arduino boards.txt entry for M5Cardputer still offers PSRAM menu options; they have no effect on this hardware. I could not parse the Espressif datasheet PDF, so the FN8 part-number meaning was not checked against Espressif directly. A newer Cardputer Zero exists but is a different platform (see missedFacts).
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs>
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>
- Source: <https://docs.m5stack.com/en/products_selector/m5cardputer_compare>

### jp-02 · confirmed

M5GFX ships two built-in Japanese font families. efontJA comes in 10, 12, 14, 16 and 24 px, each in regular, bold, italic and bold-italic (20 fonts). lgfxJapanMincho, lgfxJapanMinchoP, lgfxJapanGothic and lgfxJapanGothicP come in 8, 12, 16, 20, 24, 28, 32, 36 and 40 px (36 fonts). All are u8g2-format arrays (lgfx::U8g2font).

- Applies to: All variants (library-level, M5GFX master, library.properties version 0.2.30)
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://docs.m5stack.com/ja/arduino/m5gfx/m5gfx_appendix>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/library.properties>

### jp-03 · corrected

Flash footprint per built-in font, taken from the declared array lengths in source: efontJA_10 225,686 B; efontJA_12 308,265 B; efontJA_14 383,747 B; efontJA_16 467,155 B; efontJA_24 743,624 B (bold and italic variants are up to about 10 percent larger). lgfxJapanGothic_8 69,135 B; _12 108,977 B; _16 159,271 B; _20 217,424 B; _24 278,669 B; _40 534,168 B. Mincho and the P variants are within a few percent of Gothic at the same size.

- Applies to: All variants (library-level)
- Correction: All eleven byte counts are confirmed exactly from the declared array lengths on M5GFX master (0.2.30, released 2026-09-21); decoded data length is N minus 1. Only the side remarks are off. efontJA bold is 0 to 3 percent larger than regular, but italic and bold-italic are 5 to 14 percent larger, not 'up to about 10 percent' (efontJA_14_bi 436,983 B, efontJA_16_bi 530,475 B, efontJA_24_bi 812,886 B). Mincho is 2 to 6.4 percent larger than Gothic at the same size (lgfxJapanMincho_12 115,975 B) and the P variants are within about 6 percent (lgfxJapanGothicP_8 66,290 B, lgfxJapanMinchoP_8 65,160 B). Library-level, all variants.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>
- Source: <https://api.registry.platformio.org/v3/packages/m5stack/library/M5GFX>

### jp-04 · confirmed

Glyph coverage differs a lot between the two families. lgfxJapan* fonts hold 4,425 glyphs (4,427 for P variants) including 3,487 kanji: 2,827 of 2,965 JIS level-1 kanji, only 589 of 3,390 JIS level-2 kanji, and 2,135 of the 2,136 Joyo kanji (the one missing is U+20B9F, outside the 16-bit range; the common form U+53F1 is present). They include all hiragana, all katakana and 63 half-width katakana. efontJA 10 to 16 px hold 10,838 or 10,839 glyphs including 9,500 CJK ideographs, covering 100 percent of JIS level 1 and level 2; efontJA_24 holds 9,801 glyphs (8,784 kanji) and still covers all of JIS level 1 and 2. efontJA has no half-width katakana and lacks the two rare small kana U+3095 and U+3096. efontJA includes macron vowels (U+014D, U+016B) for Hepburn romanisation; lgfxJapan fonts do not.

- Applies to: All variants (library-level)
- Correction: Confirmed by an independent in-memory decode of all 56 arrays plus Unihan kJoyoKanji and the EUC-JP codec. Sharpening: the kanji counts are for the block U+4E00-9FFF only (with compatibility and Extension A ideographs the totals are 3,545 for lgfxJapan, 9,687 for efontJA 10-16 and 8,791 for efontJA_24). efontJA has one code point in the half-width block (U+FF64) and no half-width kana. efontJA_24 additionally lacks U+3094 (hiragana vu), U+30F7-30FA, circled numbers 16-20 and U+3231. Both families have gaps in common symbols: efontJA lacks U+FF5E (full-width tilde), U+2015, U+FF3C and U+FFE0-FFE2; lgfxJapan lacks U+2014, U+2212, U+2016, U+2605, U+2606, U+266A, U+2640, U+2642 and all of Latin Extended-A.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/ja.map>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip>

### jp-05 · confirmed

With PlatformIO's m5stack-stamps3 board the default partition table is default_8MB.csv: two OTA app slots of 0x330000 (3,342,336 B) each plus 1.5 MB SPIFFS. In the Arduino IDE the 'M5Cardputer' board defaults to the 4 MB 'default' scheme with a 1,310,720 B app slot, with an '8M with spiffs' option at 3,342,336 B. So under PlatformIO defaults, three built-in fonts fit with room to spare on paper (efontJA 12+16+24 = 1.52 MB; lgfxJapanGothic 12+16+24 = 0.55 MB), while under the Arduino IDE default a single efontJA font plus Wi-Fi code is likely to overflow.

- Applies to: All variants with 8 MB flash (original, v1.1, ADV)
- Correction: Confirmed. The same Arduino default (partitions 'default', 1,310,720 B; 8M option 3,342,336 B) is also in M5Stack's own board package 3.3.9, which is what M5Stack tells Arduino IDE users to install. PlatformIO has no Cardputer-specific board; m5stack-stamps3 and esp32-s3-devkitc-1 (the board the community projects use) both default to default_8MB.csv. The 'room to spare' estimate is now supported by two Cardputer ADV firmwares with Wi-Fi and TLS: about 1.22 MB including lgfxJapanGothic_12 (merged image 1,288,384 B written from offset 0) and about 1.6 MB including efontJA_16, so the baseline is near 1.1 MB and efontJA 12+16+24 lands near 2.6 MB of the 3,342,336 B slot. The stock max_app_8MB.csv gives one 0x7E0000 (8,257,536 B) app slot if OTA and SPIFFS are not needed. Applies to K132, K132-V11 and K132-Adv.
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/m5stack-stamps3.json>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/tools/partitions/default_8MB.csv>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/boards.txt>
- Source: <https://zenn.dev/kinako_fusic/articles/ee0e354e36960e>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>
- Source: <https://raw.githubusercontent.com/platformio/platform-espressif32/develop/boards/esp32-s3-devkitc-1.json>

### jp-06 · corrected

The lgfxJapan* fonts are machine-rasterised from IPA and IPAex outline fonts (otf2bdf at 72 dpi, then u8g2 bdfconv with ja.map), including the 8 and 12 px sizes, and fall under the IPA Font License. efontJA derives from the /efont/ bitmap font project and is BSD 3-clause licensed.

- Applies to: All variants (library-level)
- Correction: The IPA half is confirmed (README pipeline with otf2bdf -r 72 and bdfconv; IPA_Font_License_Agreement_v1.0.txt is in the directory). The efontJA half is oversimplified: M5GFX ships only the /efont/ BSD-style COPYRIGHT.txt, but upstream efont-unicode-bdf is a merge of separately licensed fonts. Its README lists the Japanese sources as Shinonome 12, 14 and 16 (public domain), jiskan24 for 24 px (public domain), and for 10 px the optional naga10 font whose licence is 'Freely usable, but restricted'. This matters only if firmware is redistributed. I verified by decoding that every JIS X 0208 kanji and kana glyph in efontJA_12, _14 and _16 is pixel-identical to Shinonome shnmk12, 14 and 16. The legibility inference does have blog support: the lang-ship post says efont, being a hand-dotted bitmap font, suffers less character crushing at small sizes, and that Mincho needs 24 px or more.
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/efont/COPYRIGHT.txt>
- Source: <https://lang-ship.com/blog/work/lovyangfx-3-ja-font/>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://github.com/m5stack/M5GFX/tree/master/src/lgfx/Fonts/IPA>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/COPYRIGHT.txt>

### jp-07 · confirmed

Screen capacity for full-width glyphs on 240x135, using the real line heights in the font headers: 8 px gives 30 columns by 15 lines (lgfxJapanGothic_8 has a 9 px line height); 10 px gives 24 by 13 (efontJA_10); 12 px gives 20 by 11 with efontJA_12, 20 by 10 with lgfxJapanGothic_12 (13 px line height) and 20 by 9 with lgfxJapanGothicP_12 (14 px); 16 px gives 15 by 8 (efontJA_16 and lgfxJapanGothic_16), 15 by 7 with GothicP_16 (19 px); 24 px gives 10 by 5.

- Applies to: All variants (same 240x135 panel)
- Correction: Confirmed from the headers and from decoded per-glyph advances: every kanji advances exactly the nominal size in all fonts checked, including the P variants. Additions: efontJA_14 gives 17 by 9; lgfxJapanGothicP_8, lgfxJapanMincho_8 and both MinchoP_8 have a 10 px line height (13 lines); lgfxJapanGothicP_24 has a 28 px line height, so 10 by 4. Half-width glyphs advance half the nominal size in efontJA and lgfxJapanGothic, so Latin text gets twice the columns. Same panel on all three variants.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl>
- Source: <https://raw.githubusercontent.com/dj-oyu/cardputer-adv-pocketjs/main/docs/apps/japanese-input.md>

### jp-08 · corrected

The panel is about 241 pixels per inch (275.4 px diagonal over 1.14 inch), so one pixel is about 0.105 mm. Glyph heights are roughly 0.84 mm at 8 px, 1.05 mm at 10 px, 1.26 mm at 12 px, 1.68 mm at 16 px and 2.52 mm at 24 px.

- Applies to: All variants (same panel size and resolution in the docs)
- Correction: The arithmetic from the nominal diagonal is right (241.6 ppi, 0.105 mm), but the standard 1.14 inch 135x240 ST7789 glass has an active area of 24.912 x 14.864 mm (Waveshare module spec for the same class of panel), which means non-square pixels: about 0.104 mm pitch along the 240 px axis and 0.110 mm along the 135 px axis (about 245 by 231 ppi). In the Cardputer's landscape orientation glyphs are therefore about 6 percent taller than wide: roughly 0.83 x 0.88 mm at 8 px, 1.04 x 1.10 mm at 10 px, 1.25 x 1.32 mm at 12 px, 1.66 x 1.76 mm at 16 px and 2.49 x 2.64 mm at 24 px. M5Stack publishes only the ST7789V2 driver datasheet, not the panel drawing, so this assumes the Cardputer uses the standard glass. Applies equally to K132, K132-V11 and K132-Adv.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://www.waveshare.com/wiki/1.14inch_LCD_Module>

### jp-09 · corrected

People who display Japanese on a Cardputer choose 12 px for body text in two independent projects and 24 px in a third. GeminiCardputerADV_Japanese uses lgfxJapanGothic_12 everywhere and describes it as a readable 12 px font. cardputer-adv-pocketjs chose Shinonome 12 px for body text and Misaki 8 px for a narrow console area after comparing 12 and 14 px on the real device, and rejected Noto Sans JP because its shapes break when reduced to 1 bit per pixel. CPJapaneseInput uses lgfxJapanGothic_24. I found no controlled test of the smallest size at which complex kanji stay recognisable on this panel.

- Applies to: GeminiCardputerADV_Japanese and cardputer-adv-pocketjs: Cardputer ADV. CPJapaneseInput: original Cardputer with Stamp-S3. Community projects, not vendor documentation.
- Correction: Two corrections. (1) GeminiCardputerADV_Japanese does use lgfxJapanGothic_12 everywhere and calls it readable, but its README says the bundled binary was built and not verified on a real device, so it is not on-device evidence. (2) The sample is too narrow to say people choose 12 px. Real-device Cardputer ADV projects: Cardputer-Adv-Radiko uses lgfxJapanGothic_12 (photo of the running device in its README); pocketjs uses Shinonome 12 after comparing 12 and 14 on the device (confirmed); M5OpurSan uses efontJA_16 on a 1 bpp canvas, 30 half-width columns by 8 rows (photos in its blog post); necobit/Cardputer-TTS uses efontJA_16. CPJapaneseInput (original Cardputer) and GOROman/LLMCardputer use lgfxJapanGothic_24. A code search also finds Cardputer projects on efontJA_10, _12 and _14 and lgfxJapanGothic_16. Because efontJA_12 is pixel-identical to Shinonome 12 for kanji and kana, the pocketjs result transfers to the built-in font. One ADV project records 12 px as the minimum legible size on the physical screen, for Latin text. I also found no controlled test of kanji recognisability. All community sources.
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://raw.githubusercontent.com/k-natori/CPJapaneseInput/main/src/main.cpp>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/README.md>

### jp-10 · confirmed

M5GFX decodes UTF-8 itself and draws only code points up to U+FFFF from fonts; anything above U+FFFF is routed to an optional emoji callback and otherwise drawn as the missing glyph. setTextWrap(true) wraps glyph by glyph when the next glyph would cross the right clip edge, with no word-boundary or Japanese line-breaking (kinsoku) rules. textWidth(string) returns the pixel width using the same decoding. setTextSize takes float scale factors for x and y.

- Applies to: All variants (library-level, M5GFX master)
- Correction: Confirmed in LGFXBase.inl and LGFXBase.hpp. Sharpening: the emoji callback is also called for code points at or below U+FFFF that the active font lacks, so it works as a general missing-glyph hook; variation selectors U+FE00-FE0F are skipped silently; a missing glyph is drawn as a hollow rectangle of the font's maximum glyph width; wrapping exists only in the print and write path (on by default), drawString never wraps; and M5GFX has textLength(string, width), which returns how many bytes of a UTF-8 string fit in a pixel width, so wrapping does not need repeated textWidth calls. Library-level, all variants.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.hpp>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl>

### jp-11 · confirmed

M5GFX has no vertical-writing text function, and neither built-in Japanese family contains vertical presentation forms (U+FE10 to FE19, U+FE30 to FE4F both zero glyphs). Vertical text would need per-glyph positioning in application code and would show horizontal forms of the long-vowel mark, brackets and punctuation. OpenFontRender does offer a Layout::Vertical option.

- Applies to: All variants (library-level)
- Correction: Confirmed. I decoded all 56 built-in Japanese arrays and none contains U+FE10-FE19 or U+FE30-FE4F. OpenFontRender's Layout::Vertical is not just an enum value; it is handled in its drawString paths. Per-glyph placement in M5GFX is possible through the public drawChar(codepoint, x, y).
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.hpp>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.h>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.cpp>

### jp-12 · confirmed

Fonts loaded at run time from SD through M5GFX loadFont default to the VLW format. The loader keeps five per-glyph tables in RAM totalling 9 bytes per glyph and reads each glyph bitmap from the file when drawing. That is about 40 KB of heap for a 4,425-glyph font and about 98 KB for a 10,838-glyph font. The same function also accepts an 'ft_lvgl' type handled by a compact bitmap font class (BFFfont). TrueType loading is compiled in only if a separate TTF header is present, and that header is not in the M5GFX or LovyanGFX master trees.

- Applies to: All variants (library-level). Heap impact matters on every variant because none lists PSRAM.
- Correction: Confirmed (9 bytes per glyph, glyph bitmaps read from the file on every draw, PSRAM-first allocation that falls back to internal heap; lgfx_TTFfont.hpp returns 404 in M5GFX master and in LovyanGFX master and develop, and exists only in third-party forks). Sharpening: BFFfont is not undocumented, it is the LVGL binary font format written by lv_font_conv; M5GFX ships examples/Basic/LvglFont for it and the loader cites font_spec.md. It accepts 1 to 4 bpp with optional compression and keeps the cmap payload plus 4 bytes per glyph in RAM. VLW and BFF are the only formats loadFont reads at run time, so BDF, FONTX2 and u8g2 files must be converted on the Mac or compiled in. A full JIS X 0208 VLW font would hold about 62 KB of heap, against about 78 KB free after Wi-Fi in one measured ADV firmware, so compiled-in fonts are the practical choice for full coverage.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://zenn.dev/kinako_fusic/articles/ee0e354e36960e>
- Source: <https://github.com/keach/m5stack-tts/issues/91>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/examples/Basic/LvglFont/LvglFont.ino>

### jp-13 · confirmed

A full-screen 240x135 sprite costs 64,800 bytes at 16 bits per pixel, 32,400 at 8, 16,200 at 4 (palette) and 4,050 at 1 bit per pixel, allocated from the internal heap when PSRAM is not used.

- Applies to: All variants
- Correction: Confirmed; the buffer is one contiguous DMA-capable block. Real-device caution from M5OpurSan on a Cardputer ADV (community, specific to that firmware): with Wi-Fi up the heap fell from about 129 KB to 78 KB, an mbedTLS handshake needs 45 to 50 KB, and an 8 bpp full-screen canvas (32 KB) left 44 KB so HTTPS failed until the canvas was changed to 1 bpp (4 KB). pocketjs reports a largest contiguous free block near 23.5 KiB while an app runs.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFX_Sprite.hpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFX_Sprite.inl>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/CLAUDE.md>
- Source: <https://raw.githubusercontent.com/dj-oyu/cardputer-adv-pocketjs/main/docs/platform/hardware-constraints.md>

### jp-14 · confirmed

Hand-drawn small bitmap fonts with full JIS level 1 and 2 coverage exist and are tiny. Misaki is 8x8 (glyphs drawn inside 7x7), k8x12 is 8x12, both cover JIS level 1 and 2 and are offered as BDF, TTF and PNG under a licence that permits use, copying, modification and distribution including commercially. Shinonome comes in 12, 14 and 16 px and is public domain. Stored as fixed 1-bit cells for all 6,879 JIS X 0208 characters, a Cardputer ADV project reports Misaki 54 KB, k8x12 81 KB, Shinonome 12 at 161 KB, 14 at 188 KB and 16 at 215 KB.

- Applies to: All variants (font data). Size figures measured by a community project on the Cardputer ADV.
- Correction: Confirmed from the Little Limit and /efont/ pages and the pocketjs document. Sharpening: the size table is in KiB and is simply fixed cell bytes times 6,879 (8, 12, 24, 28 and 32 bytes per glyph), excluding header and code map, so it is arithmetic rather than a measurement. Misaki is also offered as FONTX2, and its author's own page says 8x8 dots are hard to read. Shinonome 12 also comes in mincho and maru styles. Building Shinonome yourself is unnecessary because efontJA_12, _14 and _16 already contain it.
- Source: <https://littlelimit.net/misaki.htm>
- Source: <https://littlelimit.net/k8x12.htm>
- Source: <https://littlelimit.net/font.htm>
- Source: <http://openlab.ring.gr.jp/efont/shinonome/>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://sources.debian.org/data/main/x/xfonts-shinonome/1:0.9.11-7/LICENSE>

### jp-15 · confirmed

Any u8g2-format font array can be used in M5GFX by wrapping it in lgfx::U8g2font, and u8g2 ships smaller Japanese subsets: u8g2_font_b10_t_japanese1 is 24,806 B (1,283 glyphs), b12_t_japanese1 33,370 B (1,283), b12_t_japanese3 109,530 B (3,870), b16_t_japanese3 156,817 B (3,875), unifont_t_japanese3 149,411 B (3,905). The same bdfconv tool can build a custom subset on the Mac from any BDF font.

- Applies to: All variants (library-level)
- Correction: Confirmed. Sharpening: these u8g2 sets are cut from the same /efont/ source as efontJA, so they give the same Shinonome glyph shapes at about a third of the flash. Decoded coverage: japanese1 has 1,006 kanji; japanese2 has 1,946 kanji and covers 1,940 of the 2,136 Joyo kanji; japanese3 has 3,449 kanji and covers 2,132 of 2,136 Joyo (2,825 JIS level 1, 583 level 2). So u8g2_font_b12_t_japanese3 (109,530 B) matches lgfxJapanGothic_12 in size and Joyo coverage but with hand-drawn bitmaps. u8g2 has no 14 px or 24 px efont sets.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp>
- Source: <https://github.com/olikraus/u8g2/wiki/fntgrpunifont>
- Source: <https://raw.githubusercontent.com/olikraus/u8g2/master/tools/font/build/single_font_files/u8g2_font_b12_t_japanese3.c>
- Source: <https://github.com/m5stack/M5GFX/blob/master/src/lgfx/Fonts/IPA/README.md>
- Source: <https://raw.githubusercontent.com/olikraus/u8g2/master/tools/font/build/single_font_files/u8g2_font_b12_t_japanese2.c>
- Source: <https://raw.githubusercontent.com/olikraus/u8g2/master/tools/font/build/single_font_files/u8g2_font_b12_t_japanese1.c>

### jp-16 · corrected

OpenFontRender (v1.2.0) renders TrueType from SD or memory through FreeType (default 2.4.12), works with LovyanGFX-style drawers, and is FTL licensed. Its default glyph cache is the minimum setting and its optional render task defaults to a 20,480 byte stack. Its README lists M5Stack Basic, Core2 and Wio Terminal as tested, not the Cardputer, and gives no RAM figure. I found no measurement of its heap use on a no-PSRAM ESP32-S3.

- Applies to: All variants; untested on any Cardputer as far as I could find
- Correction: Library facts confirmed: v1.2.0, FreeType 2.4.12 by default, FTL with a requirement to show credit, minimum cache by default, Layout::Vertical. Corrections: (1) the render task is off by default when FreeType 2.4.12 is used, so the 20,480 B stack is only allocated if it is enabled; (2) the README's tested list also includes STM32H750; (3) it is not unused on the Cardputer: handomade/M5AozoraTxtViewer (community, Cardputer variant not stated) renders a Japanese TTF from SD with OpenFontRender at 10 to 16 px and falls back to lgfxJapanGothic_12. No project publishes heap figures, so the RAM need on a no-PSRAM ESP32-S3 is still unmeasured. The tested M5Stack Basic also has no PSRAM, but the README sample uses a 'Tiny' subset font.
- Source: <https://github.com/takkaO/OpenFontRender>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.cpp>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/src/OpenFontRender.h>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/README.md>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/library.properties>
- Source: <https://raw.githubusercontent.com/takkaO/OpenFontRender/master/LICENSE>

### jp-17 · confirmed

Standard romaji input rules, as implemented in Google's open-source Mozc table (323 rows): n, nn and n-apostrophe all give the moraic n, so a learner must type nn or n' before a vowel or y; a doubled consonant gives small tsu plus the consonant; xtu, ltu and xtsu give a standalone small tsu; x or l prefixes give small kana; the hyphen gives the long-vowel mark; both Hepburn and Nihon-shiki spellings are accepted (shi/si, chi/ti, tsu/tu, fu/hu, ji/zi); di and du give the rarely used voiced chi and tsu kana. Long vowels are typed as spelled in kana (kou, not ko with a macron) and the particles wa, o and e must be typed ha, wo and he.

- Applies to: All variants (software rule set)
- Correction: Confirmed by querying the 323-row table for every case. Additions: Mozc is BSD 3-clause; the table also maps ltsu and xn, and maps vu to U+3094, a glyph efontJA_24 lacks; tilde and z- give the wave dash U+301C, which both built-in families have.
- Source: <https://raw.githubusercontent.com/google/mozc/master/src/data/preedit/romanji-hiragana.tsv>
- Source: <https://en.wikipedia.org/wiki/W%C4%81puro_r%C5%8Dmaji>
- Source: <https://raw.githubusercontent.com/google/mozc/master/LICENSE>

### jp-18 · confirmed

The Cardputer key map has hyphen, apostrophe, comma, period, square brackets and slash as unshifted keys, so the long-vowel mark and n-apostrophe can be typed directly. Arrow keys exist only on the Fn layer (Fn with semicolon, comma, period, slash), and Escape is Fn with backtick.

- Applies to: Original Cardputer, v1.1 and ADV through the M5Cardputer library v1.1.1, which states support for both Cardputer and Cardputer-ADV. The ADV uses a different keyboard controller but the same 4x14 map.
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.h>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/library.properties>

### jp-19 · corrected

Working Japanese input code for the Cardputer already exists. k-natori/CPJapaneseInput (original Cardputer, PlatformIO, M5Cardputer library) does romaji to kana from a 136-line table file and SKK-dictionary kana-to-kanji from a user-supplied UTF-8 dictionary on SD, toggled with Fn+Space, candidates cycled with Space; no licence is stated. Happymc2525/GeminiCardputerADV_Japanese (ADV) does romaji to hiragana only, explicitly without kanji conversion. dj-oyu/cardputer-adv-pocketjs (ADV, ESP-IDF, MIT for its own code) ports an SKK engine in plain C with the dictionary in a memory-mapped flash partition.

- Applies to: CPJapaneseInput: original Cardputer (Stamp-S3). The other two: Cardputer ADV. Community projects.
- Correction: CPJapaneseInput (original Cardputer) and pocketjs (ADV) are confirmed as described; the kanadic.txt table has 137 entries and is minimal (moraic n only via nn, small tsu only via tt, xtu or xtsu), and neither it nor M5JapaneseInput has a licence file. GeminiCardputerADV_Japanese is confirmed as romaji-to-hiragana only, but its README states the binary was not verified on a real device, so it should not be counted as proven working. Missed: kikyujin/M5OpurSan (Cardputer ADV, PlatformIO, MIT code, GPL-2.0 dictionary) is a complete offline IME verified by its author on the ADV, with a 927,000-entry dictionary on microSD; necobit/Cardputer-TTS (ADV, MIT) has a romaji-to-hiragana converter feeding on-device speech synthesis. Toggle keys differ per project: Fn+Space, Tab, Ctrl+J or Opt+Space.
- Source: <https://github.com/k-natori/CPJapaneseInput>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>
- Source: <https://note.com/njrecalls/n/n1e39e8311951>
- Source: <https://github.com/k-natori/M5JapaneseInput>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>

### jp-20 · confirmed

SKK dictionary sizes in the skk-dev/dict repository today: SKK-JISYO.S 55,683 B in EUC-JP (73,810 B as UTF-8), 3,379 entries; M 144,468 B (194,881), 8,346 entries; ML 952,884 B (1,311,205), 48,750 entries; L 4,489,815 B (6,156,797), 175,791 entries. All four headers state GNU GPL version 2 or later. Entries are pre-sorted in EUC-JP byte order (okuri-ari descending, okuri-nasi ascending), which allows binary search by file seek; after a plain conversion to UTF-8 the okuri-nasi block of M and L is no longer byte-sorted.

- Applies to: All variants (data files)
- Correction: Confirmed exactly (sizes, entry counts, GPL v2 or later in all four headers, EUC-JP sort order). Sharpening: after conversion to UTF-8 the okuri-nasi block is unsorted in M (2 inversions), ML (22) and L (285), because the long-vowel mark sorts before kana in EUC-JP and after it in UTF-8; S stays sorted in both encodings.
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.S>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.M>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.ML>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.L>
- Source: <https://github.com/skk-dev/dict>
- Source: <https://note.com/njrecalls/n/n1e39e8311951>

### jp-21 · confirmed

SD-backed or flash-backed dictionary lookup without loading the dictionary into RAM is practical and has been done. M5JapaneseInput stores the file offset of each first kana and seeks into the dictionary on SD because the whole file would not fit in heap; the same author reports the Cardputer port behaves almost identically. The pocketjs project instead preprocesses the dictionary on a PC into an indexed image in a 2 MiB flash partition: S becomes 116,991 B, M 303,297 B, ML 1,949,758 B, and L (8.07 MB) does not fit. Its engine state is about 1.5 KB of RAM per session.

- Applies to: SD approach: M5Stack Basic and original Cardputer. Flash-partition approach: Cardputer ADV. Both should carry over to any 8 MB variant.
- Correction: Confirmed. Caveat on the SD method: CPJapaneseInput reads the whole dictionary at boot to index first-kana offsets and then reads lines sequentially inside the block, which suits S and M but would be slow for L. The pocketjs document says its flash-mapped engine cannot be pointed at SD. A third approach exists: M5OpurSan does binary search by file seek over a byte-sorted 33.3 MB binary dictionary on SD with an offset table at the end of the file, on a Cardputer ADV. No project publishes lookup latency; the M5Stack author only says the speed was sufficient.
- Source: <https://note.com/njrecalls/n/n1e39e8311951>
- Source: <https://note.com/njrecalls/n/n7c364c39e14e>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://raw.githubusercontent.com/k-natori/CPJapaneseInput/main/src/JPutil.cpp>
- Source: <https://raw.githubusercontent.com/dj-oyu/cardputer-adv-pocketjs/main/docs/apps/japanese-input.md>
- Source: <https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/opur_editor/opur_dict.c>

### jp-22 · confirmed

The lgfxJapan fonts cannot display every SKK conversion candidate. Kanji used in the dictionaries but absent from the lgfxJapan glyph set: 139 of 2,969 for SKK-JISYO.S, 164 of 3,031 for M, 1,327 of 4,587 for ML and 2,936 of 6,352 for L; in L, 2,921 entries have a first candidate containing a missing glyph. All kanji in all four dictionaries are inside JIS X 0208, so efontJA, Shinonome, Misaki and k8x12 cover them fully.

- Applies to: All variants (library and data level)
- Correction: Confirmed exactly by recomputing from ja.map and the four dictionaries (139 of 2,969; 164 of 3,031; 1,327 of 4,587; 2,936 of 6,352; 2,921 first candidates in L). One nuance: with a standard EUC-JP decoder the candidates also contain U+2015 and U+FF3C, which efontJA lacks although it has the equivalent JIS glyphs at U+2014 and U+005C, so remap those two when converting the dictionary to UTF-8.
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/ja.map>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.L>
- Source: <https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.ML>
- Source: <https://github.com/dj-oyu/cardputer-adv-pocketjs/blob/main/docs/apps/japanese-input.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c>
- Source: <https://raw.githubusercontent.com/dj-oyu/cardputer-adv-pocketjs/main/docs/apps/japanese-input.md>

### jp-23 · confirmed

Google's kana-to-kanji web endpoint (www.google.com/transliterate with langpair=ja-Hira|ja and text=hiragana) responded without any key over both plain HTTP and HTTPS when tested on 2026-09-27, returning a JSON array of segments each with up to five candidates. Commas in the text control segmentation. The official developer page documents the request and response only and states nothing about terms of use, rate limits, keys or availability.

- Applies to: All variants when online (hotspot or hotel Wi-Fi)
- Correction: Confirmed on 2026-09-27: plain HTTP and HTTPS both returned 200 with JSON and no key, and the official page documents only the request, the response and comma segmentation, with nothing on terms, limits or availability. Notes: one of my four HTTPS attempts timed out at 30 s; segments returned four or five candidates; candidates can include half-width katakana, which efontJA cannot draw, so filter them.
- Source: <https://www.google.co.jp/ime/cgiapi.html>
- Source: <http://www.google.com/transliterate?langpair=ja-Hira|ja&text=%E3%81%AB%E3%81%BB%E3%82%93%E3%81%94>
- Source: <https://scrapbox.io/villagepump/Google%E6%97%A5%E6%9C%AC%E8%AA%9E%E5%85%A5%E5%8A%9BAPI>
- Source: <https://www.google.com/transliterate?langpair=ja-Hira|ja&text=%E3%81%AB%E3%81%BB%E3%82%93%E3%81%94>

### jp-24 · confirmed

Yahoo! Japan's kana-kanji conversion API has been called from an M5Stack over HTTPS POST with JSON and requires an application ID sent in the User-Agent header.

- Applies to: Demonstrated on M5Stack CoreS3 with CardKB, not on a Cardputer
- Correction: Confirmed, now against an archived copy of the official page (snapshot 2026-01-06): POST only, JSON-RPC 2.0, endpoint https://jlp.yahooapis.jp/JIMService/V2/conversion, a Client ID is mandatory, at most 80 characters per request, and it also offers roman and predictive modes. The 'User-Agent: Yahoo AppID:' form comes from the Qiita code; the official page defers to sample code I did not open. The 403 the researcher hit is Yahoo! JAPAN's block on the EEA and UK, in force since 2022-04-06, and it also blocks the developer site where a Client ID is issued; the API host itself answered 401 without credentials from the same location. Demonstrated on CoreS3, not on any Cardputer.
- Source: <https://qiita.com/kowloon/items/de7538f7f0340406a718>
- Source: <https://web.archive.org/web/20260106103640id_/https://developer.yahoo.co.jp/webapi/jlp/jim/v2/conversion.html>
- Source: <https://developer.yahoo.co.jp/webapi/jlp/jim/v2/conversion.html>
- Source: <https://jlp.yahooapis.jp/JIMService/V2/conversion>

## Found by the fact-check

- A newer Cardputer does exist, on a different platform. M5Stack's Cardputer Zero and Zero Lite are Linux handhelds built on a Raspberry Pi Compute Module Zero (Kickstarter from 2026-05-26; M5Stack's page says shipping is expected around November), so none of the ESP32-S3, M5GFX, 240x135 or PlatformIO findings apply to one. A community app README gives its screen as 320x170 and uses the OS input method (fcitx5-mozc). In M5Stack's shop the original Cardputer and v1.1 are marked EOL and only the ADV is on sale, so a recently bought ESP32 Cardputer is most likely an ADV. Sources: https://m5stack.com/cardputerzero , https://github.com/m5stack/CardputerZeroRepository , https://github.com/u44e/cardputerzero-ssh-term (community), https://shop.m5stack.com/search?q=cardputer+zero&type=product
- The built-in efontJA_12, _14 and _16 are the Shinonome hand-drawn bitmap font. Decoding the arrays and comparing with shnmk12, 14 and 16.bdf shows all 6,356 kanji-block glyphs and all 177 kana pixel-identical at each size; only about 230 symbols differ. The upstream README names the sources: Shinonome for 12, 14 and 16 px, jiskan24 for 24 px, the optional naga10 for 10 px. So the font pocketjs chose after an on-device comparison is already in M5GFX and no custom font build is needed. Sources: https://sources.debian.org/data/main/x/xfonts-efont-unicode/0.4.2-12/README , https://sources.debian.org/data/main/x/xfonts-shinonome/1:0.9.11-7/bdf/ , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c
- Pre-generated or model-written Japanese text will hit glyph gaps unless it is normalised on the Mac to the chosen font. efontJA has the wave dash U+301C but not the full-width tilde U+FF5E that Windows-origin text uses, and lacks U+2015, U+FF3C, U+FFE0-FFE2 and half-width katakana. lgfxJapan fonts have both tildes but lack U+2014, U+2212, U+2016, the star and music-note symbols (U+2605, U+2606, U+266A) and every macron vowel, so they cannot show Hepburn romanisation with macrons. A missing glyph renders as a hollow box. A Cardputer ADV radio project already strips music-note symbols for this reason. Sources: decoded from https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c and https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c ; https://raw.githubusercontent.com/NAKADANobuhiro/Cardputer-Adv-Radiko/main/src/audio_player.cpp (community)
- kikyujin/M5OpurSan (community, verified by its author on a Cardputer ADV only) is a working offline Japanese word processor: romaji to kana to kanji with a 927,000-entry, 33.3 MB dictionary on microSD, efontJA_16 on a 1 bpp canvas, MIT code and GPL-2.0 dictionary. Its notes give the only real heap budget I found for this hardware: about 320 KB of DRAM in total, Wi-Fi takes about 50 KB (heap 129 KB down to 78 KB), a TLS handshake needs 45 to 50 KB, and an 8 bpp full-screen canvas made HTTPS fail. Design consequence: any firmware that also does HTTPS should use 1 bpp or 4 bpp sprites or draw directly. Sources: https://github.com/kikyujin/M5OpurSan , https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/CLAUDE.md , https://raw.githubusercontent.com/kikyujin/M5OpurSan/main/platformio.ini , https://note.com/kikyujin/n/ndca2a3bfbf7a (blog)
- M5GFX has hooks that simplify Japanese layout and were not reported. textLength(string, width) returns the byte count that fits a pixel width, so wrapping is one call per line. The callback set with setEmojiCallback is invoked for any code point the font lacks, which allows a fallback font or a logged warning. IFont::updateFontMetric(metrics, codepoint) returns false for a missing glyph; one Cardputer project uses it for per-glyph fallback between two fonts. drawChar(codepoint, x, y) is public, so furigana and vertical placement can be done per glyph. Sources: https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.hpp , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/LGFXBase.inl , https://github.com/ZUENS2020/Cardio (community)
- There is a Mac-side tool made for this workflow. lgfx-font-tool (LGFXFontToolJs, MIT, npm 3.0.0, by the author of the lang-ship blog) reads and writes u8g2, VLW, BFF, BDF and FONTX2, subsets a font to the characters in a text, checks that a text is fully covered by a font, and renders text pixel-exactly as LovyanGFX would. Japanese screens can be previewed and content validated before flashing. I did not run it. Sources: https://github.com/tanakamasayuki/LGFXFontToolJs , https://registry.npmjs.org/lgfx-font-tool
- Yahoo! JAPAN cannot be set up from the UK or EEA. The developer site returns HTTP 403 with a notice that Yahoo! JAPAN has been unavailable in the EEA and United Kingdom since 2022-04-06, so a Client ID cannot be obtained or the API tested before the trip from those regions; the conversion endpoint itself answered 401 from the same location. Google's keyless endpoint is the only online converter I could exercise. Sources: https://developer.yahoo.co.jp/webapi/jlp/jim/v2/conversion.html (shows the notice from the EEA or UK), https://web.archive.org/web/20260106103640id_/https://developer.yahoo.co.jp/webapi/jlp/jim/v2/conversion.html
- Two existing Cardputer apps are close to the learning use case (both community). kanawha-st/CardputerGlossary is a vocabulary trainer that reads id,word,meaning from a UTF-8 CSV on SD, shows Japanese in lgfxJapanGothic_16, keeps progress in progress.csv and builds with PlatformIO board m5stack-stamps3. handomade/M5AozoraTxtViewer is a Japanese text reader that pages UTF-8 files from SD, renders with an OpenFontRender TTF at 10 to 16 px or the built-in lgfxJapanGothic_12, and removes Aozora ruby marks instead of showing them. I found no Cardputer project that displays furigana. Sources: https://github.com/kanawha-st/CardputerGlossary , https://github.com/handomade/M5AozoraTxtViewer
- The brief asked about showing readings and the researcher returned no claim. By arithmetic from the font headers: 8 px ruby (9 or 10 px line height) over 16 px text gives a 25 px pitch, so 5 annotated lines of 15 characters; 8 px over 12 px gives 21 px, so 6 lines of 20; a reading on its own line at the same size gives 5 pairs at 12 px and 4 pairs at 16 px. The only built-in 8 px Japanese fonts are outline rasters and the Misaki author calls 8x8 hard to read, so ruby legibility needs an on-device test before committing. Also, setTextSize only scales bitmaps and adds no stroke detail, so a kanji study view needs a real large font: lgfxJapanGothic_40 (534,168 B) covers 2,135 of 2,136 Joyo kanji, and efontJA_24 (743,624 B) covers all of JIS level 1 and 2. Sources: https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/IPA/lgfx_font_japan.c , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/Fonts/efont/lgfx_efont_ja.c , https://littlelimit.net/misaki.htm

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
