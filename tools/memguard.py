"""Leap-C memory guards for the test harness (project_plan.md section 6, Phase 4; docs/milestones/M4.md).

Banking invariants. Three ZEsarUX breakpoint conditions, armed in slots 9-11 (the harness's own
breakpoints use 1-8) while the ROM compiles and runs a program. ZEsarUX evaluates them after every
instruction; the first one that holds stops the machine, and `fired()` names it:
  - the stack in chunk 6 (spec.md 2.2 bank rule 2: never, whatever runs);
  - a paging depth other than 0 while a program runs outside a BREAK-deferring section
    (RUNNING set and NOBRK 0: spec.md 3.3; the EXROM trampolines are NOBRK sections);
  - a write to chunk 6 while the EXROM is paged in (bank rule 3: the EXROM-resident compiler parts
    and the trampolines never touch chunk 6; the IM 1 handler never does).

RAM canary. Before the compile, the RAM no compile may write is filled with CANARY; after it, every
byte that changed is reported. The same before and after the run. Spans:
  - "cells": the tail of the Leap-C cell area (LEAPC_CELLS_END .. LEAPC_CELLS_LIMIT);
  - "platform": the V2 platform cells at $F180-$F3FF (UDGs, the editor's line buffer, dead V2
    cells), except GFX_LINE_X0..Y1, which draw() uses;
  - "top": $FF04-$FFFF (the ROM never uses $FF00-$FFFF; the harness's return slot is $FF00-$FF03);
  - "region N": each image region's gap between the code (up from its base) and the static data
    (down from its end), from the compiler's limits (IMG_LIM) after the compile. Before the compile
    the whole region is canary: the compiler writes only code and data. In the run, writes to the
    region-4 gap are display file 2 when the program switches to the hi-res mode (`hires_ok`);
  - the stack ($F800 .. $FEFF): its low-water mark is measured, not a hit unless below $F800.
The source (the line store) must be unchanged: exectest checks that itself.
"""
INV_SLOT = 9
CANARY = 0xA5
STACK = (0xF800, 0xFF00)
TOP = (0xFF04, 0x10000)


def invariants(S):
    d, r, n = S("BANK_EXROM_DEPTH"), S("RUNNING"), S("NOBRK")
    return [("the stack in chunk 6", "SP>BFFFH and SP<E000H"),
            ("a paging depth other than 0 while the program runs",
             "PEEK(%04XH)<>0 and PEEK(%04XH)=0 and PEEK(%04XH)<>0" % (r, n, d)),
            ("a write to chunk 6 with the EXROM paged in", "MWA>BFFFH and MWA<E000H and PEEK(%04XH)<>0" % d)]


def arm(m, on=True):
    for i, (_, cond) in enumerate(invariants(m.sym)):
        m.cmd("set-breakpoint %d %s" % (INV_SLOT + i, cond) if on else "set-breakpoint %d" % (INV_SLOT + i))


def fired(m):
    """The invariants whose condition holds now (after an unexpected stop)."""
    out = []
    for name, cond in invariants(m.sym):
        try:
            if int(m.cmd("evaluate " + cond).strip().split()[0]):
                out.append(name)
        except (ValueError, IndexError):
            pass
    return out


def regions(S):
    return [(S("LEAPC_IMG%d_BASE" % k), S("LEAPC_IMG%d_END" % k)) for k in (1, 2, 3, 4)]


def dead_spans(S):
    gl = S("GFX_LINE_X0")
    return [("cells", S("LEAPC_CELLS_END"), S("LEAPC_CELLS_LIMIT")),
            ("platform", S("LEAPC_PLAT_BASE"), gl), ("platform", gl + 4, S("LEAPC_PLAT_END")),
            ("top", TOP[0], TOP[1])]


def limits(m):
    """The compiler's image limits after a compile: per region [low][high]."""
    d = m.read(m.sym("IMG_LIM"), 16)
    return [(d[4 * k] | d[4 * k + 1] << 8, d[4 * k + 2] | d[4 * k + 3] << 8) for k in range(4)]


class Canary:
    def __init__(self, m):
        self.m = m
        self.S = m.sym
        self.compile_spans = None
        self.run_spans = None
        self.stack_low = {}

    def _fill(self, spans):
        for _, lo, hi in spans:
            if hi > lo:
                self.m.write(lo, bytes([CANARY]) * (hi - lo))

    def _check(self, spans):
        hits = []
        for name, lo, hi in spans:
            if hi <= lo:
                continue
            d = self.m.read(lo, hi - lo)
            bad = [lo + i for i, x in enumerate(d) if x != CANARY]
            if bad:
                hits.append(dict(span=name, first="$%04X" % bad[0], last="$%04X" % bad[-1], bytes=len(bad)))
        return hits

    def _low(self, what):
        d = self.m.read(STACK[0], STACK[1] - STACK[0])
        low = next((STACK[0] + i for i, x in enumerate(d) if x != CANARY), None)
        self.stack_low[what] = low
        return low

    def before_compile(self):
        self.compile_spans = dead_spans(self.S) + [("region %d" % (k + 1), lo, hi)
                                                   for k, (lo, hi) in enumerate(regions(self.S))]
        self._fill(self.compile_spans + [("stack", STACK[0], STACK[1])])

    def after_compile(self):
        """Hits of the compile: the dead spans, and each region outside its code and data."""
        lim = limits(self.m)
        spans = dead_spans(self.S)
        for k, ((base, end), (low, high)) in enumerate(zip(regions(self.S), lim)):
            if base <= low <= high <= end:
                spans.append(("region %d" % (k + 1), low, high))
        self._low("compile")
        return self._check(spans)

    def before_run(self, hires_ok=False):
        lim = limits(self.m)
        self.hires_ok = hires_ok
        self.run_spans = dead_spans(self.S)
        for k, ((base, end), (low, high)) in enumerate(zip(regions(self.S), lim)):
            if base <= low <= high <= end:
                self.run_spans.append(("region %d" % (k + 1), low, high))
        self._fill(self.run_spans + [("stack", STACK[0], STACK[1])])

    def run_stack_low(self):
        """The run's lowest stack byte: read before the harness calls anything after the run."""
        return self._low("run")

    def after_run(self):
        """The run's hits (chunk 6 must be RAM: the caller pages the EXROM out first)."""
        hits = self._check(self.run_spans)
        if self.hires_ok:
            for h in hits:
                if h["span"] == "region 4":
                    h["span"] = "region 4 (display file 2, hi-res mode)"
                    h["allowed"] = True
        return hits
