"""Leap-C declaration tests (project_plan.md M1.2): decode the compiler's workspace and check it.

A case is a C file in tests/decl/**. The production ROM compiles it (CC_COMPILE, chunk 6 paged
out); the harness then reads the compile workspace (symbol entries, type nodes: layout in
include/leapc_decl.inc) and the image regions straight from RAM. Block and prototype scopes are
captured at every SCOPE_CLOSE (a breakpoint): the closing scope's entries, before they are
reclaimed. Nothing in the ROM is test-only.

Expectation lines (any number; `//` comments in the case):
  // expect: error E_NAME LINE        the compile stops with this error at this line
  // sym: NAME KIND TYPE [key=value]   a file-scope entry. KIND: obj func typedef enumc
  // local: NAME[#k] KIND TYPE [key=value]   the k-th (default 1st) captured block/prototype-scope
                                        entry with this name (scopes in closing order, entries in
                                        declaration order)
  // tag: NAME struct|enum [size=N] [members=a@0:int,b@2:*char]   a file-scope tag
  // nosym: NAME                       no file-scope ordinary identifier NAME
  // data: NAME HEX                    the object's static storage holds exactly these bytes
  // addr: NAME 0xADDR                 the object's static storage address
  // frame: N                          FRAME_MAX after the compile (the last function's frame)
  // prefill: HH                       fill chunk 6 with byte HH before the compile
  keys: size=N (object size), val=N (address, frame offset, argument offset, enum value),
        flags=a,b (exactly these SF_ flags: static extern const defined auto param enum noaddr;
        `flags=` for none), count=N (struct member count)
TYPE notation: void char schar int uint, *T (pointer), [N]T or []T (array), fn(T,T)R, fn()R
(a `(void)` prototype), fn(?)R (no prototype), struct NAME (tagged) or struct{a:T,b:T}.
"""
import os
import re

import c2src

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = {0: "void", 1: "char", 2: "schar", 3: "int", 4: "uint", 5: "float"}
KINDS = {1: "obj", 2: "func", 3: "typedef", 4: "enumc", 0x10: "tag", 0x20: "member", 0x30: "label"}
FLAGS = ["static", "extern", "const", "defined", "auto", "param", "enum", "noaddr"]
NODE_H = 0x40


def _equs(path):
    out = {}
    for line in open(path):
        m = re.match(r"\s*([A-Z_0-9]+)\s+EQU\s+(\$?[0-9A-Fa-f]+)\b", line)
        if m:
            v = m.group(2)
            out[m.group(1)] = int(v[1:], 16) if v.startswith("$") else int(v)
    return out


ER = _equs(os.path.join(ROOT, "include", "leapc_errors.inc"))
ER_NAME = {v: k for k, v in ER.items() if k.startswith("E_")}


class Mem:
    """Cached reader of the emulated RAM (256-byte pages)."""

    def __init__(self, m):
        self.m = m
        self.pages = {}

    def b(self, a):
        p = a >> 8
        if p not in self.pages:
            self.pages[p] = self.m.read(p << 8, 256)
        return self.pages[p][a & 255]

    def w(self, a):
        return self.b(a) | self.b(a + 1) << 8

    def bytes(self, a, n):
        return bytes(self.b(a + i) for i in range(n))


class Entry:
    def __init__(self, mem, addr):
        self.addr = addr
        self.link = mem.w(addr)
        self.kind = mem.b(addr + 2)
        n = mem.b(addr + 3)
        self.flags = mem.b(addr + 4)
        self.type = mem.w(addr + 5)
        self.val = mem.w(addr + 7)
        self.name = mem.bytes(addr + 9, n).decode("latin-1")

    def flagnames(self):
        return [f for i, f in enumerate(FLAGS) if self.flags >> i & 1]


def chain(mem, head, stop=0):
    out = []
    a = head
    seen = set()
    while a and a >= stop and a not in seen and len(out) < 2000:
        seen.add(a)
        e = Entry(mem, a)
        out.append(e)
        a = e.link
    return out


class Decoder:
    def __init__(self, mem, tags):
        self.mem = mem
        self.tags = tags                    # struct node -> tag name

    def members(self, node):
        first = self.mem.w(node + 5)
        return chain(self.mem, first)

    def t(self, h, depth=0):
        if depth > 40:
            return "..."
        if h >> 8 < NODE_H:
            return "*" * (h >> 8) + BASES.get(h & 255, "?%02X" % (h & 255))
        k = self.mem.b(h)
        a = self.mem.w(h + 3)
        if k == 1:
            return "*" + self.t(a, depth + 1)
        if k == 2:
            n = self.mem.w(h + 5)
            return "[%s]" % (n if n else "") + self.t(a, depth + 1)
        if k == 3:
            n, fl = self.mem.b(h + 5), self.mem.b(h + 6)
            if not fl & 1:
                ps = "?"
            else:
                ps = ",".join(self.t(self.mem.w(h + 7 + 2 * i), depth + 1)   # stored last first
                              for i in reversed(range(n)))
            return "fn(%s)%s" % (ps, self.t(a, depth + 1))
        if k == 4:
            if h in self.tags:
                return "struct " + self.tags[h]
            if self.mem.w(h + 5) == 0:
                return "struct{?}"
            return "struct{%s}" % ",".join("%s:%s" % (m.name, self.t(m.type, depth + 1))
                                            for m in self.members(h))
        return "?node%02X" % k

    def size(self, h):
        if h >> 8 < NODE_H:
            if h >> 8:
                return 2
            return {0: None, 1: 1, 2: 1, 3: 2, 4: 2, 5: 5}.get(h & 255)
        k = self.mem.b(h)
        if k == 1:
            return 2
        if k == 2:
            n = self.mem.w(h + 5)
            es = self.size(self.mem.w(h + 3))
            return n * es if n and es else None
        if k == 4:
            return self.mem.w(h + 3) if self.mem.w(h + 5) else None
        return None


