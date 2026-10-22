# Phase 11, second milestone — The tape block routines rewritten clean-room; 1.0.0-beta.2: milestone report

**Date:** 2026-10-22. **Status: complete up to the owner's steps.** Leap-C's ROM images no longer contain code derived
from the TS2068 / Spectrum ROM: the cassette block routines and the block-graphics glyph were rewritten clean-room, and
release v1.0.0-beta.2 is prepared as a draft pre-release. The owner publishes it.

- **Baseline:** M11-beta (`6201aa2`, tag v1.0.0-beta.1), `spec.md` v0.12, ROMs HOME `ba8e0ab6…`, EXROM `9bd71cef…`.
- **Approval:** the owner's option C (M11-beta §2, A8; `project_plan.md` §13): rewrite `STORAGE_SEND_BLOCK` and
  `STORAGE_RECEIVE_BLOCK` (V2's port of the stock SA-BYTES / LD-BYTES) and the block-graphics quarter generator (the
  stock PO-GR-2 sequence) from the specification alone, keep every contract and behaviour, then `NOTICE` loses its
  exception.
- **Result:** ROMs HOME `043becf4b2e58e9783ef83b8188648214ed6a84e83a13709458439385df5fba5`, EXROM
  `97fe95236ff16b7ccb1c5e138d228d67ca25bf31d7b86bdbd15995c85ac207e7`, combined
  `9cc679793a1f855f7ddcc2d99113e2730bd45c37e7204ea91df0d8f8e4b5af04` (`.dck` `cd34fdd1…`). `spec.md` v0.13.

## 1. Completion criteria

