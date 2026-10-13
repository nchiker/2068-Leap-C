"""Compile-workspace capacity measurements for M1.2 (project_plan.md: "workspace bytes per global
scalar, per struct member, per local"), taken from the production ROM.

Each measurement compiles a generated program twice, with N and 2N declarations, and divides the
difference in workspace use by N, so the fixed overhead cancels out. Names are 4 characters long
(the expected cost is 9 + name length bytes per symbol entry; include/leapc_decl.inc).

measure(m) -> list of dict(what, n, bytes_each, detail)"""
import decltest


def _names(prefix, n):
    return ["%s%03d" % (prefix, i) for i in range(n)]          # 4 characters


def _lines(stem, items, per_line=12):
    out = []
    for i in range(0, len(items), per_line):
        out.append(stem % ",".join(items[i:i + per_line]))
    return out


def _global_bytes(m, src):
    r = decltest.run_compile(m, src, capture_scopes=False)
    assert r.ok and not r.errnum, ("compile failed", r.errnum, r.errline)
    return 0xC000 - r.ws_glo, r


def _local_bytes(m, src):
    r = decltest.run_compile(m, src, capture_scopes=True)
    assert r.ok and not r.errnum, ("compile failed", r.errnum, r.errline)
    # the function body's scope is the last one closed; its entries span SCOPE_BASE..WS_LOC
    s = r.snaps[-1]
    used = sum(9 + len(e.name) for e in s["entries"])
    return used, r


def measure(m, n=24):
    rows = []

    def per(what, f, detail):
        a, _ = f(n)
        b, r2 = f(2 * n)
        rows.append(dict(what=what, n=n, bytes_each=(b - a) / n, detail=detail,
                         tstates_2n=r2.tstates, lines_2n=None))

    # global scalars: one symbol entry each, the type is a handle (no node)
    per("global int scalar", lambda k: _global_bytes(m, _lines("int %s;", _names("g", k))),
        "file-scope entry (9 + name) in the global area; static data is in the image")
    # global arrays: an entry and an array type node each
    per("global int array", lambda k: _global_bytes(m, _lines("int %s;", [x + "[2]" for x in _names("a", k)], 10)),
        "entry + TN_ARRAY node (7)")
    # struct members: a member entry each (the struct's node and tag are fixed overhead)
    per("struct member", lambda k: _global_bytes(m, ["struct s {"] + _lines("int %s;", _names("m", k)) + ["};"]),
        "member entry (9 + name) in the global area")
    # pointers to a struct: one TN_PTR node for the type, shared by all such pointers
    per("pointer to struct", lambda k: _global_bytes(m, ["struct s { int a; };"] +
                                                    _lines("struct s *%s;", _names("p", k), 10)),
        "entry only: the struct's pointer type node is made once")
    # locals: an entry each in the local area, reclaimed when the block closes
    per("local int", lambda k: _local_bytes(m, ["void f(void) {"] + _lines("int %s;", _names("l", k)) + ["}"]),
        "block-scope entry (9 + name) in the local area, reclaimed at the block end")
    # function prototypes with 2 parameters
    per("prototype f(int,char*)", lambda k: _global_bytes(m, ["int %s(int a, char *b);" % x for x in _names("f", k)]),
        "entry + TN_FUNC node (7 + 2 per parameter); parameter entries are reclaimed")
    # enum constants
    per("enum constant", lambda k: _global_bytes(m, ["enum {"] + _lines("%s,", _names("e", k)) + ["};"]),
        "file-scope entry (9 + name)")
    return rows
