#!/usr/bin/env python3
"""Build a Leap-C library's tapes from its assembly source (spec.md 7.2, 8.4; project_plan.md Phase 10).

A library is an image for image region 3 ($F400-$F7FF, 1 KB): a header (magic, ABI version, export count),
the export table (per function its name, address and signature byte, LIB_NAMES's records, then a 0), then
its code and data. Its source includes the ABI, include/leapc_lib.inc, which defines the header's macros,
the ROM services' jump-table slots (LX_*: fixed addresses in HOME) and the pinned cells, and starts with

        INCLUDE "leapc_lib.inc"
        ORG  LX_BASE
        LX_HEADER n
        LX_EXPORT "name", routine, LXR_*, LXP_*     ; n times
        LX_EXPORTS_END

The source is assembled with sjasmplus (warnings are errors) and the image checked: the magic and an ABI no
later than the include's, 1-99 exports, each name a C identifier of 1-31 characters, each address inside the
image, each signature a return type the compiler can bind and one of the ROM's 16 parameter lists, the table
ending where the count says, at most 1 KB in all. A name the ROM's library also has is reported: the ROM's
function is the one bound.

The tape is what LIB "name" reads: a header block (type LX_TYPE 4, V2's package tapes; the name padded to 10
characters; the length; the image's magic and ABI as the version word in the autostart field; the length
again) and a data block holding the image. Outputs by extension: .tap, .tzx (standard speed blocks), .wav
(8-bit mono 44.1 kHz audio, the stock ROM's pulses: tools/tapes.py), .bin (the image), .sym (its labels).

Usage: lib2tape.py [--name NAME] SRC.asm OUT [OUT ...]
The name defaults to the source's base name (1-10 characters).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tapes                                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INC = os.path.join(ROOT, "include", "leapc_lib.inc")


def abi_constants():
    """LX_* constants from the ABI include (the single source of truth)."""
    out = {}
    for line in open(INC):
        m = re.match(r"(LX_\w+)\s+EQU\s+(\$[0-9A-Fa-f]+|\d+)\b", line)
        if m:
            v = m.group(2)
            out[m.group(1)] = int(v[1:], 16) if v.startswith("$") else int(v)
    out["LX_WORD"] = out["LX_MAGIC"] << 8 | out["LX_ABI"]
    return out


LX = abi_constants()
ROM_NAMES = ("cls putchar puts print printf at tab ink paper border bright flash inverse over getkey inkey gets "
             "plot draw point attr mode sprite_get sprite_put beep sound frames pause rand srand inp outp strlen "
             "strcpy strncpy strcmp strcat strchr memcpy memmove memset memcmp atoi itoa abs malloc free exit "
             "tape_save tape_load").split()
C_KEYWORDS = set("auto break case char const continue default do double else enum extern float for goto if int "
                 "long register return short signed sizeof static struct switch typedef union unsigned void "
                 "volatile while".split())


class LibError(Exception):
    pass


def assemble(src):
    """(image bytes, {label: address}) of the library source."""
    src = os.path.abspath(src)
    with tempfile.TemporaryDirectory() as d:
        wrap = os.path.join(d, "wrap.asm")
        out = os.path.join(d, "lib.bin")
        sym = os.path.join(d, "lib.sym")
        open(wrap, "w").write('    DEVICE NOSLOT64K\n    INCLUDE "%s"\nLX_IMAGE_END:\n'
                              '    ASSERT LX_IMAGE_END <= LX_END, "the library is larger than image region 3"\n'
                              '    SAVEBIN "%s", LX_BASE, LX_IMAGE_END - LX_BASE\n' % (src, out))
        r = subprocess.run(["sjasmplus", "--nologo", "--msg=war", "--inc=" + os.path.dirname(INC),
                            "--inc=" + os.path.dirname(src), "--sym=" + sym, wrap],
                           capture_output=True, text=True)
        log = (r.stdout + r.stderr).strip()
        if r.returncode != 0 or re.search("warning", log, re.I):
            raise LibError("sjasmplus: %s" % log)
        image = open(out, "rb").read()
        syms = {}
        for line in open(sym):
            m = re.match(r"([A-Za-z_][\w.]*):\s+EQU\s+0x([0-9A-F]+)", line, re.I)
            if m:
                syms[m.group(1)] = int(m.group(2), 16)
    return image, syms


def exports(image):
    """Check the image's header and export table: [(name, address, signature)]."""
    base = LX["LX_BASE"]
    if len(image) < 4:
        raise LibError("the image is %d bytes: no header" % len(image))
    if len(image) > LX["LX_END"] - base:
        raise LibError("the image is %d bytes: more than image region 3's %d" % (len(image), LX["LX_END"] - base))
    if image[0] != LX["LX_MAGIC"]:
        raise LibError("magic $%02X, not $%02X (LX_HEADER)" % (image[0], LX["LX_MAGIC"]))
    if not 1 <= image[1] <= LX["LX_ABI"]:
        raise LibError("ABI %d: this ABI (include/leapc_lib.inc) is %d" % (image[1], LX["LX_ABI"]))
    count = image[2]
    if not 1 <= count <= LX["LX_EXPORTS_MAX"]:
        raise LibError("%d exports: 1 to %d" % (count, LX["LX_EXPORTS_MAX"]))
    out, p = [], 3
    for k in range(count):
        name = ""
        while True:
            if p >= len(image):
                raise LibError("export %d: the table runs past the image" % (k + 1))
            c = image[p]
            p += 1
            name += chr(c & 0x7F)
            if c & 0x80:
                break
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,30}", name) or name in C_KEYWORDS:
            raise LibError("export %d: %r is not a C identifier of 1-31 characters" % (k + 1, name))
        if p + 3 > len(image):
            raise LibError("export %r: the table runs past the image" % name)
        addr = image[p] | image[p + 1] << 8
        sig = image[p + 2]
        p += 3
        if not base + p <= addr < base + len(image):
            raise LibError("export %r: address $%04X is not in the library's code" % (name, addr))
        ret = sig >> 4
        if ret & 7 > 5 or (ret & 8 and ret & 7 not in (0, 1, 2, 3, 4, 5)):
            raise LibError("export %r: return type %d" % (name, ret))
        out.append((name, addr, sig))
    if p >= len(image) or image[p] != 0:
        raise LibError("the export table does not end with 0 after %d exports (LX_EXPORTS_END)" % count)
    return out