| Criterion (the approval) | Result | Evidence |
|---|---|---|
| Stage A: a specification from public format descriptions, Leap-C's documents and the contracts only | **done**: `docs/TAPE_SIGNAL_SPEC.md` | §2, `docs/TAPE_CLEANROOM.md` |
| Stage B: the routines by a fresh author with only the specification; the glyph from the screen format | **done** | §2, §3 |
| The clean-room record: who wrote what from which inputs, the prompts | **done**: `docs/TAPE_CLEANROOM.md` | |
| No old body in any prompt, document or commit | **done**: the platform patches of D20/D21 hold no removed line (`platform/deltas/*.cut`: hashes only) | §4 |
| The same signal (pulse widths within the tests' tolerance) | **pass** | §5.1 |
| The same receiver behaviour; the envelope at least the old one's | **pass**: 67 of 71 cases against beta.1's 54, every one of beta.1's among them | §5.2 |
| Interrupts off, no stack in chunk 6, chunk 6 paged out, NOBRK rules | **pass** (memguard's invariants on every transfer; lib-stack 28 B as before) | §5 |
| Leap-C, V2 and stock tapes mutually readable; version words as before | **pass** (cross-version both ways; beta.1 ⇄ beta.2 on Fuse; the host tapes) | §5.3 |
| Size within the tape_block budget; HOME reserve ≥ 384 B | **316 B** of the old 331 B; reserve 482 B | §3 |
| Platform bookkeeping: D20, D21, UPSTREAM, MANIFEST, deltas, ledger | **done**: L76, L77 | §4 |
| The existing suites, the kit, Fuse, test-fast, canary, power-on | **pass** | §6 |
| New: the tolerance envelope test, run on the old and new images | **done**: `tools/tapetol.py`, `make tapetol` (in `make qualify`) | §5.2 |
| New: SAVE measured pulse by pulse, and decoded by an independent decoder | **pass** (a defect found and fixed on the way: §5.1) | §5.1 |
| New: the provenance check against the stock ROMs, in `make check` | **pass**: `tools/provenance.py` | §4 |
| ROM change: `make repro` first, then `make qualify`, logs kept | **pass** | §6 |
| Fresh-clone build, CI green | §7 | |
| NOTICE, README, release notes, `spec.md` v0.13, this report; v1.0.0-beta.2 as a draft; the TSRun fork's ROMs on a local branch | **done** | §8 |

## 2. The clean-room method

Three fresh agents, each with only its prompt (reproduced in full in `docs/TAPE_CLEANROOM.md` §5):

1. **Stage A** wrote `docs/TAPE_SIGNAL_SPEC.md` (65 KB): the signal (§2), the hardware (§3), the contracts as the
   callers use them (§4: carry, DE outstanding, IX walking, the sender's carry, which `SH_TAPE_SEND` relies on although
   the old header said "none meaningful"), the receiver's behaviour as requirements (§5), the tolerance (§6), mutual
   readability (§7), the constraints (§8: the capture slots, memguard, the stack limit of 34 B it derived from
   *lib-stack*) and a test map (§9). Its inputs: the TZX format's documentation and two public descriptions of the
   signal; Leap-C's documents; the old routines' contract headers and callers; the tests. Fuse's loader detection
   (which Leap-C's Fuse suites rely on to start the tape) was described to it in words by the orchestrator.
   §10, the beta.1 receiver's measured envelope, was added by the orchestrator from `tools/tapetol.py`.
2. **Stage B (tape)** wrote `src/runtime/tapeblock.asm` from the specification, ran the suites itself and iterated.
3. **Stage B (glyph)** wrote `.is_block_graphics` (36 B) from a description of the glyph, after the old code had been
   removed from the file.

Before the Stage B authors started, the orchestrator removed the old code from `platform/` (deltas D20, D21), so their
working tree, builds and listings never contained it. What each author and the orchestrator read, including the few
lines of old code that the orchestrator and Stage A saw by accident, is in `docs/TAPE_CLEANROOM.md` §2-§3.

**Changes requested after the first version** (each a behaviour, named in words; `TAPE_CLEANROOM.md` §5.2):

- **Border stripes.** The first version wrote no border; the stripes are how a cassette user sees the signal. Both
  routines now stripe at every edge and restore the border after the block.
- **The closing half-pulse.** The independent-decoder check (§5.1) found that fuse-utils' `audio2tape` decoded a
  Fuse recording of the new SAVE's header but missed its data block; beta.1's SAVE ends each block with one more
  half-pulse after the last bit, and with it both blocks decode. The specification had made it optional (§2.4); it was
  amended to required, and the sender sends it. To stay within the 318 B then budgeted, the author merged the
  receiver's search and sync-wait loops (the lock is now 255 pilot half-pulses in a row, not 256; no test or envelope
  case changed).

## 3. The routines as built

| | Bytes | Notes |
|---|---:|---|
| `TAPE_SEND_BLOCK` (with `TS_HALF`) | 143 | one edge routine: a `djnz` delay, the port image in A' toggled on MIC and the border, one `out`; each kind of half-pulse its own delay count (every T-state count in the comments); SPACE after every byte; the closing half-pulse |
| `TAPE_RECV_BLOCK` (with `TR_BYTE`, `TR_SEDGE`, `TR_EDGE`) | 173 | one read of port `$7FFE` per 63 T pass (EAR and SPACE together), B a pass counter (Fuse's loader detection follows it); widths as counter differences; lock on 255 pilot half-pulses of 16-49 passes; each bit decided on its full length (above 34 passes: a 1); silence budget in counter overflows (`STORAGE_ENTRY_RETRY`, about 8.6 s) |
| **Total** | **316** | the old pair 331 B; ledger L76 (−15 B) |
| `GFX_CHAR_TO_FONT_OFFSET.is_block_graphics` | 36 | V2's 48 B; ledger L77 (−12 B) |

HOME: 15,902 B used, **482 B free** (floor 384 B; 455 B before). EXROM unchanged in size (186 B free); its bytes
changed only because HOME's addresses moved. Stack: *lib-stack* measures 28 B, as before. ROM coverage: every
instruction of `tapeblock.asm` executed (188 of 188 on the final images; the suites' coverage overall: HOME 99.8 %, EXROM
99.4 %, every routine entered).

The shrink-z80 skill's pattern scan found nothing worth taking (five `nop`s that are timing pads; the code was already
under budget).

## 4. Provenance and the platform

- **`tools/provenance.py`** (`make provenance`; in `make check` when `$LEAPC_STOCK_ROMS` holds the stock `48.rom`,
  `tc2068-0.rom`, `tc2068-1.rom`): every run of 12 or more bytes that a production image shares with a stock ROM,
  located by routine. On the beta.1 images it finds exactly `NOTICE`'s list: five runs in `STORAGE_SEND_BLOCK` (33, 19,
  22, 13 B), one in `STORAGE_RECEIVE_BLOCK` (31-32 B), the two 12-byte runs in `GFX_CHAR_TO_FONT_OFFSET`, and
  `SH_IDCHAR`'s 15 B. On the new images: **only `SH_IDCHAR`'s 15 B** (recorded with its reason: Leap-C's own letter
  test, equal to the stock ALPHA routine) and the $FF fill. Only offsets and lengths are printed, never stock bytes.
- **Platform deltas.** D20 removes V2's block I/O, its timing constants and the file header that described it from
  `kernel/storage/storage.asm` (the tag's lines 1-106 and 188-592); D21 replaces `.is_block_graphics` in
  `kernel/graphics/graphics.asm` (the tag's lines 474-527). A patch would quote the removed lines, so
  `tools/check_platform.py` gained **cut records**: `platform/deltas/<file>.cut` lists the removed upstream line ranges
  with their sha256, and the patch is the delta from the tag's file without them; the check verifies the ranges' hashes
  and the base against the tag. No line of the old routines' text is in this milestone's commit as such: a check of every added line against the old bodies' 227 distinct lines finds 11 equal single lines, all generic (the contract line `; Destroys: AF, AF', BC, DE, HL, IX`, `out  (PORT_ULA), a`, `in   a, (PORT_ULA)`, `ld   a, (PORT_FE_SHADOW)`, `ld   (STORAGE_ENTRY_RETRY), hl`), no two consecutive. HOME no longer
  includes `storage.asm`; the EXROM includes it for the header logic, unchanged.
- **Ledger:** L76 (tape_block −15 B), L77 (platform −12 B). UPSTREAM.md, MANIFEST and spec.md §2.1 record D20, D21.

## 5. The signal, the envelope and mutual readability

### 5.1 SAVE's output

Measured by the cassette suite's capture on ZEsarUX (every `out` of the sender, `tools/tapes.py` decode):

| Half-pulse | Nominal (T) | Measured (T) | Tolerance |
|---|---:|---:|---|
| pilot | 2,168 | 2,169-2,175 | −2..+16 |
| sync 1 | 667 | 667 | |
| sync 2 | 735 | 735-740 | |
| bit 0 | 855 | 855-867 | |
| bit 1 | 1,710 | 1,711-1,719 | |
| closing | 855 | 862 | |

Pilots 8,063 / 3,223 (decoded 8,063 / 3,222: the first `out` of a block sets the level without an edge, as before).
The 8 KB *roundtrip-large*: 49.4 s of tape, the same widths.

**Independent decoder.** fuse-utils' `audio2tape` decodes the kit's 39 WAVs (`hwkit.py --verify`), and since this
milestone `fusetest save` also converts Fuse's own recording of SAVE (`tape2wav`) and requires `audio2tape` to find
exactly the program's two blocks. The first version failed this (the data block was missed: no closing half-pulse);
the fix is §2. Fuse's recording of the final SAVE: header 19 B and data 154 B, checksums correct.

### 5.2 The tolerance envelope

`tools/tapetol.py` (`make tapetol`, a step of `make qualify`): 71 program tapes, each with one distortion, as TZX
direct recordings at 4 T a sample, LOADed by `LOAD ""` on Fuse 1.9.1 (loader detection on, acceleration off). The
beta.1 images are built from the tag (`tools/beta1ref.sh`) and only run.

| Case | beta.1 | beta.2 |
|---|---|---|
| scale-all -25% | refuse | accept |
| scale-all -20% | accept | accept |
| scale-all -15% | accept | accept |
| scale-all -10% | accept | accept |
| scale-all -5% | accept | accept |
| scale-all +0% | accept | accept |
| scale-all +5% | accept | accept |
| scale-all +10% | accept | accept |
| scale-all +15% | accept | accept |
| scale-all +20% | accept | accept |
| scale-all +25% | accept | accept |
| scale-pilot -25% | accept | accept |
| scale-pilot -20% | accept | accept |
| scale-pilot -15% | accept | accept |
| scale-pilot -10% | accept | accept |
| scale-pilot -5% | accept | accept |
| scale-pilot +5% | accept | accept |
| scale-pilot +10% | accept | accept |
| scale-pilot +15% | accept | accept |
| scale-pilot +20% | accept | accept |
| scale-pilot +25% | accept | accept |
| scale-sync -25% | accept | accept |
| scale-sync -20% | accept | accept |
| scale-sync -15% | accept | accept |
| scale-sync -10% | accept | accept |
| scale-sync -5% | accept | accept |
| scale-sync +5% | accept | accept |
| scale-sync +10% | accept | accept |
| scale-sync +15% | accept | accept |
| scale-sync +20% | accept | accept |
| scale-sync +25% | accept | accept |
| scale-bits -25% | refuse | accept |
| scale-bits -20% | accept | accept |
| scale-bits -15% | accept | accept |
| scale-bits -10% | accept | accept |
| scale-bits -5% | accept | accept |
| scale-bits +5% | accept | accept |
| scale-bits +10% | accept | accept |
| scale-bits +15% | accept | accept |
| scale-bits +20% | accept | accept |
| scale-bits +25% | accept | accept |
| jitter 5% | accept | accept |
| jitter 10% | accept | accept |
| jitter 15% | accept | accept |
| jitter 20% | accept | accept |
| jitter 25% | accept | accept |
| jitter 30% | refuse | accept |
| scale-all -20% jitter 10% | refuse | accept |
| scale-all -10% jitter 10% | accept | accept |
| scale-all +10% jitter 10% | accept | accept |
| scale-all +20% jitter 10% | accept | accept |
| bit-skew 10% | accept | accept |
| bit-skew 20% | accept | accept |
| bit-skew 30% | accept | accept |
| pilot-short 2000 | refuse | accept |
| pilot-short 1500 | refuse | accept |
| pilot-short 1000 | refuse | accept |
| pilot-short 800 | refuse | accept |
| pilot-short 600 | refuse | accept |
| pilot-short 400 | refuse | accept |
| pilot-missing | accept | accept |
| pilot-missing-end | refuse | refuse |
| pilot-extra | accept | accept |
| inverted | accept | accept |
| pilot-dropout 2 ms | accept | accept |
| pilot-dropout 10 ms | refuse | accept |
| pilot-dropout 50 ms | refuse | accept |
| pilot-dropout 200 ms | refuse | accept |
| data-dropout 1 ms | refuse | refuse |
| data-dropout 5 ms | refuse | refuse |
| data-dropout 20 ms | refuse | refuse |

**beta.1: 54 of 71. beta.2: 67 of 71**, every case beta.1 accepts among them. beta.2 refuses an edge missing 4 pulses
before the sync (as beta.1 does) and the three dropouts inside the data block (as it must). Jitter J is a uniform
factor 1 ± J on every half-pulse; the speed cases scale every width.

### 5.3 Mutual readability

- *cross-version* and *lib-cross-version* (tapetest): V2's reference ROM and Leap-C exchange tapes made by each one's
  SAVE; each refuses the other's with `BAD TAPE VERSION`, as before.
- beta.1 and beta.2 on Fuse: each LOADs the other's SAVE recorded by Fuse's deck.
- *host-tape*, the corpus on Fuse (780 programs from `c2tape.py`'s standard-speed tapes), the kit's WAVs on both
  emulators: stock-format tapes load.

## 6. Qualification

ROM change: `make repro` first, then `make qualify`, then `make test-fast` (logs kept outside `build/`).

| Step | Result |
|---|---|
| `make repro` | reproducible: two clean builds give the hashes above, and the libraries |
| `make test` (in qualify) | **PASS, 0 failures** (883 s, 7 emulators): every corpus suite, the canary (921 cases), power-on (8 patterns, 144 boot checks, 706 corpus slices), the cassette suite **30/30**, the float core 5,451/5,451, the shell and workflow (921/921 through RUN) |
| `make fuse` | PASS: boot, keyboard, typed, BREAK, frames, save (with the independent decode), wav, lib, corpus **780/780** LOADed from tape and RUN |
| `make timing` | pass |
| RAM patterns (warm, random:7) | pass |
| `make capacity` | pass |
| kit `--verify` (30-minute soak) | PASS; `audio2tape` decoded 39/39 WAVs |
| `make tapetol` | 54 → 67 of 71, nothing narrower |
| `make check` | pass (budget, platform with the cut records, test image, RAM layout, doc examples, provenance) |
| `make test-fast` | PASS, 0 failures |

An earlier run of the qualification (before the closing pulse) had one canary case fail with a ZRCP transport
timeout (`tests/rt/break_malloc.c`, a harness error, not a result); the case passed four times alone and the whole
`make test` passed on a rerun. The final run had no failure.

## 7. The fresh clone and CI

A clone of this milestone's commit, built in an empty environment (`env -i`, a scratch `HOME`, `PATH` = system
directories and sjasmplus 1.23.1 built from source as `CONTRIBUTING.md` says, `LEAPC_V2_REPO` = a fresh clone of
2068-Leap from GitHub):

| Step | Result |
|---|---|
| `make` | pass |
| `make check` with the stock ROMs (`LEAPC_STOCK_ROMS`) | pass; provenance: 3 common runs, 0 not accounted for |
| `make check` without them (unset, or a missing folder) | pass; `provenance: SKIPPED: the stock ROMs are not in ... (set LEAPC_STOCK_ROMS)` |
| `make repro` | pass: HOME `043becf4…`, EXROM `97fe9523…`, combined `9cc67979…` |
| `make kit`, `make release` in a second fresh clone | pass; the zips byte-identical to the first clone's; the emulator pack's own `SHA256SUMS` checks 106 files |

The release assets: `leapc-1.0.0-beta.2-emulators.zip` (126,617 B, `3c260d68…`), `leapc-1.0.0-beta.2-hardware-kit.zip`
(420,908 B, `fa4e9e94…`), `SHA256SUMS`. CI on GitHub: see the commit's run (§8).

## 8. Documents and release

- `NOTICE`: §3 is now the history (beta.1 and earlier contained the derived code; how it was removed); MIT covers the
  ROM images. `README.md`'s licence paragraph; `CONTRIBUTING.md` (`LEAPC_STOCK_ROMS`); `spec.md` v0.13 (§2.1 D20,
  D21; §8.5 the routines as built and the envelope); `project_plan.md` §13; `platform/UPSTREAM.md`.
- The guides (`EMULATORS.md`, `BETA_TESTING.md`, `USER_GUIDE.md`) and the bug-report template: version 1.0.0-beta.2
  and the new hashes; `docs/hardware/EMULATOR_RESULTS.md` regenerated by the kit's verification.
- `docs/releases/v1.0.0-beta.2.md`: the release notes.
