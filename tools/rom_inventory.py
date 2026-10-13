#!/usr/bin/env python3
"""ROM inventory: every routine, table and gap of a production image, from its assembler listing.

Read-only: it reads build/*.lst, build/*.sym, build/*.bin and budget.toml and writes only its report
(and the --json file when asked). `make inventory` runs it on the production HOME image.

For each byte of the bank up to its code end the listing says what produced it: an instruction
(code), DB/DW/DM data (data), DS fill (fill), or nothing (an ORG gap). Bytes are grouped by
top-level label (a routine or a table) and the routines by budget.toml component. A cross
reference over the operands of every assembled line (and, for HOME, the EXROM's references to the
HOME exports) gives each routine's referrers, data references (helper address tables) and EQU
aliases included; reachability from the roots (page zero, the production entries in ENTRIES, the
EXROM's references) separates routines in use from routines that nothing references yet.

Usage: rom_inventory.py [--bank home|exrom] [--md] [--json FILE]
"""
import argparse
import json
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINE_RE = re.compile(r"^\s*(\d+)(\+*)\s*([0-9A-F]{4})(.*)$")
LABEL_RE = re.compile(r"^([A-Za-z_][\w]*|\.[\w]+)\s*(:|\s|$)")
IDENT_RE = re.compile(r"[A-Za-z_][\w.]*")
DATA_OPS = {"DB", "DEFB", "BYTE", "DM", "DEFM", "DZ", "DC", "ABYTE", "DW", "DEFW", "WORD", "DEFD"}
FILL_OPS = {"DS", "DEFS", "BLOCK"}
NOT_LABEL = {"EQU", "DEFL", "=", "MACRO"}
END_OPS = re.compile(r"^(ret|reti|retn|halt)\s*$|^(jp|jr)\s+(?![a-z]{1,2}\s*,)|^(jp\s+\((hl|ix|iy)\))", re.I)


def load_syms(path):
    syms = {}
    for line in open(path):
        m = re.match(r"([A-Za-z_][\w.]*):\s+EQU\s+0x([0-9A-F]+)", line)
        if m:
            syms[m.group(1)] = int(m.group(2), 16)
    return syms


def strip_comment(text):
    out, q = [], None
    for ch in text:
        if q:
            out.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            # `af'` is a register, not a quote
            if ch == "'" and out and "".join(out).rstrip().lower().endswith("af"):
                out.append(ch)
                continue
            q = ch
            out.append(ch)
        elif ch == ";":
            break
        else:
            out.append(ch)
    return "".join(out)


def parse_listing(path, lo, hi):
    """Rows (addr, size, kind, statement) for the bytes in [lo, hi), and the label definitions."""
    raw = []
    for line in open(path, encoding="latin-1"):
        m = LINE_RE.match(line.rstrip("\n"))
        if not m:
            continue
        num, addr, rest = int(m.group(1)), int(m.group(3), 16), m.group(4)
        skipped = rest.startswith(" ~")
        field, src = rest[:14], rest[14:]
        raw.append([num, addr, skipped, field, src])
    rows, labels, last_src = [], [], {}
    parent = None
    for i, (num, addr, skipped, field, src) in enumerate(raw):
        if skipped:
            continue
        hexb = re.findall(r"\b[0-9A-F]{2}\b", field)
        if src.strip() == "" and hexb and num in last_src:
            src_eff = last_src[num]          # a continuation row of a long DB
        else:
            src_eff = src
            last_src[num] = src
        stmt = strip_comment(src_eff)
        lm = LABEL_RE.match(stmt)
        if lm:
            name = lm.group(1)
            after = stmt[lm.end(1):].lstrip(": \t").split()
            if not (after and after[0].upper() in NOT_LABEL) and name.upper() not in DATA_OPS | FILL_OPS:
                if src == src_eff:           # (a continuation row repeats its line's label)
                    if name.startswith("."):
                        label = "%s%s" % (parent, name) if parent else name
                    else:
                        label = name
                        parent = name
                    if lo <= addr < hi:
                        labels.append((addr, label))
                stmt = stmt[lm.end(1):].lstrip(": \t")
        if not hexb or not (lo <= addr < hi):
            continue
        if "..." in field:
            nxt = next((r[1] for r in raw[i + 1:] if not r[2]), addr)
            size = nxt - addr
        else:
            size = len(hexb)
        op = stmt.strip().split()[0].upper() if stmt.strip() else ""
        kind = "data" if op in DATA_OPS else "fill" if op in FILL_OPS else "code"
        rows.append((addr, size, kind, stmt.strip()))
    return rows, labels


