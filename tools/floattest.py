#!/usr/bin/env python3
"""The float core on the production ROM against its bit-exact model (Phase 8; tools/fpmodel.py).

Every operation of the EXROM's float core (src/runtime/fpcore.asm) is called through the HOME
routine compiled code uses (F_X: the EXROM paged in, a BREAK-deferring section) or, for the
compiler's constants, the trampoline CX_FOLD, on operands chosen to cover the format: zeros, powers
of two, mantissas of all ones, both signs, exponents near the range's ends, random bit patterns, and
the integer boundaries. The result (F_ACC, HL or the flags) must equal the model's byte for byte, and
the model is checked against Python's own floating point (within the 32-bit mantissa's precision).

Usage: floattest.py [--port N] [--count N] [--seed N]    (as a module: run(m, count, seed) -> rows)
"""
import argparse
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fpmodel as F            # noqa: E402

LEFT = 0xE000                  # a binary operation's left operand (image region 2: free at the idle prompt)
TEXT = 0xE100                  # a constant's text (ATOF)
ERRSP = 0xE200                 # CC_SP for the error cases: CC_ERROR returns to the harness from here


def fop(name):
    return {"FRI": 0, "FRU": 1, "TOI": 2, "NEG": 3, "INC": 4, "DEC": 5, "PINC": 6, "PDEC": 7, "FTOA": 8,
            "ATOF": 9, "ADD": 0x80, "SUB": 0x82, "SUBR": 0x83, "MUL": 0x84, "DIV": 0x86, "DIVR": 0x87,
            "CMP": 0x88, "CMPR": 0x89}[name]


class Core:
    def __init__(self, m):
        self.m = m
        self.S = m.sym
        self.acc = m.sym("F_ACC")

    def op(self, name, acc=None, left=None, hl=0, c=0, routine="F_X"):
        m = self.m
        if acc is not None:
            m.write(self.acc, bytes(acc))
        if left is not None:
            m.write(LEFT, bytes(left))
            hl = LEFT
        m.setreg("AF", fop(name) << 8)
        m.setreg("HL", hl)
        m.setreg("BC", c)
        r = m.call(routine, maxi=5_000_000)
        rg = m.regs()
        return dict(ok=r["ok"], acc=m.read(self.acc, 5), hl=rg["HL"], f=rg["AF"] & 0xFF, pc=r["pc"])


def interesting(rng):
    """A float worth testing (5 bytes)."""
    k = rng.randrange(10)
    if k == 0:
        return bytes(5)
    s = rng.choice((0, 0x80))
    if k == 1:
        e = rng.choice((1, 2, 127, 128, 129, 130, 254, 255))
    elif k == 2:
        e = rng.randrange(120, 150)
    else:
        e = rng.randrange(1, 256)
    if k == 3:
        m = rng.choice((0, 0x7FFFFFFF, 0x7FFFFF00, 1, 0x40000000))
    else:
        m = rng.getrandbits(31)
    return bytes([e, s | m >> 24 & 0x7F, m >> 16 & 255, m >> 8 & 255, m & 255])


def near(rng):
    """Two floats close in magnitude (subtraction's cancellation)."""
    a = interesting(rng)
    b = bytearray(a)
    b[4] ^= rng.getrandbits(3)
    if rng.random() < 0.5:
        b[1] ^= 0x80
    return a, bytes(b)


