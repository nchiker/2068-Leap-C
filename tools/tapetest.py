#!/usr/bin/env python3
"""Leap-C cassette tests (project_plan.md Phase 7), suite `tape` of make test.

Every case runs the production ROM in ZEsarUX and moves real tape signals:
  - SAVE (the shell's, and tape_save from a running program) is captured at the MIC line: every
    `out (PORT_ULA), a` of HOME's STORAGE_SEND_BLOCK prints its T-state and level without stopping the
    machine (lcharness.Machine.tape_capture); tools/tapes.decode() turns the pulses back into blocks and
    measures every width, so the bytes and the timing on tape are both checked;
  - LOAD and VERIFY (and tape_load) read the EAR line through ZEsarUX's real-tape input (`realtape-open`):
    a captured SAVE played back exactly as the ROM timed it (the round trips), tapes synthesised with the
    stock ROM's timing and any fault built in (a bad checksum, a dropout, a truncated block, a bad version
    word, unsound records, a header longer than the room), and the host tool's .tap/.tzx through ZEsarUX's
    own conversion;
  - BREAK is the real CAPS SHIFT + SPACE held on the keyboard matrix (the tape routines test SPACE);
  - V2 (the reference ROM, built read-only from its tag: tools/v2ref.sh) and Leap-C exchange tapes made by
    each one's own SAVE: each refuses the other's with BAD TAPE VERSION and changes nothing.
After every shell command the editor's state is checked (the source, the cursor, the view, the paging
depth); the banking invariants (tools/memguard.py, with the tape-block ones) are armed through every
transfer. Synthesised tapes use the data block's stock pilot (2 s) for the header too, to keep the suite short;
the round trips and the host tapes keep the stock pilots.

Usage: tapetest.py [--port N] [substring ...]
"""
import argparse
import os
import struct
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2src                                                    # noqa: E402
import c2tape                                                   # noqa: E402
import exectest                                                 # noqa: E402
import lcharness                                                # noqa: E402
import memguard                                                 # noqa: E402
import tapes                                                    # noqa: E402
from lcharness import Machine, RET_SLOT                         # noqa: E402
from shelltest import Shell, ENTER, Z_CAPS, Z_SPACE, expect     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILOT = tapes.DATA_PILOT        # pilot pulses of the synthesised tapes (2 s: the receiver waits 1 s, then counts 256 cycles)
ROOM = 0xC000 - 0x7800          # the line store's room: LOAD's most
CASES = []
LONG = ("load-not-found", "roundtrip-large", "cross-version", "roundtrip", "load-fail-direct", "lib-load-results",
        "lib-cross-version", "lib-keep-unload", "lib-direct", "lib-fail-keeps", "lib-refused")  # (run first)

PROG = ["int main(void)", "{", '    puts("TAPE");', "    return 7;", "}"]
SRC_A = ["int f(int x)", "{", "    return x * 3;", "}", "int main(void)", "{", "    return f(4);", "}"]
SRC_B = ["// loaded from tape", "char *s = \"LOADED\";", "int main(void)", "{", "    puts(s);", "    return 9;",
         "}"]


def case(name, title):
    def deco(fn):
        CASES.append((name, title, fn))
        return fn
    return deco


# ===================================================================== helpers
def rec(lines):
    return c2src.records(lines)


def ptape(name, lines=None, data=None, htype=tapes.PROGRAM, version=tapes.LEAPC_VERSION, pilot=PILOT,
          length=None, **faults):
    """A tape file (header and data block) with the stock timing and short pilots; faults apply to the data
    block (tapes.Tape.block), `length` overrides the header's length, `bad_checksum` flips the data block's
    checksum."""
    payload = rec(lines) if data is None else bytes(data)
    hdr = tapes.framed(0x00, tapes.header(htype, name, len(payload) if length is None else length, version))
    body = bytearray(tapes.framed(0xFF, payload))
    if faults.pop("bad_checksum", False):
        body[-1] ^= 0x01
    t = tapes.Tape()
    t.block(hdr, pilot=pilot)
    t.block(bytes(body), pilot=pilot, **faults)
    return t


def join(*tps):
    t = tapes.Tape()
    for x in tps:
        t.runs += x.runs
    return t


def play(sh, tape, lead=1.5):
    """`tape` (a tapes.Tape or a file) as the EAR input from now on; the caller restores the editor next."""
    m = sh.m
    if isinstance(tape, tapes.Tape):
        path = os.path.join(m.snapdir, "case.rwa")
        tape.write_rwa(path, lead=lead)
    else:
        path = tape
    m.tape_insert(path)


def state(sh):
    m, S = sh.m, sh.S
    return dict(store=sh.store(), index=sh.index(), pos=m.w16(S("CUR_EDIT_POS")), view=m.w16(S("VIEW_TOP_INDEX")),
                depth=m.read(S("BANK_EXROM_DEPTH"), 1)[0], editor=sh.in_editor(),
                verify=m.read(S("STORAGE_VERIFY_MODE"), 1)[0], hook=m.w16(S("STORAGE_PROGRESS_HOOK")),
                dest=m.w16(S("TAPE_DEST")))


def neat(msg):
    return (msg[0].rstrip(), msg[1]) if isinstance(msg, tuple) else msg


def source_row(lines):
    n = len(rec(lines))
    return "SOURCE %d B  FREE %d B" % (n, ROOM - n)


def command(sh, text, maxi=400_000_000, invariants=True):
    """`text` typed on the append line and ENTER: the report (row 22 without its padding, row 23) and the
    rows shown; then a key, back to the editor."""
    memguard.arm(sh.m, invariants)
    try:
        for ch in text:
            sh.key(ord(ch))
        msg = sh.key(ENTER, maxi=maxi)
    finally:
        memguard.arm(sh.m, False)
    rows = sh.rows()
    sh.key(ord(" "))
    return neat(msg), rows


def command_to(sh, text, stops, n=1, maxi=400_000_000):
    """`text` and ENTER, then on to the n-th stop at one of `stops` (the invariants armed); the caller
    finishes with finish()."""
    m, S = sh.m, sh.S
    for ch in text:
        sh.key(ord(ch))
    memguard.arm(m, True)
    m.write(S("KBD_LASTK"), ENTER)
    m.write(S("KBD_KEYHIT"), 0xFF)
    m.cmd("cpu-step")
    for k in range(n):
        if k:
            m.cmd("cpu-step")
        pc = m.run_to(stops, maxi)
        if pc not in stops:
            raise RuntimeError("stopped at %04X before %s (%s)" % (pc, [hex(s) for s in stops], memguard.fired(m)))
    return pc


def finish(sh, maxi=400_000_000, on_message=None):
    try:
        msg = sh._wait(maxi, on_message=on_message)
    finally:
        memguard.arm(sh.m, False)
    rows = sh.rows()
    sh.key(ord(" "))
    return neat(msg), rows


