#!/usr/bin/env python3
"""Plays the app on a real Cardputer over USB and reads its screen back.

The device shell listens on the serial port (see src/console.h). This class speaks to it with
the same methods as the simulator's driver in sim_driver.py, so that a check written for one
runs on the other.

Needs pyserial, which PlatformIO brings along. Find its Python with `pio system info`
("Python Executable") and run the checks with that.

    <that python> tools/device_driver.py            # prints the state of the device
    <that python> tools/device_driver.py shot.png   # and saves what is on its screen
"""
import base64
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardputer_screen import HEIGHT, WIDTH, Screen  # noqa: E402

SCREENS = ["home", "menu", "kana", "settings"]


def find_port():
    found = sorted(glob.glob("/dev/cu.usbmodem*"))
    if not found:
        raise RuntimeError("No Cardputer found on USB. Is it plugged in and switched on?")
    return found[0]


class Device:
    def __init__(self, port=None, seed=None):
        try:
            import serial
        except ImportError:
            raise RuntimeError("pyserial is missing. Use PlatformIO's Python: see `pio system info`.")
        self.link = serial.Serial()
        self.link.port = port or find_port()
        self.link.baudrate = 115200
        self.link.timeout = 0.5
        # Both lines low before opening: a pulse on them would restart the chip.
        self.link.dtr = False
        self.link.rts = False
        try:
            self.link.open()
        except serial.SerialException as error:
            raise RuntimeError("cannot open %s: %s" % (self.link.port, error.strerror or error))
        time.sleep(0.2)
        self.link.reset_input_buffer()

    def _ask(self, line, prefix, timeout=5.0):
        self.link.write((line + "\n").encode("utf-8"))
        self.link.flush()
        end = time.time() + timeout
        pending = b""
        while time.time() < end:
            chunk = self.link.read(8192)
            if not chunk:
                continue
            pending += chunk
            while b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").strip()
                if text.startswith("#error"):
                    raise RuntimeError("the device answered %r to %r" % (text, line))
                if text.startswith(prefix):
                    return text[len(prefix):].strip()
        raise RuntimeError("no answer from the device to %r within %.0f seconds. It answers only while the app "
                           "is running: not during the hardware check, and not with firmware older than the "
                           "console." % (line, timeout))

    def key(self, name):
        self._ask("key " + name, "#ok")

    def type(self, text):
        self._ask("type " + text, "#ok")

    def fn(self, character):
        self._ask("fn " + character, "#ok")

    def info(self):
        return json.loads(self._ask("info", "#info"))

    def look(self):
        return self.info()["look"]

    def frame(self):
        """Returns (screen name, rows of (r, g, b))."""
        answer = self._ask("frame", "#frame", timeout=10.0)
        screen, width, height, data = answer.split(" ", 3)
        if int(width) != WIDTH or int(height) != HEIGHT:
            raise RuntimeError("unexpected picture size %s x %s" % (width, height))
        raw = base64.b64decode(data)
        flat = []
        for i in range(0, len(raw) - 2, 3):
            run, high, low = raw[i], raw[i + 1], raw[i + 2]
            value = (high << 8) | low
            r5, g6, b5 = (value >> 11) & 0x1F, (value >> 5) & 0x3F, value & 0x1F
            flat.extend([((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))] * run)
        if len(flat) != WIDTH * HEIGHT:
            raise RuntimeError("the picture has %d pixels, expected %d" % (len(flat), WIDTH * HEIGHT))
        rows = [flat[y * WIDTH:(y + 1) * WIDTH] for y in range(HEIGHT)]
        index = int(screen)
        return (SCREENS[index] if 0 <= index < len(SCREENS) else str(index)), rows

    def close(self):
        self.link.close()


def save(rows, path, scale=3):
    picture = Screen((0, 0, 0))
    picture.pixels = [list(row) for row in rows]
    picture.save(path, scale)


def main():
    try:
        device = Device()
    except RuntimeError as error:
        sys.exit("error: %s" % error)
    try:
        state = device.info()
        width = max(len(key) for key in state)
        for key, value in state.items():
            print("  %-*s  %s" % (width, key, value))
        if len(sys.argv) > 1:
            name, rows = device.frame()
            save(rows, sys.argv[1])
            print("screen '%s' saved to %s" % (name, sys.argv[1]))
    except RuntimeError as error:
        sys.exit("error: %s" % error)
    finally:
        device.close()


if __name__ == "__main__":
    main()