# fixed vectors without a label in the source
VECTORS = {"home": {0x0038: "(IM 1 vector)", 0x0066: "(NMI vector)"}}
# production entry points called by the shell (Phase 6) and today by the test harness
ENTRIES = {"home": ["CC_PROGRAM", "RT_RUN"], "exrom": ["COMP_XSHELL_BEGIN", "COMP_XCOMP_ENTRY"]}


class Bank:
    def __init__(self, name, cfg, lst, sym, binf, base):
        self.name, self.cfg, self.base = name, cfg, base
        self.syms = load_syms(sym)
        self.end = self.syms[cfg["code_end"]]
        self.size = cfg["size"]
        self.image = open(binf, "rb").read()
        self.rows, labels = parse_listing(lst, base, base + self.size)
        # the routine's name is the last label defined at its address (a table's `_END:` label is
        # followed by the next routine's), COMP_ markers only where nothing else starts there
        tops = {}
        for addr, lab in labels:
            if "." in lab:
                continue
            if addr in tops and lab.startswith("COMP_") and not tops[addr].startswith("COMP_"):
                continue
            tops[addr] = lab
        for addr, lab in VECTORS.get(name, {}).items():
            tops[addr] = lab
            labels.append((addr, lab))
        # an ORG gap (padding before a fixed vector) is an item of its own
        listed = set()
        for raddr, rsize, _, _ in self.rows:
            listed.update(range(raddr, raddr + rsize))
        for a in range(base + 1, self.end):
            if a not in listed and (a - 1) in listed:
                tops[a] = "(padding)"
            elif a in listed and (a - 1) not in listed and a not in tops:
                tops[a] = "(after padding)"
        self.alias = {}           # address -> every top-level name defined there
        for addr, lab in labels:
            if "." not in lab:
                self.alias.setdefault(addr, []).append(lab)
        self.starts = sorted(a for a in tops if a < self.end)
        self.top = {a: tops[a] for a in self.starts}
        self.name_addr = {}
        for addr, lab in labels:
            self.name_addr[lab] = addr
        self.equ_alias = {}
        for line in open(lst, encoding="latin-1"):
            m = LINE_RE.match(line.rstrip("\n"))
            if m and not m.group(4).startswith(" ~"):
                e = re.match(r"^([A-Za-z_]\w*)\s+EQU\s+([A-Za-z_]\w*)\s*(;|$)", m.group(4)[14:])
                if e:
                    self.equ_alias[e.group(1)] = e.group(2)
        self.bytekind = {}
        for addr, size, kind, _ in self.rows:
            for a in range(addr, addr + size):
                self.bytekind[a] = kind
        self.comps = []
        for c in cfg["component"]:
            ranges = [(self.syms[a], self.syms[b]) for a, b in c.get("ranges", [])]
            self.comps.append((c["id"], c["title"], ranges))

    def owner(self, addr):
        lo, hi = 0, len(self.starts) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.starts[mid] <= addr:
                best, lo = self.starts[mid], mid + 1
            else:
                hi = mid - 1
        return best

    def comp_of(self, addr):
        for cid, _, ranges in self.comps:
            for a, b in ranges:
                if a <= addr < b:
                    return cid
        return None

    def routines(self):
        out = []
        for i, a in enumerate(self.starts):
            b = self.starts[i + 1] if i + 1 < len(self.starts) else self.end
            # a component boundary inside the span ends the routine there
            for _, _, ranges in self.comps:
                for ra, rb in ranges:
                    if a < ra < b:
                        b = ra
                    if a < rb < b:
                        b = rb
            kinds = {"code": 0, "data": 0, "fill": 0, "gap": 0}
            for x in range(a, b):
                kinds[self.bytekind.get(x, "gap")] += 1
            out.append({"name": self.top[a], "start": a, "end": b, "size": b - a,
                        "comp": self.comp_of(a), **kinds,
                        "aliases": [n for n in self.alias.get(a, []) if n != self.top[a]]})
        return out


