# Hardware variants and limits

Four ESP32-S3 Cardputer variants/kits and one Linux variant exist as of 2026-09-27: original Cardputer (SKU K132, Stamp-S3, EOL), Cardputer v1.1 (K132-V11, Stamp-S3A, EOL), Cardputer-Adv (K132-Adv, Stamp-S3A, the only ESP32 model M5Stack's shop still sells, $29.90), Cardputer Mesh Kit (K152 = green-back ADV + Cap LoRa-1262 with GNSS), and CardputerZero / Zero-Lite (C154/C155, Raspberry Pi CM0 Linux, Kickstarter May-July 2026, reported shipping around November 2026, so the owner almost certainly does not have one). All three ESP32 models share the same core limits: ESP32-S3FN8 with 8 MB flash, 512 KB SRAM and NO PSRAM; 1.14 inch 240x135 ST7789V2 LCD with PWM backlight on G38; 56-key keyboard with arrows only on the Fn layer; 2.4 GHz Wi-Fi 4 and Bluetooth LE only (no Bluetooth Classic, so no A2DP earbuds); microSD over SPI (FAT32); one Grove port on G1/G2; IR emitter only; no RTC; battery measured only by ADC on G10 with no charge-state detection; power switch must be ON to charge. The ADV differs materially for a language buddy: ES8311 codec + 3.5 mm headphone output, better mic (65 dB SNR), 1750 mAh single battery, BMI270 IMU, TCA8418 I2C keyboard controller (interrupt driven, better rollover), and a 14-pin EXT header that takes the Cap LoRa-1262 GNSS cap. On v1.0/v1.1 the PDM mic and I2S speaker share G43 and M5Stack's own example says they cannot be used at the same time. Hard user-measured battery-life data is thin: M5Stack publishes ADV currents (120 mA idle, 132 mA Wi-Fi, 155 mA BLE at 4.2 V) implying a ceiling of roughly 11-14 h, while blog reports say 6-8 h. I found no trustworthy data on sunlight readability, heat, or deep/light sleep behaviour on any variant.

Fact-check: done.

## Statements

### hw-01 · confirmed

As of 2026-09-27 the Cardputer family consists of: Cardputer (SKU K132, Stamp-S3), Cardputer v1.1 (SKU K132-V11, Stamp-S3A), Cardputer-Adv (SKU K132-Adv / K132-ADV, Stamp-S3A), Cardputer Mesh Kit (SKU K152, a green-back-shell Cardputer-Adv bundled with Cap LoRa-1262), and the Linux-based CardputerZero (C154) and CardputerZero-Lite (C155). K132 and K132-V11 are marked EOL on M5Stack's shop; the shop's Cardputer collection lists only the ADV ($29.90) and the Mesh Kit ($48.00).

- Applies to: All variants
- Correction: Confirmed as written. Sharpening: M5Stack's product index lists no other Cardputer computers. The only other Cardputer-named items are the Cardputer Accessory Kit and Accessory Kit v1.1 (Stamp-S3 or Stamp-S3A plus display, sold as repair or upgrade parts), so an original K132 base can carry a Stamp-S3A. CardputerZero (C154/C155) is still marked work in progress and is reported to ship around November 2026, so a unit already in hand is K132, K132-V11, K132-Adv or the K152 kit.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-kit-w-m5stamps3>

### hw-02 · confirmed

All three ESP32 Cardputers (K132, K132-V11, K132-Adv) use the ESP32-S3FN8 SoC: dual-core LX7 at 240 MHz, 8 MB in-package quad-SPI flash, 512 KB SRAM, and no PSRAM.

- Applies to: Cardputer K132, v1.1, ADV (not CardputerZero)
- Correction: Confirmed as written. Espressif datasheet v2.2 Table 1-1 lists ESP32-S3FN8 with 8 MB (Quad SPI) in-package flash, no in-package PSRAM and 3.3 V VDD_SPI; the feature list gives ROM 384 KB, SRAM 512 KB, RTC SRAM 16 KB. There is no drop-in PSRAM upgrade: forum users report the PSRAM-equipped Stamp-S3Bat is not pin compatible with the Stamp-S3A socket, and one user hand-modified an ADV to add PSRAM (user reports).
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://documentation.espressif.com/esp32-s3_datasheet_en.pdf>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://docs.m5stack.com/en/core/StampS3>

### hw-03 · confirmed

The ESP32 Cardputers have 2.4 GHz 802.11 b/g/n Wi-Fi and Bluetooth 5 LE (plus BLE Mesh) only. There is no Bluetooth Classic, so A2DP audio to ordinary Bluetooth earbuds/speakers is not possible from the device itself.

- Applies to: Cardputer K132, v1.1, ADV
- Correction: Confirmed as written, and the A2DP inference holds. ESP-IDF's soc_caps.h for esp32s3 defines SOC_BLE_SUPPORTED, SOC_BLE_50_SUPPORTED and SOC_BLE_MESH_SUPPORTED but not SOC_BT_CLASSIC_SUPPORTED, which the original ESP32 does define, so A2DP, HFP and SPP are unavailable. The datasheet's Bluetooth LE feature list contains no isochronous channels, so LE Audio earbuds are not an option either (inference from absence). Wi-Fi is 2.4 GHz only.
- Source: <https://documentation.espressif.com/esp32-s3_datasheet_en.pdf>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://www.cnx-software.com/2025/10/23/m5stack-cardputer-adv-esp32-s3-computer-gains-improved-antenna-larger-1750-mah-battery-es8311-audio-codec/>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/release/v5.3/components/soc/esp32s3/include/soc/soc_caps.h>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/release/v5.3/components/soc/esp32/include/soc/soc_caps.h>
- Source: <https://www.espressif.com/en/products/socs/esp32-s3>

### hw-04 · confirmed

All three ESP32 variants use the same display: 1.14 inch ST7789V2, 240 x 135 px, driven over SPI (MOSI G35, SCK G36, DC/RS G34, CS G37, RST G33) with the backlight on G38 under PWM, so brightness is software-controllable. On Stamp-S3A models (v1.1, ADV) the RGB LED shares the backlight supply and is not powered properly when brightness is below 100 percent.

- Applies to: Cardputer K132, v1.1, ADV
- Correction: Confirmed as written. All three M5Stack pin maps list G34 = RS (DC) and G35 = DAT (MOSI), matching M5GFX (pin_dc 34, pin_mosi 35, sclk 36, CS 37, RST 33, panel 135 x 240, rotation 1). M5GFX calls _set_pwm_backlight(GPIO_NUM_38, 7, 256, false, 16), a 256 Hz PWM. The explicit warning that the RGB LED is not powered properly below 100 percent backlight is printed on the v1.1 page only; the ADV page says GPIO38 must be high before using the RGB LED, which is the same Stamp-S3A mechanism.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>

### hw-05 · confirmed

Keyboard: all three have 56 keys (4 x 14). K132 and v1.1 scan a GPIO matrix through a 74HC138 decoder (address lines G8/G9/G11, seven input lines G13/G15/G3/G4/G5/G6/G7) by polling. The ADV uses a TCA8418 I2C keypad controller (SDA G8, SCL G9, INT G11) that scans autonomously and raises an interrupt. Modifier keys are Fn, Shift (Aa), Ctrl, Opt, Alt; arrow keys exist only as Fn + ; , . / and Esc/Del/F1-F12 are also on the Fn layer.

- Applies to: Cardputer K132, v1.1 (74HC138); ADV (TCA8418)
- Correction: Confirmed as written, with a version caveat. The Fn layer in the library key map (arrows on ; , . / plus Esc, Del, F1-F12) was added in M5Cardputer release 1.2.0 (2026-06-08). Keyboard.h at tag 1.1.1 has no Fn layer, and library.properties and library.json still read 1.1.1 at tag 1.2.0 and on master, so an install pinned to version 1.1.1 may lack it. ADV (TCA8418) support arrived in release 1.1.0 (2025-09-05). Pin the library by git tag or commit.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.h>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/IOMatrix.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/TCA8418.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.cpp>

### hw-06 · corrected

Keyboard rollover differs by variant: a third-party reference reports 10+ simultaneous keys with no ghosting on the ADV and roughly 3-key rollover on the original GPIO-matrix Cardputer. Key actuation force is 160 gf on the ADV and on v1.1 units built after a 2025-08 revision, versus 260 gf on older units. A reviewer reports frequent typos because of the tight key pitch.

- Applies to: ADV vs K132/v1.1
- Correction: The community reference says the ADV supports 'at least 10 simultaneous non-modifier keys with no ghosting on the home row'. The no-ghosting test covers the home row only, not the whole matrix. The 3-key limit for the original does have an M5Stack source: the official examples multiPress.ino and usbKeyboard.ino (dated 2023-10-13, hardware M5Cardputer) carry the comment 'max press 3 button at the same time'. Key force is confirmed: ADV 160 gf; the v1.1 version table records a change from 260 gf to 160 gf on 2025.8.2. The typo quote is confirmed; that blog does not name the variant it reviewed.
- Source: <https://github.com/RetroBreeze/cardputer-keyboard-reference>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>
- Source: <https://raw.githubusercontent.com/RetroBreeze/cardputer-keyboard-reference/main/README.md>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/examples/Basic/keyboard/multiPress/multiPress.ino>

### hw-07 · confirmed

Audio on K132 and v1.1: SPM1423 PDM MEMS microphone (DAT G46, CLK G43) and an NS4168 I2S amplifier driving an 8 ohm 1 W speaker (BCLK G41, SDATA G42, LRCLK G43). Mic clock and speaker LRCLK share G43, and M5Stack's own example states the mic and speaker cannot be used at the same time; firmware must call Speaker.end() before Mic.begin(). There is no headphone jack.

- Applies to: Cardputer K132, v1.1
- Correction: Confirmed as written. Sharpening: on K132 and v1.1 this is a hardware limit, not only a library one. G43 carries both the PDM microphone clock (MHz range) and the speaker's I2S word select, two different signals on one pin, so simultaneous record and playback is impossible with any driver. A third-party ESP-IDF board package states the same.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/examples/Basic/mic/mic.ino>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/mic>

### hw-08 · corrected

Audio on the ADV: ES8311 mono codec (I2C on G8/G9; I2S SCLK G41, LRCK G43, DSDIN G42, ASDOUT G46), MEMS microphone with 65 dB SNR, NS4150B amplifier with 8 ohm 1 W speaker, and a 3.5 mm jack that is audio OUTPUT only; inserting a plug disables the speaker amplifier. In M5Unified the mic and speaker use the same I2S pins and separate enable callbacks that each reset and reconfigure the ES8311, so the stock library treats record and playback as alternating modes rather than full duplex.

- Applies to: Cardputer-Adv (and Mesh Kit)
- Correction: Hardware facts are confirmed (ES8311 on I2C G8/G9; SCLK G41, LRCK G43, DSDIN G42, ASDOUT G46; 65 dB SNR mic; NS4150B with 8 ohm 1 W speaker; jack documented as audio output only; plug disables the amplifier). Two fixes. (1) The callbacks do not reset the codec: both write reg 0x00 = 0x80, which Espressif's es8311 driver labels 'Power-on command' (its reset value is 0x1F). They then load different clock-manager values, reg 0x01 = 0xB5 for speaker and 0xBA for microphone, where Espressif's driver uses 0x3F plus bit 7 to enable all clocks; mic disable writes reg 0x00 = 0x00. So the M5Stack Arduino stack is half duplex by configuration, and M5Stack's mic page says mic and speaker cannot be used at the same time on both Cardputer and Cardputer-Adv. (2) Full duplex on the ADV is no longer an open question on paper: the third-party espp board package documents that on the ADV 'both go through the ES8311 codec in full duplex on a single I2S bus'. I did not test it.
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/speaker>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/mic>
- Source: <https://raw.githubusercontent.com/espressif/esp-bsp/master/components/es8311/es8311.c>

### hw-09 · confirmed

Battery: K132 and v1.1 have a 120 mAh cell in the main unit plus a 1400 mAh cell in the base (1520 mAh total); the ADV has a single 1750 mAh cell. None of the ESP32 variants has a fuel gauge or charge-status signal: battery voltage is read through an ADC on G10 (divider ratio 2.0) and M5Stack states the charging state and battery current cannot be read.

- Applies to: Cardputer K132, v1.1, ADV
- Correction: Confirmed as written. The v1.1 page itself lists G10 as Battery Detect (ADC); G11 is a 74HC138 address line, so the 'GPIO 11' reading was a fetch error. Practical consequence reported by users: with the switch OFF and USB connected the battery is disconnected and firmware shows about 100 percent, and readings under load or while charging are unreliable (user reports).
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Power_Class.inl>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/battery>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://www.reddit.com/r/CardPuter/comments/1q1b1ml/battery_recharge_cardputer_adv/>

### hw-10 · corrected

Charging and power switch: on all ESP32 variants the power switch must be in the ON position for the battery to charge over USB-C. The switch disconnects the battery (documented power-off current 0.15-0.26 uA); USB still powers the board with the switch OFF, which is how download mode is entered (switch OFF, hold G0, plug in USB). There is no charge indicator LED. A community member measured about 7 hours for a full charge of the original Cardputer at roughly 62 mA charge current.

- Applies to: Cardputer K132, v1.1, ADV (charge time measurement: K132 only)
- Correction: Switch ON for charging is confirmed for all three variants, and M5Stack states that otherwise the battery is disconnected and the device runs on external power. Corrections: the sub-microamp figures are labelled 'Sleep Current' on the K132 (0.26 uA) and v1.1 (0.15 uA) pages and 'Standby Current (Power Switch Set to OFF)' 0.23 uA on the ADV page; they are switch-off leakage, not a firmware sleep current. The '7 hours' and '62 mA' figures come from two separate posts by one forum user and do not fit together (62 mA for 7 h is about 430 mAh against 1520 mAh), so they should not be combined. About 7 h for a full charge of the original is corroborated by an independent Reddit measurement. No charge time was found for the ADV; ADV owners report slow charging, some report units that would not charge until power-cycled, one reports a unit that failed on first charge, and users advise plain 5 V USB-A sources (all user reports).
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://community.m5stack.com/topic/6044/how-do-i-charge-the-cardputer>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>
- Source: <https://shop.m5stack.com/blogs/blog/m5stack-cardputer-adv-the-limitless-computer>

### hw-11 · corrected

Battery life: M5Stack publishes ADV current draw of 120.2 mA operating, 132.3 mA with Wi-Fi and 154.6 mA with BLE (all at 4.2 V), which gives a theoretical ceiling of roughly 11 to 14.5 hours from 1750 mAh. Reported real-world figures are lower: a blog review of an ADV-based Mesh Kit says 6 to 8 hours in normal use. For v1.1 M5Stack lists 138.93 mA in keyboard mode, implying at most about 11 hours from 1520 mAh. I found no rigorous Wi-Fi-on versus Wi-Fi-off runtime measurements from users for any variant.

- Applies to: ADV (published currents, blog report); v1.1 (published current)
- Correction: The published currents are confirmed (ADV 120.2 mA operating, 132.3 mA Wi-Fi, 154.6 mA BLE at 4.2 V; v1.1 138.93 mA key mode; K132 165.7 mA keyboard mode). But capacity divided by those currents is not a ceiling: test conditions are unstated and they are not the minimum draw. User measurements exist. An original Cardputer ran about 25 h with the display on at setBrightness(50), about 20 percent of the 0-255 range, and Wi-Fi connecting once every 10 minutes, roughly 61 mA average, and took about 7 h to charge (Reddit user report with published source code). An original Cardputer ran about 7 h of continuous BLE scanning (Reddit user report). The 6 to 8 h blog figure is for an ESP32-S3 Cardputer with the add-on SX1262/GNSS module running Meshtastic; the post does not name the variant. I found no ADV runtime without the LoRa cap and no controlled Wi-Fi-on versus Wi-Fi-off comparison. Backlight level and radio duty cycle are the main levers.
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>
- Source: <https://www.aliexpress.com/s/wiki-ssr/article/m5launcher-cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer>

### hw-12 · confirmed

microSD on all ESP32 variants is wired over SPI (CS G12, MOSI G14, CLK G40, MISO G39), not SDMMC. M5Stack's guide requires a FAT32-formatted card and uses the Arduino SD library at 25 MHz; M5Stack publishes no capacity limit. exFAT is disabled by default in ESP-IDF's FatFs, so cards of 64 GB and above (shipped as exFAT) must be reformatted to FAT32. On the ADV the SD SPI lines (G40, G14, G39) are also routed to the EXT header and are shared with the LoRa radio on Cap LoRa-1262.

- Applies to: Cardputer K132, v1.1, ADV
- Correction: Confirmed, and the exFAT part can be raised to high confidence: ESP-IDF's components/fatfs/src/ffconf.h hard-codes '#define FF_FS_EXFAT 0' on master and release/v5.3, and it is not a Kconfig option, so stock Arduino-ESP32 and ESP-IDF builds cannot mount exFAT. M5Stack's pages give no capacity limit. One ADV owner reports a 16 GB Verbatim microSDHC FAT32 card that the device would not read, unresolved (user report), so test the exact card before travelling.
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/sdcard>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://github.com/espressif/esp-idf/issues/13229>
- Source: <https://raw.githubusercontent.com/espressif/esp-idf/master/components/fatfs/src/ffconf.h>

### hw-13 · confirmed

Reports of 'SD card mount failed' on the Cardputer exist, but in the one forum thread I read the cause was the factory demo firmware rather than the cards: 4 GB SDHC cards that failed under the demo firmware worked after switching to M5Launcher. I found no verified list of incompatible card brands or sizes.

- Applies to: Cardputer K132 (forum thread); likely applies to v1.1
- Correction: The thread is described accurately (128 GB SDXC and two 4 GB SDHC cards; a user concluded the demo firmware's Notepad app was at fault and M5Launcher worked). Additions: a second thread shows UIFlow2 needs an explicit SD card init block before access, and a 2026-08 thread reports an ADV that would not read a 16 GB FAT32 microSDHC card, unresolved. Still no verified incompatibility list (all user reports).
- Source: <https://community.m5stack.com/topic/6437/card-computer-sd-card-can-t-format>
- Source: <https://community.m5stack.com/topic/6128>
- Source: <https://community.m5stack.com/topic/8332>

### hw-14 · confirmed

None of the ESP32 Cardputers has a real-time clock chip, so wall-clock time is lost at power-off and must be set from NTP (Wi-Fi), GNSS, or by hand. Only the ADV has an IMU (BMI270 6-axis on the internal I2C bus G8/G9). CardputerZero does have an RTC (RX8130CE) and BMI270 + BMM150.

- Applies to: K132, v1.1, ADV (no RTC); ADV (IMU); CardputerZero (RTC)
- Correction: Confirmed as written. Supporting evidence: none of the three spec pages or pin maps lists an RTC, M5Stack's Arduino docs offer no RTC page for Cardputer, and a long-standing forum contributor states the Cardputer Adv has no RTC chip. The Stamp-S3 and Stamp-S3A schematics show only a 40 MHz crystal net, so sleep timekeeping relies on the chip's internal oscillator (my reading of the schematic net names). M5Stack's Unit RTC (U126, HYM8563, I2C 0x51, coin cell) is an external option on the Grove port.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://community.m5stack.com/topic/8050>

### hw-15 · corrected

Expansion: every ESP32 variant has one HY2.0-4P Grove port carrying GND, 5V, G2 (yellow) and G1 (white). Only the ADV adds a rear EXT 2.54 mm 14-pin header exposing G3, G4, G5, G6, G8 (I2C SDA), G9 (I2C SCL), G13 (UART TX), G15 (UART RX), G14 (MOSI), G39 (MISO), G40 (SCK), plus 5VIN, 5VOUT and GND. An M5Stack store blog says the ADV has a small switch next to the Grove port that sets the 5 V line direction (power out to a sensor, or power in).

- Applies to: All ESP32 variants (Grove); ADV only (EXT header, Grove 5V switch)
- Correction: Grove pins and the ADV EXT header table are confirmed. The Grove 5 V direction switch is not ADV-only. Original Cardputer owners described 'the switch next to the grove port set to 5Vout' in March 2024, before v1.1 or ADV existed; a reseller article on the original says the port 'can be adjusted for 5V input or output using a switch'; and M5Stack's schematic for the original lists two switches and a 5VIN net. The switch must be at 5V OUT for a Grove unit such as GPS to be powered. Only the EXT header is ADV-specific.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://shop.m5stack.com/blogs/blog/m5stack-cardputer-adv-the-limitless-computer>
- Source: <https://geo-tp.github.io/ESP32-Bit-Pirate/boards/cardputer-adv/>
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/481/Sch_M5Cardputer.pdf>

### hw-16 · confirmed

IR: all ESP32 variants have an infrared emitter only, on G44, with no receiver. M5Stack rates the K132/v1.1 emitter at 410 cm on-axis, 170 cm at 45 degrees and 66 cm at 90 degrees. CardputerZero has both an IR transmitter and receiver.

- Applies to: K132, v1.1, ADV (TX only); CardputerZero (TX+RX)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>

### hw-17 · corrected

USB: a single USB-C port on the Stamp module provides power/charging and the ESP32-S3's native USB, which M5Stack documents as 'USB OTG, USB Serial/JTAG'. I did not find M5Stack documentation or an official example demonstrating USB HID, mass storage or USB host on the Cardputer; the M5Cardputer library's Basic examples are button, buzzer, display, ir_nec, keyboard, mic, mic_wav_record and sdcard.

- Applies to: K132, v1.1 (documented); ADV (same SoC and module family, USB line not stated on the ADV page)
- Correction: The 'USB OTG, USB Serial/JTAG' wording is confirmed for K132 and v1.1; the ADV page has no USB row. But official USB HID demonstrations do exist. The M5Cardputer library ships examples/Basic/keyboard/usbKeyboard/usbKeyboard.ino using USBHIDKeyboard, and the factory firmware M5Cardputer-UserDemo has main/apps/app_keyboard with usb_keyboard and ble_keyboard modules. The Basic directory list is correct at top level; its keyboard folder holds inputText, multiPress, singlePress and usbKeyboard. I found no official example for USB mass storage or USB host. M5Stack's published PlatformIO flags use -DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1; TinyUSB classes such as HID normally need USB-OTG mode instead, which I did not build-test.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://github.com/m5stack/M5Cardputer/tree/master/examples/Basic>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/examples/Basic/keyboard/usbKeyboard/usbKeyboard.ino>
- Source: <https://github.com/m5stack/M5Cardputer/tree/master/examples/Basic/keyboard>
- Source: <https://github.com/m5stack/M5Cardputer-UserDemo/tree/main/main/apps/app_keyboard>

### hw-18 · confirmed

Dimensions and weight per M5Stack: K132 is 84.0 x 54.0 x 19.7 mm and 92.3 g; v1.1 is 84.0 x 54.0 x 19.7 mm and 90.0 g; ADV is 84.0 x 54.0 x 19.6 mm and 81.0 g. All are rated for 0 to 40 C operation. The ADV has a lanyard hole, magnets in the back and LEGO-compatible holes.

- Applies to: K132, v1.1, ADV
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### hw-19 · corrected

Telling variants apart without opening the case: (1) the SKU on the box or order is K132, K132-V11 or K132-Adv/K132-ADV (K152 for the Mesh Kit); (2) an ADV has a 3.5 mm audio jack, a 14-pin header on the rear, and a lanyard hole, none of which exist on K132 or v1.1; (3) a Mesh Kit ADV has a green back shell; (4) K132 shipped with a 2.0 mm hex key and v1.1 with a 1.5 mm hex key; (5) v1.1's Stamp-S3A has a visibly larger boot button (4.0 x 3.0 x 2.0 mm versus 2.6 x 1.6 x 0.55 mm). In software, M5GFX/M5Unified autodetection distinguishes only Cardputer from CardputerADV (by probing G8/G9 pull-ups); it cannot tell v1.0 from v1.1.

- Applies to: All ESP32 variants
- Correction: Cues 1 to 4 are confirmed from M5Stack docs and shop pages, and the autodetect description matches M5GFX source. Additions: M5Stack's store blog says the ADV is white and the previous model light gray; documented weights are 92.3 g (K132), 90.0 g (v1.1) and 81.0 g (ADV); a Japanese certification label, if present, names the type. Cue 5 is weaker than stated. The button sizes are documented for the bare Stamp modules, I could not verify that the difference is visible on an assembled Cardputer, and because M5Stack sells an Accessory Kit v1.1 an original base may carry a Stamp-S3A. Telling the ADV from the other two is easy; telling K132 from v1.1 without the box is not reliable.
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-kit-w-m5stamps3>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-with-m5stamps3-v1-1>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>

### hw-20 · confirmed

v1.1 differs from the original K132 only in the core module and keys: Stamp-S3A instead of Stamp-S3 (optimised antenna, RGB LED power switched with the backlight via G38, larger boot button, lower USB sleep current of 88.82 uA versus 400.67 uA) and lighter key force on later units. Display, audio parts, batteries, Grove, microSD and pin map are the same, and M5Unified treats both as the single board type board_M5Cardputer. A reseller blog claiming Grove, microSD and the dual battery are 'V1.1 exclusive' is wrong.

- Applies to: K132 vs v1.1
- Correction: Confirmed as written. Further documented differences are small: lower published operating current (138.93 mA against 165.7 mA in key mode, 148.07 mA against 255.6 mA in IR mode), weight 90.0 g against 92.3 g, and a 1.5 mm hex key in place of 2.0 mm. The reseller article does make the 'V1.1 exclusive' claim and it is wrong.
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://openelab.io/blogs/learn/difference-between-m5stack-cardputer-and-m5stack-cardputer-v1-1>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>

### hw-21 · confirmed

GNSS option for K132, v1.1 and ADV via the Grove port: M5Stack Unit GPS v1.1 (SKU U032-V11), an ATGM336H-6N module on the AT6668 chip supporting GPS, QZSS, BD2, BD3, Galileo and GLONASS, UART at 115200 bps 8N1, 5 V at 31.64 mA, cold start 23 s, hot start 1 s, under 1.5 m CEP50, 48 x 24 x 8 mm, 12.3 g, supplied with a 20 cm Grove cable. It occupies the only Grove port (G1/G2).

- Applies to: K132, v1.1, ADV (any variant with the Grove port)
- Correction: All figures confirmed from the Unit GPS v1.1 page. Wiring detail: the unit's yellow wire is its UART_RX and white is its UART_TX, so on a Cardputer G2 (yellow) must be the transmit pin and G1 (white) the receive pin. The Grove 5 V switch must be at 5V OUT. M5Stack also sells Unit GPS SMA (U190), same AT6668 receiver with an external active antenna. Compatibility with the Cardputer port remains an inference; M5Stack does not state it.
- Source: <https://docs.m5stack.com/en/unit/Unit-GPS%20v1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/unit/Unit-GPS%20SMA>
- Source: <https://www.reddit.com/r/CardPuter/comments/1bm8jsj/advice_for_using_port_a/>

### hw-22 · corrected

GNSS option for the ADV via the EXT header: Cap LoRa-1262 (SKU U214, about $14.50 alone or in the $48 Mesh Kit) combines an SX1262 LoRa radio (868-923 MHz, external RP-SMA antenna) with the same ATGM336H-6N/AT6668 GNSS (GPS/QZSS/BD2/BD3/GAL/GLO) and a built-in ceramic antenna. M5Stack's Arduino example reads GNSS on UART RX G15 / TX G13 at 115200 baud with a TinyGPSPlus fork; LoRa uses NSS G5, IRQ G4, RST G3, BUSY G6 and the SD card's SPI lines. M5Stack lists no Japanese radio certification for it, and warns not to power it without the antenna fitted.

- Applies to: Cardputer-Adv and CardputerZero only (not K132 or v1.1, which lack the EXT header)
- Correction: Hardware facts are confirmed (SKU U214, SX1262 868-923 MHz at +22 dBm, ATGM336H-6N/AT6668 GNSS with QZSS and ceramic antenna, GNSS UART on G15/G13 at 115200, LoRa NSS G5 / IRQ G4 / RST G3 / BUSY G6 on the SD card's SPI lines, antenna warning, $14.50 and $48.00). The certification statement is wrong. M5Stack's Product Certifications page lists CE, FCC and MIC for Cap LoRa-1262, and Japan's MIC database shows type 'Cap LoRa-1262', number 211-251216, dated 2026-02-12, certified for 922-923.4 MHz, 8 channels at 200 kHz spacing, 1.5-5.0 mW. That is far narrower than the hardware's range and its +22 dBm (about 158 mW) maximum, so LoRa transmission in Japan is covered only on a unit bearing that mark with firmware held inside those limits. GNSS is receive-only.
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://docs.m5stack.com/en/arduino/projects/cap/cap_lora868>
- Source: <https://www.cnx-software.com/2026/04/30/m5stack-cardputer-goes-off-grid-with-new-mesh-kit-featuring-lora-gnss-and-meshtastic-support/>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>
- Source: <https://docs.m5stack.com/en/certification>
- Source: <https://www.tele.soumu.go.jp/giteki/list?OF=2&DC=1&SC=1&NUM=211-251216>

### hw-23 · confirmed

CardputerZero is a different class of device: Raspberry Pi CM0 (quad Cortex-A53 at 1 GHz, 512 MB LPDDR2) running Linux, 1.9 inch 320 x 170 ST7789v3 LCD, 46-key keyboard, ES8389 codec with 3.5 mm TRRS audio in/out, RX8130CE RTC, BQ27220 fuel gauge, IR TX+RX, HDMI, Ethernet, 8 MP camera (not on Lite), 84.0 x 54.0 x 23.1 mm. It was crowdfunded on Kickstarter from 2026-05-26 and is reported to ship around November 2026; M5Stack's doc page still marks it 'Work in progress'.

- Applies to: CardputerZero (C154) and CardputerZero-Lite (C155)
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://shop.m5stack.com/blogs/news/m5stack-launches-cardputerzero-a-pocket-sized-linux-computer-for-makers-and-developers>
- Source: <https://www.cnx-software.com/2026/05/25/cardputerzero-a-raspberry-pi-cm0-pocket-computer-for-makers/>
- Source: <https://itsfoss.com/news/cardputerzero-crowdfunding/>

### hw-24 · corrected

Sleep behaviour is not documented by M5Stack beyond power-off/standby currents, and I found no trustworthy user measurements of light-sleep or deep-sleep current or wake reliability on any Cardputer. Structurally, the ADV's TCA8418 provides a single interrupt line on G11 (an RTC-capable GPIO on ESP32-S3) that could serve as a key-press wake source, whereas the K132/v1.1 polled matrix has no interrupt, leaving the G0 button or a timer as the straightforward wake sources. M5Stack's UIFlow2 guide notes the ADV keyboard starts in a low-power sleep mode under that firmware.

- Applies to: ADV vs K132/v1.1
- Correction: Structural facts are confirmed from source: the ADV's TCA8418 interrupt is on G11, which is RTC_GPIO11 on the ESP32-S3 and so usable as a deep-sleep wake pin; K132 and v1.1 keyboards are polled matrices; the UIFlow2 sentence is quoted correctly. Corrections: (1) M5Stack does publish module-level sleep currents: Stamp-S3A 6.84 uA on VIN_5V and 88.82 uA on USB, against 310.89 uA and 400.67 uA for the Stamp-S3 in K132. No whole-device sleep current is published for any Cardputer. (2) In M5Unified the Cardputer boards have no PMIC, power-hold pin or wake pin, so M5.Power.powerOff() just calls esp_deep_sleep_start(); only the slide switch disconnects the battery, and key wake must be set up by the application. (3) I also found no measured sleep current for a whole Cardputer; one community ADV firmware that depends on key wake states its on-device measurements were not taken. Key wake on K132 and v1.1 remains untested.
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/TCA8418.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/IOMatrix.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/uiflow2/cardputer-adv/program>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Power_Class.inl>
- Source: <https://documentation.espressif.com/esp32-s3_datasheet_en.pdf>

### hw-25 · confirmed

Known physical gotchas from M5Stack and reviewers: the display FPC cable is fragile when the Stamp module is removed from the front panel (K132/v1.1); Cap LoRa-1262 must be fixed with M2 x 4 mm screws because longer screws can press on the internal PCB; ADV buyers report creaking function keys and gaps between case parts; a v1.1 buyer found the screen too small for 'old eyes'. I found no sourced data on sunlight readability, panel brightness in nits, or heat for any variant.

- Applies to: K132/v1.1 (FPC); ADV (cap screws, build reports); all (screen size)
- Correction: Confirmed on spot check. The FPC warning also appears on the v1.1 page for the Stamp-S3A. I likewise found no sourced data on sunlight readability, panel brightness or heat.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-with-m5stamps3-v1-1>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>

## Found by the fact-check

- Japan radio certification (K132, v1.1, ADV). Japan's MIC database lists construction-design certifications held by M5Stack for type 'Cardputer' (219-249271, 2024-07-25) and 'Cardputer Adv' (219-259647, 2025-11-05), and for the modules 'StampS3' (219-229318, 2023-01-09) and 'StampS3A' (219-249504, 2025-01-07), all for 2.4 GHz Wi-Fi and BLE only. M5Stack's own certification page lists MIC for Cardputer-Adv and Stamp-S3 but only RoHS for Cardputer v1.1 and Stamp-S3A, and has no entry for the original K132. Certification covers units that carry the mark, so check the unit for the mark and number. Sources: https://www.tele.soumu.go.jp/giteki/list?OF=2&DC=1&SC=1&TN=Cardputer , https://www.tele.soumu.go.jp/giteki/list?OF=2&DC=5&SC=1&NAM=M5Stack&TN=StampS3 , https://docs.m5stack.com/en/certification
- Visitor rule in Japan (all variants). The regulator states radio equipment used in Japan must meet Japanese technical standards, but visitors may use Wi-Fi and Bluetooth devices without the mark for 90 days after entry if they meet equivalent standards, including connecting to a smartphone by tethering on 2.4 GHz. Routers brought from abroad may be used only with the mark, which by my inference matters for firmware that runs the Cardputer as a Wi-Fi access point. The exemption names only Wi-Fi and Bluetooth, not 920 MHz LoRa. Source: https://www.tele.soumu.go.jp/e/sys/others/inbound/index.htm
- Existing firmware is not interchangeable between variants. Firmware built on the original 74HC138 keyboard driver leaves the ADV keyboard dead; forum users report that only reset and G0 respond. The official M5Cardputer library gained ADV support only in release 1.1.0 (2025-09-05). Any third-party firmware or app chosen for the trip must be an ADV-aware build if the unit is an ADV. Sources: https://github.com/m5stack/M5Cardputer/releases , https://community.m5stack.com/topic/8256/cardputer-adv-doom-keyboard-fix-first-working-firmware , https://community.m5stack.com/topic/8333 (forum posts are user reports)
- Measured runtime is better than the published currents imply when the backlight is dimmed and Wi-Fi is used in bursts. One user logged about 25 h on an original Cardputer with the display on at setBrightness(50) and Wi-Fi connecting once every 10 minutes, and about 7 h to recharge, with source code published. Another reports about 7 h of continuous BLE scanning. Both are single user reports on the original model; no equivalent ADV figure was found. Sources: https://www.reddit.com/r/CardPuter/comments/1psw6gf/battery_charge_discharge_profile_of_cardputer_s3/ , https://gist.github.com/kobylin/1e83968ab7073fdb4058bb5757214233 , https://www.reddit.com/r/CardPuter/comments/1dv56ln/the_battery_life_on_this_is_great/
- Screen density for Japanese text (all ESP32 variants). 240 x 135 pixels on a 1.14 inch diagonal is about 242 pixels per inch, a pixel pitch near 0.105 mm (my arithmetic from M5Stack's spec). A 16 px kanji is about 1.7 mm tall and the screen holds 15 x 8 full-width characters; at 24 px it is about 2.5 mm and 10 x 5 characters; 8 px furigana would be under 1 mm. M5GFX ships Japanese bitmap fonts lgfxJapanGothic and lgfxJapanMincho from 8 to 40 px and efontJA from 10 to 24 px; their flash cost inside the 8 MB was not measured. Sources: https://docs.m5stack.com/en/core/Cardputer-Adv , https://raw.githubusercontent.com/m5stack/M5GFX/master/src/lgfx/v1/lgfx_fonts.hpp
- Private listening on K132 and v1.1, which have no jack and no Bluetooth audio. M5Stack's Unit AudioPlayer (U197) is a Grove UART device, 9600 bps, with its own microSD slot (FAT16/FAT32, 32 GB maximum), MP3 and WAV decoding and a 3.5 mm stereo jack, drawing about 25 mA. It would play pre-generated audio through earphones but occupies the only Grove port, so it competes with a GPS or RTC unit. Compatibility with the Cardputer is my inference from the port type. Source: https://docs.m5stack.com/en/unit/Unit_AudioPlayer
- Build and serial setup. M5Stack publishes an official PlatformIO environment on the Cardputer and Cardputer-Adv pages: platform espressif32@6.7.0, board esp32-s3-devkitc-1, flags -DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1, library from the M5Cardputer GitHub URL. The chip's default UART0 pins GPIO43 and GPIO44 are wired to the audio clock line and the IR LED on every variant, so logs must go over native USB. Sources: https://docs.m5stack.com/en/core/Cardputer , https://docs.m5stack.com/en/core/Cardputer-Adv , https://documentation.espressif.com/esp32-s3_datasheet_en.pdf
- Phone hotspot band. The radio is 2.4 GHz only, so the phone hotspot must offer a 2.4 GHz network. For iPhone 12 or later Apple's advice when a device cannot join is to turn on Maximize Compatibility in Personal Hotspot settings. Apple's page does not name the band; the 2.4 GHz behaviour is widely reported but I did not find it in Apple's text. Sources: https://support.apple.com/en-us/119837 , https://documentation.espressif.com/esp32-s3_datasheet_en.pdf
- Adjacent to this facet: Espressif's on-device speech command engine MultiNet supports only Chinese and English on ESP32-S3, so there is no stock on-device Japanese speech recognition; a Japanese wake word model exists. Any Japanese speech recognition or pronunciation checking would have to run off-device over the tethered connection. Source: https://github.com/espressif/esp-sr

## What this means for the design

- Identify the variant first; it decides the audio design. Ask for the SKU on the box and whether the unit has a 3.5 mm jack and a 14-pin rear header. One firmware binary can serve K132/v1.1 and ADV because M5Unified/M5GFX autodetect Cardputer vs CardputerADV at boot, but feature flags (headphones, IMU, GNSS cap) must branch on the detected board.
- No PSRAM and 512 KB SRAM: keep dictionaries, example sentences, kanji data, fonts and audio on the microSD card and read them by seeking into pre-built indexed files. Do not plan to load a JMdict-scale dictionary, large JSON, or whole audio clips into RAM. Pre-compute on the Mac: binary-search or hash index files, fixed-width record tables, and pre-rendered bitmap font subsets.
- No on-device speech recognition, TTS or translation models are realistic on this hardware. Pre-generate all Japanese audio (words, phrases, dialogues) on the Mac and store it on SD; anything requiring ASR, LLM or translation must go over Wi-Fi to a cloud API via the phone hotspot and needs an offline fallback.
- Prefer WAV (M5Stack's documented playback path) at a modest mono sample rate for phrase audio; MP3/Opus decode is possible on ESP32-S3 in principle but competes for the same limited RAM as TLS and was not verified here. Stream from SD in small buffers.
- 240 x 135 px is tiny for Japanese: at a 16 px font that is about 15 full-width characters by 8 lines, at 24 px about 10 by 5. Design single-card screens (one word or one short phrase with furigana/romaji toggled by key), large kanji view for stroke detail, and horizontal paging instead of scrolling paragraphs.
- Bluetooth earbuds will not work (BLE only). For private listening on trains the ADV's 3.5 mm jack with wired earphones is the only built-in path; K132/v1.1 have speaker only, which is awkward in quiet Japanese public spaces, so on those variants lean on visual/typing drills and keep audio optional.
- Treat record and playback as alternating modes on every variant. A shadowing/pronunciation feature should be: play model audio, stop speaker, record user, stop mic, play back. Do not design anything that needs simultaneous mic and speaker (live conversation with barge-in, echo cancellation).
- The keyboard is US QWERTY, so Japanese input must be romaji-to-kana conversion in firmware, with kana-to-kanji conversion limited to a small SD-backed lookup. Arrow keys need Fn held, so make primary navigation single keys (for example , . / ; without Fn, or Enter/Space/Tab) and keep chords to at most two keys so the original matrix keyboard's limited rollover never matters.
- There is no RTC. Spaced-repetition scheduling needs a trustworthy date: sync NTP whenever Wi-Fi is available, or take time from GNSS if fitted, persist the last known time to SD/NVS, and make the scheduler tolerant of unknown or backwards time (for example count sessions rather than days when the clock is unset). Set the timezone to JST explicitly.
- Budget for roughly a day of intermittent use rather than multi-day standby: keep Wi-Fi off by default and bring it up only for sync or cloud calls, dim the backlight via PWM, blank the screen on idle, and use the hardware power switch for real off. Save study state to SD after every card so a power-switch-off loses nothing. Carry a USB-C power bank.
- Show battery as a coarse voltage-based estimate only and tell the user to charge with the switch ON; the firmware cannot detect charging or show a reliable percentage. Expect overnight-scale charging on the original (about 7 h reported).
- Location-aware ideas (station names, nearby-context vocabulary, trip log) require extra hardware: Unit GPS v1.1 on the Grove port for any variant, or Cap LoRa-1262 on an ADV. Both support QZSS. If using the cap, do not enable LoRa transmission in Japan without checking certification, and note it shares SPI lines with the SD card.
- Use a FAT32-formatted card (32 GB or smaller avoids reformatting from exFAT), keep file counts per directory moderate, and replace the factory demo firmware before judging SD compatibility. Build the SD image on the Mac with a script so it can be regenerated.
- The IMU on the ADV allows gesture extras (flip to reveal answer, shake for next card), but keep them optional since K132/v1.1 lack it.
- If the owner actually has or is waiting for a CardputerZero, the whole plan changes (Linux, Python, real TTS/dictionary tools, TRRS mic input, RTC), so confirm this before committing to ESP32 firmware.

## Not settled

- Real battery runtime with Wi-Fi on versus off, and with audio playback, for each variant. Only vendor current figures and one blog estimate (6-8 h with a LoRa cap) were found.
- Whether light sleep or deep sleep works reliably on any Cardputer, what current it draws with the display and amplifier rails still powered, and whether the ADV can wake on a key press via the TCA8418 interrupt on G11. Nothing measured was found.
- Sunlight readability and brightness (nits) of the 1.14 inch panel, and any heat issues. No sourced data found.
- Whether the ADV's ES8311 path can run full duplex (simultaneous record and playback) with a custom driver; M5Unified does not do this, and hardware capability was not confirmed.
- Whether the ADV 3.5 mm jack carries any microphone input. M5Stack describes it as output only; no schematic was read to confirm the jack wiring.
- Maximum microSD capacity that works reliably, and whether exFAT can be enabled in the PlatformIO Arduino or ESP-IDF build used. M5Stack states only 'FAT32'.
- Case colours and label/silkscreen text for each variant. M5Stack docs give none; the 'light gray vs white' description and the Grove 5 V direction switch on the ADV come from an M5Stack store blog that I could only read via summary.
- Charging current and full-charge time for the ADV's 1750 mAh cell (TP4057 charger reported by the M5Stack blog; no figures found).
- USB device classes actually usable on the Cardputer (HID keyboard, mass storage for loading SD content from the Mac) and USB host support were not verified against an M5Stack example.
- CardputerZero battery capacity is inconsistent between M5Stack docs (1750 mAh) and press coverage (1500 mAh), and its shipping date (around November 2026) comes from press, not an M5Stack statement I read.
- Discrepancies in the v1.1 doc fetch (battery ADC reported as G11, speaker LRCLK as G44) versus the K132 doc and M5Unified source (G10 and G43). I treated the source code as authoritative; the v1.1 page should be read directly to confirm it is a summarisation error.
- Legal status in Japan of transmitting with Cap LoRa-1262 (no certification information on M5Stack's page). Not researched in this facet.
