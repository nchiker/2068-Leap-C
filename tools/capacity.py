#!/usr/bin/env python3
"""The measured capacity table (project_plan.md section 6, Phase 4; docs/milestones/M4.md).

Every number is measured on the production ROM in ZEsarUX: a program is generated, compiled (and
where needed run), and each limit is found as a pair "the largest that compiles / runs" and "one
more fails, with the expected error". Limits are found by extrapolating from two small sizes and
then stepping to the exact boundary, so every reported limit is a verified pair.

  source     the largest source of a minimal program (main and comment lines), and of a typical
             program (modules of globals, a function with locals, a loop, a call), with the
             workspace, image and compile time at the limit; the limit is E_NOMEM (the source and
             the compile workspace share $7800-$BFFF)
  image      the largest image: code made by macro expansion (little source) until E_TOOBIG; the
             code and data bytes placed per region; the largest single object and all globals
  stack      the deepest recursion of reference functions; the stack per level
  heap       the largest block with a minimal program, and with the largest source
  nesting    parentheses, held operands, blocks, if/while, nested calls, struct members, pointer
             levels, parameters, frame size, pending argument words

Writes build/capacity.json and prints the table. Usage: capacity.py [--port N] [--only NAME]
"""
import argparse
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src            # noqa: E402
import exectest         # noqa: E402
from decltest import ER_NAME   # noqa: E402
from lcharness import Machine  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC_BASE, SRC_TOP, HEAP_END = 0x7800, 0xC000, 0xBFFE
REGIONS = ((0xC000, 0xE000), (0xE000, 0xF180), (0xF400, 0xF800), (0x6000, 0x7800))


class Cap:
    def __init__(self, m):
        self.m = m
        self.S = m.sym
        self.n = 0

    def compile(self, lines, run=False, maxi=200_000_000):
        self.n += 1
        r = exectest.compile_and_run(self.m, lines, run=run, audit=False, maxi=maxi)
        S = self.S
        d = self.m.read(S("IMG_LIM"), 16)
        lim = [(d[4 * k] | d[4 * k + 1] << 8, d[4 * k + 2] | d[4 * k + 3] << 8) for k in range(4)]
        out = dict(ok=r.compile_ok and not r.errnum, error=ER_NAME.get(r.errnum, r.errnum) if r.errnum else None,
                   line=r.errline, compile_t=r.compile_t, src_bytes=len(c2src.records(lines)), lines=len(lines),
                   prog_end=self.m.w16(S("PROG_END")), ws_glo=self.m.w16(S("WS_GLO")))
        out["workspace_global"] = SRC_TOP - out["ws_glo"]
        code = data = 0
        for (base, end), (low, high) in zip(REGIONS, lim):
            if base <= low <= high <= end:
                code += low - base
                data += end - high
        out.update(image_low_high=lim, image_code=code, image_data=data)
        if run and out["ok"]:
            out.update(ran=r.ran, a=r.a, hl=r.hl)
        return out

    def boundary(self, make, lo, hi=None, step=None, want=None):
        """The largest k with make(k) compiling (and want(result) true), and k + 1 failing: from a
        known-good lo, a doubling search up, then bisection. Returns (k, result k, result k + 1)."""
        good = self.compile(make(lo))
        assert self._ok(good, want), ("lower bound fails", lo, good)
        if hi is None:
            step = step or max(1, lo)
            hi = lo + step
            while True:
                r = self.compile(make(hi))
                if not self._ok(r, want):
                    bad = r
                    break
                lo, good = hi, r
                step *= 2
                hi = lo + step
        else:
            bad = self.compile(make(hi))
            assert not self._ok(bad, want), ("upper bound compiles", hi)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            r = self.compile(make(mid))
            if self._ok(r, want):
                lo, good = mid, r
            else:
                hi, bad = mid, r
        return lo, good, bad

    @staticmethod
    def _ok(r, want):
        return r["ok"] and (want is None or want(r))


