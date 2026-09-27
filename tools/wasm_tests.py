#!/usr/bin/env python3
"""Runs the C++ unit tests as WebAssembly under Node.

For machines where a locally built native program cannot be started. The tests are the same files
that `pio test -e native` runs; here they are compiled with Emscripten and executed by Node.

Usage:
    python3 tools/wasm_tests.py                # every folder under test/
    python3 tools/wasm_tests.py test_romaji    # one of them

A test folder may hold a file `sources.txt` naming the library sources it needs, one path per
line relative to the repository. Without it, every source of the portable libraries is compiled
in. Listing them keeps a test independent of code that is still being written elsewhere.

Needs Emscripten (`brew install emscripten`), Node, and the Unity sources that PlatformIO downloads
(`pio test -e native --without-testing` fetches them).
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Kept outside .pio/build, which PlatformIO empties whenever platformio.ini changes.
BUILD = os.path.join(ROOT, "build", "wasm")
UNITY = os.path.join(ROOT, ".pio", "libdeps", "native", "Unity", "src")

# Libraries that use nothing but the C++ standard library. Anything that touches the hardware
# stays out of this list and is tested on the device instead.
PORTABLE_LIBS = ["romaji", "core"]


def environment():
    env = dict(os.environ)
    if "EMSDK_PYTHON" not in env:
        for candidate in ("/opt/homebrew/bin/python3", "/usr/local/bin/python3"):
            if os.path.exists(candidate):
                env["EMSDK_PYTHON"] = candidate
                break
    return env


def run(command, env):
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    noise = ("cache:INFO", "system_libs:INFO", "ports:INFO", "shared:INFO")
    for line in (result.stdout + result.stderr).splitlines():
        if not line.startswith(noise):
            print(line)
    return result.returncode


def main():
    if not shutil.which("em++"):
        sys.exit("Emscripten is not installed. Install it with: brew install emscripten")
    if not shutil.which("node"):
        sys.exit("Node is not installed.")
    if not os.path.isdir(UNITY):
        sys.exit("Unity sources not found. Fetch them with: pio test -e native --without-testing")

    wanted = sys.argv[1:]
    folders = sorted(d for d in glob.glob(os.path.join(ROOT, "test", "test_*")) if os.path.isdir(d))
    if wanted:
        folders = [d for d in folders if os.path.basename(d) in wanted]
    if not folders:
        sys.exit("No test folders found" + (" matching " + ", ".join(wanted) if wanted else ""))

    env = environment()
    os.makedirs(BUILD, exist_ok=True)
    includes = ["-I" + UNITY] + ["-I" + os.path.join(ROOT, "lib", name) for name in PORTABLE_LIBS]
    library_sources = []
    for name in PORTABLE_LIBS:
        library_sources += sorted(glob.glob(os.path.join(ROOT, "lib", name, "*.cpp")))

    unity_object = os.path.join(BUILD, "unity.o")
    if not os.path.exists(unity_object):
        if run(["emcc", "-O1", "-c", os.path.join(UNITY, "unity.c"), "-I" + UNITY, "-o", unity_object], env):
            sys.exit("Could not compile Unity")

    failed = []
    for folder in folders:
        name = os.path.basename(folder)
        output = os.path.join(BUILD, name + ".js")
        sources = sorted(glob.glob(os.path.join(folder, "*.cpp")))
        wanted_sources = library_sources
        listing = os.path.join(folder, "sources.txt")
        if os.path.exists(listing):
            wanted_sources = [os.path.join(ROOT, line.strip()) for line in open(listing, encoding="utf-8")
                              if line.strip() and not line.startswith("#")]
            missing = [path for path in wanted_sources if not os.path.exists(path)]
            if missing:
                print("== " + name)
                print("sources.txt names files that do not exist: " + ", ".join(missing))
                failed.append(name + " (sources missing)")
                continue
        command = (["em++", "-O1", "-std=gnu++17", "-Wall", "-Wextra"] + includes + sources + wanted_sources +
                   [unity_object, "-o", output])
        print("== " + name)
        if run(command, env):
            failed.append(name + " (did not compile)")
            continue
        if run(["node", output], env):
            failed.append(name)

    if failed:
        sys.exit("FAILED: " + ", ".join(failed))
    print("All test folders passed.")


if __name__ == "__main__":
    main()
