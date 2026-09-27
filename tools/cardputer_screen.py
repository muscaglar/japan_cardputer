#!/usr/bin/env python3
"""Pixel-exact preview of the Cardputer screen on a computer.

Draws 240x135 screens with the same bitmap fonts the firmware uses (the u8g2-format Japanese
fonts bundled with M5GFX), decoded with the same algorithm, and writes PNG files. What this
renders is what the panel shows, pixel for pixel, so screen designs and font sizes can be judged
before anything is flashed.

Needs the M5GFX sources that PlatformIO downloads into .pio/libdeps (run `pio pkg install`).
Uses only the Python standard library.
"""
import os
import re
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, ".pio", "libdeps", "cardputer", "M5GFX", "src", "lgfx", "Fonts")
CACHE_DIR = os.path.join(ROOT, ".pio", "fontcache")

WIDTH = 240
HEIGHT = 135

# firmware name -> (source file, array name)
FONT_SOURCES = {}
for _size in (10, 12, 14, 16, 24):
    for _suffix in ("", "_b", "_i", "_bi"):
        FONT_SOURCES["efontJA_%d%s" % (_size, _suffix)] = ("efont/lgfx_efont_ja.c", "lgfx_efont_ja_%d%s" % (_size, _suffix))
for _size in (8, 12, 16, 20, 24, 28, 32, 36, 40):
    FONT_SOURCES["lgfxJapanGothic_%d" % _size] = ("IPA/lgfx_font_japan.c", "lgfx_font_japan_gothic_%d" % _size)
    FONT_SOURCES["lgfxJapanGothicP_%d" % _size] = ("IPA/lgfx_font_japan.c", "lgfx_font_japan_gothic_p_%d" % _size)
    FONT_SOURCES["lgfxJapanMincho_%d" % _size] = ("IPA/lgfx_font_japan.c", "lgfx_font_japan_mincho_%d" % _size)
    FONT_SOURCES["lgfxJapanMinchoP_%d" % _size] = ("IPA/lgfx_font_japan.c", "lgfx_font_japan_mincho_p_%d" % _size)

_ESCAPES = {"n": 10, "r": 13, "t": 9, "a": 7, "b": 8, "f": 12, "v": 11, "\\": 92, '"': 34, "'": 39, "?": 63}


def _extract_arrays(path):
    """Yields (name, bytes) for every byte array defined in a C source file."""
    source = open(path, encoding="latin-1").read()
    n = len(source)
    for match in re.finditer(r"const\s+(?:uint8_t|unsigned char)\s+(\w+)\s*\[\s*\d*\s*\][^=;]*=\s*", source):
        name = match.group(1)
        k = match.end()
        data = bytearray()
        if source[k] == "{":
            end = source.index("}", k)
            for token in re.findall(r"0[xX][0-9a-fA-F]+|\d+", source[k + 1:end]):
                data.append(int(token, 0))
        else:
            while k < n:
                c = source[k]
                if c == '"':
                    k += 1
                    while source[k] != '"':
                        ch = source[k]
                        if ch == "\\":
                            k += 1
                            e = source[k]
                            if e in "01234567":
                                octal = e
                                while len(octal) < 3 and source[k + 1] in "01234567":
                                    k += 1
                                    octal += source[k]
                                data.append(int(octal, 8) & 0xFF)
                            elif e == "x":
                                digits = ""
                                while source[k + 1] in "0123456789abcdefABCDEF":
                                    k += 1
                                    digits += source[k]
                                data.append(int(digits, 16) & 0xFF)
                            else:
                                data.append(_ESCAPES[e])
                        else:
                            data.append(ord(ch))
                        k += 1
                    k += 1
                elif c == ";":
                    break
                else:
                    k += 1
        yield name, bytes(data)


def _font_bytes(name):
    if name not in FONT_SOURCES:
        raise KeyError("unknown font %r" % name)
    relative, array = FONT_SOURCES[name]
    cached = os.path.join(CACHE_DIR, array + ".bin")
    if not os.path.exists(cached):
        source = os.path.join(FONT_DIR, relative)
        if not os.path.exists(source):
            raise SystemExit("M5GFX sources not found. Run: pio pkg install -e cardputer")
        os.makedirs(CACHE_DIR, exist_ok=True)
        for array_name, data in _extract_arrays(source):
            with open(os.path.join(CACHE_DIR, array_name + ".bin"), "wb") as handle:
                handle.write(data)
    # The C arrays are string literals, so their final zero bytes (the end-of-font marker) are implicit.
    return open(cached, "rb").read() + b"\x00\x00\x00\x00"


