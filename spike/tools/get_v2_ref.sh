#!/usr/bin/env bash
# Export the frozen Leap V2 release (tag v2.0.1-emu.1) from ~/2068-Leap with `git archive`
# (the repository is only read), build it in a temporary directory, and copy the images and
# symbol tables the spike needs into spike/v2ref/build/. Verifies the published release hashes.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
repo="${LEAPC_V2_REPO:-${LEAP_V2_REPO:-$HOME/2068-Leap}}"
tag="v2.0.1-emu.1"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git -C "$repo" archive "$tag" | tar -x -C "$tmp"
( cd "$tmp" && make build >/dev/null 2>&1 && make budget > build/budget.log 2>&1 )
out="$here/v2ref/build"
mkdir -p "$out"
for f in ts2068rom_zesarux.bin test_basic.bin exrom.bin test_basic.sym exrom.sym test_basic.lst exrom.lst budget.log; do
  cp "$tmp/build/$f" "$out/"
done
git -C "$repo" rev-parse "$tag^{commit}" > "$out/V2_COMMIT"
( cd "$out" && sha256sum test_basic.bin exrom.bin ts2068rom_zesarux.bin > SHA256SUMS )
grep -q '^3f13ec2cc4ef02c1' "$out/SHA256SUMS" || { echo "HOME hash differs from the release"; exit 1; }
grep -q '24b1ebb0b1377aad' "$out/SHA256SUMS" || { echo "EXROM hash differs from the release"; exit 1; }
echo "v2ref ready: $(cat "$out/V2_COMMIT")"; cat "$out/SHA256SUMS"
