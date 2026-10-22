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
import socket
import struct
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser("~/ts2068-debug"))
from ts2068_debug.zrcp import ZRCPClient, ZRCPError      # noqa: E402
from ts2068_debug.process import ZEsarUXProcess as _ZProcess  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZESARUX = os.path.expanduser("~/Applications/ZEsarUX-13.0")
# ZEsarUX's own speed settings (Phase 5): --emulatorspeed shortens the real-time wait after each
# frame (10-1000 %) and --frameskip skips drawing frames; neither changes the emulated machine (the
# T-states per frame, the interrupts), so every measurement is unchanged. Measured on the idle editor:
# 3.4 MT/s at real speed, 8.1 MT/s with these. LEAPC_REALTIME=1 runs at real speed.
FAST_ARGS = [] if os.environ.get("LEAPC_REALTIME") else ["--emulatorspeed", "1000", "--frameskip", "49"]
RET_SLOT = 0xFF00          # return address slot for routine calls (spec.md 3.1: unused by the ROM)
TAPE_SLOTS = (14, 15, 16, 17, 18)  # breakpoint slots of the SAVE capture (set_bps: 1-8; memguard: 9-11; 12-13 ad hoc)
AUTOLOAD_PC = 0x11F8       # ZEsarUX's TS2068 autoload trigger (storage/tape.c gestionar_autoload_spectrum)
STOP_ADDR = 0xFF02         # `jr $` written here; routine calls return to it
GLYPH_PROG = 0xF400        # glyph rendering program (image region 3, free at the idle prompt)
LIBS = os.path.join(ROOT, "build", "libs")      # Phase 10: the libraries' images (make libs: tools/lib2tape.py)
LX_BASE = 0xF400           # a loaded library's image (image region 3; include/leapc_lib.inc)
UNKNOWN = "\u2591"         # screen_rows: a cell that is no glyph
BOLD_MARK = "\u2022"       # screen_rows(marks=True): the next character is bold


class _QuickAckSocket:
    """A socket that acknowledges every segment at once (TCP_QUICKACK, re-armed around each recv: Linux
    clears it). ZEsarUX writes a reply and its prompt separately; with Nagle on its side and delayed
    ACKs on ours, the prompt waited for our ACK: 41 ms for every command with a reply (measured,
    Phase 6), 0.04 ms with this."""

    def __init__(self, sock):
        self._s = sock

    def recv(self, n):
        self._quick()
        data = self._s.recv(n)
        self._quick()
        return data

    def _quick(self):
        if hasattr(socket, "TCP_QUICKACK"):
            try:
                self._s.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            except OSError:
                pass

    def __getattr__(self, name):
        return getattr(self._s, name)


class ZRCP(ZRCPClient):
    """ts2068-debug's ZRCP client with the socket's delayed ACKs and Nagle off (_QuickAckSocket)."""

    def connect(self, *args, **kw):
        super().connect(*args, **kw)
        if self._sock is not None and not isinstance(self._sock, _QuickAckSocket):
            self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._sock = _QuickAckSocket(self._sock)


class ZEsarUXProcess(_ZProcess):
    """ts2068-debug's ZEsarUX launcher (the same arguments) with FAST_ARGS. With stdout_path, ZEsarUX's
    standard output goes to that file line by line (stdbuf): the tape capture's breakpoint actions print
    there (Machine.tape_capture, Phase 7)."""
    stdout_path = None

    def start(self):
        args = ["./" + self.binary, "--noconfigfile", "--machine", self.machine, "--enable-remoteprotocol",
                "--remoteprotocol-port", str(self.port), "--vo", "null", "--ao", "null"] + FAST_ARGS
        if self.romfile:
            args += ["--romfile", os.path.abspath(self.romfile)]
        out = subprocess.DEVNULL
        if self.stdout_path:
            out = open(self.stdout_path, "w")
            args = ["stdbuf", "-oL"] + args
        self._proc = subprocess.Popen(args, cwd=str(self.install_dir), stdout=out, stderr=subprocess.DEVNULL)
        if out is not subprocess.DEVNULL:
            out.close()


