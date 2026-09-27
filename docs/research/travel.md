# Travel practicalities in Japan

Travel practicalities look favourable, with a few variant-specific caveats. RADIO: the MIC (総務省) giteki database, queried directly on 2026-09-27, lists M5Stack certifications for type names "Cardputer Adv" (219-259647), "Cardputer" (219-249271, dated 2024-07-25), "StampS3" (219-229318) and "StampS3A" (219-249504). All cover only 2.4 GHz Wi-Fi channels 1-13 (2412-2472 MHz, 802.11b/g/n) and BLE 1M/2M. The Cardputer v1.1 has no product-level entry of its own that I could find (M5Stack's certification page lists only RoHS for it), although its StampS3A module is certified. The 90-day visitor exemption (電波法第4条の2第1項) exists as a fallback but its wording is aimed at Wi-Fi Alliance / Bluetooth SIG logo devices such as phones and game consoles. Custom firmware should stay on standard 802.11b/g/n + BLE, channels 1-13, and avoid Espressif LR mode. CONNECTIVITY: ESP32-S3 is 2.4 GHz only and BLE only; iPhone tethering needs Maximize Compatibility and drops idle third-party clients after 90 s; captive portals are impractical for a microcontroller; Web Bluetooth does not exist on iOS Safari. AIR TRAVEL: battery is about 5.6 Wh (original/v1.1, computed) or 6.475 Wh (Adv, from the IEC 62133 report), far below the 100 Wh limit; carry-on is recommended. POWER: both Stamp module schematics show 5.1k CC pull-downs, so USB-C to USB-C chargers should work; the power switch must be ON to charge; Japan is 100 V, 50/60 Hz. NEEDS: the Japan Tourism Agency FY2025 survey puts staff communication (15.4%) and signage (10.9%) among top difficulties, concentrated in restaurants (38%) and stations (27%). IR: transmit-only on GPIO44; IRremoteESP8266 v2.9.0 supports the main Japanese AC brands and Arduino core 3, but hotel AC control will be hit-and-miss. Note: MIC pages returned HTTP 403 to the plain fetcher and were read through a headless browser instead; several PDFs were read from the fetcher's automatic download cache. No files were written and no builds run.

Fact-check: done.

## Statements

### radio-01 · confirmed

The Cardputer-Adv holds Japanese technical conformity (construction design) certification number 219-259647, issued by KL-Certification GmbH (CAB 219) to M5Stack Technology Co., Ltd, covering BLE 1M/2M at 2402-2480 MHz (1.5 mW) and 802.11b/g/n HT20 at 2412-2472 MHz plus HT40 at 2422-2462 MHz.

- Applies to: Cardputer-Adv (K132-Adv) only
- Correction: Confirmed as written against the certificate PDF and the MIC database (219-259647, type name 'Cardputer Adv', 2025-11-05, MRA construction design certification by KL-Certification GmbH, CAB ID 219; PDF signed St. Ingbert 06.11.2025; antenna Espressif H0920 WIFI PIFA 4.23 dBi). Rated power per mode: BLE 1M and 2M 1.5 mW; 802.11b 1.0 mW/MHz; 802.11g and 11n HT20 0.5 mW/MHz; 11n HT40 0.3 mW/MHz. Caveat, Cardputer-Adv only: the Adv was on sale before this certificate existed (Switch Science release date 2025-09-22), and the MIC-published photograph of the Adv test sample (report AiTDG-251013004) shows its Stamp S3A sticker printed with the earlier mark 'R 219-249271' and 'Model Name: M5Cardputer'. A given Adv may therefore display 219-249271 rather than 219-259647; read the number on the unit.
- Source: <https://docs.m5stack.com/en/learn/certification/certification>
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/K132-Adv/MIC/MIC-Certificate.pdf>
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&NUM=219-259647>
- Source: <https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=251128N219&SN=%E8%AA%8D%E8%A8%BC&LN=72&R1=*****&R2=*****>
- Source: <https://www.switch-science.com/products/10737>

### radio-02 · corrected

The MIC database contains a separate certification 219-249271 dated 2024-07-25 for type name 'Cardputer' (M5Stack), but M5Stack's own certification page has no row for the original K132 and lists only RoHS for Cardputer v1.1, so whether a v1.1 unit is covered at product level is not established.

- Applies to: Original Cardputer (K132) most likely; Cardputer v1.1 (K132-V11) coverage uncertain
- Correction: The database and documentation facts are confirmed: MIC lists 219-249271 (type 'Cardputer', 2024-07-25, BLE 1 mW, Wi-Fi 1 mW/MHz, 2412-2472 MHz and 2422-2462 MHz) and 219-259647 ('Cardputer Adv'); M5Stack's certification page has no K132 row and only RoHS for K132-V11; the three Switch Science pages contain no mention of giteki. The inference about which hardware 219-249271 covers is contradicted by the attachments MIC publishes with that record. The test reports (AIT24031204, sample received 12 Mar 2024, issued 12 Jul 2024) state a metal antenna of 4.23 dBi, and the photographs show an original-style Cardputer containing a black Stamp board silk-screened 'M5 STAMP S3 V0.3' with the tall metal antenna. That matches the StampS3A certificate 219-249504 (report AiTDG-241205002: black board marked V0.3, 4.23 dBi) and not the StampS3 certificate 219-229318 (green board marked V0.2, 2.46 dBi). In addition, the MIC photograph of the Cardputer Adv sample shows a Stamp S3A sticker reading 'Model Name: M5Cardputer', 'FCC ID: 2AN3WM5CARDPUTER' and giteki 'R 219-249271'. Corrected statement: 219-249271 is the number printed on Stamp-S3A modules built for Cardputers, so Cardputer v1.1 (Stamp-S3A) is very probably the hardware this certificate covers, while the earliest original K132 units fitted with a V0.2 StampS3 would rely on module certificate 219-229318. That mapping to SKUs is my inference from photographs; the decisive check is the sticker on the owner's Stamp module.
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&TN=Cardputer>
- Source: <https://docs.m5stack.com/en/learn/certification/certification>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://www.switch-science.com/products/10300>
- Source: <https://www.switch-science.com/products/9277>
- Source: <https://www.switch-science.com/products/10737>

### radio-03 · confirmed

Both core modules are individually certified in Japan: StampS3 is 219-229318 (2023-01-09) and StampS3A (including PIN127, PIN254 and FPC8 variants) is 219-249504 (2025-01-07), even though M5Stack's certification page shows only RoHS for Stamp-S3A.

- Applies to: StampS3 (inside original Cardputer); StampS3A (inside Cardputer v1.1 and Cardputer-Adv)
- Correction: Confirmed. StampS3: 219-229318, 2023-01-09; certificate annex gives hardware v0.2, BLE 1M and 2M 4.0 mW, 802.11b 3.0 mW/MHz, 11g/n 1.0 mW/MHz, antenna Shanghai Deman TFPD07H09100011 2.46 dBi. StampS3A, StampS3A PIN127, PIN254 and FPC8: 219-249504, 2025-01-07, 1.5 mW BLE and 1.5 mW/MHz Wi-Fi, antenna 4.23 dBi per test report AiTDG-241205002W6. M5Stack's page lists only RoHS for Stamp-S3A (SKU S007-V033). Sharpening: a module certificate only helps if its mark is displayed on the unit, and the Stamp S3A photographed inside a Cardputer Adv sample is labelled with the Cardputer product number 219-249271, not 219-249504. Each certificate states that its validity is limited to products equal to the examined one.
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/S007/MIC/MIC-Certificate.pdf>
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&TN=StampS3>
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&NUM=219-229318>
- Source: <https://docs.m5stack.com/en/learn/certification/certification>
- Source: <https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=250328N219&SN=%E8%AA%8D%E8%A8%BC&LN=39&R1=*****&R2=*****>
- Source: <https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=230111N219&SN=%E8%AA%8D%E8%A8%BC&LN=123&R1=*****&R2=*****>

### radio-04 · confirmed

Japan lets visitors use self-imported Wi-Fi and Bluetooth devices without the giteki mark for up to 90 days from the date of entry, under Radio Act Article 4-2 paragraph 1, provided the device conforms to standards equivalent to Japan's; MIC's page frames this as devices whose IEEE 802.11 conformity is confirmable by a Wi-Fi Alliance logo 'etc.' or Bluetooth Core Spec 2.1+ conformity by a Bluetooth SIG logo 'etc.'.

- Applies to: All variants (as a fallback if the unit does not carry a giteki mark)
- Correction: Confirmed from the statute, the MIC portal page and the MIC deck. Radio Act Article 4-2 paragraph 1 covers equipment that a person entering Japan brings in personally, for a period not exceeding 90 days from the date of entry. The legally designated equivalent standards are in MIC Notice No. 437 of 2015 (as amended, in force 2025-01-21): IEEE 802.11b, a, g, n, ac, ax and be, Bluetooth Core Specification 2.1 or later, IEEE 802.15.4 and 802.15.4z, and ETSI EN 305 550. FCC and CE are not the legal test, so the GMO blog's wording is inaccurate. MIC's English leaflet phrases the practical condition as 'the device has the Wi-Fi logo' and 'a device with the Bluetooth logo'; I found no evidence that any Cardputer variant carries either logo, so relying on this rule for a unit without a giteki mark is a grey area resting on the word 'etc.'. The IIJ blog (dated 2019-11-20) cites Article 4 paragraph 2, which is the earlier numbering of the same provision.
- Source: <https://www.tele.soumu.go.jp/j/sys/others/inbound/index.htm>
- Source: <https://www.soumu.go.jp/main_content/000987309.pdf>
- Source: <https://techlog.iij.ad.jp/archives/2689/>
- Source: <https://developers.gmo.jp/technology/40225/>
- Source: <https://laws.e-gov.go.jp/api/1/articles;lawId=325AC0000000131;article=4_2>
- Source: <https://www.tele.soumu.go.jp/horei/law_honbun/71ab5073.html>

### radio-05 · confirmed

Under the 90-day rule a 2.4 GHz station may only talk to an access point that is giteki-marked, or not connected to telecom line equipment, or housed in the same enclosure as a foreign radio device (that is, a visitor's phone tethering); a 2.4 GHz access point run by the visitor's device is allowed only if it is not connected to telecom line equipment or is in such a shared enclosure.

- Applies to: All variants when relying on the 90-day rule rather than on a giteki mark
- Correction: Confirmed verbatim from page 2 of the MIC deck (2.4 GHz access point allowed under footnote 1, station under footnote 2, Bluetooth allowed). Practical reading for all variants when no giteki mark is present: the device may join a giteki-marked access point (hotel network, pocket Wi-Fi rented in Japan) or a phone's tethering hotspot, and may run its own soft-AP only when that AP is not connected onward to a telecommunications line. Sharing an upstream internet connection through the Cardputer (AP plus station with NAT) would fall outside footnote 1. MIC's Q and A adds that a wireless LAN router brought from abroad may be used only if it bears the giteki mark. None of these limits applies to a unit that displays a giteki mark.
- Source: <https://www.soumu.go.jp/main_content/000987309.pdf>
- Source: <https://www.tele.soumu.go.jp/j/sys/others/inbound/index.htm>
- Source: <https://www.tele.soumu.go.jp/resource/j/others/wifi/en.pdf>

### radio-06 · confirmed

The Japanese certifications cover only channels 1-13 (2412-2472 MHz) with 802.11b/g/n emission types and BLE 1M/2M PHY; channel 14, Espressif's patented Long Range Wi-Fi mode and BLE coded PHY are not among the certified emissions, so custom firmware should not enable them.

- Applies to: All variants
- Correction: Confirmed. All four certificates (219-229318 StampS3, 219-249271 Cardputer, 219-249504 StampS3A, 219-259647 Cardputer Adv) list only 2412-2472 MHz for 802.11b/g/n HT20, 2422-2462 MHz for HT40, and BLE 2402-2480 MHz at 1 Mbps and 2 Mbps. Channel 14 (2484 MHz) lies outside every listed range, and neither Espressif LR nor BLE coded PHY is listed. ESP-IDF v5.1 and v5.5 both describe LR as an Espressif-patented mode with 1/2 and 1/4 Mbps PHY rates; it is also not one of the IEEE 802.11 standards designated for the 90-day rule. The ESP-NOW page (now ESP-IDF v6.1) confirms a vendor-specific action frame and a default bit rate of 1 Mbps; whether that is within the certified design remains an unsourced legal interpretation, as the claim says. The claim omits that the certificates also fix rated transmit power well below ESP32-S3 firmware defaults (see missed facts).
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/K132-Adv/MIC/MIC-Certificate.pdf>
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/S007/MIC/MIC-Certificate.pdf>
- Source: <https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/api-guides/wifi.html>
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/network/esp_now.html>
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&TN=Cardputer>
- Source: <https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&TN=StampS3>

### radio-07 · confirmed

The ESP-IDF Wi-Fi driver defaults to country code '01' with channels 1-11 active and policy AUTO, under which channels 12-14 are passively scanned only, so a hidden SSID on channels 12-14 will not be found unless the country configuration is changed.

- Applies to: All variants (ESP32-S3 Wi-Fi driver, ESP-IDF v5.1 documentation)
- Correction: Confirmed and extended beyond v5.1. ESP-IDF v5.1 and v5.5 both document the default cc '01', schan 1, nchan 11, WIFI_COUNTRY_POLICY_AUTO, with active scan on channels 1 to 11, passive scan on 12 to 14, and the note that a hidden SSID on a passive-scan channel will not be found. The current stable API reference (ESP-IDF v6.1) still gives default country '01' (world safe mode), lists 'JP' among supported codes and ties channel 14 to the country code. The restructured v6.1 Wi-Fi driver guide no longer has a country code section. Because the M5Stack certificates stop at channel 13, firmware that sets JP manually should restrict nchan to 13.
- Source: <https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/api-guides/wifi.html>
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/wifi-driver/index.html>
- Source: <https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-guides/wifi.html>
- Source: <https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/network/esp_wifi.html>

### conn-01 · confirmed

The ESP32-S3 radio is 2.4 GHz Wi-Fi (802.11 b/g/n) and Bluetooth 5 LE only, with no 5 GHz and no Bluetooth Classic.

- Applies to: All variants (all use ESP32-S3FN8)
- Source: <https://www.espressif.com/en/products/socs/esp32-s3>
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>

### conn-02 · confirmed

On iPhone 12 or later the Personal Hotspot must have Maximize Compatibility enabled to offer a 2.4 GHz network, the user should stay on the Personal Hotspot screen until the device connects, and third-party devices are disconnected after 90 seconds without network traffic.

- Applies to: All variants when tethered to an iPhone
- Correction: Confirmed. Apple's Platform Support guide (published 22 October 2025) states 'Third-party devices automatically disconnect after 90 seconds without network traffic' and 'enable Maximize Compatibility in Settings > Personal Hotspot to use 2.4GHz connections'. The support article (published 7 March 2025) lists iPhone 12 or later for Maximize Compatibility and says 'Stay on this screen until you connect your other device to the Wi-Fi network'. Design consequence: firmware must either send traffic at intervals under 90 seconds or treat every request as connect, fetch, disconnect.
- Source: <https://support.apple.com/en-gb/ht203302>
- Source: <https://support.apple.com/en-gb/guide/platform-support/sup025284ac0/26/web/26>
- Source: <https://support.apple.com/en-gb/guide/platform-support/sup025284ac0/web>

### conn-03 · corrected

Android hotspots have a 'Turn off hotspot automatically' option that shuts the hotspot down when no devices are connected, and a band or 'Speed & compatibility' setting that may need to be set to 2.4 GHz.

- Applies to: All variants when tethered to an Android phone
- Correction: Verified half: the Pixel help page describes 'Turn off hotspot automatically' with the text 'To save battery, your hotspot turns off when no devices are connected', and the general Android help page describes the same setting. No time period is given. Unverified half: neither Google page mentions a band or 'Speed & compatibility' setting, and I could not open a primary Google or Samsung page for the 2.4 GHz band option or Samsung's timeout (the session's web search allowance was exhausted, so only direct page fetches were possible). Treat the band-setting statement as plausible but unverified and check it on the actual phone.
- Source: <https://support.google.com/pixelphone/answer/2812516?hl=en>
- Source: <https://support.google.com/android/answer/9059108?hl=en>

### conn-04 · confirmed

Most Japanese lodgings offer free in-room Wi-Fi and free public hotspots exist at airports, stations, convenience stores and cafes, but public networks range from easy to ones needing cumbersome registration; pocket Wi-Fi rental, SIM and eSIM plans are widely available to visitors.

- Applies to: All variants
- Source: <https://www.japan-guide.com/e/e2279.html>
- Source: <https://www.tele.soumu.go.jp/j/sys/others/inbound/index.htm>
- Source: <https://www.tele.soumu.go.jp/resource/j/others/wifi/en.pdf>

### conn-05 · corrected

A microcontroller has no browser, so networks with captive portals or web registration cannot be joined in a general way; any scripted login is specific to one portal and fragile, which makes phone tethering or a rented pocket Wi-Fi the only dependable route to the internet.

- Applies to: All variants
- Correction: Sound as engineering inference but overstated, and no primary source quantifies captive portal use in Japanese lodgings. Corrected statement: an ESP32-S3 can join any network that uses ordinary password authentication, which includes hotel Wi-Fi run that way, but it cannot complete browser-based portals or registration flows in a general way, and a scripted login is specific to one portal. Phone tethering or a rented pocket Wi-Fi is the most predictable route rather than the only dependable one. The only sourced part is Japan Guide's statement that public networks 'vary widely from easy-to-use ones to others that require cumbersome registrations'. The design should treat connectivity as optional and keep all core learning content on the microSD card.
- Source: <https://www.japan-guide.com/e/e2279.html>

### conn-06 · corrected

Using Bluetooth LE to the phone as the internet route would need a native companion app on iOS because Safari on iOS has no Web Bluetooth support, whereas Chrome on Android does support Web Bluetooth; Bluetooth tethering (PAN) is not possible because the ESP32-S3 lacks Bluetooth Classic.

- Applies to: All variants
- Correction: Browser facts confirmed from caniuse data: Safari on iOS has no Web Bluetooth support through version 27.2, Chrome for Android and Samsung Internet support it, Firefox does not. MDN marks it experimental, secure context only, requiring a permission prompt triggered by user activation. ESP32-S3 has Bluetooth LE only, so Bluetooth PAN tethering is not available. Correction to the inference: iOS needs native code on the phone, but not necessarily a custom companion app. caniuse notes a third-party Safari web extension (iOSWebBLE) that bridges navigator.bluetooth to CoreBluetooth. In every case the BLE link is an application-level relay in which the phone performs the HTTP request for the device; it is not an IP connection, and on Android it needs a page open in the foreground with a user gesture to connect.
- Source: <https://caniuse.com/web-bluetooth>
- Source: <https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API>
- Source: <https://www.espressif.com/en/products/socs/esp32-s3>
- Source: <https://raw.githubusercontent.com/Fyrd/caniuse/main/features-json/web-bluetooth.json>

### air-01 · confirmed

The Cardputer-Adv battery is a single 3.7 V 1750 mAh lithium-ion pouch cell rated 6.475 Wh (model 603075, Shenzhen Yisheng Energy), with an IEC 62133-2 test report published by M5Stack.

- Applies to: Cardputer-Adv only
- Correction: Confirmed from report DGCTL202509160022A (issued 2025-09-29): model 603075, 3.7 V, 1750 mAh, 6.475 Wh, 1S1P with protection circuit, recommended charge 875 mA, maximum 1750 mA. The applicant and manufacturer named in the report is the cell maker Shenzhen Yisheng Energy, not M5Stack. Independent confirmation: the MIC-published photographs of the Cardputer Adv sample show the cell printed 'YS 603075 1750mAh 3.7V 6.475Wh'. The device's external back label shows only 'BAT 1750mAh'.
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/K132-Adv/IEC62133/IEC62133-Report.pdf>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=251128N219&SN=%E8%AA%8D%E8%A8%BC&LN=72&R1=*****&R2=*****>

### air-02 · confirmed

The original Cardputer and Cardputer v1.1 contain two cells of 120 mAh and 1400 mAh (1520 mAh total), which works out to roughly 5.6 Wh at an assumed 3.7 V nominal; M5Stack does not publish a watt-hour figure for these variants.

- Applies to: Original Cardputer (K132) and Cardputer v1.1
- Correction: Confirmed, and the estimate can be replaced by label evidence. M5Stack's pages for K132 and K132-V11 give 120 mAh plus 1400 mAh and no watt-hour figure, and the certification page lists no battery report for either. The MIC-published photographs for certificate 219-249271 show the base cell printed '3.7V 5.18Wh' and 'RS 602866 1400mAh', and the internal cell printed 'DC 401525 3.7V 120mAh' with no watt-hour marking. 5.18 Wh plus 0.444 Wh (calculated) gives about 5.62 Wh in total. The photographed sample is the 2024 Cardputer; v1.1 has the same stated battery configuration.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/learn/certification/certification>
- Source: <https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=240802N219&SN=%E8%AA%8D%E8%A8%BC&LN=10&R1=*****&R2=*****>

### air-03 · confirmed

IATA's 2026 passenger guidance allows a portable electronic device with an installed lithium-ion battery of 100 Wh or less in carry-on without operator approval and recommends carry-on; it may go in checked baggage only if protected from damage and completely switched off, and power banks are carry-on only with a maximum of two.

- Applies to: All variants
- Source: <https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passengers_travelling_with_lithium_batteries.pdf>
- Source: <https://www.iata.org/en/youandiata/travelers/batteries/>

### power-01 · confirmed

Both Stamp module schematics show 5.1 kΩ pull-down resistors on the USB-C CC1 and CC2 pins, so a USB-C to USB-C cable from a Power Delivery charger or power bank should supply 5 V and a USB-A to USB-C cable is not required.

- Applies to: StampS3 v0.2 schematic (original Cardputer) and StampS3A v0.3.3 schematic (Cardputer v1.1, Cardputer-Adv)
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/522/Sch_M5StampS3_v0.2.pdf>
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1150/Sch_StampS3_v0.3.3.pdf>
- Source: <https://docs.m5stack.com/en/core/Stamp-S3A>
- Source: <https://docs.m5stack.com/en/core/StampS3>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>

### power-02 · confirmed

All three variants must have the power switch set to ON while charging, and the original Cardputer has no charge indicator and charges slowly (a forum member measured about 62 mA at the battery and about 7 hours for a full charge).

- Applies to: Power switch note: original, v1.1 and Adv. Indicator and charge time: original Cardputer only (forum evidence)
- Correction: Confirmed, and the apparent contradiction can be reconciled. All three product pages say to switch power ON when charging. The main-board schematic (the K132 and K132-V11 files are byte-identical) and the Cardputer-Adv schematic both show a TP4057 charger with a 3.3 kOhm PROG resistor, CHRG and STDBY pins left unconnected, and the indicator LED drawn as not fitted, so the Adv also has no charge indicator by schematic. The TP4057 datasheet formula R_PROG = 1000 / I_BAT gives about 0.3 A nominal. The battery reaches the charger node only through the power switch, which explains the ON requirement. Forum evidence (M5Stack community, supporting only): one member measured USB draw of 0.3 A with the switch on against 0.05 A off; another reported about 7 hours for a full charge and about 62 mA into the battery while firmware was running. The 62 mA figure is what is left after the running system takes its share, which is my interpretation.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/Cardputer/Sch_M5Cardputer.pdf>
- Source: <https://community.m5stack.com/topic/6044/how-do-i-charge-the-cardputer>
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/481/Sch_M5Cardputer.pdf>

### power-03 · confirmed

Japan's mains supply is 100 V AC throughout, at 50 Hz in eastern Japan and 60 Hz in western Japan, with two-flat-pin sockets resembling North American ones.

- Applies to: All variants (affects the USB charger, not the Cardputer itself)
- Source: <https://www.japan.travel/en/plan/plug-and-electricity/>
- Source: <https://www.japan-guide.com/e/e2225.html>

### need-01 · confirmed

In the Japan Tourism Agency's FY2025 survey of 4,110 foreign visitors, 15.4% reported trouble communicating with staff and 10.9% reported too little or unclear multilingual signage, with communication trouble concentrated in restaurants (38%) and railway stations or bus terminals (27%); 43.7% reported no trouble at all.

- Applies to: All variants (content design)
- Correction: Confirmed verbatim from the press release, and I also read the full results PDF. Sharpening: the 38 percent (restaurants) and 27 percent (railway stations and bus terminals) are shares of the 634 respondents who reported communication trouble, multiple answers allowed, not of all 4,110. The 68 percent refers to staff or traveller using 'automatic translation systems, translation applications and other ICT tools'; about three in ten gave up communicating.
- Source: <https://www.mlit.go.jp/kankocho/news08_00039.html>
- Source: <https://www.mlit.go.jp/kankocho/content/001998584.pdf>

### need-02 · corrected

JNTO states that English is generally understood particularly in major cities and tourist centres and that transport announcements and signs commonly include English or roman characters, while it may not be understood in rural areas or small local shops.

- Applies to: All variants (content design)
- Correction: The first half is confirmed verbatim from JNTO's FAQ: 'English is generally understood throughout the country, particularly in major cities and tourist centers' and 'Public transportation announcements are frequently made in both Japanese and English, and signs generally include decipherable roman characters or English explanations'. The rural and small-shop caveat does not appear on either JNTO page I opened (the word 'rural' is absent from the language page), so it should not be attributed to JNTO. JNTO's language page does recommend the Tourist's Language Handbook and VoiceTra. For an urban versus rural comparison use the Japan Tourism Agency survey instead: restaurants were the top place for communication trouble among both city-only and rural-only visitors (36 percent each).
- Source: <https://www.japan.travel/en/plan/faq/>
- Source: <https://www.japan.travel/en/plan/japanese-language/>
- Source: <https://www.mlit.go.jp/kankocho/content/001998584.pdf>

### need-03 · confirmed

On Japanese trains passengers are expected to keep phones on silent, not make calls (except on the decks of long-distance trains) and keep voices down, so a device that plays audio through a speaker is unsuitable there; I found no authoritative source on device etiquette in restaurants.

- Applies to: All variants; only Cardputer-Adv has a 3.5 mm headphone jack
- Correction: Confirmed. Japan Guide's train manners page (updated 3 December 2025) also says 'Set the volume of your headphones low'. Its dining page does not address phone or device etiquette, consistent with the claim that no authoritative restaurant guidance was found. The headphone jack is on Cardputer-Adv only, and M5Stack states that inserting a 3.5 mm plug disables the speaker amplifier.
- Source: <https://www.japan-guide.com/e/e2230.html>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://www.japan-guide.com/e/e2040.html>

### ir-01 · confirmed

All Cardputer variants have an infrared emitter on GPIO44 and no infrared receiver, so the device cannot learn codes from a hotel remote and must rely on pre-loaded protocol libraries or code databases.

- Applies to: Original Cardputer, Cardputer v1.1, Cardputer-Adv
- Correction: Confirmed for all three variants. Sharpening: the Cardputer-Adv schematic shows the same arrangement as the original (IR LED driven from G44 through a 22 Ohm resistor, no transistor, no receiver part), so output is limited by GPIO drive current on every variant. The range figures (410 cm at 0 degrees, 170 cm at 45 degrees, 66 cm at 90 degrees) are published for the original and v1.1 only; the Adv page gives none. M5Stack's official example applies to 'Cardputer and Cardputer-Adv', uses Arduino-IRremote with IR_TX_PIN 44, and requires M5Stack Board Manager 3.2.2 or later and M5Cardputer library 1.1.0 or later.
- Source: <https://docs.m5stack.com/en/core/Cardputer>
- Source: <https://docs.m5stack.com/en/core/Cardputer-Adv>
- Source: <https://docs.m5stack.com/en/core/Cardputer%20V1.1>
- Source: <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/Cardputer/Sch_M5Cardputer.pdf>
- Source: <https://docs.m5stack.com/en/arduino/m5cardputer/ir_nec>
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/481/Sch_M5Cardputer.pdf>

### ir-02 · confirmed

IRremoteESP8266 lists air-conditioner protocol support for Daikin (ten variants), Mitsubishi Electric, Mitsubishi Heavy, Panasonic, Hitachi, Fujitsu, Sharp, Toshiba, Corona and Sanyo, and version 2.9.0 released on 2 January 2026 adds ESP32 Arduino core version 3 support; the previous release 2.8.6 (July 2023) fails to compile against core 3.x.

- Applies to: All variants (ESP32-S3)
- Correction: Confirmed from the raw SupportedProtocols.md (last generated 2 January 2026) and the GitHub releases: ten Daikin protocol variants, plus Mitsubishi Electric, Mitsubishi Heavy Industries, Panasonic, Hitachi, Fujitsu, Sharp, Toshiba, Corona and Sanyo; v2.9.0 published 2026-01-02 with 'ESP32: Esp32 Core version 3 support (#2144)'; v2.8.6 published 2023-07-28; issue 2218 reports timer API compile errors on core 3.3.1 and was closed as a duplicate of issue 2039. Filling the stated gap: the official PlatformIO platform-espressif32 v7.1.3 (published 2026-09-11) still pins the Arduino core 2.0.17 package, so a default PlatformIO build is on core 2.x; Arduino core 3.x in PlatformIO comes from the community pioarduino fork (release 55.03.312, Arduino 3.3.12 on ESP-IDF 5.5.5).
- Source: <https://github.com/crankyoldgit/IRremoteESP8266/blob/master/SupportedProtocols.md>
- Source: <https://github.com/crankyoldgit/IRremoteESP8266/releases>
- Source: <https://github.com/crankyoldgit/IRremoteESP8266/releases/tag/v2.9.0>
- Source: <https://github.com/crankyoldgit/IRremoteESP8266/issues/2218>
- Source: <https://github.com/crankyoldgit/IRremoteESP8266>
- Source: <https://raw.githubusercontent.com/crankyoldgit/IRremoteESP8266/master/SupportedProtocols.md>

### ir-03 · corrected

Controlling Japanese hotel air conditioners by infrared will be unreliable: protocol support is tied to specific tested models, many listed models are export models, and hotel rooms may use centrally controlled systems or wall-mounted wired panels instead of a handheld infrared remote. Televisions are a better bet because they use simpler fixed codes.

- Applies to: All variants
- Correction: Verified parts: SupportedProtocols.md lists specific tested models and remotes per protocol, mostly export model numbers with a few Japanese domestic ones (for example Corona CSH-N series); geo-tp/Ultimate-Remote targets the M5Cardputer and states 3498 profiles from 636 manufacturers with Flipper-IRDB file compatibility, and its README does not mention air conditioners or Japanese brands. Unverified parts: the statement that hotel rooms often use central systems or wired wall panels rests on a blog I could not locate or open, and no measured success rate exists, so the reliability judgement stays a low-confidence opinion. Additional hardware limit the claim omits: on every variant the IR LED is driven straight from a GPIO through 22 Ohm with no transistor, and the documented on-axis range is 4.1 m falling to 0.66 m at 90 degrees, so aiming matters. The device cannot learn codes because it has no receiver. Treat IR as a playful extra, not a dependable feature.
- Source: <https://github.com/crankyoldgit/IRremoteESP8266/blob/master/SupportedProtocols.md>
- Source: <https://github.com/geo-tp/Ultimate-Remote>
- Source: <https://raw.githubusercontent.com/crankyoldgit/IRremoteESP8266/master/SupportedProtocols.md>
- Source: <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/481/Sch_M5Cardputer.pdf>
- Source: <https://docs.m5stack.com/en/core/Cardputer>

### ir-04 · confirmed

Common Japanese labels on air-conditioner remotes include 運転 (unten, run), 停止 (teishi, stop), 入/切 (on/off), 冷房 (reibou, cooling), 暖房 (danbou, heating), 除湿 or ドライ (joshitsu, dehumidify), 送風 (soufuu, fan only), 自動 (jidou, auto), 温度 (ondo, temperature), 風量 (fuuryou, fan strength), 風向 (fuukou or kazamuki, airflow direction), タイマー (timer), 入タイマー and 切タイマー (on and off timer), 省エネ (energy saving).

- Applies to: All variants (learning content, independent of hardware)
- Correction: Confirmed against the Coto Academy article (a language school blog, supporting evidence only); every listed label appears there, and the article does write 'Ondou' for 温度, which the researcher correctly normalised to ondo. Small additions: on remotes 入 and 切 are read iri and kiri, so 入タイマー and 切タイマー are iri taimaa and kiri taimaa; the article gives 送風 as 'Soufu' where the standard reading is soufuu. Other labels in the same article worth adding to learning content: 自動運転, 強風, 弱風, 静か, 空気清浄, 内部クリーン, 衣類乾燥, スイング, 取り消し.
- Source: <https://cotoacademy.com/how-to-use-your-japanese-air-conditioner-remote/>

## Found by the fact-check

- The giteki question can be settled by reading one sticker. MIC publishes photographs with each certification record, and the Cardputer Adv sample's Stamp S3A sticker reads 'Model Name: M5Cardputer', 'FCC ID: 2AN3WM5CARDPUTER' and the giteki mark 'R 219-249271'. The mark is on the Stamp module sticker, not on the large back label. The owner should photograph that sticker on first unboxing: a visible mark with 219-249271 or 219-259647 means the 90-day rule and its restrictions are not needed. Source: https://www.tele.soumu.go.jp/giteki/SearchServlet?pageID=jg01_01&PC=219&TC=N&PK=1&FN=251128N219&SN=%E8%AA%8D%E8%A8%BC&LN=72&R1=*****&R2=***** (attachment 219-259647_01_002.pdf).
- Certified transmit power is far below ESP32-S3 firmware defaults, which the researcher did not address although the brief asked about transmit power. Certified values from the MIC database: Cardputer Adv BLE 1.5 mW and Wi-Fi 1.0, 0.5, 0.5, 0.3 mW/MHz (11b, 11g, HT20, HT40); 'Cardputer' 219-249271 BLE 1 mW and Wi-Fi 1 mW/MHz; StampS3A 1.5 mW and 1.5 mW/MHz (https://www.tele.soumu.go.jp/giteki/list?SC=1&OF=2&DC=1&TN=Cardputer). ESP-IDF documents a default BLE transmit power of ESP_PWR_LVL_P9, plus 9 dBm, about 7.9 mW (https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/bluetooth/controller_vhci.html) and a Wi-Fi maximum transmit power range of 2 to 20 dBm (https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/network/esp_wifi.html). The certification test reports show the units were tested with reduced-power tool settings (Wi-Fi parameter 45 for the Adv, 30 and 28 for the Cardputer; BLE parameter 9 and 8). My interpretation, not a sourced legal ruling: firmware that wants to stay inside the certified design should cap Wi-Fi at roughly 8 to 10 dBm and BLE at 0 to 3 dBm. The general Japanese ceiling quoted in the test reports is 10 mW/MHz, so default power is not over the legal limit, only over the certified rating.
- Japan changed its aircraft power bank rules on 24 April 2026. The Ministry of Land, Infrastructure, Transport and Tourism notice says: no power banks in checked baggage, none over 160 Wh, not in overhead compartments, and new from 24 April 2026 a maximum of two power banks per passenger, no charging of power banks from aircraft power, and 'Do NOT use power banks to charge other electronic devices during the flight'. The Cardputer therefore cannot be topped up from a power bank in the air on flights under Japanese rules; charge it fully before boarding. Source: https://www.mlit.go.jp/koku/content/001998101.pdf (linked from https://www.mlit.go.jp/koku/koku_fr2_000007.html).
- The watt-hour rating is not visible from outside any Cardputer. IATA states that lithium-ion batteries must have the watt-hour rating marked on the case and that if staff cannot verify it from the battery or the user documentation 'the operator may not permit the carriage' (https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passengers_travelling_with_lithium_batteries.pdf). On the Cardputer the rating is printed only on the cells inside (Adv 6.475 Wh; original-type base cell 5.18 Wh, the 120 mAh cell has no watt-hour marking) and the external label shows only mAh. Carry a saved copy of the M5Stack product page and, for the Adv, the IEC 62133 report (https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/certification/K132-Adv/IEC62133/IEC62133-Report.pdf).
- Charging is slow on every variant and competes with the running firmware. All three schematics show a TP4057 linear charger with a 3.3 kOhm programming resistor, which the datasheet formula puts at about 0.3 A, no fitted charge LED, and a battery path that only connects through the power switch. With the device necessarily switched on, whatever the firmware draws is subtracted from the charge current. The firmware should offer a charging screen with backlight low and radios off, and the traveller should plan overnight charging. Battery voltage is available to firmware on G10 through a 100k/100k divider. Sources: https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/Sch_M5CardputerAdv_v1.0_2025_06_20_17_19_58.pdf , https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/481/Sch_M5Cardputer.pdf , https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1811151533_TOPPOWER-Nanjing-Extension-Microelectronics-TP4057_C12044.pdf
- The default PlatformIO toolchain and M5Stack's current examples are on different Arduino core generations. The official platform-espressif32 v7.1.3 pins Arduino core 2.0.17 (https://raw.githubusercontent.com/platformio/platform-espressif32/v7.1.3/platform.json), while M5Stack's official Cardputer IR example requires M5Stack Board Manager 3.2.2 or later and M5Cardputer library 1.1.0 or later (https://docs.m5stack.com/en/arduino/m5cardputer/ir_nec). Arduino core 3.x under PlatformIO needs the community pioarduino platform (https://github.com/pioarduino/platform-espressif32/releases). This choice decides which IR library version works (IRremoteESP8266 2.8.6 on core 2.x, 2.9.0 on core 3.x) and should be made before any firmware work starts.
- The Japan Tourism Agency results PDF gives concrete targets for learning content that the press release summary does not. Trouble with multilingual signage occurred most in railway station premises and restaurants (24 percent each of 446 respondents); city-only visitors named stations most (30 percent), rural-only visitors named restaurants (23 percent). The main complaint was signage not being multilingual at all (67 percent). For transport, the hardest tasks were finding a route to the destination (45 percent) and locating the boarding or alighting point (38 percent); the problem mode was non-Shinkansen rail in cities (73 percent) and buses in rural areas (42 percent). This argues for prioritising station, bus and menu reading vocabulary over general conversation. Sources: https://www.mlit.go.jp/kankocho/content/001998584.pdf and https://www.mlit.go.jp/kankocho/news08_00039.html
- Restaurant ordering in Japan is increasingly done without speaking, which changes what a phrase tool should cover. Japan Guide (updated 1 June 2025) says 'ordering through a tablet computer or touch screen at the table or through one's own mobile phone after scanning a QR code has become common', that some restaurants use meal-ticket vending machines at the entrance, that staff are called with 'sumimasen' or a call button, that 'others may have only Japanese menus', and that the bill is usually paid at a cashier near the exit. Reading practice for ticket machine and menu kanji is likely more useful than spoken ordering scripts. Source: https://www.japan-guide.com/e/e2040.html
- Only the Cardputer-Adv is still on sale, which narrows the unknown variant. Switch Science lists the original K132 as discontinued (released 2023-10-13), v1.1 as sold out and scheduled for discontinuation (released 2025-03-31), and the Adv as in stock (released 2025-09-22); M5Stack's own shop marks v1.1 as EOL and points to the Adv. A unit bought in the last year is most likely an Adv, the only variant with a headphone jack, which matters because speaker audio is unsuitable on trains. Sources: https://www.switch-science.com/products/9277 , https://www.switch-science.com/products/10300 , https://www.switch-science.com/products/10737 , https://shop.m5stack.com/products/m5stack-cardputer-with-m5stamps3-v1-1
- Verification limit for the decision maker: the session's web search allowance was exhausted before this check began, so everything above was verified by opening known primary URLs directly. Three items remain unverified for that reason and should not be relied on: the Android hotspot 2.4 GHz band setting, the prevalence of captive portals and central air conditioning in Japanese hotels, and whether Espressif's Wi-Fi Alliance or Bluetooth SIG listings would satisfy MIC's logo condition for a Cardputer without a giteki mark. The MIC leaflet that sets the logo condition is at https://www.tele.soumu.go.jp/resource/j/others/wifi/en.pdf

## What this means for the design

- Build the core experience to work fully offline from the microSD card. Connectivity on the trip depends on a phone hotspot that sleeps, so treat the network as an occasional sync or lookup channel, never a requirement for the main study loop.
- Pre-compute on the Mac before departure: phrase decks grouped by the situations the Japan Tourism Agency survey flags (restaurants first, then stations and bus terminals, then shops and lodging), signage and kanji-reading drills (menus, ticket machines, station signs, remote control labels), and any audio clips. Signage reading deserves as much weight as speaking.
- Keep Wi-Fi firmware conservative: station mode with standard 802.11b/g/n, channels 1-13 only, no channel 14, no Espressif Long Range mode, no BLE coded PHY, and do not raise transmit power above defaults. Prefer avoiding ESP-NOW since there is no second device to talk to anyway.
- Do not build features that scan, sniff, deauthenticate or otherwise transmit outside ordinary client behaviour. Many popular Cardputer firmwares include such tools; keep them off the device for this trip.
- For tethering, add a keep-alive (a small request at under 90 second intervals while online) and automatic reconnect, and show a clear on-screen hint telling the user to open the iPhone Personal Hotspot screen with Maximize Compatibility on. Disconnect Wi-Fi when idle to save battery: Wi-Fi draw is about 130 mA on the Adv.
- Do not plan on hotel or public Wi-Fi with a login page. Offer only WPA2 password networks and the phone hotspot in the Wi-Fi picker, and do not attempt to get round captive portals.
- Skip a Bluetooth LE internet bridge for a first version if the phone is an iPhone, since it needs a native iOS app. It is only cheap on Android via Web Bluetooth in Chrome.
- Make every feature usable silently: text first, audio optional and off by default, with a visible mute state. Audio listening practice on trains is realistic only on the Cardputer-Adv with headphones; on the original and v1.1 there is no headphone jack.
- Treat the infrared remote as a playful bonus that teaches remote-control vocabulary. Design it as a labelled Japanese button panel (運転, 停止, 冷房, 暖房, 温度) with a brand picker that tries protocols in turn, and set expectations that it may not work in a given room. Because there is no infrared receiver, codes cannot be learned on the spot.
- Pin library versions in PlatformIO: IRremoteESP8266 2.9.0 or later if the build uses Arduino core 3.x, or use Arduino-IRremote as in M5Stack's own example for simple television codes.
- Pack for power: a 100-240 V USB charger with a Type A plug or adapter and a USB-C cable. Remind the user that the power switch must be ON to charge and that the original model has no charging light, so show battery voltage in the user interface.
- Carry the Cardputer in hand luggage, switched off with the physical switch. Keep a copy of the battery rating to hand (6.475 Wh for the Adv from the IEC report) in case airline staff ask.

## Not settled

- Does a Cardputer v1.1 unit carry a giteki mark and number on its case, label or packaging, and does certification 219-249271 ('Cardputer') legally extend to the v1.1 hardware with its different StampS3A antenna? The MIC database has no separate v1.1 entry and M5Stack lists only RoHS for it.
- Does the certification remain valid in practice when the owner flashes custom firmware? The certificates list software version as N/A or v0.2 and certify the hardware design; I found no MIC statement on user-flashed firmware for certified modules.
- Do the default ESP-IDF and Arduino core transmit power settings stay within the certified power density values (for example 0.5 to 1.5 mW/MHz)? I could not find the test configuration used for certification.
- What channel range does the ESP32 driver apply when the country code is explicitly set to 'JP' in current ESP-IDF and Arduino core 3.x? I could only verify default behaviour from the v5.1 documentation.
- Whether ESP-NOW frames fall within the certified emission designators in the regulator's view. No source found.
- Actual charge current and charge time for each variant, and whether USB-C to USB-C charging from Power Delivery chargers works in practice as the schematics imply. Forum measurements of 62 mA conflict with the 3.3 kΩ PROG resistor on the original schematic.
- How common captive portals are on Japanese hotel Wi-Fi compared with simple WPA2 passwords. No quantitative source found.
- What share of Japanese hotel rooms have infrared-controllable air conditioners, and how well IRremoteESP8266 or Flipper-IRDB files cover Japanese domestic models. No measured data found; reliable market share figures by brand were also not found from a primary source.
- Etiquette for using small electronic devices in restaurants in Japan. I found no reputable source addressing this specifically.
- Which Arduino core version the PlatformIO espressif32 platform installs by default at present, which determines whether IRremoteESP8266 2.8.6 or 2.9.0 is needed. Not verified in this facet.
- Whether a newer Cardputer variant than the Adv exists as of September 2026. The M5Stack certification page and MIC database showed only the variants named here.
