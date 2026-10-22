#!/usr/bin/env python3
"""Per-component ROM budget report and check (spec.md section 2.2, project_plan.md section 1.2).

Usage: budget.py [--check] [--json OUT] [--build DIR]
Reads budget.toml and the production symbol files build/leapc_home.sym, build/leapc_exrom.sym.
Prints the budget table and the ROM map. With --check, exits 1 when a component exceeds its budget,
when code is not covered by exactly one component, or when a reserve falls below its floor. A ledger entry
whose component is "reserve_floor" changes the bank's floor (Phase 10, owner decision)."""
import argparse
import json
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_syms(path):
    out = {}
    for line in open(path):
        m = re.match(r"([A-Za-z_][A-Za-z0-9_.]*):\s+EQU\s+0x([0-9A-F]+)", line, re.I)
        if m:
            out[m.group(1)] = int(m.group(2), 16)
    return out


def bank_report(name, cfg, syms, ledger):
    base = cfg.get("base", 0)
    end = syms[cfg["code_end"]]
    errors = []
    comps = []
    intervals = []
    pinned = []
    for c in cfg["component"]:
        delta = sum(e["delta"] for e in ledger if e["bank"] == name and e["component"] == c["id"])
        size = 0
        rs = []
        for a, b in c["ranges"]:
            lo, hi = syms[a], syms[b]
            if hi < lo:
                errors.append("%s: range %s..%s is negative" % (c["id"], a, b))
            rs.append((lo, hi))
            (pinned if c.get("pinned") else intervals).append((lo, hi, c["id"]))
            size += hi - lo
        budget = c["budget"] + delta
        comps.append(dict(id=c["id"], title=c["title"], base_budget=c["budget"], ledger=delta,
                          budget=budget, size=size, ranges=rs))
        if size > budget:
            errors.append("%s: %d B exceeds its budget of %d B" % (c["id"], size, budget))
    # coverage: the components must tile base..end exactly
    intervals.sort()
    pos = base
    for lo, hi, cid in intervals:
        if lo == hi:
            continue
        if lo > pos:
            errors.append("unaccounted bytes $%04X-$%04X (%d B)" % (pos, lo - 1, lo - pos))
        elif lo < pos:
            errors.append("%s overlaps the previous component at $%04X" % (cid, lo))
        pos = max(pos, hi)
    if pos != end:
        errors.append("components end at $%04X, code ends at $%04X" % (pos, end))
    for lo, hi, cid in pinned:              # (a pinned component lies above the code at a fixed address:
        if lo < end:                        # Phase 10, the library slots at the end of HOME)
            errors.append("%s at $%04X overlaps the code (ends $%04X)" % (cid, lo, end))
    used = end - base + sum(hi - lo for lo, hi, _ in pinned)
    allocated = sum(c["budget"] for c in comps)
    reserve = cfg["size"] - allocated
    floor = cfg["reserve_floor"] + sum(e["delta"] for e in ledger if e["bank"] == name and e["component"] == "reserve_floor")
    if reserve < floor:
        errors.append("reserve %d B is below the floor of %d B" % (reserve, floor))
    return dict(bank=name, size=cfg["size"], base=base, used=used, free=cfg["size"] - used,
                allocated=allocated, reserve=reserve, reserve_floor=floor,
                components=comps, intervals=[i for i in intervals if i[0] != i[1]], pinned=sorted(pinned),
                code_end=end, errors=errors)


def print_report(r):
    print("%s ROM: %d B used, %d B free of %d B; allocated %d B, reserve %d B (floor %d B)" % (
        r["bank"].upper(), r["used"], r["free"], r["size"], r["allocated"], r["reserve"],
        r["reserve_floor"]))
    print("  %-12s %6s %7s %6s  %s" % ("component", "size", "budget", "left", "title"))
    for c in r["components"]:
        led = " (ledger %+d)" % c["ledger"] if c["ledger"] else ""
        print("  %-12s %6d %7d %6d  %s%s" % (c["id"], c["size"], c["budget"], c["budget"] - c["size"],
                                            c["title"], led))
    print("  ROM map:")
    for lo, hi, cid in r["intervals"]:
        print("    $%04X-$%04X %6d  %s" % (lo, hi - 1, hi - lo, cid))
    top = r["pinned"][0][0] if r["pinned"] else r["base"] + r["size"]
    print("    $%04X-$%04X %6d  (free)" % (r["code_end"], top - 1, r["free"]))
    for lo, hi, cid in r["pinned"]:
        print("    $%04X-$%04X %6d  %s" % (lo, hi - 1, hi - lo, cid))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    a = ap.parse_args()
    cfg = tomllib.load(open(os.path.join(ROOT, "budget.toml"), "rb"))
    ledger = cfg.get("ledger", [])
    reports = [bank_report("home", cfg["home"], load_syms(os.path.join(a.build, "leapc_home.sym")), ledger),
               bank_report("exrom", cfg["exrom"], load_syms(os.path.join(a.build, "leapc_exrom.sym")), ledger)]
    for r in reports:
        print_report(r)
        print()
    if ledger:
        print("Ledger:")
        for e in ledger:
            print("  %s %s %s %s %+d B: %s" % (e["id"], e["date"], e["bank"], e["component"], e["delta"],
                                              " ".join(e["reason"].split())))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(reports, f, indent=1)
    errs = [(r["bank"], e) for r in reports for e in r["errors"]]
    for bank, e in errs:
        print("BUDGET ERROR (%s): %s" % (bank, e), file=sys.stderr)
    if a.check and errs:
        return 1
    if a.check:
        print("budget check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