def run(m, count=300, seed=8):
    rng = random.Random(seed)
    core = Core(m)
    m.restore()
    rows = []

    def check(what, got, want, info=""):
        rows.append(dict(case=what, ok=got == want, msg="" if got == want else "%s: ROM %r, model %r %s" % (
            what, got, want, info)))

    # ---- binary operations
    for name, sym, rev in (("ADD", "+", False), ("SUB", "-", False), ("SUBR", "-", True), ("MUL", "*", False),
                           ("DIV", "/", False), ("DIVR", "/", True)):
        for i in range(count):
            a, b = near(rng) if name in ("ADD", "SUB", "SUBR") and i % 3 == 0 else (interesting(rng), interesting(rng))
            left, right = (b, a) if rev else (a, b)     # rev: F_ACC is the left operand
            try:
                want = F.binop(sym, left, right).hex()
            except F.FloatError:
                want = "error"
            if want == "error":
                continue                                 # (the error path: below)
            r = core.op(name, acc=b, left=a)
            check("%s %s %s" % (name, a.hex(), b.hex()), r["acc"].hex() if r["ok"] else "PC=%04X" % r["pc"], want)
    # ---- comparisons: C less, Z equal
    for name, rev in (("CMP", False), ("CMPR", True)):
        for i in range(count):
            a = interesting(rng)
            b = a if i % 7 == 0 else (near(rng)[1] if i % 3 == 0 else interesting(rng))
            left, right = (b, a) if rev else (a, b)
            want = F.binop("cmp", left, right)
            r = core.op(name, acc=b, left=a)
            got = -1 if r["f"] & 1 else (0 if r["f"] & 0x40 else 1)
            check("%s %s %s" % (name, a.hex(), b.hex()), got if r["ok"] else "PC=%04X" % r["pc"], want)
    # ---- conversions
    ints = [0, 1, -1, 2, 255, 256, 32767, -32768, -32767, 12345, 40000, 65535, 0x8001] + \
        [rng.getrandbits(16) for _ in range(count)]
    for v in ints:
        for name, f in (("FRI", F.fri), ("FRU", F.fru)):
            r = core.op(name, hl=v & 0xFFFF)
            check("%s %d" % (name, v), r["acc"].hex(), f(v).hex())
    for i in range(count):
        a = interesting(rng) if i % 2 else F.encode(rng.uniform(-70000, 70000))
        r = core.op("TOI", acc=a)
        check("TOI %s" % a.hex(), r["hl"], F.toi(a))
    for i in range(count // 2):
        a = interesting(rng)
        r = core.op("NEG", acc=a)
        check("NEG %s" % a.hex(), r["acc"].hex(), F.neg(a).hex())
        for name, f in (("INC", F.inc), ("DEC", F.dec)):
            try:
                want = f(a).hex()
            except F.FloatError:
                continue
            r = core.op(name, acc=a)
            check("%s %s" % (name, a.hex()), r["acc"].hex(), want)
        r = core.op("PINC", acc=a)
        old = m.read(m.sym("F_OLD"), 5)
        try:
            check("PINC %s" % a.hex(), (r["acc"].hex(), old.hex()), (F.inc(a).hex(), a.hex()))
        except F.FloatError:
            pass
    # ---- the model against Python's floating point (32-bit mantissa: relative 2^-31)
    for i in range(count):
        x, y = rng.uniform(-1e6, 1e6), rng.uniform(-1e6, 1e6)
        a, b = F.encode(x), F.encode(y)
        for sym, real in (("+", lambda p, q: p + q), ("-", lambda p, q: p - q), ("*", lambda p, q: p * q),
                          ("/", lambda p, q: p / q)):
            want = real(F.value(a), F.value(b))
            got = F.value(F.binop(sym, a, b))
            tol = 2.0 ** -30 * (abs(want) if sym in "*/" else max(abs(F.value(a)), abs(F.value(b))))
            ok = abs(got - want) <= tol
            rows.append(dict(case="model %s" % sym, ok=ok, msg="" if ok else "model %r %s %r = %r, real %r" % (
                F.value(a), sym, F.value(b), got, want)))
    # ---- decimal constants (compile time, through CX_FOLD) and the output (printf's %f)
    texts = ["1.5", "0.1", "3.14159", "1e10", "2.5e-3", ".5", "1.", "100.0", "123456789012.5", "1e38", "1e-38",
             "1e-45", "0.0", "1.5f", "2.5L", "6.02E23", "1.0e+2", "007.25", "4294967295.0", "99999999999e-1"]
    texts += ["%d.%de%d" % (rng.randrange(1000), rng.randrange(1000), rng.randrange(-20, 20)) for _ in range(count // 4)]
    for t in texts:
        m.write(TEXT, (t + ";").encode())
        r = core.op("ATOF", hl=TEXT, routine="CX_FOLD")
        want, n = F.atof(t + ";")
        got = (m.read(m.sym("TOK_BUF"), 5).hex(), r["hl"] - TEXT)
        check("ATOF %s" % t, got, (want.hex(), n))
        real = float(t.rstrip("fFlL"))
        ok = real == 0 and F.value(want) == 0 or real != 0 and (abs(F.value(want) - real) <= abs(real) * 2e-9 or
                                                               abs(real) < 3e-39)
        rows.append(dict(case="ATOF value %s" % t, ok=ok, msg="" if ok else "%s -> %r" % (t, F.value(want))))
    for i in range(count):
        a = interesting(rng) if i % 3 else F.encode(rng.uniform(-1e5, 1e5))
        if a[0] > 200:
            continue
        p = rng.randrange(10)
        m.write(LEFT, a)
        r = core.op("FTOA", hl=LEFT, c=p)
        n = 0
        txt = m.read(r["hl"], 64)
        txt = txt[:txt.index(0)].decode() if 0 in txt else "?"
        check("FTOA %s %d" % (a.hex(), p), txt, F.ftoa(a, p))
    # ---- errors: overflow, division by 0, malformed constants (compile time: CC_ERROR with the error)
    def err_case(what, name, acc=None, left=None, hl=0, routine="F_X", want=16, text=None):
        m.restore()
        if text is not None:
            m.write(TEXT, (text + ";").encode())
        m.write(ERRSP, bytes([0x02, 0xFF]))             # CC_ERROR returns to STOP_ADDR ($FF02)
        m.poke16(m.sym("CC_SP"), ERRSP)
        m.write(m.sym("CC_ERRNUM"), 0)
        r = core.op(name, acc=acc, left=left, hl=hl, routine=routine)
        got = (r["ok"], m.read(m.sym("CC_ERRNUM"), 1)[0], m.read(m.sym("BANK_EXROM_DEPTH"), 1)[0])
        check(what, got, (True, want, 0))
    err_case("overflow *", "MUL", acc=bytes([0xF0, 0, 0, 0, 0]), left=bytes([0xA0, 0, 0, 0, 0]))
    err_case("overflow +", "ADD", acc=bytes([0xFF, 0x7F, 255, 255, 255]), left=bytes([0xFF, 0x7F, 255, 255, 255]))
    err_case("division by 0", "DIV", acc=bytes(5), left=F.ONE)
    for t, want in (("1e39", 16), ("1e", 15), ("1e+", 15), ("1.5x", 15), ("1..2", 15), ("1.2.3", 15), ("1.5_", 15),
                    ("0x1.5", 15), ("1.5e5e5", 15)):
        err_case("ATOF %s" % t, "ATOF", hl=TEXT, routine="CX_FOLD", want=want, text=t)
    m.restore()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10790)
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--seed", type=int, default=8)
    ap.add_argument("--build", default=os.path.join(os.path.dirname(HERE), "build"))
    a = ap.parse_args()
    from lcharness import Machine
    m = Machine(a.build, a.port)
    m.start()
    try:
        rows = run(m, a.count, a.seed)
    finally:
        m.stop()
    bad = [r for r in rows if not r["ok"]]
    for r in bad[:40]:
        print("FAIL", r["msg"])
    print("float core: %d/%d checks pass" % (len(rows) - len(bad), len(rows)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
