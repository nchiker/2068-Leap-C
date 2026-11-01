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
