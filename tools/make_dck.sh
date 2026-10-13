#!/bin/sh
# EightyOne/ZEsarUX-style .dck holding the 8 KB EXROM image (copied from 2068-Leap's
# tools/make_eightyone_dck.sh, tag v2.0.1-emu.1). Usage: make_dck.sh EXROM.bin OUT.dck
set -eu
input=$1
output=$2
size=$(wc -c < "$input")
if [ "$size" -ne 8192 ]; then
    echo "make_dck: expected an 8192-byte EXROM, got $size bytes" >&2
    exit 1
fi
printf '\376\000\000\000\000\000\000\002\000' > "$output"
dd if="$input" of="$output" bs=1 seek=9 conv=notrunc 2>/dev/null
[ "$(wc -c < "$output")" -eq 8201 ] || { echo "make_dck: bad output size" >&2; exit 1; }
