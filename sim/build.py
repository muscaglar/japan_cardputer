#!/usr/bin/env python3
"""Builds the simulator: the app compiled to WebAssembly.

    python3 sim/build.py            # build/sim/sim.js + sim.wasm, for Node
    python3 sim/build.py --page     # also docs/sim/index.html, one file, for a browser

Needs Emscripten (`brew install emscripten`) and the libraries PlatformIO downloads
(`pio pkg install -e cardputer`).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M5GFX = os.path.join(ROOT, ".pio", "libdeps", "cardputer", "M5GFX", "src")
# Kept outside .pio/build, which PlatformIO empties whenever platformio.ini changes.
BUILD = os.path.join(ROOT, "build", "sim")
EXPORTS = ("_sim_init,_sim_key,_sim_advance,_sim_render,_sim_pixels,_sim_screen,_sim_restart,_sim_info,"
           "_sim_keep,_malloc,_free")

LIBRARY_C = [
    "lgfx/utility/lgfx_miniz.c", "lgfx/utility/lgfx_pngle.c", "lgfx/utility/lgfx_qoi.c",
    "lgfx/utility/lgfx_qrcode.c", "lgfx/utility/lgfx_tjpgd.c",
    "lgfx/Fonts/efont/lgfx_efont_ja.c", "lgfx/Fonts/IPA/lgfx_font_japan.c",
]
LIBRARY_CPP = ["lgfx/v1/lgfx_v1.cpp", "M5GFX.cpp"]


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
    if result.returncode:
        sys.exit("FAILED: " + " ".join(command[:4]) + " ...")


def newer(source, target):
    return not os.path.exists(target) or os.path.getmtime(source) > os.path.getmtime(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", action="store_true", help="also write docs/sim/index.html")
    args = parser.parse_args()

    if not shutil.which("em++"):
        sys.exit("Emscripten is not installed. Install it with: brew install emscripten")
    if not os.path.isdir(M5GFX):
        sys.exit("M5GFX sources not found. Fetch them with: pio pkg install -e cardputer")

    env = environment()
    os.makedirs(os.path.join(BUILD, "lib"), exist_ok=True)
    os.makedirs(os.path.join(BUILD, "app"), exist_ok=True)
    # -isystem keeps the library's own warnings out of our build output
    common = ["-O2", "-DLGFX_SDL", "-sUSE_SDL=2", "-isystem", M5GFX]
    objects = []

    # The graphics library changes rarely; its objects are kept between builds.
    for source in LIBRARY_C + LIBRARY_CPP:
        path = os.path.join(M5GFX, source)
        target = os.path.join(BUILD, "lib", os.path.basename(source) + ".o")
        if newer(path, target):
            compiler = ["emcc"] if source.endswith(".c") else ["em++", "-std=gnu++17"]
            run(compiler + common + ["-c", path, "-o", target], env)
        objects.append(target)

    app_sources = sorted(
        glob.glob(os.path.join(ROOT, "lib", "romaji", "*.cpp")) +
        glob.glob(os.path.join(ROOT, "lib", "core", "*.cpp")) +
        glob.glob(os.path.join(ROOT, "lib", "ui", "**", "*.cpp"), recursive=True) +
        [os.path.join(ROOT, "sim", "main.cpp")])
    includes = ["-I" + os.path.join(ROOT, "lib", name) for name in ("romaji", "core", "ui")]
    headers = glob.glob(os.path.join(ROOT, "lib", "**", "*.h"), recursive=True)
    newest_header = max(os.path.getmtime(h) for h in headers)
    for source in app_sources:
        name = os.path.relpath(source, ROOT).replace(os.sep, "_") + ".o"
        target = os.path.join(BUILD, "app", name)
        if newer(source, target) or os.path.getmtime(target) < newest_header:
            run(["em++", "-std=gnu++17", "-Wall", "-Wextra", "-Wno-unused-parameter"] + common + includes +
                ["-c", source, "-o", target], env)
        objects.append(target)

    link = ["em++"] + common + objects + [
        "-sEXPORTED_FUNCTIONS=" + EXPORTS,
        "-sEXPORTED_RUNTIME_METHODS=HEAPU8,UTF8ToString,stringToNewUTF8",
        "-sALLOW_MEMORY_GROWTH=1", "-sMODULARIZE=1", "-sEXPORT_NAME=createSim",
    ]
    node_target = os.path.join(BUILD, "sim.js")
    run(link + ["-sENVIRONMENT=node", "-o", node_target], env)
    print("built %s (%.0f KB of WebAssembly)" % (
        os.path.relpath(node_target, ROOT), os.path.getsize(node_target.replace(".js", ".wasm")) / 1024))

    if args.page:
        # One self-contained file. Plain JavaScript instead of WebAssembly, so that it also runs
        # where a page may not compile WebAssembly.
        script = os.path.join(BUILD, "sim_web.js")
        run(link + ["-sENVIRONMENT=web", "-sWASM=0", "-sSINGLE_FILE=1", "-o", script], env)
        shell = open(os.path.join(ROOT, "sim", "shell.html"), encoding="utf-8").read()
        code = open(script, encoding="utf-8").read().replace("</script", "<\\/script")
        page = shell.replace("/*SIMULATOR*/", code)
        target = os.path.join(ROOT, "docs", "sim", "cardputer-simulator.html")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        open(target, "w", encoding="utf-8").write(page)
        print("built %s (%.0f KB)" % (os.path.relpath(target, ROOT), os.path.getsize(target) / 1024))


if __name__ == "__main__":
    main()
