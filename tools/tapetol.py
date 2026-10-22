#!/usr/bin/env python3
"""The tape receiver's tolerance envelope (Phase 11, M11-tape; spec.md 8, docs/TAPE_SIGNAL_SPEC.md).

A program tape (a header block and a data block, the stock pilots) is synthesised with a distortion, written
as a TZX direct recording (block $15, 4 T a sample: the pulse widths exact to 4 T) and LOADed with `LOAD ""`
on Fuse 1.9.1 (tools/fusedrive.py: the ROM's own receiver, Fuse's tape deck started and stopped by its loader
detection, its loader acceleration off so that the ROM's own timing loops measure every pulse). A case passes
when the report is LOADED and the line store is the program.

The distortions (tools/tapes.py's stock widths and pilots otherwise):
  scale-all/pilot/sync/bits S   those pulse widths times 1 + S (S = -25%..+25% in 5% steps)
  jitter J                      every pulse's width times a uniform 1 +- J (seeded)
  scale+jitter                  combinations
  bit-skew K                    each bit's first half-pulse times 1 + K, the second times 1 - K
  pilot-short N                 N pilot pulses before each block instead of 8,063 / 3,223
  pilot-missing / -extra        one edge missing in the middle of each pilot (a 4,336 T pulse) / one more
                                pilot pulse (the sync and data inverted)
  pilot-missing-end             one edge missing 4 pulses before the sync
  inverted                      the whole signal inverted
  pilot-dropout D               D ms without an edge in the middle of each pilot
  data-dropout D                D ms without an edge in the data block (a LOAD that must fail)

Usage: tapetol.py [--build DIR ...] [--json OUT] [--workers N] [--only SUBSTR]
  With two or more --build directories (e.g. the beta.1 images, then the current ones), the report compares
  them: every case the first accepts must be accepted by each later one.
"""
import argparse
import json
import multiprocessing as mp
import os
import random
import shutil
import struct
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2tape           # noqa: E402
import tapes            # noqa: E402
from fusedrive import Fuse, glyph_tables  # noqa: E402

ROOT = os.path.dirname(HERE)
PROG = ["int main(void)", "{", '    puts("TOL");', "    return 3;", "}"]
NAME = "tol"
SAMPLE = 4                                  # T-states a direct-recording sample
WIDTHS = dict(pilot=tapes.PILOT_T, sync1=tapes.SYNC1_T, sync2=tapes.SYNC2_T, zero=tapes.ZERO_T, one=tapes.ONE_T)


def synth(blocks, scale=None, jitter=0.0, skew=0.0, pilot=None, missing=None, extra=False, invert=False,
          pilot_dropout=0.0, data_dropout=0.0, seed=1):
    """The blocks' EAR signal as [(level, T)] runs, distorted (the module docstring)."""
    scale = scale or {}
    rnd = random.Random(seed)
    runs, level = [], 1 if invert else 0

    def w(kind, f=1.0):
        t = WIDTHS[kind] * (1 + scale.get(kind if kind in ("pilot",) else
                                          "sync" if kind.startswith("sync") else "bits", 0.0)) * f
        if jitter:
            t *= 1 + rnd.uniform(-jitter, jitter)
        return max(SAMPLE, int(round(t)))

    def pulse(t):
        nonlocal level
        runs.append((level, t))
        level ^= 1

    def flat(t):
        runs.append((level, t))

    flat(tapes.CPU_HZ)                                      # 1 s of silence first
    for data in blocks:
        n = (tapes.HEADER_PILOT if data[0] < 0x80 else tapes.DATA_PILOT) if pilot is None else pilot
        n += 1 if extra else 0
        for i in range(n):
            if missing == "mid" and i == n // 2:
                runs[-1] = (runs[-1][0], runs[-1][1] + w("pilot"))        # no edge: two widths at one level
                continue
            if missing == "end" and i == n - 4:
                runs[-1] = (runs[-1][0], runs[-1][1] + w("pilot"))
                continue
            if pilot_dropout and i == n // 2:
                flat(int(pilot_dropout * tapes.CPU_HZ / 1000))
            pulse(w("pilot"))
        pulse(w("sync1"))
        pulse(w("sync2"))
        bits = [v >> k & 1 for v in data for k in range(7, -1, -1)]
        for j, b in enumerate(bits):
            if data_dropout and data[0] >= 0x80 and j == len(bits) // 2:
                flat(int(data_dropout * tapes.CPU_HZ / 1000))
            kind = "one" if b else "zero"
            pulse(w(kind, 1 + skew))
            pulse(w(kind, 1 - skew))
        pulse(w("zero"))
        flat(tapes.CPU_HZ)                                  # 1 s between the blocks and after the last
    return runs