def xref(bank):
    """Edges caller-routine -> callee-routine from operands (code and data), plus fall-through."""
    names = {}
    for lab, addr in bank.name_addr.items():
        if bank.base <= addr < bank.end:
            names[lab] = bank.owner(addr)
    # EQU aliases of labels (NAME EQU LABEL) count as the label
    for alias, target in bank.equ_alias.items():
        if target in names:
            names[alias] = names[target]
    edges = {}
    def add(src, dst):
        if src is None or dst is None or src == dst:
            return
        edges.setdefault(dst, set()).add(src)
    rows = sorted(bank.rows)
    for addr, size, kind, stmt in rows:
        if kind == "fill":
            continue
        src = bank.owner(addr)
        parts = stmt.split(None, 1)
        operands = parts[1] if len(parts) > 1 else ""
        for ident in IDENT_RE.findall(re.sub(r'"[^"]*"', "", operands)):
            if ident.startswith("."):
                continue
            if ident in names:
                add(src, names[ident])
    # fall-through: a routine whose last code row is not an unconditional transfer runs into the next
    last = {}
    for addr, size, kind, stmt in rows:
        if addr < bank.end:
            last[bank.owner(addr)] = (kind, stmt)
    for i, a in enumerate(bank.starts[:-1]):
        k = last.get(a)
        # (a one-byte DB at the end is a skip opcode: `DB $21` hides the next entry's `ld a,n`)
        skip = k and k[0] == "data" and re.match(r"^(DB|DEFB)\s+\$(01|11|21|3E|06|0E|16|1E|26|2E)\s*$",
                                                  k[1].strip(), re.I)
        if k and (skip or k[0] == "code" and not END_OPS.match(k[1].strip())):
            add(a, bank.starts[i + 1])
    return edges


def exrom_refs_to_home(home, exrom_lst, exports):
    """(exrom-label, home-name) for every EXROM operand naming a HOME export or a KTAB alias of one."""
    alias = {}
    for line in open(exrom_lst, encoding="latin-1"):
        m = re.search(r"^\s*\d+\+*\s*[0-9A-F]{4}\s{10,}(KTAB_\w+)\s+EQU\s+(\w+)", line)
        if m:
            alias[m.group(1)] = m.group(2)
    rows, labels = parse_listing(exrom_lst, 0xC000, 0xE000)
    starts = sorted((a, l) for a, l in labels if "." not in l)
    out = []
    for addr, size, kind, stmt in rows:
        parts = stmt.split(None, 1)
        if len(parts) < 2:
            continue
        own = None
        for a, l in starts:
            if a <= addr:
                own = l
            else:
                break
        for ident in IDENT_RE.findall(parts[1]):
            ident = alias.get(ident, ident)
            if ident in exports:
                out.append(("EXROM:" + (own or "?"), ident))
    return out


