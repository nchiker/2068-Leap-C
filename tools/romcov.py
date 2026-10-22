"""ROM coverage (Phase 9): which instructions of the production HOME and EXROM images the test suites execute.

`run_tests.py --coverage build/coverage.json` collects ZEsarUX's code coverage (cpu-code-coverage: the
addresses whose instructions ran, re-enabled after every snapshot load, as V2's tools/qual/qdiff.py did)
over every task, per image (lcharness.Machine.cov_harvest; in chunk 6 an address counts only where no
compiled program's region-1 code was: the EXROM's figures are conservative; the test image's runs count
where it is the production image). This tool maps those
addresses onto the listings' instructions (build/leapc_home.lst, build/leapc_exrom.lst; data, DB/DW/DC
tables and the like, are not instructions) and reports, per routine (the nearest global code label before it
in the listing)
and per source file, the instructions executed, and every routine none of whose instructions ran.

Usage: romcov.py [COVERAGE.json] [--md OUT] [--json OUT]
"""
import argparse
import collections
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
Z80 = set("""ld push pop ex exx ldi ldir ldd lddr cpi cpir cpd cpdr add adc sub sbc and or xor cp inc dec daa
cpl neg ccf scf nop halt di ei im rlca rla rrca rra rlc rl rrc rr sla sra sll sl1 srl rld rrd bit set res jp jr
djnz call ret reti retn rst in ini inir ind indr out outi otir outd otdr""".split())   # (data and macros are not)
LINE = re.compile(r"^\s*(\d+)\+*\s+([0-9A-F]{4})\s+((?:[0-9A-F]{2} ?)+)\s{2,}(.*)$")
BANKS = (("HOME", "leapc_home", 0x0000, 0x4000), ("EXROM", "leapc_exrom", 0xC000, 0xE000))


def instructions(lst, lo, hi):
    """[(address, size, file:line, text)] of the instructions in a listing within [lo, hi)."""
    files, out = [], []
    for raw in open(lst, encoding="latin-1"):
        if raw.startswith("# file opened:"):
            files.append(raw.split(":", 1)[1].strip())
            continue
        if raw.startswith("# file closed:"):
            if files:
                files.pop()
            continue
        m = LINE.match(raw.rstrip("\n"))
        if not m:
            continue
        addr = int(m.group(2), 16)
        nbytes = len(m.group(3).split())
        code = m.group(4).split(";")[0].strip()
        if not code or not lo <= addr < hi:
            continue
        code = re.sub(r"^[A-Za-z_.][A-Za-z0-9_.]*:\s*", "", code)     # a label on the same line
        op = code.split()[0].lower() if code.split() else ""
        if op not in Z80:
            continue
        out.append((addr, nbytes, "%s:%s" % (files[-1] if files else "?", m.group(1)), code))
    return out


LABEL = re.compile(r"^\s*\d+\+*\s+([0-9A-F]{4})\s+(?:(?:[0-9A-F]{2} ?)+\s+)?([A-Za-z_][A-Za-z0-9_]*):")


def labels(lst, lo, hi):
    """Sorted [(address, name)] of the global code labels (`NAME:` in the listing; no local '.', no EQU
    constants) in [lo, hi)."""
    out = []
    for raw in open(lst, encoding="latin-1"):
        m = LABEL.match(raw)
        if m and lo <= int(m.group(1), 16) < hi and not re.search(r":\s+EQU\b", raw, re.I):
            out.append((int(m.group(1), 16), m.group(2)))
    return sorted(set(out))


