# 2068-Leap-C — Tape Block Signal Specification

**Version 1.0, 2026-10-22.** The clean-room specification of Leap-C's tape block I/O: `TAPE_SEND_BLOCK` (send one
cassette block) and `TAPE_RECV_BLOCK` (receive or verify one). It replaces, for a new implementation, the routines
that V2 ported from the stock ROM (`NOTICE` §3; `project_plan.md` Phase 11, "the tape block routines rewritten").

**How it was written (Stage A).** It describes the **signal** on the tape and the **behaviour** the callers and the
tests require. It was written from public descriptions of the cassette format, Leap-C's own documents, the callers'
code and contract headers, and the tests. Its author did not read the old routines' bodies, any stock ROM image or
any ROM disassembly. Nothing here describes the stock ROM's algorithm or its loop constants. Where the old routines'
behaviour shows only through a test or a document, that is said, with the source. The Stage B author writes the
code from this document alone.

**How to read it.** "Must" is a requirement: a test, a caller or the format depends on it. "Should" is a target:
the owner wants it, and no current test checks it. Every fact gives its source in brackets:

| Tag | Source |
|---|---|
| [TZX] | the TZX format description, `worldofspectrum.net/TZXformat.html`: blocks ID $10-$15, the timing table of ID $11, the pulse-level notes |
| [WIKI] | Sinclair Wiki, "Spectrum tape interface" (`sinclair.wiki.zxnet.co.uk/wiki/Spectrum_tape_interface`): pulses, pilot, sync, bit encoding, flag, XOR checksum, polarity |
| [FAQ] | comp.sys.sinclair FAQ, "16K/48K ZX Spectrum Reference" (`worldofspectrum.org/faq/reference/48kreference.htm`): port $FE, keyboard half-rows, EAR bit, I/O contention |
| [FUSE-LD] | Fuse 1.9.1's loader detection (`loader.c`, `loader_detect_loader`), **as the orchestrator described it** (the Stage A author did not read Fuse's source; its accelerator part matches on stock ROM code) |
| file:line | a Leap-C file. Line numbers are for commit `6201aa2` as read during Stage A (see §11) |
| *case* | a test case: `tools/tapetest.py` (suite `tape`), `tools/fusetest.py` (`make fuse`), `tests/lib/tape/*.c` (the corpus), `tools/hwkit.py --verify` |

---

## 1. Summary of the requirements

| # | Requirement | Section |
|---|---|---|
| R1 | Emit the standard signal: pilot 2,168 T, sync 667 / 735 T, bits as two equal half-pulses of 855 T (0) or 1,710 T (1), most significant bit first, 8,063 / 3,223 pilot half-pulses, then a closing edge | §2 |
| R2 | Every emitted half-pulse within −2..+16 T of nominal on ZEsarUX, at every place in the block (pilot to sync, sync to bits, between bytes, the last bit) | §2.6 |
| R3 | MIC on bit 3 of port $FE, written only by `out (PORT_ULA), a`, at most 5 of them, all between `TAPE_SEND_BLOCK` and `TAPE_RECV_BLOCK` | §3, §8.3 |
| R4 | Disable interrupts at entry (`TAPE_BLOCK` enters with them **on**); leave the paging alone; never use more than 34 B of stack below the entry SP | §3.3-§3.5 |
| R5 | The contracts of §4 exactly: registers in and out, carry, DE outstanding, IX walking the buffer, nothing stored outside [IX, IX+DE) | §4 |
| R6 | The sender tests SPACE after every byte (the flag included), never during the pilot or sync, and returns carry **set** when the block was sent whole and carry **clear** when SPACE stopped it | §4.1 |
| R7 | The receiver tests SPACE at every edge wait, silence included, and fails at once | §5.6 |
| R8 | The receiver reports every failure with carry set: no signal, SPACE, wrong flag, verify mismatch, dropout, checksum | §4.2 |
| R9 | A receive call gives up in silence after about 8.6 s (so a LOAD that finds nothing ends after about 2 minutes) | §4.4 |
| R10 | The receiver accepts every pilot of ≥ 3,223 half-pulses, either polarity, the sampling of ZEsarUX (224 T), Fuse (80 T) and 44.1 kHz WAVs, and the envelope of §6 | §5, §6 |
| R11 | The receiver's port reads satisfy Fuse's loader detection | §5.8 |
| R12 | Tapes stay readable both ways with V2's ROM and a stock TS2068 or Spectrum | §7 |
| R13 | HOME, sjasmplus 1.23.1 strict, ≤ 331 B for both (budget 340 B with the ledger), Leap-C's source style | §8 |

---

## 2. The signal (R1, R2)

### 2.1 The half-pulse model

