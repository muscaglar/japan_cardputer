#!/usr/bin/env python3
"""Makes the memory card in a Cardputer hold what a folder on the computer holds, over USB.

The card stays in the device. The folder is laid out like the card:
card/nihongo/audio/f/signs/sign-eki.wav becomes /nihongo/audio/f/signs/sign-eki.wav.

    python3 tools/sd_sync.py card              # sends what the card lacks or has differently
    python3 tools/sd_sync.py card --dry-run    # only says what it would do
    python3 tools/sd_sync.py card --delete     # also removes from the audio folders what the folder no longer has
    python3 tools/sd_sync.py card --quick      # believes a file of the same size to be the same
    python3 tools/sd_sync.py card --port /dev/cu.usbmodem1101

A file is the same when its size and its CRC-32 are. Every file is asked back for its CRC-32 after
it was sent, and sent again if the card holds something else. Stopping is harmless: a file is on the
card whole or not at all, and the next run sends only what is still missing.

Files and folders whose names start with a dot are left out. Names may hold letters, digits and
. _ - only, and a path on the card at most 120 letters: the device takes nothing else. A name
that ends in a dot is refused too, because the card would keep it without the dot.

The device's side is src/files.cpp, and src/files.h says what is sent to and fro. Nothing here reads
what a file on the card holds, and the device has no word for it.

Needs pyserial, which PlatformIO's own Python has. Started with another Python, the tool looks for
that one and starts itself again with it.

Ends with 0 when the card holds the folder, 1 when something was refused or failed, 2 when it could
not begin.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import zlib

TOOLS = os.path.dirname(os.path.abspath(__file__))

LONGEST_PATH = 120
INCOMING = "/incoming.part"  # the name under which the device writes a file that arrives
TAKEN_AGAIN = "SD_SYNC_STARTED_AGAIN"

# Answers of the device after which the same file need not be tried again.
FINAL = ("bad path", "no folder", "in the way", "no card", "unknown command", "put takes")


class Refused(RuntimeError):
    """The device answered "#error <why>". It takes words again."""

    def __init__(self, why, asked):
        RuntimeError.__init__(self, "the device answered %r to %r" % (why, asked))
        self.why = why


class Silent(RuntimeError):
    """No answer came in time, or one that makes no sense. What the device does now is not known."""


class Failed(RuntimeError):
    """A file did not get onto the card, however often it was tried."""


def good_path(path):
    """The rule of the device for paths (src/files.h)."""
    if not re.fullmatch(r"/[A-Za-z0-9/._-]*", path) or len(path) > LONGEST_PATH:
        return False
    if ".." in path or "//" in path or "." in path.split("/"):
        return False
    return path == "/" or not path.endswith("/")


def folder_of(path):
    above = path.rsplit("/", 1)[0]
    return above or "/"


def shown(text):
    """A name from the card, safe to print: it may hold anything."""
    return "".join(c if c.isprintable() else "\\x%02x" % ord(c) for c in text)


def amount(count):
    for unit, size in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if count >= size:
            return "%.1f %s" % (count / size, unit)
    return "%d B" % count


def duration(seconds):
    if seconds < 60:
        return "%.1f s" % seconds
    return "%d min %d s" % (seconds // 60, seconds % 60)


class SerialLink:
    """The USB port, as pyserial opened it.

    When the cable is pulled or the device starts anew, the port is gone and pyserial raises an
    OSError. That ends the run: it must not be taken for a file here that cannot be read.
    """

    def __init__(self, port):
        self.port = port

    def write(self, data):
        try:
            self.port.write(data)
            self.port.flush()
        except OSError as error:
            raise Silent("the USB port is gone (%s)" % (error.strerror or error))

    def read_some(self, seconds):
        """What has arrived, at once; else what arrives first within that time; else nothing."""
        end = time.time() + seconds
        try:
            while True:
                waiting = self.port.in_waiting
                if waiting:
                    return self.port.read(waiting)
                if time.time() >= end:
                    return b""
                # Returns with the first byte, or empty after the short time the port was opened with.
                first = self.port.read(1)
                if first:
                    return first
        except OSError as error:
            raise Silent("the USB port is gone (%s)" % (error.strerror or error))


class Card:
    """The words of the device for its memory card. The link needs write() and read_some()."""

    def __init__(self, link, patience=3.0, slow=20.0):
        self.link = link
        self.patience = patience  # how long the device waits for the next byte of a file
        self.slow = slow          # how long an answer may take
        self.pending = b""
        self.asked = ""
        self.unsure = False       # an answer failed to come: settle before the next word

    def _line(self, until):
        while b"\n" not in self.pending:
            left = until - time.time()
            if left <= 0:
                return None
            self.pending += self.link.read_some(min(left, 0.25))
        raw, self.pending = self.pending.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")

    def _forget(self):
        self.pending = b""
        while self.link.read_some(0):
            pass

    def _send(self, line):
        if self.unsure:
            self.settle()
        self._forget()
        self.asked = line
        self.link.write((line + "\n").encode("ascii"))

    def _lost(self, what):
        self.unsure = True
        return Silent("%s after %r" % (what, self.asked))

    def _answer(self, words, seconds, knock=False):
        """Waits for a line that starts with one of the words: returns the word and the rest.

        A knock is an empty line, which the device answers with "#". It pushes out an answer that
        stayed behind. Never while a file is sent: there every byte counts as one of the file. And
        ever more seldom: knocks wait in the queue of a device that is busy, and a full queue
        drops the next word.
        """
        end = time.time() + seconds
        pause = 1.0
        while True:
            line = self._line(min(end, time.time() + pause) if knock else end)
            if line is None:
                if time.time() >= end:
                    raise self._lost("no answer within %.0f seconds" % seconds)
                self.link.write(b"\n")
                pause = min(pause * 2, 30.0)
                continue
            word, _, rest = line.partition(" ")
            if word == "#error":
                raise Refused(rest, self.asked)
            if word in words:
                return word, rest
            if line.startswith(('{"app"', '{"probe"')):
                raise self._lost("the device started anew")

    def _number(self, text, base=10):
        try:
            return int(text, base)
        except ValueError:
            raise self._lost("the answer %r makes no sense" % text)

    def settle(self):
        """After an answer failed to come: waits until the device takes words again."""
        # First quiet, for as long as the device waits for a byte: if it still takes a file, a
        # knock would be one more byte of it, and would make it wait on.
        end = time.time() + self.patience + 0.5
        while True:
            line = self._line(end)
            if line is None or line.startswith("#error"):
                break
        end = time.time() + self.slow
        while time.time() < end:
            self._forget()
            self.link.write(b"\n")
            until = time.time() + 1.0
            while True:
                line = self._line(until)
                if line is None:
                    break
                if line == "#":
                    self.unsure = False
                    return
        raise Silent("the device does not answer any more")

    def df(self):
        """Bytes in all and bytes used."""
        self._send("df")
        _, rest = self._answer(("#df",), self.slow * 3, knock=True)
        total, _, used = rest.partition(" ")
        return self._number(total), self._number(used)

    def ls(self, folder):
        """What the folder holds: (name, size), the size None for a folder and -1 if not known."""
        self._send("ls " + folder)
        found = []
        while True:
            word, rest = self._answer(("#file", "#dir", "#end"), self.slow, knock=True)
            if word == "#end":
                if self._number(rest) != len(found):
                    raise self._lost("%d entries came, %s were announced" % (len(found), rest))
                return found
            if word == "#dir":
                found.append((rest, None))
            else:
                size, _, name = rest.partition(" ")
                found.append((name, int(size) if size.isdigit() else -1))

    def crc(self, path, size=0):
        """CRC-32 and size of a file on the card. The size is what is expected, for the waiting."""
        self._send("crc " + path)
        _, rest = self._answer(("#crc",), self.slow + size / 20000.0, knock=True)
        crc, _, length = rest.partition(" ")
        return self._number(crc, 16), self._number(length)

    def rm(self, path):
        self._send("rm " + path)
        self._answer(("#ok",), self.slow * 30, knock=True)

    def mkdir(self, path):
        self._send("mkdir " + path)
        self._answer(("#ok",), self.slow, knock=True)

    def put(self, path, size, crc, read, tick=None):
        """Sends a file. read(count) gives its next bytes, tick(bytes so far) is told how far it is."""
        self._send("put %s %d %08x" % (path, size, crc))
        _, rest = self._answer(("#ready",), self.slow)
        piece = self._number(rest)
        if not 0 < piece <= 65536:
            raise self._lost("a piece of %d bytes makes no sense" % piece)
        sent = 0
        try:
            while sent < size:
                want = min(piece, size - sent)
                data = read(want)
                # A file that became shorter meanwhile is filled up, so that both sides stay in step.
                # Its CRC-32 will not be the one announced, and the device throws it away.
                data += bytes(want - len(data))
                self.link.write(data)
                sent += want
                _, rest = self._answer(("#got",), self.slow)
                if self._number(rest) != sent:
                    raise self._lost("the device counts %s bytes, %d were sent" % (rest, sent))
                if tick:
                    tick(sent)
            _, rest = self._answer(("#done",), self.slow)
        except Refused as refused:
            if refused.why == "timeout":
                # The device gave up waiting while bytes were on their way: they came late, and
                # it took them for words.
                self.unsure = True
            raise
        except OSError:
            self.unsure = True  # the file here cannot be read on: the device still waits for the rest
            raise
        if self._number(rest, 16) != crc:
            raise self._lost("the device kept a file with CRC-32 %s, not %08x" % (rest, crc))


class Folder:
    """What a folder on the computer holds, under the names it gets on the card."""

    def __init__(self, top):
        self.folders = []  # paths on the card, those above before those below
        self.files = []    # (path on the card, path here, size)
        self.refused = []  # (path here, why)
        self.unread = set()  # folders that cannot be read here: paths on the card, in small letters
        self.hidden = 0
        taken = {}

        def cannot(error):
            inside = os.path.relpath(error.filename, top).replace(os.sep, "/")
            self.refused.append((error.filename, "the folder cannot be read: %s" % (error.strerror or error)))
            self.unread.add(("/" + inside).lower())

        for here, folders, names in os.walk(top, onerror=cannot):
            inside = os.path.relpath(here, top).replace(os.sep, "/")
            above = "" if inside == "." else "/" + inside
            kept = []
            for name in sorted(folders) + sorted(names):
                whole = os.path.join(here, name)
                path = above + "/" + name
                is_folder = name in folders and not os.path.islink(whole)
                if name.startswith("."):
                    self.hidden += 1
                    continue
                why = self.wrong(whole, path, taken)
                if why:
                    self.refused.append((whole, why))
                    continue
                taken[path.lower()] = whole
                if is_folder:
                    kept.append(name)
                    self.folders.append(path)
                    continue
                try:
                    self.files.append((path, whole, os.path.getsize(whole)))
                except OSError as error:
                    self.refused.append((whole, error.strerror or str(error)))
            folders[:] = kept  # what was refused or left out is not entered
        self.folders.sort(key=lambda path: (path.count("/"), path))
        self.files.sort()
        self.names = set(taken)  # all that is here and could be on the card, in small letters

    @staticmethod
    def wrong(whole, path, taken):
        if os.path.islink(whole):
            return "a link"
        if not os.path.isdir(whole) and not os.path.isfile(whole):
            return "neither a file nor a folder"
        if len(path) > LONGEST_PATH:
            return "%s has %d letters, the device takes %d" % (path, len(path), LONGEST_PATH)
        if ".." in path:
            return "the device takes no name with two dots in a row"
        if not good_path(path):
            return "the device takes letters, digits and . _ - only"
        if path.endswith("."):
            return "the card drops a dot at the end of a name"
        if path.lower() == INCOMING:
            return "the device uses this name itself"
        if path.lower() in taken:
            return "the card cannot tell it from %s" % taken[path.lower()]
        return None


def measure(whole):
    """Size and CRC-32 of a file here."""
    size = 0
    crc = 0
    with open(whole, "rb") as source:
        while True:
            data = source.read(1 << 16)
            if not data:
                return size, crc & 0xFFFFFFFF
            size += len(data)
            crc = zlib.crc32(data, crc)


class Report:
    """One line per thing done. On a terminal the line of the file on its way shows how far it is."""

    def __init__(self, out):
        self.out = out
        self.moving = out.isatty() if hasattr(out, "isatty") else False
        self.shown = 0
        self.last = 0.0

    def line(self, text):
        if self.shown:
            self.out.write("\r" + " " * self.shown + "\r")
            self.shown = 0
        self.out.write(text + "\n")
        self.out.flush()

    def live(self, text):
        if not self.moving or time.time() - self.last < 0.1:
            return
        self.last = time.time()
        self.out.write("\r" + text.ljust(self.shown))
        self.out.flush()
        self.shown = max(self.shown, len(text))


class Sync:
    def __init__(self, card, top, out, delete=False, dry_run=False, quick=False, verbose=False, tries=3):
        self.card = card
        self.top = top
        self.report = Report(out)
        self.delete = delete
        self.dry_run = dry_run
        self.quick = quick
        self.verbose = verbose
        self.tries = tries
        self.listings = {}
        self.sent = 0
        self.sent_bytes = 0
        self.sending = 0.0
        self.same = 0
        self.made = 0
        self.removed = 0
        self.failed = 0

    def listing(self, folder):
        """What the card has in a folder, by name in small letters. None: the card has no such
        folder. False: a file of that name is in the way."""
        if folder not in self.listings:
            for last in (False, False, True):
                try:
                    entries = self.card.ls(folder)
                except Refused as refused:
                    if refused.why not in ("not there", "not a folder"):
                        raise
                    self.listings[folder] = None if refused.why == "not there" else False
                except Silent:
                    # A line of a long listing can get lost on the way. The count at its end
                    # shows that, and the listing is asked for again.
                    if last:
                        raise
                    continue
                else:
                    self.listings[folder] = dict((name.lower(), (name, size)) for name, size in entries)
                break
        return self.listings[folder]

    def fail(self, what, why):
        self.failed += 1
        self.report.line("FAILED   %s: %s" % (what, why))

    def run(self):
        local = Folder(self.top)
        tidied = self.audio_folders(local)
        if self.delete and not tidied:
            self.report.line("%s has no folder audio: with --delete the card's /audio would be emptied. "
                             "Nothing was done." % self.top)
            return 2
        try:
            total, used = self.begin()
        except Refused as refused:
            if refused.why == "no card":
                self.report.line("The device has no memory card in, or cannot read it.")
            elif refused.why == "unknown command":
                self.report.line("The firmware on the device is older than this tool: it has no words for the "
                                 "card. Write the newest build to it with tools/flash.py.")
            else:
                self.report.line("error: %s" % refused)
            return 2
        self.free = total - used
        self.report.line("card    %s, %s used" % (amount(total), amount(used)))
        self.report.line("folder  %s: %d files, %s%s" % (
            self.top, len(local.files), amount(sum(size for _, _, size in local.files)),
            ", %d left out because their names start with a dot" % local.hidden if local.hidden else ""))
        for whole, why in local.refused:
            self.fail(whole, why)
        if INCOMING[1:] in (self.listing("/") or {}) and not self.dry_run:
            self.card.rm(INCOMING)  # left by a run that was cut short

        started = time.time()
        self.widest = max([len(path) for path, _, _ in local.files] + [0])
        for path in local.folders:
            self.folder(path)
        for index, (path, whole, size) in enumerate(local.files):
            self.file("%*d/%d" % (len(str(len(local.files))), index + 1, len(local.files)), path, whole, size)
        if self.delete:
            for path in tidied:
                self.tidy(path, local)

        would = "would be " if self.dry_run else ""
        parts = ["%d %ssent" % (self.sent, would)]
        if self.sent:
            parts[0] += " (%s" % amount(self.sent_bytes)
            if self.sending > 0:
                parts[0] += " in %s, %s/s" % (duration(self.sending), amount(self.sent_bytes / self.sending))
            parts[0] += ")"
        parts.append("%d the same" % self.same)
        if self.made:
            parts.append("%d folders %smade" % (self.made, would))
        if self.delete:
            parts.append("%d %sremoved" % (self.removed, would))
        parts.append("%d failed" % self.failed)
        self.report.line("total   %d files: %s; %s" % (len(local.files), ", ".join(parts),
                                                      duration(time.time() - started)))
        return 1 if self.failed else 0

    @staticmethod
    def audio_folders(local):
        """The folders --delete may tidy: those named audio that the folder here holds, such as
        /nihongo/audio. Nothing else on the card is ever removed."""
        found = [path for path in local.folders if path.lower().rsplit("/", 1)[-1] == "audio"]
        return [path for path in found
                if not any(path != other and path.lower().startswith(other.lower() + "/") for other in found)]

    def begin(self):
        """Asks for the room on the card. A run that was stopped may have left the device waiting
        for the rest of a file: then the first words are taken for bytes of it."""
        for last in (False, False, True):
            try:
                return self.card.df()
            except Silent:
                if last:
                    raise
            except Refused as refused:
                if last or refused.why in FINAL:
                    raise

    def folder(self, path):
        there = self.listing(path)
        if there is False:
            self.fail(path, "a file of that name is in the way on the card")
            return
        if there is not None:
            return
        if self.listing(folder_of(path)) is False:
            self.fail(path, "the folder above it could not be made")
            self.listings[path] = False
            return
        if self.dry_run:
            self.report.line("would make   %s" % path)
        else:
            try:
                self.card.mkdir(path)
            except Refused as refused:
                self.fail(path, "the folder could not be made: " + refused.why)
                self.listings[path] = False
                return
            self.report.line("made     %s" % path)
        self.made += 1
        self.listings[path] = {}

    def file(self, place, path, whole, size):
        entries = self.listing(folder_of(path))
        if not isinstance(entries, dict):
            self.fail(path, "its folder is not on the card")
            return
        name, there = entries.get(path.rsplit("/", 1)[1].lower(), (None, 0))
        if size > 0xFFFFFFFF:
            self.fail(path, "%s: a file on the card holds less than 4 GB" % amount(size))
            return
        if name is None:
            reason = "new"
        elif there is None:
            self.fail(path, "a folder of that name is in the way on the card")
            return
        elif there != size:
            reason = "changed"
        elif self.quick:
            reason = None
        else:
            try:
                reason = None if self.card.crc(path, size) == (measure(whole)[1], size) else "changed"
            except Refused as refused:
                self.fail(path, "the card cannot say what it has: " + refused.why)
                return
            except OSError as error:
                self.fail(whole, error.strerror or str(error))
                return
        if reason is None:
            self.same += 1
            if self.verbose:
                self.report.line("%s  same     %s" % (place, path.ljust(self.widest)))
            return
        if self.dry_run:
            self.sent += 1
            self.sent_bytes += size
            self.report.line("%s  would send  %s  %9s  %s" % (place, path.ljust(self.widest), amount(size), reason))
            return
        # What a file replaces makes no room for it: that goes only when the new one is on the card.
        if size > self.free:
            self.fail(path, "the card has no room for %s" % amount(size))
            return
        try:
            size, took, tries = self.send(place, path, whole)
        except (Refused, Failed) as error:
            self.fail(path, str(error))
            return
        except OSError as error:
            self.fail(whole, error.strerror or str(error))
            return
        self.sent += 1
        self.sent_bytes += size
        self.sending += took
        self.free -= size - (there if there and there > 0 else 0)
        speed = amount(size / took) + "/s" if size and took > 0 else ""
        self.report.line("%s  sent     %s  %9s  %11s  %s%s" % (
            place, path.ljust(self.widest), amount(size), speed, reason,
            "" if tries == 1 else ", at try %d" % tries))

    def send(self, place, path, whole):
        """Sends a file and asks it back. Returns its size, the seconds it took and the tries."""
        why = ""
        for attempt in range(1, self.tries + 1):
            size, crc = measure(whole)
            started = time.time()

            def tick(so_far):
                took = max(time.time() - started, 0.001)
                self.report.live("%s  sending  %s  %3d %%  %s/s" % (place, path, 100 * so_far // max(size, 1),
                                                                   amount(so_far / took)))
            try:
                with open(whole, "rb") as source:
                    self.card.put(path, size, crc, source.read, tick)
                took = time.time() - started
                if self.card.crc(path, size) == (crc, size):
                    return size, took, attempt
                why = "the card holds other bytes than were sent"
                if attempt == self.tries:
                    self.card.rm(path)  # rather no clip than a wrong one
            except Refused as refused:
                if refused.why.startswith(FINAL):
                    raise
                why = str(refused)
            except Silent as silent:
                why = str(silent)
                self.card.settle()  # if the device is gone for good, this ends the run
        raise Failed("%s, in %d tries" % (why, self.tries))

    def tidy(self, folder, local):
        """Removes from a folder of the card what the folder here does not have."""
        if folder.lower() in local.unread:
            return  # nobody knows what the folder here has: nothing goes from the one on the card
        entries = self.listing(folder)
        if not isinstance(entries, dict):
            return
        folders = set(path.lower() for path in local.folders)
        for name, size in sorted(entries.values(), key=lambda entry: entry[0]):
            path = folder + "/" + name
            if path.lower() in local.names:
                # Where one side has a file and the other a folder, that was reported above.
                if size is None and path.lower() in folders:
                    self.tidy(path, local)
                continue
            if not good_path(path):
                self.fail(shown(path), "cannot be removed: the device takes no such name")
                continue
            if self.dry_run:
                self.report.line("would remove %s" % path)
            else:
                try:
                    self.card.rm(path)
                except Refused as refused:
                    self.fail(path, "could not be removed: " + refused.why)
                    continue
                self.report.line("removed  %s" % path)
            self.removed += 1


def platformio_python():
    """PlatformIO's own Python: the first line of the pio command names it."""
    found = []
    for name in ("pio", "platformio"):
        command = shutil.which(name)
        if not command:
            continue
        try:
            with open(command, "rb") as script:
                first = script.readline(400).decode("utf-8", "replace").strip()
        except OSError:
            continue
        if first.startswith("#!"):
            found.append(first[2:].strip().split(" ")[0])
    home = os.path.join(os.path.expanduser("~"), ".platformio", "penv")
    found += [os.path.join(home, "bin", "python"), os.path.join(home, "Scripts", "python.exe")]
    for python in found:
        if os.path.basename(python).startswith("python") and os.path.isfile(python) and os.access(python, os.X_OK):
            if subprocess.run([python, "-c", "import serial"], capture_output=True).returncode == 0:
                return python
    return None


