#!/usr/bin/env python3
"""Turn `jp` / `jp z|nz|c|nc` into `jr` wherever the assembled target is in relative range
(a shrink aid, project_plan.md 1.2 step 1). Reads the production listing, edits the given source
files in place, and reports how many jumps changed; run `make prod` and repeat until it reports 0
(shrinking only moves targets closer, so a converted jump never goes out of range again).

Usage: relax_jumps.py [--list build/leapc_home.lst] FILE.asm...   (files under src/)"""
import argparse
import os
import re

OPS = {0xC3: "", 0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="build/leapc_home.lst")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    wanted = {os.path.basename(f): f for f in a.files}
    stack = []
    edits = {}
    for line in open(a.list, encoding="latin-1"):
        m = re.match(r"# file opened: (.*)", line)
        if m:
            stack.append(os.path.basename(m.group(1).strip()))
            continue
        m = re.match(r"# file closed: (.*)", line)
        if m:
            stack.pop()
            continue
        if not stack or stack[-1] not in wanted:
            continue
        m = re.match(r"\s*(\d+)\+*\s+([0-9A-F]{4})\s+((?:[0-9A-F]{2} )+)\s*(.*)$", line)
        if not m:
            continue
        lineno, addr = int(m.group(1)), int(m.group(2), 16)
        code = [int(x, 16) for x in m.group(3).split()]
        src = m.group(4)
        if len(code) != 3 or code[0] not in OPS or not re.match(r"\s*jp\s", src):
            continue
        target = code[1] | code[2] << 8
        d = target - (addr + 2)
        if -128 <= d <= 127:
            edits.setdefault(wanted[stack[-1]], set()).add(lineno)
    total = 0
    for f, lines in edits.items():
        src = open(f).read().split("\n")
        for n in lines:
            new = re.sub(r"\bjp(\s+)", r"jr\1", src[n - 1], count=1)
            if new != src[n - 1]:
                src[n - 1] = new
                total += 1
        open(f, "w").write("\n".join(src))
    print("relax_jumps: %d jumps changed to jr" % total)


if __name__ == "__main__":
    main()