def report(executed, build=BUILD):
    banks = {}
    for bank, base, lo, hi in BANKS:
        ins = instructions(os.path.join(build, base + ".lst"), lo, hi)
        labs = labels(os.path.join(build, base + ".lst"), lo, hi)
        routines = collections.OrderedDict()
        files = collections.OrderedDict()
        li = 0
        for addr, n, f, text in ins:
            while li + 1 < len(labs) and labs[li + 1][0] <= addr:
                li += 1
            name = labs[li][1] if labs and labs[li][0] <= addr else "?"
            hit = addr in executed
            fname = f.rsplit(":", 1)[0]
            r = routines.setdefault(name, dict(addr=labs[li][0] if labs else 0, file=fname, n=0, hit=0, missed=[]))
            r["n"] += 1
            r["hit"] += hit
            if not hit:
                r["missed"].append("$%04X %s (%s)" % (addr, text, f))
            fr = files.setdefault(fname, [0, 0])
            fr[0] += 1
            fr[1] += hit
        banks[bank] = dict(instructions=len(ins), executed=sum(r["hit"] for r in routines.values()),
                           routines=routines, files=files)
    return banks


def markdown(banks, title="ROM coverage"):
    out = ["# %s (Phase 9, tools/romcov.py)" % title, ""]
    out += ["| Image | Instructions | Executed | % | Routines | Routines entered | Routines never entered |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for bank, b in banks.items():
        rs = b["routines"].values()
        out.append("| %s | %d | %d | %.1f | %d | %d | %d |" % (
            bank, b["instructions"], b["executed"], 100.0 * b["executed"] / max(1, b["instructions"]), len(b["routines"]),
            sum(1 for r in rs if r["hit"]), sum(1 for r in rs if not r["hit"])))
    for bank, b in banks.items():
        out += ["", "## %s: by source file" % bank, "", "| File | Instructions | Executed | % |", "|---|---:|---:|---:|"]
        for f, (n, h) in b["files"].items():
            out.append("| `%s` | %d | %d | %.1f |" % (f, n, h, 100.0 * h / n))
        never = [(name, r) for name, r in b["routines"].items() if not r["hit"]]
        out += ["", "## %s: routines never entered (%d)" % (bank, len(never)), ""]
        out += ["- `%s` ($%04X, %s, %d instructions)" % (name, r["addr"], r["file"], r["n"]) for name, r in never] or ["(none)"]
        part = [(name, r) for name, r in b["routines"].items() if r["hit"] and r["hit"] < r["n"]]
        out += ["", "## %s: routines entered with instructions not executed (%d)" % (bank, len(part)), ""]
        out += ["- `%s`: %d of %d executed; not: %s" % (name, r["hit"], r["n"], "; ".join(r["missed"][:6]) +
                                                         (" ..." if len(r["missed"]) > 6 else ""))
                for name, r in part]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("coverage", nargs="?", default=os.path.join(BUILD, "coverage.json"))
    ap.add_argument("--md", default=os.path.join(BUILD, "romcov.md"))
    ap.add_argument("--json", default=os.path.join(BUILD, "romcov.json"))
    a = ap.parse_args()
    cov = json.load(open(a.coverage))
    executed = set(cov.get("production", []))
    # the test image (-DLEAPC_TEST: the lexer suite) is the production image up to LEAPC_HOME_CODE_END, and
    # its EXROM is the production EXROM (tools/check_test_image.py, make check): its runs count there too
    same_end = [a for n, a in labels(os.path.join(BUILD, "leapc_home.lst"), 0, 0x4000) if n == "LEAPC_HOME_CODE_END"]
    same_end = same_end[0] if same_end else int(re.search(r"LEAPC_HOME_CODE_END: EQU 0x([0-9A-F]+)",
                                                            open(os.path.join(BUILD, "leapc_home.sym")).read()).group(1), 16)
    executed |= {x for x in cov.get("test", []) if x < same_end or 0xC000 <= x < 0xE000}
    banks = report(executed)
    open(a.md, "w").write(markdown(banks))
    json.dump(banks, open(a.json, "w"), indent=1)
    for bank, b in banks.items():
        rs = b["routines"].values()
        print("romcov: %s %d/%d instructions executed (%.1f%%); %d/%d routines entered" % (
            bank, b["executed"], b["instructions"], 100.0 * b["executed"] / max(1, b["instructions"]),
            sum(1 for r in rs if r["hit"]), len(b["routines"])))
    print("romcov: %s" % a.md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
