#!/usr/bin/env python3
"""Provenance check of the production images against the stock ROMs (Phase 11, M11-tape; NOTICE).

Every run of MIN (12) or more bytes that a production image (build/leapc_home.bin, build/leapc_exrom.bin)
shares, byte for byte, with a stock ROM is listed with its place in the image (the routine, from the
listing's labels) and in the stock ROM. A run is accepted only if it is recorded in ALLOWED below with a
reason, or is mostly one byte repeated (less than MIN other bytes: an $FF fill, which the stock ROMs have
too; windows of one repeated byte are not compared at all). The stock ROMs are
read from the directory in $LEAPC_STOCK_ROMS (default: ~/fuse-build/roms, Fuse's source tree) and are
never stored in this repository: 48.rom (the Spectrum 48K), tc2068-0.rom and tc2068-1.rom (the TS2068's
HOME ROM and EXROM). Only offsets and lengths are reported, never the stock bytes.

Exit status 0 when every run is accepted, 1 otherwise, 2 when the stock ROMs are not there (make check
skips the check then, saying so).

Usage: provenance.py [--build DIR] [--min N] [--roms DIR]
"""
import argparse
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import romcov           # noqa: E402

ROOT = os.path.dirname(HERE)
MIN = 12
STOCK = ("48.rom", "tc2068-0.rom", "tc2068-1.rom")
IMAGES = (("leapc_home.bin", "leapc_home.lst", "LEAPC_HOME_BASE", 0x0000),
          ("leapc_exrom.bin", "leapc_exrom.lst", "LEAPC_EXROM_BASE", None))
# (image, routine containing the run's first byte, length) -> reason
ALLOWED = {
    ("leapc_exrom.bin", "SH_IDCHAR", 15): "Leap-C's own range test for identifier characters (src/shell/highlight.asm): "
                                         "the usual Z80 way to test 'A'-'Z' / 'a'-'z'; it equals the stock ALPHA "
                                         "routine byte for byte (NOTICE)",
}


def runs(img, rom, n):
    """[(image offset, rom offset, length)] of the maximal common runs of at least n bytes."""
    index = {}
    for j in range(len(rom) - n + 1):
        w = rom[j:j + n]
        if w.count(w[0]) != n:                              # (one byte repeated: fill, see trimmed())
            index.setdefault(w, []).append(j)
    out, seen = [], set()
    for i in range(len(img) - n + 1):
        for j in index.get(img[i:i + n], ()):
            if (i - j) in seen and i > 0 and j > 0 and img[i - 1] == rom[j - 1]:
                continue                                    # (inside a run already found)
            k = n
            while i + k < len(img) and j + k < len(rom) and img[i + k] == rom[j + k]:
                k += 1
            if i > 0 and j > 0 and img[i - 1] == rom[j - 1]:
                continue
            out.append((i, j, k))
            seen.add(i - j)
    return out


def trimmed(data):
    """The run without the repeated bytes at either end (the image's or the stock ROM's fill)."""
    a, z = 0, len(data)
    while a + 1 < z and data[a] == data[a + 1]:
        a += 1
    while z - 1 > a and data[z - 1] == data[z - 2]:
        z -= 1
    return data[a:z]


def base_of(build, lst, name, default):
    if default is not None:
        return default
    for line in open(os.path.join(build, lst.replace(".lst", ".sym"))):
        p = line.split()
        if p and p[0] == name + ":":
            return int(p[2], 16)
    raise SystemExit("provenance: %s not in %s" % (name, lst))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--min", type=int, default=MIN)
    ap.add_argument("--roms", default=os.environ.get("LEAPC_STOCK_ROMS", os.path.expanduser("~/fuse-build/roms")))
    a = ap.parse_args()
    roms = {}
    for r in STOCK:
        p = os.path.join(a.roms, r)
        if not os.path.exists(p):
            print("provenance: SKIPPED: the stock ROMs are not in %s (set LEAPC_STOCK_ROMS)" % a.roms)
            return 2
        roms[r] = open(p, "rb").read()
    bad = total = 0
    used = set()
    for img_name, lst, base_name, default in IMAGES:
        img = open(os.path.join(a.build, img_name), "rb").read()
        base = base_of(a.build, lst, base_name, default)
        labs = romcov.labels(os.path.join(a.build, lst), base, base + len(img))
        for rom_name, rom in roms.items():
            for i, j, k in runs(img, rom, a.min):
                total += 1
                addr = base + i
                where = max((x for x in labs if x[0] <= addr), default=(base, "?"))
                fill = len(trimmed(img[i:i + k])) < a.min
                key = (img_name, where[1], k)
                why = ALLOWED.get(key) or ("one byte repeated (fill)" if fill else None)
                if key in ALLOWED:
                    used.add(key)
                print("provenance: %s $%04X (%s+%d) = %s $%04X, %d bytes: %s" % (
                    img_name, addr, where[1], addr - where[0], rom_name, j, k, why or "NOT ACCOUNTED FOR"))
                bad += why is None
    for key in ALLOWED:
        if key not in used:
            print("provenance: note: the recorded run %s %s (%d bytes) is no longer found" % key)
    print("provenance: %d common runs of %d bytes or more, %d not accounted for" % (total, a.min, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
