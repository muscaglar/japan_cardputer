#!/usr/bin/env python3
"""Restarts the device and prints what it says on the USB serial port.

    pio pkg exec -p tool-esptoolpy -- python tools/serial_report.py
    pio pkg exec -p tool-esptoolpy -- python tools/serial_report.py --port /dev/cu.usbmodem2101 --seconds 8

Run through PlatformIO so that its copy of pyserial is used. The port is opened first and the
device restarted afterwards, so that the lines printed at start are not missed. Lines that are
JSON are printed again at the end, formatted.
"""
import argparse
import glob
import json
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial is missing. Run this through PlatformIO:\n"
             "  pio pkg exec -p tool-esptoolpy -- python tools/serial_report.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--no-restart", action="store_true", help="listen without restarting the device")
    args = parser.parse_args()

    port = args.port
    if not port:
        found = sorted(glob.glob("/dev/cu.usbmodem*"))
        if not found:
            sys.exit("No Cardputer found on USB. Is it plugged in and switched on?")
        port = found[0]

    link = serial.Serial()
    link.port = port
    link.baudrate = 115200
    link.timeout = 0.2
    link.dtr = False
    link.rts = False
    try:
        link.open()
    except serial.SerialException as error:
        sys.exit("error: cannot open %s: %s" % (port, error.strerror or error))
    if not args.no_restart:
        # The same restart the flashing tool does: a pulse on the reset line.
        link.rts = True
        time.sleep(0.15)
        link.rts = False

    reports = []
    pending = b""
    end = time.time() + args.seconds
    while time.time() < end:
        try:
            chunk = link.read(4096)
        except serial.SerialException:
            # The port disappears for a moment while the chip restarts.
            time.sleep(0.2)
            try:
                link.close()
                link.open()
            except serial.SerialException:
                pass
            continue
        if not chunk:
            continue
        pending += chunk
        while b"\n" in pending:
            raw, pending = pending.split(b"\n", 1)
            text = raw.decode("utf-8", "replace").rstrip("\r")
            print(text)
            if text.startswith("{") and text.endswith("}"):
                try:
                    reports.append(json.loads(text))
                except ValueError:
                    pass
    link.close()

    if not reports:
        print("\nNo report line was seen in %.0f seconds." % args.seconds)
        return 1
    print()
    for report in reports:
        width = max(len(key) for key in report)
        for key, value in report.items():
            print("  %-*s  %s" % (width, key, value))
    return 0


if __name__ == "__main__":
    sys.exit(main())
