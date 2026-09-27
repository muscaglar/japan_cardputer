#!/usr/bin/env python3
"""Type-check the firmware sources without running the ESP32 compiler.

Some machines refuse to run the Xtensa toolchain that PlatformIO downloads. This script parses
our sources with the system clang in syntax-only mode, against the real Arduino, ESP-IDF and
M5Stack headers, so that API mistakes are caught before a build is possible.

It is not a build: nothing is linked, and code size is not checked.

Every source file under src/ and lib/ is checked, also one that was added after the list of
compile commands was written: it borrows the flags of a file beside it.

Usage:
    pio run -e cardputer -t compiledb      # writes compile_commands.json, runs no compiler
    python3 tools/syntax_check.py
    python3 tools/syntax_check.py --db ../main/compile_commands.json
        # in a second checkout: the commands of the first one, with its paths turned into ours
"""
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLCHAIN = os.path.expanduser("~/.platformio/packages/toolchain-xtensa-esp32s3")
GCC_VERSION_DIR = os.path.join(TOOLCHAIN, "xtensa-esp32s3-elf", "include", "c++")

# The ESP-IDF headers contain Xtensa inline assembly that an ARM-targeted parser rejects.
EXPECTED_NOISE = re.compile(r"invalid (output|input) constraint .* in asm|unknown register name .* in asm")


def flags_from(command):
    args = shlex.split(command)
    kept = []
    i = 1
    paired = ("-I", "-D", "-isystem", "-include", "-iprefix", "-iwithprefix")
    while i < len(args):
        a = args[i]
        if a == "-o":
            i += 2
            continue
        if a.startswith(("-I", "-D", "-U", "-isystem", "-include", "-iprefix", "-iwithprefix")):
            kept.append(a)
            if a in paired:
                i += 1
                kept.append(args[i])
        i += 1
    return kept


def project_sources():
    found = []
    for top in ("src", "lib"):
        for folder, _, names in os.walk(os.path.join(ROOT, top)):
            for name in sorted(names):
                if name.endswith((".cpp", ".cc", ".cxx", ".c")):
                    found.append(os.path.join(folder, name))
    return sorted(found)


def main():
    db_path = os.path.join(ROOT, "compile_commands.json")
    if "--db" in sys.argv:
        db_path = os.path.abspath(sys.argv[sys.argv.index("--db") + 1])
    if not os.path.exists(db_path):
        sys.exit("compile_commands.json is missing. Run: pio run -e cardputer -t compiledb")
    text = open(db_path).read()
    written_in = os.path.dirname(db_path)
    if written_in != ROOT:
        # The libraries that were downloaded stay where they are; our own sources are ours.
        for top in ("src", "lib", "include"):
            text = text.replace(os.path.join(written_in, top), os.path.join(ROOT, top))
    database = json.loads(text)
    for entry in database:
        if os.path.abspath(entry["directory"]) == written_in:
            entry["directory"] = ROOT

    listed = {}
    for entry in database:
        path = os.path.abspath(os.path.join(entry["directory"], entry["file"]))
        if path.startswith((os.path.join(ROOT, "src") + os.sep, os.path.join(ROOT, "lib") + os.sep)):
            listed[path] = entry
    if not listed:
        sys.exit("No project sources found in compile_commands.json")

    def neighbour(path):
        """The entry of the listed file that shares the longest path with this one."""
        def shared(other):
            return len(os.path.commonpath([os.path.dirname(path), os.path.dirname(other)]))
        return listed[max(sorted(listed), key=shared)]

    ours = []
    for path in project_sources():
        if path.endswith("deck_data.cpp") and "--all" not in sys.argv:
            continue  # written by a program, large, and checked whenever it is written
        entry = dict(listed.get(path) or neighbour(path))
        entry["file"] = path
        ours.append(entry)

    versions = sorted(os.listdir(GCC_VERSION_DIR)) if os.path.isdir(GCC_VERSION_DIR) else []
    if not versions:
        sys.exit("Xtensa toolchain headers not found under " + TOOLCHAIN)
    cxx = os.path.join(GCC_VERSION_DIR, versions[-1])
    system_includes = [
        cxx,
        os.path.join(cxx, "xtensa-esp32s3-elf"),
        os.path.join(cxx, "backward"),
        os.path.join(TOOLCHAIN, "xtensa-esp32s3-elf", "sys-include"),
        os.path.join(TOOLCHAIN, "xtensa-esp32s3-elf", "include"),
    ]

    failed = False
    for entry in ours:
        source = entry["file"]
        is_cpp = source.endswith((".cpp", ".cc", ".cxx"))
        command = ["clang++" if is_cpp else "clang", "--target=arm-none-eabi", "-fsyntax-only",
                   "-std=gnu++11" if is_cpp else "-std=gnu99", "-nostdlibinc", "-ferror-limit=0",
                   "-Wall", "-Wextra", "-Wno-unknown-pragmas", "-Wno-unknown-attributes",
                   "-Wno-unused-parameter", "-Wno-ignored-attributes", "-Wno-deprecated-declarations",
                   "-D__XTENSA__=1", "-D__xtensa__=1", "-D__XTENSA_EL__=1", "-D__XTENSA_WINDOWED_ABI__=1",
                   "-U__arm__", "-U__ARM_EABI__", "-U__thumb__", "-U__ARMEL__"]
        if is_cpp:
            command += ["-fno-rtti", "-fno-exceptions"]
        for path in system_includes:
            command += ["-isystem", path]
        command += flags_from(entry["command"]) + [source]

        result = subprocess.run(command, cwd=entry["directory"], capture_output=True, text=True)
        findings = []
        for line in result.stderr.splitlines():
            match = re.match(r"(.+?):(\d+):(\d+): (fatal error|error|warning): (.*)", line)
            if not match:
                continue
            path, _, _, kind, message = match.groups()
            absolute = os.path.abspath(os.path.join(entry["directory"], path))
            in_project = absolute.startswith((os.path.join(ROOT, "src") + os.sep,
                                              os.path.join(ROOT, "lib") + os.sep))
            if kind != "warning" and not in_project and EXPECTED_NOISE.search(message):
                continue
            if kind == "warning" and not in_project:
                continue
            findings.append((kind, line))

        errors = [f for f in findings if f[0] != "warning"]
        label = os.path.relpath(os.path.join(entry["directory"], source), ROOT)
        print(("FAIL " if errors else "ok   ") + label +
              ("" if not findings else "  (%d errors, %d warnings)" % (len(errors), len(findings) - len(errors))))
        for _, line in findings:
            print("    " + line)
        failed = failed or bool(errors)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