def tzx_direct(runs):
    """A TZX file of one direct-recording block ($15), SAMPLE T-states a sample, the levels of `runs`."""
    parts, t = [], 0
    for level, dt in runs:
        t1 = t + dt
        parts.append("01"[level] * (t1 // SAMPLE - t // SAMPLE))
        t = t1
    bits = "".join(parts)
    used = len(bits) % 8 or 8
    bits += "0" * (-len(bits) % 8)
    data = int("1" + bits, 2).to_bytes(len(bits) // 8 + 1, "big")[1:]
    return (b"ZXTape!\x1a" + bytes([1, 20]) + bytes([0x15]) + struct.pack("<HHB", SAMPLE, 0, used) +
            struct.pack("<I", len(data))[:3] + bytes(data))


def cases():
    out = []
    steps = [s / 100 for s in range(-25, 26, 5)]
    for part in ("all", "pilot", "sync", "bits"):
        for s in steps:
            if part != "all" and s == 0:
                continue
            sc = dict(pilot=s, sync=s, bits=s) if part == "all" else {part: s}
            out.append(("scale-%s %+d%%" % (part, round(s * 100)), dict(scale=sc)))
    for j in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
        out.append(("jitter %d%%" % round(j * 100), dict(jitter=j)))
    for s in (-0.20, -0.10, 0.10, 0.20):
        out.append(("scale-all %+d%% jitter 10%%" % round(s * 100),
                    dict(scale=dict(pilot=s, sync=s, bits=s), jitter=0.10)))
    for k in (0.10, 0.20, 0.30):
        out.append(("bit-skew %d%%" % round(k * 100), dict(skew=k)))
    for n in (2000, 1500, 1000, 800, 600, 400):
        out.append(("pilot-short %d" % n, dict(pilot=n)))
    out.append(("pilot-missing", dict(missing="mid")))
    out.append(("pilot-missing-end", dict(missing="end")))
    out.append(("pilot-extra", dict(extra=True)))
    out.append(("inverted", dict(invert=True)))
    for d in (2, 10, 50, 200):
        out.append(("pilot-dropout %d ms" % d, dict(pilot_dropout=d)))
    for d in (1, 5, 20):
        out.append(("data-dropout %d ms" % d, dict(data_dropout=d)))
    return out


def worker(build, k, todo, q):
    blocks = c2tape.program_blocks("\n".join(PROG) + "\n", NAME)
    wdir = os.path.join(ROOT, "build", "tapetol", "%s-%d" % (os.path.basename(os.path.normpath(build)), k))
    shutil.rmtree(wdir, ignore_errors=True)
    os.makedirs(wdir)
    f = None
    try:
        for name, kw in todo:
            path = os.path.join(wdir, "case.tzx")
            open(path, "wb").write(tzx_direct(synth(blocks, **kw)))
            for attempt in (1, 2):              # (a harness failure, e.g. a lost key handshake: a new Fuse, again)
                try:
                    if f is None:
                        f = Fuse(build, os.path.join(wdir, "fuse"), extra=["--no-accelerate-loader"]).start()
                    f.new()
                    r = f.cmd("tape_open %s" % path)
                    if r != "0":
                        q.put((name, False, "tape_open: %s" % r))
                        break
                    f.command('load ""', timeout=600)
                    msg = f.rows()[22]
                    f.key(" ")
                    q.put((name, msg == "LOADED %s" % NAME and f.store() == PROG, msg))
                    break
                except Exception as e:
                    if f:
                        f.stop()
                    f = None
                    if attempt == 2:
                        q.put((None, False, "%s %r: %r" % (wdir, name, e)))
    finally:
        if f:
            f.stop()


def run(build, workers, only):
    todo = [c for c in cases() if not only or only in c[0]]
    glyph_tables(build)                 # (the screen reader's cache, made once: its ZEsarUX has a fixed port)
    q, procs = mp.Queue(), []
    for k in range(workers):
        p = mp.Process(target=worker, args=(build, k, todo[k::workers], q), daemon=True)
        p.start()
        procs.append(p)
    res = {}
    while any(p.is_alive() for p in procs) or not q.empty():
        try:
            name, ok, msg = q.get(timeout=1)
        except Exception:
            continue
        if name is None:
            print("tapetol: worker failed: %s" % msg, file=sys.stderr)
            continue
        res[name] = dict(ok=ok, msg=msg)
    for p in procs:
        p.join()
    return [(n, res.get(n)) for n, _ in todo]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="append", help="an image directory (default: build)")
    ap.add_argument("--json", default=os.path.join(ROOT, "build", "tapetol.json"))
    ap.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 4) - 1)))
    ap.add_argument("--only")
    a = ap.parse_args()
    builds = a.build or [os.path.join(ROOT, "build")]
    table = {}
    for b in builds:
        table[b] = run(b, a.workers, a.only)
    names = [n for n, _ in table[builds[0]]]
    print("%-28s %s" % ("case", "  ".join("%-14s" % os.path.basename(os.path.normpath(b)) for b in builds)))
    narrower, missing = [], []
    for i, n in enumerate(names):
        cells = []
        for b in builds:
            r = table[b][i][1]
            cells.append("-- not run --" if r is None else ("accept" if r["ok"] else "refuse (%s)" % r["msg"][:20]))
            if r is None:
                missing.append((b, n))
        print("%-28s %s" % (n, "  ".join("%-14s" % c for c in cells)))
        first = table[builds[0]][i][1]
        for b in builds[1:]:
            r = table[b][i][1]
            if first and first["ok"] and not (r and r["ok"]):
                narrower.append((b, n))
    json.dump({b: {n: r for n, r in table[b]} for b in builds}, open(a.json, "w"), indent=1)
    for b in builds:
        acc = sum(1 for _, r in table[b] if r and r["ok"])
        print("tapetol: %s accepts %d of %d cases" % (b, acc, len(names)))
    for b, n in narrower:
        print("tapetol: NARROWER: %s refuses %r, which %s accepts" % (b, n, builds[0]))
    for b, n in missing:
        print("tapetol: NOT RUN: %s %r" % (b, n))
    return 1 if narrower or missing else 0


if __name__ == "__main__":
    sys.exit(main())
