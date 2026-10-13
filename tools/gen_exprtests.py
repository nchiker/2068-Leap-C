#!/usr/bin/env python3
"""Generate the operator test cases in tests/expr/gen/ (project_plan.md M1.3).

The expected results come from a Python model of Leap-C's integer semantics (spec.md 4.2-4.4),
written from the specification, not from the ROM: 16-bit int and unsigned int, unsigned char,
signed char; the integer promotions and the usual arithmetic conversions; two's complement
wraparound; division truncating toward zero, the remainder with the dividend's sign, division by
zero giving 0; `>>` arithmetic for a signed left operand; shift counts above 15 shifting every bit
out (as the compiler's constant folding does).

Every case evaluates its operator in several code shapes, so each template path of the code
generator is exercised: parameters, globals, locals, function results on both sides (held and
spilled operands), a constant right operand and a constant left operand. The results go to the
global array r[]; the case checks r[] byte for byte after the run (`// mem:`).

Usage: gen_exprtests.py [--out tests/expr/gen]   (rewrites the directory's generated cases)
"""
import argparse
import glob
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CTYPE = {"char": "char", "schar": "signed char", "int": "int", "uint": "unsigned"}
VALUES = {
    "char": [0, 1, 7, 127, 128, 200, 255],
    "schar": [-128, -100, -1, 0, 1, 7, 127],
    "int": [-32768, -32767, -300, -7, -1, 0, 1, 2, 7, 255, 300, 32767],
    "uint": [0, 1, 2, 7, 255, 300, 32767, 32768, 65534, 65535],
}


def conv(v, t):
    """Value v converted to type t (C89 6.2.1.2 as Leap-C implements it)."""
    if t in ("char", "schar"):
        v &= 0xFF
        return v - 256 if t == "schar" and v & 0x80 else v
    v &= 0xFFFF
    return v - 65536 if t == "int" and v & 0x8000 else v


def promote(t):
    return "int" if t in ("char", "schar") else t


def usual(ta, tb):
    ta, tb = promote(ta), promote(tb)
    return "uint" if "uint" in (ta, tb) else "int"


def trunc_div(x, y):
    q = abs(x) // abs(y)
    return q if (x < 0) == (y < 0) else -q


def binop(op, a, ta, b, tb):
    """(value, type) of `a op b` for a of type ta, b of type tb."""
    if op in ("&&", "||"):
        r = (a != 0 and b != 0) if op == "&&" else (a != 0 or b != 0)
        return int(r), "int"
    if op in ("<<", ">>"):
        rt = promote(ta)
        x = conv(a, rt)
        n = b & 0xFFFF
        if n > 15:
            n = 16
        if op == "<<":
            return conv(x << n, rt), rt
        return conv(x >> n, rt), rt
    ct = usual(ta, tb)
    x, y = conv(a, ct), conv(b, ct)
    if op in ("<", ">", "<=", ">=", "==", "!="):
        return int(eval("x %s y" % op)), "int"
    if op == "+":
        r = x + y
    elif op == "-":
        r = x - y
    elif op == "*":
        r = x * y
    elif op == "/":
        r = 0 if y == 0 else trunc_div(x, y)
    elif op == "%":
        r = 0 if y == 0 else x - y * trunc_div(x, y)
    elif op == "&":
        r = (x & 0xFFFF) & (y & 0xFFFF)
    elif op == "|":
        r = (x & 0xFFFF) | (y & 0xFFFF)
    elif op == "^":
        r = (x & 0xFFFF) ^ (y & 0xFFFF)
    else:
        raise ValueError(op)
    return conv(r, ct), ct


def unop(op, a, ta):
    if op == "!":
        return int(a == 0), "int"
    rt = promote(ta)
    x = conv(a, rt)
    r = {"-": -x, "~": ~x, "+": x}[op]
    return conv(r, rt), rt


def lit(v, t):
    """A C constant of type t with value v."""
    if v < 0:
        s = "(%s)(-%d)" % (CTYPE[t], -v) if v != -32768 else "(%s)(-32767 - 1)" % CTYPE[t]
    else:
        s = "%d" % v
        s = s if t == "int" and v <= 32767 else "(%s)%s" % (CTYPE[t], s)
    return s


def mem_lines(words):
    data = b"".join((w & 0xFFFF).to_bytes(2, "little") for w in words)
    out = []
    for i in range(0, len(data), 24):
        out.append("// mem: r+%d %s" % (i, data[i:i + 24].hex()))
    return out


