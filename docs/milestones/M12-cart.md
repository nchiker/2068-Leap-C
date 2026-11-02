# Milestone 12 — The runtime cartridge (`make cart`): plan and report

**Status: done 2026-11-01 (plan approved by the owner the same day).** Released as 1.1.0. Sections 1-9 are the plan as approved, corrected where the build differs (marked *as built*); section 10 is the report. Promised to the Leap IDE in
`~/Projects/Leap-IDE/docs/requests/LEAP_C_ANSWERS.md` Q5. The nearest models: 2068-Forth `82af031` ("make cart runs
Forth and a SAVE-LIB program from the DOCK of a stock TS2068") and Leap V2.1's cartridge as the IDE built it
(`~/Projects/Leap-IDE/cartridge-build/Docs/CARTRIDGE_STATUS.md`, `docs/LEAP_CARTRIDGE_BUILD.md`).

## 1. Goal

A `.dck` (emulators) and a flat 64 KB `.bin` (a physical cartridge, e.g. a PicoROM) that run **one compiled Leap-C
program on a stock TS2068** (stock HOME ROM and EXROM installed, nothing replaced). The program is compiled by the
**release** ROM (in the IDE, or by this repository's tool) and runs on the cartridge's HOME. There is no editor, no
shell and no source on the cartridge. After the program: the shell's one-row report, then a key runs it again from
a cold start.

## 2. Requirements already agreed (handoff, Q5)

- A build flag (`-DLEAPC_CART`) and `make cart` here; **the release ROM images do not change** (`make repro` still
  gives HOME `d2b18eaa…`, EXROM `02790ebe…`).
- **Every HOME routine keeps its release address**: compiled code calls absolute HOME addresses (the RST helpers,
  `RT_*`, the float calls, every library function). Patches are same-size; the build compares the two `.sym` files.
- The EXROM is needed at run time (the float core, `beep`/`sound`, `tape_save`/`tape_load`); the shell is not.
- The image format of the IDE's proposal: a header (signature, format, ROM identity, entry) then `[address,
  length, bytes]` blocks per used region and a loaded library's region 3. Identity: a CRC-16 over HOME + EXROM,
  computed at build time (0 ROM bytes), published with the release.

## 3. Memory map

| DOCK chunk | Address | Content | Mapped (HSR, port `$F4`) |
|---|---|---|---|
| 0-1 | `$0000-$3FFF` | the cartridge HOME (`build/cart/leapc_cart_home.bin`) | always (`$03`/`$43`) |
| 2 | `$4000-$5FFF` | the program image's continuation (only for an image over 16 KB) | only in the copy, interrupts off |
| 3 | `$6000-$7FFF` | absent | never (image region 4 / display file 2 is HOME RAM) |
| 4-5 | `$8000-$BFFF` | the program image | only in the copy, interrupts off |
| 6 | `$C000-$DFFF` | **the release EXROM, unchanged** (`leapc_exrom.bin`) | while `BANK_EXROM_DEPTH` > 0 (`$43`), else HOME RAM: image region 1 |
| 7 | `$E000-$FFFF` | absent | never |

Port `$FF` bit 7 stays 0 (DOCK) from the cold start on; the stock ROMs are never selected again. The EXROM needs no
patch at all: everything cartridge-specific is in HOME, so the cartridge's EXROM is byte-identical to the release's,
and the cartridge build only adds one 16 KB image.

## 4. The HOME changes (all under `IFDEF LEAPC_CART`)

| Where | Release | Cartridge | Size |
|---|---|---|---|
| `$0000-$0004` | `di` / `jp COLD_START` / `IO_KEY_SCAN_ROW` at `$0004` | the LROS header: `$00` (byte 0, unused; as built, as 2068-Forth and V2), `$01` (LROS), `CART_ENTRY` (LE16), chunk spec `$BC` (chunks 0, 1, 6 DOCK; low-active) | same |
| `IO_KEY_SCAN_ROW` | `$0004` (`in a,($FE)` / `ret`, 3 B) | moved to the page-zero gap `$000D-$000F` (free in the release); its one caller (`IO_KEY_SCAN_ALL`'s `call`) changes operand | same; one label moves (allowed by name in the check: nothing compiled calls it) |
| `BANK_PAGE_EXROM_IN` (*as built: `src/cart/cart_bank.asm` in place of `kernel/bank/bank.asm`*) | depth 0→1: `$FF` shadow bit 7 set, `$F4 = $40` | depth 0→1: `$F4 = $43`; port `$FF` and its shadow untouched. The bytes saved hold `BANK_CART_HOME` (`ld a,$03` / `out ($F4),a` / `ei` / `ret`) | same (`DS` pads to the release size) |
| `BANK_PAGE_EXROM_OUT` | depth 1→0: `xor a` / `out ($F4),a` | depth 1→0: `jr z, BANK_CART_HOME` in place of the release's `jr nz, .still_nested` / `xor a` / `out ($F4),a` (2 B for 5, padded; Forth's arrangement) | same |
| `COLD_START`'s last instruction | `jp LEAPC_EXROM_SHELL` | `jp CART_RUN` | same |
| HOME free space (`$3DEF-$3FCF`, 481 B) | `$FF` | `CART_ENTRY`, `CART_RUN`, the copy, the checks, the report, `NO PROGRAM` | an estimated 220-260 B |

The other writers of the ports, checked in source: `GFX_SET_MODE` (`$FF` through `PORT_FF_SHADOW`, which keeps bit
7 = 0 on the cartridge), `COLD_START` (`$FF = 0`) and `CC_ERROR` (`src/compiler/cerror.asm`, `$F4`: the compiler,
never run on a cartridge). The build also scans the listing for every `out` to `$F4`/`$FF` so a new writer cannot
slip in. Nothing in Leap-C jumps to `$0000` (checked: no `rst $00`, no `jp 0`).

- **`CART_ENTRY`** (the LROS entry): `di`; `ld sp, LEAPC_STACK_TOP`; `$F4 = $03`; the AY's volumes 0 (the stock
  ROM has written the AY); `jp COLD_START`. The release cold start then clears RAM, sets `$FF = 0`, `MEM_INIT` (an
  empty source store, so `PROG_END` is an empty store's end and `RT_RUN`'s heap is built from there), the keyboard
  ISR, IM 1, `ei`, `BANK_PAGE_EXROM_IN` (depth 1), and `jp CART_RUN`.
- **`CART_RUN`**: `CART_LOAD` (below); no image or a bad one: `NO PROGRAM` on row 23 (the report's style), a key,
  `jp CART_ENTRY`. A good one: `GFX_CLS`, `call RT_RUN` (exactly as `SH_RUN.compiled`), then the report built with
  the EXROM shell's own routines and messages (`SH_APPEND`, `DG_APPEND`, `SH_APPEND_NUM`, `SH_TXT_EXIT`,
  `SH_MSG_RUNTIME`, `SH_MSG_BREAK`, `SH_REPORT`): `EXIT n`, `RUNTIME ERROR n MESSAGE` or `BREAK`, white on black
  on row 23, then `SH_WAIT_KEY`; then `jp CART_ENTRY` (a cold start re-copies the image: the program may have
  changed its own static data). The shell's `.line` step (`SH_JUMP_TO_LINE`) is not used: there is no source.
- **`CART_LOAD`**, interrupts off: map the image (`$F4 = $33`, and `$37` for a continuation in chunk 2), check the
  signature, format, identity, length and CRC, copy each block, set the run cells, `$F4 = $43`, `ei`. While chunk 2
  is DOCK the cells at `$5B00-$5FFF` are hidden, so that part of the copy keeps its state in registers and the
  stack (chunk 7) only. The copy never maps over its own destinations (regions 4, 1, 2, 3 are chunks 3, 6, 7).

## 5. The program image (format 1)

At DOCK `$8000` (continuing at DOCK `$4000` past 16 KB). Little-endian words.

| Offset | Size | Content |
|---|---|---|
| 0 | 4 | `"LCPG"` |
| 4 | 1 | format, `1` |
| 5 | 2 | identity: CRC-16/CCITT-FALSE (poly `$1021`, init `$FFFF`) of the compiling release's HOME then EXROM (V2's scheme) |
| 7 | 2 | `RUN_MAIN` (main's address; the entry) |
| 9 | 1 | `RUN_VOID` |
| 10 | 16 | `IMG_LIM` (the compiler's region limits; `mode(1)` reads region 4's to refuse hi-res when the image uses `$6000-$77FF`) |
| 26 | 1 | `LIB_LOADED` (`$F4` when a library is carried in region 3, else 0) |
| 27 | … | blocks `[length:2][address:2][bytes]` (1 to 8192 bytes, inside one region), ended by a length of 0: per region its code `[base, low)` and its static data `[high, end)`, a library's whole region 3, and region 4 up to its last non-zero byte for `#pragma hires` |
| end | 2 | CRC-16/CCITT-FALSE of every byte before it, **high byte first** (the CRC over the whole image is then 0) |

*As built:* there is **no `RUN_FNLINES` field** (the plan had one at offset 10), so the header is 27 bytes and `LIB_LOADED` is at 26. `RUN_FNLINES` stays 0 (the cold start's value), so `RT_ERRLINE` is 0 and the shell's `SH_RUN.compiled` never looks for a source line; that is how the cartridge reuses the shell's report code unchanged (the cartridge calls `SH_RUN.compiled` itself). The block order is also `[length][address]`, not the plan's `[address, length]`.

Largest: the four regions hold 19,840 B, so an image is at most about 19.9 KB: chunks 4-5 and part of chunk 2. A
program the IDE's checker compiled with the release ROM is valid for this cartridge exactly when the identity
matches; the cartridge refuses any other with `NO PROGRAM`.

**The identity value for 1.0.0** is computed by `make cart` from the release images and published in
`CHANGELOG.md` and the cartridge's notes (0 ROM bytes in the release images; the cartridge build holds it as a
constant).

## 6. Tools

- **`tools/cart_check.py`** (run by `make cart` and `make check`): every release label at its release address
  (except `IO_KEY_SCAN_ROW`, named); bytes differ only in the places of §4; the cartridge code within the free
  space; the EXROM identical to the release's; every `out` to `$F4`/`$FF` in the listing is one of the known ones.
- **`tools/c2cart.py PROGRAM.c [--lib NAME] -o OUT.dck [--bin OUT.bin]`**: compiles the program on the **release**
  ROMs in ZEsarUX (`lcharness`; for a library, `LIB "name"` first), stops at `SH_RUN.ccdone`, reads the cells and
  regions of §5, and packs the image, the `.dck` (one block, bank 0, chunks 0, 1, 2 if used, 4, 5, 6) and the flat
  `.bin` (the eight chunks in order, `$FF` in absent ones). The packing is a separate function with no emulator in
  it (`tools/cartpack.py`), the reference for the IDE's JavaScript one.
- **`make cart`** builds `build/cart/leapc_cart_home.bin`, runs `cart_check.py` and the packer's self-test (no
  emulator, so `make check` can depend on it). `make cart PROG=x.c [LIB=shapes]` builds one program's `.dck` and `.bin`.
  *As built:* the demo is a separate target, `make cart-demo` (`examples/cart_hello.c` to `build/cart/hello.dck` and
  `hello.bin`; it needs ZEsarUX; `make release` depends on it). `make repro` covers the cartridge HOME.

