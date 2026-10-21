#!/usr/bin/env bash
# Build the Leap V2 reference ROM (tag v2.0.1-emu.1, platform/UPSTREAM.md) into build/v2ref/ for the
# cross-version tape tests (Phase 7: V2 refuses Leap-C tapes, Leap-C refuses V2's). The frozen V2 repository
# is only read, through `git archive` of the tag; the build runs in build/v2ref/src. The images must have the
# V2 reference hashes (HOME 3f13ec2c..., EXROM 24b1ebb0...).
# Usage: tools/v2ref.sh [V2_REPO]   (default ~/2068-Leap)
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=${1:-$HOME/2068-Leap}
OUT=build/v2ref
HOME_SHA=3f13ec2cc4ef02c1b9694ccd3d40c02658ff4ddef100e16f50230d3002306f1c
EXROM_SHA=24b1ebb0b1377aad8e2e6caee443a9c5611cfad2f0eab495311e07df43b22b7e
rm -rf "$OUT"
mkdir -p "$OUT/src"
git -C "$REPO" archive v2.0.1-emu.1 | tar -x -C "$OUT/src"
make -C "$OUT/src" build > "$OUT/build.log" 2>&1 || { tail -20 "$OUT/build.log"; exit 1; }
echo "$HOME_SHA  $OUT/src/build/test_basic.bin" | sha256sum -c --quiet
echo "$EXROM_SHA  $OUT/src/build/exrom.bin" | sha256sum -c --quiet
cp "$OUT/src/build/ts2068rom_zesarux.bin" "$OUT/src/build/test_basic.sym" "$OUT/src/build/exrom.sym" "$OUT/"
echo "v2ref: $OUT/ts2068rom_zesarux.bin (HOME ${HOME_SHA:0:8}, EXROM ${EXROM_SHA:0:8})"
