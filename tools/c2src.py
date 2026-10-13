#!/usr/bin/env python3
"""Turn a host C source file into Leap-C line-store records (spec.md section 3.2):
[length:2, little-endian = text bytes + 1][text][CR] per line, the format the editor keeps and that
program tapes carry. The same records are used by the test harness and, in Phase 7, by c2tape.py.

Rules (the editor's): ASCII 32-126 only, at most 127 characters per line. Tabs are expanded to
8-column stops; a trailing newline does not add an empty line; anything else is refused.

Usage: c2src.py FILE.c OUT.bin      (or import: lines_of(text) / records(lines))"""
import struct
import sys

MAX_LINE = 127


class SourceError(Exception):
    pass


def lines_of(text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    for n, l in enumerate(lines, 1):
        l = l.rstrip("\r").expandtabs(8)
        bad = [c for c in l if not (32 <= ord(c) <= 126)]
        if bad:
            raise SourceError("line %d: character %r is outside ASCII 32-126" % (n, bad[0]))
        if len(l) > MAX_LINE:
            raise SourceError("line %d: %d characters (the limit is %d)" % (n, len(l), MAX_LINE))
        out.append(l)
    return out


def records(lines):
    return b"".join(struct.pack("<H", len(l) + 1) + l.encode("ascii") + b"\r" for l in lines)


def main():
    src, out = sys.argv[1:3]
    try:
        data = records(lines_of(open(src, encoding="latin-1").read()))
    except SourceError as e:
        sys.exit("c2src: %s: %s" % (src, e))
    open(out, "wb").write(data)


if __name__ == "__main__":
    main()
