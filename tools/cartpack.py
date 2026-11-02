#!/usr/bin/env python3
"""Pack a compiled Leap-C program into the runtime cartridge's image, .dck and flat .bin (make cart; no emulator code).

The image is src/cart/cart.asm's (little-endian words):
  "LCPG", format 1, identity (2), RUN_MAIN (2), RUN_VOID (1), IMG_LIM (16), LIB_LOADED (1)     = 27 bytes
  blocks [length:2][address:2][bytes] (1..8192 bytes, inside one image region), then a length of 0 (00 00)
  CRC-16/CCITT-FALSE of every byte before it, HIGH byte first (the CRC over the whole image is then 0)
It sits at DOCK $8000 (chunks 4-5, 16 KB); past that it continues at DOCK $4000 (chunk 2, 8 KB).

As a module: image(), verify(), place(), dck(), flat_bin().     cartpack.py --selftest   runs the model of cart.asm."""
import os
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cart_build import crc16  # noqa: E402

CHUNK = 0x2000
FORMAT = 1
SIGNATURE = b"LCPG"
HEADER_SIZE = 27
MAX_BLOCK = 0x2000
MAX_IMAGE = 2 * CHUNK + CHUNK
REGIONS = [(0x6000, 0x7800), (0xC000, 0xE000), (0xE000, 0xF180), (0xF400, 0xF800)]


class CartPackError(Exception):
    pass


def image(run_main, run_void, img_lim16, lib_loaded, blocks, identity):
    """The program image. blocks: [(address, bytes)]."""
    img_lim16 = bytes(img_lim16)
    if len(img_lim16) != 16:
        raise CartPackError("IMG_LIM is %d bytes, not 16" % len(img_lim16))
    for what, v, hi in (("RUN_MAIN", run_main, 0xFFFF), ("RUN_VOID", run_void, 0xFF), ("LIB_LOADED", lib_loaded, 0xFF),
                        ("identity", identity, 0xFFFF)):
        if not 0 <= v <= hi:
            raise CartPackError("%s $%X is out of range" % (what, v))
    out = bytearray(SIGNATURE + bytes([FORMAT]) + struct.pack("<HHB", identity, run_main, run_void)
                    + img_lim16 + bytes([lib_loaded]))
    assert len(out) == HEADER_SIZE
    for addr, data in blocks:
        data = bytes(data)
        if not data:
            raise CartPackError("empty block at $%04X" % addr)
        if len(data) > MAX_BLOCK:
            raise CartPackError("block at $%04X is %d bytes, over %d" % (addr, len(data), MAX_BLOCK))
        if not any(lo <= addr and addr + len(data) <= hi for lo, hi in REGIONS):
            raise CartPackError("block $%04X-$%04X is outside the image regions (or crosses one)"
                                % (addr, addr + len(data) - 1 if addr + len(data) else 0xFFFF))
        out += struct.pack("<HH", len(data), addr) + data
    out += b"\0\0"
    out += struct.pack(">H", crc16(out))
    if len(out) > MAX_IMAGE:
        raise CartPackError("the image is %d bytes; at most %d fit (DOCK chunks 4-5 and 2)" % (len(out), MAX_IMAGE))
    return bytes(out)


def verify(img, identity=None):
    """Re-check an image as CART_LOAD does (CRC residue 0, the blocks); returns (header dict, [(address, bytes)])."""
    img = bytes(img)
    if len(img) < HEADER_SIZE + 4 or img[:4] != SIGNATURE or img[4] != FORMAT:
        raise CartPackError("not a format-%d image" % FORMAT)
    if crc16(img) != 0:
        raise CartPackError("the image's CRC is wrong")
    ident, main, void = struct.unpack_from("<HHB", img, 5)
    if identity is not None and ident != identity:
        raise CartPackError("identity $%04X, expected $%04X" % (ident, identity))
    hdr = dict(identity=ident, run_main=main, run_void=void, img_lim=img[10:26], lib_loaded=img[26])
    blocks, p = [], HEADER_SIZE
    while True:
        n = img[p] | img[p + 1] << 8
        p += 2
        if n == 0:
            break
        if n > MAX_BLOCK:
            raise CartPackError("block over %d bytes" % MAX_BLOCK)
        addr = img[p] | img[p + 1] << 8
        blocks.append((addr, img[p + 2:p + 2 + n]))
        p += 2 + n
    if p + 2 != len(img):
        raise CartPackError("%d stray bytes after the block list" % (len(img) - p - 2))
    return hdr, blocks


