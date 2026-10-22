"""Fuse 1.9.1 qualification of the production ROMs (Phase 9, project_plan.md section 11: courtesy emulators).

Fuse is a second, independent emulator of the TS2068 (its own Z80 core, ULA/SCLD timing, keyboard
matrix, tape deck and loader detection), run headless through tools/fusedrive.py. Unlike ZEsarUX 13.0,
which runs its TS2068 with the 48K Spectrum's 50 Hz frame (69,888 T), Fuse uses the TS2068's own 60 Hz
frame (224 T x 262 lines = 58,688 T at 3.528 MHz): the frame rate a real machine has.

Cases (everything through the keyboard matrix, the screen read back with the ROM's glyphs):
  boot        the editor after a cold start; the status bar; one interrupt (FRAMES) per frame (60 Hz)
  keyboard    every printable character typed on the Leap-C key map (spec.md 6.2), the edit line and its
              screen row; a keyword shown bold
  typed       the workflow's typed programs (tools/e2etest.py TYPED): typed, RUN, the report and screen
  break       BREAK (CAPS SHIFT + SPACE) in a loop, in pause(), in a float loop, held 2 s: the report stays up
              while it is held (past the keyboard's auto-repeat delay) and waits for a key after
  frames      FRAMES counts every frame while a program runs: integer code, and float code, which pages the
              EXROM in and out for every operation (with V2's DI in the bank routines, 1% of the frame
              interrupts were lost there: the TS2068's INT lasts 32 T; delta D14)
  save        SAVE recorded by Fuse's tape deck; the recording LOADed back, the source identical
  wav         a program tape as audio (tapes.Tape.to_wav: the hardware kit's WAV), its samples played as a
              TZX direct recording (Fuse's libspectrum here reads no WAV), LOADed and RUN
  lib         (Phase 10) LIB "shapes" from its .tzx and LIB "testlib" from its WAV on Fuse's tape deck, the
              reports, programs typed and RUN with their functions, BREAK in the library's code, LIB alone
  corpus      the executable corpus (and the declaration cases): each program made a tape (tools/c2tape.py),
              LOADed by the ROM's own loader from Fuse's tape deck (traps off), RUN, its report and screen
              checked against the case's expectations; one Fuse session runs a whole slice (a soak of
              hundreds of LOAD/RUN cycles without a reset); (Phase 10) a case that needs a library gets it
              by LIB from the library's tape first (build/libs/NAME.tzx), and LIB alone unloads it after

Usage: fusetest.py [--workers N] [--json OUT] [--only SUBSTR] [CASE ...]   (default: every case)
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import c2tape           # noqa: E402
import exectest         # noqa: E402
import gen_diag         # noqa: E402
import tapes            # noqa: E402
from e2etest import TYPED, EXEC_DIRS, decl_expect  # noqa: E402
from fusedrive import Fuse, fuse_version, chord, BREAK, TPF  # noqa: E402

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
WORK = os.path.join(BUILD, "fuse")
MSGS = gen_diag.messages()
C_CHARS = ("abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 "
           "!\"#%&'()*+,-./:;<=>?[\\]^_{|}~ $@")
IGNORED = {"maxi", "noaudit", "mem", "golden", "region", "rundepth", "ay", "attr", "pixel", "cell", "breakpc",
           "stacklow", "breakdeferred"}     # memory-level expectations: the ZEsarUX suites check them
NAMED = {21, 22, 23, 52, 70, 76}            # the errors whose report names the identifier (Phase 9: 23; Phase 10)
LIBS = os.path.join(BUILD, "libs")


def new_fuse(name, speed=20000):
    d = os.path.join(WORK, name)
    shutil.rmtree(d, ignore_errors=True)
    return Fuse(BUILD, d, speed=speed).start()


# =========================================================================== reports
def image_size(f):
    d = f.peek(f.S["IMG_LIM"], 16)
    return exectest.image_size([(d[4 * k] | d[4 * k + 1] << 8, d[4 * k + 2] | d[4 * k + 3] << 8) for k in range(4)])


def memory_row(f):
    return "IMAGE %d B  HEAP %d B" % (image_size(f), exectest.heap_free(f.w16(f.S["PROG_END"])))


def undeclared_name(f, lines, line=None):
    name = f.peek(f.w16(f.S["NM_PTR"]), f.peek(f.S["NM_LEN"], 1)[0]).decode("latin-1")
    where = lines if not line or line > len(lines) else \
        [lines[line - 1]] + [l for l in lines if l.lstrip().startswith("#") and "define" in l]
    ok = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,30}", name) and any(
        re.search(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(name), l) for l in where)
    return name[:exectest.UNDECL_NAME_MAX] if ok else "<NM %r>" % name


def error_rows(f, n, line, lines):
    row = "LINE %d" % line
    if n in NAMED and f.peek(f.S["NM_LEN"], 1)[0]:
        row += "  '%s'" % undeclared_name(f, lines, line)
    return [gen_diag.report("E", n, MSGS), row]


def lib_command(f, name, path=None):
    """LIB "name" from the tape at `path` (default build/libs/NAME.tzx), or LIB alone (name None): the report or
    message; then a key back to the editor. Returns None, or what went wrong."""
    if name is None:
        f.command("lib")
        msg = f.rows()[23].rstrip()
        f.key(" ")
        return None if msg == "NO LIBRARY" and not f.peek(f.S["LIB_LOADED"], 1)[0] else "LIB alone showed %r" % msg
    r = f.cmd("tape_open %s" % (path or os.path.join(LIBS, name + ".tzx")))
    if r != "0":
        return "tape_open: %s" % r
    f.command('lib "%s"' % name, timeout=120)
    msg = f.rows()[22]
    f.key(" ")
    img = open(os.path.join(LIBS, name + ".bin"), "rb").read()
    want = "LIBRARY %s: %d FUNCTIONS" % (name, img[2])
    if msg != want or f.peek(0xF400, len(img)) != img or f.peek(f.S["LIB_LOADED"], 1)[0] != 0xF4:
        return "LIB showed %r, expected %r (image %s)" % (msg, want, f.peek(0xF400, len(img)) == img)
    return None


def editor_back(f, lines, line):
    """After the report's key: the editor, the cursor on `line` (0: the append line) and its text loaded."""
    bad = []
    rows = f.rows()
    if not rows[23].startswith("LINE "):
        bad.append("not back in the editor: row 23 %r" % rows[23])
    want = line - 1 if line else len(lines)
    if f.index() != want:
        bad.append("cursor on line %d, expected %d" % (f.index() + 1, want + 1))
    if line and f.edit_line() != lines[line - 1][:127]:
        bad.append("edit line %r" % f.edit_line())
    return bad


