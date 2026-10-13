#!/usr/bin/env python3
"""The test build (-DLEAPC_TEST) only appends test hooks: its HOME image must equal the production
HOME image up to LEAPC_HOME_CODE_END, and its EXROM must equal the production EXROM."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")


def sym(path, name):
    for line in open(path):
        m = re.match(r"%s:\s+EQU\s+0x([0-9A-F]+)" % re.escape(name), line, re.I)
        if m:
            return int(m.group(1), 16)
    sys.exit("check_test_image: %s not in %s" % (name, path))


def main():
    end = sym(os.path.join(B, "leapc_home.sym"), "LEAPC_HOME_CODE_END")
    if sym(os.path.join(B, "test", "leapc_home.sym"), "LEAPC_HOME_CODE_END") != end:
        sys.exit("check_test_image: production code ends at a different address in the test build")
    ph = open(os.path.join(B, "leapc_home.bin"), "rb").read()
    th = open(os.path.join(B, "test", "leapc_home.bin"), "rb").read()
    pe = open(os.path.join(B, "leapc_exrom.bin"), "rb").read()
    te = open(os.path.join(B, "test", "leapc_exrom.bin"), "rb").read()
    if ph[:end] != th[:end]:
        sys.exit("check_test_image: HOME production bytes differ in the test build")
    if pe != te:
        sys.exit("check_test_image: EXROM differs in the test build")
    print("test image check: OK (HOME $0000-$%04X and EXROM identical to production)" % (end - 1))


if __name__ == "__main__":
    main()