def place(img):
    """{DOCK chunk: 8 KB}: the first 16 KB at chunks 4-5 ($8000), the rest at chunk 2 ($4000); $FF pads."""
    if len(img) > MAX_IMAGE:
        raise CartPackError("the image is %d bytes; at most %d fit" % (len(img), MAX_IMAGE))
    pad = lambda b: b + b"\xff" * (CHUNK - len(b))      # noqa: E731
    out = {4: pad(img[:CHUNK]), 5: pad(img[CHUNK:2 * CHUNK])}
    if len(img) > 2 * CHUNK:
        out[2] = pad(img[2 * CHUNK:])
    return out


def chunks(cart_home, exrom, img):
    if len(cart_home) != 2 * CHUNK or len(exrom) != CHUNK:
        raise CartPackError("the cartridge HOME must be 16384 bytes and the EXROM 8192")
    out = {0: cart_home[:CHUNK], 1: cart_home[CHUNK:], 6: bytes(exrom)}
    if img is not None:                         # (img None: a cartridge with no program, chunks 4-5 absent: tests)
        out.update(place(img))
    return out


def dck(cart_home, exrom, img):
    """A .dck as 2068-Forth's forthcart.py writes it: one DOCK bank (id 0), 8 descriptors (2 = ROM, 0 = absent), then
    the present chunks' 8 KB in chunk order."""
    c = chunks(cart_home, exrom, img)
    return bytes([0] + [2 if i in c else 0 for i in range(8)]) + b"".join(c[i] for i in sorted(c))


def flat_bin(cart_home, exrom, img):
    """64 KB: the eight chunks in address order, $FF where absent."""
    c = chunks(cart_home, exrom, img)
    return b"".join(c.get(i, b"\xff" * CHUNK) for i in range(8))


# ---------------------------------------------------------------- the model of cart.asm (tests)
def model_load(img, identity):
    """CART_LOAD's two passes on the placed image: returns (memory dict, cells) or None for 'bad' (carry set)."""
    ch = place(img)

    def at(i):                                  # CART_GETB: the stream goes on at $4000 when it reaches $C000
        a = 0x8000 + i
        if a >= 0xC000:
            a = 0x4000 + (a - 0xC000)
        c = ch.get(a >> 13)
        if c is None:
            raise IndexError("read from an absent chunk at $%04X" % a)
        return c[a & 0x1FFF]

    crc = 0xFFFF
    p = 0

    def nxt():
        nonlocal p, crc
        b = at(p)
        p += 1
        crc = crc16(bytes([b]), crc)
        return b

    sig = SIGNATURE + bytes([FORMAT]) + struct.pack("<H", identity)
    for s in sig:
        if nxt() != s:
            return None
    for _ in range(HEADER_SIZE - len(sig)):
        nxt()
    while True:                                 # pass 1
        n = nxt() | nxt() << 8
        if n == 0:
            break
        if n >> 8 >= 0x21:
            return None
        nxt()
        nxt()
        for _ in range(n):
            nxt()
    nxt()
    nxt()
    if crc != 0:
        return None
    mem, p = {}, HEADER_SIZE                    # pass 2
    while True:
        n = at(p) | at(p + 1) << 8
        a = at(p + 2) | at(p + 3) << 8
        p += 4 if n else 2
        if n == 0:
            break
        for k in range(n):
            mem[(a + k) & 0xFFFF] = at(p + k)
        p += n
    cells = dict(run_main=at(7) | at(8) << 8, run_void=at(9), img_lim=bytes(at(10 + k) for k in range(16)),
                 lib_loaded=at(26))
    return mem, cells


