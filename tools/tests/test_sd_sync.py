#!/usr/bin/env python3
"""Tests for tools/sd_sync.py and for the words of the device it speaks to (src/files.h).

    python3 tools/tests/test_sd_sync.py            # everything
    python3 tools/tests/test_sd_sync.py delete     # the tests whose name contains a word
    python3 tools/tests/test_sd_sync.py --allow-skips

No device is needed. Two stand in for it, each with a folder as its memory card:

  the pretended device  The device's side written once more, here, in Python, from what src/files.h
                        says. It speaks over a pair of sockets, and can be told to go wrong: to find
                        a wrong CRC-32, to lose an answer or give it late, to write a damaged file,
                        to start anew, to fall silent for good.
  the compiled device   src/files.cpp itself, compiled to WebAssembly with Emscripten and run by
                        Node, with a pretended Arduino around it: the USB port is a pair of files,
                        the card a folder. Without Emscripten or Node those tests are reported as
                        SKIPPED and the run fails, unless --allow-skips is given.

The same words are said to both, and their answers are compared line by line.

Nothing outside build/test_sd_sync/ is written.
"""
import io
import os
import random
import select
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import zlib

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(TESTS)
ROOT = os.path.dirname(TOOLS)
WORK = os.path.join(ROOT, "build", "test_sd_sync")

sys.path.insert(0, TOOLS)
import sd_sync  # noqa: E402

BOOT_LINE = '{"app":"japan_cardputer","board":"Cardputer ADV","memoryCard":true}'


class Failure(Exception):
    pass


def expect(condition, message):
    if not condition:
        raise Failure(message)


def same(got, want, what):
    if got != want:
        raise Failure("%s: got %r, expected %r" % (what, got, want))


# ---------------------------------------------------------------------------------------------
# The pretended device


class SocketLink:
    def __init__(self, end):
        self.end = end

    def write(self, data):
        self.end.sendall(data)

    def read_some(self, seconds):
        ready, _, _ = select.select([self.end], [], [], seconds)
        return self.end.recv(65536) if ready else b""


class StoppingLink(SocketLink):
    """Stops the tool after so many bytes, the way Ctrl-C does."""

    def __init__(self, end, after):
        SocketLink.__init__(self, end)
        self.left = after

    def write(self, data):
        if len(data) > self.left:
            self.end.sendall(data[:self.left])
            self.left = 1 << 40
            raise KeyboardInterrupt()
        self.left -= len(data)
        self.end.sendall(data)


class Pretended(threading.Thread):
    """The device's side of the words in src/files.h, and of the line reading in src/console.cpp."""

    LONGEST_LINE = 200
    LONGEST_PATH = 120
    INCOMING = "/incoming.part"
    name_of_kind = "pretended"

    def __init__(self, card, piece=512, patience=0.3):
        threading.Thread.__init__(self)
        self.daemon = True
        self.card = card
        self.piece = piece
        self.patience = patience
        self.slow = 1.5           # how long the tool is to wait for an answer
        self.has_card = True
        self.knows_the_words = True
        self.faults = []          # what goes wrong with the next files that arrive, one each
        self.words = []           # every line it was given
        self.arrived = []         # the path of every file that arrived whole
        self.taken = 0            # bytes of files, whole or not
        self.waiting = b""
        self.dead = False
        self.stopped = False
        self.near, far = socket.socketpair()
        self.far = far
        self.link = SocketLink(far)
        self.start()

    def stop(self):
        self.stopped = True
        self.join(2)
        self.near.close()
        self.far.close()

    def more(self, seconds):
        ready, _, _ = select.select([self.near], [], [], seconds)
        if not ready:
            return False
        data = self.near.recv(65536)
        if not self.dead:
            self.waiting += data
        return bool(data)

    def reply(self, line):
        self.near.sendall(line.encode("utf-8") + b"\r\n")

    def run(self):
        line = b""
        overflowed = False
        while not self.stopped:
            if not self.waiting:
                self.more(0.05)
                continue
            c, self.waiting = self.waiting[:1], self.waiting[1:]
            if c == b"\r":
                continue
            if c != b"\n":
                if len(line) < self.LONGEST_LINE:
                    line += c
                else:
                    overflowed = True
                continue
            if overflowed:
                self.reply("#error line too long")
            elif not line:
                self.reply("#")
            else:
                self.carry_out(line.decode("utf-8", "replace"))
            line = b""
            overflowed = False

    def real(self, path):
        return os.path.join(self.card, *[name for name in path.split("/") if name])

    def good(self, path):
        if path == "" or len(path) > self.LONGEST_PATH or path[0] != "/":
            return False
        if len(path) > 1 and path[-1] == "/":
            return False
        for c in path:
            if c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/._-":
                return False
        for name in path[1:].split("/"):
            if (name == "" and path != "/") or name == "." or ".." in name:
                return False
        return True

    def carry_out(self, line):
        self.words.append(line)
        word, _, rest = line.partition(" ")
        if word not in ("df", "ls", "crc", "rm", "mkdir", "put") or not self.knows_the_words:
            self.reply("#error unknown command")
        elif not self.has_card:
            self.reply("#error no card")
        elif word == "df":
            self.reply("#df 8000000000 1000000")
        elif word == "put":
            self.put(rest)
        elif not self.good(rest):
            self.reply("#error bad path")
        else:
            getattr(self, word)(rest, self.real(rest))

    def ls(self, path, real):
        if not os.path.exists(real):
            self.reply("#error not there")
        elif not os.path.isdir(real):
            self.reply("#error not a folder")
        else:
            names = os.listdir(real)
            for name in names:
                whole = os.path.join(real, name)
                if os.path.isdir(whole):
                    self.reply("#dir %s" % name)
                else:
                    self.reply("#file %d %s" % (os.path.getsize(whole), name))
            self.reply("#end %d" % len(names))

    def crc(self, path, real):
        if not os.path.exists(real):
            self.reply("#error not there")
        elif os.path.isdir(real):
            self.reply("#error not a file")
        else:
            with open(real, "rb") as source:
                data = source.read()
            self.reply("#crc %08x %d" % (zlib.crc32(data) & 0xFFFFFFFF, len(data)))

    def rm(self, path, real):
        if path == "/":
            self.reply("#error bad path")
        elif not os.path.exists(real):
            self.reply("#error not there")
        else:
            if os.path.isdir(real):
                shutil.rmtree(real)
            else:
                os.remove(real)
            self.reply("#ok")

    def mkdir(self, path, real):
        so_far = self.card
        for name in [name for name in path.split("/") if name]:
            so_far = os.path.join(so_far, name)
            if os.path.isdir(so_far):
                continue
            if os.path.exists(so_far):
                self.reply("#error in the way")
                return
            os.mkdir(so_far)
        self.reply("#ok")

    def take(self, count):
        """The next bytes of a file, or None after too long a time without one."""
        last = time.time()
        while len(self.waiting) < count:
            if self.stopped:
                return None
            if self.more(0.02):
                last = time.time()
            elif time.time() - last > self.patience:
                self.waiting = b""
                return None
        data, self.waiting = self.waiting[:count], self.waiting[count:]
        return data

    def put(self, rest):
        fields = rest.split(" ")
        if len(fields) != 3:
            self.reply("#error put takes a path, a size and a crc")
            return
        path, size, announced = fields
        if not self.good(path) or path in ("/", self.INCOMING):
            self.reply("#error bad path")
            return
        digits = size != "" and len(size) <= 10 and all(c in "0123456789" for c in size)
        hexes = len(announced) == 8 and all(c in "0123456789abcdefABCDEF" for c in announced)
        if not digits or not hexes or int(size) > 0xFFFFFFFF:
            self.reply("#error put takes a path, a size and a crc")
            return
        size = int(size)
        announced = int(announced, 16)
        target = self.real(path)
        if not os.path.isdir(os.path.dirname(target)):
            self.reply("#error no folder")
            return
        if os.path.isdir(target):
            self.reply("#error in the way")
            return
        fault = self.faults.pop(0) if self.faults else None
        part = self.real(self.INCOMING)
        if os.path.isdir(part):
            self.reply("#error cannot open")
            return
        out = open(part, "wb")
        self.reply("#ready %d" % self.piece)
        crc = 0
        got = 0
        while got < size:
            want = min(self.piece, size - got)
            data = self.take(want)
            if data is None:
                out.close()
                os.remove(part)
                self.reply("#error timeout")
                return
            self.taken += want
            if fault == "starts anew":
                out.close()  # and the part stays on the card, as it does when the power goes
                self.reply(BOOT_LINE)
                return
            if fault == "falls silent":
                out.close()
                self.dead = True
                return
            if fault == "wrong crc" and got == 0:
                data = bytes([data[0] ^ 0x20]) + data[1:]
            out.write(data)
            crc = zlib.crc32(data, crc)
            got += want
            if fault == "loses an answer" and got == want:
                continue
            if fault == "answers late" and got == want:
                time.sleep(self.slow * 0.8)  # longer than the tool waits before it knocks elsewhere
            self.reply("#got %d" % got)
        out.close()
        crc &= 0xFFFFFFFF
        if crc != announced:
            os.remove(part)
            self.reply("#error wrong crc %08x" % crc)
            return
        if fault == "damaged":
            with open(part, "r+b") as written:
                first = written.read(1)
                written.seek(0)
                written.write(bytes([first[0] ^ 0x01]))
        if os.path.exists(target):
            os.remove(target)
        os.rename(part, target)
        self.arrived.append(path)
        self.reply("#done %08x" % crc)


