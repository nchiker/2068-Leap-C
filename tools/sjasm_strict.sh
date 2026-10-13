#!/usr/bin/env bash
# Strict sjasmplus wrapper: any error, any warning, or a truncated/overflowed image fails the build.
# Derived from 2068-Leap's tools/sjasmplus_strict.sh (V2 refused only the truncation warnings).
# Usage: tools/sjasm_strict.sh [sjasmplus args...]   (run from the repository root)
set -euo pipefail
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
set +e
sjasmplus --nologo --msg=war --inc=. --inc=platform "$@" >"$log" 2>&1
rc=$?
set -e
cat "$log"
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
if grep -Eiq 'warning' "$log"; then
    echo "sjasm_strict: warnings are errors in this build" >&2
    exit 1
fi
