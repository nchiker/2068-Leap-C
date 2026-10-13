#!/usr/bin/env bash
# Reproducible build check: two builds from a clean tree must give identical image hashes.
set -euo pipefail
cd "$(dirname "$0")/.."
make clean >/dev/null && make build >/dev/null
cp build/SHA256SUMS /tmp/leapc_repro_1.$$
( cd build/test && sha256sum leapc_home.bin leapc_exrom.bin ) >> /tmp/leapc_repro_1.$$
make clean >/dev/null && make build >/dev/null
cp build/SHA256SUMS /tmp/leapc_repro_2.$$
( cd build/test && sha256sum leapc_home.bin leapc_exrom.bin ) >> /tmp/leapc_repro_2.$$
if cmp -s /tmp/leapc_repro_1.$$ /tmp/leapc_repro_2.$$; then
    echo "reproducible: OK"; cat /tmp/leapc_repro_1.$$
    rm -f /tmp/leapc_repro_[12].$$
else
    echo "reproducible: FAILED" >&2; diff /tmp/leapc_repro_1.$$ /tmp/leapc_repro_2.$$ >&2 || true
    rm -f /tmp/leapc_repro_[12].$$; exit 1
fi
