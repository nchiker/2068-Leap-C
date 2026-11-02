#!/usr/bin/env python3
"""The display routines' speed against ceilings (1.2.0: faster text, scrolling and keyboard interrupt).

Each routine is timed directly on the ROM in ZEsarUX, the way the 1.2.0 measurements were made: a stub in
RAM does DI, loads the registers, CALLs the routine and stops on the instruction after the CALL; the cost of
the DI, the loads and the CALL is taken off. The run is repeated 12 times, each after a spin of a random
number of T-states (interrupts off), and the MAX of the 12 is compared with the ceiling. (Interrupts are off
so the frame interrupt never lands inside a routine; the phase moves the emulator's frame position.)

The keyboard interrupt is timed by running the whole handler from $0038 to its RETI: idle (no key), and with
a key held steady (12 frames spread over the held-steady stretch, after the accept and before the repeat).

A case whose symbol is missing, or that does not run to its end, is reported as FAIL, not a crash.

Usage: displaytest.py [--build DIR] [--port N] [--no-ceilings]
Exit status 0 when every case is under its ceiling, 1 otherwise.
"""
import argparse
import os
import random
import struct
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lcharness import Machine, STOP_ADDR, RET_SLOT  # noqa: E402

ROOT = os.path.dirname(HERE)
STUB, SPIN, REPS = 0xFF10, 0xFE70, 12


class Fail(Exception):
    pass


def le(v):
    return struct.pack("<H", v & 0xFFFF)


def timed(m, target, a=None, b=None, c=None, hl=None, pre=None, reps=REPS):
    """T-states of CALL target after DI and loading the registers; the stub's own cost removed."""
    try:
        addr = m.sym(target)
    except KeyError:
        raise Fail("no symbol %s" % target)
    code, ov = b"\xF3", 4
    if a is not None:
        code += bytes([0x3E, a]); ov += 7
    if b is not None:
        code += bytes([0x06, b]); ov += 7
    if c is not None:
        code += bytes([0x0E, c]); ov += 7
    if hl is not None:
        code += b"\x21" + le(hl); ov += 10
    code += b"\xCD" + le(addr); ov += 17
    stopx = STUB + len(code)                  # the instruction right after the CALL
    m.write(stopx, b"\x18\xFE")
    out = []
    for _ in range(reps):
        m.write(SPIN, b"\xF3\x18\xFE"); m.setreg("PC", SPIN); m.setreg("SP", 0xFF00)
        m.run(random.randrange(1, 6000))      # DI; JR $: moves the frame phase
        if pre:
            pre()
        m.write(STUB, code)
        m.write(0xFF00, le(stopx)); m.setreg("SP", 0xFF00); m.setreg("PC", STUB)
        m.tstates_reset()
        pc = m.run_to([stopx], 1_000_000)
        if pc != stopx:
            raise Fail("%s did not return (PC=$%04X)" % (target, pc))
        out.append(m.tstates() - ov)
    return out


def libstate(m, row=5, col=5, attr=0x38):
    for n, v in (("LIB_ATTR", attr), ("LIB_INVF", 0), ("LIB_OVERF", 0), ("LIB_ROW", row), ("LIB_COL", col)):
        try:
            m.write(m.sym(n), v)
        except KeyError:
            raise Fail("no symbol %s" % n)


def isr_once(m):
    """The whole handler, $0038 to RETI, without the 13 T of the IM 1 acknowledge."""
    m.write(STOP_ADDR, b"\x18\xFE")
    m.write(RET_SLOT, le(STOP_ADDR))
    m.setreg("SP", RET_SLOT); m.setreg("PC", 0x38)
    m.tstates_reset()
    pc = m.run_to([STOP_ADDR], 100_000)
    if pc != STOP_ADDR:
        raise Fail("the interrupt handler did not return (PC=$%04X)" % pc)
    return m.tstates()


def isr_idle(m):
    m.restore()
    return [isr_once(m) for _ in range(REPS)]


def isr_held(m):
    m.restore()
    m.cmd("send-keys-event %d 1" % ord("a"))
    try:
        seq = [isr_once(m) for _ in range(36)]    # frame 0 sees the key, 1 accepts it, 35 repeats it
    finally:
        m.cmd("send-keys-event %d 0" % ord("a"))
    return seq[2:35:3]                            # 12 frames of the held-steady stretch


def build_cases(m):
    """(name, ceiling in T, function -> the T of each run); the 1.1.0 and 1.2.0 maxima are in the comments"""
    return [
        # interrupt, whole handler: 1.1.0 max 2028 (idle), 1656 (held steady); 1.2.0 225, 856
        ("interrupt idle", 300, lambda: isr_idle(m)),
        ("interrupt key held steady", 1100, lambda: isr_held(m)),
        # 1.1.0 max 849 ('A'), 2136 ('$'), 911 (over); 1.2.0 453, 453, 514
        ("GFX_PUTCHAR 'A' (5,5)", 570, lambda: timed(m, "GFX_PUTCHAR", a=ord("A"), b=5, c=5)),
        ("GFX_PUTCHAR '$' (5,5)", 570, lambda: timed(m, "GFX_PUTCHAR", a=ord("$"), b=5, c=5)),
        ("GFX_PUTCHAR_OVER 'A' (5,5)", 650, lambda: timed(m, "GFX_PUTCHAR_OVER", a=ord("A"), b=5, c=5)),
        # 1.1.0 max 1523; 1.2.0 892
        ("LIB_PUTC 'A' (5,5)", 1120, lambda: timed(m, "LIB_PUTC", a=ord("A"), pre=lambda: libstate(m))),
        # 1.1.0 max 237,433; 1.2.0 135,492
        ("GFX_SCROLL_OUTPUT_UP", 170_000, lambda: timed(m, "GFX_SCROLL_OUTPUT_UP")),
        # 1.1.0 max 33,352 (B = 23 only; it took no attribute); 1.2.0 7,659
        ("GFX_CLEAR_ROW A=$38 B=23", 9600, lambda: timed(m, "GFX_CLEAR_ROW", a=0x38, b=23)),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--port", type=int, default=12800)
    ap.add_argument("--no-ceilings", action="store_true")
    a = ap.parse_args()
    m = Machine(a.build, a.port)
    failed = 0
    try:
        m.start()
        m.restore()
        try:
            r = m.call("BANK_PAGE_EXROM_OUT", maxi=100000)
            if not r["ok"]:
                raise Fail("BANK_PAGE_EXROM_OUT did not return")
            m.write(STOP_ADDR, b"\x18\xFE")
            setup = None
        except (KeyError, Fail) as e:
            setup = str(e) or "no symbol BANK_PAGE_EXROM_OUT"
        print("%-30s %8s %9s %8s %9s  %s" % ("case", "min", "mean", "max", "ceiling", ""))
        for name, ceiling, fn in build_cases(m):
            try:
                if setup:
                    raise Fail(setup)
                out = fn()
            except (Fail, KeyError, AssertionError, RuntimeError, OSError, ValueError) as e:
                print("%-30s FAIL (%s)" % (name, e))
                failed += 1
                continue
            mx = max(out)
            ok = a.no_ceilings or mx <= ceiling
            failed += not ok
            print("%-30s %8d %9.0f %8d %9s  %s" % (name, min(out), sum(out) / len(out), mx,
                                                 "-" if a.no_ceilings else ceiling, "ok" if ok else "OVER"))
    finally:
        m.stop()
    print("displaytest: PASS" if not failed else "displaytest: %d FAILED" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
