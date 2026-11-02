#!/usr/bin/env python3
"""Check the runtime cartridge's HOME (build/cart/leapc_cart_home.bin) against the release's (make cart, make check;
docs/milestones/M12-cart.md section 6).

  - every release label has the same value in the cartridge's .sym, except IO_KEY_SCAN_ROW (moved $0004 -> $000D;
    nothing compiled calls it) and the local labels of BANK_PAGE_EXROM_IN (the release ones keep their values);
  - the cartridge adds only CART_*, COMP_CART_*, BANK_CART_* and BANK_PAGE_EXROM_IN.home / .out;
  - the two 16 KB images differ only in the header ($0000-$0007), the moved IO_KEY_SCAN_ROW ($000D-$000F), the two
    paging routines, COLD_START's final jump, the operand of IO_KEY_SCAN_ROW's one call, and COMP_CART_BEGIN..END
    (release bytes there are all $FF, below LX_SLOTS);
  - CART_IDENTITY in build/cart/cart_exrom.inc is the CRC of the release images (cart_build.identity());
  - every `out` to port $F4 or $FF in the cartridge listing is in a known routine; `out (c)` lines are listed for review.
Prints a summary; exit 1 on any failure.   Usage: cart_check.py"""
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cart_build  # noqa: E402

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
CART = os.path.join(BUILD, "cart")
KNOWN_OUT = {"BANK_PAGE_EXROM_IN", "CART_ENTRY", "CART_LOAD", "GFX_SET_MODE", "COLD_START", "CC_ERROR",
             "CC_ERROR_AT"}      # (CC_ERROR_AT: the second entry of CC_ERROR)
ALLOWED_NEW = ("CART_", "COMP_CART_", "BANK_CART_")
LST = re.compile(r"^\s*\d+\+*\s+([0-9A-F]{4}) ((?:[0-9A-F]{2} )+)\s*(\S.*)?$")     # a line with assembled bytes
LBL = re.compile(r"^\s*\d+\+*\s+([0-9A-F]{4})\s+([A-Za-z_]\w*):(?!\s*EQU)")        # a global label


def listing(path):
    """[(address, bytes, text, routine)] of the assembled lines; routine = the last global label before the line."""
    out, routine = [], None
    for line in open(path, encoding="latin-1"):
        line = line.rstrip("\n")
        m = LBL.match(line)
        if m:
            routine = m.group(2)
            continue
        m = LST.match(line)
        if m:
            out.append((int(m.group(1), 16), bytes.fromhex(m.group(2)), (m.group(3) or "").split(";")[0].strip(),
                        routine))
    return out


