// Drives the simulator from another program, one command per line on standard input.
//   init <seed>            start a fresh device
//   key <name>             a special key: Enter, Backspace, Tab, Up, Down, Left, Right, Esc, Button
//   fn <character>         a character typed with Fn held
//   type <text>            characters, one key each (the rest of the line, spaces included)
//   wait <milliseconds>    let time pass
//   frame                  answers with one line: "frame <screen number> <base64 of 240x135 RGBA>"
//   info                   answers with one line: "info <JSON>"
//   restart                switches off and on again: the app starts anew, its files stay
//   keep / back            keeps settings and progress aside / brings them back; answers "done 1" or "done 0"
//   fresh                  forgets all progress and starts at day 1; answers "done 1"
//   card in / card out     puts the pretended memory card in or takes it out
//   sitting <deck id>      starts a sitting from that deck; without a name, the course; answers "done 1" or "done 0"
//   quit
const path = require("path");
const readline = require("readline");

const CODES = { Char: 1, Enter: 2, Backspace: 3, Tab: 4, Up: 5, Down: 6, Left: 7, Right: 8, Esc: 9, Button: 10 };

require(path.join(path.dirname(__dirname), "build", "sim", "sim.js"))().then(sim => {
  sim._sim_init(1, 0);
  const lines = readline.createInterface({ input: process.stdin });
  lines.on("line", line => {
    const space = line.indexOf(" ");
    const command = space < 0 ? line : line.slice(0, space);
    const rest = space < 0 ? "" : line.slice(space + 1);
    if (command === "init") {
      sim._sim_init(parseInt(rest, 10) || 1, 0);
    } else if (command === "key") {
      if (!(rest in CODES)) { console.log("error unknown key " + rest); return; }
      sim._sim_key(CODES[rest], 0, 0);
    } else if (command === "fn") {
      sim._sim_key(CODES.Char, rest.charCodeAt(0), 1);
    } else if (command === "type") {
      for (const ch of rest) sim._sim_key(CODES.Char, ch.charCodeAt(0), 0);
    } else if (command === "wait") {
      sim._sim_advance(parseInt(rest, 10) || 0);
    } else if (command === "frame") {
      sim._sim_advance(20);
      sim._sim_render();
      const at = sim._sim_pixels();
      const pixels = Buffer.from(sim.HEAPU8.subarray(at, at + 240 * 135 * 4));
      console.log("frame " + sim._sim_screen() + " " + pixels.toString("base64"));
    } else if (command === "info") {
      console.log("info " + sim.UTF8ToString(sim._sim_info()));
    } else if (command === "restart") {
      sim._sim_restart();
    } else if (command === "keep" || command === "back" || command === "fresh") {
      console.log("done " + sim._sim_keep(command === "keep" ? 0 : command === "back" ? 1 : 2));
    } else if (command === "sitting") {
      const at = sim.stringToNewUTF8(rest);
      console.log("done " + sim._sim_sitting(at));
      sim._free(at);
    } else if (command === "card") {
      sim._sim_card(rest === "out" ? 0 : 1);
    } else if (command === "quit") {
      process.exit(0);
    } else if (command) {
      console.log("error unknown command " + command);
    }
  });
  lines.on("close", () => process.exit(0));
});
