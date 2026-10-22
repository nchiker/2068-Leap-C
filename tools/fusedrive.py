"""Fuse 1.9.1 as a second, independent emulator for the Leap-C ROMs (Phase 9).

Fuse runs headless (SDL's dummy video driver, no sound; --speed 20000: about 7,700 frames a second, 130 times
a real machine, where Fuse saturates one host core) with the production images as its TS2068 ROMs
(--rom-ts2068-0 HOME, --rom-ts2068-1 EXROM), and is driven through tools/fuse/fuseshim.c, an LD_PRELOAD
library that answers commands on a Unix socket once per emulated frame (see its header). Only Fuse's
own emulation is used: keys go into its keyboard matrix as a person would press them, the debugger's
breakpoints observe, tapes go through its tape deck as signals (tape traps off, so the ROM's own loader
reads the EAR bit). Nothing in the ROM is test-only.

The key handshake (as the ZEsarUX harness's Shell.press): the shim presses a chord only while the machine
waits for a key (its PC, or at the frame's interrupt the PC it interrupted, in IO_READ_KEY's loop), and
holds it until IO_LATCH_AND_CLEAR has run: a debugger breakpoint, set before the emulation starts, counts
those runs in RAM the ROM leaves unused (ACC, in $FF00-$FFFF: spec.md 3.1). Typing is paced by the
machine, not by the clock, at any Fuse speed.

The screen is read from Fuse's memory and decoded with the ROM's own glyphs (lcharness: rendered once by
the real GFX_PUTCHAR in ZEsarUX and cached per ROM hash in build/fuse/; the glyphs are the ROM's data,
not an emulator's).
"""
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lcharness import Machine, load_syms, UNKNOWN  # noqa: E402,F401

ROOT = os.path.dirname(HERE)
FUSE = os.environ.get("LEAPC_FUSE", "/usr/local/bin/fuse")
SHIM_SRC = os.path.join(HERE, "fuse", "fuseshim.c")
SHIM_SYMS = ("memory_map_read", "z80", "frames_since_reset", "tstates", "keyboard_press", "keyboard_release",
             "debugger_command_evaluate", "writebyte_internal", "tape_open", "tape_write", "tape_record_start",
             "tape_record_stop", "tape_is_playing", "tape_toggle_play")
MEMORY_PAGE_SIZE = 32       # sizeof(memory_page) in fuseshim.c (x86-64)
PROCESSOR_SIZE = 52         # sizeof(processor) (z80/z80.h) with SP and PC at 26 and 28, as fuseshim.c reads them
TPF = 224 * 262             # Fuse's TS2068 frame: 224 T a line, 262 lines (libspectrum timings.c)
ACC = 0xFFF1                # the handshake's key-acceptance counter
K_ENTER, K_CAPS, K_SYM = 0x100, 0x101, 0x102
SYM_KEYS = {"<": "r", ">": "t", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "_": "0", ")": "9", "(": "8",
            "'": "7", "&": "6", '"': "p", ";": "o", "]": "u", "[": "y", "=": "l", "+": "k", "-": "j", "^": "h",
            ".": "m", ",": "n", "*": "b", ":": "z", "?": "c", "/": "v", "~": "a", "|": "s", "\\": "d", "{": "f",
            "}": "g"}


def chord(ch):
    """The keys that type `ch` on the Leap-C key map (spec.md 6.2): Fuse keyboard_key_name values."""
    if ch == "\n":
        return [K_ENTER]
    if ch == " ":
        return [0x20]
    if ch.islower() or ch.isdigit():
        return [ord(ch)]
    if ch.isupper():
        return [K_CAPS, ord(ch.lower())]
    return [K_SYM, ord(SYM_KEYS[ch])]


DELETE = [K_CAPS, ord("0")]
DOWN = [K_CAPS, ord("6")]
BREAK = [K_CAPS, 0x20]


