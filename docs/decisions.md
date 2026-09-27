# Decisions

Settled on 27 September 2026. Each line is a choice the design now depends on.

| Topic | Decision | What follows from it |
|---|---|---|
| Scope | Generic, not tuned to one trip | No dates, routes or seasonal content are built in. The built-in decks cover travel in Japan in general. Day packs are an optional feature that works from any itinerary. |
| Device | Cardputer ADV | Headphone socket, ES8311 audio codec, 1,750 mAh battery. One firmware still runs on the older models. |
| Ideas | All eighteen | Built in the stages listed in the README. |
| Level | Kana is shaky | Nothing is assumed: the course starts with hiragana, every kanji comes with its reading, romaji is one key away. |
| Goals | Listening and speaking first | Stage 2 (sound) follows straight after the first typed cards. |
| Sound in public | Wired earphones | Listening drills are designed for use on a platform or train. The speaker stays off unless switched on. |
| Pitch notation | Line and hook | A line over the high beats, a hook where the pitch falls. |
| Romaji | Hidden, one key shows it | Peeking is counted, so the scheduler knows when kana was not enough. |
| Model voice | Alternating female and male | Two voices per clip set. |
| Look | Notebook by default | Station sign, game windows and paper-and-vermilion ship as selectable themes. |
| Typing | No IME habits | Textbook romaji is the default: `minna` gives みんな, `kin'en` gives きんえん. |
| Online | iPhone hotspot, evenings | The hotspot needs Maximise Compatibility. Everything else works offline. |
| Claude | Personal key on the card | The key lives in its own workspace with a monthly cap and an expiry date. It is read from the card, never compiled in. |
| Builds | In the cloud | GitHub Actions builds every push and publishes the image as the `latest` release. `tools/flash.py` writes it to the device. |
| microSD | Larger than 32 GB | To be formatted as FAT32 with an MBR partition table before first use. |
| Show cards | No allergy or medical cards needed | Show cards cover ordinary requests only. |
| Company | Travelling with a non-speaker | Missions assume the owner speaks for two. |
| Long-term use | Keep studying with it | A general scheduler with long intervals, not one tuned to a two-week stay. Words can be exported for a desktop flashcard program. |
| Add-ons | None | No GPS: the station quiz runs in line mode, and caught words are stamped with time only. |
| Language of the controls | English | Decided on the device, 27 September 2026: labels, menus, hints and settings are in English, so that someone with little or no Japanese can use it. Japanese is what is learnt, never what steers. |
| Size of text | Nothing under 16 px | Decided on the device the same day: 12 px is 1.3 mm on this screen. Readings and typed answers are 24 px, prompts 32 px, single kana 64 px. |
| Help | One key, Tab | First the romaji, then the answer. After a mark it shows the note. |
| microSD, as found | The 122 GB card mounted as it was | No reformatting was needed on the owner's device. |
| Where it begins | With the kana, a few at a time | Asked on the device, 27 September 2026: cards assumed that characters and their sounds were known. The course now takes hiragana first, then katakana with numbers and counters, then words. A kana is asked before it is taught, so that what is known costs one answer. |
| What kanji mean | On the card of every word | One meaning per kanji, from KANJIDIC, chosen to explain the words in the decks. Where the characters do not explain a word, the card says so in its own line or shows none. |
| How it sounds | A guide of twelve pages, and every card spoken | The guide explains the sounds and the line over a reading once; the clips let every answer be heard. |
| Clips | Made on a computer, kept out of the repository | The voices of the operating system are licensed for personal use. `tools/make_audio.py` makes them, measures them and marks what it doubts. |
| Place on the card | One folder, `/nihongo` | Asked for by the owner: the card holds other things, and the app's files are to stay apart from them. |
| Filling the card | Over the USB cable | The card stays in the device. The device takes files but never gives their content back, because the card will hold a key. |
