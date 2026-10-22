"""Power-on RAM qualification (Phase 9, project_plan.md section 11: "randomised power-on RAM").

A real TS2068 powers on with whatever its DRAM holds, and its reset button keeps the RAM; every other
suite boots ZEsarUX from zeroed RAM. Here the machine boots from a pattern written over $4000-$FFFF,
and over the registers a Z80 reset leaves undefined, after reset-cpu (which keeps ZEsarUX's RAM and
those registers: measured in Phase 9). The patterns:

  zero      all $00: the reference, every other suite's boot
  ones      all $FF
  alt       $55, $AA alternating
  addr      each byte its address's low byte (a stale pointer reads as plausible data)
  random:N  bytes and registers from Python's random.Random(N): reproducible from N
  warm      the reset button after a session: a program compiled and run (its image in regions 1-3,
            its heap), then reset with the RAM and registers as the session left them

What a pattern must not change (check_boot): the boot reaches the idle prompt in the same T-states
with the same SP; every byte the ROM defines there is the zero boot's: $4000-$BFFF (the screen, the
system variables and cells, display file 2, the source region), the UDG table, the edit buffer and the
live stack (SP to $FEFF). Not defined by design (programs and the compiler write them before reading):
image regions 1-3, the stack below SP, $FF00-$FFFF, the V2 platform cells Leap-C does not use, and
GFX_LINE_X0..Y1 (draw() sets all four first). Then the programs: run_tests.py's `poweron` suite runs
a slice of the executable corpus from each pattern's boot, and `run_tests.py --ram PATTERN` runs any
suite from it (Machine.power_on).

Standalone: python3 tools/poweron.py [--port N] [PATTERN ...]  (boot checks only)
"""
import argparse
import os
import random
import struct
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lcharness import Machine  # noqa: E402

ROOT = os.path.dirname(HERE)
RAM_BASE, RAM_SIZE = 0x4000, 0xC000
PATTERNS = ("ones", "alt", "addr", "random:1", "random:2", "random:3", "random:4", "warm")
# the registers a Z80 reset leaves as they were (I, R, PC, IFF and IM are reset; AF and SP read $FFFF
# on real chips, set here anyway: the ROM must not depend on them either)
FREE_REGS = ("AF", "BC", "DE", "HL", "IX", "IY", "SP", "AF'", "BC'", "DE'", "HL'")
WARM_PROGRAM = ["char big[6000];", "int table[700];", "int main(void)", "{", "    char *p = malloc(4000);",
                "    int i;", "    for (i = 0; i < 6000; i++) big[i] = i * 7;", "    for (i = 0; i < 700; i++) table[i] = -i;",
                "    for (i = 0; i < 4000; i++) p[i] = 255 - i;", '    printf("WARM %d", big[100]);', "    return 0;",
                "}"]


