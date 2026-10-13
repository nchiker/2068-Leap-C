#!/usr/bin/env python3
"""Routine-level map of a Leap V2 build: size per routine, owning file, and call/jump/data
references between routines (both images). Usage: romdeps.py BUILD_DIR > deps.json"""
import re, sys, json, collections
B = sys.argv[1]
LINE = re.compile(r"^\s*\d+\+*\s*([0-9A-F]{4})(.)((?:[0-9A-F]{2} ?)*)(.*)$")
LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*):(?!\s*equ)", re.I)
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
def parse(path, lo, hi, img):
    stack = []; routines = []; refs = []; cur = None
    for raw in open(path, encoding="utf-8", errors="replace"):
        if raw.startswith("# file opened:"):
            stack.append(raw.split(":", 1)[1].strip()); continue
        if raw.startswith("# file closed:"):
            stack.pop(); continue
        m = LINE.match(raw.rstrip("\n"))
        if not m: continue
        addr = int(m.group(1), 16); flag = m.group(2); hexb = m.group(3).split(); text = m.group(4)
        if "~" in raw[:30]: continue  # inactive conditional
        if not (lo <= addr < hi): continue
        f = stack[-1] if stack else "?"
        lm = LABEL.match(text)
        if lm and not lm.group(1).startswith("."):
            cur = {"name": lm.group(1), "addr": addr, "file": f, "img": img, "bytes": 0}
            routines.append(cur)
        if hexb and cur is not None:
            cur["bytes"] += len(hexb)
            code = text.split(";", 1)[0]
            ids = [i for i in IDENT.findall(code) if not i.startswith(".")]
            refs.append((cur["name"], f, ids))
        elif hexb and cur is None:
            pass
    return routines, refs
r1, f1 = parse(f"{B}/test_basic.lst", 0, 0x4000, "HOME")
r2, f2 = parse(f"{B}/exrom.lst", 0xC000, 0xE000, "EXROM")
def sized(rs, end):
    rs = sorted(rs, key=lambda r: r["addr"])
    for a, b in zip(rs, rs[1:] + [{"addr": end}]):
        a["size"] = b["addr"] - a["addr"]
    return rs
r1 = sized(r1, 0x3FED); r2 = sized(r2, 0xDFE6)
routines = {r["name"]: r for r in r1 + r2}
edges = collections.defaultdict(int)
for name, f, ids in f1 + f2:
    for i in ids:
        i = i.split(".")[0]
        if i in routines and i != name:
            edges[(name, i)] += 1
json.dump({"routines": list(routines.values()), "edges": [[a, b, n] for (a, b), n in edges.items()]},
          sys.stdout, indent=0)
