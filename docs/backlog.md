# Backlog

The eighteen ideas are all wanted and are built in the stages listed in the README. This file
holds what two independent reviews added on 27 September 2026: one by the standards of an embedded
engineer, one by those of a Japanese teacher. Nothing here is decided.

## Suggested additions

| Idea | What it is | Needs |
|---|---|---|
| Keigo decoder | Maps what staff say onto forms the learner knows: お持ちですか is 持っていますか, ございます is あります. About thirty patterns. | text only |
| Particle and conjugation gaps | Sentences with one gap and one right answer, which the device can mark reliably: 京都＿行きたいんですが. | text only |
| Conjugation gym | Typed て-form, past, negative and potential forms in the same card format as the counters. | text only |
| Machine screens | A ramen ticket machine, a fare adjustment machine and a tablet order as a sequence of Japanese screens, worked with number keys. | text only |
| Directions by ear | Hear まっすぐ行って、二つ目の信号を右に, then choose the route. | audio |
| Beat line and length pairs | The beat count on every card, and a listening drill of pairs such as びょういん and びよういん. Timing causes more misunderstandings than pitch. | audio |
| Pitch pairs by ear | 箸, 橋, 端: hear one and choose. Already drawn as a concept screen. | audio |
| Questions you will be asked | どちらからですか, 日本は初めてですか, with the owner's own answers prepared in advance. | text, audio |
| Eyes-free loop | Screen off, three keys: replay, next, mark. For walking with earphones; also saves battery. | audio, ADV |
| Forms pack | The fields of a hotel registration card and the owner's name in katakana. | text only |
| Emergency pack | Alert words, a few fixed sentences and emergency numbers, as fixed and checked content. | text only |
| QR hand-off | The diary or a caught word as a QR code for the phone to scan. M5GFX can draw one. | none |
| Start from known words | Import words already known from a desktop flashcard program, export caught words back. | a computer |
| Example sentences offline | Tatoeba links sentences to dictionary entries, so examples need no connection. Attribution per sentence. | microSD |
| Large stroke view | KanjiVG strokes fit the screen height 1:1 and cover kanji the 32 px font lacks. | microSD |
| Charging screen | Backlight at minimum and radios off while charging, which is slow and only works with the switch ON. | none |
| Recovery kit | The current build, one older known-good build and a launcher image on the card. | microSD |

## Points the reviews corrected

| Topic | What to do |
|---|---|
| Clock | No model has a clock chip. The day number is confirmed by the owner at the first start of the day, and taken from the network when there is one. |
| Navigation keys | Single unmodified keys first: Space, Enter, Tab, digits, and the bare `;` `,` `.` `/`. The arrows behind Fn are an extra. |
| Particles | は, を and へ are typed ha, wo, he. Marking accepts wa, o and e for particles and shows the written form in the feedback. |
| Large kanji | The 32 px font lacks menu kanji such as 餃 and 鮪. Words that need them are drawn with the 16 px font doubled, or later from stroke data. |
| Fixed reply sets | Replies are written per staff line. はい、お願いします does not answer 何名様ですか. |
| Counters | "Beer x 3" has more than one right answer depending on the container. Accepted answers are listed per item. |
| Study and sync | Wi-Fi is never started in study mode. Syncing is a separate mode, so that memory is unfragmented for the one secure connection. Each sync joins, transacts and leaves. |
| Sound formats | WAV through the library's own speaker class. MP3 would need a GPL library pinned to an old version. |
| Key on the card | Readable by whoever finds the device. Limit the damage with a dedicated workspace, a monthly cap and an expiry date; a relay that holds the key is the stronger option. |
| Pronunciation scoring | No service scores Japanese pitch. One scores sounds and fluency. Timing and beats can be shown from the kana alone. |