def ram_bytes(name):
    """The 48 K written over $4000-$FFFF, and the free registers' values (None: as reset left them)."""
    if name == "zero":
        return bytes(RAM_SIZE), None
    if name == "ones":
        return bytes([0xFF]) * RAM_SIZE, None
    if name == "alt":
        return bytes([0x55, 0xAA]) * (RAM_SIZE // 2), None
    if name == "addr":
        return bytes(a & 0xFF for a in range(RAM_BASE, RAM_BASE + RAM_SIZE)), None
    if name.startswith("random:"):
        rng = random.Random(int(name.split(":", 1)[1]))
        return rng.randbytes(RAM_SIZE), {r: rng.randrange(0x10000) for r in FREE_REGS}
    raise ValueError("unknown RAM pattern %r" % name)


def power_on(name):
    """Machine.power_on for a pattern: called after reset-cpu, before the boot runs."""
    def fill(m):
        if name == "warm":
            _session(m)
            m.cmd("reset-cpu")
            return
        data, regs = ram_bytes(name)
        m.write(RAM_BASE, data)
        for r, v in (regs or {}).items():
            m.setreg(r, v)
    return fill


def _session(m):
    """The warm pattern's session: boot from zeroed RAM, compile and run WARM_PROGRAM (exectest's direct
    path) and leave everything as it ends."""
    import exectest
    m.write(RAM_BASE, bytes(RAM_SIZE))
    m.tstates_reset()
    assert m.run_to([m.sym("IO_READ_KEY")], 20_000_000) == m.sym("IO_READ_KEY"), "warm: the first boot"
    res = exectest.compile_and_run(m, WARM_PROGRAM, restore=False)
    assert res.compile_ok and not res.errnum and res.ran and not res.a, "warm: the session's program failed"


def defined_areas(m, sp):
    """The RAM the ROM defines at the idle prompt: [(name, address, bytes)]."""
    S = m.sym
    return [("screen, system variables, cells, display file 2, source region", RAM_BASE, 0xC000 - RAM_BASE),
            ("UDG table", S("UDG_TABLE"), S("EDIT_LINE_BUF") - S("UDG_TABLE")),
            ("edit buffer", S("EDIT_LINE_BUF"), 128),
            ("live stack", sp, 0xFF00 - sp)]


def boot_state(m, name):
    """Reset, write pattern `name`, boot to the idle prompt. Returns dict(reached, tstates, regs, areas)
    with the defined areas' bytes; the machine is left at the idle prompt."""
    m.cmd("reset-cpu")
    power_on(name)(m)
    m.tstates_reset()
    pc = m.run_to([m.sym("IO_READ_KEY")], 20_000_000)
    regs = m.regs()
    out = dict(reached=pc == m.sym("IO_READ_KEY"), tstates=m.tstates(), regs=regs, areas={})
    if out["reached"]:
        for what, a, n in defined_areas(m, regs["SP"]):
            out["areas"][what] = (a, m.read(a, n))
    return out


def ranges(a, b, base):
    """The address ranges where a and b differ, as text."""
    out, start = [], None
    for i in range(len(a) + 1):
        diff = i < len(a) and a[i] != b[i]
        if diff and start is None:
            start = i
        elif not diff and start is not None:
            out.append("$%04X-$%04X" % (base + start, base + i - 1) if i - 1 > start else "$%04X" % (base + start))
            start = None
    return out


def check_boot(m, name, ref=None):
    """The boot from pattern `name` against the zero boot `ref` (boot_state(m, "zero") if None).
    Returns (checks [(what, ok, detail)], state). The machine is left at the pattern's idle prompt."""
    ref = ref or boot_state(m, "zero")
    st = boot_state(m, name)
    checks = [("reaches the idle prompt", st["reached"], "PC=%04X" % st["regs"]["PC"])]
    if not st["reached"]:
        return checks, st
    checks.append(("boot T-states as from zeroed RAM", st["tstates"] == ref["tstates"],
                   "%d, zeroed RAM %d" % (st["tstates"], ref["tstates"])))
    checks.append(("SP as from zeroed RAM", st["regs"]["SP"] == ref["regs"]["SP"],
                   "%04X, zeroed RAM %04X" % (st["regs"]["SP"], ref["regs"]["SP"])))
    for what, (a, data) in st["areas"].items():
        ra, rdata = ref["areas"].get(what, (None, None))
        same = ra == a and rdata == data
        checks.append(("defined RAM: " + what, same, "" if same or ra != a else
                       "differs at " + ", ".join(ranges(rdata, data, a)[:12])))
    return checks, st


def save_boot(m, name, ref=None):
    """check_boot, then the pattern's idle prompt as the machine's boot snapshot (m.snap), so that
    every case restored after this starts from it. Returns (checks, state, previous snapshot path)."""
    checks, st = check_boot(m, name, ref)
    prev = m.snap
    if st["reached"]:
        m.snap = os.path.join(m.snapdir, "boot_%s.zsf" % name.replace(":", "_"))
        m.cmd("snapshot-save " + m.snap)
    return checks, st, prev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10850)
    ap.add_argument("patterns", nargs="*", default=list(PATTERNS))
    a = ap.parse_args()
    m = Machine(os.path.join(ROOT, "build"), a.port)
    failed = 0
    try:
        m.start()
        ref = boot_state(m, "zero")
        print("zero: boot %d T-states, SP=%04X" % (ref["tstates"], ref["regs"]["SP"]))
        for name in a.patterns:
            checks, _ = check_boot(m, name, ref)
            for what, ok, detail in checks:
                failed += not ok
                print("%-10s %-70s %s %s" % (name, what, "PASS" if ok else "FAIL", detail if not ok else ""))
    finally:
        m.stop()
    print("poweron: %d failures" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