# ---------------------------------------------------------------------------------------------
# The compiled device: src/files.cpp with a pretended Arduino around it

STAND_IN = {}

STAND_IN["Arduino.h"] = r"""
// Stands in for the Arduino core: only what src/files.cpp uses.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>

typedef bool boolean;

class String {
public:
    String(const char* text = "") : _text(text ? text : "") {}
    unsigned int length() const { return static_cast<unsigned int>(_text.size()); }
    const char* c_str() const { return _text.c_str(); }

private:
    std::string _text;
};

uint32_t millis();
void delay(uint32_t ms);

class UsbPort {
public:
    int available();
    int read();
    size_t read(uint8_t* buffer, size_t size);
    size_t println(const char* line);
    void flush() {}
    size_t setRxBufferSize(size_t size);
};

extern UsbPort Serial;
"""

STAND_IN["hal/usb_serial_jtag_ll.h"] = r"""
// Stands in for the driver of the USB port: only what src/files.cpp uses, to stop it listening
// while its queue is replaced.
#pragma once
#include <cstdint>

#define USB_SERIAL_JTAG_INTR_SERIAL_OUT_RECV_PKT (1u << 2)

void usb_serial_jtag_ll_disable_intr_mask(uint32_t mask);
void usb_serial_jtag_ll_ena_intr_mask(uint32_t mask);
"""

STAND_IN["FS.h"] = r"""
// Stands in for the FS library of the Arduino core, with the same names and the same manners.
#pragma once
#include <Arduino.h>

#include <memory>

#define FILE_READ "r"
#define FILE_WRITE "w"

namespace fs {

struct Opened;

class File {
public:
    File() {}
    File(std::shared_ptr<Opened> opened) : _opened(opened) {}
    operator bool() const;
    boolean isDirectory();
    size_t size() const;
    size_t read(uint8_t* buffer, size_t size);
    size_t write(const uint8_t* buffer, size_t size);
    void close();
    String getNextFileName(boolean* isDir);

private:
    std::shared_ptr<Opened> _opened;
};

class FS {
public:
    File open(const char* path, const char* mode = FILE_READ, const bool create = false);
    bool exists(const char* path);
    bool remove(const char* path);
    bool rename(const char* pathFrom, const char* pathTo);
    bool mkdir(const char* path);
    bool rmdir(const char* path);
};

}  // namespace fs

using fs::File;
"""

STAND_IN["stand_in.cpp"] = r"""
// The USB port is two files: what the computer sends is added to one, what the device answers
// to the other. The card is a folder.
#include <Arduino.h>
#include <FS.h>

#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <chrono>
#include <cstdio>
#include <cstring>

#include "card.h"
#include "files.h"
#include "hal/usb_serial_jtag_ll.h"

namespace {

std::string cardFolder;
bool cardIn = true;
int fromComputer = -1;
int toComputer   = -1;
std::string unread;
size_t queueHolds = 256;  // 0: there is no queue
bool canWiden     = false;
bool listening    = true;  // whether what arrives is put into the queue
fs::FS theCard;

std::string real(const char* path)
{
    return cardFolder + path;
}

void reply(const char* line)
{
    Serial.println(line);
    Serial.flush();
}

}  // namespace

uint32_t millis()
{
    static const auto start = std::chrono::steady_clock::now();
    return static_cast<uint32_t>(
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count());
}

void delay(uint32_t ms)
{
    usleep(ms * 1000);
}

UsbPort Serial;

void usb_serial_jtag_ll_disable_intr_mask(uint32_t mask)
{
    if (mask & USB_SERIAL_JTAG_INTR_SERIAL_OUT_RECV_PKT) {
        listening = false;
    }
}

void usb_serial_jtag_ll_ena_intr_mask(uint32_t mask)
{
    if (mask & USB_SERIAL_JTAG_INTR_SERIAL_OUT_RECV_PKT) {
        listening = true;
    }
}

int UsbPort::available()
{
    if (!listening) {
        // On the real port nothing would arrive any more.
        listening = true;
        println("#error the port was left deaf");
        exit(5);
    }
    if (queueHolds == 0) {
        return -1;
    }
    char chunk[4096];
    for (;;) {
        const ssize_t got = ::read(fromComputer, chunk, sizeof(chunk));
        if (got <= 0) {
            break;
        }
        unread.append(chunk, static_cast<size_t>(got));
    }
    if (unread.size() > queueHolds) {
        // The real port would have dropped bytes: the computer sent more than the queue holds.
        println("#error the queue of the port ran over");
        exit(3);
    }
    return static_cast<int>(unread.size());
}

int UsbPort::read()
{
    if (available() <= 0) {
        return -1;
    }
    const int c = static_cast<unsigned char>(unread[0]);
    unread.erase(0, 1);
    return c;
}

size_t UsbPort::read(uint8_t* buffer, size_t size)
{
    available();
    const size_t count = size < unread.size() ? size : unread.size();
    memcpy(buffer, unread.data(), count);
    unread.erase(0, count);
    return count;
}

size_t UsbPort::println(const char* line)
{
    const std::string whole = std::string(line) + "\r\n";
    return static_cast<size_t>(::write(toComputer, whole.data(), whole.size()));
}

// As the real one: the old queue is gone in any case, and what it held with it.
size_t UsbPort::setRxBufferSize(size_t size)
{
    if (listening) {
        // On the real port what arrives just then would be put into a queue that is gone.
        println("#error the queue was replaced while the port listened");
        exit(4);
    }
    unread.clear();
    queueHolds = (size > 256 && !canWiden) ? 0 : size;
    return queueHolds;
}

namespace fs {

struct Opened {
    FILE* file = nullptr;
    DIR* folder = nullptr;
    std::string path;
    size_t size = 0;
    bool written = false;
};

File::operator bool() const
{
    return _opened && (_opened->file || _opened->folder);
}

boolean File::isDirectory()
{
    return _opened && _opened->folder;
}

size_t File::size() const
{
    if (!_opened || !_opened->file) {
        return 0;
    }
    if (_opened->written) {
        struct stat st;
        fflush(_opened->file);
        if (stat(real(_opened->path.c_str()).c_str(), &st) == 0) {
            return static_cast<size_t>(st.st_size);
        }
    }
    return _opened->size;
}

size_t File::read(uint8_t* buffer, size_t size)
{
    if (!_opened || !_opened->file || !buffer || !size) {
        return 0;
    }
    return fread(buffer, 1, size, _opened->file);
}

size_t File::write(const uint8_t* buffer, size_t size)
{
    if (!_opened || !_opened->file || !buffer || !size) {
        return 0;
    }
    _opened->written = true;
    return fwrite(buffer, 1, size, _opened->file);
}

void File::close()
{
    if (!_opened) {
        return;
    }
    if (_opened->file) {
        fclose(_opened->file);
        _opened->file = nullptr;
    }
    if (_opened->folder) {
        closedir(_opened->folder);
        _opened->folder = nullptr;
    }
}

String File::getNextFileName(boolean* isDir)
{
    if (!_opened || !_opened->folder) {
        return "";
    }
    for (;;) {
        struct dirent* entry = readdir(_opened->folder);
        if (!entry) {
            return "";
        }
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;  // a FAT card does not name these
        }
        std::string whole = _opened->path;
        if (whole.empty() || whole.back() != '/') {
            whole += "/";
        }
        whole += entry->d_name;
        struct stat st;
        if (isDir) {
            *isDir = stat(real(whole.c_str()).c_str(), &st) == 0 && S_ISDIR(st.st_mode);
        }
        return String(whole.c_str());
    }
}

File FS::open(const char* path, const char* mode, const bool)
{
    if (!path || path[0] != '/') {
        return File();
    }
    auto opened  = std::make_shared<Opened>();
    opened->path = path;
    struct stat st;
    if (stat(real(path).c_str(), &st) == 0) {
        if (S_ISDIR(st.st_mode)) {
            opened->folder = opendir(real(path).c_str());
        } else {
            opened->file = fopen(real(path).c_str(), mode);
            opened->size = static_cast<size_t>(st.st_size);
        }
    } else if (mode && mode[0] != 'r') {
        opened->file = fopen(real(path).c_str(), mode);
    }
    if (!opened->file && !opened->folder) {
        return File();
    }
    return File(opened);
}

bool FS::exists(const char* path)
{
    File there = open(path);
    const bool is = there;
    there.close();
    return is;
}

bool FS::remove(const char* path)
{
    File there = open(path);
    const bool isFile = there && !there.isDirectory();
    there.close();
    return isFile && unlink(real(path).c_str()) == 0;
}

bool FS::rename(const char* pathFrom, const char* pathTo)
{
    struct stat st;
    if (!exists(pathFrom) || stat(real(pathTo).c_str(), &st) == 0) {
        return false;  // a FAT card does not rename onto what is there
    }
    return ::rename(real(pathFrom).c_str(), real(pathTo).c_str()) == 0;
}

bool FS::mkdir(const char* path)
{
    File there = open(path);
    if (there) {
        const bool isFolder = there.isDirectory();
        there.close();
        return isFolder;
    }
    return ::mkdir(real(path).c_str(), 0777) == 0;
}

bool FS::rmdir(const char* path)
{
    File there = open(path);
    const bool isFolder = there && there.isDirectory();
    there.close();
    return isFolder && ::rmdir(real(path).c_str()) == 0;
}

}  // namespace fs

bool cardBegin()
{
    return cardIn;
}

bool cardReady()
{
    return cardIn;
}

fs::FS& cardFiles()
{
    return theCard;
}

uint64_t cardBytesTotal()
{
    return cardIn ? 8000000000ull : 0;
}

uint64_t cardBytesUsed()
{
    return cardIn ? 1000000ull : 0;
}

// Reads lines as src/console.cpp does, and knows the words for the card only.
int main(int count, char** arguments)
{
    if (count < 5) {
        return 2;
    }
    cardFolder   = arguments[1];
    fromComputer = open(arguments[2], O_RDONLY);
    toComputer   = open(arguments[3], O_WRONLY | O_APPEND);
    cardIn       = std::string(arguments[4]) == "card";
    canWiden     = count > 5 && std::string(arguments[5]) == "wide";
    if (fromComputer < 0 || toComputer < 0) {
        return 2;
    }
    const size_t longestLine = 200;
    std::string pending;
    bool overflowed = false;
    for (;;) {
        while (Serial.available() > 0) {
            const int c = Serial.read();
            if (c == '\r') {
                continue;
            }
            if (c != '\n') {
                if (pending.size() < longestLine) {
                    pending.push_back(static_cast<char>(c));
                } else {
                    overflowed = true;
                }
                continue;
            }
            if (overflowed) {
                reply("#error line too long");
            } else if (pending.empty()) {
                reply("#");
            } else if (pending == "switch off") {
                return 0;
            } else {
                const size_t space     = pending.find(' ');
                const std::string word = pending.substr(0, space);
                const std::string rest = (space == std::string::npos) ? std::string() : pending.substr(space + 1);
                if (!filesCarryOut(word, rest, reply)) {
                    reply("#error unknown command");
                }
            }
            pending.clear();
            overflowed = false;
        }
        delay(1);
    }
}
"""


