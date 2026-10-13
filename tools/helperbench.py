"""Helper core micro-measurements (project_plan.md M1.3; the spike's method, docs/C_FEASIBILITY_STUDY.md
4.4): each case is a short code snippet assembled into RAM ($E000) with the production ROM's
symbols; the harness times the instructions between labels t0 and t1 with ZEsarUX's T-state
counter, interrupts off, and checks the result registers or memory against the helper's contract.

measure(m) -> list of dict(name, site_bytes, tstates, ok, detail)
"""
import os
import subprocess
import tempfile

ORG = 0xE100
DATA = 0xE000

# name, setup (before t0), the site (t0..t1), the check (python: regs dict r, memory reader mem)
CASES = [
    ("LDI (rst $08): HL = (HL)", "ld hl,DATA\n ld (hl),$34\n inc hl\n ld (hl),$12\n dec hl",
     "rst $08", lambda r, mem: r["HL"] == 0x1234),
    ("STI (rst $10): (DE) = HL", "ld de,DATA\n ld hl,$BEEF",
     "rst $10", lambda r, mem: mem(DATA, 2) == b"\xef\xbe" and r["HL"] == 0xBEEF and r["DE"] == DATA + 1),
    ("CMPLT (rst $28), same signs, 3 < 5", "ld de,3\n ld hl,5", "rst $28", lambda r, mem: r["F"] & 1),
    ("CMPLT (rst $28), signs differ, -1 < 5", "ld de,-1\n ld hl,5", "rst $28", lambda r, mem: r["F"] & 1),
    ("CMPLT (rst $28), 5 < -1 false", "ld de,5\n ld hl,-1", "rst $28", lambda r, mem: not r["F"] & 1),
    ("unsigned compare (inline or a / sbc hl,de)", "ld de,3\n ld hl,5", "or a\n sbc hl,de", lambda r, mem: not r["F"] & 1),
    ("empty function with 2 B of locals: call + ENTER 2 + LEAVE", "jr skip\nfn: rst $18\n db 2\n rst $20\nskip: ld ix,$1234",
     "call fn", lambda r, mem: r["IX"] == 0x1234),
    ("ENTER 0 + LEAVE (call of an empty function)", "jr skip\nfn: rst $18\n db 0\n rst $20\nskip: ld ix,$1234",
     "call fn", lambda r, mem: r["IX"] == 0x1234),
    ("load local word, inline (ld l,(ix-2) / ld h,(ix-1))", "ld ix,DATA+2\n ld hl,$5678\n ld (DATA),hl\n ld hl,0",
     "ld l,(ix-2)\n ld h,(ix-1)", lambda r, mem: r["HL"] == 0x5678),
    ("store local word, inline", "ld ix,DATA+2\n ld hl,$9ABC",
     "ld (ix-2),l\n ld (ix-1),h", lambda r, mem: mem(DATA, 2) == b"\xbc\x9a"),
    ("RT_CALLHL (call through a pointer to `ret`)", "jr skip\nfn: ret\nskip: ld hl,fn",
     "call RT_CALLHL", lambda r, mem: True),
    ("RT_MUL 123 * 45", "ld de,123\n ld hl,45", "call RT_MUL", lambda r, mem: r["HL"] == 5535),
    ("RT_DIVS -1000 / 7", "ld de,-1000\n ld hl,7", "call RT_DIVS", lambda r, mem: r["HL"] == (-142) & 0xFFFF),
    ("RT_MODS -1000 % 7", "ld de,-1000\n ld hl,7", "call RT_MODS", lambda r, mem: r["HL"] == (-6) & 0xFFFF),
    ("RT_DIVU 60000 / 7", "ld de,60000\n ld hl,7", "call RT_DIVU", lambda r, mem: r["HL"] == 8571),
    ("RT_MODU 60000 % 7", "ld de,60000\n ld hl,7", "call RT_MODU", lambda r, mem: r["HL"] == 3),
    ("RT_SHL $0123 << 4", "ld de,$0123\n ld hl,4", "call RT_SHL", lambda r, mem: r["HL"] == 0x1230),
    ("RT_SHR $8120 >> 4", "ld de,$8120\n ld hl,4", "call RT_SHR", lambda r, mem: r["HL"] == 0x0812),
    ("RT_SAR $8120 >> 4", "ld de,$8120\n ld hl,4", "call RT_SAR", lambda r, mem: r["HL"] == 0xF812),
    ("RT_SHL by 16 (every bit out)", "ld de,$FFFF\n ld hl,16", "call RT_SHL", lambda r, mem: r["HL"] == 0),
    ("RT_CPL ~$00FF", "ld hl,$00FF", "call RT_CPL", lambda r, mem: r["HL"] == 0xFF00),
    ("MATH_NEGATE16 -(300)", "ld hl,300", "call MATH_NEGATE16", lambda r, mem: r["HL"] == (-300) & 0xFFFF),
    ("RT_MUL 1000 * 999 (wraps)", "ld de,1000\n ld hl,999", "call RT_MUL", lambda r, mem: r["HL"] == 999000 & 0xFFFF),
    ("RT_DIVU 65535 / 1", "ld de,65535\n ld hl,1", "call RT_DIVU", lambda r, mem: r["HL"] == 65535),
    ("RT_DIVU 65535 / 40000 (17-bit remainder steps)", "ld de,65535\n ld hl,40000", "call RT_DIVU",
     lambda r, mem: r["HL"] == 1 and r["DE"] == 25535),
    ("RT_DIVS -32768 / -1 (wraps)", "ld de,-32768\n ld hl,-1", "call RT_DIVS", lambda r, mem: r["HL"] == 0x8000),
    ("RT_DIVS 7 / 0 = 0", "ld de,7\n ld hl,0", "call RT_DIVS", lambda r, mem: r["HL"] == 0),
    ("RT_MODS -17 % 0 = 0", "ld de,-17\n ld hl,0", "call RT_MODS", lambda r, mem: r["HL"] == 0),
    ("LIB_RAND, state 0 (program start): srand(1)'s first value", "ld hl,0\n ld (RND_STATE),hl", "call LIB_RAND",
     lambda r, mem: r["HL"] == rand_seq(1, 1)[0] and mem(RND_STATE, 2) != b"\0\0"),
    ("LIB_SRAND 12345 (C convention: the argument on the stack)", "ld hl,12345\n push hl",
     "call LIB_SRAND", lambda r, mem: mem(RND_STATE, 2) == b"\x39\x30" and r["SP"] == 0xFF00 - 2),
]