# =========================================================================== cases
CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


@case("boot")
def c_boot(out):
    f = new_fuse("boot")
    try:
        rows = f.rows()
        bad = []
        if any(rows[:23]) or rows[23] != "LINE 1/0":
            bad.append("editor screen %r" % rows[22:])
        attrs = f.peek(0x5800 + 23 * 32, 32)
        if attrs != bytes([7] * 29 + [0x10, 0x20, 0x08]):
            bad.append("status bar attributes %s" % attrs.hex())
        ed = f.peek(0x5800, 22 * 32)
        if any(a != 0x38 for a in ed[1:]):                 # (cell 0: the cursor's)
            bad.append("editor attributes not paper 7 ink 0")
        a, fa = f.ping()[0], f.w16(f.S["FRAMES"])
        f.wait_frames(600)
        b, fb = f.ping()[0], f.w16(f.S["FRAMES"])
        if abs((fb - fa) - (b - a)) > 1:
            bad.append("FRAMES +%d over %d frames" % (fb - fa, b - a))
        info = dict(boot_frames=f.boot["frames"], boot_tstates=f.boot["total"], frame_tstates=TPF,
                    isr_per_frame="%d/%d" % (fb - fa, b - a))
        out("fuse: boot: cold start to the editor's key wait in %d T (%d frames of %d T); FRAMES +%d in %d frames" % (
            f.boot["total"], f.boot["frames"], TPF, fb - fa, b - a))
        return not bad, "; ".join(bad), info
    finally:
        f.stop()


