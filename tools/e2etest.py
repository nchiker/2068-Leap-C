#!/usr/bin/env python3
"""Leap-C compile/run workflow tests (project_plan.md Phase 6), suite `e2e` of make test.

Everything runs on the production ROM from its booted editor and goes through the shell's real RUN
path (the `run` command typed on the append line, SH_COMPILE, RT_RUN, the report, a key back to the
editor):
  - typed programs: 25 programs typed key by key (tools/shelltest.py: the ISR's latch, and for four
    of them the real keyboard matrix), run, and their screens and reports checked; the editor's
    store must hold exactly the typed lines;
  - the corpus: every executable program of the test corpus (tests/expr ... tests/mem) injected into
    the line store and RUN through the shell (exectest.check_case with shell=...: the case's own
    expectations, the report, the cursor on the error's line, the banking invariants armed); the
    declaration corpus too (a compile error, or NO MAIN FUNCTION, reported with the cursor on its
    line). The compile speed over the corpus is measured from the shell's compiles;
  - the diagnostics: every message of include/leapc_errors.inc produced by the EXROM's table
    (DG_APPEND), STRING TOO LONG through a line the editor cannot make, every compile error number
    seen through the shell;
  - the reports: the exit status (negative, void main, exit() from depth), the image's size
    (against the declarations' sizes), the free heap (malloc() of exactly that succeeds and one byte
    more fails), FREE.

Usage: e2etest.py [--port N] [--shard K/N] [--group typed,report,corpus] [substring ...]
"""
import argparse
import glob
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2src                                                    # noqa: E402
import exectest                                                 # noqa: E402
import gen_diag                                                 # noqa: E402
import shelltest                                                # noqa: E402
from decltest import ER                                         # noqa: E402
from lcharness import Machine, UNKNOWN                          # noqa: E402
from shelltest import Shell, ENTER, Z_ENTER, expect             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEC_DIRS = ("expr", "experr", "golden", "run", "stmt", "stmterr", "pp", "pperr", "lib", "rt", "mem")
CASES = []


def case(name, title, group):
    def deco(fn):
        CASES.append((name, title, group, fn))
        return fn
    return deco


