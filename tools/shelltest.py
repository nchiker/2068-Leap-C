#!/usr/bin/env python3
"""Leap-C shell tests (project_plan.md Phase 5: the editor and C punctuation).

Every case runs the production ROM from its booted editor (the snapshot lcharness takes at the first
key wait) and drives it through the keyboard, as V2's production regression (tools/v2_prod.py at the
V2 reference tag) does:
  - key(code): a key code through the ISR's latch (KBD_LASTK, KBD_KEYHIT); the machine then runs to
    its next key wait, and the status-row message shown on the way (SH_SHOW_MESSAGE) is returned;
  - press(ch): a character typed on the real keyboard matrix (ZEsarUX send-keys-event: CAPS SHIFT or
    SYMBOL SHIFT and the key, held until the ISR accepts the key, then released), so the ISR's scan
    and the key map (kernel/io IO_DECODE_KEY) are what is tested;
  - BREAK is the real CAPS SHIFT + SPACE, held while a program runs.
The cases port the applicable V2 editor tests (tools/v2_prod_regress.py, v2_known_defects.py,
study_edit_preserve.py, study_u6.py, study_flicker.py at the V2 reference tag; their names are kept)
and add Phase 5's: the C punctuation's keys and glyphs, keyword highlighting, the view with wrapped
lines, RUN with compile-error, runtime-error and BREAK recovery, the typing cost per key and the
selective-redraw oracle (after every key the screen equals what a full redraw draws).

Usage: shelltest.py [--port N] [--json OUT] [substring ...]
"""
import argparse
import json
import os
import struct
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2src                                                    # noqa: E402
import exectest                                                 # noqa: E402
import memguard                                                 # noqa: E402
from lcharness import Machine, STOP_ADDR, UNKNOWN, BOLD_MARK    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEFT, DOWN, UP, RIGHT, DELETE, ENTER = 1, 2, 3, 4, 8, 13
INSERT_LINE, DELETE_LINE, BREAK = 11, 15, 16
Z_CAPS, Z_SYM, Z_SPACE, Z_ENTER = 135, 138, 128, 129           # ZEsarUX send-keys-event codes
SYM_KEYS = {":": "z", "?": "c", "/": "v", "~": "a", "|": "s", "\\": "d", "{": "f", "}": "g", "<": "r",
            ">": "t", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "_": "0", ")": "9", "(": "8",
            "'": "7", "&": "6", '"': "p", ";": "o", "]": "u", "[": "y", "=": "l", "+": "k", "-": "j",
            "^": "h", ".": "m", ",": "n", "*": "b"}
C_GRAPHIC = "!\"#%&'()*+,-./:;<=>?[\\]^_{|}~"                   # the 29 of C's basic source character set
NEW_GLYPHS = {"[": [0x70, 0x40, 0x40, 0x40, 0x40, 0x40, 0x70, 0], "]": [0x70, 0x10, 0x10, 0x10, 0x10, 0x10, 0x70, 0],
              "{": [0x18, 0x20, 0x20, 0x40, 0x20, 0x20, 0x18, 0], "}": [0xC0, 0x20, 0x20, 0x10, 0x20, 0x20, 0xC0, 0],
              "|": [0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0], "~": [0, 0, 0x40, 0xA8, 0x10, 0, 0, 0],
              "^": [0x20, 0x50, 0x88, 0, 0, 0, 0, 0], "\\": [0, 0x40, 0x20, 0x10, 0x08, 0x04, 0, 0]}
NEW_GLYPHS = {k: bytes(v) for k, v in NEW_GLYPHS.items()}


def matrix_keys(ch):
    """The ZEsarUX key events that type `ch` on the Leap-C key map (spec.md 6.2)."""
    if ch == " ":
        return [Z_SPACE]
    if ch.islower() or ch.isdigit():
        return [ord(ch)]
    if ch.isupper():
        return [Z_CAPS, ord(ch.lower())]
    return [Z_SYM, ord(SYM_KEYS[ch])]


def bold(text):
    """Expected screen text: `word` is bold (each character BOLD_MARK + it)."""
    out, on = "", False
    for c in text:
        if c == "`":
            on = not on
        else:
            out += (BOLD_MARK + c) if on and c != " " else c
    return out