@case("keyboard")
def c_keyboard(out):
    f = new_fuse("keyboard")
    try:
        bad = []
        f.type(C_CHARS, enter=False)
        if f.edit_line() != C_CHARS:
            bad.append("edit line %r" % f.edit_line())
        rows = f.rows()
        if " ".join(rows[0:4]) != C_CHARS:             # (the editor wraps a long line at its spaces)
            bad.append("screen %r" % rows[0:4])
        f.chords([[0x100]])                     # ENTER: stored as line 1
        if f.store() != [C_CHARS]:
            bad.append("stored %r" % f.store())
        f.new()
        f.type("int x;")                        # (a line is highlighted once the cursor leaves it)
        marked = f.rows(marks=True)[0]
        if marked != "•i•n•t x;":
            bad.append("keyword not bold: %r" % marked)
        return not bad, "; ".join(bad), dict(chars=len(C_CHARS))
    finally:
        f.stop()


@case("typed")
def c_typed(out):
    f = new_fuse("typed")
    fails, n = [], 0
    try:
        for name, lines, screen, report, keys, _matrix in TYPED:
            n += 1
            report, row23, col = (report + (None,))[:3] if isinstance(report, tuple) else (report, None, None)
            f.enter_program(lines)
            bad = []
            if f.store() != lines:
                bad.append("stored %r" % f.store())
            rows = f.run(keys=[chr(k) for k in keys or []])
            if rows[22] != report:
                bad.append("report %r, expected %r" % (rows[22], report))
            elif report.startswith("EXIT"):
                if rows[23] != memory_row(f):
                    bad.append("memory row %r, expected %r" % (rows[23], memory_row(f)))
            elif row23 is not None and rows[23] != row23:
                bad.append("row 23 %r, expected %r" % (rows[23], row23))
            elif report.startswith("ERROR") and rows[23] != "LINE %d" % f.w16(f.S["CC_ERRLINE"]) and row23 is None:
                bad.append("row 23 %r" % rows[23])
            if screen is not None:
                want = [screen.get(r, "") for r in range(22)]
                if rows[:22] != want:
                    bad.append("screen %r" % [r for r in rows[:22] if r])
            f.key(" ")
            if col is not None and f.w16(f.S["EDIT_BUF_OFFSET"]) != col:
                bad.append("cursor at column %d, expected %d" % (f.w16(f.S["EDIT_BUF_OFFSET"]), col))
            if bad:
                fails.append("%s: %s" % (name, "; ".join(bad)))
        out("fuse: typed: %d/%d typed programs pass" % (n - len(fails), n))
        return not fails, "; ".join(fails), dict(programs=n)
    finally:
        f.stop()


BREAK_PROGRAMS = [
    ("loop", ["int main(void)", "{", "    unsigned n = 0;", "    for (;;) n++;", "}"]),
    ("pause", ["int main(void)", "{", "    pause(30000);", "    return 1;", "}"]),
    ("float", ["int main(void)", "{", "    float x = 1;", "    for (;;) x = x * 1.0001 / 1.0001;", "}"]),
]


