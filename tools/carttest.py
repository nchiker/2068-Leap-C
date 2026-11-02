#!/usr/bin/env python3
"""The runtime cartridge on a stock TS2068 (make cart; docs/milestones/M12-cart.md section 7; src/cart/cart.asm): make test-cart.

Programs are compiled on the RELEASE ROMs in ZEsarUX (tools/c2cart.compile_image: what the IDE does), packed by
tools/cartpack.py into a .dck, and run by ZEsarUX 13.0 with its STOCK ts2068.rom: the stock ROM finds the LROS header and
hands over to the cartridge's HOME. Breakpoints on HOME addresses also fire in the stock ROM, so every one carries
`PEEK(1)=1` (the LROS header's type byte: the cartridge's HOME is at $0000, not the stock ROM). The program's end is
RT_RUN.leave; the report's key wait is IO_READ_KEY reached after it.

  A  equivalence   a corpus slice (every tests/lib program that needs no keys, BREAK, tape or loaded library; every 4th
                   tests/doc program that needs no keys), each RUN through the shell on the release ROM and run on the
                   cartridge: rows 0-22 of the screen (text, bitmap and attributes) and the report on row 23. The expected
                   differences are listed in EXPECTED_DIFFS, each with its reason; a program over the image limits is skipped
                   with its reason
  B  behaviour     EXIT n, runtime errors, BREAK, a key restarts from a cold start, float, beep/sound, mode(1) with and
                   without #pragma hires, library programs, an image over 16 KB (DOCK chunk 2), NO PROGRAM (no image, wrong
                   identity, wrong CRC, a truncated block list, a damaged tail in chunk 2) and a key after it
  C  port audit    every `out` to $F4 / $FF in the cartridge HOME (found in its listing) trapped after the hand-off:
                   $F4 only $03/$43/$33/$37, $FF bit 7 never set
  D  the hand-off  interrupt state, IM, SP, ports at CART_ENTRY; an interrupt (the IM 1 handler at $0038) before CART_ENTRY's
                   `di`, with and without BREAK held, returns and the program still runs
  E  (--fuse)      the hello cartridge and equivalence programs on Fuse 1.9.1 with its stock ROMs and the .dck, screens
                   compared with ZEsarUX's

Ports 11780-11799 (worker k uses base + k). EMULATOR LIMITS: ZEsarUX's and Fuse's Z80, SCLD and DOCK models with the stock ROM
images; no hardware. A pass says what the emulators did.

Usage: carttest.py [--port N] [--only SUBSTR] [--fuse] [--workers N]      exit 0: all pass, 1: a failure
"""
import argparse
import glob
import multiprocessing as mp
import os
import queue
import re
import shutil
import signal
import socket
import struct
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2cart       # noqa: E402
import c2src        # noqa: E402
import cart_build   # noqa: E402
import cart_check   # noqa: E402
import cartpack     # noqa: E402
import exectest     # noqa: E402
import fusedrive    # noqa: E402
import gen_diag     # noqa: E402
import lcharness    # noqa: E402
from lcharness import Machine, ZEsarUXProcess, ZRCP, ZESARUX, load_syms  # noqa: E402

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
CART = os.path.join(BUILD, "cart")
STOCK_ROM = os.path.join(ZESARUX, "ts2068.rom")
PORT_LO, PORT_HI = 11780, 11799
MSGS = gen_diag.messages()
ZKEY_CAPS, ZKEY_SPACE = exectest.ZKEY_CAPS, exectest.ZKEY_SPACE

# ------------------------------------------------------------------------------------------------ expected differences
# (substring of the case name, what may differ, reason).  A case whose name contains the substring is still compared;
# the listed part is ignored ("rows": the text rows 0-22, "pix": bitmap and attributes of rows 0-22, "report": row 23).
# Everything else must match.  M12 section 7 names three causes; each entry below is one of them or a measured one.
EXPECTED_DIFFS = [
    ("B:expected-heap", "rows", "no source on the cartridge: RT_RUN's heap starts at the empty line store's end, so malloc() "
     "returns lower addresses than under RUN, where the program's source lies below the heap"),
    ("B:expected-peek0", "rows", "PEEK of $0000-$0004 reads the cartridge's LROS header (0, 1, CART_ENTRY, chunk byte $BC), "
     "not the release's di / jp COLD_START"),
]
UDG_NOTE = ("UDGs start blank at every run (the cold start clears them); under RUN they persist between runs")
# not a difference the shell run can show (it restores a fresh snapshot per case): under RUN a UDG a program defined stays
# defined for the next RUN; the cartridge's cold start clears the table at every restart -- B:expected-udg runs it twice

# programs that read the keyboard or the clock in ways the shell's run differs for, or that are not the slice's kind
A_SKIP_DIRS = ("keys", "tape", "loaded")
KEYED = re.compile(r"\b(getkey|inkey|getchar|gets|readline|input|pause)\s*\(")


# ================================================================================================ screens
def screen_view(scr):
    """scr: the 6912 bytes at $4000. -> dict(rows: text rows 0-22, pix: the bitmap lines of rows 0-22, attr: their attributes)."""
    class G:
        pass
    g = G()
    g.glyphs, g.bold = GLYPHS
    rows = Machine.screen_rows(g, bytes(scr[:6144]), nrows=23)
    pix = b"".join(bytes(scr[(y & 0xC0) << 5 | (y & 7) << 8 | (y & 0x38) << 2:][:32]) for y in range(184))
    return dict(rows=rows, pix=pix, attr=bytes(scr[6144:6144 + 23 * 32]))


