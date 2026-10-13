"""Leap-C executable tests (project_plan.md M1.3): compile a C program on the ROM and run it.

A case is a C file (tests/expr/**, tests/golden/**, ...). The production ROM compiles it
(CC_PROGRAM, chunk 6 paged out) and, if that succeeds, runs it (RT_RUN: main's exit value in HL,
the runtime error in A). Nothing in the ROM is test-only.

Expectation lines (`//` comments in the case):
  // expect: exit N                main returns N (compared modulo 65536; N may be negative)
  // expect: error E_NAME LINE     the compile stops with this error at this line
  // expect: rterror N             the program ends with runtime error N (spec.md 5.9)
  // mem: NAME[+OFF] HEX           after the run, the global object NAME (from byte OFF) holds
                                   exactly these bytes
  // golden: NAME HEX              the code of function NAME is exactly these bytes (`..`: any
                                   byte; {SYM}: a ROM symbol's address; {&g}: the address of the
                                   program's global or function g); the next byte must be the next
                                   function's or the code's end unless the HEX ends with `+`
  // region: NAME N                the global object or function NAME lies in image region N
                                   (1 $C000-$DFFF, 2 $E000-$F17F, 3 $F400-$F7FF, 4 $6000-$77FF)
  // maxi: N                       instruction budget of the run (default 20,000,000)
  // noaudit                       do not stop at every LEAVE (deep recursion)
  // rundepth: 1                   run with the EXROM paged in (as from the shell); the paging
                                   depth must be 1 again afterwards

Audit (every run unless `noaudit`): a breakpoint at RST LEAVE checks at each function return
that SP is exactly at the function's frame (IX - n: no temporaries left, every pushed argument
popped by its caller), and one after main's return checks that IX is the caller's again and SP
is back where the run started.
"""
import os
import re
import struct

import c2src
from decltest import Mem, chain, ER, ER_NAME

SENTINEL_IX = 0x5A5A
REGIONS = ((0xC000, 0xE000), (0xE000, 0xF180), (0xF400, 0xF800), (0x6000, 0x7800))
AUDIT_MAX = 64


def parse_case(path):
    text = open(path, encoding="latin-1").read()
    exp = []
    for l in text.split("\n"):
        s = l.strip()
        m = re.match(r"//\s*(expect|mem|golden|maxi|rundepth|region):\s*(.*)$", s) or \
            re.match(r"//\s*(noaudit)()\s*$", s)
        if m:
            exp.append((m.group(1), m.group(2).strip()))
    return text, exp


def call_to(m, routine, stops, maxi):
    """Start `routine` with SP = RET_SLOT; run to STOP_ADDR or one of `stops`. Returns the PC."""
    from lcharness import RET_SLOT, STOP_ADDR
    m.write(STOP_ADDR, b"\x18\xFE")
    m.write(RET_SLOT, struct.pack("<H", STOP_ADDR))
    m.setreg("SP", RET_SLOT)
    m.setreg("PC", m.sym(routine))
    return m.run_to([STOP_ADDR] + list(stops), maxi)


class Result:
    pass


def expand(m, ordinary, hx):
    """Golden hex with symbolic words: {SYM} = a ROM symbol's address, {&name} = a program global's
    or function's address (both little-endian)."""
    def word(name):
        if name.startswith("&"):
            e = ordinary.get(name[1:])
            v = e.val if e else 0xFFFF
        else:
            v = m.sym(name)
        return "%02x%02x" % (v & 255, v >> 8)
    return re.sub(r"\{([^}]+)\}", lambda mo: word(mo.group(1)), hx)


def compile_and_run(m, lines, maxi=20_000_000, audit=True, run=True, restore=True, depth=0):
    """restore=False: keep the machine as the previous run left it (recovery tests). depth=1: run
    with the EXROM paged in, as the shell does (RT_RUN pages it out and back)."""
    from lcharness import STOP_ADDR
    S = m.sym
    res = Result()
    res.audit = []
    if restore:
        m.restore()
    m.put_store(c2src.records(lines))
    r = m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)
    assert r["ok"], "BANK_PAGE_EXROM_OUT did not return"
    m.tstates_reset()
    pc = call_to(m, "CC_PROGRAM", [], 60_000_000)
    res.compile_ok = pc == STOP_ADDR
    res.compile_t = m.tstates()
    mem = Mem(m)
    res.errnum = mem.b(S("CC_ERRNUM"))
    res.errline = mem.w(S("CC_ERRLINE"))
    res.globals = chain(mem, mem.w(S("SYM_GLO")))
    res.code_end = mem.w(S("CG_PC"))
    res.ran = False
    if not res.compile_ok or res.errnum or not run:
        res.mem = mem
        return res
    funcs = sorted((e.val, e) for e in res.globals if e.kind == 2 and e.flags & 8)
    if depth:
        r = m.call("BANK_PAGE_EXROM_IN", maxi=100_000)
        assert r["ok"], "BANK_PAGE_EXROM_IN did not return"
    m.setreg("IX", SENTINEL_IX)
    stops = [S("RT_RUN.back")] + ([S("RST_LEAVE")] if audit else [])
    m.tstates_reset()
    pc = call_to(m, "RT_RUN", stops, maxi)
    hits = 0
    while pc != STOP_ADDR and pc in stops:
        rg = m.regs()
        if pc == S("RST_LEAVE"):
            hits += 1
            ret = m.w16(rg["SP"]) - 1         # the rst LEAVE itself
            f = [e for a, e in funcs if a <= ret]
            if f:
                fa = f[-1].val
                n = m.read(fa + 1, 1)[0]
                if rg["SP"] + 2 != (rg["IX"] - n) & 0xFFFF:
                    res.audit.append("%s: LEAVE with SP=%04X, IX=%04X, frame %d" % (f[-1].name, rg["SP"], rg["IX"], n))
            if hits >= AUDIT_MAX:
                stops = [S("RT_RUN.back")]
        else:
            if rg["IX"] != SENTINEL_IX:
                res.audit.append("IX after main %04X, expected %04X" % (rg["IX"], SENTINEL_IX))
            if rg["SP"] != m.w16(S("RUN_SP")):
                res.audit.append("SP after main %04X, RUN_SP %04X" % (rg["SP"], m.w16(S("RUN_SP"))))
            stops = [s for s in stops if s != S("RT_RUN.back")]
        m.cmd("cpu-step")
        pc = m.run_to([STOP_ADDR] + stops, maxi)
    res.run_t = m.tstates()
    res.ran = pc == STOP_ADDR
    rg = m.regs()
    res.hl = rg["HL"]
    res.a = rg["A"] if "A" in rg else (rg.get("AF", 0) >> 8)
    res.sp = rg["SP"]
    res.depth = m.read(S("BANK_EXROM_DEPTH"), 1)[0]
    res.pc = pc
    res.mem = Mem(m)
    return res


