"""Leap-C tapes for the tests and the host tools (project_plan.md Phase 7; spec.md 8).

Blocks, files and signals:
  - framed(flag, payload): a tape block as the ROM sends it: the flag byte, the payload, the XOR checksum;
  - header(htype, name, length, version, proglen): the 17-byte header payload (stock TS2068 layout: type,
    10-character name padded with spaces, length, the autostart field holding the version word, program
    length);
  - tap(blocks), tzx(blocks): the .tap file (each block with its 2-byte length) and the .tzx file (standard
    speed data blocks, ID $10, 1 s pause after each);
  - Tape: an EAR signal as a list of (level, T-states) runs, with the stock ROM's timing (the pulses Leap-C's
    own SAVE sends: STORAGE_SEND_BLOCK, the real ROM's SA-BYTES); faults can be built in (a dropout, a
    truncated block, any byte changed, fewer pilot pulses), and it is written as ZEsarUX's raw tape
    format (.rwa: 8-bit unsigned samples, one per scan line) for its real-tape input (`realtape-open`);
  - decode(edges): the blocks in a captured MIC signal: [(T-state, level)] at each `out` of the ROM's
    STORAGE_SEND_BLOCK (lcharness.Machine.tape_capture), with every pulse width measured.

Derived from 2068-Leap's tools/tape_synth.py and tools/make_extension_tzx.py (V2 reference tag
v2.0.1-emu.1): the same run-list model, the same sample levels; copied and adapted, not imported. V2
synthesised its pulses from 80-T samples; Leap-C uses the stock ROM's T-state widths, which its own SAVE
produces (measured: decode()).
"""
import struct
from functools import reduce
from operator import xor

CPU_HZ = 3_528_000              # TS2068 CPU clock
SAMPLE_T = 224                  # ZEsarUX reads one real-tape sample per scan line (screen_testados_linea)
PILOT_T, SYNC1_T, SYNC2_T, ZERO_T, ONE_T = 2168, 667, 735, 855, 1710       # the stock ROM's half-pulses
HEADER_PILOT, DATA_PILOT = 8063, 3223                                        # pilot half-pulses
LEAPC_VERSION = 0x8C00          # spec.md 8.1 (include/leapc_layout.inc LEAPC_TAPE_VERSION)
V2_VERSION = 0x8101             # Leap V2's program-format word (V2_FORMAT_WORD: major 1, minor 1)
PROGRAM, DATA = 0, 3            # header types: a program (the source), a data block (tape_save)


def framed(flag, payload):
    body = bytes([flag]) + bytes(payload)
    return body + bytes([reduce(xor, body, 0)])


def header(htype, name, length, version=LEAPC_VERSION, proglen=None):
    nm = name.encode("latin-1") if isinstance(name, str) else bytes(name)
    nm = nm[:10].ljust(10, b" ")
    return (bytes([htype]) + nm + struct.pack("<HHH", length & 0xFFFF, version & 0xFFFF,
                                              (length if proglen is None else proglen) & 0xFFFF))


def file_blocks(htype, name, data, version=LEAPC_VERSION):
    """The two framed blocks of a tape file: the header, then the data."""
    return [framed(0x00, header(htype, name, len(data), version)), framed(0xFF, data)]


def tap(blocks):
    return b"".join(struct.pack("<H", len(b)) + b for b in blocks)


def tzx(blocks, pause_ms=1000):
    out = bytearray(b"ZXTape!\x1a\x01\x14")
    for b in blocks:
        out += bytes([0x10]) + struct.pack("<HH", pause_ms, len(b)) + b
    return bytes(out)


def read_tap(data):
    """The blocks of a .tap file."""
    out, p = [], 0
    while p + 2 <= len(data):
        n = data[p] | data[p + 1] << 8
        out.append(data[p + 2:p + 2 + n])
        p += 2 + n
    return out


