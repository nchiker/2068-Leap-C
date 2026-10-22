#!/usr/bin/env bash
# Build the beta.1 images (tag v1.0.0-beta.1: the last ROMs with the stock-ROM-derived tape block routines,
# NOTICE) into build/beta1/ for the receiver's envelope comparison (tools/tapetol.py, Phase 11 M11-tape). The
# tag is only read, through `git archive`; the build runs in build/beta1/src, and the images must have the
# beta.1 hashes (HOME ba8e0ab6..., EXROM 9bd71cef...). Only the images (the combined one for the screen reader's
# glyph cache, tools/fusedrive.py) and their symbols are kept: the
# comparison runs them, nothing reads their code.
# Usage: tools/beta1ref.sh
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=build/beta1
HOME_SHA=ba8e0ab6bf277c03f969f8ac9e829a0c32665efe6bed1a12613555196e10a04a
EXROM_SHA=9bd71cefbd78fd80d449609c94d349a2671625f3b3642fd0380b6c8dbfbca47a
rm -rf "$OUT"
mkdir -p "$OUT/src"
git archive v1.0.0-beta.1 | tar -x -C "$OUT/src"
make -C "$OUT/src" prod > "$OUT/build.log" 2>&1 || { tail -20 "$OUT/build.log"; exit 1; }
echo "$HOME_SHA  $OUT/src/build/leapc_home.bin" | sha256sum -c --quiet
echo "$EXROM_SHA  $OUT/src/build/leapc_exrom.bin" | sha256sum -c --quiet
cp "$OUT/src/build/leapc_home.bin" "$OUT/src/build/leapc_exrom.bin" "$OUT/src/build/leapc_zesarux.bin" "$OUT/src/build/leapc_home.sym" \
    "$OUT/src/build/leapc_exrom.sym" "$OUT/"
rm -rf "$OUT/src"
echo "beta1ref: $OUT (HOME ${HOME_SHA:0:8}, EXROM ${EXROM_SHA:0:8})"
