#!/usr/bin/env python3
"""Compile and run one C file on the production ROM in ZEsarUX and show what happened (a
development aid for M1.3+; the test runner uses tools/exectest.py).

Usage: runc.py FILE.c [--port N] [--noaudit] [--dis]
Prints the compile error or the exit value / runtime error, the audit findings, each function's
address and code bytes (--dis: disassembled with z80dasm if installed)."""
import argparse
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import exectest         # noqa: E402
from decltest import ER_NAME   # noqa: E402
from lcharness import Machine  # noqa: E402

ROOT = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--port", type=int, default=10770)
    ap.add_argument("--noaudit", action="store_true")
    ap.add_argument("--words", nargs=2, metavar=("NAME", "N"), help="print N signed words of global NAME")
    a = ap.parse_args()
    lines = c2src.lines_of(open(a.file, encoding="latin-1").read())
    m = Machine(os.path.join(ROOT, "build"), a.port)
    try:
        m.start()
        r = exectest.compile_and_run(m, lines, audit=not a.noaudit)
        print("compile: %s, %d T (%d lines, %.2f ms/line)" % (
            "returned" if r.compile_ok else "DID NOT RETURN", r.compile_t, len(lines),
            r.compile_t / max(1, len(lines)) / 3528.0))
        if r.errnum:
            print("error %s at line %d" % (ER_NAME.get(r.errnum, r.errnum), r.errline))
        funcs = sorted((e.val, e.name) for e in r.globals if e.kind == 2 and e.flags & 8)
        bounds = [a for a, _ in funcs] + [r.code_end]
        for i, (addr, name) in enumerate(funcs):
            n = bounds[i + 1] - addr
            print("%-12s $%04X %3d B: %s" % (name, addr, n, r.mem.bytes(addr, max(0, min(n, 200))).hex(" ")))
        print("code end $%04X" % r.code_end)
        if r.ran:
            hl = r.hl - 65536 if r.hl & 0x8000 else r.hl
            print("run: exit %d ($%04X), runtime error %d, %d T, SP %04X, depth %d" % (
                hl, r.hl, r.a, r.run_t, r.sp, r.depth))
        elif not r.errnum:
            print("run: did not return (PC=%04X)" % getattr(r, "pc", 0))
        for f in r.audit:
            print("AUDIT:", f)
        if a.words:
            e = [g for g in r.globals if g.name == a.words[0]][0]
            ws = [r.mem.w(e.val + 2 * i) for i in range(int(a.words[1]))]
            print("%s: %s" % (a.words[0], " ".join("%d:%d" % (i, w - 65536 if w & 0x8000 else w)
                                                    for i, w in enumerate(ws))))
    finally:
        m.stop()


if __name__ == "__main__":
    main()
