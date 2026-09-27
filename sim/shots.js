// Runs key sequences through the simulator and writes each resulting screen as a PNG.
//
//   node sim/shots.js                       writes docs/screens/*.png
//   node sim/shots.js --out /tmp/shots      writes elsewhere
//   node sim/shots.js --check               compares with docs/screens and reports differences
//
// Scenarios are in sim/scenarios.json. Keys: a plain string types its characters; names in
// angle brackets are special keys, e.g. "<Enter>", "<Tab>", "<Esc>", "<Up>", "<Fn+r>".
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const ROOT = path.dirname(__dirname);
const WIDTH = 240, HEIGHT = 135;
const CODES = { None: 0, Char: 1, Enter: 2, Backspace: 3, Tab: 4, Up: 5, Down: 6, Left: 7, Right: 8, Esc: 9, Button: 10 };

function crc32(buffer) {
  let c, crc = 0xffffffff;
  for (let n = 0; n < buffer.length; n++) {
    c = (crc ^ buffer[n]) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const length = Buffer.alloc(4); length.writeUInt32BE(data.length);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
}

function png(rgba, scale) {
  const w = WIDTH * scale, h = HEIGHT * scale;
  const raw = Buffer.alloc((w * 3 + 1) * h);
  let o = 0;
  for (let y = 0; y < h; y++) {
    raw[o++] = 0;
    const sy = Math.floor(y / scale);
    for (let x = 0; x < w; x++) {
      const i = (sy * WIDTH + Math.floor(x / scale)) * 4;
      raw[o++] = rgba[i]; raw[o++] = rgba[i + 1]; raw[o++] = rgba[i + 2];
    }
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(w, 0); header.writeUInt32BE(h, 4);
  header[8] = 8; header[9] = 2; header[10] = 0; header[11] = 0; header[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", header), chunk("IDAT", zlib.deflateSync(raw, { level: 9 })), chunk("IEND", Buffer.alloc(0)),
  ]);
}

function send(sim, token) {
  const special = /^<(.+)>$/.exec(token);
  if (!special) {
    for (const ch of token) sim._sim_key(CODES.Char, ch.charCodeAt(0), 0);
    return;
  }
  let name = special[1], mods = 0;
  if (name.startsWith("Fn+")) { mods |= 1; name = name.slice(3); }
  if (name in CODES) sim._sim_key(CODES[name], 0, mods);
  else if (name.length === 1) sim._sim_key(CODES.Char, name.charCodeAt(0), mods);
  else throw new Error("unknown key " + token);
}

async function main() {
  const args = process.argv.slice(2);
  const check = args.includes("--check");
  const outIndex = args.indexOf("--out");
  const golden = path.join(ROOT, "docs", "screens");
  const out = outIndex >= 0 ? args[outIndex + 1] : (check ? fs.mkdtempSync(path.join(require("os").tmpdir(), "shots-")) : golden);
  fs.mkdirSync(out, { recursive: true });

  const createSim = require(path.join(ROOT, "build", "sim", "sim.js"));
  const scenarios = JSON.parse(fs.readFileSync(path.join(__dirname, "scenarios.json"), "utf8"));
  let failed = 0;

  for (const scenario of scenarios) {
    const sim = await createSim();
    sim._sim_init(scenario.seed || 1, 0);
    for (const token of scenario.keys || []) {
      send(sim, token);
      sim._sim_advance(50);
    }
    sim._sim_render();
    const pointer = sim._sim_pixels();
    const rgba = Buffer.from(sim.HEAPU8.subarray(pointer, pointer + WIDTH * HEIGHT * 4));
    const file = path.join(out, scenario.name + ".png");
    fs.writeFileSync(file, png(rgba, 3));
    if (check) {
      const reference = path.join(golden, scenario.name + ".png");
      if (!fs.existsSync(reference)) {
        console.log("NEW      " + scenario.name + " (no reference yet)");
        failed++;
      } else if (!fs.readFileSync(reference).equals(fs.readFileSync(file))) {
        console.log("CHANGED  " + scenario.name + "  see " + file);
        failed++;
      } else {
        console.log("same     " + scenario.name);
      }
    } else {
      console.log("wrote " + path.relative(ROOT, file));
    }
  }
  if (check && failed) {
    console.log(failed + " screen(s) differ from docs/screens. Look at them; if the change is intended, run: node sim/shots.js");
    process.exit(1);
  }
}

main().catch(error => { console.error(error); process.exit(1); });
