#!/usr/bin/env python3
"""Leap-C test runner (make test): boot, lexer and declaration tests in ZEsarUX.

Boot tests (production and test images): cold start reaches the shell's idle key wait with the
baseline layout in force (spec.md 3.1) and the start screen shown.

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

Usage: run_tests.py [--port N] [--only SUBSTR] [--suite boot,lexer,decl,exec,bench] [--json OUT]"""
import argparse
import glob
import json
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
from lcharness import Machine   # noqa: E402

ROOT = os.path.dirname(HERE)
EXEC_DIRS = ("expr", "experr", "golden", "run")
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
    out.append(("screen banner", rows[0] == "2068-LEAP-C" and rows[2] == "READY", repr(rows[:3])))
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
    # cold-cleared RAM: the Leap-C cells and the source region read 0 after boot (spot check)
    z = m.read(S("LEAPC_CELLS_BASE"), S("LEAPC_CELLS_END") - S("LEAPC_CELLS_BASE"))
    out.append(("Leap-C cells cleared", not any(z), ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10760)
    ap.add_argument("--only")
    ap.add_argument("--json", default=os.path.join(ROOT, "build", "test_results.json"))
    ap.add_argument("--suite", default="boot,lexer,decl,exec,bench")
    a = ap.parse_args()
    suites = a.suite.split(",")
    results = dict(boot={}, lexer=[], bench=[], decl=[], exec=[])
    failed = 0
    t_start = time.time()

    # ---- boot tests on both images
    for name, build in (("production", "build"), ("test", "build/test")):
        if "boot" not in suites:
            break
        m = Machine(os.path.join(ROOT, build), a.port)
        try:
            m.start()
            checks = boot_checks(m)
            results["boot"][name] = dict(boot_tstates=m.boot["tstates"],
                                         checks=[dict(name=n, ok=ok, detail=d) for n, ok, d in checks])
            for n, ok, d in checks:
                print("%s boot: %-38s %s %s" % (name, n, "PASS" if ok else "FAIL", d if not ok else ""))
                failed += not ok
            print("%s boot: cold start to idle prompt %d T-states" % (name, m.boot["tstates"]))
        finally:
            m.stop()

    # ---- declaration cases on the production image
    if "decl" in suites:
        m = Machine(os.path.join(ROOT, "build"), a.port)
        try:
            m.start()
            cases = sorted(glob.glob(os.path.join(ROOT, "tests", "decl", "**", "*.c"), recursive=True))
            if a.only:
                cases = [c for c in cases if a.only in c]
            npass = nerr = 0
            for c in cases:
                ok, msg, info = decltest.check_case(m, c)
                rel = os.path.relpath(c, ROOT)
                results["decl"].append(dict(case=rel, ok=ok, msg=msg, info=info))
                npass += ok
                if info and info["error"]:
                    nerr += ok
                if not ok:
                    failed += 1
                    print("decl: FAIL %s: %s" % (rel, msg))
            print("decl: %d/%d cases pass (%d declaration cases, %d error cases)" % (
                npass, len(cases), npass - nerr, nerr))
            if "bench" in suites and not a.only:
                results["decl_ws"] = declbench.measure(m)
                for r in results["decl_ws"]:
                    print("workspace: %-26s %5.1f B each   (%s)" % (r["what"], r["bytes_each"], r["detail"]))
        finally:
            m.stop()

    # ---- executable cases on the production image (M1.3)
    if "exec" in suites:
        m = Machine(os.path.join(ROOT, "build"), a.port)
        try:
            m.start()
            cases = []
            for d in EXEC_DIRS:
                cases += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
            if a.only:
                cases = [c for c in cases if a.only in c]
            counts = {}
            lines = tstates = 0
            for c in cases:
                ok, msg, info = exectest.check_case(m, c)
                rel = os.path.relpath(c, ROOT)
                results["exec"].append(dict(case=rel, ok=ok, msg=msg, info=info))
                group = rel.split(os.sep)[1]
                n, p = counts.get(group, (0, 0))
                counts[group] = (n + 1, p + ok)
                if ok and info and not info["error"]:
                    lines += info["lines"]
                    tstates += info["compile_t"]
                if not ok:
                    failed += 1
                    print("exec: FAIL %s: %s" % (rel, msg))
            if "bench" in suites and not a.only:
                results["helpers"] = helperbench.measure(m)
                for r in results["helpers"]:
                    failed += not r["ok"]
                    print("helper: %-58s %s %4s T %d B site %s" % (
                        r["name"], "PASS" if r["ok"] else "FAIL", r.get("tstates"), r.get("site_bytes", 0),
                        r["detail"]))
            if not a.only:
                # built-in: the machine is sane after a stack overflow -- a second program compiles
                # and runs in the same machine state (no snapshot restore in between)
                ov = c2src.lines_of(open(os.path.join(ROOT, "tests", "run", "stack_overflow.c")).read())
                r1 = exectest.compile_and_run(m, ov, audit=False)
                r2 = exectest.compile_and_run(m, ["int f(int x) { return x * 3; }", "int main(void) { return f(14); }"],
                                              restore=False)
                ok = (r1.ran and r1.a == 1 and r1.sp == 0xFF02 and r1.depth == 0 and r2.ran and r2.a == 0
                      and r2.hl == 42 and not r2.audit)
                msg = "" if ok else "overflow run a=%s sp=%04X; next run hl=%s a=%s %s" % (
                    r1.a, r1.sp, getattr(r2, "hl", None), getattr(r2, "a", None), r2.audit)
                results["exec"].append(dict(case="(built-in) recovery after a stack overflow", ok=ok, msg=msg,
                                            info=None))
                n, p = counts.get("run", (0, 0))
                counts["run"] = (n + 1, p + ok)
                if not ok:
                    failed += 1
                    print("exec: FAIL recovery after a stack overflow: " + msg)
            for g, (n, p) in sorted(counts.items()):
                print("exec %-8s %d/%d cases pass" % (g + ":", p, n))
            if lines:
                results["compile_speed"] = dict(lines=lines, tstates=tstates, t_per_line=tstates / lines,
                                                ms_per_line=tstates / lines / 3528.0)
                print("compile speed: %d lines in %d T = %.0f T/line (%.2f ms/line at 3.528 MHz)" % (
                    lines, tstates, tstates / lines, tstates / lines / 3528.0))
        finally:
            m.stop()

    # ---- lexer cases and throughput on the test image
    if "lexer" not in suites and "bench" not in suites:
        cases = []
    m = Machine(os.path.join(ROOT, "build", "test"), a.port)
    try:
        if "lexer" not in suites and "bench" not in suites:
            raise StopIteration
        m.start()
        cases = sorted(glob.glob(os.path.join(ROOT, "tests", "lexer", "**", "*.c"), recursive=True))
        if a.only:
            cases = [c for c in cases if a.only in c]
        if "lexer" not in suites:
            cases = []
        npass = 0
        for c in cases:
            ok, msg, info = check_lexer_case(m, c)
            rel = os.path.relpath(c, ROOT)
            results["lexer"].append(dict(case=rel, ok=ok, msg=msg, info=info))
            npass += ok
            if not ok:
                failed += 1
                print("lexer: FAIL %s: %s" % (rel, msg))
        if not a.only and "lexer" in suites:
            # built-in case: a truly empty line store (no records) gives one EOF token, line 1, at a
            # line start (a .c file always has at least its expectation line)
            m.restore()
            m.put_store(b"")
            m.write(TEST_AREA + 2, 0)
            r = m.call("TEST_LEX_DUMP", maxi=1_000_000)
            toks, err = decode_dump(m.read(TEST_DUMP_DATA, m.w16(TEST_AREA) - TEST_DUMP_DATA))
            ok = (r["ok"] and err is None and len(toks) == 1 and
                  toks[0].key() == (clex.TK["TK_EOF"], clex.TF_BOL, 1, None, None))
            results["lexer"].append(dict(case="(built-in) empty line store", ok=ok, msg="" if ok else repr(toks),
                                         info=None))
            npass += ok
            cases.append("(built-in) empty line store")
            if not ok:
                failed += 1
                print("lexer: FAIL empty line store: %r %s" % (toks, err))
            # built-in raw-record cases: line-store contents the editor and c2src.py never produce
            # (lines over 127 characters, bytes outside 32-126); the lexer must still be safe
            for name, lines, want in RAW_CASES:
                ok, msg = check_raw_case(m, lines, want)
                results["lexer"].append(dict(case="(built-in raw) " + name, ok=ok, msg=msg, info=None))
                cases.append("(built-in raw) " + name)
                npass += ok
                if not ok:
                    failed += 1
                    print("lexer: FAIL raw %s: %s" % (name, msg))
        if "lexer" in suites:
            print("lexer: %d/%d cases pass" % (npass, len(cases)))
        for b in sorted(glob.glob(os.path.join(ROOT, "tests", "bench", "*.c"))):
            if "bench" not in suites:
                break
            lines = c2src.lines_of(open(b, encoding="latin-1").read())
            recs = c2src.records(lines)
            # correctness of the sample first (full dump against the reference)
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
            results["bench"].append(row)
            failed += not row["ok"]
            print("bench %s: %s %d lines, %d text bytes, %d tokens, %s T = %.1f T/byte, %.0f T/token, "
                  "%.0f T/line (%.2f ms/line at 3.528 MHz)" % (
                      row["sample"], "PASS" if row["ok"] else "FAIL " + msg, row["lines"], text_bytes, ntok,
                      r["tstates"], row["t_per_byte"] or 0, row["t_per_token"] or 0, row["t_per_line"] or 0,
                      (row["t_per_line"] or 0) / 3528.0))
    except StopIteration:
        pass
    finally:
        m.stop()
    results["failed"] = failed
    results["wall_s"] = round(time.time() - t_start, 1)
    with open(a.json, "w") as f:
        json.dump(results, f, indent=1)
    print("TOTAL: %s (%d failures), %.0f s" % ("PASS" if not failed else "FAIL", failed, results["wall_s"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
