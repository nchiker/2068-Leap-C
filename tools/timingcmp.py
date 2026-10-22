"""Timing on two emulators (Phase 9): the same programs compiled and run through the shell's RUN on
ZEsarUX 13.0 and on Fuse 1.9.1, measured in T-states over the same HOME spans:

  compile   SH_COMPILE to the instruction after its `call CC_PROGRAM` (src/rom/home.asm)
  run       RT_RUN to RT_RUN.leave (the program, with the run's fixed setup and teardown)
  frames    the ISR's FRAMES count over the run (frames(): the frame rate is the emulator's)

ZEsarUX measures with its T-state counter (lcharness: run to each address). Fuse prints its frame count
and the T-states in the frame at debugger breakpoints there (tools/fusedrive.py), the T-states being
frames x 58,688 + those. Each program's report (rows 22-23) must be the same on both.

Why the two can differ: ZEsarUX runs its TS2068 with the 48K Spectrum's frame (69,888 T: 50 Hz) and the
48K's contention timing; Fuse with the TS2068's (58,688 T: 60 Hz, 192 of 262 lines contended). So the ISR
(about 2,000 T a frame) runs 20% more often on Fuse, and code or data in $4000-$7FFF (the display files,
image region 4) waits more. A real TS2068 has Fuse's frame. The fixtures are tests/timing/*.c and, for the
compile alone, every documentation example that needs no key during its run.

Usage: timingcmp.py [--json OUT] [--md OUT]
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import c2tape           # noqa: E402
import tapes            # noqa: E402
from lcharness import Machine  # noqa: E402
from shelltest import Shell, ENTER  # noqa: E402
from fusedrive import Fuse, TPF, fuse_version  # noqa: E402

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
CPU_HZ = 3_528_000
ZX_FRAME = 69_888


def fixtures():
    return sorted(glob.glob(os.path.join(ROOT, "tests", "timing", "*.c")))


def zesarux_measure(m, sh, lines):
    """compile T, run T, FRAMES over the run, rows 22-23 (the report) on ZEsarUX."""
    S = m.sym
    sh.load(lines, len(lines))
    for ch in "run":
        sh.key(ord(ch))
    m.write(S("KBD_LASTK"), ENTER)
    m.write(S("KBD_KEYHIT"), 0xFF)
    m.cmd("cpu-step")
    assert m.run_to([S("SH_COMPILE")], 60_000_000) == S("SH_COMPILE"), "RUN did not compile"
    m.tstates_reset()
    assert m.run_to([S("SH_COMPILE") + 6], 200_000_000) == S("SH_COMPILE") + 6, "the compile did not end"
    compile_t = m.tstates()
    if m.read(S("CC_ERRNUM"), 1)[0]:                # a compile error (an example that shows one): no run
        sh._wait(60_000_000)
        rows = m.screen_rows()
        return dict(compile_t=compile_t, run_t=None, frames=None, report=rows[22:24], row0=rows[0])
    assert m.run_to([S("RT_RUN")], 60_000_000) == S("RT_RUN"), "the program did not start"
    f0 = m.w16(S("FRAMES"))
    m.tstates_reset()
    assert m.run_to([S("RT_RUN.leave")], 400_000_000) == S("RT_RUN.leave"), "the program did not end"
    run_t, f1 = m.tstates(), m.w16(S("FRAMES"))
    msg = sh._wait(60_000_000)
    rows = m.screen_rows()
    return dict(compile_t=compile_t, run_t=run_t, frames=(f1 - f0) & 0xFFFF, report=rows[22:24], row0=rows[0])


MARK = 0xB1000


def fuse_arm(f):
    """Breakpoints printing MARK + k, the frame count and the frame's T-states at the four points."""
    S = f.S
    for k, a in enumerate((S["SH_COMPILE"], S["SH_COMPILE"] + 6, S["RT_RUN"], S["RT_RUN.leave"])):
        f.nbp += 1
        f.dbg("break 0x%04x\ncommands %d\nprint 0x%x\nprint spectrum:frames\nprint ula:tstates\nprint [0x%04x]+256*[0x%04x]"
              "\ncontinue\nend" % (a, f.nbp, MARK + k, S["FRAMES"], S["FRAMES"] + 1))