class FileLink:
    def __init__(self, to_device, from_device, process):
        self.out = os.open(to_device, os.O_WRONLY | os.O_APPEND)
        self.back = os.open(from_device, os.O_RDONLY)
        self.from_device = from_device
        self.process = process

    def write(self, data):
        os.write(self.out, data)

    def last_words(self):
        with open(self.from_device, "rb") as said:
            lines = said.read().decode("utf-8", "replace").splitlines()
        return lines[-1] if lines else ""

    def read_some(self, seconds):
        end = time.time() + seconds
        while True:
            ended = self.process.poll()
            data = os.read(self.back, 65536)
            if data or time.time() >= end:
                return data
            if ended is not None:
                # Waiting for every answer of a device that is no more would take minutes.
                raise Failure("the compiled device ended with %s, saying %r" % (ended, self.last_words()))
            time.sleep(0.001)

    def close(self):
        os.close(self.out)
        os.close(self.back)


def environment():
    env = dict(os.environ)
    if "EMSDK_PYTHON" not in env:
        for candidate in ("/opt/homebrew/bin/python3", "/usr/local/bin/python3"):
            if os.path.exists(candidate):
                env["EMSDK_PYTHON"] = candidate
                break
    return env


BUILT = []


def built():
    """The compiled device as a file for Node, or the reason why there is none."""
    if BUILT:
        return BUILT[0]
    if not shutil.which("em++"):
        BUILT.append("SKIPPED: Emscripten is not installed")
    elif not shutil.which("node"):
        BUILT.append("SKIPPED: Node is not installed")
    else:
        folder = os.path.join(WORK, "compiled")
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)
        for name, text in STAND_IN.items():
            os.makedirs(os.path.dirname(os.path.join(folder, name)), exist_ok=True)
            with open(os.path.join(folder, name), "w", encoding="utf-8") as out:
                out.write(text.lstrip("\n"))
        program = os.path.join(folder, "device.js")
        # The firmware is built as gnu++11 and for the USB port of the chip itself, so this is too.
        result = subprocess.run(["em++", "-O1", "-std=gnu++11", "-Wall", "-Wextra", "-sNODERAWFS=1",
                                 "-sEXIT_RUNTIME=1", "-DARDUINO_USB_MODE=1", "-DARDUINO_USB_CDC_ON_BOOT=1",
                                 "-I" + folder, "-I" + os.path.join(ROOT, "src"),
                                 os.path.join(ROOT, "src", "files.cpp"), os.path.join(folder, "stand_in.cpp"),
                                 "-o", program], env=environment(), capture_output=True, text=True)
        noise = ("cache:INFO", "system_libs:INFO", "ports:INFO", "shared:INFO")
        said = "\n".join(line for line in (result.stdout + result.stderr).splitlines() if not line.startswith(noise))
        if result.returncode != 0:
            raise Failure("src/files.cpp did not compile:\n" + said)
        if "warning" in said:
            raise Failure("src/files.cpp compiled with warnings:\n" + said)
        BUILT.append(program)
    return BUILT[0]


