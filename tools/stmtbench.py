#!/usr/bin/env python3
"""The spike workloads compiled by the real compiler (project_plan.md Phase 2 completion criterion):
code bytes per function and T-states per call, against the code-shape spike's mixed-template form
(spike/results/spike_results.json, Mrst_C000: its hand-assembled output from the same templates).

The production ROM compiles tests/spike/workloads.c and runs its main (which sets up the arrays);
each workload is then called from a driver assembled into RAM exactly as the spike's driver did:
interrupts off, the arguments pushed last first, the call, the arguments popped; ZEsarUX's T-state
counter times the driver from before the pushes to after the pops, and the result is checked.

measure(m) -> list of dict(name, bytes, spike_bytes, tstates, spike_tstates, ok, detail)
Usage: stmtbench.py [--port N]"""
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import exectest         # noqa: E402

DRIVER = 0xF000
# name, function, the spike's case id, arguments (C order; names are program globals), check
CASES = [
    ("sum(255)", "sum", "sum", [255], lambda r, mem, g: r["HL"] == 32640),
    ("copy(dst, src, 256)", "copy", "copy", ["dst", "src", 256],
     lambda r, mem, g: mem(g["dst"], 256) == bytes(range(256))),
    ("asum(100)", "asum", "asum", [100], lambda r, mem, g: r["HL"] == 4950),
    ("move(pts, 20, 3)", "move", "move", ["pts", 20, 3],
     lambda r, mem, g: all(mem(g["pts"] + 5 * i, 4) == bytes([(i + 3) & 255, 0, (i + 3) & 255, 0]) for i in range(20))),
    ("fact(7)", "fact", "fact7", [7], lambda r, mem, g: r["HL"] == 5040),
]
SIZE_NAMES = {"sum": "SUM", "copy": "COPY", "asum": "ASUM", "move": "MOVE", "fact": "FACT"}


def measure(m):
    spike = json.load(open(os.path.join(ROOT, "spike", "results", "spike_results.json")))
    lines = c2src.lines_of(open(os.path.join(ROOT, "tests", "spike", "workloads.c")).read())
    res = exectest.compile_and_run(m, lines, audit=False)
    out = []
    if res.errnum or not res.ran or res.hl != 0:
        return [dict(name="compile and set-up", ok=False, detail="error %s, ran %s" % (res.errnum, res.ran))]
    g = {}
    for e in res.globals:
        if e.kind < 0x10:
            g.setdefault(e.name, e.val)
    funcs = sorted(e.val for e in res.globals if e.kind == 2 and e.flags & 8)
    m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)          # chunk 6 = RAM, as RT_RUN has it
    for name, fn, sid, args, check in CASES:
        start = g[fn]
        end = [a for a in funcs if a > start]
        nbytes = (end[0] if end else res.code_end) - start
        d = tempfile.mkdtemp(prefix="lcsb-")
        src = ["    DEVICE ZXSPECTRUM48", "    ORG $%04X" % DRIVER, "start: di", "t0:"]
        for a in reversed(args):
            src += ["    ld hl,%s" % (("$%04X" % g[a]) if isinstance(a, str) else str(a)), "    push hl"]
        src += ["    call $%04X" % start] + ["    pop bc"] * len(args)
        src += ["t1: jr t1", '    SAVEBIN "%s/b.bin", $%04X, $-$%04X' % (d, DRIVER, DRIVER)]
        open(d + "/b.asm", "w").write("\n".join(src) + "\n")
        subprocess.run(["sjasmplus", "--nologo", "--sym=" + d + "/b.sym", d + "/b.asm"], check=True,
                       capture_output=True)
        lab = {l.split()[0].rstrip(":"): int(l.split()[2], 16) for l in open(d + "/b.sym") if " EQU " in l}
        m.write(DRIVER, open(d + "/b.bin", "rb").read())
        m.setreg("SP", 0xFF00)
        m.setreg("PC", DRIVER)
        m.run_to([lab["t0"]], 100_000)
        m.tstates_reset()
        ok = m.run_to([lab["t1"]], 5_000_000) == lab["t1"]
        t = m.tstates()
        r = m.regs()
        ok = ok and bool(check(r, lambda a, n: m.read(a, n), g))
        out.append(dict(name=name, bytes=nbytes, spike_bytes=spike["sizes"]["Mrst_C000"][SIZE_NAMES[fn]],
                        tstates=t, spike_tstates=spike["cases"]["Mrst_C000/%s/di" % sid]["t"], ok=ok,
                        detail="" if ok else "HL=%04X" % r["HL"]))
    return out


def main():
    import argparse
    from lcharness import Machine
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10790)
    a = ap.parse_args()
    m = Machine(os.path.join(ROOT, "build"), a.port)
    try:
        m.start()
        tb = ts = sb = ss = 0
        for r in measure(m):
            if "bytes" not in r:
                print(r)
                continue
            print("%-22s %s %3d B (spike %3d, %+5.1f%%)  %7d T (spike %7d, %+5.1f%%)" % (
                r["name"], "PASS" if r["ok"] else "FAIL", r["bytes"], r["spike_bytes"],
                100.0 * (r["bytes"] - r["spike_bytes"]) / r["spike_bytes"], r["tstates"], r["spike_tstates"],
                100.0 * (r["tstates"] - r["spike_tstates"]) / r["spike_tstates"]))
            tb += r["bytes"]; sb += r["spike_bytes"]; ts += r["tstates"]; ss += r["spike_tstates"]
        print("%-22s      %3d B (spike %3d, %+5.1f%%)  %7d T (spike %7d, %+5.1f%%)" % (
            "all", tb, sb, 100.0 * (tb - sb) / sb, ts, ss, 100.0 * (ts - ss) / ss))
    finally:
        m.stop()


if __name__ == "__main__":
    main()
