#!/usr/bin/env python3
"""Size of every top-level routine between two labels of a symbol file (shrink work aid).
Usage: routine_sizes.py [SYMFILE] [FROM_LABEL] [TO_LABEL]"""
import re
import sys

sym = sys.argv[1] if len(sys.argv) > 1 else "build/leapc_home.sym"
lo_l = sys.argv[2] if len(sys.argv) > 2 else "COMP_SYMTAB_BEGIN"
hi_l = sys.argv[3] if len(sys.argv) > 3 else "COMP_STMT_END"
syms = {}
for l in open(sym):
    m = re.match(r"([A-Za-z_][A-Za-z0-9_.]*):\s+EQU\s+0x([0-9A-F]+)", l)
    if m:
        syms[m.group(1)] = int(m.group(2), 16)
lo, hi = syms[lo_l], syms[hi_l]
labs = sorted((v, k) for k, v in syms.items() if lo <= v < hi and "." not in k)
labs = [x for i, x in enumerate(labs) if i + 1 == len(labs) or labs[i + 1][0] != x[0] or x[1].startswith("COMP_")]
for i, (v, k) in enumerate(labs):
    nxt = labs[i + 1][0] if i + 1 < len(labs) else hi
    print("%5d %s" % (nxt - v, k))
