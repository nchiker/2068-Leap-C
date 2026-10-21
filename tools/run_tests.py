#!/usr/bin/env python3
"""Leap-C test runner (make test): boot, lexer and declaration tests in ZEsarUX.

Boot tests (production and test images): cold start reaches the editor's key wait with the
baseline layout in force (spec.md 3.1) and the editor's empty screen shown.

Lexer tests (tests/lexer/**/*.c, test image): each case is written into the line store and lexed
by the ROM (TEST_LEX_DUMP). The dump must equal the host reference lexer (tools/clex.py) on every
field, and must satisfy the case's own hand-written expectations:

    // expect: <tokens>        tokens, in order (several lines are joined); the list must match
                               the whole stream up to the EOF token (which is implied)
    // expect: error <E_NAME> <line>
    // mode: eol               lex with LM_EOL (end-of-line tokens)

Token syntax in expectations: a keyword or punctuator as written (`int`, `<<=`); `id:name`;
`num:N` (append `u` for an unsigned type, written `num:40000u`); `chr:N` (character constant);
`str:text` (no spaces), `strx:hexbytes` or `strrep:hexbyte*count`; `eol`. A suffix `@N` also checks the line; a prefix
` (backquote) also checks the line-start flag (`#).

Throughput (tests/bench/*.c): TEST_LEX_COUNT, T-states per source byte (interrupts on).

Declaration tests (tests/decl/**/*.c, production image): the ROM compiles each case (CC_COMPILE);
tools/decltest.py decodes the workspace and the static data and checks the case's expectations
(see that file). tools/declbench.py measures the workspace per symbol.

Executable tests (tests/expr, tests/experr, tests/golden, tests/run: M1.3, production image): the
ROM compiles each case (CC_PROGRAM) and runs it (RT_RUN); tools/exectest.py checks the exit value,
the compile or runtime error, memory and generated code, and audits every function return (stack
balance, IX). tools/gen_exprtests.py generates tests/expr/gen from a model of the integer semantics.

Phase 4 (tests/mem, and the built-ins of phase4_builtins): image regions and their transitions,
#pragma hires, the stack's floor and the pending-argument limit, the heap's bounds, trampoline nesting,
the IM 1 handler during chunk-6 code. The RAM canary and the banking invariants over the whole corpus
are tools/canary.py (make test runs it after this).

Phase 5 (suite `shell`, tools/shelltest.py): the editor and its commands driven through the keyboard
(the ISR's latch and the real key matrix), the C punctuation's keys and glyphs, keyword highlighting,
RUN with its error and BREAK recovery, the typing cost per key and the selective-redraw oracle.

Phase 6 (suite `e2e`, tools/e2etest.py): the compile/run workflow: typed programs RUN from the editor,
the whole corpus through the shell's RUN path, the diagnostics and the reports. Suite `canary`: the RAM
canary and banking invariants over the corpus (tools/canary.py), as tasks of the same pool.

Phase 7 (suite `tape`, tools/tapetest.py): cassette SAVE, LOAD and VERIFY and the library's tape_save /
tape_load on real tape signals (the MIC line captured, ZEsarUX's real-tape input played), their failures and
recoveries, the host tool's tapes, V2 and Leap-C refusing each other's tapes.

Every suite runs as tasks on a pool of emulators (--workers, default the CPUs less one, at most 8).

Usage: run_tests.py [--port N] [--only SUBSTR] [--workers N]
                    [--suite boot,lexer,decl,exec,bench,shell,e2e,tape,canary] [--json OUT]"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import clex             # noqa: E402
import decltest         # noqa: E402
import declbench        # noqa: E402
import exectest         # noqa: E402
import helperbench      # noqa: E402
import memguard         # noqa: E402
import stmtbench        # noqa: E402
import shelltest        # noqa: E402
import e2etest          # noqa: E402
import tapetest         # noqa: E402
import canary           # noqa: E402
from lcharness import Machine   # noqa: E402

ROOT = os.path.dirname(HERE)
EXEC_DIRS = ("expr", "experr", "golden", "run", "stmt", "stmterr", "pp", "pperr", "lib", "rt", "mem")
TEST_AREA = 0xE000
TEST_DUMP_DATA = TEST_AREA + 8


# ---------------------------------------------------------------- dump decoding
def decode_dump(data):
    """ROM token dump -> (tokens as clex.Token, error (code, line) or None)."""
    toks = []
    i = 0
    while i < len(data):
        kind = data[i]
        if kind == 0xFF:
            return toks, (data[i + 1], data[i + 2] | data[i + 3] << 8)
        flags, line = data[i + 1], data[i + 2] | data[i + 3] << 8
        i += 4
        value = text = None
        if kind == clex.TK["TK_NUM"]:
            value = data[i] | data[i + 1] << 8
            i += 2
        elif kind in (clex.TK["TK_IDENT"], clex.TK["TK_STR"]):
            n = data[i]
            text = bytes(data[i + 1:i + 1 + n])
            i += 1 + n
        toks.append(clex.Token(kind, flags, line, value, text))
        if kind == clex.TK["TK_EOF"]:
            break
    return toks, None


# ---------------------------------------------------------------- expectations
def parse_case(path):
    text = open(path, encoding="latin-1").read()
    exp, mode, err = [], False, None
    for l in text.split("\n"):
        s = l.strip()
        if s.startswith("// expect:"):
            body = s[len("// expect:"):].split()
            if body and body[0] == "error":
                err = (clex.ER[body[1]], int(body[2]))
            else:
                exp += body
        elif s.startswith("// mode:") and "eol" in s:
            mode = True
    return text, exp, err, mode


def match_expect(item, tok):
    """Check one expectation item against a token; returns None or a mismatch message."""
    want_bol = item.startswith("`")
    if want_bol:
        item = item[1:]
    want_line = None
    if "@" in item and not item.startswith("str"):
        item, ln = item.rsplit("@", 1)
        want_line = int(ln)
    T = clex.TK
    if item.startswith("id:"):
        ok = tok.kind == T["TK_IDENT"] and tok.text == item[3:].encode()
    elif item.startswith("num:"):
        v = item[4:]
        uns = v.endswith("u")
        v = int(v.rstrip("u"), 0)
        ok = (tok.kind == T["TK_NUM"] and tok.value == v and not tok.flags & clex.TF_CHARCONST
              and bool(tok.flags & clex.TF_UNSIGNED) == uns)
    elif item.startswith("chr:"):
        ok = tok.kind == T["TK_NUM"] and tok.value == int(item[4:], 0) and tok.flags & clex.TF_CHARCONST
    elif item.startswith("strrep:"):
        hx, n = item[7:].split("*")
        ok = tok.kind == T["TK_STR"] and tok.text == bytes.fromhex(hx) * int(n)
    elif item.startswith("strx:"):
        ok = tok.kind == T["TK_STR"] and tok.text == bytes.fromhex(item[5:])
    elif item.startswith("str:"):
        ok = tok.kind == T["TK_STR"] and tok.text == item[4:].encode()
    elif item == "eol":
        ok = tok.kind == T["TK_EOL"]
    elif item in clex.KW_KIND:
        ok = tok.kind == clex.KW_KIND[item]
    elif item in clex.PUNCT_KIND:
        ok = tok.kind == clex.PUNCT_KIND[item]
    else:
        return "bad expectation item %r" % item
    if ok and want_line is not None and tok.line != want_line:
        ok = False
    if ok and want_bol and not tok.flags & clex.TF_BOL:
        ok = False
    return None if ok else "expected %s, got %r" % (item, tok)


def check_lexer_case(m, path, ref_only=False):
    """ref_only: compare with the reference lexer only (samples without expectations)."""
    text, exp, err, eol = parse_case(path)
    lines = c2src.lines_of(text)
    m.restore()
    m.put_store(c2src.records(lines))
    m.write(TEST_AREA + 2, 1 if eol else 0)
    r = m.call("TEST_LEX_DUMP", maxi=20_000_000)
    if not r["ok"]:
        return False, "did not return (PC=%04X)" % r["pc"], None
    end = m.w16(TEST_AREA)
    rom_toks, rom_err = decode_dump(m.read(TEST_DUMP_DATA, end - TEST_DUMP_DATA))
    ref_toks, ref_e = clex.lex(lines, eol)
    ref_err = (ref_e.code, ref_e.line) if ref_e else None
    msgs = []
    # 1. ROM == reference lexer, every field
    if [t.key() for t in rom_toks] != [t.key() for t in ref_toks] or rom_err != ref_err:
        for k, (a, b) in enumerate(zip(rom_toks, ref_toks)):
            if a.key() != b.key():
                msgs.append("token %d: ROM %r, reference %r" % (k, a, b))
                break
        else:
            msgs.append("ROM %d tokens err %s, reference %d tokens err %s" % (
                len(rom_toks), rom_err, len(ref_toks), ref_err))
    # 2. hand-written expectations
    if ref_only:
        pass
    elif err is not None:
        if rom_err != err:
            msgs.append("expected error %s, ROM gave %s" % (err, rom_err))
    else:
        if rom_err is not None:
            msgs.append("unexpected error %s" % (rom_err,))
        stream = [t for t in rom_toks if t.kind != clex.TK["TK_EOF"]]
        if len(stream) != len(exp):
            msgs.append("expected %d tokens, ROM gave %d: %r" % (len(exp), len(stream), stream))
        else:
            for item, tok in zip(exp, stream):
                e = match_expect(item, tok)
                if e:
                    msgs.append(e)
                    break
        if not rom_toks or rom_toks[-1].kind != clex.TK["TK_EOF"]:
            msgs.append("no EOF token")
    info = dict(tokens=len(rom_toks), error=rom_err, bytes=len(c2src.records(lines)))
    return not msgs, "; ".join(msgs), info


RAW_CASES = [
    ("string beyond TOK_BUF (E_TOOLONG)", ["x;", 's = "' + "B" * 140 + '";'], ("E_TOOLONG", 2)),
    ("string of exactly 128 bytes", ['"' + "C" * 128 + '"'], None),
    ("TAB byte (E_BADCHAR)", ["int\tx;"], ("E_BADCHAR", 1)),
    ("NUL inside a line (E_BADCHAR)", ["a", "b\0c"], ("E_BADCHAR", 2)),
    ("byte $80 (E_BADCHAR)", ["a \x80"], ("E_BADCHAR", 1)),
    ("byte $7F (E_BADCHAR)", ["\x7f"], ("E_BADCHAR", 1)),
    ("identifier of 200 characters", ["k" * 200 + " z"], None),
]


def check_raw_case(m, lines, want):
    """Raw records (bypassing c2src.py) against the reference lexer and the expected error."""
    import struct
    recs = b"".join(struct.pack("<H", len(l) + 1) + l.encode("latin-1") + b"\r" for l in lines)
    m.restore()
    m.put_store(recs)
    m.write(TEST_AREA + 2, 0)
    r = m.call("TEST_LEX_DUMP", maxi=5_000_000)
    if not r["ok"]:
        return False, "did not return"
    rom_toks, rom_err = decode_dump(m.read(TEST_DUMP_DATA, m.w16(TEST_AREA) - TEST_DUMP_DATA))
    ref_toks, ref_e = clex.lex(lines)
    ref_err = (ref_e.code, ref_e.line) if ref_e else None
    if [t.key() for t in rom_toks] != [t.key() for t in ref_toks] or rom_err != ref_err:
        return False, "ROM %r %s, reference %r %s" % (rom_toks, rom_err, ref_toks, ref_err)
    exp = (clex.ER[want[0]], want[1]) if want else None
    if rom_err != exp:
        return False, "expected %s, got %s" % (exp, rom_err)
    return True, ""


# ---------------------------------------------------------------- boot tests
def boot_checks(m):
    """Checks at the idle prompt (snapshot state). Returns list of (name, ok, detail)."""
    S = m.sym
    out = []
    rows = m.screen_rows()
    out.append(("editor screen (Phase 5 shell)", not any(rows[:23]) and rows[23] == "LINE 1/0", repr(rows[22:])))
    r = m.regs()
    out.append(("idle key wait", r["PC"] == S("IO_READ_KEY"), "PC=%04X" % r["PC"]))
    out.append(("stack in $F800-$FEFF", 0xF800 <= r["SP"] <= 0xFF00, "SP=%04X" % r["SP"]))
    out.append(("EXROM paged in, depth 1", m.read(S("BANK_EXROM_DEPTH"), 1)[0] == 1, ""))
    out.append(("sysvars relocated to $5B00", S("EDIT_BUF_OFFSET") == 0x5B00 and S("LEAPC_SYSVARS_END") == 0x5D5A,
                "EDIT_BUF_OFFSET=%04X end=%04X" % (S("EDIT_BUF_OFFSET"), S("LEAPC_SYSVARS_END"))))
    out.append(("Leap-C cells below $6000", S("LEAPC_CELLS_END") <= 0x6000, "end=%04X" % S("LEAPC_CELLS_END")))
    out.append(("empty line store at $7800", S("PROG_AREA_START") == 0x7800 and m.w16(S("PROG_END")) == 0x7800,
                "PROG_END=%04X" % m.w16(S("PROG_END"))))
    out.append(("source ceiling $C000", m.w16(S("VARS_START")) == 0xC000, "VARS_START=%04X" % m.w16(S("VARS_START"))))
    f0 = m.w16(S("FRAMES"))
    m.cmd("disable-breakpoints")
    m.run(300_000)
    f1 = m.w16(S("FRAMES"))
    out.append(("interrupts running (FRAMES advances)", f1 > f0, "%d -> %d" % (f0, f1)))
    m.restore()
    # chunk 6 is EXROM at the prompt: the shell entry jump is visible at $C000
    out.append(("chunk 6 = EXROM", m.read(0xC000, 1)[0] == 0xC3, "$C000=%02X" % m.read(0xC000, 1)[0]))
    # cold-cleared RAM: the Leap-C cells read 0 after boot (spot check), up to the editor's and the
    # shell's, which the editor's first redraw writes
    z = m.read(S("LEAPC_CELLS_BASE"), S("V2_REDRAW_SCOPE") - S("LEAPC_CELLS_BASE"))
    out.append(("Leap-C cells cleared", not any(z), ""))
    return out


SECOND = ["int main(void)", "{", "    char *p;", "    p = malloc(10);", "    strcpy(p, \"ok\");",
          "    print(p);", "    return strlen(p) + 40;", "}"]


def phase3_builtins(m):
    """Phase 3 checks that need the harness between runs (project_plan.md section 5)."""
    S = m.sym
    out = []
    # recovery: after BREAK, a library runtime error and exit(), the next program compiles and runs
    # in the same machine state (no snapshot restore), with the shell's paging (depth 1)
    loop = c2src.lines_of(open(os.path.join(ROOT, "tests", "rt", "break_loop.c")).read())
    for what, src, brk, want in (("BREAK", loop, ("after", 200_000), 5),
                                 ("a library runtime error", ["int main(void) { mode(9); return 0; }"], None, 4),
                                 ("exit()", ["int main(void) { exit(3); return 0; }"], None, 0)):
        r1 = exectest.compile_and_run(m, src, audit=False, depth=1, brk=brk)
        r2 = exectest.compile_and_run(m, SECOND, restore=False, depth=1)
        ok = (r1.ran and r1.a == want and r1.depth == 1 and r1.sp == 0xFF02 and r1.ix == exectest.SENTINEL_IX
              and r1.src_ok and r2.ran and r2.a == 0 and r2.hl == 42 and r2.depth == 1 and not r2.audit
              and m.read(S("RUNNING"), 1)[0] == 0)
        out.append(("(built-in) a second compile and run after %s" % what, ok,
                    "" if ok else "first a=%s depth=%s sp=%04X; second hl=%s a=%s %s" % (
                        r1.a, r1.depth, r1.sp, getattr(r2, "hl", None), getattr(r2, "a", None), r2.audit)))
    # BREAK at the idle shell (no program running): an ordinary key; the shell keeps idling
    m.restore()
    pc = m.run_to([S("IO_READ_KEY")], 1_000_000)
    sp0 = m.regs()["SP"]
    exectest.press_break(m, True)
    m.set_bps([])
    m.run(400_000)
    exectest.press_break(m, False)
    m.run(200_000)
    pc = m.run_to([S("IO_READ_KEY")], 1_000_000)
    rg = m.regs()
    ok = (pc == S("IO_READ_KEY") and rg["SP"] == sp0 and m.read(S("KBD_LASTK"), 1)[0] == 0x10
          and m.read(S("BRK_HALT"), 1)[0] == 0 and m.read(S("RUNNING"), 1)[0] == 0)
    out.append(("(built-in) BREAK at the idle shell is an ordinary key", ok,
                "" if ok else "pc %04X sp %04X (was %04X) lastk %02X" % (pc, rg["SP"], sp0,
                                                                         m.read(S("KBD_LASTK"), 1)[0])))
    # the ISR's cost per frame (IM 1 vector to its reti), idle and with a key held
    def isr_cost(n):
        ts = []
        for _ in range(n):
            if m.run_to([0x0038], 1_000_000) != 0x0038:
                return None
            m.tstates_reset()
            if m.run_to([0x003C], 100_000) != 0x003C:
                return None
            ts.append(m.tstates())
            m.cmd("cpu-step")
        return ts
    m.restore()
    idle = isr_cost(20)
    m.cmd("send-keys-event 97 1")
    held = isr_cost(40)
    m.cmd("send-keys-event 97 0")
    ok = bool(idle and held) and max(idle + held) <= 2750
    msg = "ISR per frame: idle %s T (%d-%d), key held %d-%d T (V2: 2.0-2.5 kT; limit 2,750)" % (
        round(sum(idle) / len(idle)) if idle else None, min(idle or [0]), max(idle or [0]),
        min(held or [0]), max(held or [0]))
    out.append(("(built-in) ISR cost per frame within V2's +10%", ok, msg))
    # the binding's search (compile time, through the EXROM trampoline): the first and last names
    # of the table and a name that is not the library's; the least of 3 runs (no interrupt inside)
    m.restore()
    m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)
    times, ok = {}, True
    for name, want in (("cls", S("LIB_CLS")), ("exit", S("LIB_EXIT")), ("count", None)):
        m.write(0xF400, name.encode())
        m.poke16(S("NM_PTR"), 0xF400)
        m.write(S("NM_LEN"), len(name))
        best = None
        for _ in range(3):
            m.tstates_reset()
            r = m.call("CX_LIBFIND", maxi=200_000)
            t = m.tstates()
            rg = m.regs()
            found = bool(rg["AF"] & 0x40)            # Z: a library name
            ok = ok and r["ok"] and found == (want is not None) and (want is None or rg["HL"] == want)
            ok = ok and m.read(S("BANK_EXROM_DEPTH"), 1)[0] == 0
            best = t if best is None else min(best, t)
        times[name] = best
    out.append(("(built-in) the library's name search (CX_LIBFIND)", ok,
                "cls %d T, exit %d T, not a library name %d T" % (times["cls"], times["exit"], times["count"])))
    return out


LOOP = ["int main(void)", "{", "    unsigned t;", "    unsigned n;", "    t = frames() + 20;", "    n = 0;",
        "    while (frames() < t)", "        n++;", "    return n > 100;", "}"]


def phase4_builtins(m):
    """Phase 4 banking invariants that need the harness between steps (project_plan.md section 6):
    trampoline nesting, beep()'s trampoline from the shell's paging, the IM 1 handler during
    chunk-6 code. (The invariants over the whole corpus: tools/canary.py.)"""
    from lcharness import STOP_ADDR
    S = m.sym
    out = []
    marker = 0x5A

    def chunk6():                                    # what chunk 6 shows: the EXROM's jp, or RAM
        b = m.read(0xC000, 1)[0]
        return "EXROM" if b == 0xC3 else "RAM" if b == marker else "$%02X" % b

    # the compile-time trampolines at depth 0 (as the compiler calls them) and nested at depth 1
    for depth in (0, 1):
        m.restore()                                  # the idle shell: depth 1, chunk 6 = EXROM
        m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)
        m.write(0xC000, marker)
        if depth:
            m.call("BANK_PAGE_EXROM_IN", maxi=100_000)
        m.setreg("AF", S("TK_STAR") << 8)
        m.setreg("DE", 6)
        m.setreg("HL", 7)
        m.setreg("BC", 0)
        r = m.call("CX_FOLD", maxi=200_000)
        hl = m.regs()["HL"]
        d1, c1 = m.read(S("BANK_EXROM_DEPTH"), 1)[0], chunk6()
        m.write(0xF400, b"exit")
        m.poke16(S("NM_PTR"), 0xF400)
        m.write(S("NM_LEN"), 4)
        r2 = m.call("CX_LIBFIND", maxi=200_000)
        rg = m.regs()
        d2, c2 = m.read(S("BANK_EXROM_DEPTH"), 1)[0], chunk6()
        want = "EXROM" if depth else "RAM"
        ok = (r["ok"] and r2["ok"] and hl == 42 and rg["HL"] == S("LIB_EXIT") and (d1, c1, d2, c2) ==
              (depth, want, depth, want))
        out.append(("(built-in) trampolines CX_FOLD and CX_LIBFIND at paging depth %d%s" % (
            depth, " (nested)" if depth else ""), ok,
            "" if ok else "fold %d depth %d chunk 6 %s; libfind HL %04X depth %d chunk 6 %s" % (
                hl, d1, c1, rg["HL"], d2, c2)))
    # beep() from the shell's paging: RT_RUN pages the EXROM out (depth 0), the trampoline in (1),
    # NOBRK covers it; afterwards the shell's depth 1 again
    src = ["int main(void)", "{", "    beep(2, 0);", "    return 7;", "}"]
    r = exectest.compile_and_run(m, src, run=False)
    m.call("BANK_PAGE_EXROM_IN", maxi=100_000)
    m.setreg("IX", exectest.SENTINEL_IX)
    pc = exectest.call_to(m, "RT_RUN", [S("AY_WAIT_FRAMES")], 5_000_000)   # (HOME, called by the EXROM's beep)
    inside = (pc, m.read(S("BANK_EXROM_DEPTH"), 1)[0], m.read(S("NOBRK"), 1)[0], m.read(S("RUNNING"), 1)[0] != 0,
              m.read(0xC000, 1)[0] == 0xC3)
    m.cmd("cpu-step")
    pc2 = m.run_to([STOP_ADDR], 5_000_000)
    rg = m.regs()
    after = (pc2, rg["HL"], m.read(S("BANK_EXROM_DEPTH"), 1)[0], m.read(S("NOBRK"), 1)[0],
             m.read(S("RUNNING"), 1)[0], m.read(0xC000, 1)[0] == 0xC3)
    ok = r.compile_ok and not r.errnum and inside == (S("AY_WAIT_FRAMES"), 1, 1, True, True) and \
        after == (STOP_ADDR, 7, 1, 0, 0, True)
    out.append(("(built-in) beep()'s trampoline from the shell's paging (depth 1 -> 0 -> 1 -> 0 -> 1)", ok,
                "" if ok else "in the EXROM: %r; after: %r" % (inside, after)))
    # the IM 1 handler during chunk-6 code: interrupts taken with the interrupted PC in chunk 6, the
    # program's loop correct, and no write to chunk 6 at all (the loop writes none; the handler
    # must not), with the banking invariants armed
    r = exectest.compile_and_run(m, LOOP, run=False)
    main_at = [e.val for e in r.globals if e.name == "main"][0]
    memguard.arm(m, True)
    m.cmd("set-breakpoint 12 PC=0038H and PEEK(SP+1)>BFH and PEEK(SP+1)<E0H")
    m.cmd("set-breakpoint 13 MWA>BFFFH and MWA<E000H")
    m.setreg("IX", exectest.SENTINEL_IX)
    pc = exectest.call_to(m, "RT_RUN", [], 20_000_000)
    hits, other = 0, None
    while pc != STOP_ADDR:
        if pc == 0x0038 and 0xC000 <= m.w16(m.regs()["SP"]) < 0xE000:
            hits += 1
            m.cmd("cpu-step")
            pc = m.run_to([STOP_ADDR], 20_000_000)
        else:
            other = "stopped at $%04X: %s" % (pc, memguard.fired(m) or "a write to chunk 6")
            break
    for i in (12, 13):
        m.cmd("set-breakpoint %d" % i)
    memguard.arm(m, False)
    hl = m.regs()["HL"]
    ok = 0xC000 <= main_at < 0xE000 and other is None and hits >= 15 and hl == 1
    out.append(("(built-in) the IM 1 handler during chunk-6 code", ok,
                "%d interrupts taken in chunk 6 (main at $%04X), result %d%s" % (
                    hits, main_at, hl, "; " + other if other else "")))
    return out


# ---------------------------------------------------------------- tasks (Phase 6: run in parallel)
# make test runs every suite as tasks on a pool of workers, each with its own ZEsarUX (port base + its
# number), reusing it from task to task while the image (production or test) stays the same. A task
# returns its rows per suite, its failure count, its output lines and its measurements; the main
# process merges them into the report and build/test_results.json as before. Measurements are T-states
# of the emulated machine, which the host's load does not change.
SHARDS = dict(decl=3, exec=8, corpus=8, canary=8)


def _shard(items, k, n):
    return items[k::n]


def exec_cases(only):
    cases = []
    for d in EXEC_DIRS:
        cases += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
    return [c for c in cases if not only or only in c]


def t_boot(m, arg, only, suites):
    m.restore()                                 # (the worker's emulator may have run other tasks)
    checks = boot_checks(m)
    out = ["%s boot: %-38s %s %s" % (arg, n, "PASS" if ok else "FAIL", d if not ok else "") for n, ok, d in checks]
    out.append("%s boot: cold start to idle prompt %d T-states" % (arg, m.boot["tstates"]))
    return dict(rows={"boot": [dict(image=arg, boot_tstates=m.boot["tstates"],
                                    checks=[dict(name=n, ok=ok, detail=d) for n, ok, d in checks])]},
                failed=sum(not ok for _, ok, _ in checks), out=out)


def t_decl(m, arg, only, suites):
    k, n = arg
    cases = sorted(glob.glob(os.path.join(ROOT, "tests", "decl", "**", "*.c"), recursive=True))
    cases = _shard([c for c in cases if not only or only in c], k, n)
    rows, out, extra = [], [], {}
    for c in cases:
        ok, msg, info = decltest.check_case(m, c)
        rel = os.path.relpath(c, ROOT)
        rows.append(dict(case=rel, ok=ok, msg=msg, info=info))
        if not ok:
            out.append("decl: FAIL %s: %s" % (rel, msg))
    if k == 0 and "bench" in suites and not only:
        extra["decl_ws"] = declbench.measure(m)
    return dict(rows={"decl": rows}, failed=sum(not r["ok"] for r in rows), out=out, extra=extra)


def t_exec(m, arg, only, suites):
    k, n = arg
    rows, out = [], []
    for c in _shard(exec_cases(only), k, n):
        ok, msg, info = exectest.check_case(m, c)
        rel = os.path.relpath(c, ROOT)
        rows.append(dict(case=rel, ok=ok, msg=msg, info=info))
        if not ok:
            out.append("exec: FAIL %s: %s" % (rel, msg))
    return dict(rows={"exec": rows}, failed=sum(not r["ok"] for r in rows), out=out)


def t_exec_builtins(m, arg, only, suites):
    """The built-in executable checks and the measurements (helpers, ISR, spike workloads)."""
    S = m.sym
    rows, out, extra, failed = [], [], {}, 0

    def add(name, ok, msg, group):
        rows.append(dict(case=name, ok=ok, msg=msg, info=None, group=group))
        if not ok:
            out.append("exec: FAIL %s: %s" % (name, msg))
    if "bench" in suites:
        extra["helpers"] = helperbench.measure(m)
        for r in extra["helpers"]:
            failed += not r["ok"]
            out.append("helper: %-58s %s %4s T %d B site %s" % (
                r["name"], "PASS" if r["ok"] else "FAIL", r.get("tstates"), r.get("site_bytes", 0), r["detail"]))
    # the machine is sane after a stack overflow: a second program compiles and runs in the same
    # machine state (no snapshot restore in between)
    ov = c2src.lines_of(open(os.path.join(ROOT, "tests", "run", "stack_overflow.c")).read())
    r1 = exectest.compile_and_run(m, ov, audit=False)
    r2 = exectest.compile_and_run(m, ["int f(int x) { return x * 3; }", "int main(void) { return f(14); }"],
                                  restore=False)
    ok = (r1.ran and r1.a == 1 and r1.sp == 0xFF02 and r1.depth == 0 and r2.ran and r2.a == 0
          and r2.hl == 42 and not r2.audit)
    add("(built-in) recovery after a stack overflow", ok, "" if ok else "overflow run a=%s sp=%04X; next run hl=%s a=%s %s" % (
        r1.a, r1.sp, getattr(r2, "hl", None), getattr(r2, "a", None), r2.audit), "run")
    # the function -> line table (spec.md 5.9): one record per defined function, [link][address][line]
    src = ["int f(void) { return 1; }", "", "static", "int g(int x)", "{", "    return x;", "}",
           "int main(void) { return f() + g(1); }"]
    r = exectest.compile_and_run(m, src)
    recs, a_ = [], m.w16(S("RUN_FNLINES"))
    while a_ and len(recs) < 10:
        recs.append((m.w16(a_ + 2), m.w16(a_ + 4)))
        a_ = m.w16(a_)
    fn = {e.name: e.val for e in r.globals if e.kind == 2}
    want = sorted([(fn["f"], 1), (fn["g"], 3), (fn["main"], 8)])
    ok = r.ran and r.hl == 2 and sorted(recs) == want
    add("(built-in) the function -> line table", ok, "" if ok else "records %r, expected %r" % (recs, want), "run")
    # every run starts rand() afresh (RT_RUN clears its state LIB_RND: srand(1)'s sequence)
    m.restore()
    m.write(S("LIB_RND"), b"\x34\x12")
    r2 = exectest.compile_and_run(m, ["int main(void) { return 0; }"], restore=False)
    ok2 = r2.ran and m.w16(S("LIB_RND")) == 0
    add("(built-in) rand() starts afresh in every run", ok2, "" if ok2 else "LIB_RND %04X" % m.w16(S("LIB_RND")), "run")
    for name, ok, msg in phase4_builtins(m):
        add(name, ok, msg, "mem")
        if "IM 1" in name:
            out.append("measured: %s" % msg)
    for name, ok, msg in phase3_builtins(m):
        add(name, ok, msg, "rt")
        if "ISR" in name or "name search" in name:
            out.append("measured: %s" % msg)
            extra["isr" if "ISR" in name else "libfind"] = msg
    if "bench" in suites:
        extra["spike"] = stmtbench.measure(m)
        for r in extra["spike"]:
            failed += not r["ok"]
            if "bytes" not in r:
                out.append("spike: FAIL %s" % r)
                continue
            out.append("spike: %-20s %s %3d B (spike %3d) %7d T (spike %7d)" % (
                r["name"], "PASS" if r["ok"] else "FAIL", r["bytes"], r["spike_bytes"], r["tstates"], r["spike_tstates"]))
    failed += sum(not r["ok"] for r in rows)
    return dict(rows={"exec": rows}, failed=failed, out=out, extra=extra)


def t_lexer(m, arg, only, suites):
    rows, bench, out = [], [], []
    failed = 0
    if "lexer" in suites:
        cases = sorted(glob.glob(os.path.join(ROOT, "tests", "lexer", "**", "*.c"), recursive=True))
        for c in [c for c in cases if not only or only in c]:
            ok, msg, info = check_lexer_case(m, c)
            rel = os.path.relpath(c, ROOT)
            rows.append(dict(case=rel, ok=ok, msg=msg, info=info))
            if not ok:
                out.append("lexer: FAIL %s: %s" % (rel, msg))
        if not only:
            # a truly empty line store (no records) gives one EOF token, line 1, at a line start (a .c
            # file always has at least its expectation line)
            m.restore()
            m.put_store(b"")
            m.write(TEST_AREA + 2, 0)
            r = m.call("TEST_LEX_DUMP", maxi=1_000_000)
            toks, err = decode_dump(m.read(TEST_DUMP_DATA, m.w16(TEST_AREA) - TEST_DUMP_DATA))
            ok = (r["ok"] and err is None and len(toks) == 1 and
                  toks[0].key() == (clex.TK["TK_EOF"], clex.TF_BOL, 1, None, None))
            rows.append(dict(case="(built-in) empty line store", ok=ok, msg="" if ok else repr(toks), info=None))
            if not ok:
                out.append("lexer: FAIL empty line store: %r %s" % (toks, err))
            # raw-record cases: line-store contents the editor and c2src.py never produce (lines over 127
            # characters, bytes outside 32-126); the lexer must still be safe
            for name, lines, want in RAW_CASES:
                ok, msg = check_raw_case(m, lines, want)
                rows.append(dict(case="(built-in raw) " + name, ok=ok, msg=msg, info=None))
                if not ok:
                    out.append("lexer: FAIL raw %s: %s" % (name, msg))
        failed += sum(not r["ok"] for r in rows)
    for b in sorted(glob.glob(os.path.join(ROOT, "tests", "bench", "*.c"))) if "bench" in suites else []:
        lines = c2src.lines_of(open(b, encoding="latin-1").read())
        recs = c2src.records(lines)
        ok, msg, info = check_lexer_case(m, b, ref_only=True) if os.path.basename(b).startswith("lex") else (True, "", {})
        m.restore()
        m.put_store(recs)
        r = m.call("TEST_LEX_COUNT", maxi=50_000_000, t0="TEST_LEX_COUNT.t0", t1="TEST_LEX_COUNT.t1")
        ntok = m.w16(TEST_AREA + 3)
        errn = m.read(m.sym("CC_ERRNUM"), 1)[0]
        text_bytes = sum(len(l) + 1 for l in lines)
        row = dict(sample=os.path.relpath(b, ROOT), ok=ok and r["ok"] and errn == 0, msg=msg,
                   lines=len(lines), text_bytes=text_bytes, store_bytes=len(recs), tokens=ntok,
                   tstates=r["tstates"],
                   t_per_byte=r["tstates"] / text_bytes if r["tstates"] else None,
                   t_per_token=r["tstates"] / ntok if r["tstates"] else None,
                   t_per_line=r["tstates"] / len(lines) if r["tstates"] else None)
        bench.append(row)
        failed += not row["ok"]
        out.append("bench %s: %s %d lines, %d text bytes, %d tokens, %s T = %.1f T/byte, %.0f T/token, "
                   "%.0f T/line (%.2f ms/line at 3.528 MHz)" % (
                       row["sample"], "PASS" if row["ok"] else "FAIL " + msg, row["lines"], text_bytes, ntok,
                       r["tstates"], row["t_per_byte"] or 0, row["t_per_token"] or 0, row["t_per_line"] or 0,
                       (row["t_per_line"] or 0) / 3528.0))
    return dict(rows={"lexer": rows, "bench": bench}, failed=failed, out=out)


def _case_task(module, prefix, suite):
    def task(m, arg, only, suites):
        name = arg
        title, fn = [(c[1], c[-1]) for c in module.CASES if c[0] == name][0]
        sh = getattr(m, "_shell", None) or shelltest.Shell(m)
        m._shell = sh
        sh.measured = None
        try:
            ok, detail = fn(sh)
        except Exception as e:                      # noqa: BLE001 -- a case that crashes fails
            ok, detail = False, "%s: %s" % (type(e).__name__, e)
        extra = {"typing": sh.measured} if getattr(sh, "measured", None) else {}
        return dict(rows={suite: [dict(case=name, title=title, ok=ok, detail=detail)]}, failed=int(not ok),
                    out=["%s: %-34s %s %s" % (prefix, name, "PASS" if ok else "FAIL", detail if not ok else "")],
                    extra=extra)
    return task


t_shell = _case_task(shelltest, "shell", "shell")
t_e2e = _case_task(e2etest, "e2e", "e2e")


def t_tape(m, arg, only, suites):
    sh = getattr(m, "_shell", None) or shelltest.Shell(m)
    m._shell = sh
    r = tapetest.run_case(sh, arg)
    return dict(rows={"tape": [r]}, failed=int(not r["ok"]),
                out=["tape: %-34s %s %s" % (arg, "PASS" if r["ok"] else "FAIL", r["detail"] if not r["ok"] else "")])


def t_corpus(m, arg, only, suites):
    k, n = arg
    sh = getattr(m, "_shell", None) or shelltest.Shell(m)
    m._shell = sh
    out = []
    rows = e2etest.run_corpus(m, sh, _shard(e2etest.corpus([only] if only else None), k, n), out=out.append)
    return dict(rows={"e2e_corpus": rows}, failed=sum(not r["ok"] for r in rows), out=out)


def t_canary(m, arg, only, suites):
    k, n = arg
    out = []
    box = [m]

    def restart():
        box[0].stop()
        box[0].start()
        return box[0]
    rows = []
    for rec in canary.check_all(m, _shard(canary.corpus(only), k, n), restart):
        rows.append(rec)
        if not rec["ok"]:
            out.append("canary: FAIL %s: %s" % (rec["case"], rec["msg"]))
    return dict(rows={"canary": rows}, failed=sum(not r["ok"] for r in rows), out=out)


TASKS = dict(boot=t_boot, decl=t_decl, exec=t_exec, execb=t_exec_builtins, lexer=t_lexer, shell=t_shell,
             e2e=t_e2e, tape=t_tape, corpus=t_corpus, canary=t_canary)
HEAVY = ("typing-cost", "redraw-oracle")


def plan(suites, only):
    """The tasks, the longest first: (kind, image, arg)."""
    t = []
    if "shell" in suites:
        sc = [n for n, _, _ in shelltest.CASES if not only or only in n]
        t += [("shell", "build", c) for c in sc if c in HEAVY]
    if "canary" in suites:
        t += [("canary", "build", (k, SHARDS["canary"])) for k in range(SHARDS["canary"])]
    if "tape" in suites:                            # (the longest first: the not-found search, the V2 exchange)
        tc = [n for n, _, _ in tapetest.CASES if not only or only in n]
        t += [("tape", "build", n) for n in sorted(tc, key=lambda n: n not in tapetest.LONG)]
    if "e2e" in suites:
        t += [("corpus", "build", (k, SHARDS["corpus"])) for k in range(SHARDS["corpus"])]
    if "exec" in suites:
        t += [("exec", "build", (k, SHARDS["exec"])) for k in range(SHARDS["exec"])]
        if not only:
            t.append(("execb", "build", None))
    if "decl" in suites:
        t += [("decl", "build", (k, SHARDS["decl"])) for k in range(SHARDS["decl"])]
    if "lexer" in suites or "bench" in suites:
        t.append(("lexer", "build/test", None))
    if "e2e" in suites:
        t += [("e2e", "build", n) for n, _, _, _ in e2etest.CASES if not only or only in n]
    if "shell" in suites:
        t += [("shell", "build", c) for c in sc if c not in HEAVY]
    if "boot" in suites:
        t += [("boot", "build", "production"), ("boot", "build/test", "test")]
    return t


def worker(port, tasks, results, only, suites):
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))  # (the finally below stops the emulator)
    m = None
    try:
        while True:
            item = tasks.get()
            if item is None:
                break
            idx, (kind, image, arg) = item
            t0 = time.time()
            try:
                if m is None or m.build != os.path.abspath(os.path.join(ROOT, image)):
                    if m is not None:
                        m.stop()
                    m = Machine(os.path.join(ROOT, image), port)
                    m.start()
                r = TASKS[kind](m, arg, only, suites)
            except Exception as e:                  # noqa: BLE001 -- a task that crashes fails; new emulator
                r = dict(rows={}, failed=1, out=["%s: TASK FAILED %r: %s: %s" % (kind, arg, type(e).__name__, e)])
                try:
                    m.stop()
                except Exception:                   # noqa: BLE001
                    pass
                m = None
            r["kind"], r["wall"], r["idx"] = kind, time.time() - t0, idx
            results.put(r)
    finally:
        if m is not None:
            m.stop()
        results.put(None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10760)
    ap.add_argument("--only")
    ap.add_argument("--json", default=os.path.join(ROOT, "build", "test_results.json"))
    ap.add_argument("--suite", default="boot,lexer,decl,exec,bench,shell,e2e,tape,canary")
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 4) - 1)))
    a = ap.parse_args()
    suites = a.suite.split(",")
    t_start = time.time()
    tasks = plan(suites, a.only)
    nw = max(1, min(a.workers, len(tasks)))
    tq, rq = mp.Queue(), mp.Queue()
    for i, t in enumerate(tasks):
        tq.put((i, t))
    for _ in range(nw):
        tq.put(None)
    ps = [mp.Process(target=worker, args=(a.port + w, tq, rq, a.only, suites), daemon=True) for w in range(nw)]
    for p in ps:
        p.start()
    print("run_tests: %d tasks on %d emulators" % (len(tasks), nw), flush=True)
    done, got = 0, []
    try:
        while done < nw:
            r = rq.get()
            if r is None:
                done += 1
                continue
            got.append(r)
            for l in r["out"]:
                if "FAIL" in l:
                    print(l, flush=True)
        for p in ps:
            p.join()
    finally:                                        # never leave workers (and their emulators) behind
        for p in ps:
            if p.is_alive():
                p.terminate()
    got.sort(key=lambda r: r["idx"])
    results = dict(boot={}, lexer=[], bench=[], decl=[], exec=[], shell=[], e2e=[], e2e_corpus=[], tape=[])
    failed = sum(r["failed"] for r in got)
    extra = {}
    canary_rows = []
    walls = {}
    for r in got:
        walls[r["kind"]] = walls.get(r["kind"], 0) + r["wall"]
        extra.update(r.get("extra") or {})
        for suite, rows in r["rows"].items():
            if suite == "boot":
                for b in rows:
                    results["boot"][b["image"]] = dict(boot_tstates=b["boot_tstates"], checks=b["checks"])
            elif suite == "canary":
                canary_rows += rows
            else:
                results[suite] += rows
    results.update(extra)
    # ---- the report, suite by suite
    for r in got:
        if r["kind"] == "boot":
            for l in r["out"]:
                print(l)
    if "decl" in suites:
        dr = results["decl"]
        nerr = sum(1 for x in dr if x["ok"] and x["info"] and x["info"]["error"])
        print("decl: %d/%d cases pass (%d declaration cases, %d error cases)" % (
            sum(x["ok"] for x in dr), len(dr), sum(x["ok"] for x in dr) - nerr, nerr))
        for w in results.get("decl_ws", []):
            print("workspace: %-26s %5.1f B each   (%s)" % (w["what"], w["bytes_each"], w["detail"]))
    if "exec" in suites:
        for r in got:
            if r["kind"] == "execb":
                for l in r["out"]:
                    if not l.startswith("exec: FAIL"):
                        print(l)
        counts = {}
        lines = tstates = 0
        for x in results["exec"]:
            g = x.get("group") or x["case"].split(os.sep)[1]
            n, p_ = counts.get(g, (0, 0))
            counts[g] = (n + 1, p_ + x["ok"])
            if x["ok"] and x["info"] and not x["info"]["error"]:
                lines += x["info"]["lines"]
                tstates += x["info"]["compile_t"]
        for g, (n, p_) in sorted(counts.items()):
            print("exec %-8s %d/%d cases pass" % (g + ":", p_, n))
        if lines:
            results["compile_speed"] = dict(lines=lines, tstates=tstates, t_per_line=tstates / lines,
                                            ms_per_line=tstates / lines / 3528.0)
            print("compile speed: %d lines in %d T = %.0f T/line (%.2f ms/line at 3.528 MHz)" % (
                lines, tstates, tstates / lines, tstates / lines / 3528.0))
    if "lexer" in suites or "bench" in suites:
        for r in got:
            if r["kind"] == "lexer":
                for l in r["out"]:
                    if l.startswith("bench"):
                        print(l)
        if "lexer" in suites:
            print("lexer: %d/%d cases pass" % (sum(x["ok"] for x in results["lexer"]), len(results["lexer"])))
    if "shell" in suites:
        sr = results["shell"]
        print("shell: %d/%d cases pass" % (sum(x["ok"] for x in sr), len(sr)))
        for k, v in (results.get("typing") or {}).items():
            print("measured: keys %-16s %2d keys, mean %7d T, max %7d T, %d screen clears%s" % (
                k, v["keys"], v["mean"], v["max"], v["cls_keys"],
                ("   (V2: mean %d T, max %d T)" % (v["v2_mean"], v["v2_max"])) if "v2_mean" in v else ""))
    if "e2e" in suites:
        er, cr = results["e2e"], results["e2e_corpus"]
        typed = [x for x in er if x["case"].startswith("typed-")]
        print("e2e: %d/%d workflow cases pass (%d typed programs)" % (sum(x["ok"] for x in er), len(er), len(typed)))
        s = e2etest.summarise_corpus(cr)
        results["e2e_summary"] = s
        print("e2e: corpus through the shell's RUN: %d/%d pass; compile speed through RUN %s ms per line (%d lines, "
              "%d T); compile errors reported through RUN: %d numbers %s" % (
                  sum(x["ok"] for x in cr), len(cr), "%.2f" % s["ms_per_line"] if s["ms_per_line"] else "-",
                  s["lines"], s["tstates"], len(s["errors"]), s["errors"]))
        if not a.only:
            # every compile error class positions the cursor on its line through RUN (project_plan.md 8):
            # each number reported by a passing case (the corpus, and STRING TOO LONG's own case)
            seen = set(s["errors"]) | ({17} if any(x["ok"] for x in er if x["case"] == "diag-string-too-long") else set())
            missing = sorted(n for k, n in e2etest.gen_diag.messages() if k == "E" and n not in seen)
            results["e2e_summary"]["errors_missing"] = missing
            if missing:
                failed += 1
                print("e2e: FAIL compile errors never reported through RUN with the cursor checked: %s" % missing)
            else:
                print("e2e: every compile error number (%d) reported through RUN with the cursor on its line" % len(seen))
    if "tape" in suites:
        tr = sorted(results["tape"], key=lambda x: x["case"])
        print("tape: %d/%d cassette cases pass" % (sum(x["ok"] for x in tr), len(tr)))
        for x in tr:
            if x["ok"] and x.get("extra"):
                print("measured: tape %-22s %s" % (x["case"], x["extra"]))
    if "canary" in suites:
        canary_rows.sort(key=lambda r: r["case"])
        cs, line = canary.summary(canary_rows, walls.get("canary", 0))
        results["canary"] = cs
        with open(os.path.join(ROOT, "build", "canary.json"), "w") as f:
            json.dump(dict(summary=cs, cases=canary_rows), f, indent=1)
        print(line.replace("; %.0f s" % walls.get("canary", 0), "; %.0f s of emulator time" % walls.get("canary", 0)))
    results["failed"] = failed
    results["wall_s"] = round(time.time() - t_start, 1)
    results["task_wall_s"] = {k: round(v, 1) for k, v in walls.items()}
    with open(a.json, "w") as f:
        json.dump(results, f, indent=1)
    print("task time per kind (s): %s" % ", ".join("%s %.0f" % kv for kv in sorted(walls.items())))
    print("TOTAL: %s (%d failures), %.0f s on %d emulators" % ("PASS" if not failed else "FAIL", failed,
                                                               results["wall_s"], nw))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
