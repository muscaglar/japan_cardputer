#!/usr/bin/env python3
"""Asks a Cardputer on USB many times and counts the answers that came late.

    <PlatformIO's python> tools/console_check.py [PORT] [--times 200]

An answer counts as late when it needed a knock (an empty line sent after a quarter of a
second) or more than 200 ms. With firmware that flushes its answers there should be none.
Also pushes on the console: unknown words, overlong lines, an empty `type`.
"""
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from device_driver import Device  # noqa: E402


def main():
    arguments = sys.argv[1:]
    times = 200
    if "--times" in arguments:
        at = arguments.index("--times")
        times = int(arguments[at + 1])
        del arguments[at:at + 2]
    port = arguments[0] if arguments else None
    try:
        device = Device(port)
    except RuntimeError as error:
        sys.exit("error: %s" % error)
    failed = 0
    try:
        slow = 0
        lost = 0
        worst = 0.0
        kinds = ["info", "frame", "key Tab", "key Esc"]
        prefixes = {"info": "#info", "frame": "#frame", "key Tab": "#ok", "key Esc": "#ok"}
        for i in range(times):
            command = kinds[i % len(kinds)]
            start = time.time()
            try:
                device._ask(command, prefixes[command], timeout=3.0)
            except RuntimeError:
                lost += 1
                continue
            took = time.time() - start
            worst = max(worst, took)
            if took > 0.2:
                slow += 1
        print("%d requests: %d answered late, %d not at all, slowest %.0f ms" % (times, slow, lost, worst * 1000))
        failed += 1 if (slow or lost) else 0

        for line, expect in (("nonsense", "#error"), ("key Nothing", "#error"), ("fn", "#error"), ("fn ab", "#error"),
                             ("fresh", "#error"), ("type", "#ok"), ("x" * 300, "#error")):
            try:
                device._ask(line, "#ok", timeout=2)
                got = "#ok"
            except RuntimeError as error:
                got = "#error" if "#error" in str(error) else "no answer"
            ok = (got == expect)
            failed += 0 if ok else 1
            print("  %-4s %-14r -> %s" % ("ok" if ok else "FAIL", line[:12], got))
        state = device.info()
        print("still answering: screen %d, %d bytes free, lowest ever %d" % (
            state["screen"], state["heapFree"], state["heapLowest"]))
    finally:
        device.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
