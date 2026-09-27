#!/bin/sh
# For a second checkout of this repository (a git worktree): borrows what the first one has
# downloaded, so that nothing is fetched twice. Run it in the second checkout:
#
#     sh tools/share_downloads.sh /path/to/the/first/checkout
#
# It links .pio (libraries, fonts cache) and local (dictionary, accent list). Build output
# stays apart: each checkout has its own build/ folder.
set -e
first="$1"
if [ -z "$first" ] || [ ! -d "$first/.pio/libdeps" ]; then
    echo "usage: sh tools/share_downloads.sh /path/to/the/first/checkout (the one that has .pio/libdeps)" >&2
    exit 1
fi
here="$(cd "$(dirname "$0")/.." && pwd)"
for name in .pio local; do
    if [ -e "$here/$name" ] || [ -L "$here/$name" ]; then
        echo "$name is there already"
    elif [ -e "$first/$name" ]; then
        ln -s "$first/$name" "$here/$name"
        echo "$name -> $first/$name"
    fi
done
