# Cloud AI access from the device

Facet: LLM and cloud AI access from a Cardputer. Calling a cloud LLM directly from every documented Cardputer variant is proven feasible by existing open-source firmware, but all variants documented by M5Stack (original K132, v1.1, ADV) use the ESP32-S3FN8 with 8 MB flash and no PSRAM listed, so RAM (roughly 170 KB free after Wi-Fi and a display canvas, per one project's write-up) is the binding constraint, not CPU or the API. I opened and confirmed six relevant repositories. Two of them read source-level: CardputerOS calls api.anthropic.com/v1/messages directly (non-streaming, setInsecure, whole body buffered, new TLS connection per request), and GeminiCardputerADV_Japanese does the same for Gemini with the API key in a plaintext JSON on the SD card. A third (dakshaymehta/cardputer-claude-os) already implements the relay pattern: a Cloudflare Worker holds the real keys, does Whisper STT and calls Claude Haiku, and the device only holds a shared device secret. No project I opened publishes measured end-to-end latency; the only numbers found are a 2-5 s blocking STT call (ClawPuter doc) and a 3.1-5.9 s TLS handshake in one unreproduced ESP-IDF issue. From official Anthropic docs opened today: endpoint POST https://api.anthropic.com/v1/messages with x-api-key, anthropic-version: 2023-06-01 and content-type headers; SSE streaming with named events; the small fast model is Claude Haiku 4.5 (claude-haiku-4-5-20251001, $1/$5 per MTok), which is Active but carries a tentative retirement date of 'not sooner than October 15, 2026', so the model id must be configurable and not baked into firmware. Recommended pattern: offline-first content pre-generated on the Mac onto the SD card, plus an optional personal relay (Cloudflare Worker) holding a workspace-scoped Anthropic key with a monthly workspace spend limit, its own daily counter, and a revocable device token; avoid ESP32 flash encryption on a hobby device. Not settled: real latency over a Japanese phone hotspot, actual free heap during a TLS session on each variant, and whether any newer Cardputer variant with PSRAM exists (none found in M5 docs).

Fact-check: done.

## Statements

### llm-01 · corrected

All three Cardputer variants documented by M5Stack (original Cardputer, Cardputer v1.1, Cardputer-Adv) are built on the ESP32-S3FN8 with 8 MB flash and a 240x135 ST7789V2 screen, and none of the M5 docs pages lists any PSRAM. Community firmware authors state outright that the device has no PSRAM.

- Applies to: Cardputer (K132), Cardputer v1.1, Cardputer-Adv. No newer variant was found in M5 docs.
- Correction: Confirmed for the three ESP32-S3 models. M5 docs list ESP32-S3FN8, 8MB flash and ST7789V2 1.14 inch 240x135 for Cardputer (SKU K132, Stamp-S3), Cardputer v1.1 (K132-V11, Stamp-S3A) and Cardputer-Adv (K132-Adv, Stamp-S3A). I fetched the raw HTML of all three pages and the string 'PSRAM' occurs zero times. Espressif's datasheet lists ESP32-S3FN8 with 8 MB in-package flash and no in-package PSRAM, and upstream XiaoZhi's cardputer-adv board config sets CONFIG_SPIRAM=n. Two errors. (1) A newer Cardputer-family product IS in M5 docs: CardputerZero (SKU C154, Lite C155, announced 2026-05-26) with a Raspberry Pi CM0, quad Cortex-A53, 512 MB RAM, 1.9 inch 320x170 screen, 46 keys, running Linux. None of the ESP32 constraints apply to it. (2) Community authors are not unanimous: CardputerOS's roadmap describes the ADV as a 'different SoC with PSRAM', which contradicts M5 docs and should be disregarded.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/StampS3>
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/docs/esp32-voice-chat-lessons.md>

### llm-02 · confirmed

One project's write-up gives a working heap budget for the original Cardputer: about 328 KB total SRAM, about 90 KB held by the Wi-Fi stack once connected, about 65 KB for a full-screen 240x135 RGB565 canvas, leaving about 173 KB free; a 5 second 16 kHz 16-bit voice buffer costs 160 KB and leaves about 13 KB, which is too little for HTTP and JSON work.

- Applies to: Original Cardputer (M5StampS3). Likely the same order of magnitude on v1.1 and ADV since the SoC is the same, but not measured there.
- Correction: Figures confirmed verbatim in section 1 of the document (one project's report, not a vendor spec). Three sharpenings. (a) 328 KB is the project's heap figure; the ESP32-S3 has 512 KB of on-chip SRAM per Espressif. (b) The budget was measured with plain HTTP: ClawPuter uses WiFiClient with no TLS, so a TLS session (about 45 KB per CardputerOS's own notes) still has to be subtracted from the 173 KB. (c) The 'allocate on demand, free after upload' fix quoted in the evidence was reversed later in the same document (pitfall 7). Freeing and re-allocating fragmented the heap (largest free block 94 KB with 187 KB free) and the second voice turn failed. The final design allocates a 96 KB, 3 second buffer once at startup and never frees it.
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/docs/esp32-voice-chat-lessons.md>
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/src/ai_client.cpp>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/docs/architecture.md>

### llm-03 · corrected

Espressif documents about 42 KB of heap per TLS connection with default mbedTLS settings and about 22 KB with dynamic TX/RX buffers enabled. The Arduino core's prebuilt libraries enable dynamic buffers (CONFIG_MBEDTLS_DYNAMIC_BUFFER=y), so an Arduino/PlatformIO build should sit near the lower figure without any rebuild of the SDK.

- Applies to: Any ESP32-S3 Arduino build, so all Cardputer variants. The numbers are from Espressif's HTTPS example, not measured on a Cardputer.
- Correction: Espressif's figures are confirmed: 42196 B default, 42120 B, 38533 B, and 22013 B with dynamic TX/RX buffer, from the https_request example with server validation (the stable page now documents ESP-IDF v6.1). The second sentence is wrong and the conclusion reverses. The lib-builder defconfig does contain CONFIG_MBEDTLS_DYNAMIC_BUFFER=y, but the same file sets CONFIG_MBEDTLS_SSL_PROTO_DTLS=y, and ESP-IDF's Kconfig (v4.4 to v5.5) declares MBEDTLS_DYNAMIC_BUFFER as 'depends on ... !MBEDTLS_SSL_PROTO_DTLS', so the option is silently dropped. The shipped ESP32-S3 sdkconfig in Arduino core 2.0.16 and 2.0.17, in esp32-arduino-libs idf-release/v5.1, and in the current IDF 5.5.5 libs archive has no MBEDTLS_DYNAMIC_BUFFER entry, has CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=16384 with asymmetric content length not set, and has TLS 1.3 not enabled. A stock Arduino or PlatformIO build therefore uses fixed 16 KB receive and 16 KB transmit buffers. Expect at or above the 42 KB figure, not 22 KB (ESP-IDF's own default already assumes a 4 KB transmit buffer, which its Kconfig says 'saves 12KB'). CardputerOS's notes budget '~45 KB' per TLS handshake on an original Cardputer. Reaching about 22 KB needs a custom SDK build, as M5Gemini does under ESP-IDF.
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html>
- Source: <https://raw.githubusercontent.com/espressif/esp32-arduino-lib-builder/master/configs/defconfig.common>
- Source: <https://raw.githubusercontent.com/espressif/esp32-arduino-lib-builder/release/v5.1/configs/defconfig.common>
- Source: <https://raw.githubusercontent.com/espressif/esp32-arduino-lib-builder/release/v4.4/configs/defconfig.common>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/v5.5/components/mbedtls/Kconfig>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.17/tools/sdk/esp32s3/sdkconfig>

### llm-04 · confirmed

CardputerOS (urazalievf/cardputer, MIT, PlatformIO + Arduino, ArduinoJson 7) calls the Claude Messages API directly from the device. It is non-streaming, skips certificate validation, buffers the whole response in a String before parsing, opens a new TLS connection for every request, and stores API keys in NVS.

- Applies to: Original Cardputer / StampS3 (board = m5stack-stamps3). Not confirmed on ADV.
- Correction: Confirmed from source. Sharpening: direct cloud calls are the fallback path, and the default provider is a Mac daemon on the LAN. The model id is only a default and can be overridden in NVS (key m_anthropic) without reflashing. The roadmap lists Cardputer ADV as not yet supported, and lists streaming, encrypted NVS and a pinned root CA as future work. The project's notes budget about 45 KB of heap per TLS handshake and a 16 KB task stack. It pins pioarduino 55.03.32, which is Arduino core 3.3.2.
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/src/kernel/ai.cpp>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/platformio.ini>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/src/kernel/store.cpp>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/LICENSE>

### llm-05 · corrected

GeminiCardputerADV_Japanese is an existing Japanese-capable LLM chat firmware for the Cardputer ADV: romaji-to-hiragana typing with no kanji conversion, the built-in lgfxJapanGothic_12 font for display, Gemini over HTTPS without certificate validation, API key and Wi-Fi credentials in a plaintext JSON file on the SD card, and history limited to the last 8 messages.

- Applies to: Cardputer-Adv (stated target). Not stated for original or v1.1.
- Correction: Every listed behaviour is confirmed in the README and src/main.cpp, with three caveats. (1) The README states the bundled BIN has not been verified on real hardware ('実機での動作確認は未実施'), so treat the firmware as untested. (2) There is no licence file or licence statement (LICENSE, LICENSE.md, LICENSE.txt and COPYING all return 404), so no reuse rights are granted by default. (3) History is trimmed to 8 entries in memory and in the SD file, not only on screen, and every request enables Gemini's google_search tool. It builds with espressif32@6.7.0 and the M5Cardputer library pinned to a git commit.
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/README.md>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/platformio.ini>

### llm-06 · confirmed

dakshaymehta/cardputer-claude-os already implements the personal-relay pattern: a Cloudflare Worker holds the Anthropic and OpenAI keys as Wrangler secrets, accepts audio (/ask) or text (/ask-text) from the device, runs OpenAI Whisper (whisper-1) for speech-to-text, calls Claude Haiku for the reply, and keeps per-device conversation memory in Workers KV (last 8 messages, 24 hour TTL). The device authenticates with a shared secret in an x-device-secret header.

- Applies to: Targets Cardputer-Adv; README says the original Cardputer works for everything except the voice app. Device code is MicroPython, not Arduino C++.
- Correction: Confirmed. Sharpening: worker.js hard-codes CHAT_MODEL 'claude-haiku-4-5-20251001' with max_tokens 250 and sends no language hint to whisper-1. The device records a fixed 6 second clip at 16 kHz to a file and uploads it in 2 KB chunks. The browser path accepts the same secret as a ?token= query parameter, and history is keyed by the DEVICE_SECRET itself. The MicroPython client calls ssl.wrap_socket(s, server_hostname=host) with no cert_reqs or cadata, and MicroPython's default is CERT_NONE, so the device does not validate the Worker's certificate and the shared secret is exposed to an on-path attacker. The code comments report about 35 KB peak during upload and about 30 KB held by the BLE stack.
- Source: <https://github.com/dakshaymehta/cardputer-claude-os>
- Source: <https://github.com/dakshaymehta/cardputer-claude-os/blob/main/worker/README.md>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/README.md>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/worker/README.md>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/worker/src/worker.js>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/worker/wrangler.toml>

### llm-07 · corrected

ClawPuter demonstrates token-by-token SSE streaming on a no-PSRAM Cardputer, but its intelligence sits behind a gateway and an STT proxy running on a computer on the same LAN, so it does not work for a traveller as published. Its engineering notes record that reading a chunked SSE stream line-by-line with readStringUntil breaks when a data line spans a chunk boundary, and that a byte-level chunk decoder feeding a fixed line buffer fixed it.

- Applies to: Original Cardputer (SPM1423 PDM microphone is named). MIT licence, PlatformIO.
- Correction: Streaming is demonstrated, but over plain HTTP. ai_client.cpp uses WiFiClient with no TLS to POST /v1/chat/completions on the OpenClaw gateway, and parses OpenAI-style 'data:' lines ending in [DONE], not Anthropic's named events. It shows that a chunk-decoding SSE parser fits in RAM, not that TLS plus streaming fits. 'Does not work for a traveller' is too strong: the README says the gateway runs 'on your Mac or VPS' and documents a phone-hotspot fallback with a second gateway address. A traveller with the Mac on the same hotspot can use it. A VPS gateway would work but would carry the bearer token and the chat in clear text. The engineering notes are confirmed: the chunk-boundary failure from the third turn, the CS_SIZE/CS_DATA/CS_TRAILER decoder, 500 to 800 bytes lost per turn, and the 2 to 5 second STT call. Licence MIT, PlatformIO, board m5stack-stamps3.
- Source: <https://github.com/bryant24hao/ClawPuter>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/docs/esp32-voice-chat-lessons.md>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/README.md>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/src/ai_client.cpp>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/src/voice_input.cpp>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/platformio.ini>

### llm-08 · confirmed

M5Gemini (d4rkmen/M5Gemini) runs real-time speech-to-speech with the Gemini Live API from a Cardputer over a single WebSocket, half-duplex with server-side voice activity detection. It is built on ESP-IDF 5.4 or later (not Arduino), stores the API key in NVS with optional import from an SD card config file, and is GPL licensed.

- Applies to: README says 'M5 Cardputer' without naming a variant; which of original / v1.1 / ADV are supported is not stated.
- Correction: Confirmed from the README. Sharpening from the repository: main/hal/board.h defines CARDPUTER (original, IOMatrix keyboard) and CARDPUTER_ADV (TCA8418) with auto-detect, and there is an es8311 driver, so both are targeted; v1.1 is not named. The committed sdkconfig has CONFIG_SPIRAM unset, CONFIG_MBEDTLS_DYNAMIC_BUFFER=y with 8192 and 4096 byte content lengths, and CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY=y. The WebSocket config sets no CA, so the server certificate is not verified, and the API key travels in the URL query string. The README names the GPL without a version and the repository has no LICENSE file.
- Source: <https://github.com/d4rkmen/M5Gemini>
- Source: <https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/README.md>
- Source: <https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/sdkconfig>
- Source: <https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/main/hal/board.h>
- Source: <https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/main/app/s2s_client.cpp>
- Source: <https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/CHANGELOG.md>

### llm-09 · confirmed

Upstream XiaoZhi (78/xiaozhi-esp32, MIT) includes a board definition for the Cardputer ADV only (main/boards/m5stack/cardputer-adv); there is no upstream board for the original Cardputer or v1.1. XiaoZhi is a thin voice client: ASR, LLM and TTS all run server-side, the default server is xiaozhi.me, and the device streams Opus audio over WebSocket or MQTT+UDP.

- Applies to: Cardputer-Adv upstream. A separate community fork (Muhammad-Yunus/xiaozhi-esp32-cardputer-v1.1, forked from tkpdx01/xiaozhi-esp32-adv) targets v1.1 by name; its README does not describe what was changed.
- Correction: Confirmed. Sharpening: upstream's cardputer-adv config.json sets CONFIG_SPIRAM=n and an 8 MB partition table. The Muhammad-Yunus fork does contain a board directory, main/boards/m5stack-cardputer-v11, with a config.json that sets CONFIG_SPIRAM=n, an hc138_keyboard driver and a Wi-Fi config UI, although its README does not describe it. XiaoZhi also lists on-device wake word (ESP-SR) as a feature, so it is not purely server-side on boards that support it.
- Source: <https://github.com/78/xiaozhi-esp32>
- Source: <https://github.com/78/xiaozhi-esp32/tree/main/main/boards/m5stack>
- Source: <https://github.com/78/xiaozhi-esp32/tree/main/main/boards/m5stack/cardputer-adv>
- Source: <https://github.com/Muhammad-Yunus/xiaozhi-esp32-cardputer-v1.1>
- Source: <https://github.com/78/xiaozhi-esp32/tree/main/main/boards>
- Source: <https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/boards/m5stack/cardputer-adv/README.md>

### llm-10 · confirmed

AI Stack-chan (robo8080/AI_StackChan2, MIT, PlatformIO) targets the M5Stack Core2, not the Cardputer. It chains a cloud STT (Google Cloud STT or OpenAI Whisper), ChatGPT and Web VOICEVOX Japanese TTS. It is a reference for a Japanese voice pipeline but not a drop-in for Cardputer hardware.

- Applies to: M5Stack Core2 (README says CoreS3 did not work at the time of writing). Not any Cardputer variant.
- Correction: Confirmed. Sharpening: the CoreS3 warning is struck through in the current README, and platformio.ini has a CoreS3 environment with -DBOARD_HAS_PSRAM. The source is reachable under M5Unified_AI_StackChan/src. It verifies servers with pinned root CAs through setCACert (rootCACertificate.h, rootCAgoogle.h, WebVoiceVoxRootCA.h) and stores API keys in NVS, imported from /apikey.txt on the SD card. It is the one project in this set that validates TLS.
- Source: <https://github.com/robo8080/AI_StackChan2>
- Source: <https://raw.githubusercontent.com/robo8080/AI_StackChan2/main/README.md>
- Source: <https://raw.githubusercontent.com/robo8080/AI_StackChan2/main/LICENSE>
- Source: <https://raw.githubusercontent.com/robo8080/AI_StackChan2/main/M5Unified_AI_StackChan/platformio.ini>
- Source: <https://raw.githubusercontent.com/robo8080/AI_StackChan2/main/M5Unified_AI_StackChan/src/main.cpp>
- Source: <https://github.com/robo8080/AI_StackChan2/tree/main/M5Unified_AI_StackChan/src>

### llm-11 · confirmed

The Claude Messages API is POST https://api.anthropic.com/v1/messages with three headers: x-api-key, anthropic-version: 2023-06-01, and content-type: application/json. The required body fields are model, max_tokens and messages. Errors always come back as JSON with a top-level error object containing type and message.

- Applies to: All variants (protocol-level).
- Correction: Confirmed. Sharpening: the Authentication page now documents 'Authorization: Bearer <key>' as the way to send a key and calls x-api-key a legacy header that is still supported; official curl examples still use x-api-key. The error list also includes 409 conflict_error. Observed today without a key: even a 401 error body arrives with Transfer-Encoding: chunked under HTTP/1.1.
- Source: <https://platform.claude.com/docs/en/api/messages>
- Source: <https://platform.claude.com/docs/en/api/versioning>
- Source: <https://platform.claude.com/docs/en/api/errors>
- Source: <https://platform.claude.com/docs/en/manage-claude/workspaces>
- Source: <https://platform.claude.com/docs/en/manage-claude/authentication>
- Source: <https://api.anthropic.com/v1/messages>

### llm-12 · confirmed

Streaming is enabled with "stream": true and uses server-sent events where every event is named. The flow is message_start, then for each content block content_block_start, one or more content_block_delta, content_block_stop, then message_delta and message_stop. ping events can appear anywhere, an error event can arrive after the HTTP 200, there is no 'data: [DONE]' terminator, and clients must ignore unknown event types.

- Applies to: All variants (protocol-level).
- Correction: Confirmed. Sharpening: a parser should also test delta.type == 'text_delta', because other delta types exist (input_json_delta, thinking_delta, signature_delta), and should read stop_reason from message_delta to detect a reply cut off by max_tokens. The docs say code 'should handle unknown event types gracefully'.
- Source: <https://platform.claude.com/docs/en/build-with-claude/streaming>
- Source: <https://platform.claude.com/docs/en/api/versioning>
- Source: <https://platform.claude.com/docs/en/api/errors>

### llm-13 · confirmed

Anthropic positions Claude Haiku 4.5 as the small fast model: API ID claude-haiku-4-5-20251001 (alias claude-haiku-4-5), described as 'The fastest model with near-frontier intelligence', comparative latency 'Fastest', priced at $1 per million input tokens and $5 per million output tokens, 200K context, 64K max output.

- Applies to: All variants (provider-level).
- Source: <https://platform.claude.com/docs/en/about-claude/models/overview>
- Source: <https://platform.claude.com/docs/en/about-claude/models/choosing-a-model>
- Source: <https://platform.claude.com/docs/en/models/haiku-4-5/overview>
- Source: <https://platform.claude.com/docs/en/about-claude/pricing>

### llm-14 · confirmed

Claude Haiku 4.5 is listed as Active but with a tentative retirement date of 'Not sooner than October 15, 2026', which is 18 days from today. Anthropic commits to at least 60 days' notice before retiring a publicly released model and the model is not marked deprecated, so a retirement before late November 2026 would contradict that policy, but the model id could still stop working during or soon after a trip.

- Applies to: All variants (provider-level). Affects any firmware with a hard-coded model id, including CardputerOS's default.
- Correction: Confirmed. The Haiku 4.5 model page shows status 'Active (latest)'. The date is a floor, not a schedule, and no deprecation has been announced. Past Haiku retirements gave about 60 days' notice (Haiku 3.5 from 2025-12-19 to 2026-02-19, Haiku 3 from 2026-02-19 to 2026-04-20). If it were retired, the fallback Claude Sonnet 5 costs $2 and $10 per million tokens and uses the newer tokenizer, which the pricing page says produces approximately 30% more tokens for the same text. The cardputer-claude-os relay hard-codes the same dated id, but a relay can be changed without reflashing the device.
- Source: <https://platform.claude.com/docs/en/about-claude/model-deprecations>
- Source: <https://platform.claude.com/docs/en/about-claude/models/overview>
- Source: <https://platform.claude.com/docs/en/models/haiku-4-5/overview>
- Source: <https://platform.claude.com/docs/en/about-claude/pricing>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/worker/src/worker.js>

### llm-15 · corrected

The Arduino core offers three server-verification modes for TLS: setCACert (one pinned root), setCACertBundle (Mozilla root bundle) and setInsecure (no verification). As observed today, api.anthropic.com presents a 90-day leaf certificate issued by Google Trust Services WE1 chaining to GTS Root R4, so pinning must target a root, never the leaf. Both Cardputer LLM firmwares whose source I read use setInsecure.

- Applies to: All variants. The certificate chain is an observation on 2026-09-27 and is not documented or guaranteed by Anthropic.
- Correction: The certificate observation is confirmed by my own handshake on 2026-09-27: leaf CN=api.anthropic.com from Google Trust Services WE1, valid 2026-09-21 to 2026-12-20; WE1 from GTS Root R4; the served GTS Root R4 is cross-signed by GlobalSign Root CA until 2028-01-28; TLS 1.2 and 1.3 are both accepted. Both firmwares use setInsecure. The list of modes is incomplete. The class also has loadCACert(Stream&, size) to load a CA from a file, setCACert passes its buffer to mbedtls_x509_crt_parse so several PEM roots can be pinned together, and Arduino core 3.3.12 and 4.0.0-RC1 add useBuiltinCACertBundle(), which attaches the Mozilla bundle already compiled into the core libraries. That call is absent in 3.3.10 and earlier and in 2.0.x. Pin the self-signed GTS Root R4 (valid to 2036-06-22, ECDSA P-384, 525 bytes DER), not the GlobalSign cross-certificate. The host is served through Cloudflare, which rotates edge certificates, so pinning a single root can break if the issuing CA changes; pin a few roots or use the bundle.
- Source: <https://github.com/espressif/arduino-esp32/blob/master/libraries/NetworkClientSecure/README.md>
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_crt_bundle.html>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/src/kernel/ai.cpp>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/NetworkClientSecure/README.md>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/NetworkClientSecure/src/NetworkClientSecure.h>

### llm-16 · confirmed

ArduinoJson 7 supports three memory-saving patterns relevant here: a filter document (DeserializationOption::Filter) that discards unwanted fields, deserialising directly from a Stream instead of a buffered String, and parsing a large array one element at a time using find/findUntil. Arduino HTTPClient's getStream() does not decode chunked transfer encoding, so stream parsing needs either http.useHTTP10(true) or a chunk decoder such as StreamUtils' ChunkDecodingStream.

- Applies to: All variants using the Arduino framework.
- Correction: Confirmed. Sharpening from a keyless test today: api.anthropic.com returns Transfer-Encoding: chunked under HTTP/1.1 even for a short 401 JSON body, and answers an HTTP/1.0 request with Connection: close and no chunking. Chunk handling is therefore needed for non-streaming replies too when reading the stream directly. Whether a streamed reply behaves the same under HTTP/1.0 is untested.
- Source: <https://arduinojson.org/v7/how-to/deserialize-a-very-large-document/>
- Source: <https://arduinojson.org/v7/api/json/deserializejson/>
- Source: <https://arduinojson.org/v7/how-to/use-arduinojson-with-httpclient/>
- Source: <https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/docs/esp32-voice-chat-lessons.md>
- Source: <https://api.anthropic.com/v1/messages>

### llm-17 · corrected

Arduino HTTPClient supports connection reuse (setReuse) and has a 4096-byte receive buffer, a 1460-byte transmit buffer and a 5000 ms default TCP timeout. The Cardputer firmwares I read do not reuse connections, so each request pays a full TLS handshake. The only handshake timings I found for an ESP32-S3 are 3.1 s and 5.9 s in a single ESP-IDF issue that Espressif closed as 'Cannot Reproduce', so the typical cost on a Cardputer is unmeasured.

- Applies to: All variants using Arduino HTTPClient. Handshake timings are from an ESP32-S3-Korvo-2 board, not a Cardputer.
- Correction: The constants are right for Arduino core 3.x (HTTP_TCP_RX_BUFFER_SIZE 4096, HTTP_TCP_TX_BUFFER_SIZE 1460, 5000 ms default, reuse on by default). Core 2.0.17, which official PlatformIO espressif32 6.x builds use, has a single HTTP_TCP_BUFFER_SIZE of 1460. Issue 10523 is quoted correctly: 5.86 s and 3.1 s on an ESP32-S3-Korvo-2 with IDF 4.4.2, closed 'Cannot Reproduce'. It is not the only data point. ESP-IDF pull request 19027 reports a TLS 1.2 ECDHE-ECDSA handshake to api.github.com improving from 4063 ms to 2746-2759 ms, measured mainly on a classic ESP32-D0WD-V3 with ESP32-S3 as secondary validation. api.anthropic.com also negotiates ECDHE-ECDSA. Treating 3 to 6 seconds per fresh TLS connection as a planning assumption is my inference from these two reports; it is still unmeasured on a Cardputer. Stock Arduino libraries leave CONFIG_ESP_TLS_CLIENT_SESSION_TICKETS unset.
- Source: <https://github.com/espressif/arduino-esp32/blob/master/libraries/HTTPClient/src/HTTPClient.h>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/src/kernel/ai.cpp>
- Source: <https://github.com/espressif/esp-idf/issues/10523>
- Source: <https://platform.claude.com/docs/en/api/errors>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/HTTPClient/src/HTTPClient.h>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/3.3.2/libraries/HTTPClient/src/HTTPClient.h>

### llm-18 · confirmed

The practical ceiling on request and response size is device heap, not the API: the Messages API accepts requests up to 32 MB, while existing Cardputer firmware keeps replies short (600 output tokens) and history short (last 8 messages). A non-streaming client holds the raw response String and the parsed JsonDocument at the same time, so peak RAM is roughly twice the response size on top of the TLS session.

- Applies to: All variants (no PSRAM). The 'roughly twice' figure is my reasoning from the code pattern, not a measurement.
- Correction: Confirmed: 32 MB Messages API limit, 600 tokens and 8 messages in the Gemini firmware, 8 messages in the relay, reserve(320) in ClawPuter. Sharpening: the relay caps replies at max_tokens 250 and its device code reads at most 8 KB of response. CardputerOS makes a third copy when it extracts the text into a String. A 12 px font gives 20 full-width columns, but fewer than 11 rows remain once a header and input bar are drawn (the Gemini firmware reserves an 18 px header).
- Source: <https://platform.claude.com/docs/en/api/errors>
- Source: <https://raw.githubusercontent.com/Happymc2525/GeminiCardputerADV_Japanese/master/src/main.cpp>
- Source: <https://github.com/dakshaymehta/cardputer-claude-os>
- Source: <https://raw.githubusercontent.com/urazalievf/cardputer/main/src/kernel/ai.cpp>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/worker/src/worker.js>
- Source: <https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/buddy/device/apps/push_to_claude.py>

### llm-19 · confirmed

Neither on-device storage option protects a secret from someone holding a lost Cardputer: an SD card file is readable in any card reader, and NVS is not encrypted unless explicitly enabled. Making NVS secure requires flash encryption or an HMAC key, both of which burn one-time eFuses; in release mode plaintext flashing over USB is permanently disabled, which is a poor fit for a hobby device that is reflashed often.

- Applies to: All variants (ESP32-S3).
- Correction: Confirmed. Sharpening: the stock Arduino ESP32-S3 libraries ship with CONFIG_NVS_ENCRYPTION and CONFIG_SECURE_FLASH_ENC_ENABLED not set, so either scheme needs a custom SDK build on top of the eFuse burn. CardputerOS's roadmap confirms its keys are 'plaintext in flash today'. Encryption at rest also does not stop someone using a found, working device to spend the key, which is why a revocable or expiring credential matters more.
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/storage/nvs_encryption.html>
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/security/flash-encryption.html>
- Source: <https://github.com/Happymc2525/GeminiCardputerADV_Japanese>
- Source: <https://github.com/urazalievf/cardputer>
- Source: <https://github.com/d4rkmen/M5Gemini>
- Source: <https://github.com/espressif/esp32-arduino-lib-builder/releases/download/idf-release_v5.5/esp32-arduino-libs-idf-release_v5.5-b774170f-v3.zip>

### llm-20 · confirmed

Anthropic provides account-side damage limits: an API key can be scoped to a single workspace, and each non-default workspace can have its own monthly spend limit and per-minute rate limits. These limits are monthly, not daily, and cannot be set on the Default Workspace, so a dedicated workspace must be created for the gadget. Archiving that workspace archives all its keys within seconds.

- Applies to: All variants (provider-level).
- Correction: Confirmed. Sharpening: keys can also be created with an expiration (presets of 3 hours, 1 day, 7 days or 30 days, or a custom duration; fixed at creation; expired keys return 401 authentication_error), and a single key can be disabled (reversible) or deleted in the Console. Revoking the gadget's key therefore does not require archiving the workspace. Only organisation admins can create workspaces. New organisations may start in an Evaluation tier with limits below the published Start tier.
- Source: <https://platform.claude.com/docs/en/manage-claude/workspaces>
- Source: <https://platform.claude.com/docs/en/api/rate-limits>
- Source: <https://platform.claude.com/docs/en/api/errors>
- Source: <https://platform.claude.com/docs/en/manage-claude/authentication>

### llm-21 · confirmed

A Cloudflare Worker is a workable personal relay on the free plan: secrets are write-only after being set, the free plan allows 100,000 requests per day with 10 ms CPU time and 50 subrequests per request, and wall-clock duration is not limited while the client stays connected. A true daily cap cannot use Cloudflare's rate-limiting binding, which only supports 10 or 60 second windows and is documented as not an accurate accounting system; it needs a counter in KV or a Durable Object.

- Applies to: All variants (relay-side).
- Correction: Confirmed. Sharpening: CPU time excludes time spent waiting on fetch(), KV or database calls, and Cloudflare says the average Worker uses approximately 2.2 ms per request; exceeding the limit returns Error 1102. Workers KV on the free plan allows 1,000 writes per day and 1 write per second to the same key, which constrains a KV counter plus per-turn history. SQLite-backed Durable Objects are available on the free plan (100,000 requests per day) and are the better home for an exact daily cap. The rate-limit binding also counts separately per Cloudflare location.
- Source: <https://developers.cloudflare.com/workers/platform/limits/>
- Source: <https://developers.cloudflare.com/workers/configuration/secrets/>
- Source: <https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/>
- Source: <https://github.com/dakshaymehta/cardputer-claude-os/blob/main/worker/README.md>
- Source: <https://developers.cloudflare.com/kv/platform/limits/>
- Source: <https://developers.cloudflare.com/durable-objects/platform/pricing/>

### llm-22 · confirmed

Speech-to-text can run in the same relay without a second vendor key: Cloudflare Workers AI offers @cf/openai/whisper-large-v3-turbo at about $0.0005 per audio minute with a language parameter, and every account gets 10,000 Neurons per day free (that model costs 46.63 neurons per audio minute). Workers AI also lists text-to-speech models, but I did not verify that any of them produces Japanese speech.

- Applies to: All variants for typed input. Voice capture quality differs: original and v1.1 use an SPM1423 PDM microphone, ADV uses an ES8311 codec with a 65 dB SNR MEMS microphone.
- Correction: Confirmed: $0.000513 per audio minute, 46.63 neurons per audio minute, 10,000 neurons per day free, $0.011 per 1,000 neurons, and a language parameter. Sharpening: the pricing page lists no text-to-speech model described as Japanese. Aura-2 is listed only as -en and -es, and the MeloTTS page documents a 'lang' parameter with only 'en' and 'fr' as examples, so Japanese speech output on Workers AI remains unverified. The model page states no audio size or duration limit.
- Source: <https://developers.cloudflare.com/workers-ai/models/whisper-large-v3-turbo/>
- Source: <https://developers.cloudflare.com/workers-ai/platform/pricing/>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://developers.cloudflare.com/workers-ai/models/melotts/>

### llm-23 · confirmed

Pre-generating lesson content on the Mac is the only architecture with no dependency on connectivity, heap headroom, key safety or model availability at the moment of use, and Anthropic's Message Batches API halves the token price for that kind of offline bulk generation. Live cloud calls are best treated as an optional extra on top of an offline core.

- Applies to: All variants (all have a microSD slot).
- Correction: Confirmed. The pricing page gives Claude Haiku 4.5 batch prices of $0.50 input and $2.50 output per million tokens, and the batch guide says most batches finish in less than 1 hour. The supporting figure of 22 KB per TLS session should be dropped (see llm-03); the higher real cost strengthens the offline-first conclusion.
- Source: <https://platform.claude.com/docs/en/about-claude/models/overview>
- Source: <https://platform.claude.com/docs/en/api/errors>
- Source: <https://platform.claude.com/docs/en/about-claude/pricing>
- Source: <https://platform.claude.com/docs/en/build-with-claude/batch-processing>

### llm-24 · corrected

The Cardputer's radio is 2.4 GHz only, and the Arduino Wi-Fi library does not support certificate-based WPA2-Enterprise. The device has no browser, so hotel networks that require a captive-portal login are likely unusable without a workaround, which makes a phone hotspot broadcasting on 2.4 GHz the dependable route to the internet while travelling.

- Applies to: All variants (StampS3 / Stamp-S3A).
- Correction: 2.4 GHz only is confirmed (M5 docs for Cardputer, v1.1 and StampS3, and Espressif's datasheet; the ADV uses the same SoC). The WPA2-Enterprise statement is wrong. The quoted limitation sits in the WiFiMulti section of the docs and applies to WiFiMulti.addAP(). The core WiFi.begin() has an overload taking wpa2_auth_method_t (WPA2_AUTH_TLS, WPA2_AUTH_PEAP, WPA2_AUTH_TTLS) with ca_pem, client_crt and client_key in cores 2.0.17, 3.3.2 and 3.3.12, and the stock ESP32-S3 libraries set CONFIG_ESP_WIFI_ENTERPRISE_SUPPORT=y. The captive-portal point remains an inference; I found no source either, and my web search budget was exhausted before I could look for Japan-specific evidence. ClawPuter's README adds practical iPhone-hotspot notes (project report): turn on 'Maximize Compatibility' for 2.4 GHz, keep the Personal Hotspot screen open while the device joins, and expect client isolation.
- Source: <https://docs.m5stack.com/en/core/StampS3>
- Source: <https://github.com/bryant24hao/ClawPuter>
- Source: <https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/docs/en/api/wifi.rst>
- Source: <https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/WiFi/src/WiFiSTA.h>

## Found by the fact-check

- The device may not be an ESP32 at all. M5Stack documents a newer Cardputer-family product, CardputerZero (SKU C154, Lite C155, announced 2026-05-26): Raspberry Pi CM0, quad-core Cortex-A53, 512 MB RAM, 1.9 inch 320x170 screen, 46-key keyboard, 2.4 GHz Wi-Fi, Linux. If the unopened box is this one, the heap, TLS and PlatformIO constraints in this facet do not apply and an ordinary Python HTTPS client can call the API. Ask the user for the SKU on the box. https://docs.m5stack.com/en/CardputerZero and https://shop.m5stack.com/blogs/news/m5stack-launches-cardputerzero-a-pocket-sized-linux-computer-for-makers-and-developers
- Stock Arduino ESP32-S3 libraries use fixed 16 KB TLS receive and 16 KB TLS transmit buffers and TLS 1.2 only. Dynamic buffers are requested in the builder defaults but dropped, because DTLS is enabled and ESP-IDF's option 'depends on !MBEDTLS_SSL_PROTO_DTLS'. Plan about 45 KB or more of heap per open TLS connection plus a 16 KB task stack (CardputerOS's own budget), so two simultaneous TLS connections, for example speech-to-text and chat, are unlikely to fit beside a 64 KB screen canvas. This favours one connection to one relay. https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.17/tools/sdk/esp32s3/sdkconfig and https://raw.githubusercontent.com/espressif/esp-idf/v5.5/components/mbedtls/Kconfig and https://raw.githubusercontent.com/urazalievf/cardputer/main/docs/architecture.md
- None of the existing Cardputer LLM clients validates the server certificate, including the relay example. CardputerOS and GeminiCardputerADV_Japanese call setInsecure(), M5Gemini builds with CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY=y and no CA, and cardputer-claude-os uses MicroPython's ssl.wrap_socket whose default is CERT_NONE. Reusing any of them unchanged on hotel Wi-Fi exposes the API key or the device token. https://docs.micropython.org/en/latest/library/ssl.html and https://raw.githubusercontent.com/d4rkmen/M5Gemini/main/sdkconfig and https://raw.githubusercontent.com/dakshaymehta/cardputer-claude-os/main/buddy/device/apps/push_to_claude.py
- Certificate verification is now a one-line change on a current toolchain. Arduino core 3.3.12 (marked Latest) adds NetworkClientSecure::useBuiltinCACertBundle(), which uses the Mozilla bundle already compiled into the core libraries. Older cores can pin roots with setCACert, as AI_StackChan2 does. CardputerOS pins Arduino 3.3.2, which predates the call. https://raw.githubusercontent.com/espressif/arduino-esp32/3.3.12/libraries/NetworkClientSecure/src/NetworkClientSecure.h and https://raw.githubusercontent.com/robo8080/AI_StackChan2/main/M5Unified_AI_StackChan/src/main.cpp
- Anthropic API keys can be created with an expiration (3 hours, 1 day, 7 days, 30 days or a custom duration) that cannot be changed later, and a single key can be disabled or deleted. A key that expires when the trip ends, inside a dedicated workspace with a monthly cap, limits the loss from a stolen device even without a relay. https://platform.claude.com/docs/en/manage-claude/authentication
- Heap fragmentation, not total free heap, is what breaks multi-turn use. ClawPuter found that freeing and re-allocating a large buffer between network calls failed on the second turn (largest free block 94 KB with 187 KB free) and now allocates large buffers once at startup. It also reports, as a project observation I could not verify, that switching Wi-Fi off and on loses about 170 KB of heap permanently, which matters for a battery-saving design that toggles the radio. https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/docs/esp32-voice-chat-lessons.md
- Observed on 2026-09-27 without a key: api.anthropic.com sends even a short 401 JSON body with Transfer-Encoding: chunked under HTTP/1.1, and answers an HTTP/1.0 request with Connection: close. Any client that reads the socket or HTTPClient::getStream() directly needs a chunk decoder or HTTP/1.0 for ordinary replies too, not only for streaming. Background: https://arduinojson.org/v7/how-to/use-arduinojson-with-httpclient/
- A permissively licensed base that already renders Japanese exists. CardputerOS (MIT) embeds efont, about 311 KB of flash covering kana and 6,764 CJK ideographs, and its Translate app handles Japanese with a toggle between native script and romanised output. The Gemini Japanese firmware has no licence and is untested on hardware by its own README. CardputerOS targets the original Cardputer and lists the ADV as unsupported. https://raw.githubusercontent.com/urazalievf/cardputer/main/docs/apps.md
- On the original Cardputer the microphone and speaker share GPIO 43, so only one can be active at a time and a voice tutor has to switch between them. Both ClawPuter and CardputerOS document this. The ADV uses an ES8311 codec instead, so voice code is not portable between the two. https://raw.githubusercontent.com/bryant24hao/ClawPuter/main/README.md and https://raw.githubusercontent.com/urazalievf/cardputer/main/README.md
- Relay storage limits on the free plan: Workers KV allows 1,000 writes per day and 1 write per second to the same key, while SQLite-backed Durable Objects are available on the free plan. A relay that writes history and a spend counter on every turn should keep the daily cap in a Durable Object. https://developers.cloudflare.com/kv/platform/limits/ and https://developers.cloudflare.com/durable-objects/platform/pricing/

## What this means for the design

- Build offline-first. Put the core learning content (vocabulary decks, graded phrases for stations, restaurants, shops and hotels, grammar notes, quizzes, example dialogues with readings) on the SD card, generated and checked on the Mac before the trip. Treat live LLM access as an optional extra that may be slow or unavailable.
- Use the Mac for anything heavy: generate content with a stronger model than Haiku, optionally through the Message Batches API at half price, and pre-render any audio there. The Cardputer should only read, display and play.
- If live chat is wanted, prefer a personal relay (Cloudflare Worker) over calling api.anthropic.com from the device. The relay holds the real key, picks the model, trims history, caps max_tokens, and returns plain short text sized for the screen, so the firmware never parses full Messages API JSON.
- Keep the model id out of the firmware. Store it in the relay (or an SD config file if calling direct), because Claude Haiku 4.5 carries a tentative retirement date of not sooner than October 15, 2026 and a reflash mid-trip is impractical.
- Recommended key pattern: create a dedicated Anthropic workspace with a low monthly spend limit and a workspace-scoped key that lives only in the relay; give the device a random revocable token; have the relay enforce its own daily request or token counter in KV or a Durable Object. If the Cardputer is lost, revoke the device token; the Anthropic key was never on it.
- Do not enable ESP32 flash encryption or burn eFuses on a hobby Cardputer to protect a key. It is irreversible and makes reflashing harder. Accept that anything stored on the device is readable and store only a low-value revocable token.
- Do not copy the setInsecure pattern used by existing Cardputer firmware if a real API key travels over the link. Pin the root CA for the one host the device talks to (setCACert); with a relay that is a single root for your own domain.
- Shape replies for a 240x135 screen: ask for short answers (on the order of 150 to 300 output tokens), page them, and cap conversation history at a handful of turns. Existing firmware uses 600 output tokens and 8 messages as its ceiling.
- If streaming is implemented on-device, write a byte-level reader that decodes chunked transfer first and then splits lines into a fixed buffer, keep only content_block_delta text, ignore ping and unknown events, and handle an error event arriving after HTTP 200. Avoid Arduino String growth in loops; reserve buffers up front.
- Simplest streaming alternative: have the relay consume Anthropic's SSE and send the device a plain text stream (or a complete short reply). This removes SSE and JSON parsing from the firmware entirely.
- Treat voice as a second phase. Typed input works on every variant today; voice needs a 160 KB buffer for 5 seconds unless audio is streamed to the relay while recording, and the ADV has materially better audio hardware than the original or v1.1.
- Plan for the phone hotspot as the only reliable network, set to 2.4 GHz or compatibility mode. Do not design a feature that depends on hotel Wi-Fi with a login page.
- Reuse rather than start from zero: GeminiCardputerADV_Japanese shows romaji-to-kana input and the lgfxJapanGothic font working on ADV (licence unstated, so treat as reference only); cardputer-claude-os (Apache 2.0) is a working relay to adapt; CardputerOS (MIT) shows a direct Claude call in Arduino C++.
- Measure before committing to live features: on the actual device, log free heap and largest free block before and after a TLS connect, and time handshake, first byte and full reply over the phone hotspot. No published project provides these numbers.

## Not settled

- Real end-to-end latency (Wi-Fi connect, TLS handshake, time to first token, full reply) from a Cardputer over a phone hotspot in Japan. No opened project publishes it; the only figures found are a 2-5 s STT call and a 3.1-5.9 s handshake in one unreproduced issue on different hardware.
- Actual free heap and largest contiguous block on each Cardputer variant during a TLS session with M5Unified, a Japanese font and an SD card mounted. Espressif's 22-42 KB figure is from their example, not this device.
- Whether a newer Cardputer variant than the ADV exists, and whether any variant has PSRAM. M5 docs for the three known variants list none; I found no fourth variant.
- Whether the Claude API will stream SSE in response to an HTTP/1.0 request (the ArduinoJson-recommended way to avoid chunked encoding). Not documented; assume a chunk decoder is needed.
- Whether a root CA bundle fits in the 8 MB flash alongside Japanese fonts and the app. CardputerOS's author says it does not fit in their build; a single pinned root certainly does.
- Which certificate authority Anthropic will use in future. Today's chain (Google Trust Services WE1 to GTS Root R4) is an observation, not a documented commitment, so a direct-to-Anthropic pinned root could break without notice.
- The minimum amount a workspace spend limit can be set to, and whether Anthropic offers any daily (rather than monthly) cap. The pages opened only describe monthly limits.
- Whether proxying and reshaping a streamed reply, or base64-encoding uploaded audio, fits within the 10 ms CPU limit of the Cloudflare Workers free plan.
- Whether any Workers AI text-to-speech model produces acceptable Japanese, and what Japanese TTS option is best for pre-rendering audio on the Mac. Not verified in this facet.
- Accuracy of Whisper on learner-accented Japanese recorded through the Cardputer microphones (SPM1423 on original and v1.1, ES8311 path on ADV). No source found.
- Licence of GeminiCardputerADV_Japanese; none is stated, so its code cannot be assumed reusable.
- Whether the v1.1 XiaoZhi fork actually runs on a v1.1 unit; its README does not describe its changes and I did not read its source.
