"""Leap-C ZEsarUX test harness (persistent ZRCP session).

Derived from 2068-Leap's tools/qual/qharness.py (tag v2.0.1-emu.1, the V2 qualification harness):
the same approach (one headless ZEsarUX per worker, a snapshot of the booted machine restored
before every case, routines called with SP = $FF00 and a return slot, the screen read back with the
ROM's own font rendered by the real GFX_PUTCHAR). Copied and adapted, not imported: nothing here
reads or writes ~/2068-Leap. Needs ~/ts2068-debug (ZRCP client and process control) and
ZEsarUX 13.0 in ~/Applications/ZEsarUX-13.0.

What is real: the assembled ROM images (production or -DLEAPC_TEST), cold start through the
EXROM shell to its idle key wait, the lexer reading the line store, banking, interrupts.
What is substituted: source is written straight into the line store (the editor arrives in
Phase 5); test hooks are called directly.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser("~/ts2068-debug"))
from ts2068_debug.zrcp import ZRCPClient, ZRCPError      # noqa: E402
from ts2068_debug.process import ZEsarUXProcess          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZESARUX = os.path.expanduser("~/Applications/ZEsarUX-13.0")
RET_SLOT = 0xFF00          # return address slot for routine calls (spec.md 3.1: unused by the ROM)
STOP_ADDR = 0xFF02         # `jr $` written here; routine calls return to it
GLYPH_PROG = 0xF400        # glyph rendering program (image region 3, free at the idle prompt)


def load_syms(*paths):
    out = {}
    for p in paths:
        for line in open(p):
            m = re.match(r"([A-Za-z_][A-Za-z0-9_.]*):\s+EQU\s+0x([0-9A-F]+)", line, re.I)
            if m:
                out.setdefault(m.group(1), int(m.group(2), 16))
    return out


def cell_from(scr, row, col):
    y0 = row * 8
    base = ((y0 & 0xC0) << 5) | ((y0 & 0x38) << 2) | col
    return bytes(scr[base + 0x100 * k] for k in range(8))


class Machine:
    """One ZEsarUX running a Leap-C image. `build` is build/ (production) or build/test/."""

    def __init__(self, build, port, snapdir=None):
        self.build = os.path.abspath(build)
        self.port = port
        self.S = load_syms(os.path.join(self.build, "leapc_home.sym"),
                           os.path.join(self.build, "leapc_exrom.sym"))
        self.rom = os.path.join(self.build, "leapc_zesarux.bin")
        self.snapdir = snapdir or os.path.join(self.build, "snap_%d" % port)
        os.makedirs(self.snapdir, exist_ok=True)
        self.snap = os.path.join(self.snapdir, "boot.zsf")
        self.proc = None
        self.c = None
        self.glyphs = None
        self.boot = {}

    # ------------------------------------------------------------- low level
    def sym(self, n):
        return self.S[n]

    def cmd(self, line, timeout=None):
        return self.c.command(line, timeout=timeout)

    def read(self, addr, n):
        out = b""
        while n > 0:
            k = min(n, 4096)
            out += bytes.fromhex(self.cmd("read-memory %d %d" % (addr, k)).strip())
            addr += k
            n -= k
        return out

    def w16(self, addr):
        b = self.read(addr, 2)
        return b[0] | b[1] << 8

    def write(self, addr, data):
        if isinstance(data, int):
            data = bytes([data])
        for i in range(0, len(data), 2048):
            self.cmd("write-memory-raw %d %s" % (addr + i, data[i:i + 2048].hex()))

    def poke16(self, addr, v):
        self.write(addr, struct.pack("<H", v & 0xFFFF))

    def setreg(self, r, v):
        self.cmd("set-register %s=%04XH" % (r, v & 0xFFFF))

    def regs(self):
        out = {}
        for tok in self.cmd("get-registers").split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                try:
                    out[k] = int(v, 16)
                except ValueError:
                    pass
        return out

    def pc(self):
        return self.regs()["PC"]

    def _enable_bp(self):
        try:
            self.cmd("enable-breakpoints")
        except ZRCPError as e:
            if "already" not in str(e).lower():
                raise

    def set_bps(self, addrs):
        """Arm breakpoints 1..n at the given PCs; clear 1..8 beyond."""
        self._enable_bp()
        for i in range(1, 9):
            if i <= len(addrs):
                self.cmd("set-breakpoint %d PC=%04XH" % (i, addrs[i - 1]))
            else:
                self.cmd("set-breakpoint %d" % i)

    def run(self, maxi):
        return self.cmd("run %d" % maxi, timeout=max(30, maxi / 150_000 + 30))

    def run_to(self, addrs, maxi):
        """Run until PC is one of `addrs` (breakpoints) or maxi instructions pass; returns PC."""
        self.set_bps(list(addrs))
        self.run(maxi)
        return self.pc()

    def tstates_reset(self):
        self.cmd("reset-tstates-partial")

    def tstates(self):
        return int(self.cmd("get-tstates-partial").strip())

    # ------------------------------------------------------------- lifecycle
    def start(self, boot_max=20_000_000):
        if not os.path.exists(self.rom):
            raise FileNotFoundError(self.rom)
        self.proc = ZEsarUXProcess(ZESARUX, port=self.port, romfile=self.rom)
        self.proc.start()
        self.c = ZRCPClient(port=self.port, timeout=60)
        self.c.connect(retries=100)
        self.cmd("enter-cpu-step")
        self.cmd("reset-cpu")
        self.tstates_reset()
        t0 = time.time()
        pc = self.run_to([self.sym("IO_READ_KEY")], boot_max)
        self.boot = dict(pc=pc, reached=pc == self.sym("IO_READ_KEY"), tstates=self.tstates(),
                         wall=time.time() - t0)
        if not self.boot["reached"]:
            raise AssertionError("boot did not reach IO_READ_KEY (PC=%04X)" % pc)
        self.cmd("snapshot-save " + self.snap)
        self.glyphs = self._glyph_table()
        self.restore()
        return self

    def stop(self):
        try:
            if self.c:
                self.c.quit()
        except Exception:
            pass
        finally:
            if self.proc:
                self.proc.stop()

    def restore(self):
        self.cmd("snapshot-load " + self.snap)
        self._enable_bp()

    def _glyph_table(self):
        """Render chars 32..143 with the real GFX_PUTCHAR (A=char, B=row, C=col) and map each
        8x8 cell bitmap back to its character (as V2's qharness)."""
        d = tempfile.mkdtemp(prefix="lcglyph-")
        src = ["    DEVICE ZXSPECTRUM48", "    ORG $%04X" % GLYPH_PROG, "    ld d,32", "    ld b,0",
               "    ld c,0", "loop:", "    push de", "    push bc", "    ld a,d",
               "    call $%04X" % self.sym("GFX_PUTCHAR"), "    pop bc", "    pop de", "    inc d", "    inc c",
               "    ld a,c", "    cp 32", "    jr nz,nx", "    ld c,0", "    inc b", "nx: ld a,d", "    cp 144",
               "    jr nz,loop", "done: jr done", '    SAVEBIN "%s/g.bin", $%04X, $-$%04X' % (d, GLYPH_PROG, GLYPH_PROG)]
        open(d + "/g.asm", "w").write("\n".join(src) + "\n")
        r = subprocess.run(["sjasmplus", "--nologo", "--sym=" + d + "/g.sym", d + "/g.asm"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        done = [int(l.split()[2], 16) for l in open(d + "/g.sym") if l.startswith("done:")][0]
        self.write(GLYPH_PROG, open(d + "/g.bin", "rb").read())
        self.write(RET_SLOT, struct.pack("<H", done))
        self.setreg("SP", RET_SLOT)
        self.setreg("PC", GLYPH_PROG)
        assert self.run_to([done], 5_000_000) == done, "glyph render did not finish"
        scr = self.read(0x4000, 6144)
        table = {}
        for i, ch in enumerate(range(32, 144)):
            cell = cell_from(scr, i // 32, i % 32)
            table.setdefault(cell, chr(ch) if ch < 128 else chr(0x2580 + ch - 128))
        table[bytes(8)] = " "
        return table

    def screen_rows(self, scr=None, nrows=24):
        scr = scr if scr is not None else self.read(0x4000, 6144)
        rows = []
        for r in range(nrows):
            s = ""
            for col in range(32):
                cell = cell_from(scr, r, col)
                ch = self.glyphs.get(cell)
                if ch is None:
                    inv = bytes(255 - b for b in cell)
                    ch = self.glyphs.get(inv)
                    ch = ch.lower() if ch and ch.isalpha() else ("~" if ch is None else ch)
                s += ch
            rows.append(s.rstrip())
        return rows

    # ------------------------------------------------------------- Leap-C level
    def put_store(self, records):
        """Write line-store records (tools/c2src.py) at PROG_AREA_START and set PROG_END."""
        start = self.sym("PROG_AREA_START")
        if records:
            self.write(start, records)
        end = start + len(records)
        for s in ("PROG_END", "ARRAYS_END"):
            self.poke16(self.sym(s), end)

    def call(self, routine, maxi=50_000_000, t0=None, t1=None):
        """Call `routine` (name or address) with SP = RET_SLOT and run until it returns to
        STOP_ADDR. With t0/t1 (symbol names), also measure T-states from t0 to t1.
        Returns dict(ok, pc, tstates)."""
        self.write(STOP_ADDR, b"\x18\xFE")
        self.write(RET_SLOT, struct.pack("<H", STOP_ADDR))
        self.setreg("SP", RET_SLOT)
        self.setreg("PC", self.sym(routine) if isinstance(routine, str) else routine)
        t = None
        if t0:
            if self.run_to([self.sym(t0)], maxi) != self.sym(t0):
                return dict(ok=False, pc=self.pc(), tstates=None)
            self.tstates_reset()
            if self.run_to([self.sym(t1)], maxi) != self.sym(t1):
                return dict(ok=False, pc=self.pc(), tstates=None)
            t = self.tstates()
        pc = self.run_to([STOP_ADDR], maxi)
        return dict(ok=pc == STOP_ADDR, pc=pc, tstates=t)