# ===================================================================== typed programs
# (name, lines, screen rows {row: text} (the others blank), report row 22, keys during the run, matrix)
TYPED = [
    ("hello", ["int main(void)", "{", '    puts("HELLO, WORLD");', "    return 0;", "}"],
     {0: "HELLO, WORLD"}, "EXIT 0", None, True),
    ("sum-loop", ["int main(void)", "{", "    int i, s = 0;", "    for (i = 1; i <= 10; i++)", "        s += i;",
                  '    printf("%d\\n", s);', "    return s;", "}"],
     {0: "55"}, "EXIT 55", None, False),
    ("factorial", ["int fact(int n)", "{", "    if (n < 2) return 1;", "    return n * fact(n - 1);", "}",
                   "int main(void)", "{", '    printf("%d", fact(7));', "    return 0;", "}"],
     {0: "5040"}, "EXIT 0", None, False),
    ("fibonacci", ["int main(void)", "{", "    int a = 0, b = 1, t, k;", "    for (k = 0; k < 10; k++) {",
                   '        printf("%d ", a);', "        t = a + b; a = b; b = t;", "    }", "    return a;", "}"],
     {0: "0 1 1 2 3 5 8 13 21 34"}, "EXIT 55", None, False),
    ("strings", ["char buf[20];", "int main(void)", "{", '    strcpy(buf, "ABC");', '    strcat(buf, "DEF");',
                 "    puts(buf);", '    printf("%d", strlen(buf));', "    return strcmp(buf, \"ABCDEF\");", "}"],
     {0: "ABCDEF", 1: "6"}, "EXIT 0", None, False),
    ("array-pointer", ["int v[5] = {1, 2, 3, 4, 5};", "int main(void)", "{", "    int *p = v, *q = v + 4, t;",
                       "    while (p < q) { t = *p; *p++ = *q; *q-- = t; }",
                       "    for (t = 0; t < 5; t++) printf(\"%d\", v[t]);", "    return v[0];", "}"],
     {0: "54321"}, "EXIT 5", None, True),
    ("struct", ["struct point { int x, y; };", "int main(void)", "{", "    struct point p, *q = &p;",
                "    p.x = 3; q->y = 4;", '    printf("%d", p.x * p.x + q->y * q->y);', "    return sizeof p;", "}"],
     {0: "25"}, "EXIT 4", None, False),
    ("switch", ["void say(int n)", "{", "    switch (n) {", '    case 1: print("ONE "); break;',
                '    case 2: print("TWO "); break;', '    default: print("MANY ");', "    }", "}",
                "int main(void)", "{", "    int i;", "    for (i = 1; i <= 3; i++) say(i);", "    return 0;", "}"],
     {0: "ONE TWO MANY"}, "EXIT 0", None, False),
    ("do-while", ["int main(void)", "{", "    int n = 5;", '    do printf("%d", n); while (--n);', "    return n;", "}"],
     {0: "54321"}, "EXIT 0", None, False),
    ("alphabet", ["int main(void)", "{", "    char c;", "    for (c = 'A'; c <= 'Z'; c++)", "        putchar(c);",
                  "    return 'Z' - 'A';", "}"],
     {0: "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}, "EXIT 25", None, False),
    ("define", ["#define N 12", "#define SQ (N * N)", "int main(void)", "{", '    printf("%d", SQ);', "    return N;", "}"],
     {0: "144"}, "EXIT 12", None, False),
    ("bitwise", ["int main(void)", "{", "    unsigned a = 0xF0, b = 0x3C;",
                 '    printf("%x %x %x %x", a & b, a | b, a ^ b, ~a & 0xFF);', "    return !(a && b) || 0;", "}"],
     {0: "30 fc cc f"}, "EXIT 0", None, True),
    ("static-local", ["int counter(void)", "{", "    static int n;", "    return ++n;", "}", "int main(void)", "{",
                      '    printf("%d ", counter());', '    printf("%d ", counter());', '    printf("%d", counter());',
                      "    return counter();", "}"],
     {0: "1 2 3"}, "EXIT 4", None, False),
    ("negative", ["int main(void)", "{", '    printf("%d", -1234);', "    return -5;", "}"],
     {0: "-1234"}, "EXIT -5", None, False),
    ("exit-deep", ["void quit(int n)", "{", '    puts("BYE");', "    exit(n * 6);", "}", "int main(void)", "{",
                   "    quit(7);", "    return 1;", "}"],
     {0: "BYE"}, "EXIT 42", None, False),
    ("at-print", ["int main(void)", "{", "    at(5, 10);", '    print("X");', "    at(7, 0);", "    tab(3);",
                  '    print("Y");', "    return 0;", "}"],
     {5: "          X", 7: "   Y"}, "EXIT 0", None, False),
    ("itoa-atoi", ["char b[8];", "int main(void)", "{", "    itoa(255, b, 16);", "    puts(b);",
                   '    printf("%d", atoi("123") + 1);', "    return abs(-9);", "}"],
     {0: "ff", 1: "124"}, "EXIT 9", None, False),
    ("malloc", ["int main(void)", "{", "    char *p = malloc(100);", "    if (!p) return 1;", '    strcpy(p, "HEAP OK");',
                "    puts(p);", "    free(p);", "    return 0;", "}"],
     {0: "HEAP OK"}, "EXIT 0", None, False),
    ("fn-pointer", ["int add(int a, int b) { return a + b; }", "int mul(int a, int b) { return a * b; }",
                    "int main(void)", "{", "    int (*op[2])(int, int);", "    op[0] = add; op[1] = mul;",
                    '    printf("%d %d", op[0](2, 3), op[1](2, 3));', "    return op[1](6, 7);", "}"],
     {0: "5 6"}, "EXIT 42", None, True),
    ("goto", ["int main(void)", "{", "    int i = 0;", "again:", '    printf("%d", i);', "    if (++i < 4) goto again;",
              "    return i;", "}"],
     {0: "0123"}, "EXIT 4", None, False),
    ("getkey", ["int main(void)", "{", "    int k = getkey();", "    putchar(k);", "    return k;", "}"],
     {0: "Q"}, "EXIT 81", [ord("Q")], False),
    ("graphics", ["int main(void)", "{", "    draw(0, 0, 10, 10);", '    printf("%d %d", point(5, 5), point(5, 6));',
                  "    return point(10, 10);", "}"],
     {0: "1 0", 1: " " + UNKNOWN}, "EXIT 1", None, False),
    ("printf-width", ["int main(void)", "{", '    printf("[%5d][%3s][%c]", 42, "ab", 65);', "    return 0;", "}"],
     {0: "[   42][ ab][A]"}, "EXIT 0", None, False),
    ("runtime-error", ["int main(void)", "{", '    puts("BEFORE");', "    beep(1, 99);", "    return 0;", "}"],
     {0: "BEFORE"}, "RUNTIME ERROR 4: BAD ARGUMENT", None, False),
    ("compile-error", ["int main(void)", "{", "    int total = 0;", "    totl = 5;", "    return total;", "}"],
     None, "ERROR 23: UNDECLARED IDENTIFIER", None, False),
]


def type_program(sh, lines, matrix):
    """Type the program on the append line, line by line (ENTER after each), on the keyboard matrix
    or through the ISR's latch."""
    for l in lines:
        if matrix:
            for ch in l:
                sh.press(ch)
            sh.press_code([Z_ENTER])
        else:
            sh.type(l)


def typed_case(name, lines, screen, report, keys, matrix):
    def fn(sh):
        m, S = sh.m, sh.S
        sh.boot()
        type_program(sh, lines, matrix)
        stored = sh.store()
        msg = sh.type("run")
        for k in keys or []:                    # the program waits for a key: deliver it
            if msg is not None:
                break
            msg = sh.key(k)
        rows = sh.rows()
        errline = None
        if report.startswith("ERROR"):
            errline = m.w16(S("CC_ERRLINE"))
        elif report.startswith("RUNTIME") or report == "BREAK":
            errline = m.w16(S("RT_ERRLINE"))
        sh.key(ord(" "))
        bad = []
        if stored != lines:
            bad.append("stored %r" % stored)
        if not isinstance(msg, tuple) or msg[0] != report:
            bad.append("report %r, expected %r" % (msg, report))
        elif report.startswith("EXIT"):
            want = "IMAGE %d B  HEAP %d B" % (m.w16(S("SH_IMAGE_SIZE")), exectest.heap_free(m.w16(S("PROG_END"))))
            if msg[1] != want:
                bad.append("memory report %r, expected %r" % (msg[1], want))
        elif errline and msg[1] != "LINE %d" % errline:
            bad.append("line report %r (line %d)" % (msg[1], errline))
        if rows[22:24] != list(msg or ("", "")):
            bad.append("rows 22-23 %r" % rows[22:24])
        if screen is not None:
            want_rows = [screen.get(r, "") for r in range(22)]
            if rows[:22] != want_rows:
                bad.append("screen %r" % [r for r in rows[:22] if r])
        if not sh.in_editor():
            bad.append("not back in the editor")
        if errline:
            if sh.index() != errline - 1 or sh.edit_line() != lines[errline - 1]:
                bad.append("cursor on line %d %r, expected %d" % (sh.index() + 1, sh.edit_line(), errline))
        elif sh.index() != len(lines):
            bad.append("cursor on line %d" % (sh.index() + 1))
        if sh.store() != lines:
            bad.append("source changed")
        return expect(not bad, "; ".join(bad))
    return fn


for _i, (_n, _l, _s, _r, _k, _mx) in enumerate(TYPED):
    case("typed-%02d-%s" % (_i + 1, _n), "typed%s, RUN: %s" % (" on the keyboard matrix" if _mx else "", _r),
         "typed")(typed_case(_n, _l, _s, _r, _k, _mx))


# ===================================================================== diagnostics
@case("diag-table", "the EXROM's message table (DG_APPEND) gives the text of include/leapc_errors.inc for every compile "
                    "and runtime error, and nothing for numbers without a message", "report")
def diag_table(sh):
    m, S = sh.m, sh.S
    msgs = gen_diag.messages()
    bad = []
    keys = [(n, n, "%d: %s" % (n, t)) for (k, n), t in msgs.items() if k == "E"]
    keys += [(n, gen_diag.DG_RT + n, "%d: %s" % (n, t)) for (k, n), t in msgs.items() if k == "RT" and n != 5]
    keys += [(n, n, "%d: " % n) for n in (0, 2, 18, 19, 30, 39, 43, 56, 69, 77, 93, 99, 102, 127)]
    keys += [(5, gen_diag.DG_RT + 5, "5: "), (7, gen_diag.DG_RT + 7, "7: ")]
    buf = S("SH_REPORT_BUF")
    for shown, key, want in keys:
        sh.boot()
        m.setreg("AF", shown << 8)
        m.setreg("BC", key)
        m.setreg("DE", buf)
        r = m.call("DG_APPEND", maxi=200_000)
        got = m.read(buf, 33).split(b"\0")[0].decode("latin-1")
        if not r["ok"] or got != want:
            bad.append("key %d: %r, expected %r" % (key, got, want))
    n_e = sum(1 for k in msgs if k[0] == "E")
    return expect(not bad and n_e == 40, "%d compile messages; %s" % (n_e, bad[:6]))


@case("diag-string-too-long", "STRING TOO LONG (a line longer than the editor makes, injected): the report, the cursor "
                              "on the line with its first 127 characters", "report")
def diag_string_too_long(sh):
    long_line = '    char *s = "' + "B" * 140 + '";'
    src = ["int main(void)", "{", long_line, "    return 0;", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    sh.key(ord(" "))
    ok = msg == ("ERROR 17: STRING TOO LONG", "LINE 3") and sh.index() == 2 and sh.edit_line() == long_line[:127]
    return expect(ok, "msg=%r index=%d edit=%r" % (msg, sh.index(), sh.edit_line()[:30]))


# ===================================================================== reports
def _run(sh, src):
    sh.load(src, len(src))
    msg = sh.type("run")
    sh.key(ord(" "))
    return msg


@case("report-exit-status", "the exit status: main's value (signed), 0 for a void main, exit()'s argument from a nested "
                            "call, the extremes", "report")
def report_exit(sh):
    got = []
    for src, want in ((["int main(void) { return -32768; }"], "EXIT -32768"),
                      (["int main(void) { return 32767; }"], "EXIT 32767"),
                      (["unsigned main(void) { return 65535; }"], "EXIT -1"),
                      (["void main(void) { puts(\"V\"); }"], "EXIT 0"),
                      (["void f(int d) { if (d) f(d - 1); else exit(-7); }", "int main(void) { f(20); return 1; }"],
                       "EXIT -7")):
        msg = _run(sh, src)
        got.append((msg[0] if msg else None, want))
    return expect(all(a == b for a, b in got), "%r" % got)


@case("report-image-size", "IMAGE: the code below CG_PC and the static data the declarations need (globals, a string, "
                           "the function -> line records, 6 B each)", "report")
def report_image(sh):
    m, S = sh.m, sh.S
    src = ["int a;", "char b[10];", "int c[3] = {1, 2, 3};", "int f(int x) { return x + a; }",
           'int main(void) { puts("HI"); return f(2); }']
    msg = _run(sh, src)
    data = 2 + 10 + 6 + len("HI") + 1 + 6 * 2
    code = m.w16(S("CG_PC")) - 0xC000
    want = "IMAGE %d B  HEAP %d B" % (code + data, exectest.heap_free(m.w16(S("PROG_END"))))
    lim = exectest.memguard.limits(m)
    return expect(msg == ("EXIT 2", want) and lim[0][1] == 0xE000 - data,
                  "msg=%r, expected %r (code %d, data %d; region 1 %r)" % (msg, want, code, data, lim[0]))


@case("report-heap-real", "HEAP is the largest block malloc() gives: malloc(HEAP) succeeds, malloc(HEAP + 1) returns "
                          "NULL, in a program of the same length", "report")
def report_heap(sh):
    def prog(n):
        return ["int main(void)", "{", "    return malloc(%5d) != 0;" % n, "}"]
    msg = _run(sh, prog(0))
    heap = int(msg[1].split("HEAP ")[1].split()[0])
    m1 = _run(sh, prog(heap))
    m2 = _run(sh, prog(heap + 1))
    return expect(m1[0] == "EXIT 1" and m2[0] == "EXIT 0" and 10000 <= heap < 99999,
                  "heap %d: malloc(heap) %r, malloc(heap + 1) %r" % (heap, m1, m2))


@case("report-image-hires", "#pragma hires at the top: region 4 reserved and not counted in IMAGE; mode(1) allowed",
      "report")
def report_hires(sh):
    m, S = sh.m, sh.S
    src = ["#pragma hires", "int g = 5;", "int main(void) { mode(1); return g; }"]
    msg = _run(sh, src)
    lim = exectest.memguard.limits(m)
    code = lim[0][0] - 0xC000
    data = 0xE000 - lim[0][1]
    return expect(msg is not None and msg[0] == "EXIT 5" and lim[3] == (0x7800, 0x7800)
                  and msg[1].startswith("IMAGE %d B" % (code + data)), "msg=%r limits=%r" % (msg, lim))


@case("cmd-free", "FREE (any case, trailing spaces) on an empty source, after typing, and after a RUN: SOURCE, FREE, "
                  "IMAGE (the last compile's), HEAP; the editor is left as it was", "report")
def cmd_free(sh):
    m, S = sh.m, sh.S
    sh.boot()
    r1 = sh.type("FREE")
    sh.key(ord(" "))                             # (the key that ends a report is not typed)
    lines = ["int main(void)", "{", "    return 7;", "}"]
    for l in lines:
        sh.type(l)
    r2 = sh.type("free  ")
    sh.key(ord(" "))
    size = sum(len(l) + 3 for l in lines)
    sh.type("run")
    sh.key(ord(" "))
    image = m.w16(S("SH_IMAGE_SIZE"))
    r3 = sh.type("Free")
    sh.key(ord(" "))
    after = (sh.store(), sh.index(), sh.in_editor())
    want = [("SOURCE 0 B  FREE 18432 B", "IMAGE 0 B  HEAP 18428 B"),
            ("SOURCE %d B  FREE %d B" % (size, 18432 - size), "IMAGE 0 B  HEAP %d B" % exectest.heap_free(0x7800 + size)),
            ("SOURCE %d B  FREE %d B" % (size, 18432 - size),
             "IMAGE %d B  HEAP %d B" % (image, exectest.heap_free(0x7800 + size)))]
    ok = [r1, r2, r3] == want and image > 0 and after == (lines, 4, True) and sh.rows()[23] == "LINE 5/4"
    return expect(ok, "got %r, expected %r; after %r" % ([r1, r2, r3], want, after))


@case("report-over-program", "a report covers only rows 22-23: the program's rows 0-21 stay; the report's colours (white "
                             "on black, the swatch); the next key redraws the editor", "report")
def report_over(sh):
    m = sh.m
    src = ["int main(void)", "{", "    int r;", "    paper(2); cls();", "    for (r = 0; r < 23; r++) {",
           "        at(r, 0);", '        printf("ROW%d", r);', "    }", "    return 0;", "}"]
    sh.load(src, len(src))
    msg = sh.type("run")
    rows = sh.rows()
    attrs = m.read(0x5800 + 21 * 32, 96)
    sh.key(ord(" "))
    ok = (all(rows[r] == "ROW%d" % r for r in range(22)) and rows[22:24] == list(msg)
          and attrs[:32] == bytes([0x10] * 32) and attrs[32:64] == bytes([7] * 32)
          and attrs[64:] == bytes([7] * 29 + [0x10, 0x20, 0x08]) and sh.rows()[0] == "int main(void)")
    return expect(ok, "rows %r msg %r attrs %s" % (rows[20:], msg, attrs.hex()))


# ===================================================================== the corpus through the shell's RUN
def corpus(only=None):
    out = []
    for d in EXEC_DIRS + ("decl",):
        out += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
    return [c for c in out if not only or any(o in c for o in only)]


def decl_expect(path):
    for l in open(path, encoding="latin-1"):
        s = l.strip()
        if s.startswith("// expect: error"):
            t = s.split()
            return ER[t[3]], int(t[4])
    return None


def check_decl(m, sh, path):
    """A declaration case through RUN: its expected error, or NO MAIN FUNCTION (it has no main): the
    report and the cursor (exectest.check_report)."""
    lines = c2src.lines_of(open(path, encoding="latin-1").read())
    res = exectest.compile_and_run(m, lines, shell=sh, invariants=True)
    want = decl_expect(path)
    msgs = []
    if not res.compile_ok:
        return False, "compile did not return: %s" % res.violation, None
    got = (res.errnum, res.errline) if res.errnum else None
    if want and got != want:
        msgs.append("compile gave %r, expected %r" % (got, want))
    if not want and (not got or got[0] != ER["E_NOMAIN"]) and not res.ran:
        msgs.append("compile gave %r, expected NO MAIN FUNCTION" % (got,))
    msgs += res.violation
    msgs += exectest.check_report(m, res, lines)
    return not msgs, "; ".join(msgs), dict(error=got, compile_t=res.compile_t, lines=len(lines), report=res.report)


def run_corpus(m, sh, paths, out=print):
    rows = []
    for p in paths:
        rel = os.path.relpath(p, ROOT)
        try:
            if os.sep + "decl" + os.sep in p:
                ok, msg, info = check_decl(m, sh, p)
            else:
                ok, msg, info = exectest.check_case(m, p, shell=sh, invariants=True)
        except Exception as e:                          # noqa: BLE001 -- a harness failure: restart
            ok, msg, info = False, "harness: %r" % e, None
            m.stop()
            m.start()
        rows.append(dict(case=rel, ok=ok, msg=msg, info=info))
        if not ok:
            out("e2e: FAIL corpus %s: %s" % (rel, msg))
    return rows


def summarise_corpus(rows):
    """Compile speed through the shell (cases that compiled and have lines) and the compile error
    numbers reported through the shell."""
    lines = t = 0
    errs = set()
    for r in rows:
        i = r.get("info") or {}
        if r["ok"] and i.get("error"):
            errs.add(i["error"][0])
        elif r["ok"] and i.get("compile_t") and not i.get("error"):
            lines += i["lines"]
            t += i["compile_t"]
    return dict(lines=lines, tstates=t, ms_per_line=t / lines / 3528.0 if lines else None, errors=sorted(errs))


# ===================================================================== running
def run_cases(m, sh, names, out=print):
    rows = []
    for name, title, group, fn in CASES:
        if name not in names:
            continue
        try:
            ok, detail = fn(sh)
        except Exception as e:                          # noqa: BLE001 -- a case that crashes fails
            ok, detail = False, "%s: %s" % (type(e).__name__, e)
        rows.append(dict(case=name, title=title, ok=ok, detail=detail))
        out("e2e: %-34s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10780)
    ap.add_argument("--group", default="typed,report,corpus")
    ap.add_argument("only", nargs="*")
    a = ap.parse_args()
    groups = a.group.split(",")
    m = Machine(os.path.join(ROOT, "build"), a.port)
    t0 = time.time()
    failed = 0
    try:
        m.start()
        sh = Shell(m)
        names = [n for n, _, g, _ in CASES if g in groups and (not a.only or any(o in n for o in a.only))]
        rows = run_cases(m, sh, names)
        failed += sum(not r["ok"] for r in rows)
        if "corpus" in groups:
            crow = run_corpus(m, sh, corpus(a.only or None))
            failed += sum(not r["ok"] for r in crow)
            s = summarise_corpus(crow)
            print("e2e: corpus through RUN: %d/%d pass; compile speed %s ms per line (%d lines); compile errors "
                  "reported: %s" % (sum(r["ok"] for r in crow), len(crow),
                                    "%.2f" % s["ms_per_line"] if s["ms_per_line"] else "-", s["lines"], s["errors"]))
    finally:
        m.stop()
    print("e2e: %d failures (%.0f s)" % (failed, time.time() - t0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
