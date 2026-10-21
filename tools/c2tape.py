#!/usr/bin/env python3
"""Turn a host C source file into a Leap-C program tape (spec.md 8.1; project_plan.md Phase 7).

The tape is what the ROM's own SAVE "name" writes for that source: a header block (type 0, the name padded
to 10 characters with spaces, the length, the version word $8C00 in the autostart field, the program
length) and a data block holding the line store verbatim ([length:2][text][CR] per line: tools/c2src.py,
with the editor's rules: ASCII 32-126, at most 127 characters a line). LOAD "name" or LOAD "" reads it.

The output's extension picks the format: .tap (each block with its length) or .tzx (standard speed data
blocks, a 1 s pause after each). Real tape audio is made from either by any TAP/TZX player.

Usage: c2tape.py [--name NAME] FILE.c OUT.tap|OUT.tzx
The name defaults to the file's base name (at most 10 characters: longer ones are refused, as SAVE does).
"""
import argparse
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2src                                                    # noqa: E402
import tapes                                                    # noqa: E402

ROOM = 0xC000 - 0x7800          # the line store's room (spec.md 3.1: LOAD refuses a longer program)


def program_blocks(text, name):
    """The two framed blocks of the program tape for C source `text`."""
    if not 1 <= len(name) <= 10 or any(not 32 <= ord(c) <= 126 or c == '"' for c in name):
        raise c2src.SourceError("the name must be 1-10 characters of ASCII 32-126, no quote (%r)" % name)
    data = c2src.records(c2src.lines_of(text))
    if not data:
        raise c2src.SourceError("no program (an empty source cannot be loaded)")
    if len(data) > ROOM:
        raise c2src.SourceError("%d bytes of line store: more than the %d that LOAD accepts" % (len(data), ROOM))
    return tapes.file_blocks(tapes.PROGRAM, name, data)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--name")
    ap.add_argument("src")
    ap.add_argument("out")
    a = ap.parse_args()
    name = a.name if a.name is not None else os.path.splitext(os.path.basename(a.src))[0]
    ext = os.path.splitext(a.out)[1].lower()
    if ext not in (".tap", ".tzx"):
        sys.exit("c2tape: the output must be a .tap or .tzx file")
    try:
        blocks = program_blocks(open(a.src, encoding="latin-1").read(), name)
    except c2src.SourceError as e:
        sys.exit("c2tape: %s: %s" % (a.src, e))
    open(a.out, "wb").write(tapes.tap(blocks) if ext == ".tap" else tapes.tzx(blocks))
    print("c2tape: %s: program %r, %d bytes of source" % (a.out, name, len(blocks[1]) - 2))


if __name__ == "__main__":
    main()
