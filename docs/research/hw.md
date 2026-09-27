# Hardware variants and limits

Four ESP32-S3 Cardputer variants/kits and one Linux variant exist as of 2026-09-27: original Cardputer (SKU K132, Stamp-S3, EOL), Cardputer v1.1 (K132-V11, Stamp-S3A, EOL), Cardputer-Adv (K132-Adv, Stamp-S3A, the only ESP32 model M5Stack's shop still sells, $29.90), Cardputer Mesh Kit (K152 = green-back ADV + Cap LoRa-1262 with GNSS), and CardputerZero / Zero-Lite (C154/C155, Raspberry Pi CM0 Linux, Kickstarter May-July 2026, reported shipping around November 2026, so the owner almost certainly does not have one). All three ESP32 models share the same core limits: ESP32-S3FN8 with 8 MB flash, 512 KB SRAM and NO PSRAM; 1.14 inch 240x135 ST7789V2 LCD with PWM backlight on G38; 56-key keyboard with arrows only on the Fn layer; 2.4 GHz Wi-Fi 4 and Bluetooth LE only (no Bluetooth Classic, so no A2DP earbuds); microSD over SPI (FAT32); one Grove port on G1/G2; IR emitter only; no RTC; battery measured only by ADC on G10 with no charge-state detection; power switch must be ON to charge. The ADV differs materially for a language buddy: ES8311 codec + 3.5 mm headphone output, better mic (65 dB SNR), 1750 mAh single battery, BMI270 IMU, TCA8418 I2C keyboard controller (interrupt driven, better rollover), and a 14-pin EXT header that takes the Cap LoRa-1262 GNSS cap. On v1.0/v1.1 the PDM mic and I2S speaker share G43 and M5Stack's own example says they cannot be used at the same time. Hard user-measured battery-life data is thin: M5Stack publishes ADV currents (120 mA idle, 132 mA Wi-Fi, 155 mA BLE at 4.2 V) implying a ceiling of roughly 11-14 h, while blog reports say 6-8 h. I found no trustworthy data on sunlight readability, heat, or deep/light sleep behaviour on any variant.

Fact-check: still running when this file was written; treat every statement as unchecked.

## Statements

### hw-01 · not checked

As of 2026-09-27 the Cardputer family consists of: Cardputer (SKU K132, Stamp-S3), Cardputer v1.1 (SKU K132-V11, Stamp-S3A), Cardputer-Adv (SKU K132-Adv / K132-ADV, Stamp-S3A), Cardputer Mesh Kit (SKU K152, a green-back-shell Cardputer-Adv bundled with Cap LoRa-1262), and the Linux-based CardputerZero (C154) and CardputerZero-Lite (C155). K132 and K132-V11 are marked EOL on M5Stack's shop; the shop's Cardputer collection lists only the ADV ($29.90) and the Mesh Kit ($48.00).

- Applies to: All variants
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-kit-w-m5stamps3>

### hw-02 · not checked

All three ESP32 Cardputers (K132, K132-V11, K132-Adv) use the ESP32-S3FN8 SoC: dual-core LX7 at 240 MHz, 8 MB in-package quad-SPI flash, 512 KB SRAM, and no PSRAM.

- Applies to: Cardputer K132, v1.1, ADV (not CardputerZero)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://documentation.espressif.com/esp32-s3_datasheet_en.pdf>

### hw-03 · not checked

The ESP32 Cardputers have 2.4 GHz 802.11 b/g/n Wi-Fi and Bluetooth 5 LE (plus BLE Mesh) only. There is no Bluetooth Classic, so A2DP audio to ordinary Bluetooth earbuds/speakers is not possible from the device itself.

- Applies to: Cardputer K132, v1.1, ADV
- Source: <https://documentation.espressif.com/esp32-s3_datasheet_en.pdf>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://www.cnx-software.com/2025/10/23/m5stack-cardputer-adv-esp32-s3-computer-gains-improved-antenna-larger-1750-mah-battery-es8311-audio-codec/>

### hw-04 · not checked

All three ESP32 variants use the same display: 1.14 inch ST7789V2, 240 x 135 px, driven over SPI (MOSI G35, SCK G36, DC/RS G34, CS G37, RST G33) with the backlight on G38 under PWM, so brightness is software-controllable. On Stamp-S3A models (v1.1, ADV) the RGB LED shares the backlight supply and is not powered properly when brightness is below 100 percent.

- Applies to: Cardputer K132, v1.1, ADV
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>

### hw-05 · not checked

Keyboard: all three have 56 keys (4 x 14). K132 and v1.1 scan a GPIO matrix through a 74HC138 decoder (address lines G8/G9/G11, seven input lines G13/G15/G3/G4/G5/G6/G7) by polling. The ADV uses a TCA8418 I2C keypad controller (SDA G8, SCL G9, INT G11) that scans autonomously and raises an interrupt. Modifier keys are Fn, Shift (Aa), Ctrl, Opt, Alt; arrow keys exist only as Fn + ; , . / and Esc/Del/F1-F12 are also on the Fn layer.

- Applies to: Cardputer K132, v1.1 (74HC138); ADV (TCA8418)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/Keyboard.h>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/IOMatrix.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/TCA8418.cpp>

### hw-06 · not checked

Keyboard rollover differs by variant: a third-party reference reports 10+ simultaneous keys with no ghosting on the ADV and roughly 3-key rollover on the original GPIO-matrix Cardputer. Key actuation force is 160 gf on the ADV and on v1.1 units built after a 2025-08 revision, versus 260 gf on older units. A reviewer reports frequent typos because of the tight key pitch.

- Applies to: ADV vs K132/v1.1
- Source: <https://github.com/RetroBreeze/cardputer-keyboard-reference>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>

### hw-07 · not checked

Audio on K132 and v1.1: SPM1423 PDM MEMS microphone (DAT G46, CLK G43) and an NS4168 I2S amplifier driving an 8 ohm 1 W speaker (BCLK G41, SDATA G42, LRCLK G43). Mic clock and speaker LRCLK share G43, and M5Stack's own example states the mic and speaker cannot be used at the same time; firmware must call Speaker.end() before Mic.begin(). There is no headphone jack.

- Applies to: Cardputer K132, v1.1
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/examples/Basic/mic/mic.ino>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### hw-08 · not checked

Audio on the ADV: ES8311 mono codec (I2C on G8/G9; I2S SCLK G41, LRCK G43, DSDIN G42, ASDOUT G46), MEMS microphone with 65 dB SNR, NS4150B amplifier with 8 ohm 1 W speaker, and a 3.5 mm jack that is audio OUTPUT only; inserting a plug disables the speaker amplifier. In M5Unified the mic and speaker use the same I2S pins and separate enable callbacks that each reset and reconfigure the ES8311, so the stock library treats record and playback as alternating modes rather than full duplex.

- Applies to: Cardputer-Adv (and Mesh Kit)
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/speaker>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>

### hw-09 · not checked

Battery: K132 and v1.1 have a 120 mAh cell in the main unit plus a 1400 mAh cell in the base (1520 mAh total); the ADV has a single 1750 mAh cell. None of the ESP32 variants has a fuel gauge or charge-status signal: battery voltage is read through an ADC on G10 (divider ratio 2.0) and M5Stack states the charging state and battery current cannot be read.

- Applies to: Cardputer K132, v1.1, ADV
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/utility/Power_Class.inl>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/battery>

### hw-10 · not checked

Charging and power switch: on all ESP32 variants the power switch must be in the ON position for the battery to charge over USB-C. The switch disconnects the battery (documented power-off current 0.15-0.26 uA); USB still powers the board with the switch OFF, which is how download mode is entered (switch OFF, hold G0, plug in USB). There is no charge indicator LED. A community member measured about 7 hours for a full charge of the original Cardputer at roughly 62 mA charge current.

- Applies to: Cardputer K132, v1.1, ADV (charge time measurement: K132 only)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://community.m5stack.com/topic/6044/how-do-i-charge-the-cardputer>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>
- Source: <https://shop.m5stack.com/blogs/blog/m5stack-cardputer-adv-the-limitless-computer>

### hw-11 · not checked

Battery life: M5Stack publishes ADV current draw of 120.2 mA operating, 132.3 mA with Wi-Fi and 154.6 mA with BLE (all at 4.2 V), which gives a theoretical ceiling of roughly 11 to 14.5 hours from 1750 mAh. Reported real-world figures are lower: a blog review of an ADV-based Mesh Kit says 6 to 8 hours in normal use. For v1.1 M5Stack lists 138.93 mA in keyboard mode, implying at most about 11 hours from 1520 mAh. I found no rigorous Wi-Fi-on versus Wi-Fi-off runtime measurements from users for any variant.

- Applies to: ADV (published currents, blog report); v1.1 (published current)
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://nepamesh.com/m5stack-cardputer-review/>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>
- Source: <https://www.aliexpress.com/s/wiki-ssr/article/m5launcher-cardputer>

### hw-12 · not checked

microSD on all ESP32 variants is wired over SPI (CS G12, MOSI G14, CLK G40, MISO G39), not SDMMC. M5Stack's guide requires a FAT32-formatted card and uses the Arduino SD library at 25 MHz; M5Stack publishes no capacity limit. exFAT is disabled by default in ESP-IDF's FatFs, so cards of 64 GB and above (shipped as exFAT) must be reformatted to FAT32. On the ADV the SD SPI lines (G40, G14, G39) are also routed to the EXT header and are shared with the LoRa radio on Cap LoRa-1262.

- Applies to: Cardputer K132, v1.1, ADV
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/sdcard>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://github.com/espressif/esp-idf/issues/13229>

### hw-13 · not checked

Reports of 'SD card mount failed' on the Cardputer exist, but in the one forum thread I read the cause was the factory demo firmware rather than the cards: 4 GB SDHC cards that failed under the demo firmware worked after switching to M5Launcher. I found no verified list of incompatible card brands or sizes.

- Applies to: Cardputer K132 (forum thread); likely applies to v1.1
- Source: <https://community.m5stack.com/topic/6437/card-computer-sd-card-can-t-format>

### hw-14 · not checked

None of the ESP32 Cardputers has a real-time clock chip, so wall-clock time is lost at power-off and must be set from NTP (Wi-Fi), GNSS, or by hand. Only the ADV has an IMU (BMI270 6-axis on the internal I2C bus G8/G9). CardputerZero does have an RTC (RX8130CE) and BMI270 + BMM150.

- Applies to: K132, v1.1, ADV (no RTC); ADV (IMU); CardputerZero (RTC)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/CardputerZero>

### hw-15 · not checked

Expansion: every ESP32 variant has one HY2.0-4P Grove port carrying GND, 5V, G2 (yellow) and G1 (white). Only the ADV adds a rear EXT 2.54 mm 14-pin header exposing G3, G4, G5, G6, G8 (I2C SDA), G9 (I2C SCL), G13 (UART TX), G15 (UART RX), G14 (MOSI), G39 (MISO), G40 (SCK), plus 5VIN, 5VOUT and GND. An M5Stack store blog says the ADV has a small switch next to the Grove port that sets the 5 V line direction (power out to a sensor, or power in).

- Applies to: All ESP32 variants (Grove); ADV only (EXT header, Grove 5V switch)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://shop.m5stack.com/blogs/blog/m5stack-cardputer-adv-the-limitless-computer>
- Source: <https://geo-tp.github.io/ESP32-Bit-Pirate/boards/cardputer-adv/>

### hw-16 · not checked

IR: all ESP32 variants have an infrared emitter only, on G44, with no receiver. M5Stack rates the K132/v1.1 emitter at 410 cm on-axis, 170 cm at 45 degrees and 66 cm at 90 degrees. CardputerZero has both an IR transmitter and receiver.

- Applies to: K132, v1.1, ADV (TX only); CardputerZero (TX+RX)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/CardputerZero>

### hw-17 · not checked

USB: a single USB-C port on the Stamp module provides power/charging and the ESP32-S3's native USB, which M5Stack documents as 'USB OTG, USB Serial/JTAG'. I did not find M5Stack documentation or an official example demonstrating USB HID, mass storage or USB host on the Cardputer; the M5Cardputer library's Basic examples are button, buzzer, display, ir_nec, keyboard, mic, mic_wav_record and sdcard.

- Applies to: K132, v1.1 (documented); ADV (same SoC and module family, USB line not stated on the ADV page)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://github.com/m5stack/M5Cardputer/tree/master/examples/Basic>

### hw-18 · not checked

Dimensions and weight per M5Stack: K132 is 84.0 x 54.0 x 19.7 mm and 92.3 g; v1.1 is 84.0 x 54.0 x 19.7 mm and 90.0 g; ADV is 84.0 x 54.0 x 19.6 mm and 81.0 g. All are rated for 0 to 40 C operation. The ADV has a lanyard hole, magnets in the back and LEGO-compatible holes.

- Applies to: K132, v1.1, ADV
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### hw-19 · not checked

Telling variants apart without opening the case: (1) the SKU on the box or order is K132, K132-V11 or K132-Adv/K132-ADV (K152 for the Mesh Kit); (2) an ADV has a 3.5 mm audio jack, a 14-pin header on the rear, and a lanyard hole, none of which exist on K132 or v1.1; (3) a Mesh Kit ADV has a green back shell; (4) K132 shipped with a 2.0 mm hex key and v1.1 with a 1.5 mm hex key; (5) v1.1's Stamp-S3A has a visibly larger boot button (4.0 x 3.0 x 2.0 mm versus 2.6 x 1.6 x 0.55 mm). In software, M5GFX/M5Unified autodetection distinguishes only Cardputer from CardputerADV (by probing G8/G9 pull-ups); it cannot tell v1.0 from v1.1.

- Applies to: All ESP32 variants
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-kit-w-m5stamps3>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-with-m5stamps3-v1-1>
- Source: <https://raw.githubusercontent.com/m5stack/M5GFX/master/src/M5GFX.cpp>

### hw-20 · not checked

v1.1 differs from the original K132 only in the core module and keys: Stamp-S3A instead of Stamp-S3 (optimised antenna, RGB LED power switched with the backlight via G38, larger boot button, lower USB sleep current of 88.82 uA versus 400.67 uA) and lighter key force on later units. Display, audio parts, batteries, Grove, microSD and pin map are the same, and M5Unified treats both as the single board type board_M5Cardputer. A reseller blog claiming Grove, microSD and the dual battery are 'V1.1 exclusive' is wrong.

- Applies to: K132 vs v1.1
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://openelab.io/blogs/learn/difference-between-m5stack-cardputer-and-m5stack-cardputer-v1-1>

### hw-21 · not checked

GNSS option for K132, v1.1 and ADV via the Grove port: M5Stack Unit GPS v1.1 (SKU U032-V11), an ATGM336H-6N module on the AT6668 chip supporting GPS, QZSS, BD2, BD3, Galileo and GLONASS, UART at 115200 bps 8N1, 5 V at 31.64 mA, cold start 23 s, hot start 1 s, under 1.5 m CEP50, 48 x 24 x 8 mm, 12.3 g, supplied with a 20 cm Grove cable. It occupies the only Grove port (G1/G2).

- Applies to: K132, v1.1, ADV (any variant with the Grove port)
- Source: <https://docs.m5stack.com/en/unit/Unit-GPS%20v1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer>

### hw-22 · not checked

GNSS option for the ADV via the EXT header: Cap LoRa-1262 (SKU U214, about $14.50 alone or in the $48 Mesh Kit) combines an SX1262 LoRa radio (868-923 MHz, external RP-SMA antenna) with the same ATGM336H-6N/AT6668 GNSS (GPS/QZSS/BD2/BD3/GAL/GLO) and a built-in ceramic antenna. M5Stack's Arduino example reads GNSS on UART RX G15 / TX G13 at 115200 baud with a TinyGPSPlus fork; LoRa uses NSS G5, IRQ G4, RST G3, BUSY G6 and the SD card's SPI lines. M5Stack lists no Japanese radio certification for it, and warns not to power it without the antenna fitted.

- Applies to: Cardputer-Adv and CardputerZero only (not K132 or v1.1, which lack the EXT header)
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://docs.m5stack.com/en/arduino/projects/cap/cap_lora868>
- Source: <https://www.cnx-software.com/2026/04/30/m5stack-cardputer-goes-off-grid-with-new-mesh-kit-featuring-lora-gnss-and-meshtastic-support/>
- Source: <https://docs.m5stack.com/en/core/Cardputer_Mesh_Kit>

### hw-23 · not checked

CardputerZero is a different class of device: Raspberry Pi CM0 (quad Cortex-A53 at 1 GHz, 512 MB LPDDR2) running Linux, 1.9 inch 320 x 170 ST7789v3 LCD, 46-key keyboard, ES8389 codec with 3.5 mm TRRS audio in/out, RX8130CE RTC, BQ27220 fuel gauge, IR TX+RX, HDMI, Ethernet, 8 MP camera (not on Lite), 84.0 x 54.0 x 23.1 mm. It was crowdfunded on Kickstarter from 2026-05-26 and is reported to ship around November 2026; M5Stack's doc page still marks it 'Work in progress'.

- Applies to: CardputerZero (C154) and CardputerZero-Lite (C155)
- Source: <https://docs.m5stack.com/en/CardputerZero>
- Source: <https://shop.m5stack.com/blogs/news/m5stack-launches-cardputerzero-a-pocket-sized-linux-computer-for-makers-and-developers>
- Source: <https://www.cnx-software.com/2026/05/25/cardputerzero-a-raspberry-pi-cm0-pocket-computer-for-makers/>
- Source: <https://itsfoss.com/news/cardputerzero-crowdfunding/>

### hw-24 · not checked

Sleep behaviour is not documented by M5Stack beyond power-off/standby currents, and I found no trustworthy user measurements of light-sleep or deep-sleep current or wake reliability on any Cardputer. Structurally, the ADV's TCA8418 provides a single interrupt line on G11 (an RTC-capable GPIO on ESP32-S3) that could serve as a key-press wake source, whereas the K132/v1.1 polled matrix has no interrupt, leaving the G0 button or a timer as the straightforward wake sources. M5Stack's UIFlow2 guide notes the ADV keyboard starts in a low-power sleep mode under that firmware.

- Applies to: ADV vs K132/v1.1
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/TCA8418.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Cardputer/master/src/utility/Keyboard/KeyboardReader/IOMatrix.cpp>
- Source: <https://raw.githubusercontent.com/m5stack/M5Unified/master/src/M5Unified.inl>
- Source: <https://docs.m5stack.com/en/uiflow2/cardputer-adv/program>

### hw-25 · not checked

Known physical gotchas from M5Stack and reviewers: the display FPC cable is fragile when the Stamp module is removed from the front panel (K132/v1.1); Cap LoRa-1262 must be fixed with M2 x 4 mm screws because longer screws can press on the internal PCB; ADV buyers report creaking function keys and gaps between case parts; a v1.1 buyer found the screen too small for 'old eyes'. I found no sourced data on sunlight readability, panel brightness in nits, or heat for any variant.

- Applies to: K132/v1.1 (FPC); ADV (cap screws, build reports); all (screen size)
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/cap/Cap_LoRa-1262>
- Source: <https://botland.store/stamp-series/27278-m5stack-cardputer-adv-version-portable-computer-with-m5stamp-s3a-module-esp32-s3fn8-m5stack-k132-adv-6972934176097.html>
- Source: <https://shop.m5stack.com/products/m5stack-cardputer-with-m5stamps3-v1-1>

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
