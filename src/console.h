// Lets a computer on the USB cable press keys and read the screen, so that the app can be
// checked on the real device by a program. It listens on the serial port and does nothing until
// a command arrives. Compiled in unless DEVICE_CONSOLE is defined as 0.
//
// Commands, one per line (the same words the simulator's driver uses):
//   key <name>      Enter, Backspace, Tab, Up, Down, Left, Right, Esc, Button
//   fn <character>  a character with Fn held
//   type <text>     the rest of the line, one key per character
//   frame           answers "#frame <screen> <width> <height> <base64>": the picture in runs of
//                   equal colour, each run three bytes: length, then the colour as the panel
//                   gets it (16 bit, high byte first)
//   info            answers "#info {...}" with the state of the app and the memory left
//   keep, back      keeps settings and progress aside, brings them back: "#done 1" or "#done 0"
//   fresh           forgets all progress and starts at day 1. Refused unless "keep" was done.
//   restart         restarts the device
// Every other command is answered with "#ok" or "#error <why>".
#pragma once

#include <M5GFX.h>

#include "app.h"

#ifndef DEVICE_CONSOLE
#define DEVICE_CONSOLE 1
#endif

// Reads what has arrived and carries out complete lines. Returns true if the app was given a key.
bool consolePoll(ui::App& app, M5Canvas& canvas, ui::Platform& platform);
