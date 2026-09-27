# Audio and speech

Audio and speech facet for a Cardputer Japanese travel buddy. Headline findings: (1) every Cardputer variant I could document (original K132, v1.1, ADV) uses an ESP32-S3FN8 with 8 MB flash and no PSRAM, which rules out ESP-SR wake word/command recognition, current ESP32-audioI2S, and any in-RAM buffering of recordings; (2) Bluetooth earbuds are not possible on any variant (ESP32-S3 is LE-only, and ESP-IDF v6.1 still lists LE isochronous channels as unsupported on S3); (3) microphone and speaker are half-duplex in M5Unified on all variants (shared GPIO43 on original/v1.1; shared I2S clocks plus separate drivers on ADV), so the interaction model must be push-to-talk then play; (4) the only private-listening path is the ADV's 3.5 mm output jack; (5) playback that is proven without PSRAM is chunked PCM/WAV from SD via M5Unified playRaw, MP3 via ESP8266Audio 1.9.7 or minimp3, and Opus via Espressif's codec (about 27 KB heap) in an ESP-IDF build; (6) pre-generating Japanese clips on the Mac is cheap in storage (roughly 25 to 60 MB for 5,000 clips in Opus/MP3) and is the most robust design; VOICEVOX run locally also emits accent-phrase data that can be stored for a pitch-accent display; (7) cloud pronunciation scoring for Japanese exists (Azure ja-JP, accuracy/fluency/completeness) but I found no service that scores Japanese pitch accent, and Azure prosody scoring is en-US only; (8) reported round-trip latency for ESP32-S3 voice assistants ranges from about 4 to 5 s (LAN, local models) to about 20 s (chained Google cloud APIs). Several mic toolchain pitfalls are documented (silent mic depending on ESP-IDF version), so the mic should be tested on the actual device early. Loudness of the built-in speaker could not be quantified from sources; one magazine review calls the original's speaker 'quite tinny'.

Fact-check: done.

## Statements

### audio-01 · confirmed

On the original Cardputer and Cardputer v1.1, the PDM microphone (SPM1423: DAT=GPIO46, CLK=GPIO43) and the I2S speaker amplifier (NS4168: BCLK=GPIO41, SDATA=GPIO42, LRCLK=GPIO43) share GPIO43, so microphone and speaker cannot be active at the same time; firmware must call Speaker.end() before Mic.begin() and the reverse.

- Applies to: Cardputer (K132 original), Cardputer v1.1
- Correction: Confirmed as written for original (K132) and v1.1. Sharpening: M5Unified 0.2.23 uses one board ID (board_M5Cardputer) for both, with the PDM mic on I2S_NUM_0 (data GPIO46, clock GPIO43) and the speaker on I2S_NUM_1 (BCK 41, WS 43, DOUT 42), so both drivers claim GPIO43. M5Stack's comparison table on the ADV page also confirms that neither original nor v1.1 has an audio port.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/mic>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### audio-02 · corrected

On Cardputer ADV, M5Unified also treats mic and speaker as mutually exclusive: both go through the ES8311 codec on shared clock pins (BCK=GPIO41, WS=GPIO43; ADC data GPIO46, DAC data GPIO42), M5Unified drives them as two separate I2S drivers (mic on default I2S_NUM_0, speaker on I2S_NUM_1), and the mic enable/disable callbacks reset or power down the codec. Simultaneous record and play would need a custom full-duplex I2S driver; I found no source proving that works on ADV.

- Applies to: Cardputer ADV
- Correction: Applies to Cardputer ADV. The M5Unified description is confirmed (0.2.23): mic on I2S_NUM_0 with BCK41/WS43/DIN46, speaker on I2S_NUM_1 with BCK41/WS43/DOUT42; the mic callback enables only the ES8311 ADC clocks (reg 0x01=0xBA) and powers the codec down on disable, the speaker callback enables only the DAC clocks (0x01=0xB5). That exclusivity is a property of M5Unified (and of MicroPython machine.I2S, per lfurze), not of the hardware, and no custom driver is needed for duplex: upstream xiaozhi-esp32 ships an official board 'm5stack-cardputer-adv' that opens the ES8311 through Espressif esp_codec_dev with TX and RX channels created together on one I2S port (i2s_new_channel(&cfg,&tx,&rx)), 24 kHz in and out, no MCLK, CONFIG_SPIRAM=n. What remains unproven is capture quality while the speaker is playing (no echo measurement found), and using duplex means bypassing M5.Speaker and M5.Mic.
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Mic_Class.hpp>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/mic>
- Source: <https://github.com/espressif/esp-idf/issues/18621>
- Source: <https://github.com/78/xiaozhi-esp32/blob/main/main/boards/m5stack/cardputer-adv/m5stack_cardputer_adv.cc>
- Source: <https://github.com/78/xiaozhi-esp32/blob/main/main/audio/codecs/es8311_audio_codec.cc>

### audio-03 · confirmed

The recording API is M5Unified Mic_Class (exposed as M5Cardputer.Mic): record(int16_t* or uint8_t* buffer, length, sample_rate, stereo=false), with config defaults sample_rate 16000 Hz, over_sampling 2, magnification 16, noise_filter_level 0, dma_buf_len 128. The official Cardputer example records at 17 kHz in 240-sample chunks. Recording is asynchronous and chunk-based, so 16 kHz 16-bit mono capture in small blocks is the natural mode.

- Applies to: Cardputer original, v1.1, ADV (all via M5Unified)
- Correction: Confirmed (all variants via M5Unified). Two sharpenings: the struct default over_sampling=2 is not what runs, because M5.begin() sets mic_cfg.over_sampling=1 and i2s_port=I2S_NUM_0 for internal mics; and Mic_Class.hpp documents that on ES8311 (ADV) captured samples can be all zero for about one second after codec power-up.
- Source: <https://docs.m5stack.com/en/arduino/m5unified/mic_class>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/mic>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Mic_Class.hpp>
- Source: <https://github.com/m5stack/M5Cardputer/issues/11>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>

### audio-04 · corrected

Silent-microphone failures are documented and depend on toolchain version. On Cardputer v1.1 the stock mic examples recorded a flat line (M5Unified 0.2.8, Arduino IDE 2.3.6); the issue is still open. Community comments report fixes of resetting GPIO43/GPIO46 with gpio_reset_pin when switching between speaker and mic, and of building against ESP-IDF 5.4.x (M5Stack Arduino board package 3.2.x) instead of 5.5.x. On Cardputer ADV a separate ESP-IDF v5.5.1 regression in the legacy I2S API leaves the ES8311 mic silent; v5.4.2 works and the newer i2s_channel API works on v5.5.1.