def describe_diff(a, b, what=("rows", "pix", "attr")):
    """Why two views differ (first differences), or None."""
    out = []
    if "rows" in what and a["rows"] != b["rows"]:
        for i, (x, y) in enumerate(zip(a["rows"], b["rows"])):
            if x != y:
                out.append("row %d %r != %r" % (i, x, y))
                if len(out) >= 2:
                    break
    if "pix" in what and a["pix"] != b["pix"]:
        cells = sorted({(y // 8, x) for y in range(184) for x in range(32)
                        if a["pix"][y * 32 + x] != b["pix"][y * 32 + x]})
        out.append("bitmap differs in %d cells, first (row %d, col %d)" % (len(cells), cells[0][0], cells[0][1]))
    if "attr" in what and a["attr"] != b["attr"]:
        cells = [i for i in range(len(a["attr"])) if a["attr"][i] != b["attr"][i]]
        out.append("attributes differ in %d cells, first (row %d, col %d): %02X != %02X" % (
            len(cells), cells[0] // 32, cells[0] % 32, a["attr"][cells[0]], b["attr"][cells[0]]))
    return "; ".join(out) or None


# ================================================================================================ the cartridge machine
class CartMachine(Machine):
    """ZEsarUX with the stock ts2068.rom running a .dck (smartload). Symbols: the cartridge HOME's and the release EXROM's."""

    def __init__(self, port):
        self.tmp = tempfile.mkdtemp(prefix="carttest%d-" % port)
        Machine.__init__(self, BUILD, port, snapdir=self.tmp)
        self.S = load_syms(os.path.join(CART, "leapc_cart_home.sym"), os.path.join(BUILD, "leapc_exrom.sym"))
        self.glyphs, self.bold = GLYPHS
        self.nbps = 0
        self.stopped = False

    def start(self, boot_max=None):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", self.port)) == 0:
                raise RuntimeError("port %d is in use (an emulator left running?)" % self.port)
        self.proc = ZEsarUXProcess(ZESARUX, port=self.port, romfile=STOCK_ROM)
        self.proc.start()
        self.c = ZRCP(port=self.port, timeout=60)
        self.c.connect(retries=100)
        self.cmd("enter-cpu-step")
        return self

    def stop(self):
        try:
            Machine.stop(self)
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)

    def load(self, dck):
        """The cartridge `dck` (bytes) inserted and the machine reset into the stock ROM, which starts it."""
        path = os.path.join(self.tmp, "case.dck")
        with open(path, "wb") as f:
            f.write(dck)
        self.cmd("smartload " + path)

    def set_bps(self, addrs):
        """Breakpoints 1..n at the PCs (guarded by PEEK(1)=1: the cartridge's HOME, not the stock ROM)."""
        self._enable_bp()
        for i in range(1, max(len(addrs), self.nbps) + 1):
            if i <= len(addrs):
                self.cmd("set-breakpoint %d PC=%04XH and PEEK(1)=1" % (i, addrs[i - 1]))
            else:
                self.cmd("set-breakpoint %d" % i)
        self.nbps = len(addrs)

    def until(self, addrs, maxi=60_000_000):
        self.set_bps(list(addrs))
        self.run(maxi)
        return self.pc()

    def step(self):
        self.cmd("cpu-step")

    def ports(self):
        """(port $F4, port $FF) as ZEsarUX reports them."""
        t = self.cmd("get-io-ports")
        return int(t.split("Timex F4 port:")[1].split()[0], 16), int(t.split("Timex FF port:")[1].split()[0], 16)

    def view(self):
        return screen_view(self.read(0x4000, 6912))

    def row23(self):
        return self.screen_rows(self.read(0x4000, 6144))[23]

    def key(self, code=ord(" ")):
        """A key through the ISR's latch (as tools/shelltest.Shell.key), at the report's key wait; then one step."""
        self.write(self.sym("KBD_LASTK"), code)
        self.write(self.sym("KBD_KEYHIT"), 0xFF)
        self.step()

    def run_program(self, maxi=60_000_000):
        """From a loaded cartridge to the program's end: -> (ok, why). The screen is then the program's."""
        S = self.sym
        pc = self.until([S("RT_RUN.leave"), S("IO_READ_KEY")], maxi)
        if pc != S("RT_RUN.leave"):
            return False, "the program did not end: PC %04X" % pc
        return True, None

    def report(self, maxi=60_000_000):
        """From the program's end to the report's key wait: -> (row 23, why or None)."""
        S = self.sym
        pc = self.until([S("IO_READ_KEY")], maxi)
        if pc != S("IO_READ_KEY"):
            return None, "no key wait after the program: PC %04X" % pc
        return self.row23(), None


def press_break(m, down):
    exectest.press_break(m, down)


# ================================================================================================ the cases
class Case:
    """name: 'A:...'; lines: the Leap-C source (None: no compile; the image is derived); lib: library; ref: also RUN it through
    the shell (the equivalence reference); check(m, case, ctx) -> (ok, detail[, extra]) on the cartridge machine."""

    def __init__(self, name, lines=None, lib=None, ref=False, check=None, derive=None, maxi=None, fuse=False):
        self.name, self.lines, self.lib, self.ref, self.check = name, lines, lib, ref, check
        self.derive, self.maxi, self.fuse = derive, maxi, fuse
        self.group = name[0]


def lines_of(src):
    return c2src.lines_of(src)


def expected_for(name, part):
    for sub, what, reason in EXPECTED_DIFFS:
        if sub in name and (what == part or what == "any"):
            return reason
    return None


def check_equiv(m, case, ctx):
    """A: the cartridge's screen at the program's end and its report against the shell's."""
    ref = ctx["ref"]
    m.load(ctx["dck"])
    ok, why = m.run_program(case.maxi or 30_000_000)
    if not ok:
        return False, why, {}
    view = m.view()
    row23, why = m.report()
    if why:
        return False, why, {}
    diffs, notes = [], []
    parts = (("rows", ("rows",)), ("pix", ("pix", "attr")))
    for part, what in parts:
        d = describe_diff(view, ref["view"], what)
        if d:
            reason = expected_for(case.name, part)
            (notes if reason else diffs).append("%s: %s%s" % (part, d, " (expected: %s)" % reason if reason else ""))
    if row23 != ref["report"]:
        reason = expected_for(case.name, "report")
        (notes if reason else diffs).append("report %r != the shell's %r%s" % (row23, ref["report"],
                                                                              " (expected: %s)" % reason if reason else ""))
    f4, ff = m.ports()
    if f4 != 0x43 or ff & 0x80:
        diffs.append("ports at the report: $F4=$%02X $FF=$%02X" % (f4, ff))
    return not diffs, "; ".join(diffs + notes) or "report %r, screen identical" % row23, dict(view=view, report=row23)


# ---------------------------------------------------------------------------------------------- corpus slice (A)
def a_cases():
    out = []
    pool = []
    for p in sorted(glob.glob(os.path.join(ROOT, "tests", "lib", "**", "*.c"), recursive=True)):
        rel = os.path.relpath(p, os.path.join(ROOT, "tests", "lib"))
        if rel.split(os.sep)[0] in A_SKIP_DIRS:
            continue
        pool.append(p)
    docs = [p for p in sorted(glob.glob(os.path.join(ROOT, "tests", "doc", "*.c"))) if runnable(p)]
    pool += docs[::4]
    for p in pool:
        if not runnable(p):
            continue
        text, exp = exectest.parse_case(p)
        maxi = int(dict(exp).get("maxi", "20000000").replace(",", "").replace("_", ""))
        out.append(Case("A:" + os.path.relpath(p, ROOT), lines=lines_of(text), ref=True, check=check_equiv,
                        maxi=maxi + 10_000_000))
    return out


def runnable(path):
    """The slice's kind of program: it runs to its report with no keys, BREAK or library, and compiles."""
    text, exp = exectest.parse_case(path)
    keys = {k for k, _ in exp}
    if keys & {"keys", "break", "breakpc", "breakdeferred", "library"} or KEYED.search(text):
        return False
    for k, body in exp:
        if k == "expect" and body.split()[0] == "error":
            return False
    return any(k == "expect" and body.split()[0] in ("exit", "rterror") for k, body in exp)


# ---------------------------------------------------------------------------------------------- behaviour (B)
def expect_rows(m, ctx, row0=None, report=None, rows=None):
    """Run to the program's end and the report; check row 0 / given rows and the report. -> (bad list, view)."""
    bad = []
    m.load(ctx["dck"])
    ok, why = m.run_program(ctx.get("maxi", 30_000_000))
    if not ok:
        return [why], None
    view = m.view()
    got, why = m.report()
    if why:
        return [why], view
    for r, text in (rows or {}).items():
        if view["rows"][r] != text:
            bad.append("row %d %r, expected %r" % (r, view["rows"][r], text))
    if row0 is not None and view["rows"][0] != row0:
        bad.append("row 0 %r, expected %r" % (view["rows"][0], row0))
    if report is not None and got != report:
        bad.append("report %r, expected %r" % (got, report))
    f4, ff = m.ports()
    if f4 != 0x43 or ff & 0x80:
        bad.append("ports at the report: $F4=$%02X $FF=$%02X" % (f4, ff))
    return bad, view


def simple(row0, report, rows=None):
    def check(m, case, ctx):
        bad, view = expect_rows(m, ctx, row0=row0, report=report, rows=rows)
        return not bad, "; ".join(bad) or "row 0 %r, report %r" % (row0, report), dict(view=view, report=report)
    return check


RT = lambda n: gen_diag.report("RT", n, MSGS)       # noqa: E731


def check_break(m, case, ctx):
    """BREAK pressed during a loop: the report shows BREAK (the release RUN's text)."""
    S = m.sym
    m.load(ctx["dck"])
    pc = m.until([S("RT_RUN.leave"), S("IO_READ_KEY")], 3_000_000)
    if pc in (S("RT_RUN.leave"), S("IO_READ_KEY")):
        return False, "the loop ended by itself: PC %04X" % pc
    press_break(m, True)
    pc = m.until([S("RT_RUN.leave"), S("IO_READ_KEY")], 30_000_000)
    press_break(m, False)
    if pc != S("RT_RUN.leave"):
        return False, "BREAK did not end the program: PC %04X" % pc
    got, why = m.report()
    bad = []
    if why:
        return False, why
    if got != "BREAK":
        bad.append("report %r, expected 'BREAK'" % got)
    if m.row23().strip() != "BREAK" or m.read(S("BANK_EXROM_DEPTH"), 1)[0] != 1:
        bad.append("depth %d" % m.read(S("BANK_EXROM_DEPTH"), 1)[0])
    return not bad, "; ".join(bad) or "BREAK in a loop: report 'BREAK'"


def check_restart(m, case, ctx):
    """After the report a key restarts: CART_ENTRY is reached again (a cold start, the image copied afresh) and the program
    gives the same results, three times (a static counter and an initialised static it changes)."""
    S = m.sym
    m.load(ctx["dck"])
    seen = []
    for run in range(3):
        if run:
            m.key()
            pc = m.until([S("CART_ENTRY"), S("RT_RUN.leave")], 30_000_000)
            if pc != S("CART_ENTRY"):
                return False, "run %d: no cold start after the key: PC %04X" % (run + 1, pc)
        ok, why = m.run_program()
        if not ok:
            return False, "run %d: %s" % (run + 1, why)
        row0 = m.view()["rows"][0]
        got, why = m.report()
        if why:
            return False, "run %d: %s" % (run + 1, why)
        seen.append((row0, got))
    want = ("1 12", "EXIT 13")
    bad = ["run %d %r" % (i + 1, s) for i, s in enumerate(seen) if s != want]
    return not bad, ("%s, expected %r" % ("; ".join(bad), want)) if bad else "three runs, each %r %r (static state re-copied)" % want


def check_none(m, case, ctx):
    """NO PROGRAM on row 23 (no leave), then a key cold-starts again, still NO PROGRAM, twice."""
    S = m.sym
    m.load(ctx["dck"])
    bad = []
    for n in range(3):
        if n:
            m.key()
            pc = m.until([S("CART_ENTRY"), S("RT_RUN.leave"), S("IO_READ_KEY")], 30_000_000)
            if pc != S("CART_ENTRY"):
                return False, "after the key (round %d): PC %04X, not a cold start" % (n + 1, pc)
        pc = m.until([S("RT_RUN.leave"), S("IO_READ_KEY")], 30_000_000)
        if pc != S("IO_READ_KEY"):
            return False, "round %d: stopped at %04X, not the key wait (the program ran?)" % (n + 1, pc)
        r23 = m.row23()
        if r23 != "NO PROGRAM":
            bad.append("round %d: row 23 %r" % (n + 1, r23))
        if not m.ports()[0] in (0x43, 0x03):
            bad.append("round %d: $F4 $%02X" % (n + 1, m.ports()[0]))
    return not bad, "; ".join(bad) or "NO PROGRAM on row 23, three times (a key cold-starts again)"


def check_sound(m, case, ctx):
    bad, view = expect_rows(m, ctx, row0="DONE", report="EXIT 7")
    return not bad, "; ".join(bad) or "beep and sound returned: DONE, EXIT 7"


def check_view_ref(row0, report, extra=None):
    """The expectations of simple(), plus equivalence with the shell's run when the case has a reference."""
    def check(m, case, ctx):
        bad, view = expect_rows(m, ctx, row0=row0, report=report)
        if extra:
            bad += extra(m, view)
        ref = ctx.get("ref")
        if ref and view:
            d = describe_diff(view, ref["view"])
            if d:
                bad.append("differs from the shell's run: " + d)
        return not bad, "; ".join(bad) or "row 0 %r, report %r%s" % (row0, report, ", as the shell's" if ref else "")
    return check


def check_big(m, case, ctx):
    n = ctx["image_size"]
    bad, view = expect_rows(m, ctx, row0="1234 9", report="EXIT %d" % (1234 + 5678 + 7))
    if n <= 16384:
        bad.append("the image is only %d bytes: it does not reach chunk 2" % n)
    ref = ctx.get("ref")
    if ref and view:
        d = describe_diff(view, ref["view"])
        if d:
            bad.append("differs from the shell's run: " + d)
    return not bad, "; ".join(bad) or "image %d bytes (chunk 2 holds the last %d): 1234 9, EXIT 6919" % (n, n - 16384)


BIG = """char f1[8192];
char f2[4480];
char f3[1024];
char f4[3200];
int tail[4] = {1234, 5678, 9, 10};
char last[3] = {7, 8, 9};
int main(void)
{
    printf("%d %d", tail[0], last[2]);
    return tail[0] + tail[1] + last[0];
}
"""


UDG = """char face[8] = { 0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C };
int main(void)
{
    char *u = (char *)0xF180;
    int n = u[0] + u[1] + u[2] + u[3] + u[4] + u[5] + u[6] + u[7];
    cls();
    putchar(144);
    memcpy(u, face, 8);
    putchar(144);
    return n;
}
"""


def _heap(cart, ref):
    try:
        c, r = int(cart, 16), int(ref, 16)
    except ValueError:
        return "heap pointers %r / %r" % (cart, ref)
    return None if 0x5D00 <= c < r < 0xC000 else "malloc gave $%04X on the cartridge, $%04X under RUN (expected lower, in RAM)" % (c, r)


def _peek(cart, ref):
    # the release: di ($F3), jp ($C3), and at $0004 page zero's fill (0; 1.1's IO_KEY_SCAN_ROW, $DB = 219, went with
    # platform delta D27)
    return None if (cart, ref) == ("0 1 188", "243 195 0") else "PEEK 0/1/4: cartridge %r, RUN %r" % (cart, ref)


def check_expected(judge):
    """An expected difference (EXPECTED_DIFFS): the cartridge's screen must differ from the shell's in row 0 only, as judge
    says; both reports are EXIT 0."""
    def check(m, case, ctx):
        bad, view = expect_rows(m, ctx, report="EXIT 0")
        ref = ctx["ref"]
        if view is None:
            return False, "; ".join(bad)
        a, b = view["rows"], ref["view"]["rows"]
        if a == b:
            bad.append("no difference from the shell's run (the table entry is stale?)")
        if a[1:] != b[1:]:
            bad.append("rows 1-22 differ too")
        if not expected_for(case.name, "rows"):
            bad.append("no EXPECTED_DIFFS entry")
        j = judge(a[0], b[0])
        if j:
            bad.append(j)
        return not bad, "; ".join(bad) or "differs as listed: cartridge %r, RUN %r" % (a[0], b[0])
    return check


def check_udg(m, case, ctx):
    """A UDG defined by one run is blank at the next (the cold start clears the table): three runs, each prints UDG 144
    twice, before and after defining it; the first is blank, the second the face; EXIT 0 (the table read as zeros)."""
    S = m.sym
    m.load(ctx["dck"])
    for run in range(3):
        if run:
            m.key()
            if m.until([S("CART_ENTRY"), S("RT_RUN.leave")], 30_000_000) != S("CART_ENTRY"):
                return False, "run %d: no cold start" % (run + 1)
        ok, why = m.run_program()
        if not ok:
            return False, "run %d: %s" % (run + 1, why)
        v = m.view()
        cell = lambda c: bytes(v["pix"][y * 32 + c] for y in range(8))      # noqa: E731
        got, why = m.report()
        if got != "EXIT 0" or any(cell(0)) or cell(1) != bytes([0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C]):
            return False, "run %d: report %r, cells %s / %s" % (run + 1, got, cell(0).hex(), cell(1).hex())
    return True, "three runs: UDG 144 blank at every start (table cleared), the face once defined"


def behaviour_cases():
    P = lambda *rel: open(os.path.join(ROOT, *rel), encoding="latin-1").read()      # noqa: E731
    cs = []
    cs.append(Case("B:exit-5", lines_of('int main(void)\n{\n    puts("HI");\n    return 5;\n}\n'),
                   check=simple("HI", "EXIT 5")))
    cs.append(Case("B:exit-negative", lines_of('int main(void)\n{\n    printf("%d", -1234);\n    return -5;\n}\n'),
                   check=simple("-1234", "EXIT -5")))
    cs.append(Case("B:exit-deep", lines_of('void quit(int n)\n{\n    puts("BYE");\n    exit(n * 6);\n}\n'
                                           'int main(void)\n{\n    quit(7);\n    return 1;\n}\n'),
                   check=simple("BYE", "EXIT 42")))
    cs.append(Case("B:runtime-error-arg", lines_of(P("tests", "lib", "sound", "beep_bad_low.c")),
                   check=simple("", RT(4))))
    cs.append(Case("B:runtime-error-float", lines_of('int main(void)\n{\n    float z = 0;\n    puts("DIVIDE");\n'
                                                      '    return 1 / z;\n}\n'), check=simple("DIVIDE", RT(6))))
    cs.append(Case("B:runtime-error-stack", lines_of(P("tests", "rt", "stack_overflow_line.c")),
                   check=lambda m, case, ctx: _rt_stack(m, ctx)))
    cs.append(Case("B:break", lines_of("int main(void)\n{\n    int i = 0;\n    for (;;)\n        i++;\n    return i;\n}\n"),
                   check=check_break))
    cs.append(Case("B:restart", lines_of("int count;\nint init = 10;\nint main(void)\n{\n    count++;\n    init += 2;\n"
                                         '    printf("%d %d", count, init);\n    return count + init;\n}\n'),
                   check=check_restart))
    cs.append(Case("B:float", lines_of("float area(float r)\n{\n    return 3.14159 * r * r;\n}\nint main(void)\n{\n"
                                       '    printf("%.2f %f", area(2), 1.0 / 8);\n    return area(1) * 100;\n}\n'),
                   ref=True, check=check_view_ref("12.57 0.125000", "EXIT 314")))
    cs.append(Case("B:beep-sound", lines_of('int main(void)\n{\n    beep(1, 12);\n    beep(0, 0);\n    sound(7, 62);\n'
                                            '    sound(8, 0);\n    puts("DONE");\n    return 7;\n}\n'),
                   check=check_sound))
    cs.append(Case("B:hires-pragma", lines_of("#pragma hires\nint main(void)\n{\n    int n;\n    mode(1);\n"
                                              "    plot(10, 10);\n    n = point(10, 10);\n    mode(0);\n    return n;\n}\n"),
                   ref=True, check=check_view_ref("", "EXIT 1")))
    cs.append(Case("B:hires-no-pragma", lines_of(P("tests", "lib", "gfx", "mode_hires.c")), ref=True,
                   check=check_view_ref("", "EXIT 0")))
    cs.append(Case("B:hires-refused", lines_of(P("tests", "lib", "gfx", "mode_refused.c")), ref=True,
                   check=check_view_ref("", RT(3))))
    cs.append(Case("B:library-shapes", lines_of(P("tests", "lib", "loaded", "shapes.c")), lib="shapes", ref=True,
                   check=check_view_ref(None, "EXIT 0")))
    cs.append(Case("B:library-testlib", lines_of(P("tests", "lib", "loaded", "args.c")), lib="testlib", ref=True,
                   check=check_view_ref(None, "EXIT 0")))
    cs.append(Case("B:big-image", lines_of(BIG), ref=True, check=check_big))
    cs.append(Case("B:expected-heap", lines_of('int main(void)\n{\n    char *a;\n    a = malloc(10);\n'
                                               '    printf("%x", a);\n    return 0;\n}\n'), ref=True,
                   check=check_expected(lambda cart, ref: _heap(cart, ref))))
    cs.append(Case("B:expected-peek0", lines_of('int main(void)\n{\n    unsigned char *p = (unsigned char *)0;\n'
                                                '    printf("%d %d %d", p[0], p[1], p[4]);\n    return 0;\n}\n'), ref=True,
                   check=check_expected(lambda cart, ref: _peek(cart, ref))))
    cs.append(Case("B:expected-udg", lines_of(UDG), check=check_udg))
    # NO PROGRAM: derived from the hello image
    hello = cs[0]
    for name, how in (("no-image", "none"), ("wrong-identity", "identity"), ("wrong-crc", "crc"),
                      ("truncated-blocks", "truncate"), ("wrong-format", "format"), ("damaged-chunk-2", "tail")):
        cs.append(Case("B:no-program-" + name, derive=(how, "B:big-image" if how == "tail" else "B:exit-5"),
                       check=check_none))
    return cs


def _rt_stack(m, ctx):
    bad, _ = expect_rows(m, ctx, report=RT(1))
    return not bad, "; ".join(bad) or "report %r" % RT(1)


def derive_dck(how, img, home, exrom):
    """The cartridge for a NO PROGRAM case from a good image."""
    ident = cart_build.identity()
    hdr, blocks = cartpack.verify(img, ident)

    def repack(**kw):
        return cartpack.image(hdr["run_main"], hdr["run_void"], hdr["img_lim"], hdr["lib_loaded"], blocks,
                              kw.get("identity", ident))
    if how == "none":
        return cartpack.dck(home, exrom, None)
    if how == "identity":
        return cartpack.dck(home, exrom, repack(identity=ident ^ 0x0100))
    if how == "crc":
        bad = bytearray(img)
        bad[-1] ^= 0x01
        return cartpack.dck(home, exrom, bytes(bad))
    if how == "truncate":                           # the block list cut off before its end marker and CRC
        return cartpack.dck(home, exrom, img[:-6])
    if how == "format":
        bad = bytearray(img)
        bad[4] = 2
        return cartpack.dck(home, exrom, bytes(bad))
    if how == "tail":                               # a byte near the end of an image that continues in chunk 2
        bad = bytearray(img)
        bad[-5] ^= 0x80
        return cartpack.dck(home, exrom, bytes(bad))
    raise ValueError(how)


# ---------------------------------------------------------------------------------------------- port audit (C)
def out_sites():
    """[(address, port)]: every `out (PORT_BANK_HOME), a` / `out (PORT_SCLD), a` in the cartridge HOME's listing."""
    sites = []
    for addr, _b, text, routine in cart_check.listing(os.path.join(CART, "leapc_cart_home.lst")):
        mo = re.match(r"out\s+\(PORT_(BANK_HOME|SCLD)\)\s*,\s*a", text)
        if mo:
            sites.append((addr, 0xF4 if mo.group(1) == "BANK_HOME" else 0xFF, routine))
    return sites


def audited(m, ctx, restart=False, extra_keys=()):
    """Run the cartridge with a breakpoint on each `out` to $F4/$FF: -> (writes [(routine, port, A)], bad list)."""
    S = m.sym
    sites = out_sites()
    stops = [a for a, _p, _r in sites]
    by = {a: (p, r) for a, p, r in sites}
    leave, wait = S("RT_RUN.leave"), S("IO_READ_KEY")
    m.load(ctx["dck"])
    m.set_bps(stops + [leave, wait])
    writes, ends = [], 0
    for _ in range(40000):
        m.run(30_000_000)
        pc = m.pc()
        if pc in by:
            port, routine = by[pc]
            writes.append((routine, port, m.regs()["AF"] >> 8))
            m.step()
            continue
        if pc == leave:
            m.step()
            continue
        if pc == wait:
            ends += 1
            if restart and ends == 1:
                m.key()
                continue
            break
        return writes, ["stopped at %04X" % pc]
    else:
        return writes, ["too many port writes"]
    bad = []
    for routine, port, a in writes:
        if port == 0xF4 and a not in (0x03, 0x43, 0x33, 0x37):
            bad.append("%s wrote $F4 = $%02X" % (routine, a))
        if port == 0xFF and a & 0x80:
            bad.append("%s wrote $FF = $%02X (bit 7)" % (routine, a))
        if routine in ("CC_ERROR", "CC_ERROR_AT"):
            bad.append("the compiler's error exit ran (%s)" % routine)
    f4, ff = m.ports()
    if f4 != 0x43 or ff & 0x80:
        bad.append("ports at the report $F4=$%02X $FF=$%02X" % (f4, ff))
    return writes, bad


def check_audit(restart=False, want_ff=False):
    def check(m, case, ctx):
        writes, bad = audited(m, ctx, restart)
        f4 = sorted({a for _r, p, a in writes if p == 0xF4})
        ff = sorted({a for _r, p, a in writes if p == 0xFF})
        if not f4:
            bad.append("no $F4 write seen (the traps did not fire)")
        if want_ff and not any(a & 7 for a in ff):
            bad.append("no GFX_SET_MODE write seen")
        return not bad, "; ".join(bad) or "%d writes; $F4 in {%s}, $FF in {%s}" % (
            len(writes), ",".join("$%02X" % a for a in f4), ",".join("$%02X" % a for a in ff))
    return check


def audit_cases():
    return [Case("C:audit-hello", lines_of('int main(void)\n{\n    puts("HELLO");\n    return 3;\n}\n'), check=check_audit()),
            Case("C:audit-restart", lines_of('int main(void)\n{\n    puts("AGAIN");\n    return 4;\n}\n'),
                 check=check_audit(restart=True)),
            Case("C:audit-float", lines_of('int main(void)\n{\n    printf("%f", 2.5 * 4.0);\n    return 1;\n}\n'),
                 check=check_audit()),
            Case("C:audit-sound", lines_of("int main(void)\n{\n    beep(1, 12);\n    sound(8, 0);\n    return 2;\n}\n"),
                 check=check_audit()),
            Case("C:audit-hires", lines_of("#pragma hires\nint main(void)\n{\n    mode(1);\n    plot(1, 1);\n    mode(0);\n"
                                           "    return 0;\n}\n"), check=check_audit(want_ff=True)),
            Case("C:audit-no-program", derive=("none", "B:exit-5"), check=check_audit())]


# ---------------------------------------------------------------------------------------------- the hand-off (D)
def at_entry(m, ctx):
    """Load; stop at CART_ENTRY's first instruction (the hand-off)."""
    S = m.sym
    m.load(ctx["dck"])
    pc = m.until([S("CART_ENTRY")], 80_000_000)
    return pc == S("CART_ENTRY")


def check_handoff(m, case, ctx):
    S = m.sym
    if not at_entry(m, ctx):
        return False, "the stock ROM did not hand over to CART_ENTRY: PC %04X" % m.pc()
    raw = m.cmd("get-registers")
    f4, ff = m.ports()
    sp = m.regs()["SP"]
    running = m.read(S("RUNNING"), 1)[0]
    bad = []
    if "IM1" not in raw or "IFF12" not in raw:
        bad.append("not IM 1 with interrupts on: %s" % raw.split("IM")[-1].split()[0:2])
    if (f4, ff) != (0x43, 0x00):
        bad.append("ports $F4=$%02X $FF=$%02X, expected $43 / $00" % (f4, ff))
    if m.read(1, 4) != bytes([0x01, S("CART_ENTRY") & 255, S("CART_ENTRY") >> 8, 0xBC]):    # (byte 0 is unused)
        bad.append("the LROS header at $0000 reads %s" % m.read(0, 5).hex())
    ok, why = m.run_program()
    if not ok:
        bad.append(why)
    got, why = m.report()
    if got != "EXIT 3":
        bad.append("report %r" % (got or why))
    return not bad, "; ".join(bad) or "IM 1, interrupts on, SP $%04X, $F4=$%02X $FF=$%02X; stock RAM RUNNING=%d" % (
        sp, f4, ff, running)


def interrupt_at_entry(m, n, hold_break, running):
    """The IM 1 interrupt taken n times just before CART_ENTRY's `di` (PC pushed, PC=$0038, as the CPU does it; the
    return goes back to CART_ENTRY). -> (bad list, info)."""
    S = m.sym
    bad = []
    r0 = m.regs()
    sp0, pc0 = r0["SP"], r0["PC"]
    if hold_break:
        press_break(m, True)
        m.write(S("KBD_CUR_ROW"), 0xFF)             # the ISR's key tracking idle, so its debounce can run to BREAK's acceptance
    if running is not None:
        m.write(S("RUNNING"), running)
    info = dict(breakreq=0)
    for i in range(n):
        m.write(sp0 - 2, struct.pack("<H", pc0))
        m.setreg("SP", sp0 - 2)
        m.setreg("PC", 0x0038)
        pc = m.until([S("CART_ENTRY"), S("RT_BREAKREQ")], 200_000)
        if pc == S("RT_BREAKREQ"):                  # the ISR accepted BREAK (after its debounce)
            info["breakreq"] += 1
            info["running"] = m.read(S("RUNNING"), 1)[0]
            pc = m.until([S("CART_ENTRY")], 200_000)
        r = m.regs()
        if pc != pc0 or r["SP"] != sp0:
            bad.append("interrupt %d: back at %04X with SP %04X, expected %04X / %04X (BREAK accepted %d times; RUNNING %d)" % (
                i + 1, pc, r["SP"], pc0, sp0, info["breakreq"], m.read(S("RUNNING"), 1)[0]))
            break
        if any(r[k] != r0[k] for k in ("AF", "BC", "DE", "HL")):
            bad.append("interrupt %d changed AF/BC/DE/HL" % (i + 1))
            break
    return bad, info


def check_irq(hold_break, running_forced=None, informative=False):
    def check(m, case, ctx):
        S = m.sym
        if not at_entry(m, ctx):
            return False, "no hand-off: PC %04X" % m.pc()
        stock_running = m.read(S("RUNNING"), 1)[0]
        bad = []
        if running_forced is None and stock_running:
            bad.append("the stock RAM leaves RUNNING = %d at the hand-off" % stock_running)
        more, info = interrupt_at_entry(m, 60 if hold_break else 4, hold_break, running_forced)
        bad += more
        if hold_break and not info["breakreq"] and not bad:
            bad.append("the ISR never accepted BREAK in 60 ticks: the case tests nothing")
        if not bad:
            pc = m.until([S("RT_RUN.leave"), S("IO_READ_KEY")], 40_000_000)
            if hold_break:
                press_break(m, False)
            if pc != S("RT_RUN.leave"):
                bad.append("the program did not end: PC %04X" % pc)
            else:
                got, why = m.report()
                if got not in ("EXIT 3", "BREAK"):
                    bad.append("report %r" % (got or why))
                else:
                    got = got
                    return not bad, "; ".join(bad) or "returned each time; the program ran: %r (stock RUNNING %d%s%s)" % (
                        got, stock_running, ", forced %d" % running_forced if running_forced is not None else "",
                        "; BREAK accepted %d times" % info["breakreq"] if hold_break else "")
        elif hold_break:
            press_break(m, False)
        return (True if informative else False), ("INFO (not a failure) " if informative else "") + "; ".join(bad)
    return check


def handoff_cases():
    prog = lines_of('int main(void)\n{\n    puts("HELLO");\n    return 3;\n}\n')
    return [Case("D:handoff-state", prog, check=check_handoff),
            Case("D:irq-before-di", prog, check=check_irq(False)),
            Case("D:irq-before-di-break-held", prog, check=check_irq(True)),
            Case("D:break-held-through-handoff", prog, check=check_break_held),
            Case("D:irq-break-running-forced", prog, check=check_irq(True, running_forced=1, informative=True))]


def check_break_held(m, case, ctx):
    """BREAK held from the hand-off to the program's end: the cartridge still reaches the program and its report."""
    S = m.sym
    if not at_entry(m, ctx):
        return False, "no hand-off: PC %04X" % m.pc()
    press_break(m, True)
    pc = m.until([S("RT_RUN.leave"), S("IO_READ_KEY")], 40_000_000)
    press_break(m, False)
    if pc != S("RT_RUN.leave"):
        return False, "the program did not end: PC %04X" % pc
    got, why = m.report()
    return got in ("EXIT 3", "BREAK"), "report %r (the cartridge ran the program with BREAK held)" % (got or why)


# ================================================================================================ tasks and pools
GLYPHS = None
CASES = []


def build_task(m, k):
    """Release machine: the image of case k (and the shell's run of it as the reference)."""
    import shelltest
    case = CASES[k]
    if case.lines is None:
        return dict(ok=True, skip="derived")
    if getattr(m, "_sh", None) is None:
        m._sh = shelltest.Shell(m)
    try:
        r = c2cart.compile_image(m, case.lines, case.lib)
    except SystemExit as e:                          # (region_blocks: an IMG_LIM the packer cannot place)
        return dict(ok=True, skip="over the image limits: %s" % e)
    if isinstance(r, str):
        return dict(ok=False, detail="no image: " + r)
    run_main, run_void, lim, lib_loaded, blocks = r
    if not blocks:
        return dict(ok=False, detail="compiled to nothing")
    out = dict(ok=True)
    try:
        out["img"] = cartpack.image(run_main, run_void, lim, lib_loaded, blocks, cart_build.identity())
    except cartpack.CartPackError as e:
        return dict(ok=True, skip="over the image limits: %s" % e)
    if case.ref:
        res = exectest.compile_and_run(m, case.lines, maxi=case.maxi or 20_000_000, audit=False, shell=m._sh,
                                       library=case.lib)
        if not res.compile_ok or res.errnum or not res.ran or res.report is None:
            return dict(ok=True, skip="the shell's own run did not give a report (compile %s, error %s, ran %s)" % (
                res.compile_ok, res.errnum, res.ran))
        scr = res.mem.bytes(0x4000, 6912)
        out["ref"] = dict(view=screen_view(scr), report=res.report["shown"], exit=res.report["built"])
    return out


def cart_task(m, k, dck, ctx):
    case = CASES[k]
    ctx = dict(ctx, dck=dck, maxi=case.maxi or 30_000_000)
    r = case.check(m, case, ctx)
    ok, detail = r[0], r[1]
    extra = r[2] if len(r) > 2 else {}
    return dict(ok=ok, detail=detail, **{key: v for key, v in extra.items() if key in ("view", "report")})


def worker(port, tq, rq, make, work):
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))
    m = None
    try:
        while True:
            item = tq.get()
            if item is None:
                break
            rq.put(("take", item[0], port))
            t0 = time.time()
            try:
                if m is None:
                    m = make(port)
                    rq.put(("pid", port, lcharness.emulator_pid(m)))
                r = dict(work(m, *item[1:]))
            except Exception as e:                  # noqa: BLE001 -- a task that crashes fails; a new emulator
                r = dict(ok=False, detail="TASK FAILED %s: %s" % (type(e).__name__, e))
                try:
                    if m is not None:
                        m.stop()
                except Exception:                   # noqa: BLE001
                    pass
                m = None
            r["wall"] = time.time() - t0
            rq.put(("done", item[0], (port, r)))
    finally:
        if m is not None:
            try:
                m.stop()
            except Exception:                       # noqa: BLE001
                pass
        rq.put(("exit", port, None))