def in_data(sh, dest, nbytes, chunk=20_000, limit=40_000_000):
    """Run until the data block's receiver is `nbytes` past `dest` (IX walks it)."""
    m = sh.m
    for _ in range(limit // chunk):
        m.run(chunk)
        ix = m.regs()["IX"]
        if dest + nbytes <= ix < dest + 0x4000:
            return True
    return False


def hold_break(m, down):
    for c in ((Z_CAPS, Z_SPACE) if down else (Z_SPACE, Z_CAPS)):
        m.cmd("send-keys-event %d %d" % (c, 1 if down else 0))


def capture(sh, text):
    """SAVE typed with the MIC signal captured: (report, rows, the status row at the first block, edges)."""
    m, S = sh.m, sh.S
    m.tape_capture(True)
    try:
        command_to(sh, text, [S("TAPE_BLOCK")])
        status = sh.rows()[23]
        msg, rows = finish(sh)
    finally:
        vals = m.tape_capture(False)
    return msg, rows, status, tapes.edges_from_capture(vals)


def blocks_of(edges):
    return tapes.decode(edges)


def widths_ok(bl):
    """The stock ROM's pulses (tapes.*_T), lengthened at most 16 T by contention (the ULA port's, and a data
    byte's read in $4000-$7FFF: the line store starts at $7800), never shortened by more than 2 T."""
    want = dict(pilot=tapes.PILOT_T, sync1=tapes.SYNC1_T, sync2=tapes.SYNC2_T, zero=tapes.ZERO_T, one=tapes.ONE_T)
    for b in bl:
        for k, (lo, hi) in b["widths"].items():
            if not (want[k] - 2 <= lo <= hi <= want[k] + 16):
                return False
    return True


def spans(bl):
    out = {}
    for b in bl:
        for k, (lo, hi) in b["widths"].items():
            a, z = out.get(k, (lo, hi))
            out[k] = (min(a, lo), max(z, hi))
    return out


# ===================================================================== the shell: round trip
@case("roundtrip", "SAVE \"hello\" of a typed program, captured at the MIC line: header (type 0, name, length, $8C00, "
                   "program length) and data (the line store) blocks with valid checksums and the stock pulses; NEW; "
                   "the captured signal played back: LOAD \"\" restores the source (cursor on the append line), "
                   "VERIFY \"hello\" passes; SAVING / LOADING / VERIFYING and the name on the status row meanwhile")
def roundtrip(sh):
    m, S = sh.m, sh.S
    sh.boot()
    for l in PROG:
        sh.type(l)
    st0 = state(sh)
    msg, rows, status, edges = capture(sh, 'SAVE "hello"')
    bl = blocks_of(edges)
    want = tapes.file_blocks(tapes.PROGRAM, "hello", rec(PROG))
    bad = []
    if msg != ("SAVED hello", source_row(PROG)) or rows[22:24] != list(msg):
        bad.append("save report %r rows %r" % (msg, rows[22:24]))
    if status != "SAVING hello":
        bad.append("status during SAVE %r" % status)
    if [b["data"] for b in bl] != want or not all(b["ok"] for b in bl):
        bad.append("blocks %r" % [b["data"][:24].hex() for b in bl])
    if not widths_ok(bl) or [b["pilot"] for b in bl] != [8063, 3222]:
        bad.append("pulses %r pilots %r" % ([b["widths"] for b in bl], [b["pilot"] for b in bl]))
    if state(sh) != st0:
        bad.append("state after SAVE %r" % state(sh))
    sh.type("new")
    tape = tapes.Tape.from_edges(edges)
    play(sh, tape)
    sh.boot()
    command_to(sh, 'LOAD ""', [S("TAPE_BLOCK")], n=2)
    loading = sh.rows()[23]
    msg, rows = finish(sh)
    st = state(sh)
    if msg != ("LOADED hello", source_row(PROG)) or loading != "LOADING hello":
        bad.append("load report %r status %r" % (msg, loading))
    if st["store"] != PROG or st["index"] != len(PROG) or st["pos"] != 0xFFFF or sh.rows()[:5] != PROG \
            or sh.rows()[23] != "LINE 6/5" or not st["editor"] or st["depth"] != 1 or st["dest"] or st["hook"]:
        bad.append("after LOAD %r rows %r" % (st, sh.rows()[:6] + sh.rows()[23:]))
    play(sh, tape)
    sh.load(PROG, len(PROG))
    command_to(sh, 'VERIFY "hello"', [S("TAPE_BLOCK")], n=2)
    verifying = sh.rows()[23]
    msg, rows = finish(sh)
    if msg != ("VERIFIED hello", source_row(PROG)) or verifying != "VERIFYING hello" or sh.store() != PROG \
            or state(sh)["verify"]:
        bad.append("verify %r status %r" % (msg, verifying))
    sh.extra = dict(widths=spans(bl), pilots=[b["pilot"] for b in bl],
                    bytes=[len(b["data"]) for b in bl], seconds=round((edges[-1][0] - edges[0][0]) / tapes.CPU_HZ, 2))
    return expect(not bad, "; ".join(bad))


@case("roundtrip-large", "an 8 KB program (64 lines of 124 characters): SAVE captured (one minute of tape), NEW, LOAD of "
                         "that signal: the source byte for byte, its pulses still the stock widths")
def roundtrip_large(sh):
    lines = ["// %02d %s" % (i, ("ABCDEFGHIJ" * 13)[:118]) for i in range(64)]
    sh.load(lines, len(lines))
    msg, rows, status, edges = capture(sh, 'SAVE "large"')
    bl = blocks_of(edges)
    want = tapes.file_blocks(tapes.PROGRAM, "large", rec(lines))
    ok1 = msg == ("SAVED large", source_row(lines)) and [b["data"] for b in bl] == want and widths_ok(bl)
    play(sh, tapes.Tape.from_edges(edges))
    sh.boot()
    msg2, rows2 = command(sh, 'LOAD ""')
    seconds = round((edges[-1][0] - edges[0][0]) / tapes.CPU_HZ, 1)
    sh.extra = dict(bytes=len(rec(lines)), seconds=seconds, widths=spans(bl))
    return expect(ok1 and msg2 == ("LOADED large", source_row(lines)) and sh.store() == lines,
                  "save %r (%d blocks, widths %r) load %r" % (msg, len(bl), spans(bl), msg2))


@case("verify-fails", "VERIFY against a source that differs in one character, that has one line more, or one line "
                      "less than the tape: VERIFY FAILED, nothing written, the editor as it was")
def verify_fails(sh):
    bad = []
    changed = PROG[:2] + ['    puts("TAPF");'] + PROG[3:]
    for src in (changed, PROG + ["// more"], PROG[:-1]):
        play(sh, ptape("hello", PROG))
        sh.load(src, len(src))
        st0 = state(sh)
        msg, rows = command(sh, 'VERIFY "hello"')
        if msg != ("VERIFY FAILED", source_row(src)) or state(sh) != st0:
            bad.append("%d lines: %r %r" % (len(src), msg, state(sh)))
    return expect(not bad, "; ".join(bad))


@case("load-named", "a tape with two programs: LOAD \"hello\" skips the first (another name) and loads the second; "
                    "LOAD \"\" loads the first; any case, no space before the quote")
def load_named(sh):
    bad = []
    tape = join(ptape("other", SRC_A), ptape("hello", SRC_B))
    for cmd, want, name in (('LOAD "hello"', SRC_B, "hello"), ('load""', SRC_A, "other")):
        play(sh, tape)
        sh.load(PROG, len(PROG))
        msg, rows = command(sh, cmd)
        st = state(sh)
        if msg != ("LOADED " + name, source_row(want)) or st["store"] != want or st["index"] != len(want):
            bad.append("%s: %r %r" % (cmd, msg, st))
    return expect(not bad, "; ".join(bad))


@case("load-staged-ok", "LOAD over a source: the program arrives above the source (TAPE_DEST = PROG_END) and then "
                        "replaces it; it RUNs")
def load_staged_ok(sh):
    m, S = sh.m, sh.S
    play(sh, ptape("b", SRC_B))
    sh.load(SRC_A, len(SRC_A))
    command_to(sh, 'LOAD "b"', [S("TAPE_BLOCK")], n=2)
    ix_dest = m.w16(S("TAPE_DEST"))
    msg, rows = finish(sh)
    ok1 = msg == ("LOADED b", source_row(SRC_B)) and sh.store() == SRC_B and ix_dest == 0x7800 + len(rec(SRC_A))
    msg2, rows2 = command(sh, "run")
    return expect(ok1 and msg2[0] == "EXIT 9" and rows2[0] == "LOADED",
                  "load %r staged at %04X; run %r %r" % (msg, ix_dest, msg2, rows2[0]))


@case("load-fail-keeps-source", "LOAD failures with a source in memory: a data block with a bad checksum, a dropout, "
                                "a truncated block, unsound records (checksum valid), BREAK in the data block: each "
                                "LOAD FAILED (BREAK) with the source and the editor exactly as before")
def load_fail_keeps(sh):
    m, S = sh.m, sh.S
    bad = []
    rb = bytearray(rec(SRC_B))
    rb[2 + 19] = 0x20                           # the first record's CR becomes a space: records unsound
    tapes_ = [("bad checksum", ptape("b", SRC_B, bad_checksum=True), "LOAD FAILED"),
              ("dropout", ptape("b", SRC_B, dropout=(20, 4)), "LOAD FAILED"),
              ("truncated", ptape("b", SRC_B, truncate_after=30), "LOAD FAILED"),
              ("records", ptape("b", data=bytes(rb)), "LOAD FAILED")]
    for what, tape, want in tapes_:
        play(sh, tape)
        sh.load(SRC_A, len(SRC_A))
        st0 = state(sh)
        msg, rows = command(sh, 'LOAD "b"')
        if msg != (want, source_row(SRC_A)) or state(sh) != st0:
            bad.append("%s: %r %r" % (what, msg, state(sh)))
    play(sh, ptape("b", SRC_B))                 # BREAK once 20 bytes of the data block have arrived
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    command_to(sh, 'LOAD "b"', [S("TAPE_BLOCK")], n=2)
    dest = m.w16(S("TAPE_DEST"))
    got = in_data(sh, dest, 20)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    if not got or msg != ("BREAK", source_row(SRC_A)) or state(sh) != st0:
        bad.append("break in data (reached %s): %r %r" % (got, msg, state(sh)))
    return expect(not bad, "; ".join(bad))


@case("load-fail-direct", "a program too big to arrive above the source goes straight into the line store: it loads "
                          "whole; with a bad checksum, the source cannot be trusted and is empty (V2's known-safe state)")
def load_fail_direct(sh):
    big = ["// %s" % ("x" * 120)] * 140             # 17,220 B in the line store
    newp = ["// %d %s" % (i, "y" * 100) for i in range(14)] + SRC_B   # ~1.6 KB: does not fit above it
    bad = []
    play(sh, ptape("b", newp))
    sh.load(big, len(big))
    msg, rows = command(sh, 'LOAD "b"')
    if msg != ("LOADED b", source_row(newp)) or sh.store() != newp:
        bad.append("direct load %r" % (msg,))
    play(sh, ptape("b", newp, bad_checksum=True))
    sh.load(big, len(big))
    msg, rows = command(sh, 'LOAD "b"')
    st = state(sh)
    if msg != ("LOAD FAILED", source_row([])) or st["store"] != [] or st["index"] != 0 or sh.rows()[23] != "LINE 1/0":
        bad.append("direct fail %r %r" % (msg, st))
    return expect(not bad, "; ".join(bad))


@case("load-break-direct", "(Phase 10) BREAK during the data block of a LOAD that goes straight into the line store: "
                           "BREAK, and the source, partly overwritten, is empty (it kept the overwritten source)")
def load_break_direct(sh):
    m, S = sh.m, sh.S
    big = ["// %s" % ("x" * 120)] * 140             # 17,220 B in the line store
    newp = ["// %d %s" % (i, "y" * 100) for i in range(14)] + SRC_B   # ~1.6 KB: does not fit above it
    play(sh, ptape("b", newp))
    sh.load(big, len(big))
    command_to(sh, 'LOAD "b"', [S("TAPE_BLOCK")], n=2)
    dest = m.w16(S("TAPE_DEST"))
    got = in_data(sh, 0x7800, 20)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    st = state(sh)
    ok = got and dest == 0 and msg == ("BREAK", source_row([])) and st["store"] == [] and st["index"] == 0 \
        and sh.rows()[23] == "LINE 1/0"
    return expect(ok, "reached %s dest %04X: %r %r" % (got, dest, msg, st))


@case("load-refused", "tapes LOAD refuses at the header, writing nothing: version words $8101 (V2), $8000 (stock, no "
                      "autostart), $000A (stock, autostart line 10), $8C01 (a later Leap-C minor), $8D00: BAD TAPE "
                      "VERSION; a length beyond the line store's room: LOAD FAILED; VERIFY of a V2 tape: BAD TAPE VERSION")
def load_refused(sh):
    bad = []
    cases = [(v, 'LOAD "b"', ptape("b", SRC_B, version=v), "BAD TAPE VERSION") for v in (0x8101, 0x8000, 0x000A, 0x8C01, 0x8D00)]
    cases.append(("too long", 'LOAD "b"', ptape("b", SRC_B, length=ROOM + 1), "LOAD FAILED"))
    cases.append(("verify v2", 'VERIFY "b"', ptape("b", SRC_A, version=0x8101), "BAD TAPE VERSION"))
    for what, cmd, tape, want in cases:
        play(sh, tape)
        sh.load(SRC_A, len(SRC_A))
        st0 = state(sh)
        msg, rows = command(sh, cmd)
        if msg != (want, source_row(SRC_A)) or state(sh) != st0:
            bad.append("%s: %r %r" % (what if isinstance(what, str) else "$%04X" % what, msg, state(sh)))
    return expect(not bad, "; ".join(bad))


@case("load-break-search", "BREAK while LOAD searches (no tape): BREAK, the source and the editor as before")
def load_break_search(sh):
    m, S = sh.m, sh.S
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    command_to(sh, 'LOAD ""', [S("TAPE_BLOCK")])
    m.run(200_000)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    return expect(msg == ("BREAK", source_row(SRC_A)) and state(sh) == st0, "%r %r" % (msg, state(sh)))


@case("load-not-found", "LOAD \"hello\" with only a data tape of that name (another type, skipped) on it: the search "
                        "gives up after its 15 attempts, LOAD FAILED, the source as before")
def load_not_found(sh):
    play(sh, ptape("hello", data=b"DATA" * 8, htype=tapes.DATA))
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    t0 = time.time()
    msg, rows = command(sh, 'LOAD "hello"', maxi=600_000_000, invariants=False)   # (armed, they triple the
                                                                                  # 2 minutes of searching)
    sh.extra = dict(wall=round(time.time() - t0, 1))
    return expect(msg == ("LOAD FAILED", source_row(SRC_A)) and state(sh) == st0, "%r %r" % (msg, state(sh)))


# ===================================================================== the shell: SAVE's edges
@case("save-break", "BREAK held from SAVE's first block: the header stops after its first byte, no data block is "
                    "sent (TAPE_ABORT), BREAK is reported; the source as before")
def save_break(sh):
    m, S = sh.m, sh.S
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    m.tape_capture(True)
    try:
        command_to(sh, 'SAVE "a"', [S("TAPE_BLOCK")])
        hold_break(m, True)
        try:
            msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
        finally:
            hold_break(m, False)
    finally:
        vals = m.tape_capture(False)
    bl = blocks_of(tapes.edges_from_capture(vals))
    ok = msg == ("BREAK", source_row(SRC_A)) and state(sh) == st0 and len(bl) == 1 and len(bl[0]["data"]) <= 2
    return expect(ok, "%r %r blocks %r" % (msg, state(sh), [b["data"].hex() for b in bl]))


@case("save-commands", "the tape commands' words: BAD NAME (SAVE \"\", 11 characters, no closing quote, more after it; "
                       "LOAD and VERIFY the same), NO PROGRAM (SAVE of an empty source); SAVE, LOAD or VERIFY without a "
                       "quote, and C lines starting with those words, are source")
def save_commands(sh):
    bad = []
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    for cmd in ('SAVE ""', 'SAVE "abcdefghijk"', 'SAVE "abc', 'SAVE "abc" x', 'LOAD "abcdefghijk"', 'VERIFY "a" 1',
                'load "x', 'verify "abcdefghijk"'):
        msg, rows = command(sh, cmd, invariants=False)
        if msg != ("BAD NAME", source_row(SRC_A)) or state(sh) != st0:
            bad.append("%s: %r %r" % (cmd, msg, state(sh)))
    sh.boot()
    msg, rows = command(sh, 'save "x"', invariants=False)
    if msg != ("NO PROGRAM", source_row([])):
        bad.append("empty: %r" % (msg,))
    sh.boot()
    lines = ["SAVE", "load(x);", "verify = 1;", "Save x;"]
    for l in lines:
        sh.type(l)
    if sh.store() != lines:
        bad.append("not commands: %r" % sh.store())
    return expect(not bad, "; ".join(bad))


@case("save-typed-matrix", "SAVE \"k\" typed on the keyboard matrix (SYMBOL SHIFT + P for the quotes): SAVED k, and the "
                           "tape's name is the typed one")
def save_typed(sh):
    m, S = sh.m, sh.S
    sh.load(PROG, len(PROG))
    m.tape_capture(True)
    try:
        for ch in 'SAVE "k"':
            sh.press(ch)
        memguard.arm(m, True)
        try:
            msg = neat(sh.press_code([129], maxi=400_000_000))    # ENTER on the matrix (shelltest.Z_ENTER)
        finally:
            memguard.arm(m, False)
        sh.key(ord(" "))
    finally:
        vals = m.tape_capture(False)
    bl = blocks_of(tapes.edges_from_capture(vals))
    ok = msg == ("SAVED k", source_row(PROG)) and [b["data"] for b in bl] == tapes.file_blocks(0, "k", rec(PROG))
    return expect(ok, "%r %r" % (msg, [b["data"][:16].hex() for b in bl]))


# ===================================================================== host tapes
@case("host-tape", "tools/c2tape.py: the .tap and .tzx of a C file load through ZEsarUX's own tape conversion "
                   "(stock timing and pilots), RUN as expected; its blocks are exactly what the ROM's SAVE of the same "
                   "source sends (captured)")
def host_tape(sh):
    m = sh.m
    lines = ["// a host-built tape", "int sq(int x) { return x * x; }", "int main(void)", "{",
             '    printf("%d", sq(12));', "    return sq(3);", "}"]
    text = "\n".join(lines) + "\n"
    bad = []
    for ext in (".tap", ".tzx"):
        path = os.path.join(m.snapdir, "host" + ext)
        blocks = c2tape.program_blocks(text, "host")
        open(path, "wb").write(tapes.tap(blocks) if ext == ".tap" else tapes.tzx(blocks))
        play(sh, path)
        sh.boot()
        msg, rows = command(sh, 'LOAD ""')
        if msg != ("LOADED host", source_row(lines)) or sh.store() != lines:
            bad.append("%s: %r %r" % (ext, msg, sh.store()[:2]))
            continue
        msg, rows = command(sh, "run")
        if msg[0] != "EXIT 9" or rows[0] != "144":
            bad.append("%s run: %r %r" % (ext, msg, rows[0]))
    sh.load(lines, len(lines))
    msg, rows, status, edges = capture(sh, 'SAVE "host"')
    got = [b["data"] for b in blocks_of(edges)]
    if got != c2tape.program_blocks(text, "host"):
        bad.append("ROM SAVE %r != c2tape" % [g[:16].hex() for g in got])
    return expect(not bad, "; ".join(bad))


# ===================================================================== V2 and Leap-C
class V2Machine(Machine):
    """The V2 reference ROM (tools/v2ref.sh: build/v2ref/) on its own emulator, driven like the Leap-C one."""

    def __init__(self, port):
        d = os.path.join(ROOT, "build", "v2ref")
        if not os.path.exists(os.path.join(d, "ts2068rom_zesarux.bin")):
            r = os.system(os.path.join(ROOT, "tools", "v2ref.sh") + " > /dev/null")
            assert r == 0, "tools/v2ref.sh failed"
        self.build = d
        self.port = port
        self.S = lcharness.load_syms(os.path.join(d, "test_basic.sym"), os.path.join(d, "exrom.sym"))
        self.rom = os.path.join(d, "ts2068rom_zesarux.bin")
        self.snapdir = os.path.join(d, "snap_%d" % port)
        os.makedirs(self.snapdir, exist_ok=True)
        self.snap = os.path.join(self.snapdir, "boot.zsf")
        self.proc = self.c = None
        self.glyphs = None
        self.boot = {}

    def _glyph_table(self):
        return {}

    def store(self):
        a, e = self.sym("PROG_AREA_START"), self.w16(self.sym("PROG_END"))
        return self.read(a, e - a)

    def key(self, code, maxi=600_000_000):
        """A key through V2's latch, then on to its next key wait; the message V2 shows on the way."""
        S = self.sym
        self.write(S("KBD_LASTK"), code)
        self.write(S("KBD_KEYHIT"), 0xFF)
        self.cmd("cpu-step")
        msg = None
        pc = self.run_to([S("V2_SHOW_MESSAGE"), S("IO_READ_KEY")], maxi)
        if pc == S("V2_SHOW_MESSAGE"):
            msg = self.read(self.regs()["HL"], 33).split(b"\0")[0].decode("latin-1")
            self.cmd("cpu-step")
            pc = self.run_to([S("IO_READ_KEY")], maxi)
        if pc != S("IO_READ_KEY"):
            raise RuntimeError("V2: no key wait (PC=%04X)" % pc)
        return msg

    def type(self, text):
        for ch in text:
            self.key(ord(ch))
        return self.key(ENTER)


@case("cross-version", "BAD TAPE VERSION in both directions with each ROM's own tapes: V2 (the reference ROM) SAVEs a "
                       "program ($8101) and Leap-C refuses it; Leap-C SAVEs one ($8C00) and V2 refuses it; neither "
                       "writes anything")
def cross_version(sh):
    m, S = sh.m, sh.S
    bad = []
    sh.load(SRC_A, len(SRC_A))
    msg, rows, status, l_edges = capture(sh, 'SAVE "leapc"')
    lb = blocks_of(l_edges)
    if [b["data"] for b in lb] != tapes.file_blocks(0, "leapc", rec(SRC_A)):
        bad.append("Leap-C SAVE %r" % (msg,))
    v2 = V2Machine(m.port + 40)
    try:
        v2.start()
        v2_prog = c2src.records(["PRINT 42"])
        v2.put_store(v2_prog)
        v2.cmd("snapshot-save " + os.path.join(v2.snapdir, "prog.zsf"))
        v2.tape_capture(True)
        try:
            vmsg = v2.type('SAVE "v2prog"')
        finally:
            vals = v2.tape_capture(False)
        vb = blocks_of(tapes.edges_from_capture(vals))
        hdr = vb[0]["data"] if vb else b""
        if vmsg != "SAVED" or len(vb) != 2 or hdr[1] != 0 or hdr[12:14] != bytes([len(v2_prog) & 255, len(v2_prog) >> 8]) \
                or hdr[14:16] != struct.pack("<H", tapes.V2_VERSION) or vb[1]["data"][1:-1] != v2_prog:
            bad.append("V2 SAVE %r blocks %r" % (vmsg, [b["data"][:20].hex() for b in vb]))
        path = os.path.join(v2.snapdir, "leapc.rwa")
        tapes.Tape.from_edges(l_edges).write_rwa(path, lead=1.5)
        v2.tape_insert(path)
        v2.cmd("snapshot-load " + os.path.join(v2.snapdir, "prog.zsf"))
        v2._enable_bp()
        before = v2.store()
        vmsg = v2.type('LOAD ""')
        if vmsg != "BAD TAPE VERSION" or v2.store() != before:
            bad.append("V2 LOAD of a Leap-C tape: %r, program %s" % (vmsg, "kept" if v2.store() == before else "changed"))
    finally:
        v2.stop()
    play(sh, tapes.Tape.from_edges(tapes.edges_from_capture(vals)))
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    msg, rows = command(sh, 'LOAD ""')
    if msg != ("BAD TAPE VERSION", source_row(SRC_A)) or state(sh) != st0:
        bad.append("Leap-C LOAD of a V2 tape: %r %r" % (msg, state(sh)))
    return expect(not bad, "; ".join(bad))


# ===================================================================== the library
def lib_run(sh, lines, tape=None, capture_save=False, **kw):
    """Compile and run `lines` (exectest, the banking invariants armed) with `tape` playing; with
    capture_save, the MIC signal's blocks too. Returns (res, blocks); the captured edges in sh.edges."""
    m = sh.m
    if tape is not None:
        play(sh, tape)
    m.restore()
    if capture_save:
        m.tape_capture(True)
    try:
        res = exectest.compile_and_run(m, lines, maxi=400_000_000, invariants=True, restore=False, **kw)
    finally:
        vals = m.tape_capture(False) if capture_save else []
    sh.edges = tapes.edges_from_capture(vals)
    return res, blocks_of(sh.edges) if capture_save else None


def glob_addr(res, name):
    return [e for e in res.globals if e.name == name][0].val


@case("lib-save", "tape_save from image region 1 (chunk 6, the EXROM mapped there for the header logic) and from the "
                  "screen: data tapes (type 3, the names, the lengths, $8C00) holding exactly those bytes, captured at "
                  "the MIC line; the program continues")
def lib_save(sh):
    m = sh.m
    lines = ['char c6[24] = "SAVED FROM CHUNK SIX!";', "int main(void)", "{", '    at(0, 0); print("SCREEN");',
             '    tape_save("c6", c6, 22);', '    tape_save("screen", (char *)0x4000, 32);', "    return c6[0];", "}"]
    res, bl = lib_run(sh, lines, capture_save=True)
    a = glob_addr(res, "c6")
    want = tapes.file_blocks(tapes.DATA, "c6", b"SAVED FROM CHUNK SIX!\0")
    scr = [b["data"] for b in bl][3][1:-1] if len(bl) == 4 else b""
    ok = (res.ran and res.hl == ord("S") and not res.violation and 0xC000 <= a < 0xE000 and len(bl) == 4
          and [b["data"] for b in bl][:2] == want and all(b["ok"] for b in bl)
          and [b["data"] for b in bl][2] == tapes.framed(0, tapes.header(tapes.DATA, "screen", 32)) and len(scr) == 32
          and scr == m.read(0x4000, 32))
    return expect(ok, "ran %s hl %r viol %r c6 %04X blocks %r" % (res.ran, res.hl, res.violation, a,
                                                                 [b["data"][:12].hex() for b in bl]))


@case("lib-load-places", "tape_load into image region 1 (chunk 6), into $E000 (region 2) and into the heap from a "
                         "running program: the data byte for byte, the lengths returned; chunk 6 is RAM while the data "
                         "block arrives (the invariants)")
def lib_load_places(sh):
    m = sh.m
    d = [bytes((i * k + 5) & 255 for i in range(n)) for k, n in ((3, 100), (7, 60), (11, 200))]
    tape = join(ptape("c6", data=d[0], htype=tapes.DATA), ptape("e000", data=d[1], htype=tapes.DATA),
                ptape("heap", data=d[2], htype=tapes.DATA))
    lines = ["char buf[100];", "char *p;", "int r[3];", "int main(void)", "{", '    r[0] = tape_load("c6", buf, 100);',
             '    r[1] = tape_load("e000", (char *)0xE000, 60);', "    p = malloc(200);",
             '    r[2] = tape_load("heap", p, 200);', "    return r[0] + r[1] + r[2];", "}"]
    res, _ = lib_run(sh, lines, tape)
    b, pa, ra = glob_addr(res, "buf"), glob_addr(res, "p"), glob_addr(res, "r")
    c6 = exectest.read_chunk6(m)
    p = m.w16(pa)
    rr = struct.unpack("<3h", m.read(ra, 6)) if ra < 0xC000 or ra >= 0xE000 else \
        struct.unpack("<3h", c6[ra - 0xC000:ra - 0xC000 + 6])
    got = [c6[b - 0xC000:b - 0xC000 + 100] if 0xC000 <= b < 0xE000 else m.read(b, 100), m.read(0xE000, 60), m.read(p, 200)]
    ok = res.ran and not res.violation and res.hl == 360 and rr == (100, 60, 200) and got == d and 0xC000 <= b < 0xE000
    return expect(ok, "ran %s hl %r viol %r r %r buf %04X p %04X match %r" % (
        res.ran, res.hl, res.violation, rr, b, p, [g == w for g, w in zip(got, d)]))


@case("lib-load-results", "tape_load's results on one tape: \"\" takes the first data tape (skipping a program tape); "
                          "-1 for a tape longer than max (nothing written), -3 for a V2 version word (nothing written), "
                          "-2 for a bad checksum (written in part), the length for a good one")
def lib_load_results(sh):
    m = sh.m
    first, good = b"FIRST-ONE", bytes(range(50))
    tape = join(ptape("prog", SRC_A), ptape("first", data=first, htype=tapes.DATA),
                ptape("big", data=bytes(200), htype=tapes.DATA),
                ptape("v2", data=b"V2" * 10, htype=tapes.DATA, version=tapes.V2_VERSION),
                ptape("bad", data=b"BADBADBAD" * 4, htype=tapes.DATA, bad_checksum=True),
                ptape("good", data=good, htype=tapes.DATA))
    lines = ["int r[5];", "char b0[20], b1[100], b2[100], b3[100], b4[100];", "int main(void)", "{",
             "    memset(b1, 0x55, 100); memset(b2, 0x55, 100); memset(b3, 0x55, 100);",
             '    r[0] = tape_load("", b0, 20);', '    r[1] = tape_load("big", b1, 100);',
             '    r[2] = tape_load("v2", b2, 100);', '    r[3] = tape_load("bad", b3, 100);',
             '    r[4] = tape_load("good", b4, 100);', "    return 0;", "}"]
    res, _ = lib_run(sh, lines, tape)
    c6 = exectest.read_chunk6(m)

    def mem(name, n):
        a = glob_addr(res, name)
        return c6[a - 0xC000:a - 0xC000 + n] if 0xC000 <= a < 0xE000 else m.read(a, n)
    rr = struct.unpack("<5h", mem("r", 10))
    ok = (res.ran and not res.violation and rr == (len(first), -1, -3, -2, len(good)) and mem("b0", 9) == first
          and mem("b1", 100) == b"\x55" * 100 and mem("b2", 100) == b"\x55" * 100 and mem("b3", 100) != b"\x55" * 100
          and mem("b4", 50) == good)
    return expect(ok, "ran %s viol %r results %r" % (res.ran, res.violation, rr))


@case("lib-roundtrip", "a program tape_saves 300 bytes from chunk 6 (captured); a second program tape_loads that "
                       "signal into the heap and finds them equal (memcmp), through the shell's RUN")
def lib_roundtrip(sh):
    m = sh.m
    saver = ["char d[300];", "int main(void)", "{", "    int i;", "    for (i = 0; i < 300; i++) d[i] = i * 13 + 1;",
             '    tape_save("rt", d, 300);', "    return 0;", "}"]
    res, bl = lib_run(sh, saver, capture_save=True)
    data = bytes((i * 13 + 1) & 255 for i in range(300))
    ok1 = res.ran and len(bl) == 2 and bl[1]["data"][1:-1] == data and all(b["ok"] for b in bl)
    loader = ["int main(void)", "{", "    char *p = malloc(300), *q = malloc(300);", "    int i;",
              "    for (i = 0; i < 300; i++) q[i] = i * 13 + 1;", '    if (tape_load("rt", p, 300) != 300) return 1;',
              "    return memcmp(p, q, 300) ? 2 : 3;", "}"]
    play(sh, tapes.Tape.from_edges(sh.edges))      # the signal exactly as the ROM sent it
    sh.load(loader, len(loader))
    msg, rows = command(sh, "run")
    return expect(ok1 and msg[0] == "EXIT 3", "save ran %s blocks %d; load %r" % (res.ran, len(bl), msg))


@case("lib-break-data", "BREAK during tape_load's data block (into chunk 6) ends the program with BREAK at the line of "
                        "the function that called it, through the shell's RUN: the report, the editor intact")
def lib_break(sh):
    m, S = sh.m, sh.S
    lines = ["char buf[600];", "int load(void)", "{", '    return tape_load("big", buf, 600);', "}", "int main(void)",
             "{", "    return load();", "}"]
    play(sh, ptape("big", data=bytes(range(256)) * 2, htype=tapes.DATA))
    sh.load(lines, len(lines))
    command_to(sh, "run", [S("TAPE_BLOCK")], n=2)
    got = in_data(sh, m.regs()["IX"], 30)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    st = state(sh)
    return expect(got and msg == ("BREAK", "LINE 2") and st["store"] == lines and st["depth"] == 1,
                  "reached %s %r %r" % (got, msg, st))


@case("lib-stack", "tape_load's stack: its deepest byte below the call's first argument, measured over a whole "
                   "transfer (the interrupts between the blocks included), within the 40 B a library routine may use "
                   "plus the IM 1 handler's 18 (include/leapc_layout.inc)")
def lib_stack(sh):
    m, S = sh.m, sh.S
    lines = ["char buf[40];", "int main(void)", "{", '    return tape_load("s", buf, 40);', "}"]
    play(sh, ptape("s", data=bytes(range(40)), htype=tapes.DATA))
    m.restore()
    res = exectest.compile_and_run(m, lines, run=False, restore=False)
    assert res.errnum == 0
    m.write(lcharness.STOP_ADDR, b"\x18\xFE")
    m.write(RET_SLOT, struct.pack("<H", lcharness.STOP_ADDR))
    m.setreg("SP", RET_SLOT)
    m.setreg("PC", S("RT_RUN"))
    assert m.run_to([S("LIB_TAPE_LOAD")], 50_000_000) == S("LIB_TAPE_LOAD")
    sp = m.regs()["SP"]
    m.write(0xF800, bytes([0xA5]) * (sp - 0xF800))
    pc = m.run_to([lcharness.STOP_ADDR], 400_000_000)
    d = m.read(0xF800, sp - 0xF800)
    low = next(0xF800 + i for i, x in enumerate(d) if x != 0xA5)
    depth = sp + 2 - low                          # below the first argument (SP + 2 at the entry)
    sh.extra = dict(stack_bytes=depth)
    return expect(pc == lcharness.STOP_ADDR and m.regs()["HL"] == 40 and depth <= 40 + 18,
                  "pc %04X hl %d depth %d" % (pc, m.regs()["HL"], depth))


# ===================================================================== the loaded library (Phase 10)
LX_TYPE = 4                                         # include/leapc_lib.inc: V2's package tapes
LIB_PROG = ["int main(void)", "{", "    return t_args(1, 2, 3);", "}"]


def lib_image(name):
    return open(os.path.join(lcharness.LIBS, name + ".bin"), "rb").read()


def ltape(name, lib=None, version=None, pilot=PILOT, **kw):
    """The library tape of build/libs/LIB.bin named `name`, as tools/lib2tape.py makes it (its version word the
    image's magic and ABI unless given), with short pilots and any fault of ptape()."""
    img = lib_image(lib or name)
    return ptape(name, data=img, htype=LX_TYPE, version=(img[0] << 8 | img[1]) if version is None else version,
                 pilot=pilot, **kw)


def lib_state(sh):
    m, S = sh.m, sh.S
    return dict(loaded=m.read(S("LIB_LOADED"), 1)[0], region3=m.read(0xF400, 0x400))


def lib_report(name, n, lines):
    return ("LIBRARY %s: %d FUNCTIONS" % (name, n), source_row(lines))


def type_lines(sh, lines):
    """NEW, then `lines` typed (the library stays loaded: a restore would unload it)."""
    sh.type("NEW")
    for l in lines:
        sh.type(l)


@case("lib-load", "LIB \"testlib\" from tools/lib2tape.py's own .tap blocks played as the tape signal: the library "
                  "arrives above the source (staged), then moves into image region 3, byte for byte; LIBRARY testlib: 24 "
                  "FUNCTIONS; the source and the editor as before; then NEW, a program typed and RUN binds its function")
def lib_load(sh):
    m, S = sh.m, sh.S
    t = tapes.Tape()
    for b in tapes.read_tap(open(os.path.join(lcharness.LIBS, "testlib.tap"), "rb").read()):
        t.block(b, pilot=PILOT)
    play(sh, t)
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    command_to(sh, 'LIB "testlib"', [S("TAPE_BLOCK")], n=2)
    dest = m.w16(S("TAPE_DEST"))
    msg, rows = finish(sh)
    img = lib_image("testlib")
    ls = lib_state(sh)
    bad = []
    if msg != lib_report("testlib", 24, SRC_A) or state(sh) != st0:
        bad.append("LIB %r %r" % (msg, state(sh)))
    if ls["loaded"] != 0xF4 or ls["region3"][:len(img)] != img or dest != 0x7800 + len(rec(SRC_A)):
        bad.append("loaded %02X, image %s, staged at %04X" % (ls["loaded"], ls["region3"][:len(img)] == img, dest))
    type_lines(sh, LIB_PROG)
    msg2, rows2 = command(sh, "run")
    if msg2[0] != "EXIT 123":
        bad.append("run %r" % (msg2,))
    return expect(not bad, "; ".join(bad))


@case("lib-direct", "LIB with no room above the source: the library goes straight into image region 3 and loads whole; "
                    "with a bad checksum or BREAK in its data block, LOAD FAILED or BREAK and no library is loaded (the "
                    "region was written)")
def lib_direct(sh):
    m, S = sh.m, sh.S
    big = ["// %s" % ("x" * 120)] * 143             # 18,018 B in the line store: 414 B above it
    bad = []
    img = lib_image("testlib")
    play(sh, ltape("testlib"))
    sh.load(big, len(big))
    msg, rows = command(sh, 'LIB "testlib"')
    ls = lib_state(sh)
    if msg != lib_report("testlib", 24, big) or ls["loaded"] != 0xF4 or ls["region3"][:len(img)] != img:
        bad.append("direct %r loaded %02X" % (msg, ls["loaded"]))
    play(sh, ltape("testlib", bad_checksum=True))
    sh.load(big, len(big))
    m.lib_load("tiny")
    msg, rows = command(sh, 'LIB "testlib"')
    if msg != ("LOAD FAILED", source_row(big)) or lib_state(sh)["loaded"] != 0:
        bad.append("checksum %r loaded %02X" % (msg, lib_state(sh)["loaded"]))
    play(sh, ltape("testlib"))
    sh.load(big, len(big))
    m.lib_load("tiny")
    command_to(sh, 'LIB "testlib"', [S("TAPE_BLOCK")], n=2)
    got = in_data(sh, 0xF400, 20)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    if not got or msg != ("BREAK", source_row(big)) or lib_state(sh)["loaded"] != 0:
        bad.append("break (reached %s) %r loaded %02X" % (got, msg, lib_state(sh)["loaded"]))
    return expect(not bad, "; ".join(bad))


@case("lib-fail-keeps", "LIB failures that write nothing into image region 3 keep the library loaded before them: a "
                        "staged data block with a bad checksum, BREAK in a staged data block, BREAK while it searches")
def lib_fail_keeps(sh):
    m, S = sh.m, sh.S
    bad = []
    for what, tape in (("checksum", ltape("testlib", bad_checksum=True)), ("dropout", ltape("testlib", dropout=(30, 4)))):
        play(sh, tape)
        sh.load(SRC_A, len(SRC_A))
        tiny = m.lib_load("tiny")
        st0 = state(sh)
        msg, rows = command(sh, 'LIB "testlib"')
        ls = lib_state(sh)
        if msg != ("LOAD FAILED", source_row(SRC_A)) or ls["loaded"] != 0xF4 or ls["region3"][:len(tiny)] != tiny \
                or state(sh) != st0:
            bad.append("%s %r loaded %02X" % (what, msg, ls["loaded"]))
    play(sh, ltape("testlib"))
    sh.load(SRC_A, len(SRC_A))
    tiny = m.lib_load("tiny")
    command_to(sh, 'LIB "testlib"', [S("TAPE_BLOCK")], n=2)
    dest = m.w16(S("TAPE_DEST"))
    got = in_data(sh, dest, 20)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    ls = lib_state(sh)
    if not got or msg != ("BREAK", source_row(SRC_A)) or ls["loaded"] != 0xF4 or ls["region3"][:len(tiny)] != tiny:
        bad.append("break in data (reached %s) %r loaded %02X" % (got, msg, ls["loaded"]))
    sh.load(SRC_A, len(SRC_A))                      # no tape: BREAK while it searches
    m.lib_load("tiny")
    command_to(sh, 'LIB ""', [S("TAPE_BLOCK")])
    m.run(200_000)
    hold_break(m, True)
    try:
        msg, rows = finish(sh, on_message=lambda: hold_break(m, False))
    finally:
        hold_break(m, False)
    ls = lib_state(sh)
    if msg != ("BREAK", source_row(SRC_A)) or ls["loaded"] != 0xF4 or ls["region3"][:len(tiny)] != tiny:
        bad.append("break in search %r loaded %02X" % (msg, ls["loaded"]))
    return expect(not bad, "; ".join(bad))


@case("lib-refused", "library tapes LIB refuses at the header, writing nothing and keeping the library before them: "
                     "version words $8D02 (a later ABI), $8E01 (another magic), $8C00 (Leap-C's program word), $8200 "
                     "(V2's packages): BAD TAPE VERSION; a length beyond image region 3 (1,025 B): LOAD FAILED")
def lib_refused(sh):
    m = sh.m
    bad = []
    cases = [(v, ltape("testlib", version=v), "BAD TAPE VERSION") for v in (0x8D02, 0x8E01, 0x8C00, 0x8200)]
    cases.append(("too long", ltape("testlib", length=0x401), "LOAD FAILED"))
    for what, tape, want in cases:
        play(sh, tape)
        sh.load(SRC_A, len(SRC_A))
        tiny = m.lib_load("tiny")
        st0 = state(sh)
        msg, rows = command(sh, 'LIB "testlib"')
        ls = lib_state(sh)
        if msg != (want, source_row(SRC_A)) or state(sh) != st0 or ls["loaded"] != 0xF4 or \
                ls["region3"][:len(tiny)] != tiny or ls["region3"][len(tiny):len(tiny) + 8] != bytes(8):
            bad.append("%s: %r %r loaded %02X" % (what if isinstance(what, str) else "$%04X" % what, msg, state(sh),
                                                 ls["loaded"]))
    return expect(not bad, "; ".join(bad))


@case("lib-keep-unload", "the loaded library stays through NEW and LOAD (a program tape after it, which uses it, RUNs); "
                         "LIB alone unloads it (NO LIBRARY; the program's call is then UNDEFINED FUNCTION 't_args'); "
                         "a reset (the cold start) clears it")
def lib_keep_unload(sh):
    m, S = sh.m, sh.S
    bad = []
    tape = join(ltape("testlib"), ptape("b", LIB_PROG))
    play(sh, tape)
    sh.load(SRC_A, len(SRC_A))
    msg, rows = command(sh, 'LIB "testlib"')
    if msg != lib_report("testlib", 24, SRC_A):
        bad.append("LIB %r" % (msg,))
    sh.type("NEW")
    if lib_state(sh)["loaded"] != 0xF4 or sh.store() != []:
        bad.append("after NEW: loaded %02X store %r" % (lib_state(sh)["loaded"], sh.store()))
    msg, rows = command(sh, 'LOAD "b"')
    if msg != ("LOADED b", source_row(LIB_PROG)) or lib_state(sh)["loaded"] != 0xF4:
        bad.append("LOAD %r loaded %02X" % (msg, lib_state(sh)["loaded"]))
    msg, rows = command(sh, "run")
    if msg[0] != "EXIT 123":
        bad.append("run %r" % (msg,))
    shown = sh.type("lib")
    sh.key(ord(" "))
    if shown != "NO LIBRARY " or lib_state(sh)["loaded"] != 0 or sh.store() != LIB_PROG:
        bad.append("LIB alone %r loaded %02X" % (shown, lib_state(sh)["loaded"]))
    msg, rows = command(sh, "run")
    if msg != ("ERROR 70: UNDEFINED FUNCTION", "LINE 3  't_args'"):
        bad.append("run unloaded %r" % (msg,))
    m.lib_load("testlib")                            # a reset: the cold start clears it, the region keeps its bytes
    m.setreg("PC", 0)
    if m.run_to([S("IO_READ_KEY")], 30_000_000) != S("IO_READ_KEY"):
        bad.append("no reset")
    elif lib_state(sh)["loaded"] != 0 or lib_state(sh)["region3"][:16] != lib_image("testlib")[:16]:
        bad.append("after a reset: loaded %02X" % lib_state(sh)["loaded"])
    return expect(not bad, "; ".join(bad))


@case("lib-any-replace", "LIB \"\" skips a program tape and loads the next library (tiny); LIB \"testlib\" then replaces "
                         "it: testlib's functions bind, tiny's is gone (UNDEFINED FUNCTION 'tiny')")
def lib_any_replace(sh):
    m = sh.m
    bad = []
    t = join(ptape("b", SRC_B), ltape("tiny"))
    t.silence(4.0)
    play(sh, join(t, ltape("testlib")))
    sh.load(SRC_A, len(SRC_A))
    st0 = state(sh)
    msg, rows = command(sh, 'LIB ""')
    if msg != lib_report("tiny", 1, SRC_A) or state(sh) != st0:
        bad.append("LIB \"\" %r" % (msg,))
    msg, rows = command(sh, 'LIB "testlib"')
    if msg != lib_report("testlib", 24, SRC_A):
        bad.append("LIB testlib %r" % (msg,))
    type_lines(sh, ["int main(void)", "{", "    return t_args(0, 4, 2) + tiny();", "}"])
    msg, rows = command(sh, "run")
    if msg != ("ERROR 70: UNDEFINED FUNCTION", "LINE 3  'tiny'"):
        bad.append("run %r" % (msg,))
    return expect(not bad, "; ".join(bad))


@case("lib-commands", "LIB's words: BAD NAME (11 characters, more after the quote, no closing quote), nothing loaded or "
                      "unloaded; LIB alone in any case and with spaces unloads (NO LIBRARY); `libx = 1;` is a source line")
def lib_commands(sh):
    m = sh.m
    bad = []
    for text in ('LIB "abcdefghijk"', 'LIB "x" y', 'lib "x'):
        sh.load(SRC_A, len(SRC_A))
        tiny = m.lib_load("tiny")
        st0 = state(sh)
        msg, rows = command(sh, text)
        if msg != ("BAD NAME", source_row(SRC_A)) or state(sh) != st0 or lib_state(sh)["loaded"] != 0xF4:
            bad.append("%s: %r" % (text, msg))
    for text in ("Lib", "LIB   "):
        sh.load(SRC_A, len(SRC_A))
        m.lib_load("tiny")
        shown = sh.type(text)
        sh.key(ord(" "))
        if shown != "NO LIBRARY " or lib_state(sh)["loaded"] != 0 or sh.store() != SRC_A:
            bad.append("%r: %r loaded %02X" % (text, shown, lib_state(sh)["loaded"]))
    sh.load(SRC_A, len(SRC_A))
    m.lib_load("tiny")
    sh.type("libx = 1;")
    if sh.store() != SRC_A + ["libx = 1;"] or lib_state(sh)["loaded"] != 0xF4:
        bad.append("libx: %r" % sh.store()[-2:])
    return expect(not bad, "; ".join(bad))


@case("lib-cross-version", "V2's own package tape (SHAPES, built from its tag: tools/v2ref.sh) and Leap-C's library tape "
                           "share the header type (4) and refuse each other by the version word: LIB \"SHAPES\" is BAD TAPE "
                           "VERSION, nothing written; V2's LOAD \"testlib\" EXT refuses testlib's tape, its program kept")
def lib_cross_version(sh):
    m = sh.m
    bad = []
    v2 = V2Machine(m.port + 40)
    pkg = os.path.join(ROOT, "build", "v2ref", "v2_shapes.tzx")
    try:
        v2.start()
        v2.put_store(c2src.records(["PRINT 42"]))
        before = v2.store()
        path = os.path.join(v2.snapdir, "testlib.rwa")
        ltape("testlib").write_rwa(path, lead=1.5)
        v2.cmd("snapshot-save " + os.path.join(v2.snapdir, "prog.zsf"))
        v2.tape_insert(path)
        v2.cmd("snapshot-load " + os.path.join(v2.snapdir, "prog.zsf"))
        v2._enable_bp()
        vmsg = v2.type('LOAD "testlib" EXT')
        if vmsg != "BAD TAPE VERSION" or v2.store() != before:
            bad.append("V2 LOAD EXT of a Leap-C library: %r, program %s" % (vmsg, "kept" if v2.store() == before
                                                                          else "changed"))
    finally:
        v2.stop()
    play(sh, tapes.Tape.from_tzx_direct(open(pkg, "rb").read()))   # (a direct recording, which ZEsarUX's
    sh.load(SRC_A, len(SRC_A))                                     # real-tape input does not play)
    tiny = m.lib_load("tiny")
    st0 = state(sh)
    msg, rows = command(sh, 'LIB "SHAPES"')
    ls = lib_state(sh)
    if msg != ("BAD TAPE VERSION", source_row(SRC_A)) or state(sh) != st0 or ls["loaded"] != 0xF4 or \
            ls["region3"][:len(tiny)] != tiny:
        bad.append("Leap-C LIB of V2's SHAPES: %r loaded %02X" % (msg, ls["loaded"]))
    return expect(not bad, "; ".join(bad))


# ===================================================================== running
def run_case(sh, name):
    title, fn = [(c[1], c[2]) for c in CASES if c[0] == name][0]
    sh.extra = None
    try:
        ok, detail = fn(sh)
    except Exception as e:                          # noqa: BLE001 -- a case that crashes fails
        ok, detail = False, "%s: %s" % (type(e).__name__, e)
    finally:
        try:
            memguard.arm(sh.m, False)
            sh.m.tape_capture(False)
            sh.m.tape_eject()
        except Exception:                           # noqa: BLE001
            pass
    return dict(case=name, title=title, ok=ok, detail=detail, extra=sh.extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10785)
    ap.add_argument("only", nargs="*")
    a = ap.parse_args()
    m = Machine(os.path.join(ROOT, "build"), a.port)
    t0 = time.time()
    failed = 0
    try:
        m.start()
        sh = Shell(m)
        for name, _, _ in CASES:
            if a.only and not any(o in name for o in a.only):
                continue
            t1 = time.time()
            r = run_case(sh, name)
            failed += not r["ok"]
            print("tape: %-24s %s %.0fs %s %s" % (name, "PASS" if r["ok"] else "FAIL", time.time() - t1,
                                                 r["detail"] if not r["ok"] else "", r["extra"] or ""), flush=True)
    finally:
        m.stop()
    print("tape: %d failures (%.0f s)" % (failed, time.time() - t0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
