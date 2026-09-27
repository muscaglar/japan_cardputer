// The words of the USB console that fill the memory card. A computer sends the sound clips over
// the cable, so that the card can stay in the device: tools/sd_sync.py is the other side.
//
//   df                       "#df <bytes total> <bytes used>"
//   ls <folder>              one line per entry, "#file <size> <name>" or "#dir <name>", then
//                            "#end <count>". The size is "?" for a file that cannot be opened.
//   crc <path>               "#crc <8 hex digits> <size>": the CRC-32 of the file as zlib computes it
//   rm <path>                "#ok". Removes a file, or a folder with all that is in it. Not "/".
//   mkdir <path>             "#ok". Makes the folder and the folders above it.
//   put <path> <size> <crc>  "#ready <piece>". The computer then sends the bytes of the file as
//                            they are, in pieces of <piece> bytes, the last one shorter, and waits
//                            after each piece for "#got <bytes so far>". At the end "#done <crc>".
//
// Every word may answer "#error <why>" instead, and with no card in every one answers
// "#error no card". No word sends what a file holds: the card may hold a key.
//
// Paths start with "/", hold no "..", no "//" and no name that is a single ".", do not end in
// "/" unless they are "/" itself, are at most 120 letters long and consist of letters, digits
// and / . _ - only. Anything else is "#error bad path".
//
// A file that arrives is written as /incoming.part and gets its name when it is whole and its
// CRC-32 is the one announced, so that a clip is never half there. Until then the device does
// nothing else. It gives up after three seconds without a byte; whatever goes wrong, the part
// is removed. An error is only ever answered where the computer waits for an answer, so that the
// bytes of a file are never taken for words.
#pragma once

#include <string>

// Carries out the word and answers through reply. false, and no answer, if the word is not one
// of those above.
bool filesCarryOut(const std::string& word, const std::string& rest, void (*reply)(const char*));