@case("break")
def c_break(out):
    f = new_fuse("break")
    fails = []
    try:
        for name, lines in BREAK_PROGRAMS:
            f.enter_program(lines)
            f.to_append_line()
            f.chords([chord(c) for c in "run"] + [[0x100]], settle=False)
            f.wait_frames(120)
            if f.at_key_wait():
                fails.append("%s: the program ended before BREAK: %r" % (name, f.rows()[22:]))
                f.key(" ")
                continue
            for k in BREAK:                     # held 2 s, past the ISR's auto-repeat delay (35 frames):
                f.cmd("press %d" % k)           # the report must stay up until the release, then wait
            try:
                f.wait_frames(120)
                held = f.rows()[22:24]
            finally:
                for k in reversed(BREAK):
                    f.cmd("release %d" % k)
            f.wait(f.at_key_wait, 60, "the report's key wait")
            rows = f.rows()
            if held != ["BREAK", "LINE 1"] or rows[22:24] != ["BREAK", "LINE 1"]:
                fails.append("%s: report while BREAK held %r, after %r" % (name, held, rows[22:24]))
            f.key(" ")
            fails += ["%s: %s" % (name, b) for b in editor_back(f, lines, 1)]
        return not fails, "; ".join(fails), dict(programs=len(BREAK_PROGRAMS))
    finally:
        f.stop()


FRAMES_PROGRAMS = [
    ("integer", ["int main(void) {", "    unsigned i, s;", "    s = 0;", "    for (;;)",
                 "        for (i = 0; i < 1000; i++) s += i;", "    return 0;", "}"]),
    ("float", ["int main(void) {", "    float x;", "    x = 1.5;", "    for (;;) x = x * 1.0001 + 0.5;",
               "    return 0;", "}"]),
]


@case("frames")
def c_frames(out):
    f = new_fuse("frames")
    fails, info = [], {}
    try:
        for name, lines in FRAMES_PROGRAMS:
            f.enter_program(lines)
            f.to_append_line()
            f.chords([chord(c) for c in "run"] + [[0x100]], settle=False)
            f.wait_frames(120)
            e0, f0 = f.ping()[0], f.w16(f.S["FRAMES"])
            f.wait_frames(6000, timeout=300)
            e1, f1 = f.ping()[0], f.w16(f.S["FRAMES"])
            info[name] = dict(frames=e1 - e0, counted=(f1 - f0) & 0xFFFF)
            if info[name]["counted"] != info[name]["frames"]:
                fails.append("%s: FRAMES counted %d of %d frames" % (name, info[name]["counted"], info[name]["frames"]))
            for _ in range(20):
                f.hold(BREAK, 5)
                if f.at_key_wait():
                    break
            f.key(" ")
        return not fails, "; ".join(fails), info
    finally:
        f.stop()


SAVE_PROGRAM = ["/* SAVE on Fuse */", "int square(int n) { return n * n; }", "int main(void)", "{",
                '    printf("%d %s", square(12), "SAVED");', "    return square(5);", "}"]


def load_tape(f, path, name, timeout=120):
    """LOAD "" from the tape file at `path`: the LOADED message, a key back to the editor."""
    r = f.cmd("tape_open %s" % path)
    if r != "0":
        return "tape_open %s: %s" % (path, r)
    f.command('load ""', timeout=timeout)
    msg = f.rows()[22]
    f.key(" ")
    return None if msg == "LOADED %s" % name else "LOAD showed %r" % msg


@case("save")
def c_save(out):
    f = new_fuse("save")
    bad = []
    try:
        f.enter_program(SAVE_PROGRAM)
        f.cmd("tape_rec_start")
        f.command('save "fusesave"')
        msg = f.rows()[22]
        f.key(" ")
        f.cmd("tape_rec_stop")
        rec = os.path.join(f.wdir, "recorded.tzx")
        r = f.cmd("tape_write %s" % rec)
        if msg != "SAVED fusesave" or r != "0" or not os.path.exists(rec):
            bad.append("SAVE %r, tape_write %s" % (msg, r))
        else:
            listing = subprocess.run(["tzxlist", rec], capture_output=True, text=True).stdout
            f.new()
            e = load_tape(f, rec, "fusesave")
            if e:
                bad.append("the recording: " + e)
            elif f.store() != SAVE_PROGRAM:
                bad.append("loaded %r" % f.store())
            else:
                rows = f.run()
                if rows[0] != "144 SAVED" or rows[22] != "EXIT 25":
                    bad.append("run %r %r" % (rows[0], rows[22]))
                f.key(" ")
            shutil.copy(rec, os.path.join(WORK, "fuse_saved.tzx"))
            out("fuse: save: the recording (%s): %s" % (os.path.join("build", "fuse", "fuse_saved.tzx"),
                                                       " / ".join(l.strip() for l in listing.split("\n")
                                                                  if l.strip().startswith("Block type"))))
        return not bad, "; ".join(bad), None
    finally:
        f.stop()


