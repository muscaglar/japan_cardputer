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
from sim_driver import SCREENS  # noqa: E402


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
        self.link.timeout = 0.05
        # Both control lines stay high, as the computer sets them when the port is opened.
        # Lowering them restarts the chip, and lowering only DTR leaves it waiting for new
        # firmware until it is reset again.
        self.link.dtr = True
        self.link.rts = True
        try:
            self.link.open()
        except serial.SerialException as error:
            raise RuntimeError("cannot open %s: %s" % (self.link.port, error.strerror or error))
        self._wait_for_app(8.0)

    def _wait_for_app(self, seconds):
        """Asks until the app answers: it may be starting."""
        end = time.time() + seconds
        while time.time() < end:
            try:
                self._ask("info", "#info", timeout=0.6)
                return
            except RuntimeError:
                continue
        raise RuntimeError("no answer from the device within %.0f seconds. It answers only while the app is "
                           "running: not during the hardware check, and not with firmware older than the "
                           "console." % seconds)

    def _ask(self, line, prefix, timeout=5.0):
        # What is left from before is read away. Discarding it through the driver
        # (reset_input_buffer) made the next answer but one hang on macOS.
        while self.link.read(65536):
            pass
        self.link.write((line + "\n").encode("utf-8"))
        self.link.flush()
        start = time.time()
        knocked = start
        pending = b""
        while time.time() - start < timeout:
            chunk = self.link.read(65536)
            if not chunk:
                # The end of an answer sometimes stays on the device until it sends again.
                # An empty line makes it send: newer firmware answers it with "#".
                if time.time() - knocked > 0.25:
                    self.link.write(b"\n")
                    self.link.flush()
                    knocked = time.time()
                continue
            pending += chunk
            while b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").strip()
                if text.startswith("#error"):
                    raise RuntimeError("the device answered %r to %r" % (text, line))
                if text.startswith(prefix) and (len(prefix) > 1 or text == prefix):
                    return text[len(prefix):].strip()
        raise RuntimeError("no answer from the device to %r within %.1f seconds" % (line, timeout))

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

    def open(self, entry):
        """From the home screen: opens the menu and the entry of that name ("kana", "settings", a deck)."""
        self.key("Tab")
        state = self.info()
        names = state.get("menu", [])
        if entry not in names:
            raise RuntimeError("the menu has no entry %r: %s" % (entry, ", ".join(names)))
        steps = names.index(entry) - state["chosen"]
        for _ in range(abs(steps)):
            self.key("Down" if steps > 0 else "Up")
        self.key("Enter")

    def keep(self):
        return self._ask("keep", "#done") == "1"

    def back(self):
        return self._ask("back", "#done") == "1"

    def sitting(self, deck=""):
        """Starts a sitting from the deck of that id, or the course without one."""
        return self._ask(("sitting " + deck).strip(), "#done") == "1"

    def fresh(self):
        """Forgets all progress and starts at day 1. The device refuses unless keep() was done."""
        return self._ask("fresh", "#done") == "1"

    def restart(self):
        """Restarts the device and waits until the app answers again."""
        self._ask("restart", "#ok")
        time.sleep(0.3)
        self._wait_for_app(20.0)

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
