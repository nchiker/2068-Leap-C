#!/usr/bin/env bash
# The Phase 9 qualification on the current images (make qualify): every suite in sequence, each needing the CPU.
# Each step's output goes to build/<step>.log; the image hashes and each step's exit status to build/qualify_summary.log.
# make repro runs separately, last: it rebuilds from a clean tree.
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
make build > build/qualify_build.log 2>&1 || { echo "STEP build FAILED" | tee -a $SUMMARY; exit 1; }
sha256sum build/leapc_home.bin build/leapc_exrom.bin build/leapc_zesarux.bin build/leapc_exrom.dck >> $SUMMARY
step final_test   make test
step fuse         make fuse
step timing       make timing
step ram_warm     python3 tools/run_tests.py --ram warm --suite boot,decl,exec,shell,e2e --json build/ram_warm.json
step ram_random7  python3 tools/run_tests.py --ram random:7 --suite boot,decl,exec,shell,e2e --json build/ram_random7.json
step capacity     make capacity
step kit_verify   python3 -u tools/hwkit.py --verify --soak-minutes 30
step check        make check
ps -eo pid,args | awk '$2 ~ /\/fuse$/ {print $1}' | xargs -r kill -9      # (a Fuse left by a failed step)
if [ -n "$FAILED" ]; then echo "QUALIFY: FAIL:$FAILED" | tee -a $SUMMARY; exit 1; fi
echo "QUALIFY: PASS" | tee -a $SUMMARY
