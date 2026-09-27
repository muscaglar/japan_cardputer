#!/usr/bin/env python3
"""Waits until the cloud has built a commit and published it as the release `latest`.

    python3 tools/wait_for_build.py              # waits for the commit that is checked out here
    python3 tools/wait_for_build.py 246c3d6      # or for another one
    python3 tools/wait_for_build.py --minutes 45

It reads the public release page, which names the commit the build was made from. A build made
from a later commit that contains the wanted one counts as well. Exit code 0 when it is
published, 1 when the time is up, 2 when the commit never reached GitHub.
"""
import argparse
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOSITORY = "muscaglar/japan_cardputer"
RELEASE = "https://github.com/%s/releases/expanded_assets/latest" % REPOSITORY
PAGE = "https://github.com/%s/releases/tag/latest" % REPOSITORY
COMMIT = "https://github.com/%s/commit/%%s" % REPOSITORY


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "wait_for_build"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, ""
    except (urllib.error.URLError, OSError):
        return 0, ""


def published_commit():
    status, page = fetch(PAGE)
    if status != 200:
        return None
    found = re.search(r"Built from\s+(?:<[^>]+>\s*)*([0-9a-f]{7,40})", page)
    return found.group(1) if found else None


def contains(published, wanted):
    """Whether the published commit is the wanted one or was made on top of it."""
    if published.startswith(wanted) or wanted.startswith(published):
        return True
    known = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", wanted, published],
                           capture_output=True)
    return known.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("commit", nargs="?")
    parser.add_argument("--minutes", type=float, default=60.0)
    parser.add_argument("--every", type=float, default=30.0, help="seconds between looks")
    args = parser.parse_args()

    wanted = args.commit
    if not wanted:
        wanted = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{7,40}", wanted or ""):
        sys.exit("error: %r is not a commit" % wanted)

    end = time.time() + args.minutes * 60
    pushed = False
    last = None
    while True:
        if not pushed:
            status, _ = fetch(COMMIT % wanted)
            pushed = (status == 200)
            if pushed:
                print("%s commit %s is on GitHub, the build has started" % (time.strftime("%H:%M:%S"), wanted[:7]),
                      flush=True)
        current = published_commit()
        if current != last:
            print("%s latest build is from %s" % (time.strftime("%H:%M:%S"), (current or "unknown")[:7]), flush=True)
            last = current
        if current and contains(current, wanted):
            print("published", flush=True)
            return 0
        if time.time() > end:
            print("time is up after %.0f minutes; %s" % (
                args.minutes, "the build did not appear" if pushed else "the commit was never pushed"), flush=True)
            return 1 if pushed else 2
        time.sleep(args.every)


if __name__ == "__main__":
    sys.exit(main())