def build_shim(build):
    out = os.path.join(build, "fuse", "fuseshim.so")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(SHIM_SRC):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        cflags = subprocess.run(["sdl2-config", "--cflags"], capture_output=True, text=True).stdout.split()
        subprocess.run(["gcc", "-shared", "-fPIC", "-O2", "-Wall"] + cflags + ["-o", out, SHIM_SRC, "-ldl"], check=True)
    return out


def fuse_syms():
    """Offsets of the shim's Fuse entry points (nm of the unstripped binary), and the check that the
    shim's memory_page is Fuse's (memory_map_read holds 32 of them: 2 KB pages over 64 K)."""
    out, sizes = {}, {}
    for l in subprocess.run(["nm", "-S", FUSE], capture_output=True, text=True, check=True).stdout.split("\n"):
        p = l.split()
        if len(p) == 4:
            out[p[3]], sizes[p[3]] = p[0], int(p[1], 16)
        elif len(p) == 3:
            out.setdefault(p[2], p[0])
    missing = [n for n in SHIM_SYMS if n not in out]
    if missing:
        raise RuntimeError("Fuse binary lacks %s (not 1.9.1, or stripped)" % missing)
    if sizes.get("memory_map_read") != 32 * MEMORY_PAGE_SIZE or sizes.get("z80") != PROCESSOR_SIZE:
        raise RuntimeError("Fuse's memory_page or processor is not the shim's (%r, %r B)" % (
            sizes.get("memory_map_read"), sizes.get("z80")))
    return ",".join("%s=%s" % (n, out[n]) for n in SHIM_SYMS)


def fuse_version():
    r = subprocess.run([FUSE, "--version"], capture_output=True, text=True)
    m = re.search(r"version (\S+)\.", r.stdout + r.stderr)
    return m.group(1) if m else "?"


def glyph_tables(build, port=10898):
    """The ROM's glyph tables (Machine.glyphs, .bold), rendered by the real GFX_PUTCHAR in ZEsarUX,
    cached in build/fuse/glyphs-<HOME hash>.json."""
    h = hashlib.sha256(open(os.path.join(build, "leapc_home.bin"), "rb").read()).hexdigest()[:16]
    p = os.path.join(build, "fuse", "glyphs-%s.json" % h)
    if not os.path.exists(p):
        m = Machine(build, port)
        try:
            m.start()
            data = dict(glyphs={k.hex(): v for k, v in m.glyphs.items()}, bold={k.hex(): v for k, v in m.bold.items()})
        finally:
            m.stop()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(data, open(p, "w"))
    d = json.load(open(p))
    return ({bytes.fromhex(k): v for k, v in d["glyphs"].items()}, {bytes.fromhex(k): v for k, v in d["bold"].items()})


class _Glyphs:
    def __init__(self, glyphs, bold):
        self.glyphs, self.bold = glyphs, bold