class Shell:
    def __init__(self, m):
        self.m = m
        self.S = m.sym
        self.caller = None
        self.boot_sp = None
        self.count_cls = False
        self.cls = 0

    # ------------------------------------------------------------- driving
    def boot(self):
        self.m.restore()
        self.boot_sp = self.m.regs()["SP"]

    def _wait(self, maxi, on_message=None):
        """Run to the next key wait; returns the message shown on the way: a status-row message's
        text (SH_SHOW_MESSAGE), or a report's two rows (SH_REPORT, Phase 6) as a tuple; else None.
        With count_cls set, the whole-screen clears on the way (GFX_CLS) are counted in self.cls.
        on_message (Phase 9): called when the message or report is reached: keys held on the matrix are let
        go there, as a person does (SH_WAIT_KEY waits for their release)."""
        m, S = self.m, self.S
        msg = None
        stops = [m.xsym("SH_SHOW_MESSAGE"), m.xsym("SH_REPORT"), S("IO_READ_KEY")] + ([S("GFX_CLS")] if self.count_cls else [])
        pc = m.run_to(stops, maxi)
        while self.count_cls and pc == S("GFX_CLS"):
            self.cls += 1
            m.cmd("cpu-step")
            pc = m.run_to(stops, maxi)
        if pc in (S("SH_REPORT"), S("SH_SHOW_MESSAGE")) and on_message:
            on_message()
        if pc == S("SH_REPORT"):
            msg = tuple(m.read(S(b), 33).split(b"\0")[0].decode("latin-1") for b in ("SH_REPORT_BUF", "SH_STATUS_BUF"))
            pc = m.run_to([S("IO_READ_KEY")], maxi)
        elif pc == S("SH_SHOW_MESSAGE"):
            msg = m.read(m.regs()["HL"], 33).split(b"\0")[0].decode("latin-1")
            pc = m.run_to([S("IO_READ_KEY")], maxi)
        if pc != S("IO_READ_KEY"):
            fired = memguard.fired(m)
            raise RuntimeError("no key wait: PC=%04X%s" % (pc, (" invariant: %s" % fired) if fired else ""))
        self.caller = m.w16(m.regs()["SP"])
        return msg

    def key(self, code, maxi=60_000_000):
        """A key code through the ISR's latch, then on to the next key wait."""
        self.m.write(self.S("KBD_LASTK"), code)
        self.m.write(self.S("KBD_KEYHIT"), 0xFF)
        self.m.cmd("cpu-step")
        return self._wait(maxi)

    def type(self, text, enter=True):
        last = None
        for ch in text:
            last = self.key(ord(ch))
        if enter:
            last = self.key(ENTER)
        return last

    def press(self, ch, maxi=60_000_000):
        """`ch` typed on the keyboard matrix: held until the ISR accepts it (debounce), released, then
        on to the next key wait."""
        return self.press_code(matrix_keys(ch), maxi, ch)

    def press_code(self, codes, maxi=60_000_000, what=None):
        """ZEsarUX key events `codes` held until the ISR accepts the key, released, then on to the next
        key wait (Z_ENTER: ENTER on the matrix)."""
        m, S = self.m, self.S
        for c in codes:
            m.cmd("send-keys-event %d 1" % c)
        try:
            pc = m.run_to([S("IO_LATCH_AND_CLEAR")], 2_000_000)
        finally:
            for c in reversed(codes):
                m.cmd("send-keys-event %d 0" % c)
        if pc != S("IO_LATCH_AND_CLEAR"):
            raise RuntimeError("key %r not accepted (PC=%04X)" % (what or codes, pc))
        return self._wait(maxi)

    def run_break(self, after=1_500_000, maxi=60_000_000):
        """ENTER on a `run` line, the program runs `after` instructions, then BREAK (CAPS SHIFT + SPACE)
        is held until the report. Returns (message, RT_BREAKREQ seen)."""
        m, S = self.m, self.S
        m.write(S("KBD_LASTK"), ENTER)
        m.write(S("KBD_KEYHIT"), 0xFF)
        m.cmd("cpu-step")
        pc = m.run_to([S("IO_READ_KEY"), m.xsym("SH_SHOW_MESSAGE"), m.xsym("SH_REPORT")], after)
        if pc in (S("IO_READ_KEY"), S("SH_SHOW_MESSAGE"), S("SH_REPORT")):
            raise RuntimeError("the program ended before BREAK (PC=%04X)" % pc)
        running = m.read(S("RUNNING"), 1)[0]
        def release():
            for c in (Z_SPACE, Z_CAPS):
                m.cmd("send-keys-event %d 0" % c)
        for c in (Z_CAPS, Z_SPACE):
            m.cmd("send-keys-event %d 1" % c)
        try:
            msg = self._wait(maxi, on_message=release)
        finally:
            release()
        return msg, running

    def load(self, lines, index=0):
        """Fast source injection: the line store written, the cursor on line `index`, the editor
        entered as after ENTER (SH_SET_EDIT_FROM_INDEX returning into SH_REENTER)."""
        m, S = self.m, self.S
        self.boot()
        m.put_store(c2src.records(lines))
        m.poke16(S("CUR_EDIT_INDEX"), index)
        m.poke16(0xFEFE, S("SH_REENTER"))
        m.setreg("SP", 0xFEFE)
        m.setreg("PC", S("SH_SET_EDIT_FROM_INDEX"))
        return self._wait(60_000_000)

    # ------------------------------------------------------------- state
    def in_editor(self):
        return self.caller == self.S("EDITOR_LOOP") + 3

    def in_run_wait(self):
        return self.caller == self.m.S.get("SH_WAIT_KEY.read", self.m.S["SH_WAIT_KEY"]) + 3

    def edit_line(self):
        return self.m.read(self.S("EDIT_LINE_BUF"), 128).split(b"\0")[0].decode("latin-1")

    def store(self):
        start, end = self.S("PROG_AREA_START"), self.m.w16(self.S("PROG_END"))
        data, out, p = self.m.read(start, end - start), [], 0
        while p + 2 <= len(data):
            n = data[p] | data[p + 1] << 8
            out.append(data[p + 2:p + 2 + n - 1].decode("latin-1"))
            p += 2 + n
        return out

    def index(self):
        return self.m.w16(self.S("CUR_EDIT_INDEX"))

    def rows(self, marks=False):
        return self.m.screen_rows(marks=marks)

    def cursor_cell(self):
        """(row, col) of the cursor (the editor's flashing, inverted cell: GFX_INVERT_ATTR), or None."""
        attrs = self.m.read(0x5800, 23 * 32)
        cells = [i for i, a in enumerate(attrs) if a & 0x80]
        return divmod(cells[0], 32) if len(cells) == 1 else (None if not cells else ("many", len(cells)))

    def full_reference(self):
        """The screen a full redraw (SH_REDRAW with V2_REDRAW_SCOPE 0) draws from the current editor
        state; the machine is put back exactly as it was (snapshot)."""
        m, S = self.m, self.S
        snap = os.path.join(m.snapdir, "oracle.zsf")
        m.cmd("snapshot-save " + snap)
        try:
            sp = m.regs()["SP"] - 2
            m.write(STOP_ADDR, b"\x18\xFE")
            m.poke16(sp, STOP_ADDR)
            m.write(S("V2_REDRAW_SCOPE"), 0)
            m.setreg("SP", sp)
            m.setreg("PC", S("SH_REDRAW"))
            if m.run_to([STOP_ADDR], 60_000_000) != STOP_ADDR:
                raise RuntimeError("reference redraw did not return")
            return m.read(0x4000, 6912)
        finally:
            m.cmd("snapshot-load " + snap)
            m._enable_bp()


CASES = []


def case(name, title):
    def deco(fn):
        CASES.append((name, title, fn))
        return fn
    return deco


def expect(cond, detail):
    return bool(cond), "" if cond else detail


# ===================================================================== editor screen
@case("boot-editor", "the cold start ends in the editor: empty screen, status row LINE 1/0 in the bar's colours, "
                     "the cursor at row 0 column 0, paging depth 1")
def boot_editor(sh):
    sh.boot()
    m, S = sh.m, sh.S
    rows = sh.rows()
    bar = m.read(0x5800 + 23 * 32, 32)
    ok = (rows[23] == "LINE 1/0" and not any(rows[:23]) and bar == bytes([7] * 29 + [0x10, 0x20, 0x08])
          and sh.cursor_cell() == (0, 0) and m.read(S("BANK_EXROM_DEPTH"), 1)[0] == 1)
    return expect(ok, "rows=%r bar=%s cursor=%s" % (rows[22:], bar.hex(), sh.cursor_cell()))


# ===================================================================== keyboard and glyphs
@case("keys-c-charset", "every character of C's basic source set typed on the keyboard matrix (CAPS SHIFT for "
                        "capitals, SYMBOL SHIFT for the 29 graphic characters) reaches the edit line and the screen")
def keys_c_charset(sh):
    sh.boot()
    text = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 " + C_GRAPHIC
    for ch in text:
        sh.press(ch)
    line = sh.edit_line()
    rows = sh.rows()
    shown = " ".join(rows[:4])                  # the editor wraps at the last space on a row (dropped)
    return expect(line == text and shown == text and not rows[4], "edit=%r screen=%r" % (line, rows[:5]))


@case("keys-new-symbols", "SYMBOL SHIFT + Y U F G S A H D give [ ] { } | ~ ^ \\ (spec.md 6.2); SYMBOL SHIFT + A and S "
                          "no longer give V2's error-navigation codes")