@case("wav")
def c_wav(out):
    f = new_fuse("wav")
    bad = []
    try:
        blocks = c2tape.program_blocks("\n".join(SAVE_PROGRAM) + "\n", "wavprog")
        wav = tapes.Tape().file(blocks).to_wav()            # (the hardware kit's audio: tools/hwkit.py)
        tzx = os.path.join(f.wdir, "wavprog.tzx")           # (Fuse 1.9.1's libspectrum reads no WAV: its
        open(tzx, "wb").write(tapes.tzx_from_wav(*tapes.read_wav(wav)))   # samples as a direct recording)
        e = load_tape(f, tzx, "wavprog")
        if e:
            bad.append(e)
        elif f.store() != SAVE_PROGRAM:
            bad.append("loaded %r" % f.store())
        else:
            rows = f.run()
            if rows[0] != "144 SAVED" or rows[22] != "EXIT 25":
                bad.append("run %r %r" % (rows[0], rows[22]))
        return not bad, "; ".join(bad), None
    finally:
        f.stop()


LIB_SHAPES = ["int main(void)", "{", "    circle(128, 96, 40);", "    box(10, 10, 60, 40);",
              '    printf("%u", isqrt(10000));', "    return isqrt(1000);", "}"]
LIB_SPIN = ["int spin(void)", "{", "    return t_spin(30000);", "}", "int main(void)", "{", "    return spin();", "}"]


@case("lib")
def c_lib(out):
    f = new_fuse("lib")
    bad = []
    try:
        e = lib_command(f, "shapes")                        # the .tzx: lib2tape's standard speed blocks
        if e:
            bad.append("shapes: " + e)
        f.enter_program(LIB_SHAPES)
        rows = f.run()
        if rows[0] != "100" or rows[22] != "EXIT 31" or rows[23] != memory_row(f):
            bad.append("shapes run %r %r" % (rows[0], rows[22:24]))
        f.key(" ")
        wav = open(os.path.join(LIBS, "testlib.wav"), "rb").read()   # the WAV, as a direct recording
        tzx = os.path.join(f.wdir, "testlib_wav.tzx")
        open(tzx, "wb").write(tapes.tzx_from_wav(*tapes.read_wav(wav)))
        e = lib_command(f, "testlib", tzx)
        if e:
            bad.append("testlib: " + e)
        f.enter_program(LIB_SPIN)                           # BREAK in the library's own code (image region 3)
        f.to_append_line()
        f.chords([chord(c) for c in "run"] + [[0x100]], settle=False)
        f.wait_frames(60)
        if f.at_key_wait():
            bad.append("the program ended before BREAK: %r" % f.rows()[22:])
        for k in BREAK:                                     # (the report waits for the release)
            f.cmd("press %d" % k)
        try:
            f.wait_frames(60)
        finally:
            for k in reversed(BREAK):
                f.cmd("release %d" % k)
        f.wait(f.at_key_wait, 60, "the report's key wait")
        rows = f.rows()
        if rows[22:24] != ["BREAK", "LINE 1"]:
            bad.append("BREAK in the library %r" % rows[22:24])
        f.key(" ")
        e = lib_command(f, None)
        if e:
            bad.append(e)
        f.enter_program(["int main(void)", "{", "    return t_args(1, 2, 3);", "}"])
        rows = f.run()
        if rows[22:24] != ["ERROR 70: UNDEFINED FUNCTION", "LINE 3  't_args'"]:
            bad.append("after LIB alone %r" % rows[22:24])
        f.key(" ")
        return not bad, "; ".join(bad), None
    finally:
        f.stop()


