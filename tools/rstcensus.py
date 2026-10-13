#!/usr/bin/env python3
"""Operation census of the generated code over the executable corpus (project_plan.md Phase 2:
"RST assignment confirmed or retuned from operation frequencies counted over the corpus").

The production ROM compiles every executable case (tests/expr, golden, run, stmt, pp: the ones
that compile); the code in image region 1 ($C000 up to CG_PC) is decoded instruction by
instruction and counted: the RST helpers, every CALL target (named from the ROM's symbols), the
inline frame accesses an RST $30 LDL/STL would replace (spec.md 5.6), and the other templates.
Counts are static (occurrences in the code: what decides code size); a program whose code leaves
region 1 is counted up to the region's end.

Usage: rstcensus.py [--port N] [--json FILE]"""
import argparse
import collections
import glob
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import exectest         # noqa: E402

DIRS = ("expr", "golden", "run", "stmt", "pp")


def length(code, i):
    """Length of the Z80 instruction at code[i]."""
    op = code[i]
    if op in (0xDD, 0xFD):
        o2 = code[i + 1]
        if o2 == 0xCB:
            return 4
        if o2 in (0x21, 0x22, 0x2A, 0x36):
            return 4
        if o2 in (0x34, 0x35) or (0x40 <= o2 <= 0xBF and ((o2 & 7) == 6 or 0x70 <= o2 <= 0x77) and o2 != 0x76):
            return 3
        return 2
    if op == 0xED:
        return 4 if code[i + 1] in (0x43, 0x4B, 0x53, 0x5B, 0x63, 0x6B, 0x73, 0x7B) else 2
    if op == 0xCB:
        return 2
    if op in (0x01, 0x11, 0x21, 0x31, 0x22, 0x2A, 0x32, 0x3A, 0xC3, 0xCD) or (op & 0xC7) in (0xC2, 0xC4):
        return 3
    if (op & 0xC7) == 0x06 or op in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0xD3, 0xDB) or (op & 0xC7) == 0xC6:
        return 2
    return 1


def census(m, cases):
    S = m.S
    names = {}
    for k, v in S.items():
        if k.startswith(("RT_", "MATH_", "LIB_")) and "." not in k:
            names.setdefault(v, k)
    c = collections.Counter()
    nbytes = collections.Counter()
    programs = code_total = 0
    for path in cases:
        res = exectest.compile_and_run(m, c2src.lines_of(open(path, encoding="latin-1").read()), run=False)
        if res.errnum or not res.compile_ok:
            continue
        end = res.code_end
        if not 0xC000 <= end < 0xE000:          # the code went on in another region: region 1's
            end = res.mem.w(S["IMG_LIM"])       # code ends where its data space starts again
        code = res.mem.bytes(0xC000, end - 0xC000 + 4)
        programs += 1
        code_total += end - 0xC000
        i = 0
        while i < end - 0xC000:
            n = length(code, i)
            op = code[i]
            if (op & 0xC7) == 0xC7:
                key = {0xCF: "rst $08 LDI", 0xD7: "rst $10 STI", 0xDF: "rst $18 ENTER n", 0xE7: "rst $20 LEAVE",
                       0xEF: "rst $28 CMPLT"}.get(op, "rst $%02X" % (op & 0x38))
                if op == 0xDF:
                    n = 2                       # the frame size byte
            elif op == 0xCD:
                t = code[i + 1] | code[i + 2] << 8
                key = "call " + names.get(t, "a program function" if t >= 0x6000 else "$%04X" % t)
                if key == "call RT_SWITCH":
                    n += 2                      # the table's address follows the call
            elif op == 0xDD and code[i + 1] in (0x6E, 0x66):
                key = "ld l/h,(ix+d)  frame load (LDL candidate)"
            elif op == 0xDD and code[i + 1] in (0x75, 0x74):
                key = "ld (ix+d),l/h  frame store (STL candidate)"
            elif op == 0x21:
                key = "ld hl,nn"
            elif op == 0x11:
                key = "ld de,nn"
            elif op in (0x2A, 0x22):
                key = "ld hl,(nn) / ld (nn),hl  global"
            elif op == 0xC3:
                key = "jp nn"
            elif (op & 0xC7) == 0xC2:
                key = "jp cc,nn"
            elif op in (0xE5, 0xD1, 0xE1, 0xC1):
                key = "push hl / pop de, hl, bc"
            else:
                key = "other"
            c[key] += 1
            nbytes[key] += n
            i += n
    return programs, code_total, c, nbytes


def main():
    from lcharness import Machine
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10790)
    ap.add_argument("--json")
    ap.add_argument("--nogen", action="store_true", help="leave out the generated operator cases")
    a = ap.parse_args()
    cases = []
    for d in DIRS:
        cases += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
    if a.nogen:
        cases = [c for c in cases if os.sep + "gen" + os.sep not in c]
    m = Machine(os.path.join(ROOT, "build"), a.port)
    try:
        m.start()
        programs, total, c, nb = census(m, cases)
    finally:
        m.stop()
    print("%d programs, %d bytes of code in region 1" % (programs, total))
    print("%-48s %7s %7s %6s" % ("operation", "count", "bytes", "share"))
    for k, v in c.most_common():
        print("%-48s %7d %7d %5.1f%%" % (k, v, nb[k], 100.0 * nb[k] / total))
    if a.json:
        json.dump(dict(programs=programs, code_bytes=total, counts=c, bytes=nb), open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
