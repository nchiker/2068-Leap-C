# Milestone 14 — the scroll, text and the interrupt on 2068-Forth 2.0's code: report

**Status: built 2026-11-01 on branch `display-speed` (from `draw-speed`); not released.** Owner decision the same
day: after `draw()` (M13), port Forth v2.0's other display speed-ups. For the text, option (a) was chosen: Forth's
font in ASCII order, since the Leap IDE already reads that layout. Forth's sources are its `Display_speed.md`
(the scroll), `Words_and_keys.md` (text) and `BREAK_and_timing.md` (the interrupt), at tag `v2.0`.

## 1. Measured first (1.1.0)

These were measured with routine calls under ZEsarUX, interrupts off and the stub cost subtracted, and with C
programs (the run less a baseline).

| Cost | 1.1.0 | Where the time went |
|---|---:|---|
| The interrupt, an idle frame | 2,028 T (3.5% of a 60 Hz frame) | `IO_KEY_SCAN_ALL` (8 rows, each through `ROW_TABLE` and a call) and `IO_FIND_KEY`, every frame |
| A printed letter / `$` | 1,597 / 2,933 T | `GFX_CHAR_TO_FONT_OFFSET` 184 T (`$`: 1,471, a linear scan of 31 punctuation pairs); `GFX_PUTCHAR` 840; `GFX_SET_ATTR` 217; the library's own work about 520 |
| One scroll of program output | about 237,000 T (4 frames) | 22 + 1 rows copied a scanline at a time with `LDIR` (182k); the new row cleared through 32 `GFX_PUTCHAR` + `GFX_SET_ATTR` calls (33k); the attributes (20k) |

## 2. What changed

Platform deltas D26-D28 (`platform/UPSTREAM.md`):

- **D26, the scroll.** `GFX_SCROLL_OUTPUT_UP` is now Forth's `GFX_SCROLL_ROWS`, with A = 7 for rows 1-23 up one.
  - The attributes move as one run.
  - Each scanline of a third moves as one or two runs of 32-byte unrolled `LDI` blocks (`GFX_LDI_BLOCKS`, 16 T a byte).
  - `GFX_CLEAR_ROW` writes the row's bytes and attributes directly; its In now has A = the attribute.
  - `GFX_SCROLL_TEXT_UP` and `GFX_COPY_ROW_BITMAP` are gone.
- **D27, the interrupt.** With no key tracked, one read of port $FE with every row selected ends the frame when no
  key is down.
  - Otherwise the rows are read with `IN A,(C)` / `RLC B`. `ROW_TABLE` and the page-zero `IO_KEY_SCAN_ROW` are gone.
  - Debounce, repeat and the BREAK latch (D4) are unchanged.
  - `IO_SCAN_TABLE` is not refreshed on idle frames. Only the interrupt's own routines read it.
- **D28, text.** `FONT_TABLE` holds printable ASCII in code order: 95 glyphs.
  - The backtick, which has no glyph, keeps a blank slot, so it still prints as a space.
  - Every glyph is byte-identical to 1.1.0's; this was checked from the two images.
  - `GFX_CHAR_TO_FONT_OFFSET` is one subtraction. D21's block graphics and the UDGs are kept, and `PUNCT_CHAR_TABLE`
    is gone.
  - `GFX_CHAR_SETUP` computes the cell's address from the row and column.
  - `GFX_PUTCHAR` and `_OVER` are unrolled and keep BC.
  - `GFX_PRINT_STRING_ATTR` sets the attribute from the cell's address instead of calling `GFX_SET_ATTR`.

## 3. Speed (ZEsarUX, T-states)