# ---- table-driven checks: every pair through the helper, the results compared with a model of
# the integer semantics (spec.md 4.4; the same rules as tools/gen_exprtests.py)
def _s(v):
    return v - 65536 if v & 0x8000 else v


def _sdiv(a, b, mod):
    if b == 0:
        return 0
    q, r = abs(_s(a)) // abs(_s(b)), abs(_s(a)) % abs(_s(b))
    if mod:
        return (-r if _s(a) < 0 else r) & 0xFFFF
    return (-q if (_s(a) < 0) != (_s(b) < 0) else q) & 0xFFFF


MODELS = {
    "RT_MUL": lambda a, b: a * b & 0xFFFF,
    "RT_DIVU": lambda a, b: a // b if b else 0,
    "RT_MODU": lambda a, b: a % b if b else 0,
    "RT_DIVS": lambda a, b: _sdiv(a, b, 0),
    "RT_MODS": lambda a, b: _sdiv(a, b, 1),
}
EDGE = [0, 1, 2, 3, 7, 10, 127, 128, 255, 256, 1000, 32767, 32768, 32769, 40000, 65534, 65535]


def _pairs(n, seed):
    import random
    rnd = random.Random(seed)
    pairs = [(a, b) for a in EDGE for b in EDGE]
    pairs += [(rnd.randrange(65536), rnd.randrange(65536)) for _ in range(n // 2)]
    pairs += [(rnd.randrange(65536), rnd.randrange(1, 300)) for _ in range(n // 2)]
    return pairs


TABLE_CASES = [(h, _pairs(300, i)) for i, h in enumerate(MODELS)]
def table_case(helper, pairs):
    """The table [left][right][result] is assembled after the loop; IX ends just past it."""
    site = ("ld ix,tdata\n ld bc,%d\n" % len(pairs) +
            "tloop: push bc\n ld e,(ix+0)\n ld d,(ix+1)\n ld l,(ix+2)\n ld h,(ix+3)\n call %s\n"
            " ld (ix+4),l\n ld (ix+5),h\n ld de,6\n add ix,de\n pop bc\n dec bc\n ld a,b\n or c\n"
            " jr nz,tloop\n jp tdone\n" % helper +
            "tdata: DW %d, %d, $5555\n" % pairs[0] + "\n".join(" DW %d, %d, $5555" % p for p in pairs[1:]) +
            "\ntdone: nop")

    def check(r, mem):
        base = (r["IX"] - 6 * len(pairs)) & 0xFFFF
        got = mem(base, 6 * len(pairs))
        return all((got[6 * i + 4] | got[6 * i + 5] << 8) == MODELS[helper](a, b) for i, (a, b) in enumerate(pairs))
    return ("%s: %d pairs against the model (edge values, random)" % (helper, len(pairs)), "nop", site, check)


def rand_seq(seed, n):
    """The sequence LIB_RAND gives after srand(seed): xorshift (7, 9, 8) on 16 bits, top bit cleared."""
    x, out = seed or 1, []
    for _ in range(n):
        x ^= x << 7 & 0xFFFF
        x ^= x >> 9
        x ^= x << 8 & 0xFFFF
        out.append(x & 0x7FFF)
    return out


RND_STATE = None                     # set from the ROM's symbols by measure()
RAND_N = 64
RAND_OUT = 0xF000


def rand_case(seed):
    setup = (("ld hl,%d\n push hl\n call LIB_SRAND\n pop bc\n" % seed if seed is not None else
              "ld hl,0\n ld (RND_STATE),hl\n") +
             "ld ix,RAND_OUT\n ld b,%d\nrloop: push bc\n call LIB_RAND\n pop bc\n ld (ix+0),l\n ld (ix+1),h\n"
             " inc ix\n inc ix\n djnz rloop" % RAND_N)
    want = rand_seq(seed if seed is not None else 1, RAND_N)

    def check(r, mem):
        got = mem(RAND_OUT, 2 * RAND_N)
        return [got[2 * i] | got[2 * i + 1] << 8 for i in range(RAND_N)] == want
    return ("LIB_RAND: %d values after %s, against the model" % (
        RAND_N, "srand(%d)" % seed if seed is not None else "program start"), setup, "call LIB_RAND",
        lambda r, mem: check(r, mem) and r["HL"] == rand_seq(seed if seed is not None else 1, RAND_N + 1)[-1])


CASES += [table_case(*t) for t in TABLE_CASES]
CASES += [rand_case(None), rand_case(1), rand_case(0), rand_case(12345), rand_case(65535)]


def site_bytes(site):
    n = 0
    for ins in site.split("\n"):
        ins = ins.strip()
        if ins.startswith("rst"):
            n += 1
        elif ins.startswith("call"):
            n += 3
        elif ins.startswith("db"):
            n += 1
        elif "(ix" in ins:
            n += 3
        elif ins == "or a":
            n += 1
        elif ins.startswith("sbc"):
            n += 2
    return n


def measure(m):
    global RND_STATE
    out = []
    S = m.S
    RND_STATE = S["RND_STATE"]
    for name, setup, site, check in CASES:
        d = tempfile.mkdtemp(prefix="lchb-")
        syms = "\n".join("%s EQU $%04X" % (k, S[k]) for k in
                         ("RT_CALLHL", "RT_MUL", "RT_DIVS", "RT_MODS", "RT_DIVU", "RT_MODU", "RT_SHL",
                          "RT_SHR", "RT_SAR", "RT_CPL", "MATH_NEGATE16", "LIB_RAND", "LIB_SRAND", "RND_STATE"))
        syms += "\nRAND_OUT EQU $%04X" % RAND_OUT
        def lines(text):                 # a line with a label starts in column 1, others are indented
            return [x.strip() if ":" in x.split(";")[0] else "    " + x.strip() for x in text.split("\n")]
        src = ["    DEVICE ZXSPECTRUM48", syms, "DATA EQU $%04X" % DATA, "    ORG $%04X" % ORG,
               "start: di"] + lines(setup) + ["t0: " + site.split("\n")[0].strip()] + \
              lines("\n".join(site.split("\n")[1:])) * (site.count("\n") > 0) + \
              ["t1: jr t1", '    SAVEBIN "%s/b.bin", $%04X, $-$%04X' % (d, ORG, ORG)]
        open(d + "/b.asm", "w").write("\n".join(src) + "\n")
        r = subprocess.run(["sjasmplus", "--nologo", "--sym=" + d + "/b.sym", d + "/b.asm"],
                           capture_output=True, text=True)
        if r.returncode:
            out.append(dict(name=name, ok=False, detail=r.stdout + r.stderr))
            continue
        lab = {}
        for l in open(d + "/b.sym"):
            p = l.split()
            if len(p) >= 3 and p[1] == "EQU":
                lab[p[0].rstrip(":")] = int(p[2], 16)
        m.restore()
        m.call("BANK_PAGE_EXROM_OUT", maxi=100_000)
        m.write(ORG, open(d + "/b.bin", "rb").read())
        m.setreg("SP", 0xFF00)
        m.setreg("PC", ORG)
        if m.run_to([lab["t0"]], 100_000) != lab["t0"]:
            out.append(dict(name=name, ok=False, detail="t0 not reached"))
            continue
        m.tstates_reset()
        if m.run_to([lab["t1"]], 1_000_000) != lab["t1"]:
            out.append(dict(name=name, ok=False, detail="t1 not reached"))
            continue
        t = m.tstates()
        regs = m.regs()
        if "F" not in regs and "AF" in regs:
            regs["F"] = regs["AF"] & 0xFF
        ok = bool(check(regs, lambda a, n: m.read(a, n)))
        out.append(dict(name=name, ok=ok, tstates=t, site_bytes=site_bytes(site),
                        detail="" if ok else repr({k: "%04X" % v for k, v in regs.items()})))
    return out
