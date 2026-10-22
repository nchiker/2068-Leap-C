#!/usr/bin/env python3
"""2068-Leap-C spike: measure which RAM the platform services a C ROM would keep actually touch.

Boots the frozen V2 release ROM (spike/v2ref) in ZEsarUX, fills every candidate free region with a
canary byte, then runs a driver at $F400 (package window) that exercises the retained services:
text output and scrolling, pixels, lines, clipped plot, sprite capture/draw, 16-bit math, MEM_FILL,
key polling, 50 interrupt frames, AY BEEP and number formatting (EXROM, paged), and a tape SAVE
(EXROM). Reports every changed byte outside the display and the kernel's system variables, the
system-variable bytes that changed, and the machine-stack high-water.

Usage: python3 ram_probe.py [--port 10650]"""
import argparse, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True     # never write a bytecode cache into the frozen V2 tree
sys.path.insert(0, os.path.join(os.environ.get("LEAPC_V2_REPO", os.path.expanduser("~/2068-Leap")), "tools/qual"))
from qharness import Machine        # noqa: E402

V2REF = os.path.join(HERE, "v2ref")
DRIVER = 0xF400
CANARY = 0xA5
REGIONS = [(0x5B00, 0x8000), (0x825A, 0xC000), (0xE000, 0xF180), (0xF328, 0xF3AF), (0xF800, 0xFF00)]
CHUNK6 = (0xC000, 0xE000)            # filled and read back by the driver while EXROM is paged out
SYSVARS = (0x8000, 0x825A)

SRC = r"""
    DEVICE ZXSPECTRUM48
{equ}
    ORG ${drv:04X}
PROBE:
        im 1
        ei
        call BANK_PAGE_EXROM_OUT        ; chunk 6 = RAM
        ld hl,$C000
        ld de,$C001
        ld bc,$1FFF
        ld (hl),${can:02X}
        ldir                            ; canary in chunk-6 RAM
        call GFX_CLS
        ld b,0                          ; 22 rows x 32 columns of characters
.row:   ld c,0
.col:   push bc
        ld a,c
        add a,"A"-1
        and $3F
        add a,32
        call GFX_PUTCHAR
        pop bc
        inc c
        ld a,c
        cp 32
        jr nz,.col
        inc b
        ld a,b
        cp 22
        jr nz,.row
        ld hl,TEXT
        ld bc,$0503
        call GFX_PRINT_STRING
        call GFX_SCROLL_TEXT_UP
        call GFX_SCROLL_TEXT_UP
        ld b,0                          ; 192 pixels on a diagonal
.pix:   push bc
        ld c,b
        ld a,$38
        ld d,0
        call GFX_WRITE_PIXEL
        pop bc
        inc b
        ld a,b
        cp 192
        jr nz,.pix
        ld hl,10
        ld (GFX_LINE_X0),hl
        ld hl,180
        ld (GFX_LINE_Y0),hl
        ld hl,250
        ld (GFX_LINE_X1),hl
        ld hl,5
        ld (GFX_LINE_Y1),hl
        ld a,$38
        ld (GFX_LINE_ATTR),a
        xor a
        ld (GFX_LINE_OVER),a
        call GFX_LINE
        ld hl,-5                        ; clipped plot off screen, then on
        ld de,20
        ld a,$38
        ld b,0
        call GFX_PLOT_CLIPPED
        ld hl,100
        ld de,100
        ld a,$38
        ld b,1
        call GFX_PLOT_CLIPPED
        ld bc,$0A0A                     ; sprite 2x2 cells, buffer in the package window
        ld de,$0202
        ld hl,SPRBUF
        call GFX_SPRITE_CAPTURE
        ld bc,$0C0C
        ld de,$0202
        ld hl,SPRBUF
        call GFX_SPRITE_DRAW
        ld hl,1234
        ld de,-56
        call MATH_MULTIPLY16
        ld hl,-30000
        ld de,77
        call MATH_DIVIDE16
        ld hl,30000
        ld de,7
        call MATH_MOD16
        ld hl,30000
        call MATH_SQRT16
        ld hl,1000
        call MATH_RND16
        ld hl,FILLBUF
        ld bc,16
        call MEM_FILL
        call IO_READ_KEY_NONBLOCK
        ld b,50                         ; 50 frames of interrupts (keyboard scan, FRAMES)
.wait:  halt
        djnz .wait
        ld hl,-321                      ; number formatting through the EXROM-paging ABI slot
        xor a
        call PKG_NUM_TO_TEXT_SAFE
        call BANK_PAGE_EXROM_IN         ; EXROM services called directly, with chunk 6 = EXROM
        ld hl,0
        ld de,6
        call AY_BEEP
        ld hl,TAPENAME
        ld b,4
        ld ix,TEXT
        ld de,16
        call STORAGE_SAVE
        call BANK_PAGE_EXROM_OUT
OUT_CHECK:                              ; chunk 6 is RAM here: the harness reads it back
        call BANK_PAGE_EXROM_IN
DONE:   jr DONE
TEXT:   db "LEAP-C RAM PROBE",0
TAPENAME: db "PROB"
FILLBUF: ds 16
SPRBUF: ds 40
END:
    SAVEBIN "{out}", ${drv:04X}, END-${drv:04X}
"""
NAMES = ["BANK_PAGE_EXROM_IN", "BANK_PAGE_EXROM_OUT", "GFX_CLS", "GFX_PUTCHAR", "GFX_PRINT_STRING",
         "GFX_SCROLL_TEXT_UP", "GFX_WRITE_PIXEL", "GFX_LINE", "GFX_LINE_X0", "GFX_LINE_Y0", "GFX_LINE_X1",
         "GFX_LINE_Y1", "GFX_LINE_ATTR", "GFX_LINE_OVER", "GFX_PLOT_CLIPPED", "GFX_SPRITE_CAPTURE",
         "GFX_SPRITE_DRAW", "MATH_MULTIPLY16", "MATH_DIVIDE16", "MATH_MOD16", "MATH_SQRT16", "MATH_RND16",
         "MEM_FILL", "IO_READ_KEY_NONBLOCK", "PKG_NUM_TO_TEXT_SAFE", "AY_BEEP", "STORAGE_SAVE"]