def pairs_for(op, ta, tb, rnd, n=6):
    va, vb = VALUES[ta], VALUES[tb]
    cand = [(a, b) for a in va for b in vb]
    rnd.shuffle(cand)
    picked = []
    # always some boundaries: zero/minus-one divisors, extremes
    for want in ((va[0], vb[-1]), (va[-1], vb[0]), (va[len(va) // 2], vb[len(vb) // 2])):
        if want not in picked:
            picked.append(want)
    if op in ("/", "%"):
        for want in ((va[-1], 0), (va[0], -1 if tb in ("int", "schar") else vb[-1])):
            if want not in picked:
                picked.append(want)
    if op in ("<<", ">>"):
        cand = [(a, b) for a in va for b in (0, 1, 3, 7, 8, 15, 16) if conv(b, tb) == b]
        rnd.shuffle(cand)
    for c in cand:
        if len(picked) >= n:
            break
        if c not in picked:
            picked.append(c)
    return picked[:n]


def gen_binary(op, ta, tb, rnd):
    pairs = pairs_for(op, ta, tb, rnd)
    cta, ctb = CTYPE[ta], CTYPE[tb]
    words = []
    body = []
    for a, b in pairs:
        v, _ = binop(op, a, ta, b, tb)
        k = len(words)
        A, B = lit(a, ta), lit(b, tb)
        body.append("    r[%d] = f(%s, %s);" % (k, A, B))
        body.append("    ga = %s; gb = %s; r[%d] = ga %s gb;" % (A, B, k + 1, op))
        body.append("    la = %s; lb = %s; r[%d] = la %s lb;" % (A, B, k + 2, op))
        body.append("    r[%d] = ia(%s) %s ib(%s);" % (k + 3, A, op, B))
        body.append("    r[%d] = la %s %s;" % (k + 4, op, B))
        body.append("    r[%d] = %s %s lb;" % (k + 5, A, op))
        words += [v] * 6
    name = "%s %s %s" % (cta, op, ctb)
    head = ["// Generated by tools/gen_exprtests.py: `%s` in six code shapes (parameters, globals," % name,
            "// locals, two calls, constant right, constant left); results checked byte for byte."]
    src = head + mem_lines(words) + [
        "int r[%d];" % len(words),
        "%s ga;" % cta, "%s gb;" % ctb,
        "int f(%s a, %s b) { return a %s b; }" % (cta, ctb, op),
        "%s ia(%s v) { return v; }" % (cta, cta),
        "%s ib(%s v) { return v; }" % (ctb, ctb),
        "int main(void)", "{", "    %s la;" % cta, "    %s lb;" % ctb] + body + ["    return 0;", "}"]
    return src


def gen_unary(op, t, rnd):
    ct = CTYPE[t]
    words = []
    body = []
    for a in VALUES[t]:
        v, _ = unop(op, a, t)
        k = len(words)
        A = lit(a, t)
        body.append("    r[%d] = f(%s);" % (k, A))
        body.append("    g = %s; r[%d] = %sg;" % (A, k + 1, op))
        body.append("    l = %s; p = &l; r[%d] = %s*p;" % (A, k + 2, op))
        body.append("    r[%d] = %sid(%s);" % (k + 3, op, A))
        words += [v] * 4
    head = ["// Generated by tools/gen_exprtests.py: unary `%s` on %s (parameter, global, through a" % (op, ct),
            "// pointer, a call result); results checked byte for byte."]
    return head + mem_lines(words) + [
        "int r[%d];" % len(words), "%s g;" % ct,
        "int f(%s a) { return %sa; }" % (ct, op),
        "%s id(%s v) { return v; }" % (ct, ct),
        "int main(void)", "{", "    %s l;" % ct, "    %s *p;" % ct] + body + ["    return 0;", "}"]


def gen_compound(op, ta, tb, rnd):
    bop = op[:-1]
    pairs = pairs_for(bop, ta, tb, rnd, n=5)
    cta, ctb = CTYPE[ta], CTYPE[tb]
    words = []
    body = []
    for a, b in pairs:
        v, _ = binop(bop, a, ta, b, tb)
        nv = conv(v, ta)
        k = len(words)
        A, B = lit(a, ta), lit(b, tb)
        body.append("    l = %s; r[%d] = (l %s %s); r[%d] = l;" % (A, k, op, B, k + 1))
        body.append("    g = %s; y = %s; r[%d] = (g %s y); r[%d] = g;" % (A, B, k + 2, op, k + 3))
        body.append("    t[1] = %s; p = &t[1]; *p %s id(%s); r[%d] = t[1];" % (A, op, B, k + 4))
        body.append("    r[%d] = f(%s, %s);" % (k + 5, A, B))
        words += [nv, nv, nv, nv, nv, nv]
    head = ["// Generated by tools/gen_exprtests.py: `%s %s %s` (a local, a global, through a pointer," % (cta, op, ctb),
            "// a parameter); the value of the expression and the object afterwards, byte for byte."]
    return head + mem_lines(words) + [
        "int r[%d];" % len(words), "%s g;" % cta, "%s y;" % ctb, "%s t[3];" % cta,
        "%s id(%s v) { return v; }" % (ctb, ctb),
        "int f(%s a, %s b) { a %s b; return a; }" % (cta, ctb, op),
        "int main(void)", "{", "    %s l;" % cta, "    %s *p;" % cta] + body + ["    return 0;", "}"]


def gen_incdec(t, rnd):
    ct = CTYPE[t]
    words = []
    body = []
    for a in VALUES[t][:5] + VALUES[t][-2:]:
        k = len(words)
        A = lit(a, t)
        up, dn = conv(a + 1, t), conv(a - 1, t)
        body.append("    l = %s; r[%d] = l++; r[%d] = l;" % (A, k, k + 1))
        body.append("    l = %s; r[%d] = ++l; r[%d] = l;" % (A, k + 2, k + 3))
        body.append("    g = %s; r[%d] = g--; r[%d] = g;" % (A, k + 4, k + 5))
        body.append("    g = %s; r[%d] = --g; r[%d] = g;" % (A, k + 6, k + 7))
        body.append("    t[2] = %s; p = t; r[%d] = (*(p + 2))++; r[%d] = t[2];" % (A, k + 8, k + 9))
        body.append("    t[2] = %s; r[%d] = --p[2]; r[%d] = t[2];" % (A, k + 10, k + 11))
        body.append("    r[%d] = f(%s);" % (k + 12, A))
        words += [a, up, up, up, a, dn, dn, dn, a, up, dn, dn, conv(a + 2, t)]
    head = ["// Generated by tools/gen_exprtests.py: ++ and -- on %s, prefix and postfix (a local, a" % ct,
            "// global, through pointers, a parameter); values and objects byte for byte."]
    return head + mem_lines(words) + [
        "int r[%d];" % len(words), "%s g;" % ct, "%s t[4];" % ct,
        "int f(%s a) { a++; ++a; return a; }" % ct,
        "int main(void)", "{", "    %s l;" % ct, "    %s *p;" % ct] + body + ["    return 0;", "}"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "tests", "expr", "gen"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in glob.glob(os.path.join(a.out, "*.c")):
        os.remove(f)
    rnd = random.Random(2068)
    cases = {}
    tn = {"char": "c", "schar": "sc", "int": "i", "uint": "u"}
    opn = {"+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod", "&": "and", "|": "or", "^": "xor",
           "<<": "shl", ">>": "shr", "<": "lt", ">": "gt", "<=": "le", ">=": "ge", "==": "eq", "!=": "ne",
           "&&": "andand", "||": "oror"}
    plan = []
    for op in ("+", "-", "*", "/", "%"):
        plan += [(op, p) for p in (("int", "int"), ("uint", "uint"), ("int", "uint"), ("char", "char"), ("schar", "int"))]
    for op in ("&", "|", "^"):
        plan += [(op, p) for p in (("int", "int"), ("uint", "char"), ("schar", "schar"))]
    for op in ("<<", ">>"):
        plan += [(op, p) for p in (("int", "int"), ("uint", "int"), ("char", "int"), ("schar", "uint"))]
    for op in ("<", ">", "<=", ">=", "==", "!="):
        plan += [(op, p) for p in (("int", "int"), ("uint", "uint"), ("int", "uint"), ("char", "schar"))]
    for op in ("&&", "||"):
        plan += [(op, p) for p in (("int", "int"), ("char", "uint"))]
    for op, (ta, tb) in plan:
        cases["bin_%s_%s%s.c" % (opn[op], tn[ta], tn[tb])] = gen_binary(op, ta, tb, rnd)
    for op, nm in (("-", "neg"), ("~", "cpl"), ("!", "not"), ("+", "plus")):
        for t in ("char", "schar", "int", "uint"):
            cases["un_%s_%s.c" % (nm, tn[t])] = gen_unary(op, t, rnd)
    for op in ("+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="):
        for ta, tb in (("char", "int"), ("int", "int"), ("uint", "uint")):
            cases["cas_%s_%s%s.c" % (opn[op[:-1]], tn[ta], tn[tb])] = gen_compound(op, ta, tb, rnd)
    for t in ("char", "schar", "int", "uint"):
        cases["incdec_%s.c" % tn[t]] = gen_incdec(t, rnd)
    for name, src in sorted(cases.items()):
        for l in src:
            assert len(l) <= 127, (name, l)
        with open(os.path.join(a.out, name), "w") as f:
            f.write("\n".join(src) + "\n")
    print("%d cases in %s" % (len(cases), os.path.relpath(a.out, ROOT)))


if __name__ == "__main__":
    main()