# =========================================================================== the corpus
def corpus_cases(only=None):
    out = []
    for d in EXEC_DIRS + ("decl",):
        out += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
    return [c for c in out if not only or only in c]


def expectations(path):
    """(lines, want) for a corpus case, or (None, why) when it cannot run in this suite: want is
    ("exit", n) | ("error", n, line) | ("rterror", n, line or None) | ("nomain",), with "screen": {row: text}."""
    text, exp = exectest.parse_case(path)
    try:
        lines = c2src.lines_of(text)
        c2tape.program_blocks(text, "t")
    except c2src.SourceError as e:
        return None, "not a tape: %s" % e
    keys = {k for k, _ in exp}
    if keys & {"keys", "break"}:
        return None, "needs the keyboard during the run (the ZEsarUX suites)"
    want = {"screen": {}}
    for k, body in exp:
        if k == "expect":
            t = body.split()
            if t[0] == "exit":
                want["kind"] = ("exit", int(t[1], 0) & 0xFFFF)
            elif t[0] == "error":
                want["kind"] = ("error", exectest.ER[t[1]], int(t[2]))
            elif t[0] == "rterror":
                want["kind"] = ("rterror", int(t[1], 0))
        elif k == "rtline":
            want["rtline"] = int(body)
        elif k == "screen":
            row, _, txt = body.partition(" ")
            want["screen"][int(row)] = txt
        elif k == "library":
            want["library"] = body.strip()
    if os.sep + "decl" + os.sep in path:
        de = decl_expect(path)
        want["kind"] = ("error",) + de if de else ("nomain",)
    if "kind" not in want:
        return None, "no exit, error or runtime error expected"
    return lines, want


def check_corpus_case(f, path, lines, want, tapedir):
    lib = want.get("library")                   # (Phase 10) the library the case needs: LIB from its tape, or
    if lib != getattr(f, "library", None):      # LIB alone to unload the one loaded for the case before
        e = lib_command(f, lib)
        if e:
            return False, e
        f.library = lib
    tap = os.path.join(tapedir, "case.tap")
    open(tap, "wb").write(tapes.tap(c2tape.program_blocks("\n".join(lines) + "\n", "case")))
    e = load_tape(f, tap, "case")
    if e:
        return False, e
    if f.store() != lines:
        return False, "loaded source differs"
    rows = f.run()
    kind = want["kind"]
    bad = []
    if kind[0] == "exit":
        ex = kind[1] - 65536 if kind[1] & 0x8000 else kind[1]
        exp = ["EXIT %d" % ex, memory_row(f)]
        line = 0
    elif kind[0] == "error":
        exp = error_rows(f, kind[1], kind[2], lines)
        line = kind[2]
    elif kind[0] == "nomain":                   # a declaration case: NO MAIN FUNCTION, or (with a main) it runs
        if rows[22].startswith("EXIT"):
            exp, line = [rows[22], memory_row(f)], 0
        else:
            line = len(lines)
            exp = [gen_diag.report("E", 71, MSGS), "LINE %d" % line]
    else:
        line = want.get("rtline") or f.w16(f.S["RT_ERRLINE"])
        exp = [gen_diag.report("RT", kind[1], MSGS), "LINE %d" % line if line else ""]
    if rows[22:24] != exp:
        bad.append("report %r, expected %r" % (rows[22:24], exp))
    for r, txt in want["screen"].items():
        if r < 22 and rows[r] != txt.rstrip():
            bad.append("screen row %d %r, expected %r" % (r, rows[r], txt))
    f.key(" ")
    bad += editor_back(f, lines, line)
    return not bad, "; ".join(bad)