def blocks(image, name):
    if not 1 <= len(name) <= 10 or any(not 32 <= ord(c) <= 126 or c == '"' for c in name):
        raise LibError("the name must be 1-10 characters of ASCII 32-126, no quote (%r)" % name)
    version = image[0] << 8 | image[1]
    return [tapes.framed(0x00, tapes.header(LX["LX_TYPE"], name, len(image), version)), tapes.framed(0xFF, image)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--name")
    ap.add_argument("src")
    ap.add_argument("out", nargs="+")
    a = ap.parse_args()
    name = a.name if a.name is not None else os.path.splitext(os.path.basename(a.src))[0]
    try:
        image, syms = assemble(a.src)
        ex = exports(image)
        bl = blocks(image, name)
    except LibError as e:
        sys.exit("lib2tape: %s: %s" % (a.src, e))
    for out in a.out:
        ext = os.path.splitext(out)[1].lower()
        if ext == ".tap":
            data = tapes.tap(bl)
        elif ext == ".tzx":
            data = tapes.tzx(bl)
        elif ext == ".wav":
            data = tapes.Tape().file(bl).to_wav()
        elif ext == ".bin":
            data = image
        elif ext == ".sym":
            data = "".join("%s: EQU 0x%08X\n" % (k, v) for k, v in sorted(syms.items(), key=lambda t: t[1])).encode()
        else:
            sys.exit("lib2tape: %s: the output must be .tap, .tzx, .wav, .bin or .sym" % out)
        open(out, "wb").write(data)
    hidden = [n for n, _, _ in ex if n in ROM_NAMES]
    print("lib2tape: %s: library %r, %d bytes, ABI %d, %d functions (%s)%s" % (
        ", ".join(a.out), name, len(image), image[1], len(ex), ", ".join(n for n, _, _ in ex),
        "; hidden by the ROM's: " + ", ".join(hidden) if hidden else ""))


if __name__ == "__main__":
    main()
