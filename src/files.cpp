#include "files.h"

#include <Arduino.h>

#include <cstdio>
#include <cstdlib>

#include "card.h"

#if ARDUINO_USB_MODE && ARDUINO_USB_CDC_ON_BOOT
#include "hal/usb_serial_jtag_ll.h"
#endif

namespace {

typedef void (*Reply)(const char*);

constexpr size_t kLongestPath = 120;
constexpr size_t kDeepest     = 250;   // the longest path rm follows into a folder
constexpr size_t kBufferSize  = 4096;  // the one buffer: made when first needed, then kept
constexpr size_t kPiece       = 2048;
constexpr size_t kSmallPiece  = 192;   // fits the queue of 256 bytes that the USB port makes itself
constexpr uint32_t kPatience  = 3000;  // ms without a byte before a file is given up
constexpr uint32_t kCrcStart  = 0xFFFFFFFFu;
const char* const kIncoming   = "/incoming.part";

uint8_t* buffer = nullptr;
size_t piece    = 0;  // 0 until the first file arrives

bool haveBuffer()
{
    if (!buffer) {
        buffer = static_cast<uint8_t*>(malloc(kBufferSize));
    }
    return buffer != nullptr;
}

// Makes the queue of the USB port hold that many bytes. false where that cannot be done.
bool widenQueue(size_t bytes)
{
#if ARDUINO_USB_MODE && ARDUINO_USB_CDC_ON_BOOT
    // Nothing may be put into the queue while it is replaced. What arrives meanwhile waits in
    // the port itself.
    usb_serial_jtag_ll_disable_intr_mask(USB_SERIAL_JTAG_INTR_SERIAL_OUT_RECV_PKT);
    const bool wider = Serial.setRxBufferSize(bytes) != 0;
    if (!wider) {
        Serial.setRxBufferSize(256);
    }
    usb_serial_jtag_ll_ena_intr_mask(USB_SERIAL_JTAG_INTR_SERIAL_OUT_RECV_PKT);
    return wider;
#else
    (void)bytes;
    return false;
#endif
}

// The USB port drops what does not fit into its queue. A whole piece must fit, because the card
// may keep the device busy while one arrives. The wider queue is made once and kept.
size_t pieceSize()
{
    if (piece == 0) {
        piece = widenQueue(kPiece + 64) ? kPiece : kSmallPiece;
    }
    return piece;
}

// CRC-32 as zlib computes it, four bits at a time: start with kCrcStart, turn all bits over at the end.
uint32_t crcAdd(uint32_t crc, const uint8_t* data, size_t count)
{
    static const uint32_t kTable[16] = {0x00000000, 0x1DB71064, 0x3B6E20C8, 0x26D930AC, 0x76DC4190, 0x6B6B51F4,
                                        0x4DB26158, 0x5005713C, 0xEDB88320, 0xF00F9344, 0xD6D6A3E8, 0xCB61B38C,
                                        0x9B64C2B0, 0x86D3D2D4, 0xA00AE278, 0xBDBDF21C};
    for (size_t i = 0; i < count; ++i) {
        crc ^= data[i];
        crc = kTable[crc & 15] ^ (crc >> 4);
        crc = kTable[crc & 15] ^ (crc >> 4);
    }
    return crc;
}

bool goodPath(const std::string& path)
{
    if (path.empty() || path.size() > kLongestPath || path[0] != '/') {
        return false;
    }
    if (path.size() > 1 && path.back() == '/') {
        return false;
    }
    for (size_t i = 0; i < path.size(); ++i) {
        const char c     = path[i];
        const bool known = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '/' ||
                           c == '.' || c == '_' || c == '-';
        if (!known) {
            return false;
        }
        if (i > 0 && (c == '/' || c == '.') && path[i - 1] == c) {
            return false;  // "//" or ".."
        }
        const bool nameEnds = (i + 1 == path.size()) || path[i + 1] == '/';
        if (c == '.' && path[i - 1] == '/' && nameEnds) {
            return false;  // a name that is a single "."
        }
    }
    return true;
}

// The folder a path lies in: "/" for "/a", "/a" for "/a/b".
std::string folderOf(const std::string& path)
{
    const size_t slash = path.rfind('/');
    return (slash == 0 || slash == std::string::npos) ? std::string("/") : path.substr(0, slash);
}

std::string number(uint64_t value)
{
    char digits[24];
    size_t at    = sizeof(digits);
    digits[--at] = '\0';
    do {
        digits[--at] = static_cast<char>('0' + value % 10);
        value /= 10;
    } while (value > 0);
    return std::string(digits + at);
}

std::string hex8(uint32_t value)
{
    char text[12];
    snprintf(text, sizeof(text), "%08lx", static_cast<unsigned long>(value));
    return std::string(text);
}

bool readSize(const std::string& text, uint32_t& value)
{
    if (text.empty() || text.size() > 10) {
        return false;
    }
    uint64_t sum = 0;
    for (char c : text) {
        if (c < '0' || c > '9') {
            return false;
        }
        sum = sum * 10 + static_cast<uint64_t>(c - '0');
    }
    if (sum > 0xFFFFFFFFull) {
        return false;
    }
    value = static_cast<uint32_t>(sum);
    return true;
}

bool readCrc(const std::string& text, uint32_t& value)
{
    if (text.size() != 8) {
        return false;
    }
    value = 0;
    for (char c : text) {
        uint32_t digit = 0;
        if (c >= '0' && c <= '9') {
            digit = static_cast<uint32_t>(c - '0');
        } else if (c >= 'a' && c <= 'f') {
            digit = static_cast<uint32_t>(c - 'a' + 10);
        } else if (c >= 'A' && c <= 'F') {
            digit = static_cast<uint32_t>(c - 'A' + 10);
        } else {
            return false;
        }
        value = (value << 4) | digit;
    }
    return true;
}

void sayRoom(Reply reply)
{
    reply(("#df " + number(cardBytesTotal()) + " " + number(cardBytesUsed())).c_str());
}

void listFolder(const std::string& path, Reply reply)
{
    fs::FS& card = cardFiles();
    File folder  = card.open(path.c_str());
    if (!folder) {
        reply("#error not there");
        return;
    }
    if (!folder.isDirectory()) {
        folder.close();
        reply("#error not a folder");
        return;
    }
    uint32_t count = 0;
    for (;;) {
        bool isFolder     = false;
        const String full = folder.getNextFileName(&isFolder);
        if (full.length() == 0) {
            break;
        }
        const std::string whole(full.c_str());
        const std::string name = whole.substr(whole.rfind('/') + 1);
        if (isFolder) {
            reply(("#dir " + name).c_str());
        } else {
            File entry             = card.open(whole.c_str());
            const std::string size = entry ? number(entry.size()) : std::string("?");
            entry.close();
            reply(("#file " + size + " " + name).c_str());
        }
        ++count;
    }
    folder.close();
    reply(("#end " + number(count)).c_str());
}

void sumFile(const std::string& path, Reply reply)
{
    File file = cardFiles().open(path.c_str());
    if (!file) {
        reply("#error not there");
        return;
    }
    if (file.isDirectory()) {
        file.close();
        reply("#error not a file");
        return;
    }
    if (!haveBuffer()) {
        file.close();
        reply("#error no memory");
        return;
    }
    const size_t size = file.size();
    uint32_t crc      = kCrcStart;
    size_t seen       = 0;
    for (;;) {
        const size_t got = file.read(buffer, kBufferSize);
        if (got == 0 || got > kBufferSize) {
            break;
        }
        crc = crcAdd(crc, buffer, got);
        seen += got;
    }
    file.close();
    if (seen != size) {
        reply("#error cannot read");
        return;
    }
    reply(("#crc " + hex8(~crc) + " " + number(size)).c_str());
}

// Empties a folder and removes it, the folders in it first. Only one folder is open at a time,
// and none while something is removed.
bool removeFolder(fs::FS& card, const std::string& top)
{
    std::string current = top;
    std::string removed;
    for (;;) {
        File folder = card.open(current.c_str());
        if (!folder || !folder.isDirectory()) {
            return false;
        }
        bool isFolder      = false;
        const String first = folder.getNextFileName(&isFolder);
        folder.close();
        if (first.length() == 0) {
            if (!card.rmdir(current.c_str())) {
                return false;
            }
            if (current == top) {
                return true;
            }
            removed = current;
            current = folderOf(current);
            continue;
        }
        if (first.length() > kDeepest || removed == first.c_str()) {
            return false;  // too deep, or what was removed is still there
        }
        if (isFolder) {
            current = first.c_str();
            continue;
        }
        if (!card.remove(first.c_str())) {
            return false;
        }
        removed = first.c_str();
    }
}

void removeAt(const std::string& path, Reply reply)
{
    if (path == "/") {
        reply("#error bad path");
        return;
    }
    fs::FS& card = cardFiles();
    File there   = card.open(path.c_str());
    if (!there) {
        reply("#error not there");
        return;
    }
    const bool isFolder = there.isDirectory();
    there.close();
    const bool gone = isFolder ? removeFolder(card, path) : card.remove(path.c_str());
    reply(gone ? "#ok" : "#error cannot remove");
}

void makeFolder(const std::string& path, Reply reply)
{
    fs::FS& card = cardFiles();
    size_t at    = 0;
    while (at != std::string::npos && path.size() > 1) {
        at                     = path.find('/', at + 1);
        const std::string upTo = path.substr(0, at);
        if (card.mkdir(upTo.c_str())) {
            continue;
        }
        File there = card.open(upTo.c_str());
        reply(there ? "#error in the way" : "#error cannot make");
        there.close();
        return;
    }
    reply("#ok");
}

void giveUp(fs::FS& card, File& part, Reply reply, const char* why)
{
    part.close();
    card.remove(kIncoming);
    reply(why);
}

void receive(const std::string& rest, Reply reply)
{
    const size_t first  = rest.find(' ');
    const size_t second = (first == std::string::npos) ? first : rest.find(' ', first + 1);
    if (second == std::string::npos || rest.find(' ', second + 1) != std::string::npos) {
        reply("#error put takes a path, a size and a crc");
        return;
    }
    const std::string path = rest.substr(0, first);
    uint32_t size          = 0;
    uint32_t announced     = 0;
    if (!goodPath(path) || path == "/" || path == kIncoming) {
        reply("#error bad path");
        return;
    }
    if (!readSize(rest.substr(first + 1, second - first - 1), size) || !readCrc(rest.substr(second + 1), announced)) {
        reply("#error put takes a path, a size and a crc");
        return;
    }

    fs::FS& card         = cardFiles();
    File above           = card.open(folderOf(path).c_str());
    const bool hasFolder = above && above.isDirectory();
    above.close();
    if (!hasFolder) {
        reply("#error no folder");
        return;
    }
    File there          = card.open(path.c_str());
    const bool replaces = there;
    const bool isFolder = there && there.isDirectory();
    there.close();
    if (isFolder) {
        reply("#error in the way");
        return;
    }
    if (!haveBuffer()) {
        reply("#error no memory");
        return;
    }
    File part = card.open(kIncoming, FILE_WRITE);
    if (!part) {
        reply("#error cannot open");
        return;
    }
    const size_t most = pieceSize();
    reply(("#ready " + number(most)).c_str());

    uint32_t crc = kCrcStart;
    uint32_t got = 0;
    while (got < size) {
        const size_t want = (size - got < most) ? static_cast<size_t>(size - got) : most;
        size_t have       = 0;
        uint32_t lastByte = millis();
        while (have < want) {
            const int waiting = Serial.available();
            if (waiting > 0) {
                const size_t room = want - have;
                const size_t take = (static_cast<size_t>(waiting) < room) ? static_cast<size_t>(waiting) : room;
                const size_t came = Serial.read(buffer + have, take);
                if (came > 0 && came <= take) {
                    have += came;
                    lastByte = millis();
                    continue;
                }
            }
            if (millis() - lastByte > kPatience) {
                giveUp(card, part, reply, "#error timeout");
                return;
            }
            delay(1);
        }
        // The piece is here whole, and the computer waits: now an error can be answered.
        if (part.write(buffer, want) != want) {
            giveUp(card, part, reply, "#error cannot write");
            return;
        }
        crc = crcAdd(crc, buffer, want);
        got += static_cast<uint32_t>(want);
        reply(("#got " + number(got)).c_str());
    }

    part.close();
    crc = ~crc;
    if (crc != announced) {
        card.remove(kIncoming);
        reply(("#error wrong crc " + hex8(crc)).c_str());
        return;
    }
    File written     = card.open(kIncoming);
    const bool whole = written && !written.isDirectory() && written.size() == size;
    written.close();
    if (!whole) {
        card.remove(kIncoming);
        reply("#error cannot write");
        return;
    }
    if (replaces && !card.remove(path.c_str())) {
        card.remove(kIncoming);
        reply("#error cannot replace");
        return;
    }
    if (!card.rename(kIncoming, path.c_str())) {
        card.remove(kIncoming);
        reply("#error cannot rename");
        return;
    }
    reply(("#done " + hex8(crc)).c_str());
}

}  // namespace

bool filesCarryOut(const std::string& word, const std::string& rest, void (*reply)(const char*))
{
    const bool takesPath = (word == "ls" || word == "crc" || word == "rm" || word == "mkdir");
    if (!takesPath && word != "df" && word != "put") {
        return false;
    }
    if (!cardReady()) {
        reply("#error no card");
        return true;
    }
    if (word == "df") {
        sayRoom(reply);
    } else if (word == "put") {
        receive(rest, reply);
    } else if (!goodPath(rest)) {
        reply("#error bad path");
    } else if (word == "ls") {
        listFolder(rest, reply);
    } else if (word == "crc") {
        sumFile(rest, reply);
    } else if (word == "rm") {
        removeAt(rest, reply);
    } else {
        makeFolder(rest, reply);
    }
    return true;
}
