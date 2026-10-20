#!/usr/bin/env python3
"""Leap-C RAM layout guard (project_plan.md section 6, Phase 4; modelled on V2's
tools/check_ram_layout.py, copied idea, not code).

A static census of every RAM address the production ROMs reference, proved against the map of
include/leapc_layout.inc (spec.md 3.1). A name counts as referenced when it appears in an emitted
code or data line of build/leapc_home.lst ($0000-$3FFF) or build/leapc_exrom.lst ($C000-$DFFF), or
in the definition of such a name (EQU closure). Every referenced name whose value is a RAM address
($4000-$FFFF) must be one of:
  - a platform system variable or a Leap-C cell: $5B00 .. LEAPC_CELLS_END (below LEAPC_CELLS_LIMIT);
  - a display-file-1 address (screen and attribute constants): $4000-$5AFF;
  - one of the V2 platform cells Leap-C keeps at its V2 address in $F180-$F3FF (PLATFORM_CELLS);
  - a layout boundary (BOUNDARIES: the region symbols of leapc_layout.inc and the platform names
    defined from them), or a value that is not an address (VALUES);
  - a label of the EXROM image (EXROM code and tables, chunk 6 while paged in).
Anything else -- a cell in the source region, an image region, the stack, $FF00-$FFFF, a V2 cell
Leap-C has no use for -- is an error. The tool also checks the map itself (the regions tile RAM,
the cells end below the limit, the compiler's region table in the ROM equals the map) and that no
Leap-C source (src/, include/ except leapc_layout.inc) uses a literal RAM address.

--negative assembles the HOME image with each negative control of src/test/layout_negctl.asm
(-DLEAPC_NEGCTL=n: a deliberately misplaced cell) and requires the census to report each one.

Usage: check_ram_layout.py [--build DIR] [--negative] [--quiet]
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINE = re.compile(r"^\s*\d+\+*\s+([0-9A-F]{4})\s?(~?)\s*((?:[0-9A-F]{2} )*)\s*(.*)$")
IDENT = re.compile(r"[A-Za-z_.][A-Za-z0-9_.]*")
EQU = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_.]*):?\s+(?i:equ)\s+(.*)")

# V2 cells at their V2 addresses in $F180-$F3FF that Leap-C uses, with their sizes
PLATFORM_CELLS = {"UDG_TABLE": 168, "EDIT_LINE_BUF": 128, "GFX_LINE_X0": 1, "GFX_LINE_Y0": 1, "GFX_LINE_X1": 1,
                  "GFX_LINE_Y1": 1}
# layout boundaries: addresses that delimit regions, never cells
BOUNDARIES = {"PROG_AREA_START", "PROG_AREA_MAX", "LIB_HEAP_END", "SECOND_DISPLAY_ADDR", "CC_STACK_FLOOR",
              "LEAPC_EXROM_SHELL", "LEAPC_EXROM_FOLD", "LEAPC_EXROM_LIBFIND", "LEAPC_EXROM_BEEP",
              "LEAPC_EXROM_BASE", "LEAPC_EXROM_END"}
# values that are not addresses
VALUES = {"V2_FORMAT_WORD", "PKG_ABI_WORD", "LEAPC_TAPE_VERSION"}
LITERAL_VALUES = {0x8000, 0xFFFF}          # the heap's in-use bit (RT_RUN), all-ones sentinels


def symbols(path):
    out = {}
    for line in open(path):
        m = re.match(r"(\S+?):\s+EQU\s+0x([0-9A-Fa-f]+)", line)
        if m:
            out.setdefault(m.group(1), int(m.group(2), 16))
    return out


def census(listing, lo, hi):
    """(referenced names with the first address that uses them, EQU-defined names)"""
    used, deps, equs = {}, {}, set()
    for raw in open(listing, errors="replace"):
        m = LINE.match(raw)
        if not m or m.group(2):
            continue
        addr, code = int(m.group(1), 16), m.group(4).split(";", 1)[0]
        d = EQU.match(code)
        if d:
            equs.add(d.group(1))
            deps.setdefault(d.group(1), set()).update(IDENT.findall(d.group(2)))
            continue
        if m.group(3).strip() and lo <= addr < hi:
            for t in IDENT.findall(re.sub(r"^\s*[A-Za-z_.][A-Za-z0-9_.]*:", "", code)):
                used.setdefault(t, addr)
    work = list(used)
    while work:
        n = work.pop()
        for t in deps.get(n, ()):
            if t not in used:
                used[t] = used[n]
                work.append(t)
    return used, equs


def literals():
    """Literal RAM addresses in the Leap-C sources (spec.md 3.1: symbols only)."""
    errs = []
    files = [os.path.join(d, f) for d in ("src/compiler", "src/runtime", "src/shell", "src/rom")
             for f in sorted(os.listdir(os.path.join(ROOT, d))) if f.endswith(".asm")]
    files += ["include/" + f for f in ("leapc_cells.inc", "leapc_rom.inc", "leapc_decl.inc", "leapc_tokens.inc",
                                       "leapc_errors.inc")]
    num = r"(\$[0-9A-Fa-f]{4}|0x[0-9A-Fa-f]{4}|\b[1-9][0-9]{4}\b)"
    for f in files:
        for i, line in enumerate(open(os.path.join(ROOT, f)), 1):
            code = line.split(";", 1)[0]
            if re.match(r"\s*([A-Za-z_][A-Za-z0-9_.]*:?\s+)?(?i:equ|assert|org|ds|defs|db|dw|savebin|device)\b", code) \
                    or not code.strip():
                continue
            for mm in re.finditer(num, code):
                t = mm.group(1)
                v = int(t[1:], 16) if t[0] == "$" else int(t, 0)
                if v >= 0x4000 and v not in LITERAL_VALUES:
                    errs.append("%s:%d: literal RAM address %s" % (f, i, t))
    return errs


def check(build, quiet=False):
    S = symbols(os.path.join(build, "leapc_home.sym"))
    X = symbols(os.path.join(build, "leapc_exrom.sym"))
    errors = []
    # ---- the map itself
    g = lambda n: S[n]
    tiles = [("display file 1", 0x4000, g("LEAPC_SYSVARS_BASE")),
             ("system variables", g("LEAPC_SYSVARS_BASE"), g("LEAPC_SYSVARS_END")),
             ("Leap-C cells", g("LEAPC_CELLS_BASE"), g("LEAPC_CELLS_LIMIT")),
             ("image region 4", g("LEAPC_IMG4_BASE"), g("LEAPC_IMG4_END")),
             ("source region", g("LEAPC_SRC_BASE"), g("LEAPC_SRC_TOP")),
             ("image region 1", g("LEAPC_IMG1_BASE"), g("LEAPC_IMG1_END")),
             ("image region 2", g("LEAPC_IMG2_BASE"), g("LEAPC_IMG2_END")),
             ("platform cells", g("LEAPC_PLAT_BASE"), g("LEAPC_PLAT_END")),
             ("image region 3", g("LEAPC_IMG3_BASE"), g("LEAPC_IMG3_END")),
             ("stack", g("LEAPC_STACK_LIMIT"), g("LEAPC_STACK_TOP")),
             ("unused top", g("LEAPC_STACK_TOP"), 0x10000)]
    for (n1, _, e1), (n2, b2, _) in zip(tiles, tiles[1:]):
        if e1 != b2:
            errors.append("the map: %s ends at $%04X, %s starts at $%04X" % (n1, e1, n2, b2))
    if g("LEAPC_CELLS_END") > g("LEAPC_CELLS_LIMIT"):
        errors.append("the Leap-C cells end at $%04X, beyond $%04X" % (g("LEAPC_CELLS_END"), g("LEAPC_CELLS_LIMIT")))
    for n, v in (("PROG_AREA_START", g("LEAPC_SRC_BASE")), ("PROG_AREA_MAX", g("LEAPC_SRC_TOP")),
                 ("LIB_HEAP_END", g("LEAPC_SRC_TOP") - 2), ("SECOND_DISPLAY_ADDR", g("LEAPC_IMG4_BASE"))):
        if S[n] != v:
            errors.append("%s is $%04X, the map needs $%04X" % (n, S[n], v))
    rom = open(os.path.join(build, "leapc_home.bin"), "rb").read()
    t = g("IMG_TABLE")
    want = [g("LEAPC_IMG%d_%s" % (k, e)) for k in (1, 2, 3, 4) for e in ("BASE", "END")] + [g("LEAPC_SRC_TOP")]
    got = [rom[t + 2 * i] | rom[t + 2 * i + 1] << 8 for i in range(9)]
    if got != want:
        errors.append("the compiler's region table (IMG_TABLE) differs from the map: %s" % got)
    # ---- the census
    rows = []
    for name, listing, lo, hi, own in (("HOME", "leapc_home.lst", 0, 0x4000, S),
                                        ("EXROM", "leapc_exrom.lst", 0xC000, 0xE000, X)):
        used, equs = census(os.path.join(build, listing), lo, hi)
        for n, at in sorted(used.items()):
            v = own.get(n, S.get(n, X.get(n)))
            if v is None or v < 0x4000:
                continue
            if n in VALUES or n in BOUNDARIES or n.startswith("LEAPC_"):
                kind = "boundary or value"
            elif n not in equs and 0xC000 <= v < 0xE000 and n in X and n not in S:
                kind = "EXROM label"
            elif 0x4000 <= v < g("LEAPC_SYSVARS_BASE"):
                kind = "display file 1"
            elif g("LEAPC_SYSVARS_BASE") <= v < g("LEAPC_CELLS_END"):
                kind = "cell"
            elif any(S[c] <= v < S[c] + k for c, k in PLATFORM_CELLS.items()):
                kind = "platform cell"                   # (or a V2 alias of one: EXTENSION_ARG0 = GFX_LINE_X0)
            else:
                where = next((tn for tn, a, b in tiles if a <= v < b), "?")
                errors.append("%s code at $%04X references %s = $%04X in the %s" % (name, at, n, v, where))
                continue
            rows.append((name, n, v, kind))
    # the platform cells Leap-C keeps lie in the platform area and do not overlap each other
    pc = sorted((S[n], S[n] + k, n) for n, k in PLATFORM_CELLS.items())
    for a, e, n in pc:
        if not g("LEAPC_PLAT_BASE") <= a < e <= g("LEAPC_PLAT_END"):
            errors.append("platform cell %s ($%04X-$%04X) is outside $F180-$F3FF" % (n, a, e - 1))
    for (a1, e1, n1), (a2, _, n2) in zip(pc, pc[1:]):
        if a2 < e1:
            errors.append("platform cells %s and %s overlap" % (n1, n2))
    errors += literals()
    if errors:
        for e in errors if not quiet else ():
            print("check_ram_layout: " + e, file=sys.stderr)
        return 1, errors
    if not quiet:
        kinds = {}
        for _, _, _, k in rows:
            kinds[k] = kinds.get(k, 0) + 1
        print("check_ram_layout: OK: %d referenced RAM names (%s); map tiles $4000-$FFFF; cells end $%04X of $%04X; "
              "no literal RAM addresses" % (len(rows), ", ".join("%d %s" % (v, k) for k, v in sorted(kinds.items())),
                                            g("LEAPC_CELLS_END"), g("LEAPC_CELLS_LIMIT")))
    return 0, []


def negative():
    """Each negative control must be reported (project_plan.md section 6)."""
    src = open(os.path.join(ROOT, "src", "test", "layout_negctl.asm")).read()
    ids = sorted(set(int(x) for x in re.findall(r"LEAPC_NEGCTL\s*==\s*(\d+)", src)))
    expect = dict((int(a), b) for a, b in re.findall(r";\s*control (\d+): expect `([^`]+)`", src))
    bad = []
    for k in ids:
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run(["sjasmplus", "--nologo", "--msg=war", "--inc=.", "--inc=platform",
                                "-DLEAPC_NEGCTL=%d" % k, "--sym=%s/leapc_home.sym" % t, "--lst=%s/leapc_home.lst" % t,
                                "src/rom/home.asm"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                bad.append("control %d does not assemble: %s" % (k, (r.stdout + r.stderr)[-300:]))
                continue
            # the production bytes are unchanged (the control is appended): the image is production's
            for f in ("leapc_exrom.sym", "leapc_exrom.lst", "leapc_home.bin"):
                os.symlink(os.path.join(ROOT, "build", f), os.path.join(t, f))
            code, errs = check(t, quiet=True)
            hit = [e for e in errs if expect.get(k, "\0") in e]
            if code == 0 or not hit:
                bad.append("control %d (%s) was not reported: %s" % (k, expect.get(k), errs))
            else:
                print("check_ram_layout: negative control %d reported: %s" % (k, hit[0]))
    for b in bad:
        print("check_ram_layout: NEGATIVE CONTROL FAILED: " + b, file=sys.stderr)
    if not bad:
        print("check_ram_layout: all %d negative controls reported" % len(ids))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.negative:
        return negative()
    return check(a.build, a.quiet)[0]


if __name__ == "__main__":
    sys.exit(main())