def reach(edges_by_callee, roots, starts):
    callees = {}
    for dst, srcs in edges_by_callee.items():
        for s in srcs:
            callees.setdefault(s, set()).add(dst)
    seen, todo = set(), list(roots)
    while todo:
        x = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        todo.extend(callees.get(x, ()))
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bank", default="home", choices=["home", "exrom"])
    ap.add_argument("--md", action="store_true", help="markdown tables")
    ap.add_argument("--json", help="write the inventory as JSON")
    args = ap.parse_args()
    cfg = tomllib.load(open(os.path.join(ROOT, "budget.toml"), "rb"))
    b = os.path.join(ROOT, "build")
    if args.bank == "home":
        bank = Bank("home", cfg["home"], b + "/leapc_home.lst", b + "/leapc_home.sym",
                    b + "/leapc_home.bin", 0)
    else:
        bank = Bank("exrom", cfg["exrom"], b + "/leapc_exrom.lst", b + "/leapc_exrom.sym",
                    b + "/leapc_exrom.bin", 0xC000)
    routines = bank.routines()
    by_start = {r["start"]: r for r in routines}

    # ---- reconciliation
    total = {"code": 0, "data": 0, "fill": 0, "gap": 0}
    for r in routines:
        for k in total:
            total[k] += r[k]
    used = bank.end - bank.base
    tail = bank.image[used:]
    tail_ff = all(x == 0xFF for x in tail)
    gaps = []
    a = bank.base
    while a < bank.end:
        if bank.bytekind.get(a) is None:
            s = a
            while a < bank.end and bank.bytekind.get(a) is None:
                a += 1
            gaps.append((s, a - s, bank.image[s - bank.base:a - bank.base]))
        else:
            a += 1
    fills = [(addr, size, stmt) for addr, size, kind, stmt in bank.rows if kind == "fill" and addr < bank.end]
    comp_sum = {}
    for r in routines:
        comp_sum[r["comp"]] = comp_sum.get(r["comp"], 0) + r["size"]

    # ---- references and reachability
    extra = []
    if bank.name == "home":
        exports = set(l.strip() for l in open(os.path.join(ROOT, "src/rom/home_exports.txt")) if l.strip())
        ext = exrom_refs_to_home(bank, b + "/leapc_exrom.lst", exports)
    else:
        ext = []
    edges = xref(bank)
    ext_by = {}
    for src, name in ext:
        dst = bank.owner(bank.name_addr[name])
        ext_by.setdefault(dst, set()).add(src)
    page0 = [r["start"] for r in routines if r["comp"] == "page0"]
    entries = [bank.name_addr[n] for n in ENTRIES[bank.name] if n in bank.name_addr]
    roots_now = set(page0) | set(ext_by) | set(entries)
    live = reach(edges, roots_now, bank.starts)
    for r in routines:
        refs = sorted(by_start[s]["name"] for s in edges.get(r["start"], ()) if s in by_start)
        r["refs_rom"] = refs
        r["refs_exrom"] = sorted(ext_by.get(r["start"], ()))
        r["reachable"] = r["start"] in live
        r["kind"] = ("padding" if r["gap"] == r["size"] else
                     "table" if r["code"] == 0 and r["data"] > 0 else
                     "code+data" if r["code"] and r["data"] else
                     "fill" if r["code"] == 0 and r["data"] == 0 and r["fill"] else "code")

    report = {"bank": bank.name, "base": bank.base, "size": bank.size, "code_end": bank.end,
              "used": used, "free": bank.size - used, "tail_all_ff": tail_ff, "bytes": total,
              "gaps": [(s, n, d.hex()) for s, n, d in gaps], "fills": fills,
              "components": comp_sum, "routines": routines}
    if args.json:
        json.dump(report, open(args.json, "w"), indent=1, default=list)

    out = sys.stdout
    if not args.md:
        print("%s: used %d B ($%04X-$%04X), free %d B, after code end all $FF: %s" %
              (bank.name.upper(), used, bank.base, bank.end - 1, bank.size - used, tail_ff))
        print("  bytes: code %(code)d, data %(data)d, DS fill %(fill)d, ORG gaps %(gap)d" % total)
        for s, n, d in gaps:
            print("  gap $%04X %d B: %s" % (s, n, d.hex()))
        for addr, size, stmt in fills:
            print("  fill $%04X %d B: %s" % (addr, size, stmt))
        for cid, title, ranges in bank.comps:
            rs = [r for r in routines if r["comp"] == cid]
            if not rs:
                continue
            print("\n[%s] %d B" % (cid, sum(r["size"] for r in rs)))
            for r in rs:
                refs = r["refs_rom"] + r["refs_exrom"]
                print("  $%04X %5d %-9s %-3s %-34s <- %s" % (
                    r["start"], r["size"], r["kind"], "" if r["reachable"] else "UNR", r["name"],
                    ", ".join(refs[:6]) + (" +%d" % (len(refs) - 6) if len(refs) > 6 else "")))
        unc = [r for r in routines if r["comp"] is None]
        if unc:
            print("\nunaccounted:", unc)
        return
    for cid, title, ranges in bank.comps:
        rs = [r for r in routines if r["comp"] == cid]
        if not rs:
            continue
        out.write("\n#### `%s` — %s: %d B\n\n" % (cid, title, sum(r["size"] for r in rs)))
        out.write("| Address | Bytes | Routine | Kind | Code/data | Referenced by |\n|---|---:|---|---|---|---|\n")
        for r in rs:
            refs = r["refs_rom"] + r["refs_exrom"]
            reftxt = ", ".join("`%s`" % x for x in refs[:5]) + (" +%d" % (len(refs) - 5) if len(refs) > 5 else "")
            if not refs:
                reftxt = "—"
            cd = "%d/%d" % (r["code"], r["data"]) + (" +%d fill" % r["fill"] if r["fill"] else "") + \
                 (" +%d gap" % r["gap"] if r["gap"] else "")
            out.write("| `$%04X` | %d | `%s`%s | %s%s | %s | %s |\n" % (
                r["start"], r["size"], r["name"],
                "" if not r["aliases"] else " (= " + ", ".join("`%s`" % x for x in r["aliases"]) + ")",
                r["kind"], "" if r["reachable"] else ", **unreferenced**", cd, reftxt))


if __name__ == "__main__":
    main()