def run_pool(tasks, make, work, port0, workers, fuse_dir=None):
    """tasks: [(key, args...)] -> {key: result}. One emulator per worker (port port0 + k); a worker that dies fails its task
    and takes no more; every emulator is stopped on the way out."""
    workers = max(1, min(workers, len(tasks) or 1))
    if not tasks:
        return {}
    for k in range(workers):
        with socket.socket() as probe:
            if port0 + k > PORT_HI or probe.connect_ex(("127.0.0.1", port0 + k)) == 0:
                raise SystemExit("carttest: port %d is outside %d-%d or in use" % (port0 + k, PORT_LO, PORT_HI))
    ctx = mp.get_context("fork")
    tq, rq = ctx.Queue(), ctx.Queue()
    for t in tasks:
        tq.put(t)
    for _ in range(workers):
        tq.put(None)
    results, procs, pids, running = {}, {}, {}, {}
    old = signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))
    try:
        for k in range(workers):
            p = ctx.Process(target=worker, args=(port0 + k, tq, rq, make, work), daemon=True)
            p.start()
            procs[port0 + k] = p
        live = set(procs)
        while live:
            try:
                kind, a, b = rq.get(timeout=1)
            except queue.Empty:
                for port in list(live):
                    if not procs[port].is_alive():
                        live.discard(port)
                        if port in running:
                            results[running.pop(port)] = dict(ok=False, detail="worker on port %d died" % port)
                continue
            if kind == "take":
                running[b] = a
            elif kind == "pid":
                pids[a] = b
            elif kind == "done":
                port, r = b
                results[a] = r
                running.pop(port, None)
            elif kind == "exit":
                live.discard(a)
        for p in procs.values():
            p.join()
    finally:
        signal.signal(signal.SIGTERM, old)
        for p in procs.values():
            if p.is_alive():
                p.terminate()
        for p in procs.values():
            p.join(10)
        for port, pid in pids.items():
            if pid:
                lcharness.kill_own_emulator(pid, port=port)
        for port in procs:
            for pid in lcharness.own_emulators_on(port):
                lcharness.kill_own_emulator(pid, port=port)
        if fuse_dir:
            for pid in lcharness.own_fuses_in(fuse_dir):
                lcharness.kill_own_emulator(pid, cwd=fuse_dir)
    for t in tasks:
        results.setdefault(t[0], dict(ok=False, detail="never ran (no worker left)"))
    return results


