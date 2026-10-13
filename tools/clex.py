#!/usr/bin/env python3
"""Host reference lexer for Leap-C (spec.md section 4.1), written independently of the Z80 lexer.

The test runner compares the ROM lexer's token dump with this lexer's output on every case, field
by field (kind, line-start flag, line, value / bytes, error and its line). Token kinds and error
numbers mirror include/leapc_tokens.inc and include/leapc_errors.inc (read from those files, so the
numbering cannot drift).

Usage as a tool: clex.py FILE.c [--eol]   prints the token stream."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _equs(path):
    out = {}
    for line in open(path):
        m = re.match(r"\s*([A-Z_0-9]+)\s+EQU\s+([^;]+)", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    # resolve simple expressions (NAME + NAME, $hex, decimal)
    vals = {}

    def ev(e):
        e = e.replace("$", "0x")
        return eval(e, {}, vals)
    for _ in range(4):
        for k, e in out.items():
            if k not in vals:
                try:
                    vals[k] = ev(e)
                except Exception:
                    pass
    return vals


TK = _equs(os.path.join(ROOT, "include", "leapc_tokens.inc"))
ER = _equs(os.path.join(ROOT, "include", "leapc_errors.inc"))

KEYWORDS = ["auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else",
            "enum", "extern", "float", "for", "goto", "if", "int", "long", "register", "return", "short",
            "signed", "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void",
            "volatile", "while"]
KW_KIND = {k: TK["TK_KW_FIRST"] + i for i, k in enumerate(KEYWORDS)}
PUNCT = {
    "(": "TK_LPAREN", ")": "TK_RPAREN", "[": "TK_LBRACK", "]": "TK_RBRACK", "{": "TK_LBRACE",
    "}": "TK_RBRACE", ",": "TK_COMMA", ";": "TK_SEMI", ":": "TK_COLON", "?": "TK_QUEST",
    "~": "TK_TILDE", ".": "TK_DOT", "#": "TK_HASH", "=": "TK_ASSIGN", "!": "TK_NOT", "<": "TK_LT",
    ">": "TK_GT", "*": "TK_STAR", "/": "TK_SLASH", "%": "TK_PERCENT", "+": "TK_PLUS", "-": "TK_MINUS",
    "&": "TK_AMP", "^": "TK_CARET", "|": "TK_BAR", "<<": "TK_SHL", ">>": "TK_SHR", "&&": "TK_ANDAND",
    "||": "TK_OROR", "++": "TK_INC", "--": "TK_DEC", "->": "TK_ARROW", "...": "TK_ELLIPSIS",
    "==": "TK_EQ", "!=": "TK_NE", "<=": "TK_LE", ">=": "TK_GE", "*=": "TK_MULASSIGN",
    "/=": "TK_DIVASSIGN", "%=": "TK_MODASSIGN", "+=": "TK_ADDASSIGN", "-=": "TK_SUBASSIGN",
    "&=": "TK_ANDASSIGN", "^=": "TK_XORASSIGN", "|=": "TK_ORASSIGN", "<<=": "TK_SHLASSIGN",
    ">>=": "TK_SHRASSIGN",
}
PUNCT_KIND = {p: TK[n] for p, n in PUNCT.items()}
KIND_NAME = {v: k for k, v in PUNCT_KIND.items()}
KIND_NAME.update({v: k for k, v in KW_KIND.items()})
KIND_NAME.update({TK["TK_EOF"]: "eof", TK["TK_IDENT"]: "id", TK["TK_NUM"]: "num",
                  TK["TK_STR"]: "str", TK["TK_EOL"]: "eol"})
ESCAPES = {"n": 10, "t": 9, "r": 13, "\\": 92, "'": 39, '"': 34, "?": 63, "a": 7, "b": 8, "f": 12,
           "v": 11}
TF_BOL, TF_UNSIGNED, TF_CHARCONST = 1, 2, 4
IDENT_SIG = 31
TOK_BUF_LEN = 128


class LexError(Exception):
    def __init__(self, code, line):
        super().__init__("error %d at line %d" % (code, line))
        self.code, self.line = code, line


class Token:
    __slots__ = ("kind", "flags", "line", "value", "text")

    def __init__(self, kind, flags, line, value=None, text=None):
        self.kind, self.flags, self.line, self.value, self.text = kind, flags, line, value, text

    def key(self):
        return (self.kind, self.flags, self.line, self.value, self.text)

    def __repr__(self):
        s = "%s@%d" % (KIND_NAME.get(self.kind, hex(self.kind)), self.line)
        if self.flags & TF_BOL:
            s = "^" + s
        if self.value is not None:
            s += "=%d" % self.value
        if self.text is not None:
            s += "=%r" % self.text
        if self.flags & TF_UNSIGNED:
            s += "u"
        if self.flags & TF_CHARCONST:
            s += "c"
        return s


def lex(lines, eol_mode=False):
    """lines: list of str (the line-store records' text). Returns (tokens, error or None)."""
    toks = []
    text = "".join(l + "\r" for l in lines) + "\0"
    # line number of each offset
    i = 0
    line = 1
    bolp = True
    n = len(text)

    def err(code, at_line):
        raise LexError(ER[code], at_line)

    def isid(c):
        return c.isascii() and (c.isalnum() or c == "_")

    def digit(c, base):
        if not (c.isascii() and c.isalnum()):
            return None
        v = int(c, 36)
        return v if v < base else None

    try:
        while True:
            c = text[i]
            if c == " ":
                i += 1
                continue
            if c == "\r":
                if eol_mode:
                    toks.append(Token(TK["TK_EOL"], TF_BOL if bolp else 0, line))
                    bolp = False
                i += 1
                if text[i] != "\0":
                    line += 1
                    bolp = True
                continue
            if c == "/" and text[i + 1] == "/":
                while text[i] != "\r":
                    i += 1
                continue
            if c == "/" and text[i + 1] == "*":
                start = line                    # E_COMMENT is reported where the comment starts
                i += 2
                while True:
                    if text[i] == "\0":
                        err("E_COMMENT", start)
                    if text[i] == "*" and text[i + 1] == "/":
                        i += 2
                        break
                    if text[i] == "\r" and text[i + 1] != "\0":
                        line += 1
                        bolp = True             # a comment does not change the line-start state
                    i += 1
                continue
            flags = TF_BOL if bolp else 0
            bolp = False
            tl = line
            if c == "\0":
                if i != n - 1:
                    err("E_BADCHAR", tl)        # a NUL inside a line is not the end of the source
                toks.append(Token(TK["TK_EOF"], flags, tl))
                return toks, None
            if c == "_" or (c.isascii() and c.isalpha()):
                j = i
                while isid(text[j]):
                    j += 1
                name = text[i:j][:IDENT_SIG]
                i = j
                if name in KW_KIND:
                    toks.append(Token(KW_KIND[name], flags, tl))
                else:
                    toks.append(Token(TK["TK_IDENT"], flags, tl, text=name.encode("latin-1")))
                continue
            if c.isascii() and c.isdigit():
                if c == "0" and text[i + 1] in "xX":
                    base, j = 16, i + 2
                elif c == "0":
                    base, j = 8, i + 1
                else:
                    base, j = 10, i
                k = j
                v = 0
                while digit(text[k], base) is not None:
                    v = v * base + digit(text[k], base)
                    if v > 65535:
                        err("E_RANGE", tl)
                    k += 1
                if base == 16 and k == j:
                    err("E_NUMBER", tl)
                i = k
                f = flags
                if text[i] == ".":
                    err("E_NOTSUP", tl)
                if text[i] in "uU":
                    f |= TF_UNSIGNED
                    i += 1
                if text[i] in "lL":
                    err("E_NOTSUP", tl)
                if text[i] in "eE" and base != 16:
                    err("E_NOTSUP", tl)
                if isid(text[i]):
                    err("E_NUMBER", tl)
                if v > 32767:
                    f |= TF_UNSIGNED
                toks.append(Token(TK["TK_NUM"], f, tl, value=v))
                continue

            def one_char(i):
                """value of the literal character at i (escape-aware), new index"""
                ch = text[i]
                if ch != "\\":
                    return ord(ch), i + 1
                e = text[i + 1]
                if e in ESCAPES:
                    return ESCAPES[e], i + 2
                if e == "x":
                    k = i + 2
                    v = 0
                    while digit(text[k], 16) is not None:
                        v = v * 16 + digit(text[k], 16)
                        if v > 65535:
                            err("E_ESCAPE", tl)
                        k += 1
                    if k == i + 2 or v > 255:
                        err("E_ESCAPE", tl)
                    return v, k
                if "0" <= e <= "7":
                    k = i + 1
                    v = 0
                    while k < i + 4 and digit(text[k], 8) is not None:
                        v = v * 8 + digit(text[k], 8)
                        k += 1
                    if v > 255:
                        err("E_ESCAPE", tl)
                    return v, k
                err("E_ESCAPE", tl)

            if c == '"':
                i += 1
                out = bytearray()
                while text[i] != '"':
                    if text[i] < " ":
                        err("E_STRING", tl)
                    v, i = one_char(i)
                    if len(out) >= TOK_BUF_LEN:
                        err("E_TOOLONG", tl)
                    out.append(v)
                i += 1
                toks.append(Token(TK["TK_STR"], flags, tl, text=bytes(out)))
                continue
            if c == "'":
                i += 1
                if text[i] == "'" or text[i] < " ":
                    err("E_CHARCONST", tl)
                v, i = one_char(i)
                if text[i] != "'":
                    err("E_CHARCONST", tl)
                i += 1
                toks.append(Token(TK["TK_NUM"], flags | TF_CHARCONST, tl, value=v))
                continue
            if c == "." and text[i + 1].isascii() and text[i + 1].isdigit():
                err("E_NOTSUP", tl)
            for p in ("...", "<<=", ">>="):
                if text.startswith(p, i):
                    break
            else:
                p = None
            if p is None:
                if text[i:i + 2] in PUNCT_KIND:
                    p = text[i:i + 2]
                elif c in PUNCT_KIND:
                    p = c
                else:
                    err("E_BADCHAR", tl)
            toks.append(Token(PUNCT_KIND[p], flags, tl))
            i += len(p)
    except LexError as e:
        return toks, e


def main():
    path = sys.argv[1]
    lines = open(path).read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    toks, e = lex(lines, "--eol" in sys.argv)
    for t in toks:
        print(t)
    if e:
        print("ERROR %d line %d" % (e.code, e.line))


if __name__ == "__main__":
    main()