class Compiled:
    name_of_kind = "compiled"

    def __init__(self, card, has_card=True, wide=False):
        """wide: whether the queue of its USB port can be made wider, as on the device."""
        self.card = card
        self.patience = 3.0
        self.slow = 10.0
        self.piece = 2048 if wide else 192
        self.words = None
        folder = os.path.dirname(card)
        to_device = os.path.join(folder, "to_device.bin")
        from_device = os.path.join(folder, "from_device.bin")
        for path in (to_device, from_device):
            open(path, "wb").close()
        self.process = subprocess.Popen(["node", built(), card, to_device, from_device,
                                         "card" if has_card else "no card", "wide" if wide else "narrow"],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.link = FileLink(to_device, from_device, self.process)

    def stop(self):
        self.link.write(b"switch off\n")
        try:
            said, _ = self.process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            said, _ = self.process.communicate()
        self.link.close()
        if self.process.returncode != 0:
            raise Failure("the compiled device ended with %s, saying %r %s" % (
                self.process.returncode, self.link.last_words(), said.decode("utf-8", "replace")))


# ---------------------------------------------------------------------------------------------
# Helpers

def bytes_of(seed, count):
    return random.Random(seed).getrandbits(8 * count).to_bytes(count, "little") if count else b""


def write_files(folder, files):
    for path, data in files.items():
        whole = os.path.join(folder, *path.split("/"))
        os.makedirs(os.path.dirname(whole), exist_ok=True)
        if data is None:
            os.makedirs(whole, exist_ok=True)
        else:
            with open(whole, "wb") as out:
                out.write(data)


def tree(folder):
    """Everything under a folder: path -> bytes, folders as path/ -> None."""
    found = {}
    for here, folders, names in os.walk(folder):
        inside = os.path.relpath(here, folder).replace(os.sep, "/")
        above = "" if inside == "." else inside + "/"
        for name in folders:
            found[above + name + "/"] = None
        for name in names:
            with open(os.path.join(here, name), "rb") as source:
                found[above + name] = source.read()
    return found


def clips():
    """A small folder of the kind the tool is for. Sizes around the size of a piece on purpose."""
    return {
        "audio/f/signs/sign-eki.wav": bytes_of(1, 3000),
        "audio/f/signs/sign-deguchi.wav": bytes_of(2, 512),
        "audio/f/numbers/n-1.wav": bytes_of(3, 513),
        "audio/m/signs/sign-eki.wav": bytes_of(4, 1),
        "audio/m/signs/sign-deguchi.wav": bytes_of(5, 1024),
        "audio/m/empty.wav": b"",
        "audio/guide/": None,
        "notes.txt": b"what this card is for\n",
    }


class Bench:
    """A folder here, a device with its card, and the tool between them."""

    def __init__(self, name, files=None, kind=Pretended, **how):
        self.folder = os.path.join(WORK, name.replace(" ", "_"), kind.name_of_kind)
        shutil.rmtree(self.folder, ignore_errors=True)
        self.here = os.path.join(self.folder, "here")
        self.card = os.path.join(self.folder, "card")
        os.makedirs(self.here)
        os.makedirs(self.card)
        write_files(self.here, clips() if files is None else files)
        self.device = kind(self.card, **how)
        self.link = self.device.link

    def sync(self, *options):
        """Runs the tool as from the command line. Returns how it ended and what it printed."""
        card = sd_sync.Card(self.link, patience=self.device.patience, slow=self.device.slow)
        out = io.StringIO()
        ended = sd_sync.main([self.here] + list(options), connect=lambda port: (card, None), out=out)
        return ended, out.getvalue()

    def words(self, *which):
        return [line for line in self.device.words if line.split(" ")[0] in which]

    def close(self):
        self.device.stop()

    def __enter__(self):
        return self

    def __exit__(self, *failure):
        self.close()


def kinds():
    """The devices a test runs against, and a remark if the compiled one is missing."""
    program = built()
    if program.startswith("SKIPPED"):
        return [Pretended], program
    return [Pretended, Compiled], None


def on_both(check):
    which, remark = kinds()
    for kind in which:
        try:
            check(kind)
        except Failure as failure:
            raise Failure("with the %s device: %s" % (kind.name_of_kind, failure))
    return remark


def hear(link, seconds=5.0, pending=b""):
    """The next line a device says, and what came after it. None if it says nothing."""
    end = time.time() + seconds
    while b"\n" not in pending:
        if time.time() >= end:
            return None, pending
        pending += link.read_some(0.05)
    raw, pending = pending.split(b"\n", 1)
    return raw.decode("utf-8", "replace").rstrip("\r"), pending


def ask(link, line, seconds=5.0, data=None):
    """Says one line to a device and returns its answer lines, up to the one that ends the answer.

    With data, the line is a put: the pieces are sent as the device asks for them."""
    link.write(line.encode("utf-8") + b"\n")
    lines = []
    pending = b""
    sent = 0
    piece = 0
    while True:
        text, pending = hear(link, seconds, pending)
        if text is None:
            return lines + ["(nothing more within %.0f seconds)" % seconds]
        lines.append(text)
        word = text.split(" ")[0]
        if word == "#ready":
            piece = int(text.split(" ")[1])
        if word in ("#ready", "#got"):
            if data is not None and sent < len(data):
                link.write(data[sent:sent + piece])
                sent += piece
        elif word not in ("#file", "#dir"):
            return lines


def sent_lines(said):
    """The lines of the tool about files it sent, in words."""
    lines = [line.split() for line in said.splitlines()]
    return [words for words in lines if len(words) > 2 and words[1] == "sent" and words[2].startswith("/")]


def put_line(path, data, crc=None):
    return "put %s %d %08x" % (path, len(data), zlib.crc32(data) & 0xFFFFFFFF if crc is None else crc)


# ---------------------------------------------------------------------------------------------
# The tool

def test_first_sync_sends_everything():
    def check(kind):
        with Bench("first sync", kind=kind) as bench:
            ended, said = bench.sync()
            same(ended, 0, "the tool ended with\n" + said)
            same(tree(bench.card), tree(bench.here), "the card")
            expect("7 sent" in said and "0 failed" in said, "the total is wrong:\n" + said)
            for path in clips():
                if not path.endswith("/"):
                    expect(sum(1 for words in sent_lines(said) if words[2] == "/" + path) == 1,
                           "no line, or more than one, for %s:\n%s" % (path, said))
            expect("KB/s" in said or "B/s" in said, "no speed is shown:\n" + said)
            expect("made     /audio/guide" in said, "the empty folder was not made:\n" + said)
    return on_both(check)


def test_second_sync_sends_nothing():
    def check(kind):
        with Bench("second sync", kind=kind) as bench:
            bench.sync()
            before = tree(bench.card)
            if kind is Pretended:
                bench.device.taken = 0
                del bench.device.words[:]
            ended, said = bench.sync()
            same(ended, 0, "the tool ended with\n" + said)
            expect("0 sent" in said and "7 the same" in said, "the total is wrong:\n" + said)
            expect(not sent_lines(said) and "made" not in said, "something was done:\n" + said)
            same(tree(bench.card), before, "the card")
            if kind is Pretended:
                same(bench.device.taken, 0, "bytes of files sent")
                same(bench.words("put", "rm", "mkdir"), [], "words that change the card")
                same(len(bench.words("crc")), 7, "files asked for their CRC-32")
    return on_both(check)


def test_changed_files_are_sent_again():
    def check(kind):
        with Bench("changed", kind=kind) as bench:
            bench.sync()
            changed = clips()
            changed["audio/f/signs/sign-eki.wav"] = bytes_of(11, 3000)   # other bytes, as many
            changed["audio/m/signs/sign-deguchi.wav"] = bytes_of(12, 700)  # shorter
            changed["audio/m/empty.wav"] = b"no longer empty"
            changed["audio/guide/guide-vowels-1.wav"] = bytes_of(13, 900)  # new
            write_files(bench.here, changed)
            ended, said = bench.sync()
            same(ended, 0, "the tool ended with\n" + said)
            same(tree(bench.card), tree(bench.here), "the card")
            expect("4 sent" in said and "4 the same" in said, "the total is wrong:\n" + said)
            sent = sorted((words[2], words[-1]) for words in sent_lines(said))
            same(sent, [("/audio/f/signs/sign-eki.wav", "changed"), ("/audio/guide/guide-vowels-1.wav", "new"),
                        ("/audio/m/empty.wav", "changed"), ("/audio/m/signs/sign-deguchi.wav", "changed")],
                 "what was sent")
    return on_both(check)


def test_quick_believes_the_size():
    with Bench("quick") as bench:
        bench.sync()
        write_files(bench.here, {"audio/f/signs/sign-eki.wav": bytes_of(11, 3000), "notes.txt": b"shorter\n"})
        del bench.device.words[:]
        ended, said = bench.sync("--quick")
        same(ended, 0, "the tool ended with\n" + said)
        same([line.split(" ")[1] for line in bench.words("put")], ["/notes.txt"], "files sent")
        same(len(bench.words("crc")), 1, "questions for a CRC-32: only that of the file sent")


def test_wrong_crc_is_repaired():
    with Bench("wrong crc") as bench:
        bench.device.faults = ["wrong crc"]
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")
        expect("at try 2" in said, "the second try is not mentioned:\n" + said)
        same(len(bench.words("put")), 8, "files sent, one of them twice")


def test_damaged_file_is_found_and_sent_again():
    with Bench("damaged") as bench:
        bench.device.faults = ["damaged"]
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")
        expect("at try 2" in said, "the second try is not mentioned:\n" + said)


def test_file_that_stays_damaged_is_reported_and_removed():
    files = {"audio/a.wav": bytes_of(1, 700), "audio/b.wav": bytes_of(2, 700), "audio/c.wav": bytes_of(3, 700)}
    with Bench("stays damaged", files) as bench:
        bench.device.faults = [None, "damaged", "damaged", "damaged"]
        ended, said = bench.sync()
        same(ended, 1, "the tool ended with\n" + said)
        expect("FAILED   /audio/b.wav" in said and "other bytes" in said, "the file is not reported:\n" + said)
        expect("1 failed" in said and "2 sent" in said, "the total is wrong:\n" + said)
        del files["audio/b.wav"]
        want = dict(files)
        want["audio/"] = None
        same(tree(bench.card), want, "the card: the damaged file must not stay")


def test_lost_answer_is_repaired():
    with Bench("lost answer") as bench:
        bench.device.faults = ["loses an answer"]
        started = time.time()
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")
        expect("at try 2" in said, "the second try is not mentioned:\n" + said)
        expect(time.time() - started < 20, "it took %.0f seconds" % (time.time() - started))


def test_device_that_starts_anew_is_waited_for():
    with Bench("starts anew") as bench:
        bench.device.faults = [None, "starts anew"]
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        want = tree(bench.here)
        same(tree(bench.card), want, "the card: also the part that was left must be gone")


def test_part_left_on_the_card_is_removed():
    with Bench("part left") as bench:
        write_files(bench.card, {"incoming.part": b"half a clip"})
        ended, said = bench.sync("--dry-run")
        expect(os.path.exists(os.path.join(bench.card, "incoming.part")), "a dry run removed it")
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")

        # Also when no file is sent: the next file that arrives would else hide that it stayed.
        write_files(bench.card, {"incoming.part": b"half a clip"})
        del bench.device.words[:]
        ended, said = bench.sync()
        same(ended, 0, "with nothing to send the tool ended with\n" + said)
        same(bench.words("put"), [], "files sent")
        same(bench.words("rm"), ["rm /incoming.part"], "words that remove")
        same(tree(bench.card), tree(bench.here), "the card when nothing was sent")


def test_silent_device_is_reported():
    with Bench("silent") as bench:
        bench.device.faults = [None, None, "falls silent"]
        started = time.time()
        ended, said = bench.sync()
        same(ended, 2, "the tool ended with\n" + said)
        expect("does not answer any more" in said and "Start again" in said, "it does not say so:\n" + said)
        expect(time.time() - started < 20, "it took %.0f seconds" % (time.time() - started))
        expect(not os.path.exists(os.path.join(bench.card, "audio", "f", "signs", "sign-eki.wav")),
               "the file that was on its way has a name on the card")


def test_stopped_and_started_again():
    with Bench("stopped") as bench:
        bench.link = StoppingLink(bench.device.far, after=2600)
        ended, said = bench.sync()
        same(ended, 130, "the tool ended with\n" + said)
        expect("Start again" in said, "it does not say how to go on:\n" + said)
        first = list(bench.device.arrived)
        expect(0 < len(first) < 7, "%d files arrived before it was stopped" % len(first))
        time.sleep(bench.device.patience + 0.2)  # as long as it takes to type the command again
        for path, data in tree(bench.card).items():
            if data is not None:
                same(data, tree(bench.here).get(path), "half a file on the card: " + path)

        del bench.device.arrived[:]
        bench.link = bench.device.link
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")
        same(sorted(set(first) & set(bench.device.arrived)), [], "sent twice")
        same(len(first) + len(bench.device.arrived), 7, "files that arrived in both runs")


def test_started_again_at_once():
    """The device may still wait for the rest of a file when the tool comes back."""
    with Bench("at once", {"audio/a.wav": bytes_of(1, 5000)}, patience=1.0) as bench:
        bench.link = StoppingLink(bench.device.far, after=1500)
        ended, said = bench.sync()
        same(ended, 130, "the tool ended with\n" + said)
        bench.link = bench.device.link
        ended, said = bench.sync()
        same(ended, 0, "the second run ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")


def test_tool_never_knocks_while_a_file_is_sent():
    """A knock there would be taken for a byte of the file."""
    with Bench("late answer") as bench:
        bench.device.faults = ["answers late"]
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")
        expect("at try" not in said, "a file had to be sent again:\n" + said)
        same(len(bench.words("put")), 7, "files sent")
        same(bench.device.taken, sum(len(data) for data in clips().values() if data), "bytes taken for files")


class StallingLink:
    """Holds back the second piece of the first file for some time, once: a computer that was busy."""

    def __init__(self, link, seconds):
        self.link = link
        self.seconds = seconds
        self.pieces = None  # None before the first file, then the pieces sent of it

    def write(self, data):
        if data.startswith(b"put ") and self.pieces is None:
            self.pieces = 0
        elif self.pieces is not None and self.pieces < 2:
            self.pieces += 1
            if self.pieces == 2:
                time.sleep(self.seconds)
        self.link.write(data)

    def read_some(self, seconds):
        return self.link.read_some(seconds)


def test_piece_that_comes_too_late():
    """The device has given up by then and takes the piece for words. The tool has to find back."""
    def check(kind):
        files = {"audio/a.wav": bytes_of(1, 5000), "audio/b.wav": bytes_of(2, 600)}
        with Bench("late piece", files, kind=kind) as bench:
            bench.link = StallingLink(bench.device.link, bench.device.patience + 0.3)
            ended, said = bench.sync()
            same(ended, 0, "the tool ended with\n" + said)
            same(tree(bench.card), tree(bench.here), "the card")
            expect("/audio/a.wav" in said and "at try 2" in said, "the second try is not mentioned:\n" + said)
    return on_both(check)


class BreakingFile:
    """A file here that cannot be read on after its first piece."""

    def __init__(self, real):
        self.real = real
        self.pieces = 0

    def read(self, count=-1):
        if 0 < count < (1 << 16):  # a piece for the device, not the reading for the CRC-32
            self.pieces += 1
            if self.pieces > 1:
                raise OSError(5, "Input/output error")
        return self.real.read(count)

    def __enter__(self):
        return self

    def __exit__(self, *failure):
        self.real.close()


def test_file_here_that_cannot_be_read_on():
    """The device is left waiting for the rest. The next word must not be taken for it."""
    files = {"audio/a.wav": bytes_of(1, 5000), "audio/b.wav": bytes_of(2, 600), "audio/c.wav": bytes_of(3, 600)}
    with Bench("cannot read on", files) as bench:
        write_files(bench.card, {"audio/b.wav": files["audio/b.wav"]})

        def breaking(path, mode="r", *more):
            real = open(path, mode, *more)
            return BreakingFile(real) if path.endswith("a.wav") else real
        sd_sync.open = breaking
        try:
            ended, said = bench.sync()
        finally:
            del sd_sync.open
        same(ended, 1, "the tool ended with\n" + said)
        lines = [line for line in said.splitlines() if line.startswith("FAILED")]
        expect(len(lines) == 1 and "a.wav: Input/output error" in lines[0], "what failed:\n" + said)
        expect("1 sent" in said and "1 the same" in said and "1 failed" in said, "the total is wrong:\n" + said)
        expect("at try" not in said, "the file after it had to be sent again:\n" + said)
        del files["audio/a.wav"]
        files["audio/"] = None
        same(tree(bench.card), files, "the card")


class SocketPort:
    """What the tool uses of a port opened by pyserial, over a socket. With a number of files
    given, it is gone after the first piece of the last of them."""

    def __init__(self, end, files=None):
        self.end = end
        self.files = files
        self.pieces = 0
        self.timeout = 0.05

    def gone(self):
        if self.files == 0 and self.pieces > 1:
            raise OSError(6, "Device not configured")

    @property
    def in_waiting(self):
        self.gone()
        ready, _, _ = select.select([self.end], [], [], 0)
        return len(self.end.recv(65536, socket.MSG_PEEK)) if ready else 0

    def read(self, count):
        self.gone()
        ready, _, _ = select.select([self.end], [], [], self.timeout)
        return self.end.recv(count) if ready else b""

    def write(self, data):
        if self.files and data.startswith(b"put "):
            self.files -= 1
        elif self.files == 0:
            self.pieces += 1
        self.gone()
        self.end.sendall(data)

    def flush(self):
        self.gone()


def test_usb_port_that_goes_away():
    """As when the cable is pulled. It is not the files here that fail then."""
    with Bench("port gone") as bench:
        bench.link = sd_sync.SerialLink(SocketPort(bench.device.far, files=3))
        ended, said = bench.sync()
        same(ended, 2, "the tool ended with\n" + said)
        expect("the USB port is gone (Device not configured)" in said and "Start again" in said,
               "it does not say so:\n" + said)
        expect("FAILED" not in said, "files are said to have failed:\n" + said)
        same(len(bench.words("put")), 3, "files sent or begun")
        same(len(bench.device.arrived), 2, "files that arrived")
        time.sleep(bench.device.patience + 0.2)
        for path, data in tree(bench.card).items():
            if data is not None:
                same(data, tree(bench.here).get(path), "half a file on the card: " + path)

    with Bench("port stays") as bench:
        bench.link = sd_sync.SerialLink(SocketPort(bench.device.far))
        ended, said = bench.sync()
        same(ended, 0, "with a port that stays the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")


def test_bad_names_are_refused():
    files = clips()
    bad = {
        "audio/f/two words.wav": "letters, digits",
        "audio/f/dot-at-the-end.": "drops a dot",
        "audio/dots./inside.wav": "drops a dot",
        "audio/f/eki\u99c5.wav": "letters, digits",
        "audio/f/semi;colon.wav": "letters, digits",
        "audio/f/two..dots.wav": "two dots in a row",
        "audio/" + "x" * 120 + ".wav": "letters, the device takes 120",
        "incoming.part": "uses this name itself",
        "bad folder/inside.wav": "letters, digits",
    }
    for path in bad:
        files[path] = b"never sent"
    longest = "audio/f/" + "y" * (119 - len("audio/f/"))
    files[longest] = b"120 letters with the folders and the first stroke"
    files["audio/.DS_Store"] = b"left out"
    files[".hidden/inside.wav"] = b"left out"
    with Bench("bad names", files) as bench:
        ended, said = bench.sync()
        same(ended, 1, "the tool ended with\n" + said)
        for path, why in bad.items():
            refused = path.split("/inside")[0]
            lines = [line for line in said.splitlines() if line.startswith("FAILED") and refused in line]
            expect(len(lines) == 1 and why in lines[0], "%r is not refused for %r:\n%s" % (refused, why, said))
        expect("9 failed" in said, "the total is wrong:\n" + said)
        expect("2 left out" in said, "what was left out is not counted:\n" + said)
        for line in bench.device.words:
            expect(line == "df" or bench.device.good(line.split(" ")[1]), "the device was told %r" % line)
        expect(bench.words("put", "crc"), "nothing was sent")
        want = clips()
        want[longest] = files[longest]
        write_files(bench.folder + "/want", want)
        same(tree(bench.card), tree(bench.folder + "/want"), "the card: all the rest must be there")


def test_names_the_card_cannot_tell_apart():
    """A FAT card takes A.WAV and a.wav for one name. Many a computer does too, so no folder is made."""
    folder = os.path.join(WORK, "case")
    shutil.rmtree(folder, ignore_errors=True)
    write_files(folder, {"a.wav": b"1"})
    whole = os.path.join(folder, "a.wav")
    why = sd_sync.Folder.wrong(whole, "/audio/A.WAV", {"/audio/a.wav": "audio/a.wav"})
    expect(why and "cannot tell it from audio/a.wav" in why, "A.WAV beside a.wav: %r" % why)
    same(sd_sync.Folder.wrong(whole, "/audio/b.wav", {"/audio/a.wav": "audio/a.wav"}), None, "b.wav beside a.wav")


def test_delete_removes_from_audio_only():
    def check(kind):
        with Bench("delete", kind=kind) as bench:
            bench.sync()
            extra = {
                "audio/f/signs/sign-old.wav": b"gone from the folder",
                "audio/old-voice/a/b/c.wav": b"a folder that is gone",
                "audio/old-voice/d.wav": b"and more in it",
                "audio/._sign-eki.wav": b"what a file manager leaves",
                "own/words.tsv": b"not under audio: stays",
                "key.txt": b"not under audio: stays",
            }
            write_files(bench.card, extra)
            ended, said = bench.sync()
            same(ended, 0, "without --delete the tool ended with\n" + said)
            expect("removed" not in said, "without --delete something was removed:\n" + said)
            for path in extra:
                expect(os.path.exists(os.path.join(bench.card, path)), "without --delete %s is gone" % path)

            ended, said = bench.sync("--delete")
            same(ended, 0, "the tool ended with\n" + said)
            removed = sorted(line.split()[1] for line in said.splitlines() if line.startswith("removed"))
            same(removed, ["/audio/._sign-eki.wav", "/audio/f/signs/sign-old.wav", "/audio/old-voice"], "removed")
            expect("3 removed" in said, "the total is wrong:\n" + said)
            want = tree(bench.here)
            want.update({"own/": None, "own/words.tsv": extra["own/words.tsv"], "key.txt": extra["key.txt"]})
            same(tree(bench.card), want, "the card")
    return on_both(check)


def test_delete_spares_what_cannot_be_read_here():
    """Of a folder that cannot be read here nobody knows what it holds."""
    for closed in ("audio/f/signs", "audio"):
        with Bench("delete unread " + closed.replace("/", " ")) as bench:
            bench.sync()
            write_files(bench.card, {"audio/m/old.wav": b"gone from the folder"})
            before = tree(bench.card)
            shut = os.path.join(bench.here, *closed.split("/"))
            os.chmod(shut, 0)
            try:
                try:
                    os.listdir(shut)
                    return "not tried: this user reads a folder that is closed to all"
                except OSError:
                    pass
                ended, said = bench.sync("--delete")
            finally:
                os.chmod(shut, 0o755)
            same(ended, 1, "with %s closed the tool ended with\n%s" % (closed, said))
            lines = [line for line in said.splitlines() if line.startswith("FAILED")]
            expect(len(lines) == 1 and shut in lines[0] and "cannot be read" in lines[0], "what failed:\n" + said)
            if closed == "audio":
                same(tree(bench.card), before, "the card")
            else:
                del before["audio/m/old.wav"]
                same(tree(bench.card), before, "the card: only what is known to be gone may go")


def test_delete_needs_an_audio_folder():
    with Bench("delete without audio", {"notes.txt": b"no audio here"}) as bench:
        write_files(bench.card, {"audio/f/a.wav": b"must stay"})
        before = tree(bench.card)
        ended, said = bench.sync("--delete")
        same(ended, 2, "the tool ended with\n" + said)
        expect("Nothing was done" in said, "it does not say why:\n" + said)
        same(tree(bench.card), before, "the card")
        same(bench.device.words, [], "words said to the device")


def test_delete_leaves_names_it_cannot_say():
    with Bench("delete odd names") as bench:
        bench.sync()
        write_files(bench.card, {"audio/two words.wav": b"odd", "audio/\x1b[31mred.wav": b"odd"})
        ended, said = bench.sync("--delete")
        same(ended, 1, "the tool ended with\n" + said)
        expect("2 failed" in said and "0 removed" in said, "the total is wrong:\n" + said)
        expect("\x1b" not in said and "\\x1b[31mred.wav" in said, "the name is printed as it is:\n%r" % said)
        same(bench.words("rm"), [], "words that remove")


def test_dry_run_changes_nothing():
    def check(kind):
        with Bench("dry run", kind=kind) as bench:
            write_files(bench.card, {"audio/f/signs/sign-eki.wav": bytes_of(1, 3000),       # the same
                                     "audio/f/signs/sign-deguchi.wav": bytes_of(9, 512),    # other bytes
                                     "audio/f/old.wav": b"gone from the folder"})
            before = tree(bench.card)
            ended, said = bench.sync("--dry-run", "--delete")
            same(ended, 0, "the tool ended with\n" + said)
            same(tree(bench.card), before, "the card")
            if kind is Pretended:
                same(bench.words("put", "rm", "mkdir"), [], "words that change the card")
            lines = said.splitlines()
            would_send = sorted((line.split()[3], line.split()[-1]) for line in lines if "would send" in line)
            same(would_send, [("/audio/f/numbers/n-1.wav", "new"), ("/audio/f/signs/sign-deguchi.wav", "changed"),
                              ("/audio/m/empty.wav", "new"), ("/audio/m/signs/sign-deguchi.wav", "new"),
                              ("/audio/m/signs/sign-eki.wav", "new"), ("/notes.txt", "new")], "would send")
            same(sorted(line.split()[2] for line in lines if line.startswith("would make")),
                 ["/audio/f/numbers", "/audio/guide", "/audio/m", "/audio/m/signs"], "would make")
            same([line.split()[2] for line in lines if line.startswith("would remove")], ["/audio/f/old.wav"],
                 "would remove")
            expect("6 would be sent" in said and "1 the same" in said and "1 would be removed" in said,
                   "the total is wrong:\n" + said)
            expect(not sent_lines(said) and "\nmade" not in said and "\nremoved" not in said,
                   "it claims to have done something:\n" + said)
    return on_both(check)


def test_something_in_the_way():
    files = {"audio/a.wav": b"a file here, a folder on the card", "audio/b/c.wav": b"a folder here, a file there",
             "audio/d.wav": b"fine"}
    with Bench("in the way", files) as bench:
        write_files(bench.card, {"audio/a.wav/x.wav": b"x", "audio/b": b"a file"})
        before = tree(bench.card)
        ended, said = bench.sync("--delete")
        same(ended, 1, "the tool ended with\n" + said)
        expect("FAILED   /audio/a.wav: a folder of that name is in the way" in said, said)
        expect("FAILED   /audio/b: a file of that name is in the way" in said, said)
        expect("FAILED   /audio/b/c.wav: its folder is not on the card" in said, said)
        expect("3 failed" in said and "1 sent" in said and "0 removed" in said, "the total is wrong:\n" + said)
        before["audio/d.wav"] = files["audio/d.wav"]
        same(tree(bench.card), before, "the card")


def test_no_card():
    def check(kind):
        how = {"has_card": False} if kind is Compiled else {}
        with Bench("no card", kind=kind, **how) as bench:
            if kind is Pretended:
                bench.device.has_card = False
            ended, said = bench.sync()
            same(ended, 2, "the tool ended with\n" + said)
            expect("no memory card" in said, "it does not say so:\n" + said)
            for line in ("df", "ls /", "crc /a", "rm /a", "mkdir /a", "put /a 1 00000000", "ls //", "put"):
                same(ask(bench.link, line), ["#error no card"], "the answer to %r" % line)
    return on_both(check)


def test_older_firmware():
    with Bench("older firmware") as bench:
        bench.device.knows_the_words = False
        ended, said = bench.sync()
        same(ended, 2, "the tool ended with\n" + said)
        expect("older than this tool" in said and "flash.py" in said, "it does not say what to do:\n" + said)


def test_card_without_room():
    def nearly_full(bench):
        real = bench.device.carry_out

        def carry_out(line):
            if line == "df":
                bench.device.words.append(line)
                bench.device.reply("#df 8000000000 7999999000")
            else:
                real(line)
        bench.device.carry_out = carry_out

    files = {"audio/large.wav": bytes_of(1, 4000), "audio/small.wav": b"fits"}
    with Bench("no room", files) as bench:
        nearly_full(bench)
        ended, said = bench.sync()
        same(ended, 1, "the tool ended with\n" + said)
        expect("FAILED   /audio/large.wav: the card has no room" in said, said)
        same([line.split(" ")[1] for line in bench.words("put")], ["/audio/small.wav"], "files sent")

    # What is replaced makes no room: the old file goes only when the new one is on the card.
    with Bench("no room to replace", files) as bench:
        nearly_full(bench)
        write_files(bench.card, {"audio/large.wav": bytes_of(2, 4000), "audio/small.wav": b"FITS"})
        ended, said = bench.sync()
        same(ended, 1, "with files to replace the tool ended with\n" + said)
        expect("FAILED   /audio/large.wav: the card has no room" in said, said)
        same([line.split(" ")[1] for line in bench.words("put")], ["/audio/small.wav"], "files sent to replace")
        same(tree(bench.card)["audio/large.wav"], bytes_of(2, 4000), "the file that could not be replaced")


def test_answer_nobody_expected():
    with Bench("unexpected") as bench:
        real = bench.device.carry_out

        def cannot_read(line):
            if line == "ls /audio/f":
                bench.device.words.append(line)
                bench.device.reply("#error cannot read")
            else:
                real(line)
        bench.device.carry_out = cannot_read
        ended, said = bench.sync()
        same(ended, 1, "the tool ended with\n" + said)
        expect("error: the device answered 'cannot read' to 'ls /audio/f'" in said, "it does not say so:\n" + said)
        same(bench.words("put"), [], "files sent after that")


class PretendedPort:
    """What the tool uses of a port opened by pyserial. Bytes arrive when their time has come."""

    def __init__(self, arrivals):
        self.started = time.time()
        self.arrivals = list(arrivals)  # (seconds after the start, bytes)
        self.written = b""
        self.flushed = 0
        self.timeout = 0.05

    @property
    def in_waiting(self):
        return sum(len(data) for after, data in self.arrivals if time.time() - self.started >= after)

    def read(self, count):
        end = time.time() + self.timeout
        while self.in_waiting == 0:
            if time.time() >= end:
                return b""
            time.sleep(0.002)
        after, data = self.arrivals.pop(0)
        if len(data) > count:
            self.arrivals.insert(0, (after, data[count:]))
        return data[:count]

    def write(self, data):
        self.written += data

    def flush(self):
        self.flushed += 1


def test_usb_port_is_read_without_waiting_longer_than_needed():
    port = PretendedPort([(0.0, b"#ready 2048\r\n"), (0.3, b"#got 20"), (0.32, b"48\r\n")])
    link = sd_sync.SerialLink(port)
    started = time.time()
    same(link.read_some(0), b"#ready 2048\r\n", "what was there already")
    same(link.read_some(0), b"", "when nothing is there and there is no time to wait")
    expect(time.time() - started < 0.04, "reading what is there took %.2f seconds" % (time.time() - started))
    same(link.read_some(0.1), b"", "when nothing comes in time")
    expect(0.09 < time.time() - started < 0.2, "waiting 0.1 seconds took %.2f" % (time.time() - started))
    got = link.read_some(5.0)
    expect(0.29 < time.time() - started < 0.4, "the first byte came after %.2f seconds" % (time.time() - started))
    while len(got) < 11:
        got += link.read_some(1.0)
    same(got, b"#got 2048\r\n", "what came later")
    link.write(b"abc")
    same((port.written, port.flushed), (b"abc", 1), "written and pushed out")

    card = sd_sync.Card(sd_sync.SerialLink(PretendedPort([(0.1, b"#df 1000 "), (0.2, b"10\r\n")])), slow=1.0)
    same(card.df(), (1000, 10), "an answer that comes in two parts")


def test_folder_that_is_not_there():
    out = io.StringIO()
    ended = sd_sync.main([os.path.join(WORK, "no such folder")], connect=None, out=out)
    same(ended, 2, "the tool ended with")
    expect("is not a folder" in out.getvalue(), out.getvalue())


def test_paths_are_judged_alike():
    """The rule for paths, three times: in the tool, in the pretended device, in src/files.cpp."""
    good = ["/", "/a", "/audio/f/signs/sign-eki.wav", "/" + "a" * 119, "/.hidden", "/a/.b", "/a.b-c_d/E9",
            "/a./b", "/-", "/_", "/0"]
    bad = ["", "a", "a/b", "/a/../b", "/..", "/a..b", "/...", "/a//b", "//", "/a b", " /a", "/a ", "/a/", "/a/b/",
           "/\u00e4", "/a/./b", "/.", "/a/.", "/./a", "/" + "a" * 120, "/a\tb", "/a*", "/a\\b", "/a:b", "/a?b",
           "/a\"b", "/a'b", "/a;b", "/a|b", "/a$b", "/a%b", "/a~b", "/a+b", "/a,b", "/a=b", "/a\x7fb", "/a\x00b"]
    pretended = Pretended.good
    for path in good:
        expect(sd_sync.good_path(path), "the tool refuses %r" % path)
        expect(pretended(Pretended, path), "the pretended device refuses %r" % path)
    for path in bad:
        expect(not sd_sync.good_path(path), "the tool takes %r" % path)
        expect(not pretended(Pretended, path), "the pretended device takes %r" % path)
    expect(not sd_sync.good_path("/a\n"), "the tool takes a path with a line end")

    def check(kind):
        with Bench("paths", {}, kind=kind) as bench:
            for path in bad:
                if "\n" in path or "\r" in path or "\x00" in path:
                    continue
                lines = [word + " " + path for word in ("ls", "crc", "rm", "mkdir")]
                if " " not in path:
                    lines.append("put %s 1 00000000" % path)
                for line in lines:
                    same(ask(bench.link, line), ["#error bad path"], "the answer to %r" % line)
            for word in ("ls", "crc", "rm", "mkdir"):
                same(ask(bench.link, word), ["#error bad path"], "the answer to %r alone" % word)
            same(tree(bench.card), {}, "the card")
            for path in good[1:]:
                same(ask(bench.link, "mkdir " + path), ["#ok"], "the answer to mkdir %r" % path)
                expect(os.path.isdir(os.path.join(bench.card, path[1:])), "mkdir %r made nothing" % path)
    return on_both(check)


# ---------------------------------------------------------------------------------------------
# The words, said to both devices

def conversation(link, piece):
    """Says the same to any device. Returns what was said and answered, made fit for comparing."""
    one = bytes_of(21, 3 * piece + 17)
    two = bytes_of(22, piece)
    said = []

    def say(line, data=None, seconds=5.0):
        answer = ask(link, line, seconds, data)
        entries = sorted(a for a in answer if a.startswith(("#file", "#dir")))
        others = [a for a in answer if not a.startswith(("#file", "#dir", "#got"))]
        others = ["#ready" if a.startswith("#ready") else a for a in others]
        said.append((line, entries + others))
        return answer

    say("")
    say("df")
    say("df /")
    say("ls /")
    say("mkdir /a/b/c")
    say("mkdir /a/b/c")
    say("mkdir /")
    say("ls /")
    say("ls /a")
    say("ls /a/b/c")
    say(put_line("/a/b/c/one.wav", one), one)
    say("crc /a/b/c/one.wav")
    say("ls /a/b/c")
    say(put_line("/a/b/c/one.wav", two), two)
    say("crc /a/b/c/one.wav")
    say(put_line("/a/b/c/two.wav", one, crc=0x12345678), one)
    say("ls /a/b/c")
    say("ls /")
    say(put_line("/a/b/c/none.wav", b""), b"")
    say("crc /a/b/c/none.wav")
    say(put_line("/a/b/c/byte.wav", b"\n"), b"\n")
    say("crc /a/b/c/byte.wav")
    say(put_line("/top.wav", two), two)
    say(put_line("/a/nowhere/x.wav", two))
    say(put_line("/a/b", two))
    say(put_line("/a/b/c/one.wav/x.wav", two))
    say(put_line("/", two))
    say(put_line("/incoming.part", two))
    say("put /a/x.wav")
    say("put /a/x.wav 5")
    say("put /a/x.wav 5 1234567")
    say("put /a/x.wav 5 123456789")
    say("put /a/x.wav 5 1234567g")
    say("put /a/x.wav -5 12345678")
    say("put /a/x.wav 5.0 12345678")
    say("put /a/x.wav 0x5 12345678")
    say("put /a/x.wav 4294967296 12345678")
    say("put /a/x.wav 12345678901 12345678")
    say("put /a/x.wav  5 12345678")
    say("put /a/x.wav 5 12345678 ")
    say("put /a/x.wav 5 12345678 9")
    say("put  5 12345678")
    say("put /a/x.wav 3 ABCDEF01", b"abc")
    say("ls /a")
    say("ls /a/b/c/one.wav")
    say("ls /nothing")
    say("ls /nothing/below")
    say("crc /a")
    say("crc /")
    say("crc /nothing")
    say("mkdir /a/b/c/one.wav")
    say("mkdir /a/b/c/one.wav/below")
    say("mkdir /top.wav/below/more")
    say("rm /nothing")
    say("rm /")
    say("rm /a/b/c/byte.wav")
    say("rm /a/b/c/byte.wav")
    say("ls /a/b/c")
    say("mkdir /a/b/d/e/f")
    say(put_line("/a/b/d/e/f/deep.wav", two), two)
    say(put_line("/a/b/d/e/mid.wav", one), one)
    say("mkdir /a/b/d/empty")
    say("rm /a/b")
    say("ls /a")
    say("ls /")
    say("rm /a")
    say("rm /top.wav")
    say("ls /")
    # a folder where the file that arrives is written
    say("mkdir /incoming.part/below")
    say(put_line("/late.wav", two), two)
    say("ls /")
    say("rm /incoming.part")
    say(put_line("/late.wav", two), two)
    say("rm /late.wav")
    say("ls /")
    # no word reads what a file holds
    for word in ("get", "cat", "read", "send", "type2", "cp", "mv", "dump", "open", "show"):
        say(word + " /top.wav")
    say("LS /")
    say("x" * 201)
    return said


def test_both_devices_answer_alike():
    program = built()
    if program.startswith("SKIPPED"):
        return program
    told = {}
    for kind in (Pretended, Compiled):
        with Bench("alike", {}, kind=kind) as bench:
            told[kind] = conversation(bench.link, 192)
            same(tree(bench.card), {}, "the card of the %s device at the end" % kind.name_of_kind)
    for ours, theirs in zip(told[Pretended], told[Compiled]):
        same(theirs[1], ours[1], "the compiled device answers %r otherwise than the pretended one" % ours[0])
    late = [answer for line, answer in told[Compiled] if line.startswith("put /late.wav")]
    same(late, [["#error cannot open"], ["#ready", "#done %08x" % (zlib.crc32(bytes_of(22, 192)) & 0xFFFFFFFF)]],
         "a file that arrives while a folder has the name of the part, and after the folder is gone")
    answers = dict(told[Compiled])
    same(answers["mkdir /a/b/c"], ["#ok"], "mkdir")
    same(answers["rm /a/b"], ["#ok"], "rm of a folder with folders in it")
    same(answers["crc /a/b/c/none.wav"], ["#crc 00000000 0"], "the CRC-32 of nothing")
    same(answers["crc /a/b/c/byte.wav"], ["#crc 32d70693 1"], "the CRC-32 of a line end")
    same(answers["get /top.wav"], ["#error unknown command"], "a word that would read a file")
    return "%d things said" % len(answers)


def test_pretended_device_alone():
    """The same conversation where there is no compiled device to compare with."""
    with Bench("alone", {}) as bench:
        answers = dict(conversation(bench.link, 192))
        same(tree(bench.card), {}, "the card at the end")
    same(answers[""], ["#"], "a knock")
    same(answers["df"], ["#df 8000000000 1000000"], "df")
    same(answers["rm /"], ["#error bad path"], "rm /")
    same(answers["rm /nothing"], ["#error not there"], "rm of nothing")
    same(answers["ls /nothing"], ["#error not there"], "ls of nothing")
    same(answers["ls /a/b/c/one.wav"], ["#error not a folder"], "ls of a file")
    same(answers["crc /a"], ["#error not a file"], "crc of a folder")
    same(answers["mkdir /a/b/c/one.wav"], ["#error in the way"], "mkdir onto a file")
    same(answers["put /a/x.wav 5"], ["#error put takes a path, a size and a crc"], "put with two values")
    same(answers["put /a/x.wav 3 ABCDEF01"], ["#ready", "#error wrong crc 352441c2"], "put with a wrong CRC-32")
    same(answers["x" * 201], ["#error line too long"], "a line of 201 letters")


def test_compiled_device_gives_up_after_three_seconds():
    program = built()
    if program.startswith("SKIPPED"):
        return program
    with Bench("gives up", {}, kind=Compiled) as bench:
        data = bytes_of(31, 500)
        bench.link.write(put_line("/half.wav", data).encode("ascii") + b"\n")
        same(hear(bench.link), ("#ready 192", b""), "the answer to put")
        bench.link.write(data[:192])
        same(hear(bench.link), ("#got 192", b""), "after the first piece")
        bench.link.write(data[192:300])
        expect(os.path.exists(os.path.join(bench.card, "incoming.part")), "the part has another name")
        started = time.time()
        same(hear(bench.link, 6.0), ("#error timeout", b""), "after half a piece and nothing more")
        took = time.time() - started
        expect(2.8 < took < 4.0, "it gave up after %.1f seconds" % took)
        same(ask(bench.link, "ls /"), ["#end 0"], "the card: the part must be gone")
        same(ask(bench.link, put_line("/whole.wav", data), data=data)[-1],
             "#done %08x" % (zlib.crc32(data) & 0xFFFFFFFF), "the next file")
        same(tree(bench.card), {"whole.wav": data}, "the card")


def test_compiled_device_takes_a_large_file():
    program = built()
    if program.startswith("SKIPPED"):
        return program
    data = bytes_of(41, 150000)
    with Bench("large", {"audio/large.wav": data}, kind=Compiled) as bench:
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        same(tree(bench.card), tree(bench.here), "the card")


def test_compiled_device_widens_its_queue():
    """Where the queue of the USB port can be made wider, the pieces are larger. The pretended port
    ends the device if its queue is replaced while it listens, is left deaf, or runs over."""
    program = built()
    if program.startswith("SKIPPED"):
        return program
    files = {"audio/large.wav": bytes_of(42, 150000), "audio/piece.wav": bytes_of(43, 2048),
             "audio/more.wav": bytes_of(44, 2049), "audio/small.wav": bytes_of(45, 100)}
    with Bench("wide", files, kind=Compiled, wide=True) as bench:
        same(ask(bench.link, "")[0], "#", "a knock before the first file")
        first = bytes_of(46, 5000)
        answers = ask(bench.link, put_line("/first.wav", first), data=first)
        same(answers, ["#ready 2048", "#got 2048", "#got 4096", "#got 5000",
                       "#done %08x" % (zlib.crc32(first) & 0xFFFFFFFF)], "the answers to the first file")
        same(ask(bench.link, "")[0], "#", "a knock after the first file")
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        files["first.wav"] = first
        files["audio/"] = None
        same(tree(bench.card), files, "the card")

    with Bench("narrow", {}, kind=Compiled) as bench:
        first = bytes_of(47, 500)
        answers = ask(bench.link, put_line("/first.wav", first), data=first)
        same(answers[0], "#ready 192", "the answer to the first file where the queue stays as it is")
        same(answers[-1], "#done %08x" % (zlib.crc32(first) & 0xFFFFFFFF), "the end of the first file")
        same(ask(bench.link, "")[0], "#", "a knock after the first file")


def test_tool_never_sends_more_than_a_piece_ahead():
    """The USB port of the device drops what its queue cannot hold."""
    with Bench("ahead", piece=256) as bench:
        unanswered = [0]
        most = [0]
        write = bench.link.write
        read_some = bench.link.read_some

        def counting_write(data):
            unanswered[0] += len(data)
            most[0] = max(most[0], unanswered[0])
            write(data)

        def counting_read(seconds):
            data = read_some(seconds)
            if b"\n" in data:
                unanswered[0] = 0
            return data
        bench.link.write = counting_write
        bench.link.read_some = counting_read
        ended, said = bench.sync()
        same(ended, 0, "the tool ended with\n" + said)
        expect(most[0] <= 256, "%d bytes were on their way without an answer" % most[0])


def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow_skips = "--allow-skips" in sys.argv[1:]
    tests = [(name[len("test_"):].replace("_", " "), function) for name, function in sorted(globals().items())
             if name.startswith("test_") and callable(function)]
    if arguments:
        tests = [t for t in tests if any(word in t[0] for word in arguments)]
    if not tests:
        sys.exit("no test matches " + " ".join(arguments))

    os.makedirs(WORK, exist_ok=True)
    failed = []
    skipped = []
    for name, function in tests:
        try:
            remark = function()
        except Failure as failure:
            failed.append(name)
            print("FAIL  %s\n      %s" % (name, str(failure).replace("\n", "\n      ")))
            continue
        except Exception:
            failed.append(name)
            print("FAIL  %s\n      %s" % (name, traceback.format_exc().strip().replace("\n", "\n      ")))
            continue
        if remark and remark.startswith("SKIPPED"):
            skipped.append(name)
            print("skip  %s (%s)" % (name, remark[len("SKIPPED: "):]))
        else:
            print("ok    %s%s" % (name, " (%s)" % remark if remark else ""))

    print("%d test%s: %d passed, %d failed, %d skipped" % (len(tests), "" if len(tests) == 1 else "s",
                                                           len(tests) - len(failed) - len(skipped), len(failed),
                                                           len(skipped)))
    if failed:
        sys.exit("FAILED: " + ", ".join(failed))
    if skipped and not allow_skips:
        sys.exit("INCOMPLETE: skipped " + ", ".join(skipped))


if __name__ == "__main__":
    main()
