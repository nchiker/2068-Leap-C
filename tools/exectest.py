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
Phase 3 (the library and the runtime):
  // screen: ROW TEXT              after the run, screen row ROW reads TEXT (trailing spaces
                                   ignored; characters without a glyph read as spaces)
  // keys: K K ...                 keys fed through the ISR latch (KBD_LASTK / KBD_KEYHIT) each time
                                   the program reads the keyboard (IO_READ_KEY, IO_READ_KEY_NONBLOCK):
                                   a number, "text" (its characters), ENTER, DELETE or NONE (an
                                   inkey() that finds no key)
  // rtline: N                     the runtime error's source line (RT_ERRLINE)
  // ay: R=V ...                   after the run, AY register R holds V (read back through ports)
  // attr: ROW COL V               the attribute byte of a screen cell
  // pixel: X Y V                  the pixel (X, Y from the top) is V (0 or 1) in the bitmap
  // cell: SYMBOL V                the byte at a ROM-defined RAM cell (system variable) is V
  // break: at SYMBOL [N] | after N   press BREAK (CAPS SHIFT + SPACE, held) at the N-th time the
                                   run reaches SYMBOL (default 1), or after N instructions of the
                                   run; the keys are released when the run ends
  // breakpc: LO HI                when the ISR accepted BREAK (RT_BREAKREQ), the interrupted PC was
                                   in [LO, HI) (ROM symbols or numbers): the state the case tests
  // breakdeferred                 ... and NOBRK was above 0 (the request waited for the section's end)
After every run: IX is the caller's again (a sentinel), SP is back above the return slot, and the
line store (the source) is unchanged.

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
KEY_NAMES = {"ENTER": 13, "DELETE": 8, "NONE": None}
ZKEY_CAPS, ZKEY_SPACE = 135, 128          # ZEsarUX send-keys-event codes
AY_PROBE, AY_OUT = 0xFD00, 0xFD80
REGIONS = ((0xC000, 0xE000), (0xE000, 0xF180), (0xF400, 0xF800), (0x6000, 0x7800))
AUDIT_MAX = 64


def parse_case(path):
    text = open(path, encoding="latin-1").read()
    exp = []
    for l in text.split("\n"):
        s = l.strip()
        m = re.match(r"//\s*(expect|mem|golden|maxi|rundepth|region):\s*(.*)$", s) or \
            re.match(r"//\s*(screen|keys|rtline|ay|attr|pixel|break|cell|breakpc):\s*(.*)$", s) or \
            re.match(r"//\s*(noaudit|breakdeferred)()\s*$", s)
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


def parse_keys(text):
    out = []
    for tok in re.findall(r'"[^"]*"|\S+', text):
        if tok.startswith('"'):
            out += [ord(c) for c in tok[1:-1]]
        elif tok in KEY_NAMES:
            out.append(KEY_NAMES[tok])
        else:
            out.append(int(tok, 0))
    return out


def press_break(m, down):
    for code in ((ZKEY_CAPS, ZKEY_SPACE) if down else (ZKEY_SPACE, ZKEY_CAPS)):
        m.cmd("send-keys-event %d %d" % (code, 1 if down else 0))


def ay_regs(m):
    """The 16 AY registers, read back by a probe routine run in the emulator (port $F5 selects,
    $F6 reads), as V2's AY tests do."""
    from lcharness import RET_SLOT, STOP_ADDR
    code = bytes([0x21, AY_OUT & 255, AY_OUT >> 8,  # ld hl,AY_OUT
                  0x0E, 0xF6, 0xAF,                 # ld c,$F6 / xor a
                  0xD3, 0xF5, 0xED, 0x40, 0x70,     # lp: out ($F5),a / in b,(c) / ld (hl),b
                  0x23, 0x3C, 0xFE, 0x10, 0x20, 0xF5,   # inc hl / inc a / cp 16 / jr nz,lp
                  0xC9])                            # ret
    m.write(AY_PROBE, code)
    r = m.call(AY_PROBE, maxi=10_000)
    assert r["ok"], "AY probe did not return"
    return list(m.read(AY_OUT, 16))