def keys_new_symbols(sh):
    sh.boot()
    got = []
    for ch in "[]{}|~^\\":
        sh.press(ch)
        got.append(sh.m.read(sh.S("KBD_LASTK"), 1)[0])
    return expect(bytes(got) == b"[]{}|~^\\" and sh.edit_line() == "[]{}|~^\\", "codes=%r edit=%r" % (bytes(got),
                                                                                                        sh.edit_line()))


@case("keys-editing-matrix", "Phase 9: the editing keys typed on the keyboard matrix (CAPS SHIFT + 5 8 7 6 0, + 1 "
                             "delete line, + ENTER insert line) leave the editor as their codes through the ISR's "
                             "latch do, key by key; two letters pressed together type nothing (IO_FIND_KEY's "
                             "ambiguous case), and the keyboard works after")
def keys_editing_matrix(sh):
    m, S = sh.m, sh.S
    matrix = {LEFT: [Z_CAPS, ord("5")], RIGHT: [Z_CAPS, ord("8")], UP: [Z_CAPS, ord("7")], DOWN: [Z_CAPS, ord("6")],
              DELETE: [Z_CAPS, ord("0")], DELETE_LINE: [Z_CAPS, ord("1")], INSERT_LINE: [Z_CAPS, Z_ENTER],
              ENTER: [Z_ENTER]}
    seq = (list("int ab;") + [LEFT, LEFT, DELETE, RIGHT, ENTER] + list("x();") + [ENTER] + list("y();") +
           [UP, UP, DOWN, INSERT_LINE] + list("z();") + [ENTER, UP, DELETE_LINE, DOWN, DOWN, LEFT, DELETE])

    def state():
        return sh.store(), sh.edit_line(), sh.index(), m.w16(S("CUR_EDIT_POS"))

    want = []
    sh.boot()
    for k in seq:
        sh.key(ord(k) if isinstance(k, str) else k)
        want.append(state())
    sh.boot()
    bad = []
    for i, k in enumerate(seq):
        if isinstance(k, str):
            sh.press(k)
        else:
            sh.press_code(matrix[k], what=k)
        if state() != want[i]:
            bad.append("key %d (%r): %r, through the latch %r" % (i, k, state(), want[i]))
            break
    before = state()
    for c in (ord("q"), ord("w")):              # two letters at once: no key
        m.cmd("send-keys-event %d 1" % c)
    try:
        m.cmd("disable-breakpoints")
        m.run(1_500_000)                        # (about 25 frames)
    finally:
        for c in (ord("w"), ord("q")):
            m.cmd("send-keys-event %d 0" % c)
    m.run(300_000)
    if m.read(S("KBD_KEYHIT"), 1)[0] or state() != before:
        bad.append("two keys at once: KEYHIT %d, %r" % (m.read(S("KBD_KEYHIT"), 1)[0], state()))
    sh._wait(60_000_000)
    sh.press("k")
    if sh.edit_line() != before[1][:before[3]] + "k" + before[1][before[3]:] and sh.edit_line() != before[1] + "k":
        bad.append("after: edit %r" % sh.edit_line())
    return expect(not bad and want[-1][0] != want[0][0], "; ".join(bad) or "the sequence changed nothing")


@case("editor-line-full", "Phase 9: a line holds 127 characters: a 128th typed is refused, the line unchanged "
                          "(EDITOR_INSERT_CHAR's refusal; ROM coverage)")
def editor_line_full(sh):
    sh.boot()
    line = ("int x; " * 19)[:127]
    sh.type(line, enter=False)
    before = sh.edit_line()
    sh.key(ord("z"))
    return expect(before == line and sh.edit_line() == line, "edit %d characters %r" % (len(sh.edit_line()),
                                                                                         sh.edit_line()[-10:]))


@case("report-held-key", "Phase 9: a key held past the ISR's auto-repeat delay (35 frames) does not end a report: "
                         "BREAK held on a running loop, and RUN's ENTER held over a short program, 100 frames after "
                         "the report appears; the report waits for the release, then for a new key")
def report_held_key(sh):
    m, S = sh.m, sh.S
    bad = []

    def frames(n):
        f0 = m.w16(S("FRAMES"))
        m.cmd("disable-breakpoints")
        while (m.w16(S("FRAMES")) - f0) & 0xFFFF < n:
            m.run(100_000)

    for what, lines, keys, want in (("BREAK", ["int main(void)", "{", "    for (;;) ;", "}"], [Z_CAPS, Z_SPACE],
                                     ("BREAK", "LINE 1")),
                                    ("ENTER", ["int main(void)", "{", "    return 7;", "}"], [Z_ENTER],
                                     ("EXIT 7", None))):
        sh.load(lines, len(lines))
        for ch in "run":
            sh.key(ord(ch))
        if what == "BREAK":
            m.write(S("KBD_LASTK"), ENTER)
            m.write(S("KBD_KEYHIT"), 0xFF)
            m.cmd("cpu-step")
            m.run_to([m.xsym("SH_REPORT")], 1_500_000)
        for c in keys:
            m.cmd("send-keys-event %d 1" % c)
        try:
            pc = m.run_to([m.xsym("SH_REPORT")], 60_000_000)
            frames(100)
            rows = sh.rows()
            held = S("SH_WAIT_KEY") <= m.pc() < m.S.get("SH_WAIT_KEY.read", S("SH_WAIT_KEY"))
        finally:
            for c in reversed(keys):
                m.cmd("send-keys-event %d 0" % c)
        sh._wait(10_000_000)
        rows2 = sh.rows()
        if pc != S("SH_REPORT") or not held or rows[22] != want[0] or (want[1] and rows[23] != want[1]):
            bad.append("%s held: report %r, waiting for the release %s" % (what, rows[22:24], held))
        if not sh.in_run_wait() or rows2[22:24] != rows[22:24]:
            bad.append("%s released: not waiting for a key with the report (%r)" % (what, rows2[22:24]))
        sh.key(ord(" "))
        if not sh.in_editor():
            bad.append("%s: a key did not end the report" % what)
    return expect(not bad, "; ".join(bad))


@case("glyphs-new", "the eight new glyphs render with their designed bitmaps (the font table through GFX_PUTCHAR)")
def glyphs_new(sh):
    bad = {c: sh.m.plain_cells[c].hex() for c, want in NEW_GLYPHS.items() if sh.m.plain_cells[c] != want}
    return expect(not bad, "differ: %r" % bad)


@case("glyphs-distinct", "every printable character of C's source set has its own glyph, and no bold glyph (keyword "
                         "highlighting) reads as another character's plain glyph")