# ---------------------------------------------------------------------------------------------- Fuse (E)
def fuse_task(_m, k, dck_path, expect, tmp):
    """The cartridge on Fuse's stock ROMs: wait for the report, compare with ZEsarUX's screen and report."""
    wdir = os.path.join(tmp, "fuse%d" % k)
    f = fusedrive.Fuse(BUILD, wdir, dock=dck_path).start()
    try:
        rows = []
        t0 = time.time()
        while time.time() - t0 < 120:
            f.wait_frames(30)
            rows = f.rows()
            if re.match(r"(EXIT|RUNTIME ERROR|BREAK|NO PROGRAM)", rows[23] or ""):
                break
        else:
            return dict(ok=False, detail="no report on Fuse after 120 s: row 23 %r" % rows[23])
        view = screen_view(f.screen())
        if expect is None:
            return dict(ok=True, detail="row 23 %r" % rows[23])
        bad = []
        d = describe_diff(view, expect["view"])
        if d:
            bad.append(d)
        if rows[23] != expect["report"]:
            bad.append("report %r != ZEsarUX's %r" % (rows[23], expect["report"]))
        return dict(ok=not bad, detail="; ".join(bad) or "report %r, screen identical to ZEsarUX's" % rows[23])
    finally:
        f.stop()


# ================================================================================================ main
def main():
    global GLYPHS, CASES
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=PORT_LO, help="first of the ZEsarUX ports (%d-%d)" % (PORT_LO, PORT_HI))
    ap.add_argument("--only", action="append", default=[], help="run only the cases whose name contains this")
    ap.add_argument("--fuse", action="store_true", help="part E: Fuse 1.9.1 with the stock ROMs")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()
    for p in (os.path.join(CART, "leapc_cart_home.bin"), os.path.join(CART, "leapc_cart_home.lst"),
              os.path.join(BUILD, "leapc_exrom.bin"), STOCK_ROM):
        if not os.path.exists(p):
            print("cart: FAIL %s is missing (make cart)" % os.path.relpath(p, ROOT))
            return 1
    GLYPHS = fusedrive.glyph_tables(BUILD, port=min(a.port + 19, PORT_HI))
    home = open(os.path.join(CART, "leapc_cart_home.bin"), "rb").read()
    exrom = open(os.path.join(BUILD, "leapc_exrom.bin"), "rb").read()
    CASES = a_cases() + behaviour_cases() + audit_cases() + handoff_cases()
    want = lambda c: not a.only or any(o in c.name for o in a.only)      # noqa: E731
    # a derived case needs its source case's image
    need = {c.derive[1] for c in CASES if want(c) and c.derive}
    index = {c.name: i for i, c in enumerate(CASES)}
    todo = [i for i, c in enumerate(CASES) if want(c) or c.name in need]
    # E picks: hello plus equivalence programs that are not time or heap dependent
    e_cases = []
    if a.fuse:
        picks = [c for c in CASES if c.group == "A" and "/time/" not in c.name and "heap" not in c.name
                 and "scroll" not in c.name]
        step = max(1, len(picks) // 8)
        e_cases = [c.name for c in picks[::step][:8]] + ["B:exit-5"]
        todo = sorted(set(todo) | {index[n] for n in e_cases})
    print("cart: %d cases (%d on this run), %d workers" % (len(CASES), len(todo), a.workers), flush=True)

    # ---- phase 1: the images and the shell's reference runs, on the release ROMs
    t1 = time.time()
    build_tasks = [(i, i) for i in todo if CASES[i].lines is not None]
    make_rel = lambda port: Machine(BUILD, port).start()                 # noqa: E731
    built = run_pool(build_tasks, make_rel, build_task, a.port, a.workers)
    print("cart: images built in %.0f s" % (time.time() - t1), flush=True)

    # ---- phase 2: the cartridges on the stock ROM
    results, tasks, dcks = {}, [], {}
    for i in todo:
        c = CASES[i]
        if not want(c) and c.name not in e_cases:
            continue
        if c.lines is not None:
            b = built[i]
            if not b["ok"]:
                results[i] = dict(ok=False, detail=b["detail"])
                continue
            if b.get("skip"):
                results[i] = dict(ok=True, skipped=True, detail="SKIPPED: " + b["skip"])
                continue
            img, ctx = b["img"], dict(ref=b.get("ref"), image_size=len(b["img"]))
            dck = cartpack.dck(home, exrom, img)
        else:
            how, src = c.derive
            sb = built.get(index[src])
            if not sb or not sb["ok"] or not sb.get("img"):
                results[i] = dict(ok=False, detail="the source image of %s is missing" % src)
                continue
            dck, ctx = derive_dck(how, sb["img"], home, exrom), dict(image_size=0)
        dcks[i] = dck
        tasks.append((i, i, dck, ctx))
    t2 = time.time()
    make_cart = lambda port: CartMachine(port).start()                   # noqa: E731
    got = run_pool(tasks, make_cart, cart_task, a.port, a.workers)
    results.update(got)
    print("cart: cartridges run in %.0f s" % (time.time() - t2), flush=True)

    # ---- phase 3: Fuse
    fuse_res = {}
    if a.fuse:
        t3 = time.time()
        tmp = tempfile.mkdtemp(prefix="carttest-fuse-")
        try:
            ftasks = []
            for n in e_cases:
                i = index[n]
                r = results.get(i)
                if not r or not r["ok"] or "view" not in r:
                    fuse_res["E:" + n] = dict(ok=False, detail="no ZEsarUX result to compare with (%s)" % (r or {}).get("detail"))
                    continue
                path = os.path.join(tmp, "case%d.dck" % i)
                open(path, "wb").write(dcks[i])
                ftasks.append((i, i, path, dict(view=r["view"], report=r["report"]), tmp))
            fres = run_pool(ftasks, lambda port: None, fuse_task, a.port, min(a.workers, 4), fuse_dir=tmp)
            for k, r in fres.items():
                fuse_res["E:" + CASES[k].name[2:]] = r
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("cart: Fuse cases run in %.0f s" % (time.time() - t3), flush=True)

    # ---- report
    rows = [(CASES[i].name, results[i]) for i in sorted(results)] + sorted(fuse_res.items())
    per = {}
    for name, r in rows:
        g = name[0]
        s = per.setdefault(g, [0, 0, 0])
        if r.get("skipped"):
            s[2] += 1
        elif r["ok"]:
            s[0] += 1
        else:
            s[1] += 1
        if not r["ok"] or not name.startswith("A:") or r.get("skipped") or "expected:" in r["detail"]:
            print("cart: %s %-44s %s" % ("ok  " if r["ok"] else "FAIL", name, r["detail"]))
    failed = sum(s[1] for s in per.values())
    print("cart: expected differences from RUN (EXPECTED_DIFFS), each shown by its own case:")
    for sub, what, reason in EXPECTED_DIFFS:
        print("cart:   %-18s %-5s %s" % (sub, what, reason))
    print("cart:   %-18s %-5s %s" % ("B:expected-udg", "-", UDG_NOTE))
    for g in sorted(per):
        print("cart: part %s: %d pass, %d fail, %d skipped" % (g, per[g][0], per[g][1], per[g][2]))
    print("cart: TOTAL %s (%d failures), %.0f s" % ("PASS" if not failed else "FAIL", failed, time.time() - t0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