## 7. Tests

- **The hand-off** (first, before the rest is built): a probe cartridge on Fuse 1.9.1 and ZEsarUX 13.0 with the
  stock ROMs: interrupt state, IM, SP, `$F4`/`$FF` at the entry (V2's measurement on TSRun: interrupts on, IM 1,
  SP `$61FE`, `$F4 = $43`, `$FF = 0`); an interrupt forced before `CART_ENTRY`'s `di` runs Leap-C's ISR
  (`KBD_ISR_TICK`) on the stock stack and returns. Leap-C's ISR also tests `RUNNING` for BREAK, so the probe also
  holds BREAK at the hand-off with stock RAM in that cell.
- **`tools/carttest.py`** (a suite of `run_tests.py`, and `make test-cart`): the cartridge on the stock ROMs
  against `RUN` on the release ROMs, the same program: the report text and the final screen (rows 0-22), on
  ZEsarUX for a corpus slice (every `tests/lib` program and the manual's examples that need no keys), and on Fuse
  for a smaller slice. Behaviour cases: `EXIT n`, each runtime error, BREAK, a key restarts and the program runs
  again from a cold start, `float`, `beep`/`sound`, `mode(1)` with and without `#pragma hires`, `tape_save`
  (Fuse records it), a `shapes` library program, the largest image (over 16 KB: chunk 2's continuation),
  `NO PROGRAM` for no image, a wrong identity, a wrong CRC and a truncated block list, and the port audit (`$F4`
  only `$03`/`$43`/`$33`/`$37`, `$FF` bit 7 never set after the hand-off).
- **Expected differences** (listed in the test, as V2's): the heap is larger (no source), so `malloc`'s addresses
  differ; UDGs start blank on every run (the cold start clears them; under the shell they persist between runs);
  `PEEK(0..4)` reads the header.
- The release suites are untouched and must give the same results; `make repro` checks both builds.

## 8. When done

A note for the Leap IDE in `~/Projects/Leap-IDE/docs/requests/` (the image format, the identity value, the `make
cart` and `c2cart.py` usage, the expected differences), and Q5 of `LEAP_C_ANSWERS.md` brought up to date (it still
describes a two-row report and `LINE m`; the cartridge uses the 1.0 one-row report). A milestone report in this
file.

## 9. Decisions for the owner

1. **The release vehicle.** The cartridge HOME is a new asset; the 1.0.0 ROMs do not change. Proposed: release it
   as **1.1.0** (an added asset, `leapc-1.1.0-cartridge.zip`: the image, the demo `.dck`, `c2cart.py`, the
   identity), not as an update of the 1.0.0 release.
2. **No image or a bad one:** proposed `NO PROGRAM` on row 23, then a key retries (V2 shows `NO PROGRAM`).
3. **After the program:** the agreed report and a key restarts from cold. (V2's alternative, halting, is not
   proposed.)
4. **Images over 16 KB** use DOCK chunk 2 (agreed). If the owner prefers a simpler first version, the packer could
   refuse images over 16 KB and chunk 2 could come later; the plan as written includes it.

## 10. Report

### As built

**The HOME changes** (all under `IFDEF LEAPC_CART`; `src/rom/home.asm`, `src/cart/cart.asm`, `src/cart/cart_bank.asm`):

| Where | Cartridge |
|---|---|
| `$0000-$0004` | the LROS header: `00`, `01`, `CART_ENTRY`, chunk byte `$BC` |
| `IO_KEY_SCAN_ROW` | `$000D` (was `$0004`); the only label that moved |
| `BANK_PAGE_EXROM_IN/OUT` | **`src/cart/cart_bank.asm` assembled in place of `kernel/bank/bank.asm`** under the flag, with the release routines' sizes and label offsets (`DS` pads with `nop`, never `$FF`). Depth 0 to 1 writes `$F4` = `$43` (`CART_HSR_EXROM`) and leaves port `$FF` alone; depth 1 to 0 jumps to `BANK_CART_HOME = BANK_PAGE_EXROM_IN.home` (`$F4` = `$03`) |
| `COLD_START` | ends in `jp CART_RUN` |
| HOME free space | `CART_ENTRY`, `CART_RUN`, `CART_LOAD` and its helpers, the signature and `NO PROGRAM`: **252 bytes at `$3DEF-$3EEB`, 229 bytes of the space left** (the plan estimated 220-260) |

`CART_IDENTITY` and the EXROM addresses come from `build/cart/cart_exrom.inc` (`tools/cart_build.py`). The loader makes two passes over the image (lengths and CRC, then the copy), with interrupts off, mapping chunks 4-5 and 2 only there.

### Decisions as taken (section 9)

1. **Release vehicle:** 1.1.0, an added asset (`leapc-1.1.0-cartridge.zip`); the ROM images, and so the identity, are 1.0.0's.
2. **No image or a bad one:** `NO PROGRAM` on row 23, then a key retries.
3. **After the program:** the one-row report, then a key restarts from a cold start (the image is copied afresh).
4. **Images over 16 KB** are supported (DOCK chunk 2); the largest tested is 17,008 bytes.

### Results

The identity is **`$E90E`**. `tools/cart_check.py`: 1,908 release labels at their release addresses (only `IO_KEY_SCAN_ROW` moved); the EXROM is the release's. `tools/carttest.py --fuse`, 160 of 160, about 2.5 minutes:

- **A, equivalence (ZEsarUX, stock `ts2068.rom`):** 115 programs (66 `tests/lib`, 49 `tests/doc`); rows 0-22 (text, bitmap, attributes) and the row-23 report identical to `RUN` on the release ROM, bar the expected differences.
- **B, behaviour (25):** exit values; runtime errors 1, 4, 6 and 3; BREAK; restart from cold re-copies the image (a static counter is the same each run); float; `beep`/`sound`; `mode(1)` with and without `#pragma hires` and refused; libraries (shapes, testlib); a 17,008-byte image continuing into chunk 2; `NO PROGRAM` for no image, wrong identity, wrong CRC, truncated blocks, wrong format and a damaged chunk-2 byte; key retries.
- **C, port audit (6):** `$F4` only `$03`, `$33`, `$37`, `$43`; `$FF` only `$00` or `$02` (hi-res); bit 7 never set.
- **D, hand-off (5):** at `CART_ENTRY`: IM 1, interrupts on, SP `$61FE`, `$F4` `$43`, `$FF` `$00`; the IM 1 handler run before `di` returns and the program runs, also with BREAK held.
- **E, Fuse 1.9.1 with its stock ROMs and the `.dck` (9 programs):** screens identical to ZEsarUX's.

**Expected differences:** `malloc`'s addresses (the heap starts at an empty store's end: `$7802` against `$7868` for one program); `PEEK($0000-$0007)` reads the LROS header (0 1 ... 188); UDGs are blank at every start.

**Regression rerun for 1.1.0:** `make repro` reproducible OK (the four 1.0.0 hashes, and `leapc_cart_home.bin` `034e294d…` in both builds, identity $E90E); `make check` pass (with `tools/cart_check.py`); the fast suite pass, 0 failures; `make test-cart CARTTEST_ARGS=--fuse` 160/160 from a cold start; `make fuse` pass (corpus 1,017/1,017). Two test-tool defects found and fixed on the way: parallel Fuse workers built the Fuse shim to one path at once (now an atomic rename), and the `frames` check read Fuse's frame count and `FRAMES` with two shim commands, which Fuse could run frames between at a host load average of 15 (now one batch, answered between two frames).

**Not done:** a physical TS2068, a physical cartridge or PicoROM; TSRun.

### The known hazard

An interrupt exactly between the stock ROM's jump and `CART_ENTRY`'s `di`, with BREAK held **and** a non-zero byte left in stock RAM at `RUNNING` (`$5EB6`), would make Leap-C's interrupt handler take BREAK and unwind to a run stack of 0. It was forced in a test; it was not seen otherwise, because `RUNNING` reads 0 after the stock boot. Not fixed: the first instruction of the entry cannot run earlier.
