#!/usr/bin/env python3
"""Probe: banking state at the booted command loop, T-state counter exactness, contention by address,
whether ZRCP can write the ROM. Prints findings; nothing is saved."""
import os, sys, struct
sys.dont_write_bytecode = True     # never write a bytecode cache into the frozen V2 tree
sys.path.insert(0, os.path.expanduser("~/2068-Leap/tools/qual"))
from qharness import Machine, HARNESS_RET_SLOT
HERE = os.path.dirname(os.path.abspath(__file__))
m = Machine(os.path.join(HERE, "..", "v2ref"), 10610, label="v2ref").start()
try:
    S = m.S
    print("depth", m.read(S["BANK_EXROM_DEPTH"], 1)[0], "FF_shadow %02X" % m.read(S["PORT_FF_SHADOW"], 1)[0])
    print("byte at $C000 (EXROM?)", m.read(0xC000, 4).hex(), "exrom.bin starts", open(os.path.join(HERE, "../v2ref/build/exrom.bin"), "rb").read(4).hex())
    r = m.regs(); print("IFF/IM", m.cmd("get-registers"))
    # T-state exactness: 1000 NOPs + DI at a few addresses (DI so no interrupt in the count)
    for base in (0x6000, 0x7000, 0x8400, 0xE000, 0xF000):
        m.restore()
        code = b"\xF3" + b"\x00" * 1000 + b"\x18\xFE"   # di ; nop*1000 ; jr $
        m.write(base, code)
        end = base + 1001
        m.write(HARNESS_RET_SLOT, struct.pack("<H", end))
        m.setreg("SP", HARNESS_RET_SLOT); m.setreg("PC", base)
        m.set_bps([end])
        m.cmd("reset-tstates-partial")
        m.run(100000)
        t = int(m.cmd("get-tstates-partial").strip())
        print("base %04X: 1000 NOP + DI = %d T (pc %04X)" % (base, t, m.pc()))
    # ROM writability
    m.restore()
    before = m.read(0x0008, 1)
    m.write(0x0008, b"\x99")
    print("ROM $0008 before", before.hex(), "after write", m.read(0x0008, 1).hex())
finally:
    m.stop()
