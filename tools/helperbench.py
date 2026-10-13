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
]


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
    out = []
    S = m.S
    for name, setup, site, check in CASES:
        d = tempfile.mkdtemp(prefix="lchb-")
        syms = "\n".join("%s EQU $%04X" % (k, S[k]) for k in
                         ("RT_CALLHL", "RT_MUL", "RT_DIVS", "RT_MODS", "RT_DIVU", "RT_MODU", "RT_SHL",
                          "RT_SHR", "RT_SAR", "RT_CPL", "MATH_NEGATE16"))
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