class Fuse:
    """One headless Fuse running the Leap-C images in `build`, its files in `wdir`."""

    def __init__(self, build, wdir, speed=20000, extra=None):
        self.build = os.path.abspath(build)
        self.wdir = os.path.abspath(wdir)
        self.speed = speed
        self.extra = extra or []
        self.S = load_syms(os.path.join(self.build, "leapc_home.sym"), os.path.join(self.build, "leapc_exrom.sym"))
        self.proc = self.sock = None
        self.g = _Glyphs(*glyph_tables(self.build))
        self.boot = None

    # ------------------------------------------------------------------ process
    def start(self, timeout=60):
        os.makedirs(self.wdir, exist_ok=True)
        home = os.path.join(self.wdir, "home")
        os.makedirs(home, exist_ok=True)
        self.sock_path = "\0leapc-fuse-%d-%d" % (os.getpid(), id(self))   # (abstract: no path length limit)
        self.out_path = os.path.join(self.wdir, "fuse.out")
        S = self.S
        # before the emulation starts: the handshake counters, and the boot's first key wait printed once
        # (Fuse's parser refuses a newline after the last command)
        dbg = ("break 0x%04x\ncommands 1\nset 0x%04x ([0x%04x]+1)&255\ncontinue\nend\n"
               "tbreak 0x%04x\ncommands 2\nprint 0xb0070\nprint spectrum:frames\nprint ula:tstates\ncontinue\nend" % (
                   S["IO_LATCH_AND_CLEAR"], ACC, ACC, S["IO_READ_KEY"]))
        self.nbp = 2
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", LD_PRELOAD=build_shim(self.build),
                   LEAPC_FUSE_SOCK="@" + self.sock_path[1:], LEAPC_FUSE_SYMS=fuse_syms(), HOME=home, XDG_CONFIG_HOME=home)
        args = [FUSE, "--machine", "ts2068", "--rom-ts2068-0", os.path.join(self.build, "leapc_home.bin"),
                "--rom-ts2068-1", os.path.join(self.build, "leapc_exrom.bin"), "--no-sound", "--speed", str(self.speed),
                "--no-auto-load", "--no-traps", "--no-confirm-actions", "--no-autosave-settings",
                "--debugger-command", dbg] + self.extra
        self.out = open(self.out_path, "w")
        self.proc = subprocess.Popen(args, env=env, stdout=self.out, stderr=subprocess.STDOUT, cwd=self.wdir)
        t0 = time.time()
        while True:
            try:
                self.sock = socket.socket(socket.AF_UNIX)
                self.sock.connect(self.sock_path)
                break
            except OSError:
                self.sock.close()
                if self.proc.poll() is not None or time.time() - t0 > timeout:
                    self.stop()
                    raise RuntimeError("Fuse did not start: %s" % open(self.out_path).read()[-500:])
                time.sleep(0.05)
        self.f = self.sock.makefile("rw")
        try:
            self.wait(lambda: self.prints(0xB0070), timeout, "the boot's first key wait")
        except Exception:
            self.stop()
            raise
        frames, t = self.prints(0xB0070)[0]
        self.boot = dict(frames=frames, tstates=t, total=frames * TPF + t)
        return self

    def stop(self):
        try:
            if self.sock:
                self.f.write("quit\n")
                self.f.flush()
        except OSError:
            pass
        if self.proc:
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()                    # (SIGKILL: a halted Fuse ignores SIGTERM)
                self.proc.wait()
        if self.sock:
            self.sock.close()
        self.sock = None

    # ------------------------------------------------------------------ shim
    def cmd(self, line):
        self.f.write(line + "\n")
        self.f.flush()
        r = self.f.readline().strip()
        if not r.startswith("ok"):
            raise RuntimeError("fuseshim: %r -> %r" % (line, r))
        return r[3:]

    def ping(self):
        a, b = self.cmd("ping").split()
        return int(a), int(b)

    def peek(self, a, n):
        return bytes.fromhex(self.cmd("peek %d %d" % (a, n)))

    def w16(self, a):
        b = self.peek(a, 2)
        return b[0] | b[1] << 8

    def poke(self, a, data):
        for i in range(0, len(data), 4096):
            self.cmd("poke %d %s" % (a + i, data[i:i + 4096].hex()))

    def dbg(self, text):
        self.cmd("dbg " + text.replace("\n", "\\n"))

    def output(self):
        """Fuse's standard output so far (the debugger's prints, as 0x... lines)."""
        self.out.flush()
        return open(self.out_path, encoding="latin-1").read()

    def prints(self, marker):
        """The groups of values printed after each `print MARKER` line: [(v1, v2, ...)]."""
        vals = [int(l, 16) for l in self.output().split() if re.fullmatch(r"0x[0-9a-f]+", l)]
        out, i = [], 0
        while i < len(vals):
            if vals[i] == marker:
                j = i + 1
                while j < len(vals) and vals[j] < 0xB0000:
                    j += 1
                out.append(tuple(vals[i + 1:j]))
                i = j
            else:
                i += 1
        return out

    def wait(self, cond, timeout, what):
        t0 = time.time()
        while not cond():
            if self.proc.poll() is not None:
                raise RuntimeError("Fuse exited waiting for %s" % what)
            if time.time() - t0 > timeout:
                raise TimeoutError("Fuse: %s not reached in %d s" % (what, timeout))
            time.sleep(0.01)

    def wait_frames(self, n, timeout=120):
        f0 = self.ping()[0]
        self.wait(lambda: self.ping()[0] >= f0 + n, timeout, "%d frames" % n)

    # ------------------------------------------------------------------ keyboard
    def chords(self, seq, timeout=300, settle=True):
        """Type the chords in `seq` (lists of key codes) with the handshake; returns when the last one was
        accepted and (settle) the machine has come back to a key wait."""
        lo = self.S["IO_READ_KEY"]
        for i in range(0, len(seq), 200):
            part = seq[i:i + 200]
            self.cmd("chords %d %d %d %s" % (ACC, lo, lo + 6, " ".join("+".join(str(k) for k in c) for c in part)))
            last = settle or i + 200 < len(seq)
            self.wait(lambda: self.cmd("queue") == "0 1" if last else self.cmd("queue").startswith("0 "),
                      timeout, "the keys typed")

    def type(self, text, enter=True, timeout=300):
        self.chords([chord(c) for c in text] + ([[K_ENTER]] if enter else []), timeout)

    def key(self, ch=" ", timeout=300):
        self.chords([chord(ch)], timeout)

    def hold(self, keys, frames):
        """Keys held for `frames` frames, then released (no handshake: BREAK)."""
        for k in keys:
            self.cmd("press %d" % k)
        try:
            self.wait_frames(frames)
        finally:
            for k in reversed(keys):
                self.cmd("release %d" % k)

    def at_key_wait(self):
        return self.cmd("queue").split()[1] == "1"

    # ------------------------------------------------------------------ screen
    def screen(self):
        return self.peek(0x4000, 6912)

    def rows(self, scr=None, marks=False):
        scr = scr if scr is not None else self.screen()
        return Machine.screen_rows(self.g, scr[:6144], marks=marks)

    def edit_line(self):
        b = self.peek(self.S["EDIT_LINE_BUF"], 128)
        return b.split(b"\0")[0].decode("latin-1")

    # ------------------------------------------------------------------ shell level
    def to_append_line(self):
        """The cursor down (CAPS SHIFT + 6) to the empty line after the program, where commands are typed
        (after an error report the cursor is on the error's line)."""
        lines = self.store()
        n = len(lines)
        for _ in range(sum(len(l) // 24 + 1 for l in lines) + 2):    # (DOWN moves a wrapped line's rows)
            if self.index() >= n:
                return
            self.chords([DOWN])
        if self.index() < n:
            raise RuntimeError("the cursor does not reach the append line (index %d of %d)" % (self.index(), n))

    def command(self, text, timeout=300):
        """A shell command typed on the append line, then ENTER."""
        self.to_append_line()
        self.type(text, timeout=timeout)

    def new(self):
        self.command("new")

    def enter_program(self, lines):
        """NEW, then the program typed line by line on the append line (ENTER after each)."""
        self.new()
        text = "".join(l + "\n" for l in lines)
        self.chords([chord(c) for c in text])

    def run(self, keys=None, timeout=600):
        """RUN; then keys (characters) delivered while the program waits; returns the screen's rows (the
        report on 22-23)."""
        self.command("run", timeout=timeout)
        for k in keys or []:
            self.key(k, timeout=timeout)
        r = self.rows()
        return r

    def store(self):
        """The line store's text lines."""
        S = self.S
        base, end = S["PROG_AREA_START"], self.w16(S["PROG_END"])
        data, out, p = self.peek(base, end - base), [], 0
        while p + 2 <= len(data):                   # [len:2][text][CR], len counting the CR
            n = data[p] | data[p + 1] << 8
            out.append(data[p + 2:p + 2 + n - 1].decode("latin-1"))
            p += 2 + n
        return out

    def index(self):
        return self.w16(self.S["CUR_EDIT_INDEX"])
