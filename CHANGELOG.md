# Changelog

Leap-C's releases, newest first. Each lists what a user or a host program would notice. The per-phase reports in
`docs/milestones/` and the budget ledger in `budget.toml` hold the details.

**Stable names for hosts.** Programs that drive the ROM (the Leap IDE, test harnesses) find their way by the labels
and cells in the release's `symbols/*.sym` files. Addresses move between builds; the names below do not. Renaming
or removing one is a breaking change and is announced here first.

`IO_READ_KEY.wait_hit`, `SH_RUN`, `SH_LOOP`, `SH_WAIT_KEY.read`, `SH_WAIT_KEY.key_ret`, `RT_RUN.done`,
`RT_RUN.leave`, `STATEMENT`, `STMT_DO.cond`, `DCL_AUTOINIT`, `CG_UNIT.found`, `FUNC_DEF`, `SCOPE_CLOSE`,
`GFX_SET_BORDER`, `BANK_PAGE_EXROM_OUT`; the cells `RUNNING`, `CC_ERRNUM`, `CC_ERRLINE`, `SH_ERR_COL`, `RT_ERRNUM`,
`RT_ERRLINE`, `RUN_FNLINES`, `SYM_GLO`, `SYM_LOC`, `CUR_EDIT_INDEX`, `PROG_END`, `ARRAYS_END`, `BANK_EXROM_DEPTH`,
`TOK_LINE`, `CG_PC`.

## 1.1.0 (2026-11-01)

Adds the runtime cartridge. **The ROM images are byte-identical to 1.0.0's** (HOME `d2b18eaa…`, EXROM `02790ebe…`; the
banner stays `2068 LEAP-C 1.0`), so every host name and address of 1.0.0 holds. Qualified on emulators (Fuse 1.9.1,
ZEsarUX 13.0); not run on a physical TS2068.

**Added**
- **The runtime cartridge** (docs/CARTRIDGE.md, docs/milestones/M12-cart.md): one compiled program runs from the DOCK of a
  stock TS2068 (stock ROMs installed), as a `.dck` for emulators or a flat 64 KB `.bin` for a physical cartridge. It
  carries its own HOME (`leapc_cart_home.bin`, built with `-DLEAPC_CART`) and the release EXROM unchanged; after the
  program it shows the one-row report and a key runs it again from a cold start. `NO PROGRAM` for no image or one the
  cartridge refuses.
- **The identity `$E90E`**: the CRC-16/CCITT-FALSE of the release HOME then EXROM. A program image carries it and the
  cartridge refuses any other; a program must be compiled by the release ROM it is cartridged for (1.0.0 and 1.1.0
  share the images, so share the identity).
- **A new asset**, `leapc-1.1.0-cartridge.zip`: the cartridge HOME and EXROM, a demo cartridge (`demo/hello.dck`,
  `hello.bin`), `tools/cartpack.py`, `CARTRIDGE.md` and `SHA256SUMS`. The other assets are 1.0.0's, renamed.
- **`make cart`** (the cartridge HOME, checked against the release; emulator-free, part of `make check`),
  `make cart PROG=x.c [LIB=name]` (packs one program's `.dck` and `.bin`), `make cart-demo` (the demo; needs ZEsarUX;
  `make release` depends on it) and `make test-cart` (`CARTTEST_ARGS=--fuse` adds Fuse).

**For hosts:** the cartridge keeps the address of every release label (1,908 of them); only `IO_KEY_SCAN_ROW` moved
(`$0004` to `$000D`) on the cartridge. The cartridge's own labels (`CART_*`) are not host-stable names.

**Tools and tests (no change to the ROMs):** `tools/cart_build.py`, `cart_check.py`, `cartpack.py`, `c2cart.py` and
`carttest.py` (160 cases: the cartridge against `RUN` on 115 programs, behaviour, a port audit, the hand-off, Fuse);
`make repro` also covers the cartridge HOME; `tools/fusedrive.py` can start Fuse with a `.dck` on its stock ROMs.

## 1.0.0 (2026-11-01)

The first release, after two public betas. Qualified on emulators (Fuse 1.9.1, ZEsarUX 13.0 with a patch); not yet
run on a physical TS2068.

**Changed**
- **A report is one row.** After `RUN`, `FREE` or a tape command the report takes only the bottom row (row 23), so
  the rest of the program's screen stays visible. `RUN` reports `EXIT n`, `ERROR n MESSAGE`,
  `RUNTIME ERROR n MESSAGE` or `BREAK`. The line is no longer printed: the cursor goes to it, and the status row
  shows `LINE n/m` once you press a key. The image size, the heap and the name of an undeclared identifier are no
  longer shown; `FREE` shows the source's size and the room left.
- **The version** (`2068 LEAP-C 1.0`) shows on the status row from power-on until the first key.
- **`NULL`** is predefined as `0`. A program may still define it itself once, or `#undef` it.
- **`SAVE` and `tape_save`** leave about a second of silence between the header and the data block, as the
  TS2068's own ROM does, so tools that convert tape recordings see two blocks.

**Fixed**
- In hi-res colour mode (`mode(1)`), `plot` and `draw` coloured the wrong pixel row (all but 24 of the 192 rows).
- Output that scrolls cleared each new bottom row in white paper instead of the program's colours.
- The letters `p`, `q` and `g` sat one pixel row high, so `p` looked like a capital `P`.

**Added for hosts**
- The emulator pack carries `symbols/leapc_home.sym` and `symbols/leapc_exrom.sym`.
- Two labels: `STMT_DO.cond` (where a `do … while` condition's code starts) and `SH_WAIT_KEY.key_ret` (the return
  address of the report's key wait).

**Documentation:** the user's manual (eight parts, Markdown and Word) corrected and completed after an audit
against the ROM; the screenshots retaken.

## 1.0.0-beta.2 (2026-10-22)

The ROMs are MIT throughout: the tape block routines and a block-graphics glyph, derived from the TS2068's ROM in
beta.1, rewritten clean-room. The tape loader is more tolerant (67 of 71 distorted test tapes, against 54).

## 1.0.0-beta.1 (2026-10-22)

The first public beta, on emulators.