def _int8(value):
    return value - 256 if value > 127 else value


class _Bits:
    def __init__(self, data, position):
        self.data = data
        self.position = position
        self.bit = 0

    def unsigned(self, count):
        bit = self.bit
        value = self.data[self.position] >> bit
        total = bit + count
        if total >= 8:
            total -= 8
            self.position += 1
            value |= self.data[self.position] << (8 - bit)
        self.bit = total
        return value & ((1 << count) - 1)

    def signed(self, count):
        return self.unsigned(count) - (1 << (count - 1))


class Font:
    """One u8g2-format font, decoded the way lgfx::U8g2font does it."""

    def __init__(self, name):
        self.name = name
        d = self.data = _font_bytes(name)
        self.bits_per_0 = d[2]
        self.bits_per_1 = d[3]
        self.bits_width = d[4]
        self.bits_height = d[5]
        self.bits_x = d[6]
        self.bits_y = d[7]
        self.bits_delta = d[8]
        self.max_width = _int8(d[9])
        self.height = _int8(d[10])
        self.y_offset = _int8(d[12])
        self.baseline = self.height + self.y_offset
        self.start_upper = (d[17] << 8) | d[18]
        self.start_lower = (d[19] << 8) | d[20]
        self.start_unicode = (d[21] << 8) | d[22]
        self._glyphs = {}

    def _find(self, code):
        d = self.data
        p = 23
        if code <= 255:
            if code >= ord("a"):
                p += self.start_lower
            elif code >= ord("A"):
                p += self.start_upper
            while d[p + 1]:
                if d[p] == code:
                    return p + 2
                p += d[p + 1]
            return None
        p += self.start_unicode
        table = p
        while True:
            p += (d[table] << 8) + d[table + 1]
            last = (d[table + 2] << 8) + d[table + 3]
            table += 4
            if last >= code:
                break
        while True:
            e = (d[p] << 8) + d[p + 1]
            if e == 0:
                return None
            if e == code:
                return p + 3
            p += d[p + 2]

    def glyph(self, code):
        """Returns (width, height, x, y, advance, rows) or None when the font has no such glyph."""
        if code in self._glyphs:
            return self._glyphs[code]
        position = self._find(code) if code <= 0xFFFF else None
        if position is None:
            self._glyphs[code] = None
            return None
        bits = _Bits(self.data, position)
        w = bits.unsigned(self.bits_width)
        h = bits.unsigned(self.bits_height)
        x = bits.signed(self.bits_x)
        y = bits.signed(self.bits_y)
        advance = bits.signed(self.bits_delta)
        rows = [[0] * w for _ in range(h)]
        if w > 0 and h > 0:
            lx = ly = 0
            while ly < h:
                runs = (bits.unsigned(self.bits_per_0), bits.unsigned(self.bits_per_1))
                while True:
                    for ink in (0, 1):
                        length = runs[ink]
                        while length:
                            step = min(length, w - lx)
                            length -= step
                            if ink and ly < h:
                                row = rows[ly]
                                for column in range(lx, lx + step):
                                    row[column] = 1
                            lx += step
                            if lx == w:
                                lx = 0
                                ly += 1
                    if bits.unsigned(1) == 0:
                        break
        result = (w, h, x, y, advance, rows)
        self._glyphs[code] = result
        return result

    def has(self, character):
        return self.glyph(ord(character)) is not None

    def advance(self, character):
        g = self.glyph(ord(character))
        return g[4] if g else self.max_width

    def width(self, text):
        return sum(self.advance(c) for c in text)


_FONTS = {}


def font(name):
    if name not in _FONTS:
        _FONTS[name] = Font(name)
    return _FONTS[name]


def rgb565(color):
    """Rounds a colour to what the 16-bit panel can show."""
    r, g, b = color
    r5, g6, b5 = r >> 3, g >> 2, b >> 3
    return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))


