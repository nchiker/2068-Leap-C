# Milestone 13 — draw() on 2068-Forth 2.0's line: report

**Status: built 2026-11-01 on branch `draw-speed`; not released.** Owner decision the same day: option A of
`~/Projects/Leap-IDE/docs/requests/LEAP_C_EXAMPLE_11_ANSWERS.md` section 2 (the Leap IDE's
`LEAP_C_DRAW_SPEED.md`): port 2068-Forth v2.0's `GFX_LINE` (`kernel/graphics/graphics.asm`, its
`docs/V2/milestones/Display_speed.md`) and keep Leap-C's rule that `draw()` moves off-screen ends to the edge.

## 1. What changed

Platform delta D25 (`platform/UPSTREAM.md`), in `kernel/graphics/graphics.asm` and `kernel/math/math.asm`:

- **`GFX_LINE`** is Forth's major-axis Bresenham loop: r, dmin and dmaj in HL', DE', BC' (nothing in Leap-C uses
  `exx`: not the interrupt handler, the float core, the runtime or the cartridge code), the address and mask
  stepped from pixel to pixel (`LINE_XSTEP`, `LINE_YSTEP`), the attribute written with the first pixel of each cell
  (mode 1: of each 8x1 byte; `LINE_ATTR`). Unlike Forth's, its ends are bytes on the screen (`LIB_DRAW` clamps them
  as before), so Forth's walk off the screen, its 16-bit deltas and its edge tests are left out; and `over(1)`
  draws by exclusive-or (E bit 5: `ld a,(hl) / xor c`, then `or c` unless over).
- **`GFX_PLOT_CLIPPED`** (`plot()`, the libraries' `LX_PLOT`) checks the point, computes its address with
  `GFX_PIXEL_AT` and draws it through the line loop as a line of one point (it ends before any step, so the
  alternate registers are not touched). **`GFX_READ_PIXEL`** (`point()`) takes C = x, B = y (`LIB_POINT` follows).
- Gone: V2's `GFX_PIXEL_ADDR_SETUP`, `GFX_WRITE_PIXEL`, `GFX_LINE`, `BIT_MASK_TABLE`, and `MATH_COMPARE16` (its only
  caller was the old `GFX_LINE`). The RAM cells the old code used stay defined in `sysvars.inc`, unused (as delta
  D3 did): no RAM layout change.

## 2. Tests

`tools/linetest.py` (`make lines`, and a step of `make qualify`):

- **Pixels.** A Python model of draw() as 1.1.0 defines it (ends clamped, V2's e2 loop, an attribute per point,
  OR or XOR). Programs of 40 `draw()` calls each, run in ZEsarUX; the bitmap, the attributes and in mode 1 the second
  display file must equal the model's byte for byte. The lines: 48 fixed (corners, edges, single points, the ends
  at ±32,768, lines wholly off the screen, 24 directions from the centre) and 400 random (half on the screen, half
  with ends in -300..560, -250..450), each in mode 0 and 1, with and without `over`.
  - The model was first checked against **the 1.1.0 ROM** (12 programs, 88 lines: all equal), and shown to be
    sensitive: the e2 loop with its other tie rule draws different points for 56 of 352 of the lines.
  - On this build: seed 2068 (448 lines, 48 programs) and seed 7 (248 lines) all equal.
  - The loop itself, modelled in Python, equals the e2 form on 200,000 random lines on the screen.
- **Speed** (`--time`): one `draw()` less an empty program, with ceilings at about 1.25x this build's figures.

| T-states (ZEsarUX) | 1.1.0 | This build | |
|---|---:|---:|---:|
| `draw(0, 100, 255, 100)`, 256 pixels | 369,298 | 60,702 (ceiling 76,000) | 6.1x |
| `draw(100, 0, 100, 191)`, 192 pixels | 283,902 | 51,563 (ceiling 65,000) | 5.5x |
| `draw(0, 0, 255, 191)`, 256 pixels | 388,184 | 81,691 (ceiling 102,000) | 4.8x |
| `draw(10, 10, 100, 60)`, 91 pixels | 136,701 | 29,461 | 4.6x |
| A `plot()` call (100 in a loop, the loop's cost taken off) | 1,366 | 1,029 | -25% |

Forth's own figures for the same row, column and diagonal are 58,954, 52,286 and 83,901 T. `plot()` is still mostly
its call: `LIB_ARGS`, `LIB_OVATTR` and the bounds checks are about 600 T of its 1,029.

The regression suites: section 4.

## 3. Sizes

HOME: platform 3,068 -> 2,973 B, **95 B returned to the reserve (481 -> 576 B free)**, ledger L86. The estimate in
the answer to the IDE was 15-35 B: leaving out the edge tests (the ends are on the screen) and drawing `plot()`'s
pixel through the line loop saved the rest. EXROM unchanged.

## 4. Results

All on this branch, 2026-11-01, ZEsarUX unless stated; every one passed:

| Run | Result |
|---|---|
| `make check` | passes (271 doc examples up to date, platform deltas, RAM layout and its 8 negative controls, provenance: 0 runs unaccounted for) |
| `make test` (1,117 s, 7 emulators) | PASS, 0 failures: exec doc 271/271, experr 66/66, expr 173/173, float 96/96, golden 47/47, lib 110/110, mem 30/30, pp 11/11, pperr 25/25, rt 18/18, run 13/13, stmt 68/68, stmterr 36/36; lexer 113/113; shell 44/44; e2e 47/47 and the corpus through RUN 1,166/1,166; float 5,451/5,451 checks; poweron 144/144 boot checks, 951/951 corpus slices; tape 30/30; canary 1,166 cases, 0 hits |
| ROM coverage (`romcov`) | HOME 7,534/7,547 instructions (99.8%), 444/444 routines; EXROM 3,345/3,362 (99.5%), 154/154 routines |
| `make fuse` (Fuse 1.9.1) | PASS: boot, keyboard, typed 39/39, break, frames, save, wav, lib; corpus 1,016/1,016 |
| `make test-cart` | PASS: the 115-program comparison with RUN 115/115 (reports and final screens identical), behaviour 25/25, NO PROGRAM 6/6, port audit and hand-off 5/5 |
| `make lines` | PASS: pixels (seed 2068, 48 programs) and the speed ceilings |

Not run: `make repro`, `make qualify` and `make release` (for the 1.2.0 release, with the owner's approval).

## 5. What it changes for hosts

The ROM bytes change: a new cartridge identity (not `$E90E`), new `.sym` addresses (none of the CHANGELOG's stable
names is affected), new emulator packs, and new ROMs for TSRun and the Leap IDE. The library ABI (the jump table at
`$3FD0`) is unchanged, so library tapes built for 1.x still load.