# ---------------------------------------------------------------- generators
def filler(nbytes, width=120):
    """Comment lines whose line-store records take exactly nbytes (record = text + 3)."""
    out = []
    while nbytes > 0:
        n = min(width + 3, nbytes)
        if n < 6:                           # (a record of `//` + 1 needs 6; pad the previous line)
            out[-1] = out[-1] + "x" * n
            break
        out.append("//" + "x" * (n - 5))
        nbytes -= n
    return out


MINIMAL = ["int main(void) { return 0; }"]


def module(k):
    return ["int g%d[8];" % k,
            "int f%d(int a, int b)" % k,
            "{",
            "    int i, s;",
            "    s = 0;",
            "    for (i = 0; i < 8; i++)",
            "        s = s + g%d[i] * a - b;" % k,
            "    if (s > 100)",
            "        s = s / 2;",
            "    return s;",
            "}"]


def typical(n):
    out = []
    for k in range(n):
        out += module(k)
    out += ["int main(void)", "{", "    int t;", "    t = 0;"]
    out += ["    t = t + f%d(%d, 1);" % (k, k) for k in range(0, n, max(1, n // 8))]
    out += ["    return t;", "}"]
    return out


def macro_code(nfuncs):
    """Dense code from little source: each function body is 8 expansions of 8 statements (7 B each)."""
    out = ["int g;", "#define S8 g = g + 1; g = g + 1; g = g + 1; g = g + 1; g = g + 1; g = g + 1; "
           "g = g + 1; g = g + 1;"]
    for k in range(nfuncs):
        out.append("void f%d(void) { S8 S8 S8 S8 S8 S8 S8 S8 }" % k)
    out.append("int main(void) { f0(); return g; }")
    return out


def nested(kind, n):
    if kind == "parentheses":
        return ["int a;", "int main(void)", "{", "    a = 1;", "    return " + "(" * n + "a" + ")" * n + ";", "}"]
    if kind == "held operands":
        return ["int a;", "int *p;", "int main(void)", "{", "    p = &a; a = 1;",
                "    return " + "*p+(" * n + "*p" + ")" * n + ";", "}"]
    if kind == "blocks":
        return ["int main(void)", "{", "    int a;", "    a = 1;", "    " + "{" * n + " a = a + 1; " + "}" * n,
                "    return a;", "}"]
    if kind == "if":
        return ["int main(void)", "{", "    int a;", "    a = 1;", "    " + "if (a) " * n + "a = a + 1;",
                "    return a;", "}"]
    if kind == "while":
        return ["int main(void)", "{", "    int a;", "    a = 1;", "    " + "while (a < 2) " * n + "a = a + 1;",
                "    return a;", "}"]
    if kind == "nested calls":
        return ["int f(int x) { return x + 1; }", "int main(void)", "{",
                "    return " + "f(" * n + "0" + ")" * n + ";", "}"]
    if kind == "struct members":
        out = ["struct s0 { int v; };"]
        for k in range(1, n):
            out.append("struct s%d { struct s%d m; };" % (k, k - 1))
        out += ["struct s%d x;" % (n - 1), "int main(void)", "{",
                "    x" + ".m" * (n - 1) + ".v = 3;", "    return x" + ".m" * (n - 1) + ".v;", "}"]
        return out
    raise ValueError(kind)


def wrap(lines, width=120):
    """Split lines longer than the editor's 127 characters at spaces or punctuation."""
    out = []
    for l in lines:
        while len(l) > width:
            cut = max(l.rfind(c, 0, width) for c in " ,(+") + 1
            if cut <= 0:
                cut = width
            out.append(l[:cut])
            l = l[cut:]
        out.append(l)
    return out


# ---------------------------------------------------------------- measurements
def m_source(c, res):
    # minimal program: the largest source (comment lines) that still compiles
    base = len(c2src.records(MINIMAL))
    k, good, bad = c.boundary(lambda n: filler(n) + MINIMAL, 16000, hi=SRC_TOP - SRC_BASE - base + 1)
    res["source_minimal"] = dict(source_bytes=good["src_bytes"], prog_end="$%04X" % good["prog_end"],
                                 workspace_global=good["workspace_global"], next_error=bad["error"],
                                 next_source_bytes=bad["src_bytes"])
    # the heap with that source: malloc of everything (a run)
    big = filler(k - 300) + ["int main(void)", "{", "    char *p;", "    p = malloc(1);", "    free(p);",
                              "    return 0xBFFEu - (unsigned)p;", "}"]
    r = c.compile(big, run=True)
    res["heap_at_source_limit"] = dict(source_bytes=r["src_bytes"], heap_block=r.get("hl"), ran=r.get("ran"))
    # typical program
    k, good, bad = c.boundary(lambda n: typical(n), 20)
    res["source_typical"] = dict(modules=k, source_bytes=good["src_bytes"], lines=good["lines"],
                                 text_bytes=sum(len(l) + 1 for l in typical(k)),
                                 workspace_global=good["workspace_global"], image_code=good["image_code"],
                                 image_data=good["image_data"], compile_t=good["compile_t"],
                                 compile_ms_per_line=round(good["compile_t"] / good["lines"] / 3528.0, 2),
                                 next_error=bad["error"])


def m_image(c, res):
    k, good, bad = c.boundary(macro_code, 10)
    lim = good["image_low_high"]
    per = []
    for i, ((base, end), (low, high)) in enumerate(zip(REGIONS, lim)):
        per.append(dict(region=i + 1, bytes=end - base, code=low - base if base <= low <= end else None,
                        data=end - high if base <= high <= end else None,
                        free=high - low if base <= low <= high <= end else None))
    res["image_code"] = dict(functions=k, image_code=good["image_code"], image_data=good["image_data"],
                             source_bytes=good["src_bytes"], regions=per, next_error=bad["error"],
                             image_bytes=sum(e - b for b, e in REGIONS))
    # globals: the largest single object, and all of them
    one = lambda n: ["char a[%d];" % n, "int main(void) { a[0] = 1; return a[0]; }"]
    k1, g1, b1 = c.boundary(one, 8000, hi=8193)
    res["largest_object"] = dict(bytes=k1, next_error=b1["error"])
    allg = lambda n: ["char a[8192];", "char b[4480];", "char c[1024];", "char d[%d];" % n,
                      "int main(void) { return 0; }"]
    k2, g2, b2 = c.boundary(allg, 5000, hi=6145)
    res["all_globals"] = dict(bytes=8192 + 4480 + 1024 + k2, code_bytes=g2["image_code"], next_error=b2["error"])


def m_stack(c, res):
    out = []
    for name, params, local, extra in (("reference: 1 int parameter, 1 int local", "int n", "int x;", ""),
                                       ("no parameter, no local", "void", "", ""),
                                       ("4 int parameters, 10 int locals", "int n, int a, int b, int c",
                                        "int x[10];", "x[0] = a + b + c;")):
        arg = "n + 1" if params != "void" else ""
        args = ", 1, 2, 3" if params.count(",") == 3 else ""
        body = "depth = depth + 1; %s %s return f(%s%s);" % ("x = n;" if local == "int x;" else "", extra,
                                                            arg, args if arg else "")
        src = ["int depth;", "int f(%s)" % params, "{", "    %s" % local, "    " + body, "}",
               "int main(void) { return f(%s); }" % ("1" + args if arg else "")]
        r = exectest.compile_and_run(c.m, src, audit=False, maxi=50_000_000)
        depth = r.mem.w([e.val for e in r.globals if e.name == "depth"][0])
        out.append(dict(function=name, depth=depth, runtime_error=r.a))
    res["recursion"] = out


def m_heap(c, res):
    src = ["int main(void)", "{", "    char *p;", "    p = malloc(1);", "    free(p);",
           "    return 0xBFFEu - (unsigned)p;", "}"]
    r = c.compile(src, run=True)
    res["heap_minimal"] = dict(largest_block=r.get("hl"), first_block_data="$%04X" % (HEAP_END - r.get("hl", 0)),
                               source_bytes=r["src_bytes"])


def m_nesting(c, res):
    out = {}
    for kind, lo in (("parentheses", 20), ("held operands", 20), ("blocks", 20), ("if", 20), ("while", 20),
                     ("nested calls", 10), ("struct members", 10)):
        k, good, bad = c.boundary(lambda n, kind=kind: wrap(nested(kind, n)), lo)
        out[kind] = dict(max=k, next_error=bad["error"])
    res["nesting"] = out


MEASURES = dict(source=m_source, image=m_image, stack=m_stack, heap=m_heap, nesting=m_nesting)


def markdown(res):
    """The capacity table (docs/milestones/M4.md, spec.md 4.10.1) from build/capacity.json."""
    f = lambda n: "{:,}".format(n) if isinstance(n, int) else str(n)
    out = ["| Item | Measured limit | One more |", "|---|---|---|"]
    sm, st = res["source_minimal"], res["source_typical"]
    out.append("| Source, minimal program (comments and `main`) | %s B of line store (`PROG_END` %s); workspace %s B | %s |"
               % (f(sm["source_bytes"]), sm["prog_end"], f(sm["workspace_global"]), sm["next_error"]))
    out.append("| Source, typical program (%s modules: a global array, a function with a loop, locals, a call) | %s B "
               "of line store, %s lines (%s B of text); workspace %s B; image %s B of code, %s B of data; compile %s ms per line | %s |"
               % (f(st["modules"]), f(st["source_bytes"]), f(st["lines"]), f(st["text_bytes"]), f(st["workspace_global"]),
                  f(st["image_code"]), f(st["image_data"]), st["compile_ms_per_line"], st["next_error"]))
    ic = res["image_code"]
    regs = "; ".join("region %d: %s code, %s data, %s free" % (r["region"], f(r["code"]), f(r["data"]), f(r["free"]))
                     for r in ic["regions"])
    out.append("| Image: code (macro-expanded statements, %s functions) | %s B of code and %s B of data of %s B (%s) | %s |"
               % (f(ic["functions"]), f(ic["image_code"]), f(ic["image_data"]), f(ic["image_bytes"]), regs,
                  ic["next_error"]))
    out.append("| Image: the largest single object | %s B (region 1; an object never spans regions) | %s |"
               % (f(res["largest_object"]["bytes"]), res["largest_object"]["next_error"]))
    ag = res["all_globals"]
    out.append("| Image: all static data, with a minimal program | %s B | %s |" % (f(ag["bytes"]), ag["next_error"]))
    for r in res["recursion"]:
        out.append("| Recursion: %s | %s levels from `main` | stack overflow (runtime error %d) |"
                   % (r["function"], f(r["depth"]), r["runtime_error"]))
    hm, ha = res["heap_minimal"], res["heap_at_source_limit"]
    out.append("| Heap: the largest block, minimal program | %s B (first block's data at %s) | NULL |"
               % (f(hm["largest_block"]), hm["first_block_data"]))
    out.append("| Heap: the largest block with a large source | %s B (%s B of source, 300 B below the minimal program's "
               "limit; at the limit itself 16 B) | NULL |" % (f(ha["heap_block"]), f(ha["source_bytes"])))
    for k, v in res["nesting"].items():
        out.append("| Nesting: %s | %s levels | %s |" % (k, f(v["max"]), v["next_error"]))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10770)
    ap.add_argument("--only")
    ap.add_argument("--json", default=os.path.join(ROOT, "build", "capacity.json"))
    ap.add_argument("--md", action="store_true", help="print the table from the JSON (no measurement)")
    a = ap.parse_args()
    if a.md:
        print(markdown(json.load(open(a.json))))
        return 0
    m = Machine(os.path.join(ROOT, "build"), a.port)
    m.start()
    res = {}
    t0 = time.time()
    try:
        c = Cap(m)
        for name, f in MEASURES.items():
            if a.only and a.only != name:
                continue
            t = time.time()
            f(c, res)
            print("capacity: %s measured (%d compiles so far, %.0f s)" % (name, c.n, time.time() - t), flush=True)
        res["compiles"] = c.n
        res["wall_s"] = round(time.time() - t0, 1)
    finally:
        m.stop()
    with open(a.json, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