def runs(addrs):
    out = []
    for a in sorted(addrs):
        if out and a == out[-1][1] + 1:
            out[-1][1] = a
        else:
            out.append([a, a])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=10650)
    a = ap.parse_args()
    m = Machine(V2REF, a.port, label="ramprobe").start()
    try:
        S = m.S
        d = tempfile.mkdtemp(prefix="leapc-ramprobe-")
        equ = "\n".join("%s EQU $%04X" % (n, S[n]) for n in NAMES)
        open(d + "/p.asm", "w").write(SRC.format(equ=equ, drv=DRIVER, can=CANARY, out=d + "/p.bin"))
        r = subprocess.run(["sjasmplus", "--nologo", "--sym=" + d + "/p.sym", d + "/p.asm"], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        sym = {l.split(":")[0]: int(l.split()[2], 16) for l in open(d + "/p.sym") if " EQU " in l}
        blob = open(d + "/p.bin", "rb").read()
        m.restore()
        sv0 = m.read(SYSVARS[0], SYSVARS[1] - SYSVARS[0])
        for lo, hi in REGIONS:
            m.write(lo, bytes([CANARY]) * (hi - lo))
        m.write(DRIVER, blob)
        m.setreg("SP", 0xFF00)
        m.setreg("PC", DRIVER)
        m.set_bps([sym["OUT_CHECK"]])
        m.run(120_000_000)
        assert m.pc() == sym["OUT_CHECK"], "probe did not reach OUT_CHECK (pc %04X)" % m.pc()
        changed = []
        c6 = m.read(CHUNK6[0], CHUNK6[1] - CHUNK6[0])
        changed += [CHUNK6[0] + i for i, b in enumerate(c6) if b != CANARY]
        m.set_bps([sym["DONE"]])
        m.run(1_000_000)
        assert m.pc() == sym["DONE"]
        stack_low = None
        for lo, hi in REGIONS:
            mem = m.read(lo, hi - lo)
            ch = [lo + i for i, b in enumerate(mem) if b != CANARY]
            if lo == 0xF800:
                stack_low = min(ch) if ch else None
            else:
                changed += ch
        sv1 = m.read(SYSVARS[0], SYSVARS[1] - SYSVARS[0])
        svch = [SYSVARS[0] + i for i in range(len(sv0)) if sv0[i] != sv1[i]]
        names = {}
        for n, v in S.items():
            names.setdefault(v, n)
        res = {
            "changed_outside_display_and_sysvars": [["%04X" % x, "%04X" % y, names.get(x, "")] for x, y in runs(changed)],
            "sysvar_bytes_changed": [["%04X" % x, "%04X" % y, names.get(x, "")] for x, y in runs(svch)],
            "stack_high_water_bytes": None if stack_low is None else 0xFF00 - stack_low,
            "driver": "%04X-%04X" % (DRIVER, DRIVER + len(blob) - 1),
        }
        json.dump(res, open(os.path.join(HERE, "results", "ram_probe.json"), "w"), indent=1)
        print(json.dumps(res, indent=1))
    finally:
        m.stop()


if __name__ == "__main__":
    main()