The tape signal is a square wave whose information is only in the **time between edges** [WIKI: "the initial
polarity of the signal does not matter"]. The unit is the **half-pulse** (TZX and the Wiki call it a *pulse*): the
MIC level held for N T-states, then toggled. Two half-pulses make one complete cycle [WIKI].

- **The sender** writes a level to MIC, keeps it for N T, writes the opposite level, and so on. The width of a
  half-pulse is the time between two consecutive level changes.
- **The receiver** sees only EAR's level changes (edges) and measures the time between them. It must never rely on
  which level is "high" [TZX: "whether this is implemented as ear=1 and ear=0 respectively or the other way around is
  not important"; WIKI].

### 2.2 Widths (T-states)

| Element | Half-pulses | Width each | Source |
|---|---|---:|---|
| Pilot (leader) tone | 8,063 if the flag byte < $80 (a header block); 3,223 if ≥ $80 (a data block) | 2,168 T | [TZX] ID $10/$11; [WIKI] |
| First sync | 1 | 667 T | [TZX]; [WIKI] |
| Second sync | 1 | 735 T | [TZX]; [WIKI] |
| A 0 bit | 2 | 855 T | [TZX]; [WIKI] |
| A 1 bit | 2 | 1,710 T | [TZX]; [WIKI] |
| Bit order | — | most significant bit first | `tools/tapes.py` `Tape.block` (`for k in range(7, -1, -1)`), `decode`; M7.md §9.2 |
| After the block (TZX) | a pause, 1,000 ms by default | — | [TZX] ID $11 table |

Leap-C's constants in the tests are the same: `tools/tapes.py:33-34` (`PILOT_T, SYNC1_T, SYNC2_T, ZERO_T, ONE_T =
2168, 667, 735, 855, 1710`; `HEADER_PILOT, DATA_PILOT = 8063, 3223`). spec.md §8.1 records them as measured on
Leap-C's own SAVE.

The pilot length depends only on the flag byte: `A < $80` gives 8,063, otherwise 3,223 [TZX ID $10: "8063 pulses if
the first data byte (flag byte) is < 128, 3223 otherwise"]. Leap-C's callers use only $00 and $FF
(`STORAGE_TYPE_HEADER`, `STORAGE_TYPE_DATA`, `platform/kernel/storage/storage.asm:108-114`). The routine must still
follow the rule for any A.

### 2.3 The block

A block is the **flag byte**, the **payload** (DE bytes from IX) and the **checksum**: one byte, the XOR of the flag
and every payload byte [WIKI: "a binary XOR of the block's bytes"]. The XOR of all the bytes of a correct block,
checksum included, is therefore 0 (`tools/tapes.py` `framed`; `decode`'s `ok`).

On tape, in order: the pilot, sync 1, sync 2, then every byte of flag + payload + checksum as 8 bits (16
half-pulses each), most significant bit first, then the **closing edge** (§2.4).

Leap-C's two-block file format (header block: flag $00, 17-byte payload; data block: flag $FF) belongs to the
header logic (spec.md §8.1, §8.4; `tools/tapes.py` `header`, `file_blocks`). The block routines treat the payload as
opaque bytes.

### 2.4 The closing edge (sender)

The last half-pulse of the checksum's last bit must **end in an edge**: one more level change after its width.
Otherwise nothing marks that half-pulse's end:

- the test decoder needs it. `tools/tapes.py` `decode` reads bits as pairs of widths between edges. Without the edge,
  the last bit is lost, the block decodes one bit short (`extra_bits` 7), its checksum byte is missing and `ok` is
  false (*roundtrip*, *lib-save*, *host-tape*: the bytes must equal the expected blocks exactly);
- the stock receivers and Leap-C's own receiver time the last half-pulse up to that edge.

The synthesised tapes add one more 855 T half-pulse after the checksum (`Tape.block`: `self.pulse(ZERO_T)`, then
`gap` seconds of silence). That is the same closing edge as seen from the receiving side. A sender may give its
closing edge that form: one more toggle 855 T after the last bit's end. Nothing more is needed after it.

**Amendment (the orchestrator, after the first implementation, M11-tape).** The closing pulse is **required**, not
optional: the sender must toggle MIC once more about 855 T (a 0 half-pulse, within the same −2..+16 T) after the end
of the checksum's last bit, then leave the line. Found by the independent decoder: fuse-utils' `audio2tape` (on a
Fuse recording of SAVE converted with `tape2wav`) decodes a header block without that pulse but then misses the data
block that follows; with it, both blocks decode, as for beta.1's SAVE. Leap-C's receivers do not need it; other
decoders do.

### 2.5 Clock: 3.5 MHz and 3.528 MHz

TZX writes every timing in T-states of a **3.5 MHz** clock, the 16K/48K Spectrum's [TZX: "ALL timings written
according to a 3.5MHz clock"]. The TS2068 runs at **3.528 MHz** (`tools/tapes.py:31` `CPU_HZ = 3_528_000`).

Leap-C's tapes keep the **same T-state counts** at 3.528 MHz. The pilot is 2,168 T of the TS2068 clock (614.5 µs),
0.8% shorter in real time than a Spectrum's (619.4 µs). This is what Leap-C's SAVE measures (spec.md §8.1; M7.md
§10), what the synthesised tapes and the kit's WAVs contain (`Tape.to_wav`: "point-sampled at the TS2068 clock"),
and how Fuse plays a TZX on its TS2068 (`tapes.py` `tzx_from_wav`: "Fuse plays TZX T-states at the machine's
clock").

A tape recorded on a real 3.5 MHz Spectrum measures about 0.8% longer on a TS2068 (a pilot about 2,185 T). That is
far inside every tolerance below. **The sender must not rescale:** it emits 2,168 / 667 / 735 / 855 / 1,710 T of
its own clock.

### 2.6 What the tests accept for SAVE's output (R2)

`tools/tapetest.py` captures the MIC line of every SAVE (§8.3) and decodes it with `tools/tapes.py` `decode`.

**Widths** (`tapetest.py:194` `widths_ok`). For every block and every element (`pilot`, `sync1`, `sync2`, `zero`,
`one`), the shortest and the longest measured half-pulse must lie in **[nominal − 2, nominal + 16] T**. The
docstring's reason: "lengthened at most 16 T by contention (the ULA port's, and a data byte's read in $4000-$7FFF:
the line store starts at $7800), never shortened by more than 2 T."

- This holds for **every** half-pulse, including those that straddle a transition: the last pilot half-pulse, both
  syncs, the first bit, the half-pulse across a byte boundary (where the next byte is fetched, SPACE is tested and
  the checksum is updated), and the last bit before the closing edge. Every code path between two `out`s must take
  the nominal time to within that window. That is the main design constraint on the sender.
- The old routines measured pilot 2,168-2,173 T, sync 667 / 735-740 T, zero 855-867 T, one 1,710-1,718 T (M7.md
  §10). Both round trips confirm it: the line store at $7800-$7FFF is contended.
- The window is measured on **ZEsarUX**, whose TS2068 uses the 48K Spectrum's contention model (M9.md §1, §6). On
  Fuse's TS2068 model, contention is somewhat higher (M9.md §6: +23% against +15% for region-4 code). No test
  checks the sender's widths on Fuse; Fuse's *save* case checks only that its recording loads back.

**The decoder's own limits** (`tapes.py:270` `decode`). A pilot half-pulse must be 1,900-2,500 T, and a block needs
at least 100 of them. The two widths after the pilot are the syncs. Bits are pairs of widths that are both
< 2,500 T, a 1 when the pair's sum is > 2,565 T. A width ≥ 2,500 T after the bits ends the block.

**Pilot counts** (*roundtrip*: `tapetest.py:235`, `[b["pilot"] for b in bl] != [8063, 3222]`). The decoder counts
only half-pulses whose two ends are both recorded level changes. The capture records an edge only where the MIC
level differs from the previously captured `out` (`tapes.py:255` `edges_from_capture`), and the very first captured
`out` always counts.

- So the header block's first half-pulse is counted (8,063).
- The data block's first half-pulse is counted only if its first `out` **changes** the level the header block left.
  With the old routines it does not, so the data block decodes as 3,222 although 3,223 were sent (M7.md §10:
  "data 3,223 (2.0 s)").
- The new sender must send 8,063 / 3,223. To pass *roundtrip* unchanged, the data block's first `out` must also
  leave the MIC level where the previous block's last captured `out` put it. Equivalently: a block begins with a
  write of the line's current level, and every half-pulse then ends with a toggle.
- If the design gives `[8063, 3223]` instead, that is not a signal error. Report it so the owner adjusts the test.
  Stage A's inference from the test is that the old sender started its blocks without an edge; nothing else confirms
  it.

**BREAK in a SAVE** (*save-break*: `tapetest.py:469`, `len(bl) == 1 and len(bl[0]["data"]) <= 2`). SPACE is held
from before the header block starts. The capture must still decode **exactly one block**, with at least 100 pilot
half-pulses, both syncs and at most 2 data bytes, and no data block may follow. Hence R6: no SPACE test during the
pilot or the syncs, a test after each byte (the flag byte included), and an end within the first two bytes.

---

## 3. The hardware and the environment

### 3.1 Port $FE (`PORT_ULA`, `platform/include/hardware.inc:11`: "border/EAR/MIC, keyboard read (Spectrum-compatible)")

| Direction | Bits | Meaning | Source |
|---|---|---|---|
| write | 0-2 | border colour | [FAQ]; `sysvars.inc:1081-1083` |
| write | 3 | **MIC: the tape output**. The test capture reads exactly this bit (`TSTATESP*16+(A&8)`, `lcharness.py` `tape_capture`) | [FAQ]; `sysvars.inc:1082`; `tapes.py` `edges_from_capture` |
| write | 4 | EAR output / speaker on the Spectrum [FAQ]; "unused so far" by Leap-C (`sysvars.inc:1083`) | |
| read | 0-4 | the keyboard half-row selected by the port address's high byte; a key down reads 0 | [FAQ] |
| read | 6 | **EAR: the tape input** | [FAQ: "Bit 6 of IN-Port 0xfe is the EAR input bit"] |
| read | 5, 7 | read as 1 on the 48K Spectrum | [FAQ] |

**SPACE** is bit 0 of the half-row selected by address high byte **$7F** (port $7FFE: SPACE, SYMBOL SHIFT, M, N, B on
bits 0-4) [FAQ]. Leap-C's header logic reads it exactly so (`storage.asm` `STORAGE_LOAD`'s `.space_held`: `ld a,$7f
/ in a,(PORT_ULA) / rra`, carry clear iff SPACE is down). BREAK is CAPS SHIFT + SPACE, and the tape routines test
SPACE alone (spec.md §5.8, "the stock ROM's rule"). The tests press both (`tapetest.py` `hold_break`).

One `in a,(PORT_ULA)` with A = $7F gives EAR (bit 6) and SPACE (bit 0) together, a generic use of the port.

**Feedback.** On the Spectrum, "the EAR and MIC sockets are connected only by resistors, so activating one activates
the other" [FAQ]. The receiver **should not** change bits 3 or 4 while it samples EAR. It need not write port $FE at
all. Border effects while loading are cosmetic and not required; if used, they must not touch bits 3 and 4.

**`PORT_FE_SHADOW`** (`sysvars.inc:1081-1095`) is "the last byte written to port $FE". `GFX_SET_BORDER`
read-modify-writes it instead of writing the port blind, so that the border change keeps the MIC bit; it is the only
record of what is in the port. Requirements:

- **Exit state (both routines):** port $FE's border bits must equal `PORT_FE_SHADOW`'s bits 0-2. Either the port and
  the shadow agree when the routine returns, or the routine writes the shadow's value to the port before it returns
  (a final `out`, which in the sender is one of the ≤ 5, §8.3).
- What happens to the border **during** a block (the shadow's colour throughout, or a pattern) is the implementer's
  choice: no test checks it. The shadow's colour throughout costs nothing and keeps the screen calm.
- The MIC level left on exit is free. A final write that changes MIC after the closing edge is harmless to the
  decoder (§2.6: a width < 2,500 T followed by the inter-block gap ends the bit loop) and to receivers, which know the
  block's length.
- Whatever MIC level is left, `PORT_FE_SHADOW` should match it, or should hold MIC = 0 with the port restored to it.
- The old routine's exit state of port $FE is not known to Stage A.

### 3.2 TS2068 timing facts

- **Clock** 3.528 MHz (`tapes.py:31`). **Frame** 58,688 T at 60 Hz on a TS2068 and on Fuse; ZEsarUX 13.0 uses the 48K
  Spectrum's 69,888 T, 50 Hz (M9.md §1).
- **HOME ROM code is uncontended.** "Both ROM areas are uncontended, so the T-states are those of V2's EXROM copy"
  (M7.md §3). Instruction fetches in the routines therefore cost their nominal T-states.
- **Contended RAM** is $4000-$7FFF: the display files, the system variables at $5B00-$5D59 and the Leap-C cells at
  $5D5A-$5FFF (spec.md §3.1; M9.md §6: "they work in the system variables and cells at $5B00-$5FFF, which are
  contended"), image region 4 at $6000-$77FF and the line store's first 2 KB at $7800-$7FFF (M7.md §10).
  - Delays occur only while the display is drawn, never in the border [FAQ], so their effect on a given pulse varies.
  - A routine that reads a sysvar such as `PORT_FE_SHADOW` or `STORAGE_ENTRY_RETRY` **inside** a timed loop pays
    contention on it. One that reads it before the timed part does not.
  - A payload byte read from (send) or written to (receive) $4000-$7FFF is contended: SAVE's line store starts at
    $7800, and *lib-save* saves 32 bytes of the screen at $4000.
- **I/O contention on port $FE** [FAQ, 48K model]: an even port with an address high byte outside $40-$7F is
  "N:1, C:3", and one with a high byte in $40-$7F (e.g. $7F for the SPACE row) is "C:1, C:3".
  - The ULA must answer every even-port access, so `out (PORT_ULA)` and `in (PORT_ULA)` can be stretched while the
    display is drawn. That is part of the +16 T allowance.
  - Which pattern the TS2068's SCLD really applies is a hardware item (M9.md §6; HARDWARE_CHECKLIST.md §6).
- **The measured window**: −2..+16 T per half-pulse on ZEsarUX (§2.6). The cost of each instruction is the
  designer's problem. The design must stay inside the window with the line store in contended RAM.

### 3.3 Interrupts (R4)

- **Why off:** the IM 1 handler costs about 2,000 T a frame (M7.md §9.3: "ISR per frame idle 2,014 T"). One
  interrupt inside a block would stretch a pulse far outside any tolerance. spec.md §5.8: "While a tape block moves,
  interrupts are off".
- **Who disables:** `STORAGE_SAVE` and `STORAGE_LOAD` start with `di` (`storage.asm`, their first instructions). But every block
  is reached through `TAPE_BLOCK` (`src/rom/home.asm:248`). Its `call BANK_PAGE_EXROM_OUT` **ends with `ei`**
  (`platform/kernel/bank/bank.asm:125-126`; M9.md §12, delta D14: "Every caller gets the same exit state as before:
  interrupts on, from the routine's own `ei`").
  - **So both routines are entered with interrupts enabled, and each must execute `di` itself, first.**
  - An interrupt may arrive between `TAPE_BLOCK`'s page-out and that `di`. That is harmless: the ISR runs from HOME
    and is safe in either paging state (M9.md §12). Its stack use is counted in §3.5.
- **Who re-enables:** `TAPE_BLOCK` after each block (`call BANK_PAGE_EXROM_IN`, `bank.asm:90-91`: `ei`), and at the
  end of the command `SH_TAPE_OFF` (`src/shell/tape.asm:153`; M7.md §11: "The tape routines disable interrupts, and
  `TAPE_BLOCK`'s paging re-enables them between blocks").
  - The routines therefore **need not** re-enable interrupts. They may: `TAPE_BLOCK`'s `ei` follows at once.
- **Fuse's 32 T INT** (spec.md §2.1 D14; M9.md §1): the TS2068's frame interrupt is active for 32 T only, so a frame
  that falls while interrupts are off is lost, not deferred. While a block moves, `FRAMES` does not count (M7.md §6,
  §11). That is accepted behaviour, and no test measures frames across a transfer.

### 3.4 Paging (bank rules)

- The routines live in **HOME** (between `COMP_TAPE_BEGIN` and `COMP_TAPE_END`, `home.asm:283-285`). They run only
  through `TAPE_BLOCK`, with **chunk 6 paged to RAM** (`BANK_EXROM_DEPTH` 0). The data may be anywhere, chunk 6
  included (spec.md §8.3).
- They must **never touch the paging state**: no write to ports $F4 (`PORT_BANK_HOME`) or $FF (`PORT_SCLD`), and no
  change to `PORT_FF_SHADOW` or `BANK_EXROM_DEPTH`.
- **Bank rule 2** (spec.md §2.2): the stack is never in chunk 6. The routines run on their caller's stack (the shell's,
  or a running program's at $F800-$FEFF) and must not move SP elsewhere. `tools/memguard.py` stops the machine if SP
  is ever in $C000-$DFFF, or if either entry label runs with the EXROM paged in (§8.4).
- `IY` is reserved and unused (spec.md §5.1). The alternate set: the library may use `AF'` within a call (spec.md
  §5.1), and `TAPE_BLOCK` and the shell's callers list `AF'` among the destroyed registers. **BC', DE', HL' are listed
  nowhere as destroyed:** the routines must not change them (or must restore them), and must not touch IY.

### 3.5 Stack (R4)

- The deepest caller is `tape_load`'s data block. Counted from its call chain: `LIB_TAPE_LOAD` (`push ix`) →
  `LEAPC_EXROM_TAPE`/`SH_LIBTAPE` → `SH_LOAD_IO` → `STORAGE_LOAD` (`push hl`, `bc`, `ix`; at `.length_ok` `push ix`,
  `de`) → `SH_TAPE_RECV` → `TAPE_BLOCK` → `RT_CALLHL` (`jp (hl)`). At `TAPE_RECV_BLOCK`'s entry that is **24 B** below
  `tape_load`'s first argument, return addresses included. (Stage A's own count from `src/runtime/library.asm`
  1062-1086, `src/shell/tape.asm` 458-501 and 512-557, `storage.asm` `STORAGE_LOAD`, `home.asm` 248-256. Not
  measured separately.)
- **The limit** (*lib-stack*, `tapetest.py:800`): `depth <= 40 + 18` B below the first argument over a whole transfer,
  where 40 B is the library routine's share and 18 B the IM 1 handler's (`include/leapc_layout.inc:53-62`). The old
  routines measured 28 B in all (M7.md §6, §10).
- **So a routine may use at most 34 B below its entry SP** (58 − 24): pushes, calls and anything an interrupt could
  add.
  - Interrupts are off inside the block, so the handler's 18 B count only before the routine's `di`, when the routine
    has pushed nothing.
  - The target is **≤ 16 B**, which leaves room for the header logic to grow.
- The shell's own commands (`SAVE`, `LOAD`, `VERIFY`, `LIB`) run on the shell's stack. No tighter limit is stated
  for them beyond the bank rule and the $F800 floor (memguard, canary).

### 3.6 BREAK and NOBRK

- `tape_save()` / `tape_load()` are a `NOBRK` section (spec.md §5.8; `library.asm:1070-1072`). The ISR cannot see
  BREAK while a block moves anyway (interrupts are off).
- So the routines' own SPACE tests (§4.1, §5.6) are the only way to stop a transfer. The header logic then turns a
  SPACE failure into BREAK (`STORAGE_LOAD`'s `.abort_check`, `SH_LOAD_IO`, `SH_LIBTAPE`: runtime error 5).
- The routines need not, and must not, touch `NOBRK`, `BRKPEND` or `RUNNING`.

---

## 4. The contracts (R5-R9)

The EXROM names `STORAGE_SEND_BLOCK` and `STORAGE_RECEIVE_BLOCK` are the shell's callers of the trampoline
(`src/rom/exrom.asm:92-93`: `SH_TAPE_SEND`, `SH_TAPE_RECV`). The HOME names, exported to the EXROM through
`src/rom/home_exports.txt:93-94`, are **`TAPE_SEND_BLOCK`** and **`TAPE_RECV_BLOCK`**.

`TAPE_BLOCK` passes **A, F (carry and Z), IX and DE** through unchanged in both directions: `push af` / `pop af`
around its paging, `jp (hl)` into the routine (`home.asm:236-256`). `SH_TAPE_RECV` keeps A and F as well
(`push af` / `pop af`, `tape.asm:490-501`).

### 4.1 `TAPE_SEND_BLOCK`

```
; In:  A  = the flag byte (callers: $00 header, $FF data); the pilot is 8,063 half-pulses if A < $80, else 3,223
;      IX = the payload's first byte; DE = the payload's length (callers: 17, or 1..65,535; never 0)
;      interrupts on (TAPE_BLOCK's paging); chunk 6 = RAM
; Out: carry SET   = the block was sent whole (the last SPACE test found SPACE up)
;      carry CLEAR = SPACE stopped it (after the byte during which it was found down)
;      interrupts off or on (TAPE_BLOCK enables them next); port $FE's border bits = PORT_FE_SHADOW's
; Destroys: AF, AF', BC, DE, HL, IX
```

- **Carry out:**
  - the old contract header says "Out: none meaningful" (`storage.asm:250-256`), and `STORAGE_SAVE` ignores it
    (`storage.asm` `STORAGE_SAVE`);
  - but **`SH_TAPE_SEND` depends on it** (`tape.asm:479-489`: `call TAPE_BLOCK / ret c ; sent (carry: the last SPACE
    test found it up)` / else `inc (TAPE_ABORT)`). Carry clear sets `TAPE_ABORT`. The next block (the data block
    after an aborted header) is then not sent, and `SH_SAVE_IO` reports `TR_BREAK` (BREAK, or runtime error 5 for
    `tape_save`);
  - so: **carry set on a complete block, carry clear on SPACE**, as in the box above. A flag-only or other failure
    does not exist for the sender.
- **SPACE (R6):** spec.md §5.8 and M7.md §5 say "the sender after every byte". The sender must test SPACE after each
  complete byte, the flag byte included. If SPACE is down, it stops at once and returns carry clear: no more bits, no
  checksum. It must not test SPACE during the pilot or the syncs, or *save-break* sees no decodable block (§2.6). It
  should still end the block with its closing edge or a final write: either is harmless.
- **DE = 0:** no caller passes it (SAVE refuses an empty source, `tape_save` refuses `len` 0: M7.md §4). If given, the
  sender should send the flag and the checksum only (a well-formed empty block). It must never treat 0 as 65,536.
- **Memory:** read only [IX, IX+DE). Write no RAM except `PORT_FE_SHADOW` (if used as in §3.1) and scratch cells
  that the layout guard accepts (§8.2).

### 4.2 `TAPE_RECV_BLOCK`

```
; In:  A  = the expected flag byte (callers: $00 header, $FF data)
;      carry SET = load (store the payload at IX); carry CLEAR = verify (compare it with the bytes at IX)
;      Z CLEAR (the callers' sentinel, below)
;      IX = the destination (or the bytes to verify against); DE = the expected payload length (callers: 17, or the
;      header's length field, 0..65,535)
;      interrupts on (TAPE_BLOCK's paging); chunk 6 = RAM
; Out: carry CLEAR = success: the flag matched, DE payload bytes were stored (verified) and the checksum is right;
;      DE = 0
;      carry SET = failure: no signal (the search gave up), SPACE, wrong flag, verify mismatch, dropout or checksum;
;      DE = the payload bytes still outstanding (= the entry DE iff nothing was stored at IX)
;      during the transfer and at the return: IX = the next byte's address (entry IX + bytes stored or verified)
;      interrupts off or on; port $FE's border bits = PORT_FE_SHADOW's
; Destroys: AF, AF', BC, DE, HL, IX
```

- **Load vs verify** (carry in; `STORAGE_LOAD` `.data_load_mode` / `scf / ccf` in `storage.asm` `STORAGE_LOAD`):
  - The header search always loads (`scf` at `STORAGE_LOAD`'s `.header_search`). The data block loads, or verifies when
    `STORAGE_VERIFY_MODE` ≠ 0 (shell `VERIFY`, `tape.asm:41-57`).
  - **Verify never writes to IX.** Each received payload byte is compared with the byte at IX. The first mismatch is
    a failure, as soon as it is known or at the end of the block (the implementer's choice). It must be reported, not
    absorbed: "R10.9 ... a VERIFY mismatch [was reported] as VERIFIED" (`storage.asm:392-397`).
  - `STORAGE_LOAD` treats every verify failure as clean (`STORAGE_LOAD`'s `.data_failed`), so DE's value after a
    verify failure is free, but should follow the load rule.
- **The Z sentinel** (`STORAGE_NZ_SENTINEL` = $02, `storage.asm:131-145`). Both of `STORAGE_LOAD`'s calls do
  `ld a, type / cp STORAGE_NZ_SENTINEL / scf (or ccf)`, which leaves **Z clear**. The old receiver read the caller's Z
  to decide whether to check the flag; NZ meant "check".
  - Every caller passes NZ. **The new receiver may ignore Z entirely and always check the flag**, which is
    equivalent.
  - It must not require Z to be set for anything. The header logic's `cp STORAGE_NZ_SENTINEL` lines stay as they are:
    harmless.
- **The flag check comes before any byte is stored.** The first byte after the sync is compared with A. On a mismatch
  the receiver fails at once: carry set, **DE = the entry DE**, nothing written (*lib-load-results*: -1 "nothing
  loaded"; header search: a data block where a header was expected costs one attempt, §4.4). It must not wait for the
  rest of that block: its bits would be measured as a pilot or noise by the next attempt, which is acceptable (§5.2).
- **Storage:** only payload bytes are stored, at IX, IX+1, …, IX+DE−1. The flag and the checksum are **not** stored.
  **Nothing may be written outside [IX, IX+DE)**. `STORAGE_HEADER_BUF` (17 B) is followed directly by
  `STORAGE_REQUEST_TYPE` (`sysvars.inc:1126`, `:1160`), and the data block's destination is followed by the program's
  or the line store's live bytes.
- **IX walks the buffer:** IX must hold the next destination address throughout the payload, and must not be used for
  anything else. `tapetest.py:161` `in_data` samples the IX register every 20,000 instructions during the transfer and
  starts BREAK once `dest + n <= IX < dest + $4000` (*load-fail-keeps-source*, *load-break-direct*, *lib-direct*,
  *lib-fail-keeps*, *lib-break-data*). *lib-break-data* also takes the destination from IX at the data block's
  `TAPE_BLOCK` stop.
  - The required order is that IX advances after a byte is stored. A receiver that stores at (IX) and then increments
    IX satisfies it.
  - A temporary other value of IX in that window would start BREAK at the wrong moment. One outside it would only
    delay it.
- **DE on failure** = the payload bytes not yet stored (the entry DE minus the bytes stored). On success DE = 0
  (`STORAGE_LOAD`'s `.data_ok` reloads the length from the header).
  - **The "touched" logic** depends on DE: `STORAGE_LOAD`'s `.data_failed` compares DE with
    the entry length kept on its stack. Different means destination bytes were written: `STORAGE_LOAD_DATA_TOUCHED`.
    The shell then empties a source received in place (`TR_TOUCHED`, `tape.asm:80-91`), `LIB` unloads the library
    (`tape.asm:243-252`), and `tape_load` returns -2.
  - So a failure **after the first byte was stored** must return DE < entry DE, and one **before** must return DE =
    entry DE.
  - A checksum failure after all bytes arrived returns DE = 0, which is ≠ entry DE (touched, as it must be: *bad
    checksum* cases).
- **DE = 0 on entry:** a forged header with length 0 can reach the data call (`STORAGE_LOAD` `.length_ok` accepts any
  length ≤ the maximum). The receiver must then store nothing and terminate. It should read the flag and the checksum
  byte and succeed iff both are right (the format's empty block). It must never treat 0 as 65,536.
  - M7.md §4 records the old one's behaviour: "ends after the flag byte, never reading the checksum". The shell's
    record check refuses an empty program either way (`SH_CHECK_STORE`), and `tape_load` returns 0.
- **The checksum:** the XOR of the flag and all DE payload bytes, compared with the byte that follows them. That is
  DE + 2 bytes read in all. "The receive loop naturally consumes exactly 17+2 bytes total (block flag + 17 real +
  trailing checksum) on its own from DE=17; no caller-side +1 is needed" (`sysvars.inc:1131-1139`).
  - A mismatch is a failure with carry set ("EVERY failure exit now sets carry", `storage.asm:389-397`).
- **After the last byte** (the checksum) the receiver returns at once. It must not wait for the closing edge, a gap or
  anything after the block (§5.7).

### 4.3 The failure causes and what the callers do with them

The receiver reports all of them the same way: **carry set, DE outstanding**. The callers tell them apart by other
means: SPACE by re-reading the keyboard, "touched" by DE, version and name by the header bytes.

| Cause | Must be detected when | DE | `STORAGE_LOAD` (header search) | `STORAGE_LOAD` (data block) | Shell / library result |
|---|---|---|---|---|---|
| No signal: the search gave up (§4.4) | a call's search budget runs out | entry | the next attempt (`djnz .header_search`, 15 in all) | final failure | `LOAD FAILED` / -1 (*load-not-found*) |
| SPACE down (§5.6) | at any edge wait, silence included | entry, or less once bytes were stored | `.space_held`, then give up at once (`.header_search`) | failure; `.abort_check` sets B ≠ 0 (`.abort_check`) | `BREAK`, kept or emptied by "touched" (`TR_BREAK` / `TR_BREAKT`, `tape.asm:458-470`); runtime error 5 for the library |
| Wrong flag | at the first byte, before storing | entry | the next attempt | final failure, clean | `LOAD FAILED` / -1 |
| Verify mismatch | at a compare | free (clean) | (never: the header search loads) | final failure, clean | `VERIFY FAILED` (*verify-fails*) |
| Dropout: no edge for too long inside the block (§5.5) | at the edge wait that times out | outstanding | the next attempt | final failure; touched if bytes were stored | `LOAD FAILED`, source kept when staged (*load-fail-keeps-source* "dropout", *lib-fail-keeps* "dropout") |
| Truncated block (= a dropout at the end) | as a dropout | outstanding | the next attempt | as a dropout | *load-fail-keeps-source* "truncated" |
| Checksum | after the checksum byte | 0 | the next attempt | final failure, touched | `LOAD FAILED`; direct LOAD empties the source (*load-fail-direct*); -2 (*lib-load-results*); `LIB` unloads (*lib-direct*) |

The SPACE re-read (`.space_held`, port $7FFE bit 0) happens after the receiver returns. The receiver must therefore
return **while SPACE is still held**, within milliseconds of its press. "The receiver samples SPACE thousands of
times a second and a keypress lasts milliseconds, so re-reading it here is reliable" (`storage.asm`, `.abort_check`'s comment). The
tests hold it until the report appears.

### 4.4 The search's bounded retry and the give-up times (R9)

- `STORAGE_LOAD` calls the receiver for the header up to **15 times** (`STORAGE_HEADER_ATTEMPTS_MAX`,
  `storage.asm:147-158`). Every failure costs one attempt, as does a header of another type or name (`.header_rejected`,
  `.name_mismatch`). The data block gets **one** call.
- **Per call:** the old receiver bounds its own search with `STORAGE_ENTRY_RETRY` (a 2-byte sysvar,
  `sysvars.inc:1195-1214`) counting down from `STORAGE_ENTRY_RETRY_MAX` = 2,000. Each attempt in pure silence costs
  "~15000 T-states (~4.3ms), so 2000 gives roughly 8.6 real seconds of pure-silence tolerance per call"
  (`storage.asm:160-186`).
  - That value was chosen against a real user tape with 1.09 s of lead-in silence (same place).
  - Total: "roughly 15 * ~8.6s ≈ 2 minutes" (`storage.asm:147-158`). M7.md §10 measured "gives up after about 129 s of
    emulated silence (15 attempts)". spec.md §8.1, EMULATORS.md §7 and HARDWARE_CHECKLIST.md 7.5 promise "about 2
    minutes".
- **Requirement for the new receiver:**
  - In **pure silence** (no edge at all), a call must give up with carry set after **6-10 s** (target 8.6 s,
    30.3 M T), so that 15 calls take about 2 minutes.
  - With a signal that never forms a valid pilot (noise, or the bits of another file's data block), it must also give
    up within a bounded time: target the same order, at most about 20 s. It must never search forever.
  - How it counts (time, edges, attempts) is free. `STORAGE_ENTRY_RETRY` stays available as a 2-byte work cell, and no
    caller reads it. A new constant may replace `STORAGE_ENTRY_RETRY_MAX`.
- **Why not shorter:**
  - the data block's single call must survive the gap before the data pilot. Stock tapes and `tools/tapes.py`'s `tzx()`
    have 1 s pauses, synthesised tapes 0.5 s;
  - the header search must survive lead-in silence (the harness plays 1.0-1.5 s of idle before a tape: `write_rwa(...,
    lead=1.5)`) and gaps between files (*lib-any-replace*: 4.0 s of silence between two files; `hwkit.py --verify` H11:
    3 s between the library's WAV and the program's).
  - The outer 15 attempts cover the header search's silence anyway. The data call's tolerance is what the per-call
    budget really protects.
- **Why bounded:** *load-not-found* (a tape whose only file is of another type, then silence) must end in `LOAD FAILED`
  within the case's budget (600 M instructions) and with the source intact. TS2068 BASIC's stock loader waits forever;
  Leap-C must not.
- **SPACE ends the search at once** (§5.6). *load-break-search* and *lib-fail-keeps* run 200,000 instructions of
  silence, then hold BREAK: the report must be `BREAK` with nothing changed. *tests/lib/tape/load_break.c* does the
  same from a running program: runtime error 5 at the caller's line, within the default 20 M-instruction run budget.

### 4.5 System variables and cells

| Name | Use by the routines | Source |
|---|---|---|
| `PORT_FE_SHADOW` | read (the border bits to keep); may be written (§3.1) | `sysvars.inc:1081-1098` |
| `STORAGE_ENTRY_RETRY` (2 B) | free work cell for the search's bound (§4.4); no caller reads it | `sysvars.inc:1195-1214` |
| `STORAGE_CHECKSUM` (1 B) | **must not be used**: `STORAGE_LOAD` keeps the header search's remaining attempt count there across the receiver's calls (`STORAGE_LOAD`'s `.header_found`) | `sysvars.inc:1119-1125` |
| `STORAGE_SEND_LEN` (2 B) | must not be used: `STORAGE_SAVE`'s scratch while it builds the header (it is consumed before the first block, but nothing promises that) | `sysvars.inc:1111-1118` |
| `STORAGE_HEADER_BUF`, `STORAGE_MAX_LEN`, `STORAGE_VERIFY_MODE`, `STORAGE_OP_STATE`, `STORAGE_PROGRESS_*`, `TAPE_*` | the header logic's; never touched by the block routines (except through IX as a destination) | `sysvars.inc`, `include/leapc_cells.inc:189-195` |

Any new work cell must be a declared system variable or Leap-C cell. The layout guard fails the build on any other RAM
address (§8.2).

---

## 5. The receiver's required behaviour (R7, R10, R11)

This section states what the receiver must accept, reject and distinguish. It does not prescribe how. The thresholds
are the implementer's.

### 5.1 Edges and polarity

- The receiver reads EAR (port $FE bit 6) and reacts to its **changes**. Every measurement is the time between two
  consecutive edges, whichever direction they go.
- **Both polarities must work.** A block whose pilot starts on either level, and whose sync therefore starts on either
  level, must load [WIKI; TZX].
- One missing or one extra pilot half-pulse changes the parity of the edges before the sync. It must make no
  difference (§6).

### 5.2 What counts as a pilot

- **A pilot** is a run of consecutive half-pulses whose widths are consistent with 2,168 T under the envelope of §6.
  The receiver must not accept a block until it has seen a sustained run of them.
- **How long a run must be accepted from (R10):** the synthesised tapes use **3,223 half-pulses (2.0 s) for both
  blocks** (`tapetest.py:42` `PILOT = tapes.DATA_PILOT`; the note: "2 s: the receiver waits 1 s, then counts 256
  cycles"; M7.md §9.2: "Their pilots are at least the data block's stock 3,223 pulses ... so shorter pilots time
  out"). The stock data pilot is the shortest pilot the suite uses. Required and targets:
  - **must** lock onto a pilot of ≥ 3,223 half-pulses whose start it sees;
  - **must** lock when called after part of the pilot has already passed. Between the header block and the data
    block, `STORAGE_LOAD` checks the header and runs the progress hook, which draws the status row (`SH_TAPE_HOOK`).
    Leap-C's own SAVE leaves only its own hook's time between the two blocks (`STORAGE_SAVE`),
    so in the round trips the data pilot is already playing when the receiver is called. Requirement: lock on a
    3,223-pulse pilot even when the call comes up to 0.5 s after the pilot started;
  - **should** lock within about 1,000 half-pulses (0.6 s) of the pilot's first edge (it then accepts a call up to
    about 1.4 s into a data pilot). The old receiver needed about 1 s plus 256 cycles (the note above).
- **Must not be fooled by data:**
  - A 1 bit's half-pulse (1,710 T) is only 21% shorter than a pilot half-pulse, and the envelope (−25%) puts a fast
    tape's pilot below a nominal 1 bit. A run of $FF bytes in a data block therefore looks like a pilot of 16
    half-pulses a byte.
  - A receiver searching for a header may meet the middle of another file's data block (*load-named*,
    *lib-load-results*, *lib-any-replace*, *lib-keep-unload*: several files on one tape, the header search running
    while a data block plays).
  - It **must** require enough consecutive pilot-like half-pulses that ordinary data does not qualify. At least 256 is
    suggested: 16 bytes of $FF.
  - Should a long $FF run still qualify, the result must be a failure (wrong flag or checksum), never a wrong success.
    Each such failure costs one of 15 attempts. The false-success odds are those of the flag (1/256) and the checksum
    (1/256) together, and the header logic's own checks (type, name, version) come on top.

### 5.3 The sync

- After the pilot, the **first half-pulse clearly shorter than the pilot** is the first sync (667 T), followed by the
  second (735 T).
- The receiver must distinguish **sync from pilot** under the whole envelope. A sync at +25% is 834 / 919 T, a pilot at
  −25% is 1,626 T, plus the jitter of §6.
- It must not require the two sync half-pulses to differ from each other, nor from a 0 bit's half-pulse.
- After the sync, the next edge starts the flag byte's first bit.
- A sync-like short half-pulse **inside** the pilot (a glitch, §6) should restart the pilot search rather than start a
  block. A block that started on a glitch fails at the flag or the checksum, which is acceptable but costs an attempt.

### 5.4 Bits

- Each bit is two half-pulses of equal nominal width: 855 T (0) or 1,710 T (1). The receiver measures them and
  decides **0 vs 1**, eight bits a byte, most significant first.
- What must be distinguished: 0 from 1 under the whole envelope (§6). The feasibility note in §6.2 shows the margins
  for deciding on one half-pulse, on the full bit, or adaptively.
- An edge that comes far too late is a dropout (§5.5). One far too early (e.g. a glitch) may be treated as noise or as
  a failure. It must never be silently accepted as a valid byte without the checksum catching it: the XOR check does
  that, so no extra check is required.

### 5.5 Dropout

- **A dropout** is no edge for longer than any legitimate half-pulse allows. The longest one inside a block is a 1 bit
  at +25% plus jitter: about 2,140 + 224 ≈ 2,400 T. The receiver must end the block **as a failure** (carry set, DE
  outstanding) when no edge comes within its dropout limit.
- The limit is the implementer's. It must be above about 3,000 T (no false dropouts under the envelope) and should be
  below about 20,000 T. The synthesised dropouts are whole bytes of flat signal: *load-fail-keeps-source* `dropout=(20,
  4)` and *lib-fail-keeps* `dropout=(30, 4)`, four payload bytes, at least 4 × 8 × 1,710 = 54,720 T. A truncated block
  (`truncate_after=30`) ends in 0.5 s of silence.
- **Inside the pilot**, a short dropout must not cause a failure (§6, target). After it the receiver may resume the
  pilot or restart its search, provided enough pilot remains to lock (§5.2).
- The search's own silence (before any pilot) is not a dropout: it is bounded by §4.4.

### 5.6 SPACE (R7)

- **SPACE must be tested at every edge wait**, including the waits in pure silence during the search, and stop the
  block at once with carry set (spec.md §5.8: "the routines themselves test SPACE ... at every edge"; M7.md §5: "The
  receiver tests SPACE at every edge"). "At every edge wait" means: no wait for an edge, however long, may go without
  testing SPACE.
- One `in` from port $7FFE gives EAR and SPACE together (§3.1). A separate SPACE read is allowed but counts as a port
  read for Fuse's loader detection (§5.8).
- On SPACE the receiver returns DE as §4.2 says, so `STORAGE_LOAD` can tell `TR_BREAK` from `TR_BREAKT`
  (*load-fail-keeps-source* "break in data", *load-break-direct*, *lib-direct*, *lib-fail-keeps*, *lib-break-data*).

### 5.7 Trailing pulses and the gap after the block

- After the checksum byte's last bit the receiver returns at once (§4.2). The closing edge, any trailing pulse (the
  synthesised tapes' extra 855 T half-pulse), the pause and the next block's pilot are not its business.
- The **next** call (the data block after a header, or the next header attempt) begins in whatever follows: the end of
  the closing pulse, a gap, or the next pilot already playing. It must find the next pilot from there.
- In particular, a lone trailing edge followed by silence must not count as the start of a pilot.

### 5.8 Fuse's loader detection (R11, hard requirement)

Leap-C's Fuse suites never press PLAY: `tools/fusetest.py` *save*, *wav*, *lib*, *corpus* and `tools/hwkit.py
--verify` open the tape and type `LOAD ""` or `LIB "…"` ("Fuse starts the tape itself": M11-beta.md §4;
EMULATORS.md §2 "Detect loaders: on (default)"). Fuse runs with `--no-traps --no-auto-load`
(`tools/fusedrive.py:156-158`) and its other settings at their defaults. Detect loaders, fastloading and accelerate
loaders are all on (EMULATORS.md §2).

**How Fuse 1.9.1 decides** [FUSE-LD], with `detect_loader` = 1, the default:

- Fuse watches every read of the ULA port: any `in` whose port address has A0 = 0, keyboard reads included. For each
  such read it computes **dt** = T-states since the previous such read, and **db** = (B register now) − (B at the
  previous read), mod 256.
- **Tape stopped:** a read with dt ≤ 500 and db = +1 or −1 increments a counter, and any other read resets it. At 10
  successive such reads Fuse presses PLAY.
- **Tape playing:** a read with dt > 1,000, or db not in {0, +1, −1}, increments a counter, and a good read resets it.
  At **2 successive** bad reads Fuse presses STOP.

**So the receiver must:**

1. **While searching** (silence or signal), read the port with **B changing by exactly ±1 from one port read to the
   next**, the reads at most 500 T apart. Ten such reads in a row must occur soon after the call starts, so that Fuse
   starts the tape. A loop that waits for an edge with B as its counter, decremented or incremented once per `in`,
   does this.
   - Any port read between them with B unchanged, a separate keyboard read for instance, resets Fuse's start count.
     It must not occur often enough to keep the count below 10.
2. **Once the signal flows** (pilot, sync, bits, between bytes, at the flag check, storing, verifying, at the checksum
   and during any search restart), **never make two successive bad reads**. A bad read is one more than 1,000 T after
   the previous read, or one with B moved by other than 0 or ±1.
   - Reloading B (a new timing count at each edge or byte) is one bad read. The very next read must then be good:
     ≤ 1,000 T later, B moved by 0 or ±1.
   - A long computation between two reads (> 1,000 T) is one bad read. The read after it must be good.
3. Keep the same discipline between the header block and the data block, as far as the routines can: the header
   logic and the hook run in between, with interrupts on. The ISR's keyboard scan reads the port too.
   - Fuse may stop the tape there and start it again when the data call begins its search (rule 1). The old routines
     pass every Fuse case this way.
   - The receiver must lock onto a data pilot that resumes after such a short stop (§5.2).

**Fuse's "accelerate loaders"** (default on) recognises some loaders' code and runs their edge loops in one step. It
may or may not recognise the new code. **Correctness must not depend on it either way:** the routines must work with
acceleration on (the tests' setting, which may or may not engage) and off.

ZEsarUX's real-tape input needs no detection: the tape plays from the insert on, in emulated time
(`lcharness.py` `tape_insert`).

---

## 6. Tolerance (R10)

### 6.1 What the receiver must accept (the inputs the tests use)

| Input | Source of the signal | Effect on widths | Tests |
|---|---|---|---|
| ZEsarUX real-tape input, `.rwa` | `Tape.to_rwa`: point-sampled **one sample per 224 T** (a scan line, `tapes.py:32` `SAMPLE_T`); levels $C8 / $38, idle $80 | each edge moves to a 224 T boundary: every width is the nominal **±224 T** (855 → 672 or 896, 1,710 → 1,568 or 1,792, 667 → 448 or 672, 735 → 672 or 896, 2,168 → 2,016 or 2,240) | every *tapetest* case |
| A captured SAVE played back | `Tape.from_edges` → `.rwa` | the sender's widths (−2..+16 T), then the ±224 T sampling | *roundtrip*, *roundtrip-large*, *lib-roundtrip*, *cross-version* (V2's SAVE) |
| `.tap` / `.tzx` through ZEsarUX's own conversion | `c2tape.py`, `tapes.tzx()` (standard speed blocks, 1 s pauses) | stock widths and pilots; ZEsarUX's sampling | *host-tape*, *lib-load* (lib2tape's `.tap` blocks, short pilots) |
| TZX direct recording on ZEsarUX | V2's `SHAPES` package (`Tape.from_tzx_direct`: V2 "synthesised its pulses from 80-T samples") | ±80 T, then ±224 T | *lib-cross-version* |
| WAV, 44.1 kHz | `Tape.to_wav`: 8-bit, point-sampled at 3.528 MHz (one sample = 80 T) | ±80 T | `hwkit.py --verify` (ZEsarUX via `rwa_from_wav`: then also ±224 T) |
| Fuse, TZX direct recording | `tzx_from_wav`: **80 T a sample** (`round(3528000/44100)`) | ±80 T | *wav*, *lib* (testlib's WAV), `hwkit.py --verify` |
| Fuse, standard speed TZX | `c2tape`, `lib2tape` | stock widths, Fuse's tape timing | *corpus* (780 programs), *lib* (`shapes.tzx`) |
| Fuse, its own recording of SAVE | Fuse's recorder (a direct recording) | the sender's widths, Fuse's recording resolution | *save* |
| Real tape (not tested) | a cassette or a phone into EAR | wow and flutter, level, phase | HARDWARE_CHECKLIST.md §7 |

All of these must load. The ±224 T quantisation of ZEsarUX, the coarsest, sets the minimum jitter tolerance:
**every half-pulse may arrive up to 224 T early or late**, independently. A pair of half-pulses keeps its sum within
±224 T, because both share the middle edge.

### 6.2 Target envelope (should; the owner will compare it with the old receiver's, §10)

The receiver should load correctly under each of these, applied to a standard block:

| Perturbation | Target |
|---|---|
| **Speed:** every width scaled by the same factor | −25% … +25% (a tape running 25% fast … 25% slow) |
| **Jitter:** each half-pulse independently moved | ±80 T at any speed in the range; ±224 T (ZEsarUX) at least within −15% … +15% |
| **Pilot parity:** one pilot half-pulse missing, or one extra | no effect |
| **Pilot dropout:** a flat stretch inside the pilot | up to 50 ms anywhere in the first half of a 3,223-pulse pilot: no failure |
| **Lead-in / gaps** | as §4.4 |

**Feasibility note** (arithmetic from the widths, not a design). The worst cases decide what must be distinguished.

| Decision | Nominal | At +25% (+ jitter) | At −25% (− jitter) | Margin |
|---|---|---|---|---|
| 0 / 1 on **one half-pulse** | 855 / 1,710 | 0: 1,069 (+80 → 1,149) | 1: 1,282 (−80 → 1,202) | 53 T at ±80, none at ±224 |
| 0 / 1 on **the bit** (two halves) | 1,710 / 3,420 | 0: 2,138 (+80 → 2,218) | 1: 2,565 (−80 → 2,485) | 267 T at ±80; at ±15%: 1,967 + 224 = 2,191 vs 2,907 − 224 = 2,683 |
| sync / pilot | 667-735 / 2,168 | sync 919 (+224 → 1,143) | pilot 1,626 (−224 → 1,402) | wide |
| pilot / 1 bit (one half) | 2,168 / 1,710 | — | pilot 1,626 < a nominal 1 bit | **not separable by width** at −25%: §5.2's run-length rule is the guard |
| dropout / longest pulse | — | 1 bit 2,138 (+224 → 2,362); pilot 2,710 (+224 → 2,934) | — | limit > ~3,000 T |

- With a fixed threshold, the speed and jitter targets can be met together only by deciding on the full bit (both
  halves), or by adapting the thresholds to the measured pilot period.
- Deciding on one half-pulse with fixed thresholds meets ZEsarUX's ±224 T at nominal speed. It cannot meet ±25% with
  any jitter.
- The choice is the implementer's. The required minimum is §6.1 (all current inputs) at nominal speed. A design that
  meets less than the target table must say what it meets.

---

## 7. Mutual readability (R12)

At the signal level, these must keep reading each other's tapes. Accepting or refusing the content is the header
logic's business (version word, type, name) and is unchanged.

| Writer → reader | Requirement | How it is shown |
|---|---|---|
| Leap-C SAVE → Leap-C LOAD | must | *roundtrip*, *roundtrip-large*, *lib-roundtrip*; Fuse *save* |
| Leap-C SAVE → V2's ROM (a stock-derived receiver) | must: V2 receives the header and refuses it with `BAD TAPE VERSION` | *cross-version* |
| V2's SAVE → Leap-C LOAD | must: Leap-C receives V2's header and refuses it | *cross-version* |
| V2's package tape (80-T direct recording) → Leap-C `LIB` | must: received, refused by version | *lib-cross-version* |
| Stock-format files (`.tap` / `.tzx` standard blocks, 8,063 / 3,223 pilots, 1 s pauses) → Leap-C | must | *host-tape*, Fuse *corpus*, *lib* |
| Leap-C SAVE → a stock TS2068 or Spectrum | must at the signal level: the stock loader reads the blocks. Untested on hardware (HARDWARE_CHECKLIST.md 7.4 is the reverse direction) | follows from R1-R2: the sender emits the format's nominal widths within −2..+16 T |
| A stock TS2068 or Spectrum tape → Leap-C | must at the signal level (refused by version: `BAD TAPE VERSION`, *load-refused* synthesises such headers) | follows from R10; a 3.5 MHz Spectrum's pulses are 0.8% long (§2.5) |

The sender meets its side by emitting **exactly** the nominal widths (R2); no stock receiver's tolerance needs to be
known. The receiver meets its side by §5-§6.

---

## 8. Constraints on the code (R13)

### 8.1 Assembly and style

- **sjasmplus 1.23.1** through `tools/sjasm_strict.sh` (`--msg=war --inc=. --inc=platform`): any warning is an error.
- **HOME**, between `COMP_TAPE_BEGIN` and `COMP_TAPE_END` (`budget.toml` component `tape_block`, `ranges =
  [["COMP_TAPE_BEGIN", "COMP_TAPE_END"]]`). The labels **`TAPE_SEND_BLOCK`** and **`TAPE_RECV_BLOCK`** are the entry
  points, the send routine at the lower address. `src/rom/home_exports.txt:93-94` exports them to the EXROM by these
  names. The old `EQU`s (`home.asm:286-287`) go when the new labels exist.
- **Style** (as `src/runtime/*.asm`): a file header in a `; ===` banner (path, purpose, spec.md sections); each routine
  under its own `; ===` banner with `In:`, `Out:`, `Destroys:` lines, plain technical English, comments that explain
  timing; constants as `EQU`s with their source (this document's sections). Use `PORT_ULA` and the sysvar names, never
  literals for them.
- **Budget:**
  - The `tape_block` budget is 340 B, but ledger L38 returned 9 B to the reserve when the old pair measured 331 B
    (`budget.toml:620-631`). **The effective budget is 331 B**: the target for both routines together (the old pair:
    send 127 B, receive 204 B).
  - Up to 340 B needs a ledger entry taking the 9 B back from the HOME reserve.
  - The HOME **reserve floor** is 384 B (spec.md §2.2: ledger L73; `budget.toml` `reserve_floor = 512` with L73's
    −128). The reserve after Phase 10 was 455 B. Any growth beyond 340 B draws on that reserve and needs the owner.
  - `make check` enforces all of this.
- **The test image:** `make check` requires the test image to equal the production image up to
  `LEAPC_HOME_CODE_END` (`tools/check_test_image.py`). The routines must assemble identically with and without
  `-DLEAPC_TEST`: no test-only conditionals inside them.

### 8.2 RAM references (the layout guard)

`make check`'s `tools/check_ram_layout.py` fails the build on any RAM address the HOME code references that is not a
system variable, a Leap-C cell, a display-file-1 constant, a platform cell, a region boundary or an EXROM label
(spec.md §3.1, "The layout guard"). The routines may reference `PORT_FE_SHADOW`, `STORAGE_ENTRY_RETRY` and any newly
declared cell, and nothing else in RAM except through IX.

### 8.3 The test harness's MIC capture

`lcharness.Machine.tape_capture` (`tools/lcharness.py` 340-363) scans the bytes from `TAPE_SEND_BLOCK`'s address up to
`TAPE_RECV_BLOCK`'s address for the pair **`D3 FE`**, the encoding of `out (PORT_ULA), a`. It puts a ZEsarUX
breakpoint on each, slots 14-18 (`TAPE_SLOTS`, 5 slots). Each breakpoint prints `TSTATESP*16+(A&8)` without stopping:
the T-state at the instruction's start and MIC from **bit 3 of A**. The layout must respect that:

1. **Every write of MIC by the sender is `out (PORT_ULA), a`** (`D3 FE`), with the level in bit 3 of A. `out (c), r`
   is invisible to the capture.
2. **All of them lie between `TAPE_SEND_BLOCK` and `TAPE_RECV_BLOCK`**: send first, nothing that writes MIC placed
   after the receive label (a shared exit, for example).
3. **At most 5** such instructions (the slots). The bytes `D3 FE` must not occur in that range other than as those
   instructions, e.g. as an operand followed by a `$FE` operand. An accidental pair takes a slot and breaks the
   count.
4. As read during Stage A (commit `6201aa2`), the harness asserted **exactly 5**
   (`assert len(outs) == len(TAPE_SLOTS)`) and looked up `STORAGE_SEND_BLOCK` / `STORAGE_RECEIVE_BLOCK`. In the
   working tree at the end of Stage A, it already used `TAPE_SEND_BLOCK` / `TAPE_RECV_BLOCK` and accepted 1 to 5
   (`assert 1 <= len(outs) <= len(TAPE_SLOTS)`, `lcharness.py:346-349`). Stage B should check which applies.
5. Every one of those `out`s must be a real instruction start (the breakpoint is `PC=addr`), and every MIC change must
   pass through one. An `out` that rewrites the same level is harmless: the capture records only changes.

The receiver may use `out (PORT_ULA), a` freely (outside the scanned range), subject to §3.1's feedback caution.

### 8.4 memguard's entry checks

`tools/memguard.py` arms, through every transfer of the cassette suite and the corpus, "a tape block sent / received
with the EXROM paged in": `PC=<entry> and PEEK(BANK_EXROM_DEPTH)<>0`, on the two entry labels (`memguard.py:44-46`,
renamed to `TAPE_SEND_BLOCK` / `TAPE_RECV_BLOCK` in the working tree). It also arms the stack-in-chunk-6 and
chunk-6-write checks.

- The entry labels must be the routines' **first instructions**, entered only through `TAPE_BLOCK`.
- The routines may jump back to their own entry label: the depth is 0 then, so nothing fires.
- They must not write chunk 6 except as a load destination, with the EXROM paged out, which it always is in a block.

### 8.5 The fake-I/O test hooks

`STORAGE_SAVE` has `IFDEF STORAGE_TEST_FAKE_SEND` → `call STORAGE_TEST_SEND_BLOCK` (`storage.asm` `STORAGE_SAVE`), and the
old receive routine had an `IFDEF STORAGE_TEST_FAKE_RECEIVE` jump at its top. A search of every `.asm`, `.inc`,
`.py`, `.toml`, `.sh` and the Makefile found **no build that defines either symbol** and no `STORAGE_TEST_*_BLOCK`
routine. They are dormant, and the new routines need not provide them. `STORAGE_SAVE`'s conditional stays harmless.

### 8.6 Integration (for the owner)

- Replacing the vendored routines changes `platform/kernel/storage/storage.asm`. That is a platform delta, so
  `tools/check_platform.py`, `platform/deltas/` and `platform/MANIFEST` change with it.
- `NOTICE` §3 and M11-beta.md A8 lose the exception for the tape routines.
- `budget.toml`'s titles and L38, spec.md §2.1 (delta D9), §2.2, §8.3 and the harness's docstrings
  (`tapetest.py`, `tapes.py`, `memguard.py`) name the old routines and must be updated.

---

## 9. Tests: what exercises each requirement

The commands: `make test` (includes `tools/tapetest.py`, suite `tape`, and the corpus with `tests/lib/tape/`),
`python3 tools/tapetest.py [substring ...]` (single cases), `make fuse` (`tools/fusetest.py`), `python3
tools/hwkit.py --verify`, `make check` (budgets, layout guard, test image), `make qualify` (all of it).

| Requirement | Tests |
|---|---|
| R1 signal, pilots, bytes, checksum, closing edge | *roundtrip* (blocks equal `tapes.file_blocks`, `ok`, pilots `[8063, 3222]`), *roundtrip-large* (8 KB), *save-typed-matrix*, *host-tape* (ROM SAVE = `c2tape` blocks), *lib-save* (4 blocks from chunk 6 and the screen), *lib-roundtrip*, *cross-version* (V2 reads Leap-C's SAVE) |
| R2 widths −2..+16 T | `widths_ok` in *roundtrip*, *roundtrip-large*; *roundtrip*'s `extra` prints the spans |
| R3 MIC via `out (PORT_ULA), a`, ≤ 5, layout | every capture: *roundtrip*, *roundtrip-large*, *save-break*, *save-typed-matrix*, *host-tape*, *cross-version*, *lib-save*, *lib-roundtrip* (the harness asserts the count) |
| R4 interrupts, paging, stack | memguard invariants in every armed case (`command`, `command_to`, `lib_run`); *lib-stack* (≤ 58 B); `tests/lib/tape/save_chunk6.c` (`cell: BANK_EXROM_DEPTH 0`, `NOBRK 0`); the corpus canary |
| R5 contracts: carry, DE, IX, verify, nothing outside the buffer | *load-named*, *load-staged-ok*, *verify-fails* (one character, one line more, one less), *load-fail-keeps-source*, *load-fail-direct*, *load-break-direct*, *lib-load-places* (chunk 6, $E000, heap), *lib-load-results* (-1, -2, -3, length), *lib-direct*, *lib-fail-keeps*, *lib-load*; shell `state()` compared before and after |
| R6 sender SPACE, carry out | *save-break*; `tests/lib/tape/save_break.c` (runtime error 5, no data block) |
| R7 receiver SPACE | *load-break-search*, *load-fail-keeps-source* (break in data), *load-break-direct*, *lib-break-data*, *lib-direct* (break), *lib-fail-keeps* (break in data, break in search); `tests/lib/tape/load_break.c` |
| R8 failure causes | wrong flag: *load-named*, *lib-load-results*, *lib-any-replace* (headers vs data blocks); checksum: *load-fail-keeps-source*, *load-fail-direct*, *lib-load-results*, *lib-direct*, *lib-fail-keeps*; dropout: *load-fail-keeps-source*, *lib-fail-keeps*; truncation: *load-fail-keeps-source*; verify: *verify-fails* |
| R9 give-up | *load-not-found* (15 attempts, `LOAD FAILED`; its `extra` gives the wall time); M7.md §10's 129 s |
| R10 acceptance and tolerance | every ZEsarUX case (224 T sampling); *lib-cross-version* (80-T direct recording); `hwkit.py --verify` (WAVs on both emulators); Fuse *wav*, *lib*, *corpus*; the §6.2 envelope has no test yet (§10) |
| R11 Fuse loader detection | `make fuse`: *save*, *wav*, *lib*, *corpus*; `hwkit.py --verify` (Fuse half). A failure shows as a LOAD that never starts or stops mid-block (`LOAD FAILED` after the timeout) |
| R12 readability | *cross-version*, *lib-cross-version*, *host-tape*, Fuse *corpus* |
| R13 size, assembly, layout | `make check` (strict assembly, `budget.py`, `check_ram_layout.py`, `check_test_image.py`), `make budget` |

Corpus cases about tapes (`tests/lib/tape/`): `save_break.c`, `load_break.c`, `save_chunk6.c` exercise the block
routines. `save_noname.c`, `save_longname.c`, `save_nobytes.c` and `load_longname.c` are header-logic refusals that
never reach a block. `tests/doc/examples_24.c` uses `tape_save` / `tape_load`.

---

## 10. Measured envelope of the beta.1 receiver

*Appended by the orchestrator (Phase 11, M11-tape), measured black-box: `tools/tapetol.py` on the beta.1 images
(HOME `ba8e0ab6…`, EXROM `9bd71cef…`). Each case is a program tape (header and data block, the stock pilots, 1 s of
silence before and between the blocks) with one distortion, written as a TZX direct recording at 4 T a sample and
LOADed by `LOAD ""` on Fuse 1.9.1 (its loader detection on, its loader acceleration off). "Jitter J" multiplies
every half-pulse by an independent uniform 1 ± J (seed 1). A refused case reported LOAD FAILED.*

| Perturbation | beta.1 receiver |
|---|---|
| speed, every width × (1 + S), S = −25 … +25 % in 5 % steps | accepts −20 … +25 %; **refuses −25 %** |
| only the pilot scaled, −25 … +25 % | accepts all |
| only the syncs scaled, −25 … +25 % | accepts all |
| only the bit pulses scaled, −25 … +25 % | accepts −20 … +25 %; **refuses −25 %** |
| jitter 5, 10, 15, 20, 25, 30 % | accepts up to 25 %; **refuses 30 %** |
| speed −20 / −10 / +10 / +20 % with jitter 10 % | accepts −10, +10, +20 %; **refuses −20 %** |
| bit skew (first half × (1 + K), second × (1 − K)), K = 10, 20, 30 % | accepts all |
| pilot length 2,000 / 1,500 / 1,000 / 800 / 600 / 400 pulses (both blocks) | **refuses all** (the stock 3,223 is accepted) |
| one pilot edge missing in the middle of each pilot | accepts |
| one pilot edge missing 4 pulses before the sync | **refuses** |
| one extra pilot pulse (sync and data inverted) | accepts |
| the whole signal inverted | accepts |
| a dropout of 2 / 10 / 50 / 200 ms in the middle of each pilot | accepts 2 ms; **refuses 10, 50, 200 ms** |
| a dropout of 1 / 5 / 20 ms in the data block | refuses all (as it must) |

54 of the 71 cases are accepted. The new receiver must accept at least these 54 (the comparison is
`tools/tapetol.py --build <beta.1 images> --build build`); it may accept more (§6.2's targets are wider in places:
−25 % speed, a 50 ms pilot dropout). The give-up times are §4.4's.

---

## 11. Provenance and open points

**Read for this document:**

- **Public format descriptions:** [TZX], [WIKI], [FAQ]; [FUSE-LD] as the orchestrator described it.
- **Leap-C:** spec.md §1-§3, §5.1, §5.8, §8, §11; `project_plan.md`; `NOTICE`; docs/milestones M7, M9, M10,
  M11-beta; docs/EMULATORS.md; docs/HARDWARE_CHECKLIST.md; `platform/kernel/storage/storage.asm` lines 107-187,
  236-257, 372-401 and 599-1062 only (as committed in `6201aa2`); `src/shell/tape.asm`; `src/rom/home.asm`;
  `src/rom/exrom.asm`; `src/runtime/library.asm` (its tape part); `platform/include/sysvars.inc` and `hardware.inc`;
  `platform/kernel/bank/bank.asm`; `include/leapc_layout.inc`; `budget.toml`; `tools/tapetest.py`, `tapes.py`,
  `lcharness.py`, `memguard.py`, `fusetest.py`, `fusedrive.py`, `hwkit.py`, `exectest.py`, `sjasm_strict.sh`;
  `tests/lib/tape/`.

**Not confirmed from the allowed inputs:**

1. The data block's decoded pilot of 3,222 (§2.6) is inferred from the capture model, not from the old code.
2. The old routines' exit state of port $FE and `PORT_FE_SHADOW` (§3.1) is unknown. The requirement given is the one
   the shadow's contract implies.
3. Which bit Fuse's recorder takes as MIC. The capture and the old routines use bit 3, and Fuse's *save* case passes
   with them.
4. The stack count of §3.5 is Stage A's own count from the callers' code, not a measurement of the old routine's share.
5. The TS2068 SCLD's I/O contention pattern (§3.2) is the 48K Spectrum's per [FAQ]. M9.md leaves the real one to
   hardware.
6. The working tree changed while Stage A read it: `storage.asm`, `home.asm`, `lcharness.py`, `memguard.py` and
   others were being modified by someone else. Line numbers for `storage.asm`, `home.asm` and `lcharness.py`/`memguard.py`
   (where marked) refer to commit `6201aa2` as first read; the old routines' names, `EQU`s and the trampoline may have
   moved since. §8.3 and §8.4 give both states of the harness.