def check_case(m, path):
    text, exp = parse_case(path)
    lines = c2src.lines_of(text)
    keys = [k for k, _ in exp]
    maxi = int(dict(exp).get("maxi", "20000000").replace(",", "").replace("_", ""))
    want_err = want_exit = want_rt = None
    for k, body in exp:
        if k == "expect":
            t = body.split()
            if t[0] == "error":
                want_err = (ER[t[1]], int(t[2]))
            elif t[0] == "exit":
                want_exit = int(t[1], 0) & 0xFFFF
            elif t[0] == "rterror":
                want_rt = int(t[1], 0)
    run = want_err is None and (want_exit is not None or want_rt is not None or "mem" in keys)
    depth = int(dict(exp).get("rundepth", "0"))
    res = compile_and_run(m, lines, maxi=maxi, audit="noaudit" not in keys, run=run, depth=depth)
    msgs = []
    if not res.compile_ok:
        return False, "compile did not return", None
    got_err = (res.errnum, res.errline) if res.errnum else None
    if got_err != want_err:
        msgs.append("expected %s, compile gave %s" % (
            "error %s line %d" % (ER_NAME[want_err[0]], want_err[1]) if want_err else "no error",
            "error %s line %d" % (ER_NAME.get(got_err[0], got_err[0]), got_err[1]) if got_err else "no error"))
    ordinary = {}
    for e in res.globals:
        if e.kind < 0x10:
            ordinary.setdefault(e.name, e)
    if run and not got_err:
        if not res.ran:
            msgs.append("run did not return (PC=%04X)" % res.pc)
        else:
            if res.depth != depth:
                msgs.append("paging depth %d after the run, expected %d" % (res.depth, depth))
            if res.sp != 0xFF02:
                msgs.append("SP %04X after the run" % res.sp)
            if want_rt is not None:
                if res.a != want_rt:
                    msgs.append("expected runtime error %d, got %d" % (want_rt, res.a))
            else:
                if res.a:
                    msgs.append("runtime error %d" % res.a)
                if want_exit is not None and res.hl != want_exit:
                    msgs.append("exit %d ($%04X), expected %d ($%04X)" % (
                        res.hl - 65536 if res.hl & 0x8000 else res.hl, res.hl,
                        want_exit - 65536 if want_exit & 0x8000 else want_exit, want_exit))
            msgs += res.audit
    funcs = sorted(e.val for e in res.globals if e.kind == 2 and e.flags & 8)
    for k, body in exp:
        toks = body.split()
        if k == "mem":
            name, hx = toks[0], "".join(toks[1:])
            off = 0
            if "+" in name:
                name, o = name.split("+")
                off = int(o, 0)
            e = ordinary.get(name)
            if not e:
                msgs.append("no global %s" % name)
                continue
            want = bytes.fromhex(hx)
            got = res.mem.bytes(e.val + off, len(want))
            if got != want:
                msgs.append("%s+%d at $%04X: %s, expected %s" % (name, off, e.val + off, got.hex(), want.hex()))
        elif k == "region":
            e = ordinary.get(toks[0])
            lo, hi = REGIONS[int(toks[1]) - 1]
            if not e or not lo <= e.val < hi:
                msgs.append("%s at %s, expected region %s" % (toks[0], "$%04X" % e.val if e else None, toks[1]))
        elif k == "golden":
            name, hx = toks[0], expand(m, ordinary, "".join(toks[1:]))
            open_end = hx.endswith("+")
            hx = hx.rstrip("+")
            e = ordinary.get(name)
            if not e or e.kind != 2:
                msgs.append("no function %s" % name)
                continue
            n = len(hx) // 2
            got = res.mem.bytes(e.val, n)
            ok = all(hx[2 * i:2 * i + 2] == ".." or int(hx[2 * i:2 * i + 2], 16) == got[i] for i in range(n))
            if not ok:
                msgs.append("%s code %s, expected %s" % (name, got.hex(), hx))
            elif not open_end:
                nxt = [a for a in funcs if a > e.val]
                end = nxt[0] if nxt else res.code_end
                if end != e.val + n:
                    msgs.append("%s code is %d bytes (%s), expected %d" % (
                        name, end - e.val, res.mem.bytes(e.val, max(0, min(end - e.val, 64))).hex(), n))
    if not exp:
        msgs.append("no expectations in the case")
    info = dict(error=got_err, compile_t=res.compile_t, lines=len(lines),
                run_t=getattr(res, "run_t", None), code=res.code_end)
    return not msgs, "; ".join(msgs), info