| | 1.1.0 | 1.2.0 | |
|---|---:|---:|---:|
| Interrupt, idle frame | 2,028 | 225 | 9.0x |
| Interrupt, a key held | 1,625-1,656 | 836-856 | 1.9x |
| Interrupt, the frame a key is first seen / accepted / released | 2,510 / 1,848 / 2,187 | 1,739 / 1,059 / 1,416 | |
| `print`, a letter, digit or space (C program, per character) | 1,467-1,623 | 955 | 1.6-1.7x |
| `print`, punctuation (`$ @ ~ ^ \ <`) | 2,210-2,933 | 940-955 | up to 3.1x |
| `putchar('A')` / `putchar('$')` | 1,857 / 3,185 | 1,190 / 1,190 | 1.6x / 2.7x |
| `printf("%d", 12345)` | 17,757 | 14,277 | 1.2x |
| `GFX_PUTCHAR` 'A' / '$' (direct) | 842 / 2,128 | 449 / 450 | |
| One scroll (C program, per scroll) | 246,899 | 134,733 | 1.8x |
| `GFX_SCROLL_OUTPUT_UP` (direct, interrupts off) | 236,677 | 133,659 | 1.8x |
| `GFX_CLEAR_ROW`, row 23 | 33,152 | 7,603 | 4.4x |

The idle interrupt's 1,800 T a frame is about 3% of a 60 Hz frame, so every program gains about 3%. Forth's own
figures for the interrupt were 2,010 -> 207 T.

## 4. Sizes

HOME: platform 2,973 -> 2,925 B, **48 B returned (576 -> 624 B free)**, ledger L87. That is net of
`GFX_LDI_BLOCKS`' 64 bytes of `LDI`, the font's 8-byte backtick slot, and `PUNCT_CHAR_TABLE`'s 62 bytes going. The
page-zero `IO_KEY_SCAN_ROW` (3 B) becomes fill. The EXROM is unchanged.

## 5. Tests

All on this branch, 2026-11-01; every one passed:

| Run | Result |
|---|---|
| `make check` | passes (budget, platform deltas, test image, RAM layout and its 8 negative controls, 271 doc examples, provenance, `cart_check`: 1,892 release labels at their addresses, identity `$201F`) |
| `make test` (1,614 s, 7 emulators) | PASS, 0 failures; the corpus through RUN 1,166/1,166; ROM coverage HOME 99.8% (442 of 443 routines: `GFX_SET_ATTR` has no caller left, see section 6) |
| `make fuse` (Fuse 1.9.1) | PASS: typed 39/39, corpus 1,016/1,016, keyboard, BREAK, frames, save, wav, lib |
| `make test-cart` | PASS: the 115-program RUN comparison 115/115, behaviour 25/25, port audit 6/6, hand-off 5/5 |
| `make lines` | PASS (pixels and speed) |
| `make timing` | passes (ZEsarUX / Fuse compile timing ratio 1.026) |
| `make display` (new, `tools/displaytest.py`) | PASS on this build; on 1.1.0 all 8 ceilings fail |

Two cartridge-tool expectations named the removed `IO_KEY_SCAN_ROW` and were updated: `tools/cart_check.py` (no label
moves any more) and `carttest.py`'s `B:expected-peek0` (the release's byte `$0004` is now page zero's fill, 0, not
219).

`tools/displaytest.py` times each routine directly, with interrupts off, 12 runs at a random frame phase, and
compares the maximum with ceilings about 1.25x this build's: interrupt idle 300 T and with a key held 1,100 T;
`GFX_PUTCHAR` 'A' and '$' 570; `GFX_PUTCHAR_OVER` 650; `LIB_PUTC` 1,120; `GFX_SCROLL_OUTPUT_UP` 170,000;
`GFX_CLEAR_ROW` 9,600. It is a step of `make qualify`.

## 6. Left

- `GFX_SET_ATTR` (11 B) has no caller: the old print loop, row clear and pixel write all used it. It is removed in
  the commit after this one.
- Leap V2 takes D27 only; its own back-port already has a faster scroll and text. Its string printing steps along a
  run of characters (about 528 T a character), where Leap-C's `print` goes through `LIB_PUTC` one character at a
  time (955 T). That is a possible later change to the library, not made here.
