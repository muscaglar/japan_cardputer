#!/usr/bin/env python3
"""Downloads the latest cloud build and writes it to a Cardputer on USB.

Usage:
    python3 tools/flash.py                 # download the latest build and flash it
    python3 tools/flash.py --port /dev/cu.usbmodem1101
    python3 tools/flash.py --file japan_cardputer.bin

Writing the image replaces whatever firmware is on the device, the factory demo included.
If the device is not found: switch it off, hold the G0 button, plug in USB, release.

Needs PlatformIO (for its copy of esptool). Nothing is compiled.
"""
import argparse
import glob
import os
import subprocess
import sys
import tempfile
import urllib.request

URL = "https://github.com/muscaglar/japan_cardputer/releases/download/latest/japan_cardputer.bin"


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/cu.wchusbserial*"))
    if not ports:
        sys.exit("No device found on USB. Switch it off, hold G0, plug in USB, release, and try again.")
    if len(ports) > 1:
        print("Several ports found, using the first: %s" % ", ".join(ports))
    return ports[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port")
    parser.add_argument("--file", help="flash this image instead of downloading the latest build")
    parser.add_argument("--baud", default="921600")
    args = parser.parse_args()

    port = args.port or find_port()

    image = args.file
    if not image:
        image = os.path.join(tempfile.mkdtemp(prefix="japan_cardputer_"), "japan_cardputer.bin")
        print("Downloading %s" % URL)
        try:
            urllib.request.urlretrieve(URL, image)
        except OSError as error:
            sys.exit("Download failed (%s). Has the cloud build finished? See the Actions tab of the repository." % error)
    if not os.path.isfile(image):
        sys.exit("No such file: %s" % image)
    size = os.path.getsize(image)
    if size < 200_000:
        sys.exit("%s is only %d bytes, which is too small to be a firmware image." % (image, size))
    print("Image: %s (%.1f MB)" % (image, size / 1e6))
    command = ["pio", "pkg", "exec", "-p", "tool-esptoolpy", "--", "esptool.py", "--chip", "esp32s3",
               "--port", port, "--baud", args.baud, "write_flash", "0x0", image]
    print(" ".join(command))
    result = subprocess.run(command)
    if result.returncode != 0:
        sys.exit("Flashing failed. Put the device in download mode (off, hold G0, plug in, release) and retry.")
    print("\nDone. Press the reset button or switch the device off and on.")
    print("To read its report: python tools/serial_report.py (with PlatformIO's Python, see the file)")


if __name__ == "__main__":
    main()