def connect(port):
    """Opens the USB port and waits for the app. Returns the card and what to close at the end."""
    try:
        import serial  # noqa: F401
    except ImportError:
        python = None if os.environ.get(TAKEN_AGAIN) else platformio_python()
        if not python:
            raise RuntimeError("pyserial is missing. Use PlatformIO's Python: `pio system info` names it.")
        os.environ[TAKEN_AGAIN] = "1"
        sys.stdout.flush()
        os.execv(python, [python, os.path.abspath(__file__)] + sys.argv[1:])
    sys.path.insert(0, TOOLS)
    from device_driver import Device
    try:
        device = Device(port)
    except RuntimeError as error:
        if "no answer" not in str(error):
            raise
        # A run that was stopped may have left the device waiting for the rest of a file.
        time.sleep(3.5)
        device = Device(port)
    return Card(SerialLink(device.link)), device


def main(arguments=None, connect=connect, out=None):
    out = out or sys.stdout
    parser = argparse.ArgumentParser(description="Makes the memory card in the device hold what a folder holds.")
    parser.add_argument("folder", help="laid out like the card: folder/nihongo/audio/... becomes /nihongo/audio/...")
    parser.add_argument("--dry-run", action="store_true", help="only say what would be done")
    parser.add_argument("--delete", action="store_true",
                        help="also remove from the card's audio folders (such as /nihongo/audio) what the "
                             "folder no longer has; nothing else on the card is ever removed")
    parser.add_argument("--quick", action="store_true",
                        help="believe a file of the same size to be the same, without asking for its CRC-32")
    parser.add_argument("--verbose", action="store_true", help="also name the files that are the same")
    parser.add_argument("--port", help="the USB port of the device; without it the first Cardputer found")
    options = parser.parse_args(arguments)
    if not os.path.isdir(options.folder):
        out.write("error: %s is not a folder\n" % options.folder)
        return 2
    try:
        card, device = connect(options.port)
    except RuntimeError as error:
        out.write("error: %s\n" % error)
        return 2
    except KeyboardInterrupt:
        return 130
    sync = Sync(card, options.folder, out, delete=options.delete, dry_run=options.dry_run, quick=options.quick,
                verbose=options.verbose)
    try:
        return sync.run()
    except Refused as refused:
        sync.report.line("error: %s. Nothing more was done." % refused)
        return 1
    except Silent as silent:
        sync.report.line("error: %s. Is the device still plugged in and switched on? Start again to go on: "
                         "what has arrived is not sent twice." % silent)
        return 2
    except KeyboardInterrupt:
        sync.report.line("Stopped. Start again to go on: what has arrived is not sent twice.")
        return 130
    finally:
        if device:
            device.close()


if __name__ == "__main__":
    sys.exit(main())