class Screen:
    def __init__(self, background=(0, 0, 0), width=WIDTH, height=HEIGHT):
        self.width = width
        self.height = height
        self.pixels = [[rgb565(background)] * width for _ in range(height)]
        self.missing = []  # characters that were requested but are not in the chosen font

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color

    def fill_rect(self, x, y, w, h, color):
        color = rgb565(color)
        for yy in range(max(0, y), min(self.height, y + h)):
            row = self.pixels[yy]
            for xx in range(max(0, x), min(self.width, x + w)):
                row[xx] = color

    def rect(self, x, y, w, h, color):
        self.fill_rect(x, y, w, 1, color)
        self.fill_rect(x, y + h - 1, w, 1, color)
        self.fill_rect(x, y, 1, h, color)
        self.fill_rect(x + w - 1, y, 1, h, color)

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def round_rect(self, x, y, w, h, radius, color, fill=True):
        color565 = rgb565(color)
        for yy in range(h):
            for xx in range(w):
                dx = max(radius - xx, xx - (w - 1 - radius), 0)
                dy = max(radius - yy, yy - (h - 1 - radius), 0)
                inside = dx * dx + dy * dy <= radius * radius
                if not inside:
                    continue
                if fill:
                    self.pixel(x + xx, y + yy, color565)
                else:
                    edge = xx == 0 or yy == 0 or xx == w - 1 or yy == h - 1
                    if dx or dy:
                        edge = (dx * dx + dy * dy) > (radius - 1) * (radius - 1)
                    if edge:
                        self.pixel(x + xx, y + yy, color565)

    def text(self, x, y, string, font_name="efontJA_16", color=(255, 255, 255), scale=1, wrap=None, align="left"):
        """Draws text with its top-left corner at (x, y). Returns (x after the last glyph, y of the last line).

        wrap: right edge in pixels; glyphs that would cross it move to the next line, as M5GFX does.
        align: "left", "center" or "right" relative to x (single line only).
        """
        f = font(font_name)
        color = rgb565(color)
        if align != "left":
            total = f.width(string) * scale
            x = x - total // 2 if align == "center" else x - total
        start_x = x
        for character in string:
            if character == "\n":
                x = start_x
                y += f.height * scale
                continue
            g = f.glyph(ord(character))
            if g is None:
                if character not in self.missing:
                    self.missing.append(character)
                advance = f.max_width
                if wrap is not None and x + advance * scale > wrap:
                    x = start_x
                    y += f.height * scale
                self.rect(x + 1, y + 1, advance * scale - 2, f.height * scale - 2, (255, 0, 0))
                x += advance * scale
                continue
            w, h, gx, gy, advance, rows = g
            cell = max(gx + w, advance) * scale
            if wrap is not None and x + cell > wrap:
                x = start_x
                y += f.height * scale
            top = y + (f.baseline - gy - h) * scale
            left = x + gx * scale
            for row_index, row in enumerate(rows):
                for column_index, ink in enumerate(row):
                    if ink:
                        if scale == 1:
                            self.pixel(left + column_index, top + row_index, color)
                        else:
                            for sy in range(scale):
                                for sx in range(scale):
                                    self.pixel(left + column_index * scale + sx, top + row_index * scale + sy, color)
            x += advance * scale
        return x, y

    def png_bytes(self, scale=1):
        raw = bytearray()
        for row in self.pixels:
            line = bytearray()
            for (r, g, b) in row:
                line += bytes((r, g, b)) * scale
            for _ in range(scale):
                raw.append(0)
                raw += line

        def chunk(kind, payload):
            body = kind + payload
            return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        header = struct.pack(">IIBBBBB", self.width * scale, self.height * scale, 8, 2, 0, 0, 0)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")

    def save(self, path, scale=1):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(self.png_bytes(scale))
        return path


if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, ".pio", "preview")
    samples = ["東京駅はどこですか？", "観光案内所 営業時間 禁煙席", "餃子 鮪 炙り 鰤 饂飩 蕎麦", "チェックイン コンビニ"]
    for name in ("efontJA_10", "efontJA_12", "efontJA_14", "efontJA_16", "lgfxJapanGothic_20", "efontJA_24"):
        screen = Screen()
        f = font(name)
        screen.fill_rect(0, 0, WIDTH, 14, (0, 0, 128))
        screen.text(3, 1, "%s  %d px  %d lines" % (name, f.height, (HEIGHT - 16) // f.height), "efontJA_12")
        y = 17
        for line in samples:
            if y + f.height > HEIGHT:
                break
            screen.text(2, y, line, name)
            y += f.height + 1
        path = screen.save(os.path.join(out, "fonts_%s.png" % name), scale=3)
        print(path, "missing glyphs:", "".join(screen.missing) or "none")
