#!/usr/bin/env bash
# The Phase 9 qualification on the current images (make qualify): every suite in sequence, each needing the CPU.
# Each step's output goes to build/<step>.log; the image hashes and each step's exit status to build/qualify_summary.log.
# make repro runs separately, last: it rebuilds from a clean tree.
# QUALIFY_PORT (default 10760) moves every ZEsarUX step to other remote ports, so the qualification can run while
# another project's emulators use the defaults: the steps run one after another and each uses ports from there up
# (the test runner one per worker, 7). Fuse needs no port (each instance has its own socket).
cd "$(dirname "$0")/.." || exit 2
mkdir -p build
SUMMARY=build/qualify_summary.log
: > $SUMMARY
step() {
    local name=$1; shift
    local t0=$(date +%s)
    "$@" > build/$name.log 2>&1
    local rc=$?
    echo "STEP $name exit $rc ($(( $(date +%s) - t0 )) s)" | tee -a $SUMMARY
    [ $rc -eq 0 ] || FAILED="$FAILED $name"
}
FAILED=
P=${QUALIFY_PORT:-10760}
make build > build/qualify_build.log 2>&1 || { echo "STEP build FAILED" | tee -a $SUMMARY; exit 1; }
sha256sum build/leapc_home.bin build/leapc_exrom.bin build/leapc_zesarux.bin build/leapc_exrom.dck >> $SUMMARY
step final_test   sh -c "python3 tools/run_tests.py --port $P --coverage build/coverage.json && python3 tools/romcov.py build/coverage.json"
step fuse         make fuse
step timing       python3 tools/timingcmp.py --port $P
step display      python3 tools/displaytest.py --port $P
step lines        sh -c "python3 tools/linetest.py --port $P && python3 tools/linetest.py --time --port $P"
step ram_warm     python3 tools/run_tests.py --port $P --ram warm --suite boot,decl,exec,shell,e2e --json build/ram_warm.json
step ram_random7  python3 tools/run_tests.py --port $P --ram random:7 --suite boot,decl,exec,shell,e2e --json build/ram_random7.json
step capacity     python3 tools/capacity.py --port $P
step kit_verify   python3 -u tools/hwkit.py --verify --soak-minutes 30 --port $P
step tapetol      make tapetol
step check        make check
for pid in $(pgrep -x fuse); do                # a Fuse left by a failed step: only this repository's (its working
    [ "$(readlink /proc/$pid/cwd)" = "$PWD" ] && kill -9 $pid    # directory); another project's Fuse is left alone
done
if [ -n "$FAILED" ]; then echo "QUALIFY: FAIL:$FAILED" | tee -a $SUMMARY; exit 1; fi
echo "QUALIFY: PASS" | tee -a $SUMMARY