def glyphs_distinct(sh):
    chars = [chr(c) for c in range(32, 127) if chr(c) not in "`"]
    cells = sh.m.plain_cells
    seen = {}
    dup = []
    for c in chars:
        if cells[c] in seen:
            dup.append((seen[cells[c]], c))
        seen.setdefault(cells[c], c)
    blank = [c for c in chars if c != " " and cells[c] == bytes(8)]
    clash = [c for c in "abcdefghijklmnopqrstuvwxyz" if sh.m.bold_cells[c] in seen]
    return expect(not dup and not blank and not clash, "same glyph %r; blank %r; bold clashes %r" % (dup, blank, clash))


@case("D5b-break-key-editor", "BREAK (CAPS SHIFT + SPACE) in the editor inserts nothing")
def break_key_editor(sh):
    sh.boot()
    sh.key(BREAK)
    sh.key(ord("a"))
    return expect(sh.edit_line() == "a", "edit=%r" % sh.edit_line())


# ===================================================================== editing (V2's editor tests)
@case("editor-type-store", "typed lines reach the line store through the real key path")
def editor_type_store(sh):
    sh.boot()
    sh.type("int x;")
    sh.type("int y = 2;")
    return expect(sh.store() == ["int x;", "int y = 2;"] and sh.index() == 2, "store=%r index=%d" % (sh.store(),
                                                                                                    sh.index()))


@case("editor-delete-line", "CAPS SHIFT+1 deletes the current line")
def editor_delete_line(sh):
    sh.boot()
    for t in ("a();", "b();", "c();"):
        sh.type(t)
    sh.key(UP)
    sh.key(UP)
    sh.key(DELETE_LINE)
    return expect(sh.store() == ["a();", "c();"] and sh.edit_line() == "c();", "store=%r" % sh.store())


@case("editor-delete-empty", "DELETE on an empty line deletes the line; DELETE elsewhere deletes the character left "
                             "of the cursor")
def editor_delete_empty(sh):
    sh.load(["a();", "", "b();"], 1)
    sh.key(DELETE)
    st1 = sh.store()
    sh.key(DELETE)                              # now on "b();": the cursor is at its start, nothing to delete
    sh.key(RIGHT)
    sh.key(RIGHT)
    sh.key(DELETE)                              # "b);"
    return expect(st1 == ["a();", "b();"] and sh.edit_line() == "b);", "store=%r edit=%r" % (st1, sh.edit_line()))


@case("editor-left-right-insert", "LEFT/RIGHT move inside the line; typing inserts at the cursor")
def editor_left_right(sh):
    sh.boot()
    sh.type("x = 1;", enter=False)
    for k in (LEFT, LEFT, LEFT):
        sh.key(k)
    sh.type("+1", enter=False)
    sh.key(RIGHT)
    sh.key(RIGHT)
    sh.key(RIGHT)
    sh.key(RIGHT)                               # past the end: stays
    sh.type("//", enter=False)
    return expect(sh.edit_line() == "x =+1 1;//", "edit=%r" % sh.edit_line())