class Tape:
    """An EAR signal: (level, T-states) runs; each pulse flips the level."""

    def __init__(self):
        self.runs = []
        self.level = 0

    def pulse(self, t):
        self.runs.append((self.level, t))
        self.level ^= 1

    def flat(self, t):
        """No edge for t T-states (silence, a dropout)."""
        self.runs.append((self.level, t))

    def silence(self, seconds):
        self.flat(int(seconds * CPU_HZ))

    def block(self, data, pilot=None, dropout=None, truncate_after=None, gap=0.5):
        """One framed block (flag .. checksum in `data`): pilot, the two sync pulses, two half-pulses per
        bit (most significant first), a closing pulse, then `gap` seconds of silence.
        dropout=(first, count): those bytes (0 = the flag) are a flat stretch of the same duration;
        truncate_after=n: only the first n bytes, then silence."""
        n = (HEADER_PILOT if data[0] < 0x80 else DATA_PILOT) if pilot is None else pilot
        for _ in range(n):
            self.pulse(PILOT_T)
        self.pulse(SYNC1_T)
        self.pulse(SYNC2_T)
        for i, v in enumerate(data):
            if truncate_after is not None and i >= truncate_after:
                break
            widths = []
            for k in range(7, -1, -1):
                w = ONE_T if v >> k & 1 else ZERO_T
                widths += [w, w]
            if dropout and dropout[0] <= i < dropout[0] + dropout[1]:
                self.flat(sum(widths))
            else:
                for w in widths:
                    self.pulse(w)
        self.pulse(ZERO_T)
        self.silence(gap)
        return self

    def file(self, blocks, **faults):
        """Blocks one after another; faults (as block()'s) apply to the last."""
        for i, b in enumerate(blocks):
            self.block(b, **(faults if i == len(blocks) - 1 else {}))
        return self

    @classmethod
    def from_edges(cls, edges):
        """A captured MIC signal (decode()'s input) as a Tape, its pulses exactly as the ROM timed them."""
        t = cls()
        lv = [(tt, l) for tt, l in edges]
        for (t0, l0), (t1, _) in zip(lv, lv[1:]):
            t.runs.append((l0, t1 - t0))
        if lv:
            t.level = lv[-1][1]
        t.silence(0.5)
        return t

    def to_rwa(self, lead=1.0, tail=1.0, sample_t=SAMPLE_T):
        """Point-sampled: level 1 -> $C8, 0 -> $38, the lead and the tail idle ($80)."""
        out = bytearray()

        def until(byte, end_t):
            n = int(end_t / sample_t)
            if n > len(out):
                out.extend(bytes([byte]) * (n - len(out)))

        t = lead * CPU_HZ
        until(0x80, t)
        for level, dt in self.runs:
            t += dt
            until(0xC8 if level else 0x38, t)
        until(0x80, t + tail * CPU_HZ)
        return bytes(out)

    def write_rwa(self, path, lead=1.0, tail=1.0):
        open(path, "wb").write(self.to_rwa(lead, tail))
        return path

    def seconds(self):
        return sum(t for _, t in self.runs) / CPU_HZ


def edges_from_capture(values):
    """lcharness's capture lines (TSTATESP * 16 + (A & 8) at each `out (PORT_ULA), a`) -> [(T, MIC level)]
    at the level changes, the 32-bit counter unwrapped."""
    out, base, prev = [], 0, None
    for v in values:
        v &= 0xFFFFFFFF
        if prev is not None and v < prev:
            base += 1 << 32
        prev = v
        t, level = (base + v) >> 4, (v >> 3) & 1
        if not out or out[-1][1] != level:
            out.append((t, level))
    return out


def decode(edges):
    """The blocks in a MIC signal. Returns [dict(data=framed bytes, ok=checksum, pilot=pulses, widths=
    {"pilot", "sync1", "sync2", "zero", "one": (min, max)})]. A block is pilot pulses (1,900-2,500 T),
    two sync pulses (< 1,000 T) and bit pulses in pairs; a pulse over 5,000 T ends it."""
    w = [(t1 - t0) for (t0, _), (t1, _) in zip(edges, edges[1:])]
    blocks, i = [], 0

    def span(name, x, d):
        lo, hi = d.get(name, (x, x))
        d[name] = (min(lo, x), max(hi, x))

    while i < len(w):
        while i < len(w) and not 1900 <= w[i] <= 2500:
            i += 1
        n, widths = 0, {}
        while i < len(w) and 1900 <= w[i] <= 2500:
            span("pilot", w[i], widths)
            n += 1
            i += 1
        if i + 1 >= len(w) or n < 100:
            break
        span("sync1", w[i], widths)
        span("sync2", w[i + 1], widths)
        i += 2
        bits = []
        while i + 1 < len(w) and w[i] < 2500 and w[i + 1] < 2500:
            b = 1 if w[i] + w[i + 1] > 2 * (ZERO_T + ONE_T) / 2 else 0
            span("one" if b else "zero", w[i], widths)
            span("one" if b else "zero", w[i + 1], widths)
            bits.append(b)
            i += 2
        data = bytes(int("".join(map(str, bits[k:k + 8])), 2) for k in range(0, len(bits) - len(bits) % 8, 8))
        blocks.append(dict(data=data, ok=bool(data) and reduce(xor, data, 0) == 0, pilot=n, widths=widths,
                           extra_bits=len(bits) % 8))
    return blocks