def selftest():
    ident = 0xE90E
    lim = bytes(range(16))
    rnd = bytes((i * 37 + 11) & 0xFF for i in range(9000))
    blocks = [(0xC000, rnd[:200]), (0xE000, rnd[200:300]), (0x6000, b"\x01"), (0xF400, rnd[:0x400]),
              (0xC000 + 0x1000, rnd[:0x1000])]
    img = image(0xC010, 1, lim, 0xF4, blocks, ident)
    hdr, got = verify(img, ident)
    assert got == blocks and hdr["run_main"] == 0xC010 and hdr["lib_loaded"] == 0xF4
    assert crc16(img) == 0 and img[-2:] == struct.pack(">H", crc16(img[:-2]))
    mem, cells = model_load(img, ident)
    want = {}
    for a, d in blocks:
        for k, b in enumerate(d):
            want[a + k] = b
    assert mem == want, "copied blocks differ"
    assert cells == dict(run_main=0xC010, run_void=1, img_lim=lim, lib_loaded=0xF4)
    assert model_load(img, ident ^ 1) is None, "a wrong identity was accepted"
    bad = bytearray(img)
    bad[40] ^= 1
    assert model_load(bytes(bad), ident) is None, "a damaged image was accepted"
    # an image over 16 KB continues in chunk 2 (the crossing block spans the 16384th byte)
    big = image(0xC000, 0, lim, 0, [(0xC000, rnd[:0x2000]), (0xE000, rnd[:0x1180]), (0xF400, rnd[:0x400]),
                                      (0x6000, rnd[:0x1800]), (0xC000, rnd[:0x1000])], ident)
    mem, _ = model_load(big, ident)
    assert len(big) > 16384 and 2 in place(big) and mem[0xC000] == rnd[0]
    assert mem[0xE000 + 0x117F] == rnd[0x117F]
    # none of these must be accepted
    for what, f in (("an empty block", lambda: image(0, 0, lim, 0, [(0xC000, b"")], ident)),
                    ("a block over 8 KB", lambda: image(0, 0, lim, 0, [(0xC000, bytes(8193))], ident)),
                    ("outside the regions", lambda: image(0, 0, lim, 0, [(0x8000, b"\0")], ident)),
                    ("crossing regions", lambda: image(0, 0, lim, 0, [(0xDFFF, b"\0\0")], ident)),
                    ("past the end", lambda: image(0, 0, lim, 0, [(0xF7FF, b"\0\0")], ident)),
                    ("over 24 KB", lambda: image(0, 0, lim, 0, [(0xC000, bytes(8192))] * 4, ident)),
                    ("IMG_LIM of 15", lambda: image(0, 0, lim[:15], 0, [], ident))):
        try:
            f()
        except CartPackError:
            continue
        raise AssertionError("accepted: " + what)
    # the containers
    home, exrom = bytes([1]) * 16384, bytes([6]) * 8192
    d = dck(home, exrom, img)
    assert d[:9] == bytes([0, 2, 2, 0, 0, 2, 2, 2, 0]) and len(d) == 9 + 5 * CHUNK
    assert d[9:9 + 0x4000] == home and d[-CHUNK:] == exrom
    b = flat_bin(home, exrom, img)
    assert len(b) == 65536 and b[:0x4000] == home and b[0xC000:0xE000] == exrom
    assert b[0xE000:] == b"\xff" * 0x2000 and b[0x6000:0x8000] == b"\xff" * 0x2000
    assert b[0x4000:0x6000] == b"\xff" * 0x2000 and b[0x8000:0x8000 + len(img)] == img
    dbig, bbig = dck(home, exrom, big), flat_bin(home, exrom, big)
    assert dbig[:9] == bytes([0, 2, 2, 2, 0, 2, 2, 2, 0]) and len(dbig) == 9 + 6 * CHUNK
    assert bbig[0x4000:0x4000 + len(big) - 0x4000] == big[0x4000:] and bbig[0x8000:0xC000] == big[:0x4000]
    print("cartpack: selftest ok (%d B image, %d B big image)" % (len(img), len(big)))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(__doc__)