def main():
    errors = []
    rs = cart_build.syms(os.path.join(BUILD, "leapc_home.sym"))
    cs = cart_build.syms(os.path.join(CART, "leapc_cart_home.sym"))
    rimg = open(os.path.join(BUILD, "leapc_home.bin"), "rb").read()
    cimg = open(os.path.join(CART, "leapc_cart_home.bin"), "rb").read()
    if len(rimg) != 0x4000 or len(cimg) != 0x4000:
        sys.exit("cart_check: FAIL the HOME images are %d and %d bytes, not 16384" % (len(rimg), len(cimg)))

    # labels
    moved = {"IO_KEY_SCAN_ROW": (0x0004, 0x000D)}
    for name, value in rs.items():
        if name.startswith("BANK_PAGE_EXROM_IN.") or name in moved:
            if name in moved:
                if (value, cs.get(name)) != moved[name]:
                    errors.append("%s is $%04X in the release and $%04X in the cartridge; expected %s"
                                  % (name, value, cs.get(name, -1), "$%04X -> $%04X" % moved[name]))
                continue
        if name not in cs:
            errors.append("%s ($%04X) is missing from the cartridge build" % (name, value))
        elif cs[name] != value:
            errors.append("%s is $%04X in the cartridge build, $%04X in the release" % (name, cs[name], value))
    new = [n for n in cs if n not in rs]
    for n in new:
        if not (n.startswith(ALLOWED_NEW) or n in ("BANK_PAGE_EXROM_IN.home", "BANK_PAGE_EXROM_IN.out")):
            errors.append("new label %s ($%04X) in the cartridge build" % (n, cs[n]))

    # the places the images may differ
    allowed = [(0x0000, 0x0008), (0x000D, 0x0010),
               (rs["BANK_PAGE_EXROM_IN"], rs["BANK_PAGE_EXROM_OUT"] + 17)]
    cold_jp = rs["RT_ERR_STACK"] - 3           # COLD_START's last instruction (jp LEAPC_EXROM_SHELL / jp CART_RUN)
    if rimg[cold_jp] != 0xC3 or cimg[cold_jp] != 0xC3:
        errors.append("the 3 bytes before RT_ERR_STACK ($%04X) are not a JP in both images" % cold_jp)
    elif cimg[cold_jp + 1] | cimg[cold_jp + 2] << 8 != cs.get("CART_RUN"):
        errors.append("COLD_START's final jump does not go to CART_RUN")
    allowed.append((cold_jp, cold_jp + 3))
    if not rs["COLD_START"] < cold_jp < rs["RT_ERR_STACK"]:
        errors.append("COLD_START's final jump is not inside COLD_START")
    calls = [a for a, b, t, _ in listing(os.path.join(BUILD, "leapc_home.lst"))
             if b[:1] == b"\xcd" and re.fullmatch(r"call\s+IO_KEY_SCAN_ROW", t)]
    if len(calls) != 1:
        errors.append("expected one `call IO_KEY_SCAN_ROW` in the release listing, found %d" % len(calls))
    else:
        a = calls[0]
        if rimg[a + 1:a + 3] != bytes([0x04, 0x00]) or cimg[a + 1:a + 3] != bytes([0x0D, 0x00]) or cimg[a] != 0xCD:
            errors.append("the call at $%04X is not CALL $0004 / CALL $000D" % a)
        allowed.append((a + 1, a + 3))
    cb, ce = cs["COMP_CART_BEGIN"], cs["COMP_CART_END"]
    if not (cb <= ce <= rs["LX_SLOTS"]) or any(b != 0xFF for b in rimg[cb:ce]):
        errors.append("COMP_CART_BEGIN..END ($%04X-$%04X) is not release free space ($FF) below LX_SLOTS ($%04X)"
                      % (cb, ce, rs["LX_SLOTS"]))
    allowed.append((cb, ce))
    diff = 0
    for i in range(0x4000):
        if rimg[i] != cimg[i]:
            diff += 1
            if not any(a <= i < b for a, b in allowed):
                errors.append("byte $%04X differs (release $%02X, cartridge $%02X) outside the cartridge's places"
                              % (i, rimg[i], cimg[i]))
                break

    # the identity
    ident = cart_build.identity()
    m = re.search(r"CART_IDENTITY\s+EQU\s+\$([0-9A-Fa-f]{4})", open(os.path.join(CART, "cart_exrom.inc")).read())
    if not m or int(m.group(1), 16) != ident:
        errors.append("CART_IDENTITY in build/cart/cart_exrom.inc is not $%04X (run tools/cart_build.py)" % ident)

    # every out to $F4 / $FF
    outs, review = [], []
    for a, b, t, routine in listing(os.path.join(CART, "leapc_cart_home.lst")):
        if b[:1] == b"\xd3" and len(b) == 2 and b[1] in (0xF4, 0xFF):
            outs.append((a, routine))
            if routine not in KNOWN_OUT:
                errors.append("out to $%02X at $%04X in %s, not a known routine" % (b[1], a, routine))
        elif b == b"\xed\x41" or re.match(r"out\s+\(c\)", t):
            review.append((a, routine, t))
    seen = sorted({r for _, r in outs}, key=str)
    for r in sorted({r for _, r, _ in review}, key=str):
        n = sum(1 for _, rr, _ in review if rr == r)
        print("cart_check: review: %d `out (c)` in %s" % (n, r))
    if not outs:
        errors.append("no out to $F4/$FF found in the cartridge listing (listing parse broken?)")

    for e in errors:
        print("cart_check: FAIL " + e)
    if errors:
        return 1
    print("cart_check: ok: %d release labels at their addresses (IO_KEY_SCAN_ROW $0004 -> $000D), %d new; %d bytes differ; "
          "cartridge code $%04X-$%04X (%d B, %d B free); identity $%04X; %d out to $F4/$FF in %s"
          % (len(rs), len(new), diff, cb, ce, ce - cb, rs["LX_SLOTS"] - ce, ident, len(outs), ", ".join(seen)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
