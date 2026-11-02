#!/usr/bin/env python3
"""draw()'s pixels, attributes and speed against a model (1.2.0, docs/milestones/M13-draw.md).

The model is draw() as release 1.1.0 defines it: each end moved to the screen's edge (x 0-255, y 0-191),
then the points of the e2 form of Bresenham's line (err = dx - dy; e2 = 2 err; x steps when e2 >= -dy,
y when e2 <= dx), both ends drawn. Each point is set (OR; over(1): XOR) and gives its cell the print
attribute: in mode 0 the 8x8 cell at $5800, in mode 1 the 8x1 byte at the bitmap byte + $2000.

Each case is a C program of draw() calls (random ends on and off the screen, the edges, every octant,
over(1), mode 1), compiled and run on the ROM in ZEsarUX. The bitmap, the attributes and (mode 1) the
second display file must equal the model's, byte for byte.

--time: the T-states of one draw() (the run less an empty program's) for a row, a column and the
diagonal, against ceilings; and of 100 plot() calls.

Usage: linetest.py [--build DIR] [--port N] [--seed N] [--lines N] [--time] [--no-ceilings]
Exit status 0 when everything matches (and, with --time, is under its ceiling), 1 otherwise.
"""
import argparse
import os
import math
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import exectest         # noqa: E402
from lcharness import Machine  # noqa: E402

ROOT = os.path.dirname(HERE)
PER_PROGRAM = 40                 # draw() calls in one program
# T-state ceilings of one draw() (the call and its pixels), 1.2.0: about 1.25 x the measured figure (row 60,702,
# column 51,563, diagonal 81,691 T; 1.1.0: 369,298, 283,902, 388,184)
CEILINGS = {"row": 76_000, "column": 65_000, "diagonal": 102_000}


def clamp(v, hi):
    return 0 if v < 0 else hi if v > hi else v


def line_points(x0, y0, x1, y1):
    """draw()'s points: the ends moved to the edge, then the e2 form."""
    x0, x1 = clamp(x0, 255), clamp(x1, 255)
    y0, y1 = clamp(y0, 191), clamp(y1, 191)
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    pts = []
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= -dy:
            err -= dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def pixel_offset(x, y):
    return ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | (x >> 3)


class Screen:
    """The model's screen after cls() in ink 0, paper 7 (and mode(1): every 8x1 attribute $38)."""

    def __init__(self):
        self.bitmap = bytearray(6144)
        self.attrs = bytearray([0x38]) * 768
        self.hires = bytearray([0x38]) * 6144

    def draw(self, line, attr, over, mode):
        for x, y in line_points(*line):
            o = pixel_offset(x, y)
            mask = 0x80 >> (x & 7)
            self.bitmap[o] = self.bitmap[o] ^ mask if over else self.bitmap[o] | mask
            if mode:
                self.hires[o] = attr
            else:
                self.attrs[(y >> 3) * 32 + (x >> 3)] = attr


def gen_cases(rng, nlines):
    """[(name, mode, [(line, ink, paper, bright, over)])]"""
    def colour():
        return rng.randrange(8), rng.randrange(8), rng.randrange(2)

    fixed = [(0, 0, 255, 191), (255, 191, 0, 0), (0, 191, 255, 0), (0, 0, 255, 0), (0, 191, 255, 191),
             (0, 0, 0, 191), (255, 0, 255, 191), (128, 96, 128, 96), (0, 0, 0, 0), (255, 191, 255, 191),
             (7, 7, 8, 8), (8, 7, 7, 8), (10, 20, 100, 20), (10, 10, 100, 60), (-10, 50, 100, 60),
             (0, 0, 300, 0), (-32768, -32768, 32767, 32767), (-32768, 100, 32767, 110), (300, 200, 400, 300),
             (-5, -5, -1, -1), (100, -50, 120, 250), (250, 5, 300, 7), (40, 40, 215, 40), (40, 95, 215, 95)]
    for a in range(0, 360, 15):                         # every octant from the centre, and back
        r = 90
        fixed.append((128, 96, 128 + round(r * math.cos(math.radians(a))), 96 + round(r * math.sin(math.radians(a)))))
    lines = list(fixed)
    while len(lines) < len(fixed) + nlines:
        if rng.random() < 0.5:
            lines.append((rng.randrange(256), rng.randrange(192), rng.randrange(256), rng.randrange(192)))
        else:
            lines.append((rng.randrange(-300, 561), rng.randrange(-250, 451),
                          rng.randrange(-300, 561), rng.randrange(-250, 451)))
    cases = []
    for mode in (0, 1):
        for over in (0, 1):
            for i in range(0, len(lines), PER_PROGRAM):
                chunk = lines[i:i + PER_PROGRAM]
                cases.append(("mode %d over %d lines %d-%d" % (mode, over, i, i + len(chunk) - 1), mode,
                              [(ln,) + colour() + (over,) for ln in chunk]))
    return cases