@case("D9-edit-survives-navigation", "an uncommitted edit is not discarded by UP/DOWN")
def d9a(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.key(UP)
    sh.key(ord("9"))
    edited = sh.edit_line()
    sh.key(UP)
    sh.key(DOWN)
    now = sh.edit_line()
    return expect("9" in now and "9" in edited, "edited=%r after=%r store=%r" % (edited, now, sh.store()))


@case("D9-nav-plain", "UP/DOWN without an edit load the neighbouring line")
def d9_plain(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.key(UP)
    up = sh.edit_line()
    sh.key(UP)
    up2 = sh.edit_line()
    sh.key(DOWN)
    dn = sh.edit_line()
    return expect((up, up2, dn) == ("b = 2;", "a = 1;", "b = 2;"), "got %r %r %r" % (up, up2, dn))


def _fill_store(sh, room_left):
    """A line store with `room_left` bytes left below the source ceiling ($C000): a short first line,
    then long ones."""
    start, limit = sh.S("PROG_AREA_START"), 0xC000
    room = limit - room_left - start
    recs, used = ["int a;"], 2 + 6 + 1
    while room - used >= 8 + 3 + 120:
        recs.append("x" * 120)
        used += 2 + 120 + 1
    recs.append("y" * (room - used - 3))
    return recs


@case("D9-program-full-keeps-text", "PROGRAM FULL leaves the typed line in the edit buffer")
def d9b(sh):
    lines = _fill_store(sh, 4)
    sh.load(lines, len(lines))                   # the append line
    sh.type("y = 123456;", enter=False)
    typed = sh.edit_line()
    msg = sh.key(ENTER)
    sh.key(ord(" "))
    after = sh.edit_line()
    return expect(msg == "PROGRAM FULL" and after == typed == "y = 123456;", "msg=%r typed=%r after=%r" % (
        msg, typed, after))


@case("ep-up-commits-edit", "an edit on a stored line is stored when UP leaves it")
def ep_up(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.key(UP)
    sh.key(ord("9"))
    sh.key(UP)
    return expect(sh.store() == ["a = 1;", "9b = 2;"], "store=%r" % sh.store())


@case("ep-down-commits-edit", "an edit on a stored line is stored when DOWN leaves it")
def ep_down(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.key(UP)
    sh.key(UP)
    sh.key(ord("7"))
    sh.key(DOWN)
    return expect(sh.store() == ["7a = 1;", "b = 2;"] and sh.edit_line() == "b = 2;", "store=%r edit=%r" % (
        sh.store(), sh.edit_line()))


@case("ep-append-line-up", "text typed on the append line is stored when UP leaves it")
def ep_append_up(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.type("c = 3;", enter=False)
    sh.key(UP)
    return expect(sh.store() == ["a = 1;", "b = 2;", "c = 3;"] and sh.edit_line() == "c = 3;" and sh.index() == 2,
                  "store=%r edit=%r index=%d" % (sh.store(), sh.edit_line(), sh.index()))


@case("ep-append-line-down-noop", "DOWN on the append line keeps the typed text uncommitted")
def ep_append_down(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("zz", enter=False)
    sh.key(DOWN)
    return expect(sh.store() == ["a = 1;"] and sh.edit_line() == "zz", "store=%r edit=%r" % (sh.store(),
                                                                                             sh.edit_line()))


@case("ep-unchanged-nav-stores-nothing", "moving over unchanged lines does not rewrite the store")
def ep_unchanged(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    start = sh.S("PROG_AREA_START")
    before = sh.m.read(start, 64)
    pe = sh.m.w16(sh.S("PROG_END"))
    writes = []
    sh.m.cmd("set-breakpoint 12 MWA>77FFH and MWA<C000H")
    try:
        for k in (UP, UP, DOWN, DOWN):
            try:
                sh.key(k)
            except RuntimeError:
                writes.append("%04X" % sh.m.pc())
                break
    finally:
        sh.m.cmd("set-breakpoint 12")
    return expect(not writes and sh.m.read(start, 64) == before and sh.m.w16(sh.S("PROG_END")) == pe,
                  "a write to the source region at %r" % writes)


@case("ep-insert-line-commits", "CAPS SHIFT+ENTER (insert line) keeps an edit and inserts a blank line before the line")
def ep_insert(sh):
    sh.boot()
    sh.type("a = 1;")
    sh.type("b = 2;")
    sh.key(UP)
    sh.key(ord("9"))
    sh.key(INSERT_LINE)
    return expect(sh.store() == ["a = 1;", "", "9b = 2;"] and sh.edit_line() == "" and sh.index() == 1,
                  "store=%r edit=%r index=%d" % (sh.store(), sh.edit_line(), sh.index()))


@case("ep-full-on-nav-keeps-buffer", "PROGRAM FULL while moving keeps the buffer and the cursor")
def ep_full_nav(sh):
    sh.load(_fill_store(sh, 4), 0)
    for _ in range(6):
        sh.key(ord("y"))
    typed, idx = sh.edit_line(), sh.index()
    msg = sh.key(DOWN)
    sh.key(ord(" "))
    after = sh.edit_line()
    return expect(msg == "PROGRAM FULL" and after.startswith(typed) and sh.index() == idx and "yyyyyy" in after,
                  "msg=%r typed=%r after=%r index %d -> %d" % (msg, typed, after, idx, sh.index()))


@case("ep-full-enter-reenters-same-line", "ENTER on a full store keeps the line, and a second ENTER does not corrupt")
def ep_full_enter(sh):
    lines = _fill_store(sh, 4)
    sh.load(lines, len(lines))
    sh.type("y = 123456;", enter=False)
    typed = sh.edit_line()
    n = len(sh.store())
    m1 = sh.key(ENTER)
    sh.key(ord(" "))
    m2 = sh.key(ENTER)
    sh.key(ord(" "))
    return expect(m1 == m2 == "PROGRAM FULL" and sh.edit_line() == typed and len(sh.store()) == n,
                  "msgs=%r %r edit=%r lines %d -> %d" % (m1, m2, sh.edit_line(), n, len(sh.store())))


@case("editor-wrap-nav", "UP/DOWN move between the screen rows of a wrapped line before leaving it")
def editor_wrap_nav(sh):
    long = "int value = alpha + beta + gamma + delta + epsilon + zeta + eta + theta;"
    sh.load(["a();", long, "b();"], 1)
    sh.key(DOWN)
    r1 = (sh.index(), sh.m.w16(sh.S("EDIT_BUF_OFFSET")))
    sh.key(DOWN)
    r2 = (sh.index(), sh.m.w16(sh.S("EDIT_BUF_OFFSET")))
    sh.key(DOWN)
    r3 = sh.index()
    sh.key(UP)
    r4 = (sh.index(), sh.m.w16(sh.S("EDIT_BUF_OFFSET")))
    return expect(r1[0] == 1 and r1[1] > 0 and r2[0] == 1 and r2[1] > r1[1] and r3 == 2 and r4[0] == 1,
                  "after DOWN %r, DOWN %r, DOWN %r, UP %r" % (r1, r2, r3, r4))


@case("editor-view-wrapped", "the cursor line stays whole on the screen when the lines above it wrap (the C view; V2 "
                             "kept 20 lines above it whatever their height), also while moving down through them")
def editor_view_wrapped(sh):
    lines = ["/* line %02d: a comment that is long enough to wrap onto a second screen row */" % i for i in range(30)]

    def check(i):
        rows = sh.rows()
        top = [r for r in range(23) if rows[r].startswith("/* line %02d:" % i)]
        cur = sh.cursor_cell()
        return bool(top) and cur == (top[0], 0) and top[0] + 3 <= 23 and rows[top[0] + 2] == "second screen row */"
    got = []
    for i in (10, 15, 29):
        sh.load(lines, i)
        got.append((i, check(i)))
    for _ in range(9):                          # three lines down, three screen rows each
        sh.key(DOWN)
    got.append(("29+3 down", sh.index() == 30 and sh.edit_line() == ""))
    sh.load(lines, 3)
    for _ in range(3 * 5):
        sh.key(DOWN)
    got.append(("3, 5 lines down", sh.index() == 8 and check(8)))
    sh.type("x", enter=False)
    rows = sh.rows()
    got.append(("typed", any(r.startswith("x/* line 08:") for r in rows)))
    return expect(all(ok for _, ok in got), "%r" % got)


@case("editor-status", "the status row shows LINE n/m for the cursor's line and the line count")
def editor_status(sh):
    sh.load(["a();", "b();", "c();"], 1)
    s1 = sh.rows()[23]
    sh.key(DOWN)
    sh.key(DOWN)
    s2 = sh.rows()[23]
    return expect(s1 == "LINE 2/3" and s2 == "LINE 4/3", "%r %r" % (s1, s2))


# ===================================================================== commands
@case("cmd-new", "NEW (any case, trailing spaces) empties the source")
def cmd_new(sh):
    sh.load(["int x;", "int y;"], 2)
    sh.type("new  ")
    return expect(sh.store() == [] and sh.index() == 0 and sh.rows()[23] == "LINE 1/0", "store=%r status=%r" % (
        sh.store(), sh.rows()[23]))


@case("cmd-not-command", "a line that only starts with a command's name is source; commands are recognised only on "
                         "the append line")
def cmd_not_command(sh):
    sh.boot()
    sh.type("runner();")
    sh.type("new x;")
    sh.key(UP)                                  # on "new x;": ENTER stores it, it does not run NEW
    sh.key(ENTER)
    return expect(sh.store() == ["runner();", "new x;"], "store=%r" % sh.store())


@case("cmd-list", "LIST shows the source a page at a time with keywords bold; a line never splits across pages; "
                  "BREAK at a page end ends the listing")
def cmd_list(sh):
    lines = ["int f%02d(void) { return %d; }" % (i, i) for i in range(20)]
    lines.append("/* " + "x" * 70 + " */")      # 4 rows: does not fit after 20 rows on page 1
    lines.append("int last;")
    sh.load(lines, len(lines))
    sh.type("list")
    p1 = sh.rows(marks=True)
    w1 = sh.caller
    sh.key(ord(" "))
    p2 = sh.rows(marks=True)
    sh.key(ord(" "))                            # the end: back to the editor
    back = sh.in_editor()
    sh.type("list")
    sh.key(BREAK)
    back2 = sh.in_editor()
    ok = (p1[0] == bold("`int` f00(`void`) { `return` 0; }") and p1[19] == bold("`int` f19(`void`) { `return` 19; }")
          and not any(p1[20:]) and p2[0] == "/*" and p2[3] == "xxxxxx */" and p2[4] == bold("`int` last;")
          and back and back2 and w1 != sh.S("EDITOR_LOOP") + 3)
    return expect(ok, "page1 %r / %r; page2 %r; back %s %s" % (p1[0], p1[19:], p2[:6], back, back2))


# ===================================================================== highlighting
HL_SRC = ["int main(void)",                     # (each line within one screen row)
          "{",
          "  unsigned int1; char _if, ifx;",
          '  puts("int while \\" for");',
          "  c = '\"' + 'i';",
          "  for (;;) break; // return int",
          "  /* if */ do x++; while (x);",
          "  /* else */ INT Int;",
          "  sizeof(long) + sizeof x;",
          "  /* int",
          "  return 0;",
          "}"]
HL_WANT = ["`int` main(`void`)",
           "{",
           "  `unsigned` int1; `char` _if, ifx;",
           '  puts("int while \\" for");',
           "  c = '\"' + 'i';",
           "  `for` (;;) `break`; // return int",
           "  /* if */ `do` x++; `while` (x);",
           "  /* else */ INT Int;",
           "  `sizeof`(`long`) + `sizeof` x;",
           "  /* int",
           "  `return` 0;",
           "}"]


@case("highlight-fixture", "C keywords are bold as typed: not in identifiers, string literals, character constants or "
                           "comments, case-sensitive; the cursor's line is plain")
def highlight_fixture(sh):
    sh.load(HL_SRC, len(HL_SRC))
    rows = sh.rows(marks=True)
    bad = [(i, rows[i], bold(w)) for i, w in enumerate(HL_WANT) if rows[i] != bold(w)]
    sh.key(UP)                                   # the cursor on "}" ...
    sh.key(UP)                                   # ... then on "return 0;": drawn plain
    r10 = sh.rows(marks=True)[10]
    return expect(not bad and r10 == "  return 0;", "differ: %r; cursor line %r" % (bad, r10))


# ===================================================================== RUN
PROG_OK = ["int sq(int x)", "{", "    return x * x;", "}", "int main(void)", "{", '    printf("%d\\n", sq(7));',
           "    return 3;", "}"]


def _sane(sh, store):
    """The shell's state after a run: back in the editor at its key wait with the boot's stack, paging
    depth 1, no program running, the AY silent, the source intact."""
    m, S = sh.m, sh.S
    rg = m.regs()
    st = dict(editor=sh.in_editor(), sp=rg["SP"] == sh.boot_sp, depth=m.read(S("BANK_EXROM_DEPTH"), 1)[0] == 1,
              running=m.read(S("RUNNING"), 1)[0] == 0, source=sh.store() == store)
    st["ay"] = exectest.ay_regs(m)[8:11] == [0, 0, 0]          # (a probe routine: the registers put back)
    return all(st.values()), st


@case("editor-run-typed", "`run` typed on the append line compiles and runs the stored program; its screen stays "
                          "until a key; then the editor, intact")
def run_typed(sh):
    sh.boot()
    for l in PROG_OK:
        sh.type(l)
    memguard.arm(sh.m, True)
    try:
        sh.type("run")
        out = sh.rows()
        wait = sh.in_run_wait()
        sh.key(ord(" "))
    finally:
        memguard.arm(sh.m, False)
    ok, st = _sane(sh, PROG_OK)
    return expect(out[0] == "49" and out[22].startswith("EXIT 3") and wait and ok and sh.rows()[23] == "LINE 10/9",
                  "out=%r wait=%s state=%r" % (out[:2] + out[22:], wait, st))


@case("D4-typed-run-path", "a compile error: the cursor on the failing line with its text loaded, ERROR n LINE m; "
                          "(Phase 10, Fix 5) at the error's column, on the token the compile stopped at")
def run_compile_error(sh):
    sh.boot()
    for t in ("int main(void)", "{", "    int x = 2 3;", "    return x;", "}"):
        sh.type(t)
    msg = sh.type("run")
    sh.key(ord(" "))
    return expect(msg == ("ERROR 20: SYNTAX ERROR", "LINE 3") and sh.index() == 2 and sh.edit_line() == "    int x = 2 3;"
                  and sh.in_editor() and sh.cursor_cell() == (2, 14), "msg=%r index=%d edit=%r cursor=%r" % (
                      msg, sh.index(), sh.edit_line(), sh.cursor_cell()))


@case("run-error-at-end", "a compile error at the end of the source (a missing `}`) puts the cursor on the last line, "
                          "(Phase 10) at its end: the token the compile stopped at (the end) is past the line")
def run_error_at_end(sh):
    sh.load(["int main(void)", "{", "    return 1;"], 3)
    msg = sh.type("run")
    sh.key(ord(" "))
    return expect(msg == ("ERROR 20: SYNTAX ERROR", "LINE 3") and sh.index() == 2 and sh.edit_line() == "    return 1;"
                  and sh.cursor_cell() == (2, 13),
                  "msg=%r index=%d edit=%r cursor=%r" % (msg, sh.index(), sh.edit_line(), sh.cursor_cell()))


@case("error-column-once", "(Phase 10, Fix 5) a compile error's column applies once: the cursor on it after the "
                           "report; on the line again after DOWN and UP, at column 0; a macro's error (its token on "
                           "the #define line, before the line) at the line's end; a runtime error at column 0")
def error_column_once(sh):
    m, S = sh.m, sh.S
    bad = []
    src = ["int main(void)", "{", "    int k = 1 @ 2;", "    return k;", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    sh.key(ord(" "))
    first = (sh.index(), m.w16(S("EDIT_BUF_OFFSET")), sh.cursor_cell())
    if msg != ("ERROR 10: BAD CHARACTER", "LINE 3") or first != (2, 14, (2, 14)):
        bad.append("first %r %r" % (msg, first))
    sh.key(2)                                   # DOWN, UP: back on the line, at its start
    sh.key(3)
    again = (sh.index(), m.w16(S("EDIT_BUF_OFFSET")), sh.cursor_cell())
    if again != (2, 0, (2, 0)):
        bad.append("again %r" % (again,))
    src = ["#define BAD 1 2", "int main(void)", "{", "    return BAD;", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    sh.key(ord(" "))
    mac = (sh.index(), m.w16(S("EDIT_BUF_OFFSET")))
    if msg != ("ERROR 20: SYNTAX ERROR", "LINE 4") or mac != (3, len(src[3])):
        bad.append("macro %r %r" % (msg, mac))
    src = ["int f(int n)", "{", "    beep(1, n);", "    return 0;", "}", "int main(void)", "{", "    return f(99);", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    sh.key(ord(" "))
    rt = (sh.index(), m.w16(S("EDIT_BUF_OFFSET")), m.w16(S("SH_ERR_COL")))
    if msg != ("RUNTIME ERROR 4: BAD ARGUMENT", "LINE 1") or rt != (0, 0, 0):
        bad.append("runtime %r %r" % (msg, rt))
    return expect(not bad, "; ".join(bad))


@case("run-no-main", "RUN without main: ERROR 71: NO MAIN FUNCTION")
def run_no_main(sh):
    sh.load(["int f(void) { return 1; }"], 1)
    msg = sh.type("run")
    sh.key(ord(" "))
    return expect(msg is not None and msg[0] == "ERROR 71: NO MAIN FUNCTION" and sh.in_editor(), "msg=%r" % (msg,))


@case("run-runtime-error", "a runtime error: RUNTIME ERROR n LINE m, the cursor on the failing function's line, the "
                           "program's screen kept under the report; then the editor")
def run_runtime_error(sh):
    src = ["int f(int n)", "{", "    beep(1, n);", "    return 0;", "}", "int main(void)", "{", '    puts("hi");',
           "    return f(99);", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    out = sh.rows()[0]
    sh.key(ord(" "))
    ok, st = _sane(sh, src)
    return expect(msg == ("RUNTIME ERROR 4: BAD ARGUMENT", "LINE 1") and out == "hi" and sh.index() == 0 and ok,
                  "msg=%r out=%r index=%d state=%r" % (msg, out, sh.index(), st))


@case("run-stack-overflow", "runaway recursion: RUNTIME ERROR 1 at the function's line; a second RUN then works")
def run_stack_overflow(sh):
    src = ["int r(int n) { return r(n + 1) + 1; }", "int main(void) { return r(0); }"]
    sh.load(src, 2)
    msg = sh.type("run")
    sh.key(ord(" "))
    at = (sh.index(), sh.edit_line())           # the cursor on line 1, its text loaded
    sh.key(DELETE_LINE)                          # the recursion gone: r() calls nothing
    sh.key(INSERT_LINE)
    sh.type("int r(int n) { return n + 5; }", enter=True)
    sh.key(DOWN)                                 # (ENTER moved the cursor to line 2) the append line
    msg2 = sh.type("run") if sh.index() == 2 else "cursor at %d" % sh.index()
    wait = sh.in_run_wait()
    sh.key(ord(" "))
    return expect(msg == ("RUNTIME ERROR 1: STACK OVERFLOW", "LINE 1") and at == (0, src[0]) and msg2[0] == "EXIT 5"
                  and wait and sh.in_editor(),
                  "msg=%r at %r then %r wait=%s store=%r" % (msg, at, msg2, wait, sh.store()))


@case("run-break-loop", "BREAK (the real CAPS SHIFT + SPACE) stops a tight loop: BREAK LINE n, back to the editor "
                        "with the source intact, paging, stack and AY restored")
def run_break_loop(sh):
    src = ["int main(void)", "{", "    int i;", "    for (;;) i++;", "}"]
    sh.load(src, len(src))
    sh.type("run", enter=False)
    memguard.arm(sh.m, True)
    try:
        msg, running = sh.run_break()
    finally:
        memguard.arm(sh.m, False)
    sh.key(ord(" "))
    ok, st = _sane(sh, src)
    return expect(running and msg == ("BREAK", "LINE 1") and sh.index() == 0 and ok, "running=%s msg=%r index=%d state=%r" % (
        running, msg, sh.index(), st))


@case("run-break-beep", "BREAK during beep() (a BREAK-deferring EXROM trampoline): the beep ends early, BREAK, the AY "
                        "silent, the editor")
def run_break_beep(sh):
    src = ["int main(void)", "{", "    for (;;) beep(200, 0);", "}"]
    sh.load(src, len(src))
    sh.type("run", enter=False)
    msg, running = sh.run_break(after=600_000)
    sh.key(ord(" "))
    ok, st = _sane(sh, src)
    return expect(running and msg == ("BREAK", "LINE 1") and ok, "msg=%r state=%r" % (msg, st))


@case("run-break-pause", "BREAK during pause(): BREAK, the editor")
def run_break_pause(sh):
    src = ["int main(void)", "{", "    pause(30000);", "    return 0;", "}"]
    sh.load(src, len(src))
    sh.type("run", enter=False)
    msg, running = sh.run_break(after=600_000)
    sh.key(ord(" "))
    ok, st = _sane(sh, src)
    return expect(running and msg == ("BREAK", "LINE 1") and ok, "msg=%r state=%r" % (msg, st))


@case("u6-colour-state-restored", "a program's border, colours and hi-res mode do not follow it into the editor (the "
                                  "normal video mode, a white border, the editor's colours); a second RUN starts clean")
def u6_colours(sh):
    src = ["int main(void)", "{", "    border(2); paper(1); ink(6); bright(1); cls();", '    puts("x");', "    mode(1);",
           "    return 0;", "}"]
    sh.load(src, len(src))
    m, S = sh.m, sh.S
    sh.type("run")
    in_prog = (m.read(S("PORT_FF_SHADOW"), 1)[0] & 7, m.read(S("PORT_FE_SHADOW"), 1)[0] & 7, m.read(0x5800, 1)[0])
    sh.key(ord(" "))
    st1 = (m.read(S("PORT_FF_SHADOW"), 1)[0] & 7, m.read(S("PORT_FE_SHADOW"), 1)[0] & 7)
    attrs = m.read(0x5800, 23 * 32)
    plain = sum(1 for a in attrs if a == 0x38)
    row0 = sh.rows()[0]
    sh.load(["int main(void) { puts(\"y\"); return 0; }"], 1)
    sh.type("run")
    second = (m.read(0x5800, 1)[0], m.read(S("PORT_FE_SHADOW"), 1)[0] & 7, sh.rows()[0])
    sh.key(ord(" "))
    ok = (in_prog[1] == 2 and st1 == (0, 7) and plain == 23 * 32 - 1
          and row0.startswith("int main") and second == (0x38, 7, "y"))
    return expect(ok, "in the program (mode, border, attr) %r; editor (mode, border) %r, plain attrs %d, row0 %r; "
                      "second run %r" % (in_prog, st1, plain, row0, second))


# ===================================================================== performance and the redraw oracle
def _prog(n):
    base = ["    total = total + item * 2;", "    for (k = 1; k <= 10; k++)", "        x = x + k;",
            '    printf("%d\\n", x);', "    if (x > 20) goto done;", "    y = (x * 3) / 2 + 7;", "done:",
            "    count++;", "    z = x + y;", "    while (z) z--;"]
    return [base[i % len(base)] for i in range(n)]


def _seq(s):
    return [ord(c) for c in s]


LONG = "    x = 'a very long line that is going to wrap onto the second screen row';"
FLICKER = {
    # name: (lines, cursor line, keys) -- V2's study_flicker scenarios with C lines, and the C view's
    "type-10lines":   (_prog(10), 5, _seq("abc = abc + 1;") + [DELETE] * 4),
    "type-20lines":   (_prog(20), 10, _seq("abc = abc + 1;") + [DELETE] * 4),
    "type-wrapchg":   (["a = 1;", LONG, "b = 2;"], 1, _seq("0123456789012345") + [DELETE] * 3),
    "lr-10lines":     (_prog(10), 5, [RIGHT] * 6 + [LEFT] * 6),
    "updown-10lines": (_prog(10), 5, [DOWN, DOWN, UP, UP, UP, DOWN]),
    "updown-20lines": (_prog(20), 10, [DOWN, DOWN, UP, UP, UP, DOWN]),
    "updown-ends":    (_prog(6), 0, [UP] + [DOWN] * 7 + [UP] * 8),
    "updown-wrapped": (["short;", LONG, "mid;", LONG.replace("very", "rather"), "end;"], 0,
                       [DOWN] * 5 + [UP] * 6 + [DOWN, RIGHT, RIGHT, DOWN, DOWN, UP]),
    "updown-typed":   (_prog(8), 3, _seq("zz") + [DOWN, UP, UP] + _seq("q") + [DOWN]),
    "updown-deep":    (_prog(26), 18, [DOWN] * 4 + [UP] * 5),
    "append-up":      (_prog(5), 5, _seq("zz = 1;") + [UP, UP, DOWN, DOWN, DOWN]),
    "mixed-session":  (_prog(10), 4, _seq("a") + [UP, DOWN] + _seq("bb") + [DELETE, LEFT, DOWN, RIGHT] + _seq("c")
                       + [UP, UP, DOWN]),
    "wrapped-view":   ([LONG] * 16, 12, [DOWN, DOWN, DOWN, UP] + _seq("q") + [DOWN, UP, UP]),
}
# V2's own scenarios, text and keys exactly as in V2's tools/study_flicker.py (the editor does not care
# what language the text is), for the like-for-like typing comparison
V2_BASE = ["total = total + item * 2", "FOR k = 1 TO 10", "x = x + k", "PRINT x", "IF x > 20 THEN GOTO done",
           "y = (x * 3) / 2 + 7", "NEXT k", "done:", "count = count + 1", "z = x + y"]
V2_SCEN = {
    "v2-type-10lines": ([V2_BASE[i % 10] for i in range(10)], 5, _seq("abc = abc + 1") + [DELETE] * 4),
    "v2-type-20lines": ([V2_BASE[i % 10] for i in range(20)], 10, _seq("abc = abc + 1") + [DELETE] * 4),
    "v2-type-wrapchg": (["a = 1", "x = 'a very long line that is going to wrap onto the second screen row'", "b = 2"],
                        1, _seq("0123456789012345") + [DELETE] * 3),
    "v2-lr-10lines":   ([V2_BASE[i % 10] for i in range(10)], 5, [RIGHT] * 6 + [LEFT] * 6),
}
FLICKER.update(V2_SCEN)
# V2's measured means and maxima for them (docs/v2/V2_FEATURE_COST_STUDY_LOGS/flicker_i2.log at the V2
# reference tag: V2 production, with its selective redraws I1 and I2)
V2_TYPING = {"v2-type-10lines": (71751, 79859), "v2-type-20lines": (145523, 949409),
             "v2-type-wrapchg": (214271, 224044), "v2-lr-10lines": (1945, 2561)}


def run_flicker(sh, name, oracle=True):
    lines, start, keys = FLICKER[name]
    sh.load(lines, start)
    rows, mism = [], []
    for k in keys:
        if not oracle:
            sh.count_cls, sh.cls = True, 0
        sh.m.tstates_reset()
        try:
            sh.key(k)
        finally:
            sh.count_cls = False
        t = sh.m.tstates()
        rows.append((k, t, sh.cls if not oracle else None))
        if oracle:
            now = sh.m.read(0x4000, 6912)
            ref = sh.full_reference()
            if now != ref:
                mism.append(k)
    return rows, mism


@case("redraw-oracle", "after every key of V2's flicker scenarios (C lines, wrapped lines, the view): the screen equals "
                       "the one a full redraw draws from the same state")
def redraw_oracle(sh):
    bad = {}
    for name in FLICKER:
        _, mism = run_flicker(sh, name, oracle=True)
        if mism:
            bad[name] = mism
    return expect(not bad, "mismatches %r" % bad)


def measure_typing(sh):
    out = {}
    for name in list(V2_TYPING) + ["type-10lines", "type-20lines", "type-wrapchg", "lr-10lines"]:
        rows, _ = run_flicker(sh, name, oracle=False)
        ts = [t for _, t, _ in rows]
        out[name] = dict(keys=len(ts), mean=sum(ts) // len(ts), max=max(ts),
                         cls_keys=sum(1 for k, _, c in rows if c and k not in (UP, DOWN)))
        if name in V2_TYPING:
            out[name]["v2_mean"], out[name]["v2_max"] = V2_TYPING[name]
    return out


@case("typing-cost", "the cost per key (key delivery to the next key wait, interrupts included) is at or below V2's on "
                     "V2's own scenarios (about 70 kT per typed key on a 10-line program); C scenarios measured too; "
                     "typing never clears the whole screen while the view stays")
def typing_cost(sh):
    r = measure_typing(sh)
    sh.measured = r
    worse = {k: (v["mean"], v["v2_mean"]) for k, v in r.items() if "v2_mean" in v and v["mean"] > v["v2_mean"]}
    cls = {k: v["cls_keys"] for k, v in r.items() if v["cls_keys"]}
    return expect(not worse and not cls, "mean above V2's: %r; keys that cleared the screen: %r" % (worse, cls))


def run_all(port, only=None, out=None):
    m = Machine(os.path.join(ROOT, "build"), port)
    results = []
    failed = 0
    measured = None
    t0 = time.time()
    try:
        m.start()
        sh = Shell(m)
        for name, title, fn in CASES:
            if only and not any(o in name for o in only):
                continue
            try:
                ok, detail = fn(sh)
            except Exception as e:                      # noqa: BLE001 -- a case that crashes fails
                ok, detail = False, "%s: %s" % (type(e).__name__, e)
            if getattr(sh, "measured", None) is not None:
                measured = sh.measured
                sh.measured = None
            results.append(dict(case=name, title=title, ok=ok, detail=detail))
            failed += not ok
            print("shell: %-34s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""), flush=True)
    finally:
        m.stop()
    print("shell: %d/%d cases pass (%.0f s)" % (len(results) - failed, len(results), time.time() - t0))
    if measured:
        for k, v in measured.items():
            print("measured: keys %-16s %2d keys, mean %7d T, max %7d T, %d screen clears%s" % (
                k, v["keys"], v["mean"], v["max"], v["cls_keys"],
                ("   (V2: mean %d T, max %d T)" % (v["v2_mean"], v["v2_max"])) if "v2_mean" in v else ""))
    if out:
        json.dump(dict(cases=results, typing=measured, failed=failed), open(out, "w"), indent=1)
    return failed, results, measured


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10770)
    ap.add_argument("--json")
    ap.add_argument("only", nargs="*")
    a = ap.parse_args()
    failed, _, _ = run_all(a.port, a.only, a.json)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