def fuse_measure(f, lines, tapedir):
    tap = os.path.join(tapedir, "t.tap")
    open(tap, "wb").write(tapes.tap(c2tape.program_blocks("\n".join(lines) + "\n", "timing")))
    assert f.cmd("tape_open %s" % tap) == "0"
    f.command('load ""')
    f.key(" ")
    seen = {k: len(f.prints(MARK + k)) for k in range(4)}
    rows = f.run(timeout=900)
    if rows[22].startswith("ERROR"):
        got = f.prints(MARK + 1)
        f.key(" ")
        return dict(compile_t=(got[-1][0] - f.prints(MARK)[-1][0]) * TPF + got[-1][1] - f.prints(MARK)[-1][1],
                    run_t=None, frames=None, report=rows[22:24], row0=rows[0])
    pts = {}
    for k in range(4):
        got = f.prints(MARK + k)
        assert len(got) == seen[k] + 1, "Fuse: point %d printed %d times" % (k, len(got) - seen[k])
        pts[k] = got[-1]

    def span(a, b):
        return (pts[b][0] - pts[a][0]) * TPF + pts[b][1] - pts[a][1]
    frames = (pts[3][2] - pts[2][2]) & 0xFFFF
    f.key(" ")
    return dict(compile_t=span(0, 1), run_t=span(2, 3), frames=frames, report=rows[22:24], row0=rows[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(BUILD, "timing.json"))
    ap.add_argument("--md", default=os.path.join(BUILD, "timing.md"))
    ap.add_argument("--port", type=int, default=10852)
    a = ap.parse_args()
    progs = [(os.path.relpath(p, ROOT), c2src.lines_of(open(p).read())) for p in fixtures()]
    docs = [(os.path.relpath(p, ROOT), c2src.lines_of(open(p).read()))
            for p in sorted(glob.glob(os.path.join(ROOT, "tests", "doc", "*.c")))
            if not re.search(r"//\s*(keys|break|library):", open(p).read())]   # (no key during the run, no library)
    results = {}
    m = Machine(BUILD, a.port)
    try:
        m.start()
        sh = Shell(m)
        zboot = m.boot["tstates"]
        for name, lines in progs + docs:
            results[name] = dict(zesarux=zesarux_measure(m, sh, lines))
    finally:
        m.stop()
    wdir = os.path.join(BUILD, "fuse", "timing")
    shutil.rmtree(wdir, ignore_errors=True)
    f = Fuse(BUILD, wdir).start()
    try:
        fboot = f.boot["total"]
        fuse_arm(f)
        for name, lines in progs + docs:
            results[name]["fuse"] = fuse_measure(f, lines, wdir)
    finally:
        f.stop()
    bad = []
    for name, r in results.items():
        z, u = r["zesarux"], r["fuse"]
        if z["report"][0] != u["report"][0] or (not z["report"][0].startswith("ERROR") and z["row0"] != u["row0"]):
            bad.append("%s: ZEsarUX %r %r, Fuse %r %r" % (name, z["report"], z["row0"], u["report"], u["row0"]))
    out = ["# Timing: ZEsarUX 13.0 and Fuse %s (Phase 9, tools/timingcmp.py)" % fuse_version(), "",
           "T-states over the same HOME spans; a real TS2068 has Fuse's frame (58,688 T, 60 Hz). Time at 3.528 MHz.", "",
           "| Measure | ZEsarUX | Fuse | Fuse / ZEsarUX |", "|---|---:|---:|---:|",
           "| cold start to the editor's key wait (T) | %d | %d | %.3f |" % (zboot, fboot, fboot / zboot),
           "| frame (T) | %d | %d | %.3f |" % (ZX_FRAME, TPF, TPF / ZX_FRAME), "",
           "| Program | report | run T ZEsarUX | run T Fuse | Fuse / ZEsarUX | frames ZEsarUX / Fuse | run on a TS2068 (s) | compile T ZEsarUX | compile T Fuse |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, _ in progs:
        z, u = results[name]["zesarux"], results[name]["fuse"]
        out.append("| `%s` | %s | %d | %d | %.4f | %d / %d | %.3f | %d | %d |" % (
            name, z["report"][0], z["run_t"], u["run_t"], u["run_t"] / z["run_t"], z["frames"], u["frames"],
            u["run_t"] / CPU_HZ, z["compile_t"], u["compile_t"]))
    zc = sum(results[n]["zesarux"]["compile_t"] for n, _ in docs)
    uc = sum(results[n]["fuse"]["compile_t"] for n, _ in docs)
    nl = sum(len(l) for _, l in docs)
    out += ["", "Compile of the %d documentation examples (%d lines): ZEsarUX %d T (%.2f ms a line), Fuse %d T "
            "(%.2f ms a line), Fuse / ZEsarUX %.4f." % (len(docs), nl, zc, zc / nl / 3528.0, uc, uc / nl / 3528.0, uc / zc)]
    if bad:
        out += ["", "**Reports differ:**"] + ["- " + b for b in bad]
    text = "\n".join(out) + "\n"
    open(a.md, "w").write(text)
    json.dump(dict(results=results, zesarux_boot=zboot, fuse_boot=fboot, differ=bad), open(a.json, "w"), indent=1)
    print(text)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