def compile_and_run(m, lines, maxi=20_000_000, audit=True, run=True, restore=True, depth=0, keys=None,
                    brk=None):
    """restore=False: keep the machine as the previous run left it (recovery tests). depth=1: run
    with the EXROM paged in, as the shell does (RT_RUN pages it out and back). keys: the keyboard
    feed (parse_keys). brk: ("at", symbol, n) or ("after", n): BREAK pressed then."""
    from lcharness import STOP_ADDR
    S = m.sym
    res = Result()
    res.audit = []
    if restore:
        m.restore()
    m.put_store(c2src.records(lines))
    src0 = m.read(m.sym("PROG_AREA_START"), m.w16(m.sym("PROG_END")) - m.sym("PROG_AREA_START"))
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
    funcs = sorted(((e.val, e) for e in res.globals if e.kind == 2 and e.flags & 8), key=lambda t: t[0])
    if depth:
        r = m.call("BANK_PAGE_EXROM_IN", maxi=100_000)
        assert r["ok"], "BANK_PAGE_EXROM_IN did not return"
    m.setreg("IX", SENTINEL_IX)
    stops = [S("RT_RUN.back")] + ([S("RST_LEAVE")] if audit else [])
    keyq = list(keys or [])
    res.keys_left = None
    kstops = [S("IO_READ_KEY"), S("IO_READ_KEY_NONBLOCK")] if keys is not None else []
    bstop, bcount, pressed = None, 0, False
    if brk and brk[0] == "at":
        bstop, bcount = (S(brk[1]) if not isinstance(brk[1], int) else brk[1]), brk[2]
    stops += kstops + ([bstop] if bstop is not None else []) + ([S("RT_BREAKREQ")] if brk else [])
    res.breakreq = []
    m.tstates_reset()
    if brk and brk[0] == "after":
        pc = call_to(m, "RT_RUN", stops, brk[1])
        if pc not in stops and pc != STOP_ADDR:
            press_break(m, True)
            pressed = True
            pc = m.run_to([STOP_ADDR] + stops, maxi)
    else:
        pc = call_to(m, "RT_RUN", stops, maxi)
    hits = 0
    while pc != STOP_ADDR and pc in stops:
        rg = m.regs()
        if brk and pc == S("RT_BREAKREQ"):
            res.breakreq.append(dict(pc=m.w16(rg["SP"] + 12), running=m.read(S("RUNNING"), 1)[0],
                                     nobrk=m.read(S("NOBRK"), 1)[0]))
        elif pc == bstop:
            bcount -= 1
            if bcount <= 0:
                press_break(m, True)
                pressed = True
                stops = [x for x in stops if x != bstop]
        elif pc in kstops:
            if pc == S("IO_READ_KEY") and m.read(S("KBD_KEYHIT"), 1)[0]:
                pass                                # (the key is latched: it returns now)
            elif keyq:
                k = keyq.pop(0)
                if k is not None:
                    m.write(S("KBD_LASTK"), k)
                    m.write(S("KBD_KEYHIT"), 0xFF)
            elif pc == S("IO_READ_KEY"):
                res.keys_left = "waiting for a key with none left"
                break
        elif pc == S("RST_LEAVE"):
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
    if pressed:
        press_break(m, False)
    rg = m.regs()
    res.ix = rg.get("IX")
    res.hl = rg["HL"]
    res.a = rg["A"] if "A" in rg else (rg.get("AF", 0) >> 8)
    res.sp = rg["SP"]
    res.depth = m.read(S("BANK_EXROM_DEPTH"), 1)[0]
    res.pc = pc
    res.rtline = m.w16(S("RT_ERRLINE"))
    res.src_ok = m.read(S("PROG_AREA_START"), len(src0)) == src0 and \
        m.w16(S("PROG_END")) == S("PROG_AREA_START") + len(src0)
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
    kfeed = None
    brk = None
    for k, body in exp:
        if k == "keys":
            kfeed = (kfeed or []) + parse_keys(body)
        elif k == "break":
            t = body.split()
            brk = ("after", int(t[1].replace("_", ""), 0)) if t[0] == "after" else \
                ("at", t[1], int(t[2]) if len(t) > 2 else 1)
    run = run or any(k in keys for k in ("screen", "ay", "attr", "pixel", "rtline", "cell"))
    res = compile_and_run(m, lines, maxi=maxi, audit="noaudit" not in keys, run=run, depth=depth,
                          keys=kfeed, brk=brk)
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
            if res.ix != SENTINEL_IX:
                msgs.append("IX %04X after the run, expected %04X" % (res.ix, SENTINEL_IX))
            if not res.src_ok:
                msgs.append("the line store changed during the run")
            if res.keys_left:
                msgs.append(res.keys_left)
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
    rows = ayr = None
    for k, body in exp:
        toks = body.split()
        if not res.ran and k in ("screen", "ay", "attr", "pixel", "rtline", "cell"):
            continue
        if k == "screen":
            rows = rows or m.screen_rows()
            n, _, text = body.partition(" ")
            if rows[int(n)] != text.rstrip():
                msgs.append("screen row %s %r, expected %r" % (n, rows[int(n)], text.rstrip()))
        elif k == "rtline":
            if res.rtline != int(toks[0]):
                msgs.append("runtime error line %d, expected %s" % (res.rtline, toks[0]))
        elif k == "ay":
            ayr = ayr or ay_regs(m)
            for t in toks:
                r_, v = t.split("=")
                if ayr[int(r_)] != int(v, 0):
                    msgs.append("AY R%s = %d, expected %s" % (r_, ayr[int(r_)], v))
        elif k == "attr":
            a_ = 0x5800 + 32 * int(toks[0]) + int(toks[1])
            got = res.mem.b(a_)
            if got != int(toks[2], 0):
                msgs.append("attribute (%s, %s) = $%02X, expected %s" % (toks[0], toks[1], got, toks[2]))
        elif k == "pixel":
            x, y = int(toks[0]), int(toks[1])
            a_ = 0x4000 | (y & 0xC0) << 5 | (y & 7) << 8 | (y & 0x38) << 2 | x >> 3
            got = res.mem.b(a_) >> (7 - (x & 7)) & 1
            if got != int(toks[2]):
                msgs.append("pixel (%d, %d) = %d, expected %s" % (x, y, got, toks[2]))
        elif k == "breakpc":
            lo, hi = [m.sym(t) if not t[0].isdigit() else int(t, 0) for t in toks[:2]]
            req = [r_ for r_ in getattr(res, "breakreq", []) if r_["running"]]
            if not req or not lo <= req[0]["pc"] < hi:
                msgs.append("BREAK accepted at %s, expected in $%04X-$%04X" % (
                    ["$%04X" % r_["pc"] for r_ in req], lo, hi))
        elif k == "breakdeferred":
            req = [r_ for r_ in getattr(res, "breakreq", []) if r_["running"]]
            if not req or not req[0]["nobrk"]:
                msgs.append("BREAK was not deferred (NOBRK %s)" % [r_["nobrk"] for r_ in req])
        elif k == "cell":
            got = res.mem.b(m.sym(toks[0]))
            if got != int(toks[1], 0):
                msgs.append("%s = $%02X, expected %s" % (toks[0], got, toks[1]))
        elif k == "mem":
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