- Applies to: Cardputer v1.1 (PDM mic issue); Cardputer ADV (ES8311 regression). Original K132 not explicitly reported but uses the same PDM design.
- Correction: v1.1 part confirmed: issue 11 is open (M5Unified 0.2.8, Arduino IDE 2.3.6), the M5Stack member only pointed to the docs example, and the workarounds are user comments dated 2026-01-24 (gpio_reset_pin on GPIO43/46) and 2026-04-25 (use IDF 5.4.x, board package 3.2.x); no maintainer root cause. ADV part needs correcting. The regression is reported between ESP-IDF v5.4.2 (works) and v5.5.1 (constant -8 samples), but 'the new i2s_channel API works on 5.5.1' is only the reporter's inference from M5Stack's demo firmware. M5Unified already uses the new i2s_std/i2s_pdm driver whenever driver/i2s_std.h exists (checked at tags 0.2.8, 0.2.10 and 0.2.21), and a comment dated 2026-09-07 reproduces the silent mic on ESP-IDF v6.0.3 and v6.1 with M5Unified 0.2.21 on that new driver path, with no MCLK pin involved. The Espressif assignee could not reproduce an MCLK fault and asked for scope traces; the issue is open, 'In Progress', root cause unknown. Reported working builds for the ADV mic: ESP-IDF 5.4.2, arduino-esp32 2.0.x through PlatformIO espressif32@^6.7.0 (claude-pocket), MicroPython v1.28.0 generic S3 (lfurze). arduino-esp32 3.2.1 is based on IDF 5.4.2 and 3.3.0 on IDF 5.5.0. The UIFlow pin-to-5.4 pull request (uiflow-micropython #97) is still open.
- Source: <https://github.com/m5stack/M5Cardputer/issues/11>
- Source: <https://github.com/m5stack/M5Unified/issues/184>
- Source: <https://github.com/espressif/esp-idf/issues/18621>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/0.2.10/src/utility/Mic_Class.cpp>
- Source: <https://github.com/m5stack/uiflow-micropython/pull/97>
- Source: <https://github.com/espressif/arduino-esp32/releases/tag/3.2.1>

### audio-05 · confirmed

All three documented variants use an ESP32-S3FN8 (8 MB flash) and have no PSRAM; usable RAM for an application is roughly 300 KB or less, and projects report far less free once Wi-Fi and TLS are running.

- Applies to: Cardputer original (Stamp-S3), v1.1 (Stamp-S3A), ADV (Stamp-S3A)
- Correction: Confirmed for original, v1.1 and ADV. The '2MB PSRAM' line in xiaozhi issue 1509 is a user-written feature request and is wrong. shop.m5stack.com currently lists the Cardputer Adv (K132-ADV, ESP32-S3FN8, 8 MB flash), a Meshtastic kit, the v1.1 accessory kit and the LoRa cap; no PSRAM variant. Upstream xiaozhi builds the ADV with CONFIG_SPIRAM=n, and a user in ESP-IDF issue 18621 reports esptool showing 'no embedded PSRAM' on an ADV. Shipped ADV firmware reports about 90 KB heap left after Wi-Fi, mbedTLS and M5GFX (claude-pocket, self-reported).
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://github.com/Theblackcat98/cardputer-voice>
- Source: <https://github.com/lichen79/xiaozhi-cardputer-adv>
- Source: <https://github.com/lfurze/cardputer-voice-assistant>

### audio-06 · confirmed

Speaker hardware is an 8 ohm 1 W cavity speaker on every variant: driven by an NS4168 I2S amplifier on original/v1.1 and by an ES8311 codec plus NS4150B amplifier on ADV. Only the ADV has a 3.5 mm audio output jack; plugging in disables the speaker amplifier in hardware. I found no measured loudness (dB SPL) or speech-intelligibility data for any variant; one magazine review of the original describes the speaker as 'quite tinny'.

- Applies to: Original/v1.1 (NS4168, no jack listed); ADV (ES8311 + NS4150B + 3.5 mm output)
- Correction: Confirmed. Sharpening: M5Stack describes the ADV jack as a '3.5mm audio output jack' (no microphone input is documented), and the ADV microphone is a MEMS part with SNR 65 dB routed through the ES8311. No loudness or intelligibility measurement exists in any source I opened either.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/speaker>
- Source: <https://github.com/bigbag/cardputer_adv_player>
- Source: <https://magazine.raspberrypi.com/articles/m5stack-card-computer-review>

### audio-07 · confirmed

Classic Bluetooth audio (A2DP) to earbuds is impossible on any Cardputer: the ESP32-S3 radio is Bluetooth 5 LE only and has no BR/EDR support.

- Applies to: All variants (all are ESP32-S3)
- Correction: Confirmed for all variants. Primary statement from an Espressif collaborator in the cited issue: 'Currently, the only chip that supports Classic Bluetooth is the ESP32.'
- Source: <https://www.espressif.com/en/products/socs/esp32-s3>
- Source: <https://github.com/espressif/esp-idf/issues/16232>
- Source: <https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/bt/br-edr.html>

### audio-08 · confirmed

LE Audio is not available on ESP32-S3 either: the ESP-IDF stable (v6.1) feature-support table for ESP32-S3 lists LE Isochronous Channels (BIS/CIS) as unsupported in the controller and in both Bluedroid and NimBLE hosts. Espressif's LE Audio library targets other chips (folders for esp32h4 and esp32s31). Bluetooth earbuds are therefore not an option by any standard profile.

- Applies to: All variants
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/ble/ble-feature-support-status.html>
- Source: <https://bluekitchen-gmbh.com/le-audio-on-esp32/>
- Source: <https://github.com/espressif/esp-ble-audio-lib>

### audio-09 · corrected

Current ESP32-audioI2S (schreibfaul1) requires PSRAM and should not be the playback or streaming library for a Cardputer. Only old versions run without PSRAM, and sources disagree on which is the last one (2.0.6 according to one user discussion, 3.0.11g according to the KALO project).

- Applies to: All variants (no PSRAM)
- Correction: Current ESP32-audioI2S (4.0.0, 2026-08-06) requires PSRAM: confirmed. The last no-PSRAM version is stated by the maintainer himself: release tag 3.2.1 (2025-05-31) is titled 'last release without PSRAM' and 3.3.0 says 'PSRAM must be activated'. In 3.2.1 the buffers fall back to internal RAM, while seeking and m3u8/HLS need PSRAM, and it requires Arduino core 3.x. Release 3.1.0 dropped Arduino 2.x, so on the official PlatformIO platform (Arduino 2.0.x) the usable range is 3.0.x. Cardputer projects pin 3.0.7 (claude-pocket on ADV, HTTP/HTTPS radio) and 3.0.13 (M5Cardputer_WebRadio). The 2.0.6 and 3.0.11g figures are third-party statements, and the '704 KB buffer at boot from 3.0.0' remark in discussion 1262 does not match the 3.2.1 source.
- Source: <https://github.com/schreibfaul1/ESP32-audioI2S/wiki>
- Source: <https://github.com/schreibfaul1/ESP32-audioI2S>
- Source: <https://github.com/schreibfaul1/ESP32-audioI2S/issues/1006>
- Source: <https://github.com/schreibfaul1/ESP32-audioI2S/discussions/1262>
- Source: <https://github.com/kaloprojects/KALO-ESP32-Voice-Chat-AI-Friends>
- Source: <https://github.com/cyberwisk/M5Cardputer_WebRadio>

### audio-10 · confirmed

Playback proven to work without PSRAM on Cardputer hardware: (a) WAV/PCM streamed from SD in small chunks through M5Unified Speaker.playRaw (official example uses two 1024-byte buffers); (b) MP3 from SD decoded by ESP8266Audio with a custom output that feeds Speaker.playRaw; (c) MP3 decoded by minimp3 on ADV under PlatformIO. ESP8266Audio must be pinned to 1.9.7 when the Arduino core is based on ESP-IDF 4.4, because 2.x needs ESP-IDF 5.x.

- Applies to: (a) all variants via M5Unified; (b) ADV (AndyAiCardputer project) and 'M5Stack Cardputer' (sanchitminda project, variant not specified); (c) ADV
- Correction: Confirmed. Sharpening: ESP8266Audio's README says the official PlatformIO framework-arduinoespressif32 package is still on IDF 4.x, so ESP8266Audio 2.x (current 2.4.1) needs the community pioarduino platform; the tested AndyAi build is espressif32@6.9.0 with ESP8266Audio 1.9.7 on ADV. The bigbag README states that heap and stack margins were not measured.
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/examples/Advanced/Speaker_SD_wav_file/Speaker_SD_wav_file.ino>
- Source: <https://github.com/AndyAiCardputer/mp3-player-winamp-cardputer-adv>
- Source: <https://github.com/sanchitminda/MP3PlayerForM5Cardputer>
- Source: <https://github.com/bigbag/cardputer_adv_player>
- Source: <https://github.com/earlephilhower/ESP8266Audio>
- Source: <https://github.com/AndyAiCardputer/mp3-player-winamp-cardputer-adv/blob/main/LIBRARY_VERSIONS.md>

### audio-11 · confirmed

M5Unified Speaker.playWav takes a pointer to a complete WAV image in memory, so it is only suitable for very short clips held in RAM or flash; clips on SD should be read in chunks and queued with playRaw (8-bit unsigned, 8-bit signed or 16-bit signed PCM, any sample rate, 8 virtual channels, speaker config default sample_rate 48000).

- Applies to: All variants via M5Unified
- Correction: Confirmed. Sharpening: playRaw keeps a pointer to the caller's buffer and does not copy it. Speaker_Class.hpp says two alternating buffers are enough only if each is refilled after the speaker task releases it (setBufferReleaseCallback), otherwise use three; claude-pocket reports audible doubling when one buffer was reused.
- Source: <https://docs.m5stack.com/en/arduino/m5unified/speaker_class>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/examples/Advanced/Speaker_SD_wav_file/Speaker_SD_wav_file.ino>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Speaker_Class.hpp>
- Source: <https://github.com/Nachtfux/claude-pocket/blob/main/docs/SPEC.md>

### audio-12 · confirmed

Low-bitrate speech codecs are decodable on ESP32-S3 within a no-PSRAM budget. Espressif's esp_audio_codec reports decoder heap of about 26.6 KB for Opus, 28.0 KB for MP3, 51.2 KB for AAC, 5.4 KB for AMR-WB, 1.8 KB for AMR-NB and under 0.2 KB for ADPCM and G.711 (measured on ESP32-S3R8). Opus encode plus decode has been run on a Cardputer ADV (xiaozhi port, ESP-IDF 5.4+) and on a generic ESP32-S3 without PSRAM.

- Applies to: All variants for the codec figures (chip-level); ADV specifically for the xiaozhi port
- Correction: Confirmed. Caveats: the figures are heap only (stack excluded; Espressif advises a task stack of about 20 KB to cover all decoders, and esp32-arduino-webrtc uses a 40 KB stack for Opus encode) and were measured on ESP32-S3R8 at 48 kHz stereo for Opus, AAC and ADPCM. esp_audio_codec is a precompiled Espressif component under Espressif-only terms; esp32-arduino-webrtc bundles version 2.6.2 inside an Arduino library, so Arduino use is possible. Besides the lichen79 fork, upstream xiaozhi-esp32 has an official Cardputer ADV board (Opus, no PSRAM).
- Source: <https://components.espressif.com/components/espressif/esp_audio_codec/versions/2.4.1/readme>
- Source: <https://github.com/lichen79/xiaozhi-cardputer-adv>
- Source: <https://github.com/akdeb/esp32-arduino-webrtc>
- Source: <https://github.com/pschatzmann/arduino-audio-tools/wiki/Encoding-and-Decoding-of-Audio>
- Source: <https://github.com/earlephilhower/ESP8266Audio>
- Source: <https://github.com/78/xiaozhi-esp32/tree/main/main/boards/m5stack/cardputer-adv>

### audio-13 · confirmed

AquesTalk ESP32 is a proprietary on-device Japanese TTS that fits the Cardputer's resources: ROM 200 KB and RAM 21 KB plus a kanji dictionary of 7 MB (about 380k words) or 2 MB 'small' (about 100k words) that can live on SD or SPI flash; kana/phonetic-only synthesis needs ROM 28 KB and RAM 500 B. Input is kanji-kana mixed UTF-8 text or AquesTalk phonetic notation; output is 8 kHz 16-bit PCM in one female voice; ESP32-S3 is supported from Ver. 2.4.2 (latest listed 2.4.4, 2024-10-30).

- Applies to: All variants (ESP32-S3); not tested on a Cardputer in any source I opened
- Correction: Confirmed against the AQUEST product page. The verified modules listed there are ESP32-DevKitC, M5Stack core, M5Stack coreS3 and 'M5StampS4' (as printed); no Cardputer test was found.
- Source: <https://www.a-quest.com/products/aquestalk_esp32.html>

### audio-14 · confirmed

AquesTalk ESP32 licensing: the free evaluation build replaces all na-row and ma-row sounds with 'nu' (unusable for language learning); the usage licence costs 1,980 yen per device, is bound to the individual ESP32 module, does not permit redistribution in products, and the licence certificate is shipped by post within Japan only (no overseas shipping). AQUEST's free personal-use programme lists AquesTalk, AquesTalk2, AquesTalk10 and AqKanji2Koe but not AquesTalk ESP32.

- Applies to: All variants
- Correction: Confirmed from AQUEST's own pages: evaluation builds turn all na-row and ma-row sounds into 'nu' (download page and AQUEST blog), the usage licence is 1,980 yen tied to the module MAC address, it has no expiry, it forbids selling or distributing products, and the certificate is posted with no overseas shipping.
- Source: <https://store.a-quest.com/items/10524168>
- Source: <https://www.a-quest.com/licence.html>
- Source: <https://www.a-quest.com/licence_free.html>
- Source: <https://lang-ship.com/blog/work/aquestalk-esp32-1-0-4/>
- Source: <https://www.a-quest.com/download.html>
- Source: <http://blog-yama.a-quest.com/?eid=970195>

### audio-15 · corrected

AquesTalk pico is a separate hardware speech-synthesis LSI driven over UART/I2C/SPI rather than a library; using it would mean adding an external chip to the Cardputer. I could not open an official product page for it (the URL I tried returned 404), so price, input format and licence terms are unverified.

- Applies to: All variants (external add-on)
- Correction: The official page exists and confirms the core claim: https://www.a-quest.com/products/aquestalkpicolsi.html. AquesTalk pico LSI is an ATmega328(P)-based chip (ATP3011 at 8 kHz, ATP3012 at 10 kHz sampling) in 28-pin DIP or 32-pin TQFP, driven over UART, I2C or SPI. Input is a romaji phonetic string in ASCII (kanji text must be converted first, for example with AqKanji2Koe), output is PWM audio that needs an external amplifier, one voice per part number, 15 preset messages. Sold by Akizuki Denshi, the AQUEST store and Act-Brain. The product page gives no price and no separate licence; a search result showed 1,380 yen for ATP3012F6-PU on the AQUEST store, which I did not open.
- Source: <https://lang-ship.com/blog/work/aquestalk-esp32-1-0-4/>
- Source: <https://www.a-quest.com/products/aquestalk_esp32.html>
- Source: <https://www.a-quest.com/products/aquestalkpicolsi.html>

### audio-16 · corrected

An open-source neural Japanese TTS for ESP32-S3 exists (sanoTTS-jp, code MIT, weights under a custom model licence with attribution and usage restrictions): 559K parameters, about 654 KB of int8 weights in flash, 22.05 kHz output, real-time factor about 0.47 on ESP32-S3, kana input natively and kanji via an optional 13.7 MB dictionary. Its published memory figures (static DIRAM 211,535 B, 181,119 B free after startup, arena peak about 113 to 115 KB) were measured on an M5Stack CoreS3, and I found no evidence it runs on a no-PSRAM Cardputer, especially alongside Wi-Fi.

- Applies to: Unverified for all Cardputer variants
- Correction: Figures and licence split confirmed from the repository (559 K parameters, 654,032 B int8 weights, 22.05 kHz, xRT 0.473, static DIRAM 211,535 B, 181,119 B free after start, arena peak 113 to 115 KB, measured on M5Stack CoreS3; v1.0.0 on 2026-09-12, v1.2.0 on 2026-09-19; weights allow commercial use with mandatory attribution and inherited usage restrictions). Correction: there is evidence on a no-PSRAM ESP32-S3. The project's support matrix records a third-party run on M5Stack ATOMS3 plus Voice/Echo Base (8 MB flash, no PSRAM) with the 4 MB and 2 MB dictionaries that produced audible speech (2026-09-10; not reproduced by the author, sentence length unknown). The author states a RAM need of about 342 KB for the kanji path and lists ESP32-S3 DevKit and StampS3 class boards as flash-and-go. It models pitch accent and its native input is hiragana plus accent marks. Still true: no Cardputer port, the Arduino/PlatformIO library has not been run on hardware and needs pioarduino 3.x, and nothing covers coexistence with Wi-Fi and TLS. On a Cardputer it is at best an offline experiment.
- Source: <https://github.com/ayutaz/sanoTTS-jp>
- Source: <https://qiita.com/nnn112358/items/e72ab79b7d6595b7e860>
- Source: <https://github.com/ayutaz/sanoTTS-jp/blob/main/docs/support-matrix.md>
- Source: <https://github.com/ayutaz/sanoTTS-jp/blob/main/docs/measurements.md>
- Source: <https://github.com/ayutaz/sanoTTS-jp/blob/main/LICENSE-MODEL.md>

### audio-17 · corrected

Cloud TTS services all offer Japanese and compact speech formats that a Cardputer can decode: Google Cloud TTS returns LINEAR16 (WAV), MP3 at 32 kbps, OGG_OPUS, MULAW or ALAW and supports ja-JP in Chirp 3 HD voices; Azure offers, among others, audio-16khz-32kbitrate-mono-mp3, ogg-16khz-16bit-mono-opus, raw-16khz-16bit-mono-pcm and amr-wb-16000hz; OpenAI offers mp3, opus, aac, flac, wav and headerless 24 kHz 16-bit PCM; Amazon Polly offers MP3, Ogg Vorbis and PCM with Japanese voices Mizuki, Takumi (standard and neural), Kazuha and Tomoko (neural only); ElevenLabs gates PCM and WAV output formats behind the Pro tier and has a Japanese-only text-normalisation option that increases latency.

- Applies to: All variants (service-side facts)
- Correction: Google, Azure, OpenAI and Polly details confirmed. Corrections: (1) ElevenLabs gates only 44.1 kHz PCM and WAV behind the Pro tier and 192 kbps MP3 behind Creator; pcm_16000, pcm_24000, wav_16000, mp3_22050_32 and opus_48000_32 carry no tier note. (2) Polly: Mizuki is standard only, Takumi is standard and neural, Kazuha and Tomoko are neural only; there is no Japanese generative or long-form voice. (3) OpenAI's guide says its voices are 'optimized for English', which is the only vendor statement on Japanese quality I found. (4) Google supports Japanese custom pronunciations including pitch accent (PHONETIC_ENCODING_JAPANESE_YOMIGANA, for example chopsticks = ^は!し, Tokyo dialect only), and the Chirp 3 HD page lists ja-JP with no exclusion for pause control or custom pronunciations.
- Source: <https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioEncoding>
- Source: <https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd>
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech>
- Source: <https://developers.openai.com/api/docs/guides/text-to-speech>
- Source: <https://docs.aws.amazon.com/polly/latest/dg/available-voices.html>
- Source: <https://aws.amazon.com/polly/faqs/>

### audio-18 · corrected

Storing pre-generated speech on SD for personal use is permitted by the services whose terms I could read: Amazon Polly explicitly allows caching and replay at no extra cost and says the output belongs to the customer; Google says generated audio files may be used to power applications subject to the Google Cloud terms; VOICEVOX allows commercial and non-commercial use but requires a credit such as 'VOICEVOX:ずんだもん' and compliance with each character's voice-library terms; OpenAI requires disclosing to end users that the voice is AI-generated. ElevenLabs free-plan output is reported to be non-commercial with attribution required when published, but I saw that only in search results, not on the opened page.

- Applies to: All variants (service-side facts)
- Correction: Polly, Google, VOICEVOX and OpenAI statements confirmed word for word on the vendor pages. Additions: VOICEVOX also requires that anyone you pass the audio to is bound by the same terms; credit-free commercial use of the Zundamon family costs 400,000 yen plus tax per character; AQUEST allows publishing or selling generated audio under a usage licence. The ElevenLabs free-plan statement could not be verified (the help-centre article returned HTTP 403 and my search budget was exhausted), so treat it as unknown. Azure terms were not checked by either of us.
- Source: <https://aws.amazon.com/polly/faqs/>
- Source: <https://docs.cloud.google.com/text-to-speech/docs/basics>
- Source: <https://voicevox.hiroshiba.jp/term/>
- Source: <https://zunko.jp/con_ongen_kiyaku.html>
- Source: <https://developers.openai.com/api/docs/guides/text-to-speech>
- Source: <https://www.a-quest.com/licence.html>

### audio-19 · confirmed

VOICEVOX Engine can be run locally (it documents Mac usage) and outputs 24 kHz WAV; its audio_query response exposes the kana reading with accent phrases, where an apostrophe marks the accent position and a slash separates phrases. That data can be saved next to each clip on the Mac so the Cardputer can display pitch-accent patterns without computing them. An unofficial hosted API (tts.quest via su-shiki.com) returns WAV and MP3 download URLs but is rate-limited, asynchronous and labelled low-speed.

- Applies to: All variants (pre-computation on Mac; hosted API usable from device)
- Correction: Confirmed. Details: the README calls the notation 'AquesTalk-style' and notes it differs in part from real AquesTalk notation; an underscore before a kana marks devoicing and a full-width question mark gives question intonation; accent can be corrected and resubmitted through /accent_phrases with is_kana=true. The tts.quest service needs no API key, is described as unofficial and not approved by the trademark holder, and states that audio files are eventually deleted.
- Source: <https://github.com/VOICEVOX/voicevox_engine>
- Source: <https://voicevox.su-shiki.com/su-shikiapis/ttsquest/>
- Source: <https://voicevox.hiroshiba.jp/term/>

### audio-20 · confirmed

Storage for 5,000 pre-generated phrase clips is small. Assuming a mean of 2.5 s per clip: Opus at 16 to 24 kbps is about 25 to 38 MB, MP3 at 32 kbps about 50 MB, 16 kHz 16-bit mono WAV about 400 MB, and 24 kHz 16-bit WAV (VOICEVOX native) about 600 MB. FAT cluster rounding can add up to one cluster per file (for example up to 160 MB across 5,000 files at 32 KB clusters). Any microSD card of 1 GB or more is sufficient.

- Applies to: All variants
- Correction: Arithmetic confirmed. Note that vendor Opus outputs are 24 to 32 kbps or unspecified (Azure audio-24khz-16bit-24kbps-mono-opus and audio-16khz-16bit-32kbps-mono-opus; Google OGG_OPUS at 'approximately the same bitrate' as its 32 kbps MP3), so 16 kbps means re-encoding on the Mac.
- Source: <https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioEncoding>
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech>

### audio-21 · confirmed

A 16 kHz 16-bit mono recording is 32,000 bytes per second: 5 s is about 160 KB and 10 s about 320 KB (plus a 44-byte WAV header), and base64 encoding for JSON APIs inflates that by one third to about 213 KB and 427 KB. A 10 s clip therefore equals or exceeds the whole usable heap and cannot be buffered in RAM; it must be streamed during capture or written to SD and streamed from the file.

- Applies to: All variants
- Correction: Arithmetic confirmed. The supporting evidence should be replaced: Theblackcat98/cardputer-voice is a two-commit scaffold that had not yet been built, and the 128 KB in lfurze's project is the MicroPython heap. Better evidence is claude-pocket (ADV, Arduino, PlatformIO): about 90 KB heap after Wi-Fi, mbedTLS and M5GFX, and the recording had to move from a 128 KB RAM buffer to a LittleFS file.
- Source: <https://github.com/Theblackcat98/cardputer-voice>
- Source: <https://github.com/lfurze/cardputer-voice-assistant>
- Source: <https://github.com/Nachtfux/claude-pocket/blob/main/docs/SPEC.md>
- Source: <https://github.com/lfurze/cardputer-voice-assistant/blob/main/docs/HARDWARE.md>

### audio-22 · corrected

Streaming upload of short recordings is proven on Cardputer hardware and is accepted by several cloud STT endpoints: cardputer-voice (original and ADV) POSTs 16 kHz 16-bit mono WAV with Transfer-Encoding: chunked, 12 s maximum utterance; Azure's short-audio REST API accepts raw WAV PCM 16 kHz mono or OGG Opus bodies with chunked transfer (recommended by Microsoft) up to 60 s; Deepgram accepts a raw binary body with Content-Type audio/wav; OpenAI transcription requires multipart/form-data with files up to 25 MB; Google synchronous recognition is limited to 60 s or 10 MB.

- Applies to: All variants (cardputer-voice states it supports original and ADV via M5Cardputer auto-detection)
- Correction: Service facts confirmed: Azure short audio takes WAV PCM 16 kHz mono or OGG Opus, chunked transfer is 'strongly recommended', Expect: 100-continue is required when chunking, 60 s limit (30 s for pronunciation assessment); Deepgram takes a raw body with Content-Type audio/wav, 2 GB maximum, and supports Japanese on Nova-2, Nova-3 and Flux multilingual; OpenAI is multipart/form-data up to 25 MB; Google is 60 s or 10 MB. The Cardputer proof is wrong as cited: cardputer-voice was created on 2026-09-17, has two commits, and its roadmap still lists 'do a first pio run'. Real evidence exists on ADV only: claude-pocket streams a LittleFS recording in 1 KB chunks as a multipart body to OpenAI over HTTPS (30 s cap); cardputer-claude-os streams WAV to a Cloudflare Worker while recording (MicroPython); lfurze streams length-framed PCM over TLS. None shows chunked upload to Azure, Deepgram or Google from a Cardputer, and none is on an original or v1.1 unit.
- Source: <https://github.com/Theblackcat98/cardputer-voice>
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-speech-to-text-short>
- Source: <https://developers.deepgram.com/docs/pre-recorded-audio>
- Source: <https://developers.openai.com/api/docs/guides/speech-to-text>
- Source: <https://docs.cloud.google.com/speech-to-text/docs/sync-recognize>
- Source: <https://github.com/Nachtfux/claude-pocket>

### audio-23 · corrected

Azure Speech Pronunciation Assessment supports Japanese (ja-JP) and can be called from a microcontroller through the short-audio REST API by adding a base64 JSON Pronunciation-Assessment header with the reference text; audio must be 30 s or less. For Japanese it returns accuracy, fluency and completeness scores down to phoneme level, but prosody assessment and syllable-level scores are en-US only.

- Applies to: All variants (service-side fact)
- Correction: Confirmed: ja-JP is supported, the short-audio REST API takes a Base64 JSON Pronunciation-Assessment header with ReferenceText, the limit is 30 s, and prosody and syllable groups are en-US only. Sharpening that changes the design: phoneme names are returned only for en-US (IPA and SAPI) and zh-CN (SAPI), and spoken-phoneme detection is en-US only. For other locales the doc says 'you can only get the phoneme score'. For ja-JP the response therefore holds unnamed phoneme scores, word-level accuracy with error types (omission, insertion, mispronunciation), and full-text accuracy, fluency and completeness.
- Source: <https://raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/articles/ai-services/speech-service/includes/language-support/pronunciation-assessment.md>
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment>
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-speech-to-text-short>
- Source: <https://raw.githubusercontent.com/MicrosoftDocs/azure-ai-docs/main/articles/ai-services/speech-service/how-to-pronunciation-assessment.md>

### audio-24 · corrected

I found no cloud service that gives feedback on Japanese pitch accent. Azure's prosody scoring excludes Japanese; TonePerfect offers mora-by-mora scoring and a developer API but states it does not score pitch accent; SpeechSuper's Japanese sentence demo lists overall, pronunciation, fluency, completeness, rhythm and speed scores with no mention of pitch accent. Mora-level segmental and timing feedback is therefore obtainable, pitch-accent grading is not, and a 2025 research paper describes accent-aware Japanese recognition as limited by scarce training data.

- Applies to: All variants (service-side fact)
- Correction: No service that grades Japanese pitch accent was found: confirmed (Azure prosody is en-US only; TonePerfect's FAQ says 'We don't score or grade pitch accent'; the SpeechSuper and DolphinSOE pages do not mention it; the arXiv paper is confirmed). Correction: TonePerfect's mora-by-mora Japanese scoring is a consumer app feature. Its developer API lists 7 languages (Mandarin, English, French, Spanish, German, Italian, Portuguese) and not Japanese, so it cannot be called from a device for Japanese. APIs that do cover Japanese are Azure (unnamed phoneme scores, fluency), SpeechSuper (pronunciation, fluency, completeness, rhythm, speed) and DolphinSOE (kana-level accuracy and fluency, vendor blog dated 2025-12-16). Mora-timing feedback through an API is therefore not established; only generic fluency and rhythm scores are.
- Source: <https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment>
- Source: <https://toneperfect.app/japanese>
- Source: <https://www.speechsuper.com/demo/japanese/sentence-evaluation.html>
- Source: <https://arxiv.org/abs/2509.20655>
- Source: <https://api.toneperfect.app>
- Source: <https://www.speechsuper.com/demo/japanese/word-evaluation.html>

### audio-25 · confirmed

On-device wake word and command recognition with ESP-SR is not realistic on a Cardputer, and on-device Japanese recognition is not available at all. On ESP32-S3, WakeNet9 needs about 324 KB of PSRAM, the audio front end about 740 KB, and MultiNet 2.3 to 4.1 MB of PSRAM; MultiNet supports only Chinese and English; the no-PSRAM model WakeNet9s is for ESP32-C3/C5/C6. A Japanese wake word model exists ('こんにちは ESP', WakeNet9l) but needs those PSRAM resources.

- Applies to: All variants (no PSRAM)
- Correction: Confirmed from the ESP-SR benchmark, WakeNet and MultiNet pages and README. Nuance: this rules out ESP-SR, not every form of on-device audio detection; a custom-trained keyword spotter for a few words was not researched and would not be a pronunciation judge.
- Source: <https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html>
- Source: <https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html>
- Source: <https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/wake_word_engine/README.html>
- Source: <https://github.com/espressif/esp-sr/blob/master/README.md>
- Source: <https://github.com/lichen79/xiaozhi-cardputer-adv>

### audio-26 · corrected

Reported end-to-end latency for record, upload, transcribe, LLM, synthesise, play on ESP32-S3 class devices spans roughly 4 to 20 seconds per turn: about 4 to 5 s on a Cardputer ADV over LAN with local Whisper and Piper on a Mac; 'a few seconds' for a Cardputer with a local llama.cpp server; about 20 s (down from about 54 s) for a chained Google STT, Gemini, Google TTS pipeline on an ESP32-S3 with PSRAM. STT alone for a 5 s clip is reported as 0.5 to 2 s with ElevenLabs Scribe versus about 5 s with Deepgram in one project.

- Applies to: ADV for the 4 to 5 s figure; original and ADV for cardputer-voice; other figures are from non-Cardputer ESP32/ESP32-S3 boards
- Correction: Self-reported figures confirmed for lfurze (ADV, LAN about 4.5 s; STT and TTS on the Mac, LLM is Claude Haiku), Ingeimaks (about 54 s cut to about 20 s on an ESP32-S3 with PSRAM) and KALO (5 s clip: 0.5 to 2 s with ElevenLabs, about 5 s with Deepgram). Corrections: the 'few seconds' for cardputer-voice is an expectation written in an unbuilt scaffold, not a measurement. lfurze also measured the public TLS path used from a phone hotspot (Tailscale Funnel): about 9.8 s warm and 25 to 30 s for the first request after idle. claude-pocket publishes only a budget (2 to 4 s optimised, 4 to 7 s naive, to first sound), not measurements. My inference, not a sourced figure: plan for roughly 5 to 10 s per cloud turn on a hotspot, longer on a cold connection.
- Source: <https://github.com/lfurze/cardputer-voice-assistant>
- Source: <https://github.com/Theblackcat98/cardputer-voice>
- Source: <https://github.com/Ingeimaks/ESP32-AI-Voice-Assistant>
- Source: <https://github.com/kaloprojects/KALO-ESP32-Voice-Chat-AI-Friends>
- Source: <https://github.com/d4rkmen/M5Gemini>
- Source: <https://github.com/lfurze/cardputer-voice-assistant/blob/main/docs/REMOTE-ACCESS.md>

### audio-27 · corrected

Encrypted streaming from a no-PSRAM ESP32-S3 is feasible but leaves little headroom: one project measured about 174 KB internal heap free (largest block about 104 KB) during an HTTPS exchange and about 48 KB free (minimum 36 to 40 KB) during a live Opus call, tested over a phone hotspot. On Cardputer hardware specifically, a Gemini Live speech-to-speech client runs over a single WebSocket in half-duplex. HTTPS audio streaming of MP3 to a Cardputer was not demonstrated in any source I opened (the Cardputer web radio example uses http URLs).

- Applies to: Generic ESP32-S3 without PSRAM for the heap figures; 'M5 Cardputer' (variant unspecified) for M5Gemini
- Correction: Heap figures (174 KB free and 104 KB largest block during the HTTPS offer; about 48 KB free, minimum 36 to 40 KB, during an Opus call over a phone hotspot) and the M5Gemini description are confirmed. The last sentence is wrong: the station_list.txt shipped with M5Cardputer_WebRadio contains ten https:// stream URLs (MP3 and AAC) and no http:// ones, and claude-pocket plays HTTP/HTTPS radio on an ADV with ESP32-audioI2S 3.0.7. HTTPS MP3/AAC streaming to a no-PSRAM Cardputer is therefore demonstrated, self-reported. Caveats: claude-pocket found that streaming an OpenAI TTS response straight from WiFiClientSecure to the speaker stalled on arduino-esp32 2.x (TLS 1.3 post-handshake records), so it downloads the clip to flash first and then plays; esp32-arduino-webrtc needs a custom AudioIO for PDM microphones or I2C codecs, so it does not run on any Cardputer unmodified; M5Gemini's latest commit moved it to ESP-IDF 5.5.4.
- Source: <https://github.com/akdeb/esp32-arduino-webrtc>
- Source: <https://github.com/d4rkmen/M5Gemini>
- Source: <https://github.com/cyberwisk/M5Cardputer_WebRadio>
- Source: <https://raw.githubusercontent.com/cyberwisk/M5Cardputer_WebRadio/main/M5Cardputer_WebRadio/station_list.txt>
- Source: <https://github.com/Nachtfux/claude-pocket/blob/main/docs/SPEC.md>

## Found by the fact-check

- Toolchain choice decides which audio libraries and which microphone behaviour you get (all variants). M5Stack's product pages give one PlatformIO env for original, v1.1 and ADV: platform = espressif32@6.7.0, board = esp32-s3-devkitc-1, which is Arduino core 2.0.x on ESP-IDF 4.4 (https://docs.m5stack.com/en/core/Cardputer-Adv). On that core ESP8266Audio must be 1.9.7 and ESP32-audioI2S must be 3.0.x; ESP8266Audio 2.x and ESP32-audioI2S 3.1.0 to 3.2.1 need Arduino 3.x through the community pioarduino platform (https://github.com/earlephilhower/ESP8266Audio , https://github.com/schreibfaul1/ESP32-audioI2S/releases). arduino-esp32 3.2.1 is IDF 5.4.2 and 3.3.0 is IDF 5.5.0 (https://github.com/espressif/arduino-esp32/releases/tag/3.3.0), so Arduino 3.3 and later sits in the range where the ADV microphone is reported silent. claude-pocket reports that pioarduino 3.x panicked in psramInit on the no-PSRAM StampS3A (https://github.com/Nachtfux/claude-pocket/blob/main/docs/SPEC.md).
- The ADV silent-microphone problem is unresolved and wider than the researcher stated. A comment of 2026-09-07 reproduces it on ESP-IDF 6.0.3 and 6.1 with M5Unified 0.2.21; the issue is open with no root cause (https://github.com/espressif/esp-idf/issues/18621). M5Unified's ES8311 capture fix of 2026-09-01 is registered only for the StopWatch board, not the Cardputer ADV (https://github.com/m5stack/M5Unified/pull/348). The pull request pinning UIFlow MicroPython to IDF 5.4 for the ADV is still open, so stock UIFlow may also record silence (https://github.com/m5stack/uiflow-micropython/pull/97). Design consequence: test recording on the actual unit first, and freeze a known-good toolchain before building any speaking feature.
- ADV capture has two further gotchas in M5Unified. Mic_Class.hpp documents that the ES8311 warms up for about one second after power-up, during which samples can be all zero, and the ADV mic-disable callback powers the codec down, so a speaker-to-mic switch may clip the start of an utterance (https://github.com/m5stack/M5Unified/blob/master/src/utility/Mic_Class.hpp). M5Unified sets the ADV microphone PGA to its minimum and ADC volume to 0 dB (https://github.com/m5stack/M5Unified/blob/master/src/M5Unified.inl), while a working MicroPython project raised the PGA register 0x14 to 0x1A (https://github.com/lfurze/cardputer-voice-assistant/blob/main/docs/HARDWARE.md).
- A complete device-direct cloud voice pipeline already exists for the Cardputer ADV in PlatformIO and includes a voice translator mode: Nachtfux/claude-pocket records 16 kHz PCM to a LittleFS file, streams it in 1 KB chunks to OpenAI transcription, and downloads 24 kHz PCM speech to flash before playing. Its notes give about 90 KB free heap after Wi-Fi, mbedTLS and M5GFX, a 30 s cap per turn, and 1.44 MB of flash for 30 s of reply audio (https://github.com/Nachtfux/claude-pocket , https://github.com/Nachtfux/claude-pocket/blob/main/docs/SPEC.md). Third-party and self-reported, ADV only.
- Upstream xiaozhi-esp32 has an official Cardputer ADV board definition (ES8311 in duplex through esp_codec_dev, Opus, 24 kHz, no PSRAM, keyboard Wi-Fi setup), and the project lists Japanese among its supported languages. It is a ready reference for ADV audio outside M5Unified (https://github.com/78/xiaozhi-esp32/tree/main/main/boards/m5stack/cardputer-adv). By default it talks to the xiaozhi.me service.
- Phone hotspots must offer 2.4 GHz. All Cardputers are 2.4 GHz only (https://docs.m5stack.com/en/core/Cardputer-Adv), and an ADV project found an iPhone hotspot invisible until 'Maximize Compatibility' was switched on. The same project measured about 9.8 s per voice turn over a public TLS relay when warm and 25 to 30 s for the first request after idle, against about 4.5 s on a LAN (https://github.com/lfurze/cardputer-voice-assistant/blob/main/docs/REMOTE-ACCESS.md). Third-party source.
- Pitch accent can be controlled when pre-generating clips, which matters more for a learner than voice choice. Google Cloud TTS accepts custom pronunciations in PHONETIC_ENCODING_JAPANESE_YOMIGANA with pitch marks, where ^ starts a pitch phrase and ! marks the down-step (端 = ^はし, 箸 = ^は!し, 橋 = ^はし!), Tokyo dialect only (https://docs.cloud.google.com/text-to-speech/docs/reference/rpc/google.cloud.texttospeech.v1). VOICEVOX lets you edit the accent position in its kana string and resynthesise (https://github.com/VOICEVOX/voicevox_engine). No source guarantees that either engine's automatic accent prediction is correct, so checked accent data is needed for minimal pairs.
- For pitch-accent feedback the only tool found is open source and self-hosted: itsupera/onsei (MIT, labelled experimental) aligns a learner recording with a native reference by dynamic time warping and compares pitch contours (https://github.com/itsupera/onsei). It would have to run on the Mac or a server reached over the internet; nothing equivalent runs on the device.
- Speech-to-speech services avoid the record, transcribe, synthesise chain on no-PSRAM hardware. M5Gemini runs Gemini Live on a Cardputer in half duplex (https://github.com/d4rkmen/M5Gemini), and KALO published a LIGHT build on 2026-09-15 that runs the OpenAI Realtime API over WebSockets on an ESP32 without PSRAM or SD card (https://github.com/kaloprojects/KALO-ESP32-Voice-Chat-AI-Friends). KALO targets generic ESP32 boards with I2S microphone and amplifier, not a Cardputer, and neither publishes latency figures.
- SD card format affects the clip library: the Arduino SD library does not mount exFAT, and cards of 64 GB and larger usually ship as exFAT, so use FAT32 on a card of 32 GB or less (https://github.com/bigbag/cardputer_adv_player). Third-party README, ADV, but the library is the same on all variants.

## What this means for the design

- Make pre-generated audio on microSD the core of the product. Generate all phrase, vocabulary and example-sentence clips on the Mac and copy them to SD; this works offline on trains and planes, costs roughly 25 to 60 MB for 5,000 clips in Opus or 32 kbps MP3, and avoids every PSRAM, TLS and latency problem.
- Pick the clip format by build framework. For an Arduino/PlatformIO build with M5Unified, the lowest-risk formats are 16 kHz 16-bit mono WAV streamed in chunks with playRaw (about 400 MB for 5,000 clips, zero decoder cost) or 32 kbps mono MP3 decoded with ESP8266Audio 1.9.7 or minimp3. Opus is proven mainly in ESP-IDF builds; treat Opus under Arduino as something to prototype before committing.
- Do not use Speaker.playWav for SD clips and do not plan to hold recordings in RAM. Stream in both directions: SD to playRaw in 1 to 4 KB chunks for playback, and mic to SD or mic to chunked HTTP POST for capture.
- Design every voice interaction as push-to-talk and strictly half-duplex: stop speaker, reset pins, start mic, record, stop mic, start speaker. No barge-in, no echo cancellation, no always-listening mode, no wake word.
- Do not plan any Bluetooth audio feature. For private listening in public (trains, cafes) the only option is the ADV's 3.5 mm jack; on original or v1.1 the speaker is the only output, so include a quick volume control and a text-only/silent mode.
- Avoid current ESP32-audioI2S and ESP-SR entirely. Pin library and framework versions in platformio.ini, and test the microphone on the real device on day one, because silent-mic behaviour depends on ESP-IDF version (5.4.x reported good, 5.5.x reported problematic for both PDM and ES8311 paths).
- Pre-compute pitch-accent data on the Mac. Running VOICEVOX Engine locally gives both the audio and the accent-phrase string (apostrophe = accent nucleus, slash = phrase boundary); store it with each card so the device can draw a high/low pitch pattern on the 1.14 inch screen. Treat the predicted accents as machine output that may contain errors, and consider cross-checking against a pitch-accent dictionary.
- Offer shadowing and self-comparison as the offline pronunciation feature: play the native clip, record the user to SD, play both back. This needs no network and no scoring service.
- Make cloud pronunciation scoring an optional online feature. The best-documented route is Azure short-audio REST with a Pronunciation-Assessment header and language=ja-JP: stream up to 30 s of 16 kHz WAV with chunked transfer and show accuracy, fluency and completeness. Do not promise pitch-accent or prosody grading; no service I found provides it for Japanese.
- If a conversational tutor mode is wanted, budget 4 to 20 s per turn and show progress states on screen (recording, uploading, thinking, speaking). Prefer a single relay endpoint that returns compact audio (16 kHz PCM, 32 kbps MP3 or Opus) rather than chaining three separate HTTPS calls from the device; each TLS session costs tens of KB of heap.
- Keep API keys off the SD card in plain text where possible and consider a small personal relay server so the device holds one token; this also lets the heavy work (STT, LLM, TTS, transcoding to a Cardputer-friendly format) move off the device.
- Treat on-device TTS as optional. AquesTalk ESP32 fits technically (21 KB RAM, dictionary on SD) and would let the device speak arbitrary text offline, but it is 8 kHz robotic speech, the free build is unusable for learning (na/ma rows become nu), and buying the 1,980 yen licence requires a Japanese postal address. It is a poor pronunciation model for a learner; use it, if at all, only for reading out unknown text.
- Include credits and disclosures in an About screen if VOICEVOX voices (credit such as VOICEVOX:character name) or OpenAI voices (AI-generated disclosure) are used, even for personal use.
- Organise the 5,000 clips in sharded folders or a single pack file with an index rather than one flat FAT directory, to keep file lookup fast and reduce cluster waste.

## Not settled

- How loud and how intelligible is speech from the built-in speaker in a noisy street or station? No measured SPL or intelligibility data was found for any variant; the only qualitative remark is one review calling the original's speaker 'quite tinny'.
- Real-world microphone quality and noise floor for language-learning use: SPM1423 PDM mic on original/v1.1 versus the ADV's 65 dB SNR MEMS mic through ES8311. No comparative recordings or measurements were found, and it is unknown how well cloud STT handles Cardputer recordings of learner Japanese.
- Can the ADV do true full-duplex (simultaneous record and play) with a custom single-port I2S driver? The shared-clock ES8311 wiring suggests yes, but no source demonstrates it and M5Unified does not support it.
- Which Arduino core and ESP-IDF version will the user's PlatformIO setup actually use (official platform with Arduino 2.x on IDF 4.4, or a community platform with Arduino 3.x on IDF 5.x)? This decides whether ESP8266Audio 1.9.7 or 2.x applies and whether the silent-mic regressions are hit. Sources conflict on which M5Stack board package version maps to which IDF.
- Does sanoTTS-jp run on an ESP32-S3 without PSRAM, and with Wi-Fi active? Published figures come from an M5Stack CoreS3; the project is only weeks old. Its model licence restrictions were not read in full.
- Exact AquesTalk phonetic notation (accent and pause symbols) and whether accent can be fully controlled per phrase: the specification PDF could not be parsed. AquesTalk pico official details (price, interface, licence) are unverified because the product page URL I tried returned 404.
- Which last version of ESP32-audioI2S truly works without PSRAM (2.0.6 versus 3.0.11g)? Sources disagree. This matters only if that library is wanted despite the recommendation to avoid it.
- Is HTTPS (TLS) audio streaming of MP3 or Opus to a Cardputer stable over a phone hotspot? Heap figures from a generic no-PSRAM S3 suggest it is feasible, but no Cardputer project demonstrating HTTPS media streaming was found.
- Comparative Japanese voice quality across Google Chirp 3 HD, Azure neural, OpenAI, ElevenLabs, Polly and VOICEVOX, in particular pitch-accent correctness on isolated words and short phrases. No neutral evaluation was found; a listening test is needed.
- Storage and redistribution terms for Azure TTS output and the exact ElevenLabs free-tier terms were not read from primary pages. OpenAI's output-ownership terms were not covered on the page opened.
- What does SpeechSuper's 'tone score' on its Japanese kana and kanji assessment pages measure, and does Deepgram support Japanese on its current models? Neither was confirmed from an opened page.
- Whether a newer Cardputer variant with PSRAM or a different audio path exists beyond original, v1.1 and ADV. None was found, but the search was not exhaustive.
- Licence terms and Arduino/PlatformIO usability of Espressif's esp_audio_codec (the source of the Opus and AMR memory figures) were not stated on the page opened.
