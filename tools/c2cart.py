#!/usr/bin/env python3
"""Compile a Leap-C program on the release ROM (ZEsarUX) and pack it for the runtime cartridge (make cart PROG=x.c).

  c2cart.py PROGRAM.c [--lib NAME] [--port N] -o OUT.dck [--bin OUT.bin] [--image OUT.img]

--lib NAME   the library build/libs/NAME.bin is loaded first (as LIB "NAME"); it is carried in region 3
--port N     ZEsarUX's ZRCP port (default 11770; it must be free)
-o OUT.dck   the cartridge for ZEsarUX / Fuse / TSRun (one DOCK bank)
--bin        the same as a flat 64 KB file (a physical cartridge)
--image      the program image alone (tools/cartpack.py's format)

The compile is the shell's (CC_PROGRAM on build/leapc_home.bin + build/leapc_exrom.bin, run=False); the program is then
read from RAM: per image region its code [base, low) and static data [high, end), a loaded library's region 3 whole,
and region 4 up to its last non-zero byte when #pragma hires reserved it. Packing is tools/cartpack.py."""
import argparse
import os
import socket
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2src      # noqa: E402
import cart_build  # noqa: E402
import cartpack   # noqa: E402

ROOT = os.path.dirname(HERE)
CART = os.path.join(ROOT, "build", "cart")
# the compiler's regions in IMG_LIM order (spec): 1 $C000-$E000, 2 $E000-$F180, 3 $F400-$F800, 4 $6000-$7800
REGIONS = [(0xC000, 0xE000), (0xE000, 0xF180), (0xF400, 0xF800), (0x6000, 0x7800)]
LX_BASE = 0xF400


def region_blocks(read, lim, lib_loaded):
    """[(address, bytes)] for the IMG_LIM bytes `lim` (16: [low][high] per region); read(addr, n) reads the machine."""
    blocks = []
    for i, (base, end) in enumerate(REGIONS):
        low, high = lim[4 * i] | lim[4 * i + 1] << 8, lim[4 * i + 2] | lim[4 * i + 3] << 8
        if not (base <= low <= high <= end):
            raise SystemExit("c2cart: IMG_LIM region %d [$%04X, $%04X) is not inside $%04X-$%04X" % (i + 1, low, high, base, end))
        if i == 2 and lib_loaded == 0xF4:
            blocks.append((base, read(base, end - base)))
        elif i == 3 and low == high == end:             # #pragma hires: the program uses $6000-$77FF as the display file
            data = read(base, end - base)
            last = max((k for k, b in enumerate(data) if b), default=-1)
            if last >= 0:
                blocks.append((base, data[:last + 1]))
        else:
            if low > base:
                blocks.append((base, read(base, low - base)))
            if end > high:
                blocks.append((high, read(high, end - high)))
    return blocks


def compile_image(m, lines, library=None):
    """Compile `lines` (library `library` loaded first) on a started release Machine, as the shell does (run=False), and
    read the program back: (RUN_MAIN, RUN_VOID, IMG_LIM bytes, LIB_LOADED, [(address, bytes)]); or a string, why not
    (the compile did not return, a compile error)."""
    import exectest
    from decltest import ER_NAME
    r = exectest.compile_and_run(m, lines, run=False, library=library)
    if not r.compile_ok:
        return "the compile did not return"
    if r.errnum:
        return "compile error %d (%s) at line %d" % (r.errnum, ER_NAME.get(r.errnum, "?"), r.errline)
    S = m.sym
    run_main, run_void = m.w16(S("RUN_MAIN")), m.read(S("RUN_VOID"), 1)[0]
    lim = m.read(S("IMG_LIM"), 16)
    lib_loaded = m.read(S("LIB_LOADED"), 1)[0]
    c6 = exectest.read_chunk6(m)                        # $C000-$DFFF as RAM, whatever the paging

    def read(addr, n):
        if 0xC000 <= addr and addr + n <= 0xE000:
            return c6[addr - 0xC000:addr - 0xC000 + n]
        return m.read(addr, n)
    return run_main, run_void, lim, lib_loaded, region_blocks(read, lim, lib_loaded)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program")
    ap.add_argument("--lib")
    ap.add_argument("--port", type=int, default=11770)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--bin")
    ap.add_argument("--image")
    a = ap.parse_args()

    from lcharness import Machine

    home_p = os.path.join(CART, "leapc_cart_home.bin")
    exrom_p = os.path.join(ROOT, "build", "leapc_exrom.bin")
    for p in (home_p, exrom_p):
        if not os.path.exists(p):
            sys.exit("c2cart: %s is missing (make cart)" % os.path.relpath(p, ROOT))
    try:
        lines = c2src.lines_of(open(a.program, encoding="latin-1").read())
    except c2src.SourceError as e:
        sys.exit("c2cart: %s: %s" % (a.program, e))
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", a.port)) == 0:
            sys.exit("c2cart: port %d is in use (an emulator left running?); pick another with --port" % a.port)

    m = Machine(os.path.join(ROOT, "build"), a.port)
    try:
        m.start()
        r = compile_image(m, lines, a.lib)
        if isinstance(r, str):
            sys.exit("c2cart: %s: %s" % (a.program, r))
        run_main, run_void, lim, lib_loaded, blocks = r
    finally:
        m.stop()

    if not blocks:
        sys.exit("c2cart: %s compiled to nothing" % a.program)
    ident = cart_build.identity()
    try:
        img = cartpack.image(run_main, run_void, lim, lib_loaded, blocks, ident)
        cartpack.verify(img, ident)
        home, exrom = open(home_p, "rb").read(), open(exrom_p, "rb").read()
        dck, flat = cartpack.dck(home, exrom, img), cartpack.flat_bin(home, exrom, img)
    except cartpack.CartPackError as e:
        sys.exit("c2cart: %s" % e)
    open(a.out, "wb").write(dck)
    if a.bin:
        open(a.bin, "wb").write(flat)
    if a.image:
        open(a.image, "wb").write(img)
    print("c2cart: %s: image %d bytes (identity $%04X, main $%04X, library %s), %d blocks:" % (
        a.program, len(img), ident, run_main, a.lib if lib_loaded == 0xF4 and a.lib else "none", len(blocks)))
    for addr, data in blocks:
        print("  $%04X-$%04X  %5d bytes" % (addr, addr + len(data) - 1, len(data)))
    print("c2cart: wrote %s%s%s" % (a.out, ", " + a.bin if a.bin else "", ", " + a.image if a.image else ""))


if __name__ == "__main__":
    main()