# ---------------------------------------------------------------- expectations
def parse_case(path):
    text = open(path, encoding="latin-1").read()
    exp = []
    for l in text.split("\n"):
        s = l.strip()
        m = re.match(r"//\s*(expect|sym|local|tag|nosym|data|addr|frame|prefill):\s*(.*)$", s)
        if m:
            exp.append((m.group(1), m.group(2).strip()))
    return text, exp


def kv(tokens):
    d = {}
    rest = []
    for t in tokens:
        if "=" in t:
            k, v = t.split("=", 1)
            d[k] = v
        else:
            rest.append(t)
    return rest, d


def check_entry(dec, e, kind, typ, keys):
    msgs = []
    if KINDS.get(e.kind) != kind:
        msgs.append("%s: kind %s, expected %s" % (e.name, KINDS.get(e.kind), kind))
    if typ is not None and dec.t(e.type) != typ:
        msgs.append("%s: type %s, expected %s" % (e.name, dec.t(e.type), typ))
    for k, v in keys.items():
        if k == "size":
            got = dec.size(e.type)
            if got != int(v, 0):
                msgs.append("%s: size %s, expected %s" % (e.name, got, v))
        elif k == "val":
            want = int(v, 0) & 0xFFFF
            if e.val != want:
                msgs.append("%s: value %d ($%04X), expected %s" % (e.name, e.val, e.val, v))
        elif k == "flags":
            want = sorted(f for f in v.split(",") if f)
            if sorted(e.flagnames()) != want:
                msgs.append("%s: flags %s, expected %s" % (e.name, e.flagnames(), want))
        else:
            msgs.append("bad key %s" % k)
    return msgs


class Result:
    pass


def run_compile(m, lines, capture_scopes=True, maxi=60_000_000, prefill=None):
    """Compile `lines` (list of str) on the production ROM. Returns a Result with the error, the
    global entries, the scope snapshots and a memory reader."""
    S = m.sym
    m.restore()
    m.put_store(c2src.records(lines))
    r = m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)
    assert r["ok"], "BANK_PAGE_EXROM_OUT did not return"
    if prefill is not None:                 # chunk 6 is RAM now: fill it with garbage
        m.write(0xC000, bytes([prefill]) * 0x2000)
    import struct
    from lcharness import RET_SLOT, STOP_ADDR
    m.write(STOP_ADDR, b"\x18\xFE")
    m.write(RET_SLOT, struct.pack("<H", STOP_ADDR))
    m.setreg("SP", RET_SLOT)
    m.setreg("PC", S("CC_COMPILE"))
    snaps = []
    stops = [STOP_ADDR] + ([S("SCOPE_CLOSE")] if capture_scopes else [])
    m.tstates_reset()
    t_total = 0
    res = Result()
    res.ok = False
    while True:
        pc = m.run_to(stops, maxi)
        t_total += m.tstates()
        if pc == STOP_ADDR:
            res.ok = True
            break
        if capture_scopes and pc == S("SCOPE_CLOSE"):
            mem = Mem(m)
            base = mem.w(S("SCOPE_BASE"))
            head = mem.w(S("SYM_LOC"))
            ents = list(reversed(chain(mem, head, base)))
            snaps.append(dict(entries=ents, mem=mem, frame_ofs=mem.w(S("FRAME_OFS")),
                              frame_max=mem.w(S("FRAME_MAX"))))
            m.cmd("cpu-step")
            m.tstates_reset()
            continue
        res.pc = pc
        break
    res.tstates = t_total
    mem = Mem(m)
    res.mem = mem
    res.errnum = mem.b(S("CC_ERRNUM"))
    res.errline = mem.w(S("CC_ERRLINE"))
    res.globals = chain(mem, mem.w(S("SYM_GLO")))
    res.snaps = snaps
    res.ws_glo = mem.w(S("WS_GLO"))
    res.ws_loc = mem.w(S("WS_LOC"))
    res.frame_max = mem.w(S("FRAME_MAX"))
    res.img = [(mem.w(S("IMG_LIM") + 4 * i), mem.w(S("IMG_LIM") + 4 * i + 2)) for i in range(4)]
    return res


def tag_map(res):
    tags = {}
    for e in res.globals:
        if e.kind == 0x10 and not e.flags & 0x40:
            tags.setdefault(e.type, e.name)
    for s in res.snaps:
        for e in s["entries"]:
            if e.kind == 0x10 and not e.flags & 0x40:
                tags.setdefault(e.type, e.name)
    return tags