def program(mode, draws):
    src = ["#pragma hires" if mode else "", "int main(void)", "{", "    ink(0); paper(7); bright(0); over(0);",
           "    cls();"]
    if mode:
        src.append("    mode(1);")
    cur = None
    for (x0, y0, x1, y1), ink, paper, bright, over in draws:
        if cur != (ink, paper, bright, over):
            src.append("    ink(%d); paper(%d); bright(%d); over(%d);" % (ink, paper, bright, over))
            cur = (ink, paper, bright, over)
        src.append("    draw(%d, %d, %d, %d);" % (x0, y0, x1, y1))
    if mode:
        src.append("    mode(0);")
    src += ["    return 0;", "}"]
    return [s for s in src if s]


def run(m, src, maxi=400_000_000):
    r = exectest.compile_and_run(m, c2src.lines_of("\n".join(src) + "\n"), maxi=maxi, audit=False)
    if not r.compile_ok or r.errnum:
        raise RuntimeError("compile failed (error %s line %s):\n%s" % (r.errnum, r.errline, "\n".join(src)))
    if not r.ran:
        raise RuntimeError("the run did not end:\n" + "\n".join(src))
    return r


def check_pictures(m, cases):
    bad = 0
    for name, mode, draws in cases:
        run(m, program(mode, draws))
        s = Screen()
        for line, ink, paper, bright, over in draws:
            s.draw(line, bright << 6 | paper << 3 | ink, over, mode)
        got = dict(bitmap=m.read(0x4000, 6144), attrs=m.read(0x5800, 768))
        want = dict(bitmap=bytes(s.bitmap), attrs=bytes(s.attrs))
        if mode:
            got["hires"], want["hires"] = m.read(0x6000, 6144), bytes(s.hires)
        diffs = []
        for k in want:
            d = [i for i in range(len(want[k])) if got[k][i] != want[k][i]]
            if d:
                diffs.append("%s: %d bytes differ, first at +$%04X (ROM $%02X, model $%02X)" % (
                    k, len(d), d[0], got[k][d[0]], want[k][d[0]]))
        print("%-34s %3d lines  %s" % (name, len(draws), "ok" if not diffs else "FAIL " + "; ".join(diffs)))
        bad += bool(diffs)
    return bad


def check_time(m, ceilings):
    base = run(m, ["int main(void)", "{", "    cls();", "    return 0;", "}"]).run_t
    bad = 0
    for name, (x0, y0, x1, y1) in (("row", (0, 100, 255, 100)), ("column", (100, 0, 100, 191)),
                                    ("diagonal", (0, 0, 255, 191)), ("short", (10, 10, 100, 60))):
        t = run(m, ["int main(void)", "{", "    cls();", "    draw(%d, %d, %d, %d);" % (x0, y0, x1, y1),
                    "    return 0;", "}"]).run_t - base
        n = len(line_points(x0, y0, x1, y1))
        lim = CEILINGS.get(name) if ceilings else None
        ok = lim is None or t <= lim
        print("draw %-9s %3d pixels %8d T  %5.0f T a pixel%s" % (
            name, n, t, t / n, "" if lim is None else "  (ceiling %d: %s)" % (lim, "ok" if ok else "OVER")))
        bad += not ok
    loop = ["int main(void)", "{", "    int i;", "    cls();", "    for (i = 0; i < 100; i++)", "        %s",
            "    return 0;", "}"]
    t0 = run(m, [l % ";" if "%" in l else l for l in loop]).run_t
    t1 = run(m, [l % "plot(i, 50);" if "%" in l else l for l in loop]).run_t
    print("plot      100 calls       %8d T  %5.0f T a call (the loop's own cost taken off)" % (t1 - t0, (t1 - t0) / 100))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--port", type=int, default=10790)
    ap.add_argument("--seed", type=int, default=2068)
    ap.add_argument("--lines", type=int, default=400, help="random lines besides the fixed ones")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--no-ceilings", action="store_true")
    a = ap.parse_args()
    m = Machine(a.build, a.port)
    try:
        m.start()
        if a.time:
            bad = check_time(m, not a.no_ceilings)
        else:
            bad = check_pictures(m, gen_cases(random.Random(a.seed), a.lines))
    finally:
        m.stop()
    print("linetest: %s" % ("PASS" if not bad else "%d FAILED" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