def corpus_worker(k, n, only, q):
    f = new_fuse("corpus%d" % k)
    tapedir = os.path.join(WORK, "corpus%d-tapes" % k)
    os.makedirs(tapedir, exist_ok=True)
    rows, frames, sessions = [], 0, 1
    try:
        for path in corpus_cases(only)[k::n]:
            rel = os.path.relpath(path, ROOT)
            lines, want = expectations(path)
            if lines is None:
                rows.append(dict(case=rel, ok=None, msg=want))
                continue
            try:
                ok, msg = check_corpus_case(f, path, lines, want, tapedir)
            except Exception as e:                          # noqa: BLE001 -- a hung session: a new Fuse
                ok, msg = False, "harness: %s: %s" % (type(e).__name__, e)
                frames += f.ping()[0] if f.proc.poll() is None else 0
                f.stop()
                f = new_fuse("corpus%d" % k)
                sessions += 1
            rows.append(dict(case=rel, ok=ok, msg=msg))
        rows.append(dict(case="#session", ok=True, msg="", frames=frames + f.ping()[0], sessions=sessions))
    finally:
        f.stop()
        q.put(rows)


def run_corpus(workers, only, out):
    q = mp.Queue()
    ps = [mp.Process(target=corpus_worker, args=(k, workers, only, q), daemon=True) for k in range(workers)]
    for p in ps:
        p.start()
    rows = []
    try:
        for _ in ps:
            rows += q.get()
        for p in ps:
            p.join()
    finally:
        for p in ps:
            if p.is_alive():
                p.terminate()
    sessions = [r for r in rows if r["case"] == "#session"]
    rows = sorted((r for r in rows if r["case"] != "#session"), key=lambda r: r["case"])
    ran = [r for r in rows if r["ok"] is not None]
    for r in ran:
        if not r["ok"]:
            out("fuse: FAIL corpus %s: %s" % (r["case"], r["msg"]))
    skipped = [r for r in rows if r["ok"] is None]
    frames = sum(s["frames"] for s in sessions)
    out("fuse: corpus: %d/%d programs pass, each LOADed from tape and RUN (%d sessions, %d frames = %.0f emulated "
        "minutes at 60 Hz); %d left to the ZEsarUX suites (keys or BREAK during the run, or no outcome to check)" % (
            sum(r["ok"] for r in ran), len(ran), sum(s["sessions"] for s in sessions), frames, frames / 60.0 / 60,
            len(skipped)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 4) - 1)))
    ap.add_argument("--json", default=os.path.join(BUILD, "fuse_results.json"))
    ap.add_argument("--only")
    ap.add_argument("cases", nargs="*")
    a = ap.parse_args()
    names = a.cases or [n for n, _ in CASES] + ["corpus"]
    os.makedirs(WORK, exist_ok=True)
    t0 = time.time()
    print("fuse: Fuse %s, TS2068 (--machine ts2068), production images %s" % (
        fuse_version(), open(os.path.join(BUILD, "SHA256SUMS")).read().split()[0][:16]), flush=True)
    results, failed = {}, 0
    for name, fn in CASES:
        if name not in names:
            continue
        try:
            ok, detail, info = fn(lambda s: print(s, flush=True))
        except Exception as e:                              # noqa: BLE001
            ok, detail, info = False, "%s: %s" % (type(e).__name__, e), None
        failed += not ok
        results[name] = dict(ok=ok, detail=detail, info=info)
        print("fuse: %-10s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""), flush=True)
    if "corpus" in names:
        rows = run_corpus(a.workers, a.only, lambda s: print(s, flush=True))
        failed += sum(1 for r in rows if r["ok"] is False)
        results["corpus"] = rows
    results["failed"] = failed
    results["wall_s"] = round(time.time() - t0, 1)
    json.dump(results, open(a.json, "w"), indent=1)
    print("fuse: TOTAL %s (%d failures), %.0f s" % ("PASS" if not failed else "FAIL", failed, time.time() - t0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