def check_case(m, path):
    text, exp = parse_case(path)
    lines = c2src.lines_of(text)
    want_local = any(k == "local" for k, _ in exp)
    prefill = [int(b, 16) for k, b in exp if k == "prefill"]
    res = run_compile(m, lines, capture_scopes=want_local, prefill=prefill[0] if prefill else None)
    if not res.ok:
        return False, "did not return (PC=%04X)" % res.pc, None
    dec = Decoder(res.mem, tag_map(res))
    msgs = []
    err = None
    for k, body in exp:
        if k == "expect":
            t = body.split()
            if t[0] == "error":
                err = (ER[t[1]], int(t[2]))
    got_err = (res.errnum, res.errline) if res.errnum else None
    if err != got_err:
        msgs.append("expected %s, got %s" % (
            "error %s line %d" % (ER_NAME[err[0]], err[1]) if err else "no error",
            "error %s line %d" % (ER_NAME.get(got_err[0], got_err[0]), got_err[1]) if got_err else "no error"))
    ordinary = {}
    tags = {}
    for e in res.globals:                    # newest first: keep the newest per name
        if e.kind < 0x10:
            ordinary.setdefault(e.name, e)
        elif e.kind == 0x10:
            tags.setdefault(e.name, e)
    locals_ = [e for s in res.snaps for e in s["entries"]]
    for k, body in exp:
        if k in ("expect", "prefill"):
            continue
        toks = body.split()
        if k == "sym":
            rest, keys = kv(toks)
            name, kind = rest[0], rest[1]
            typ = " ".join(rest[2:]) if len(rest) > 2 else None
            e = ordinary.get(name)
            if not e:
                msgs.append("no file-scope %s" % name)
                continue
            msgs += check_entry(dec, e, kind, typ, keys)
        elif k == "local":
            rest, keys = kv(toks)
            name, kind = rest[0], rest[1]
            nth = 1
            if "#" in name:
                name, n = name.split("#")
                nth = int(n)
            typ = " ".join(rest[2:]) if len(rest) > 2 else None
            hits = [e for e in locals_ if e.name == name]
            if len(hits) < nth:
                msgs.append("no local %s#%d (captured: %s)" % (name, nth, [e.name for e in locals_]))
                continue
            msgs += check_entry(dec, hits[nth - 1], kind, typ, keys)
        elif k == "tag":
            members = None
            if "members=" in body:          # the member list may contain spaces (struct NAME)
                body, members = body.split("members=", 1)
                toks = body.split()
            rest, keys = kv(toks)
            if members is not None:
                keys["members"] = members.strip()
            name, what = rest[0], rest[1]
            e = tags.get(name)
            if not e:
                msgs.append("no tag %s" % name)
                continue
            is_enum = bool(e.flags & 0x40)
            if (what == "enum") != is_enum:
                msgs.append("tag %s: enum=%s" % (name, is_enum))
                continue
            if what == "struct":
                node = e.type
                if "size" in keys:
                    sz = res.mem.w(node + 3) if res.mem.w(node + 5) else None
                    if sz != int(keys["size"], 0):
                        msgs.append("struct %s: size %s, expected %s" % (name, sz, keys["size"]))
                mem_list = dec.members(node) if res.mem.w(node + 5) else []
                if "members" in keys:
                    got = ",".join("%s@%d:%s" % (x.name, x.val, dec.t(x.type)) for x in mem_list)
                    if got != keys["members"]:
                        msgs.append("struct %s: members %s, expected %s" % (name, got, keys["members"]))
                if "count" in keys and len(mem_list) != int(keys["count"]):
                    msgs.append("struct %s: %d members" % (name, len(mem_list)))
        elif k == "nosym":
            if toks[0] in ordinary:
                msgs.append("%s is declared" % toks[0])
        elif k == "data":
            name, hx = toks[0], "".join(toks[1:])
            e = ordinary.get(name)
            if not e:
                msgs.append("no %s" % name)
                continue
            n = dec.size(e.type)
            want = bytes.fromhex(hx)
            if n != len(want):
                msgs.append("%s: size %s, data given for %d bytes" % (name, n, len(want)))
            got = res.mem.bytes(e.val, len(want))
            if got != want:
                msgs.append("%s at $%04X: %s, expected %s" % (name, e.val, got.hex(), want.hex()))
        elif k == "addr":
            e = ordinary.get(toks[0])
            if not e or e.val != int(toks[1], 0):
                msgs.append("%s: address %s, expected %s" % (toks[0], "$%04X" % e.val if e else None, toks[1]))
        elif k == "frame":
            if res.frame_max != int(toks[0]):
                msgs.append("frame %d, expected %s" % (res.frame_max, toks[0]))
    info = dict(error=got_err, globals=len(res.globals), scopes=len(res.snaps),
                ws_global=0xC000 - res.ws_glo, tstates=res.tstates, lines=len(lines))
    if not exp:
        msgs.append("no expectations in the case")
    return not msgs, "; ".join(msgs), info