class InExrom(int):
    """A breakpoint address in the EXROM (Machine.xsym): it stops only while the EXROM is paged in.
    Chunk 6 is EXROM or RAM, so an EXROM label's address is also an address of a program's code in
    image region 1, where a plain PC breakpoint would fire while the program runs (Phase 6)."""


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
    power_on = None             # Phase 9: f(machine) after reset-cpu, before the boot (tools/poweron.py)
    coverage = None             # Phase 9: a set: the ROM addresses executed (cov_harvest; tools/romcov.py)

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

    def xsym(self, n):
        """An EXROM label as a breakpoint address that ignores image region 1 (InExrom)."""
        return InExrom(self.S[n])

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
        """Arm breakpoints 1..n at the given PCs; clear 1..8 beyond. An InExrom address stops only
        with the EXROM paged in (BANK_EXROM_DEPTH nonzero)."""
        self._enable_bp()
        for i in range(1, 9):
            if i <= len(addrs):
                a = addrs[i - 1]
                if isinstance(a, InExrom):
                    self.cmd("set-breakpoint %d PC=%04XH and PEEK(%04XH)<>0" % (i, a, self.S["BANK_EXROM_DEPTH"]))
                else:
                    self.cmd("set-breakpoint %d PC=%04XH" % (i, a))
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
        with socket.socket() as probe:                  # another emulator on the port would take the commands
            if probe.connect_ex(("127.0.0.1", self.port)) == 0:
                raise RuntimeError("port %d is in use (an emulator left running?)" % self.port)
        self.proc = ZEsarUXProcess(ZESARUX, port=self.port, romfile=self.rom)
        self.out_path = os.path.join(self.snapdir, "zesarux.out")
        self.proc.stdout_path = self.out_path
        self.proc.start()
        self.c = ZRCP(port=self.port, timeout=60)
        self.c.connect(retries=100)
        self.cmd("enter-cpu-step")
        self.cmd("reset-cpu")
        if self.power_on:
            self.power_on(self)
        self._cov_on()
        self.tstates_reset()
        t0 = time.time()
        pc = self.run_to([self.sym("IO_READ_KEY")], boot_max)
        self.boot = dict(pc=pc, reached=pc == self.sym("IO_READ_KEY"), tstates=self.tstates(),
                         wall=time.time() - t0)
        if not self.boot["reached"]:
            raise AssertionError("boot did not reach IO_READ_KEY (PC=%04X)" % pc)
        self.cmd("snapshot-save " + self.snap)
        self.cov_harvest()
        self.glyphs = self._glyph_table()
        if self.coverage is not None:           # (the harness's own glyph rendering is no test)
            self.cmd("cpu-code-coverage clear")
        self.restore()
        return self

    def stop(self):
        try:
            if self.c:
                self.cov_harvest()
                self.c.quit()
        except Exception:
            pass
        finally:
            if self.proc:
                self.proc.stop()

    def restore(self):
        self.cov_harvest()
        self.cmd("snapshot-load " + self.snap)
        self._enable_bp()
        self._cov_on()

    # ------------------------------------------------------------- ROM coverage (Phase 9)
    def _cov_on(self):
        if self.coverage is not None:           # (every snapshot-load switches it off)
            self.cmd("cpu-code-coverage enabled yes")
            self.cmd("cpu-code-coverage clear")

    def cov_harvest(self):
        """Add the addresses executed since the last harvest to self.coverage. Chunk 6 is the EXROM or
        a compiled program's image region 1, whose code runs at the same addresses ($C000 up to the code's
        end, IMG_LIM): those are dropped, so an EXROM address counts only where no program's code was."""
        if self.coverage is None:
            return
        try:
            got = self.cmd("cpu-code-coverage get")
            self.cmd("cpu-code-coverage clear")
        except ZRCPError:
            return
        addrs = {int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{4}\b", got or "")}
        if any(0xC000 <= a < 0xE000 for a in addrs):
            lim = self.read(self.S["IMG_LIM"], 2)
            code_end = lim[0] | lim[1] << 8
            if 0xC000 < code_end <= 0xE000:
                addrs = {a for a in addrs if not 0xC000 <= a < code_end}
        self.coverage |= addrs

    # ------------------------------------------------------------- tape (Phase 7)
    def tape_insert(self, path):
        """Play `path` (.rwa, .tap, .tzx) through ZEsarUX's real-tape input (the EAR bit of port $FE), from
        now on in emulated time. ZEsarUX resets the machine on the insert and arms its autoload, which would
        type LOAD "" into the keyboard reads once the PC reaches AUTOLOAD_PC (a compiler routine in the Leap-C
        HOME); the harness disarms it at once: the trigger is reached for one instruction and its key
        sequence is drained by reads of a keyboard row it never answers, which ends it (envia_jload_desactivar).
        A second trigger must then press nothing (checked on the ENTER row). The machine is left in no useful
        state: the caller restores the booted editor (restore, Shell.boot / load), and the tape plays on."""
        self.cmd("realtape-open " + os.path.abspath(path))
        self.set_bps([])
        self.setreg("SP", RET_SLOT)
        self.setreg("PC", AUTOLOAD_PC)
        self.cmd("run 1")
        drain = bytes([0x01, 0xFE, 0xFE, 0x11, 0xD0, 0x07, 0xED, 0x78, 0x1B, 0x7A, 0xB3, 0x20, 0xF9, 0x18, 0xFE])
        self.write(0xFF10, drain)                       # ld bc,$FEFE; ld de,2000; in a,(c) ... jr $
        self.setreg("PC", 0xFF10)
        self.run(20_000)
        self.setreg("PC", AUTOLOAD_PC)
        self.cmd("run 1")
        probe = bytes([0x01, 0xFE, 0xBF, 0x16, 0xC8, 0x1E, 0xFF, 0xED, 0x78, 0xA3, 0x5F, 0x15, 0x20, 0xF9,
                       0x7B, 0x32, 0x40, 0xFF, 0x18, 0xFE])  # ld bc,$BFFE; ld d,200; ld e,$FF; in a,(c); and e...
        self.write(0xFF20, probe)
        self.setreg("PC", 0xFF20)
        self.run(20_000)
        if not self.read(0xFF40, 1)[0] & 1:
            raise RuntimeError("ZEsarUX's tape autoload is still armed (ENTER read on row $BF)")

    def tape_eject(self):
        """End any tape: a moment of silence replaces it (and is disarmed: tape_insert)."""
        p = os.path.join(self.snapdir, "silence.rwa")
        open(p, "wb").write(bytes([0x80]) * 64)
        self.tape_insert(p)

    def tape_capture(self, on=True):
        """The MIC signal of a SAVE: every `out (PORT_ULA), a` of HOME's STORAGE_SEND_BLOCK gets a breakpoint
        whose action prints TSTATESP * 16 + (A & 8) on ZEsarUX's standard output without stopping, so the
        transfer runs undisturbed. on=False clears them and returns the values printed since on=True
        (tapes.edges_from_capture)."""
        if on:
            lo, hi = self.sym("STORAGE_SEND_BLOCK"), self.sym("STORAGE_RECEIVE_BLOCK")
            code = self.read(lo, hi - lo)
            outs = [lo + i for i in range(len(code) - 1) if code[i:i + 2] == b"\xD3\xFE"]
            assert len(outs) == len(TAPE_SLOTS), "STORAGE_SEND_BLOCK: %d `out ($FE), a`" % len(outs)
            self._cap_at = os.path.getsize(self.out_path)
            for slot, a in zip(TAPE_SLOTS, outs):
                self.cmd("set-breakpoint %d PC=%04XH" % (slot, a))
                self.cmd("set-breakpointaction %d printe TSTATESP*16+(A&8)" % slot)
            return outs
        for slot in TAPE_SLOTS:
            self.cmd("set-breakpoint %d" % slot)
            self.cmd("set-breakpointaction %d" % slot)
        self.cmd("noop")
        time.sleep(0.2)
        with open(self.out_path, "rb") as f:
            f.seek(self._cap_at)
            lines = f.read().decode("latin-1").split("\n")
        return [int(l) for l in (x.strip() for x in lines) if l.lstrip("-").isdigit()]

    def _glyph_table(self):
        """Render chars 32..143 with the real GFX_PUTCHAR (A=char, B=row, C=col) and map each
        8x8 cell bitmap back to its character (as V2's qharness). Phase 5: chars 32..126 are also
        rendered with GFX_PUTCHAR_BOLD (the editor's keyword highlighting); `self.bold` maps those
        cells to their characters."""
        d = tempfile.mkdtemp(prefix="lcglyph-")
        src = ["    DEVICE ZXSPECTRUM48", "    ORG $%04X" % GLYPH_PROG, "    ld d,32", "    ld b,0",
               "    ld c,0", "    ld hl,$%04X" % self.sym("GFX_PUTCHAR"), "    ld e,144", "loop:", "    push de",
               "    push bc", "    push hl", "    ld a,d", "    call jphl", "    pop hl", "    pop bc", "    pop de",
               "    inc d", "    inc c", "    ld a,c", "    cp 32", "    jr nz,nx", "    ld c,0", "    inc b",
               "nx: ld a,d", "    cp e", "    jr nz,loop", "    ld a,e", "    cp 127", "    jr z,done",
               "    ld e,127", "    ld d,32", "    ld b,4", "    ld c,0", "    ld hl,$%04X" % self.sym("GFX_PUTCHAR_BOLD"),
               "    jr loop", "jphl: jp (hl)",
               "done: jr done", '    SAVEBIN "%s/g.bin", $%04X, $-$%04X' % (d, GLYPH_PROG, GLYPH_PROG)]
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
        self.plain_cells = {chr(ch): cell_from(scr, i // 32, i % 32) for i, ch in enumerate(range(32, 127))}
        self.bold = {}
        self.bold_cells = {}
        for i, ch in enumerate(range(32, 127)):
            cell = cell_from(scr, 4 + i // 32, i % 32)
            self.bold_cells[chr(ch)] = cell
            if cell not in table:
                self.bold.setdefault(cell, chr(ch))
        return table

    def screen_rows(self, scr=None, nrows=24, marks=False):
        """The screen's text rows (trailing spaces dropped). A cell that is no glyph reads as
        UNKNOWN; a bold glyph (the editor's keywords) reads as its character, or with marks=True
        as BOLD_MARK followed by it."""
        scr = scr if scr is not None else self.read(0x4000, 6144)
        rows = []
        for r in range(nrows):
            s = ""
            for col in range(32):
                cell = cell_from(scr, r, col)
                ch = self.glyphs.get(cell)
                if ch is None and cell in self.bold:
                    ch = (BOLD_MARK if marks else "") + self.bold[cell]
                if ch is None:
                    inv = bytes(255 - b for b in cell)
                    ch = self.glyphs.get(inv)
                    ch = ch.lower() if ch and ch.isalpha() else (UNKNOWN if ch is None else ch)
                s += ch
            rows.append(s.rstrip())
        return rows

    # ------------------------------------------------------------- Leap-C level
    def lib_load(self, name):
        """Phase 10: the library `name` (build/libs/NAME.bin) in image region 3 and LIB_LOADED set, as LIB "name"
        leaves them (the cassette suite and Fuse load libraries from tape). Its labels become symbols "lib:LABEL"
        (build/libs/NAME.sym). Returns the image."""
        img = open(os.path.join(LIBS, name + ".bin"), "rb").read()
        self.write(LX_BASE, img)
        self.write(self.sym("LIB_LOADED"), LX_BASE >> 8)
        for k, v in load_syms(os.path.join(LIBS, name + ".sym")).items():
            self.S["lib:" + k] = v
        return img

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
