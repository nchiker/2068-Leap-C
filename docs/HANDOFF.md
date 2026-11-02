# Handoff: 1.2.0 released (after 1.0.0 and 1.1.0)

Written 2026-11-01, updated 2026-11-02 for 1.2.0. Read `docs/milestones/M13-draw.md`, `docs/milestones/M14-display.md`,
`docs/milestones/M12-cart.md` (the cartridge's milestone report), `docs/CARTRIDGE.md`,
`docs/milestones/M11-release.md` and the auto-memory.

**Owner rules in force:** lower-cost subagents for routine work and testing, always (`model: "haiku"` for runs,
`make` targets and mechanical edits; `"sonnet"` for doc writing, tools and tests); the main session keeps design,
analysis and debugging. Ask before publishing anything unless the owner has said to. Check
`pgrep -af "zesarux|/fuse"` before emulator runs; never kill another project's emulators. `make repro` runs
`make clean` in the working tree: never run it while another suite uses `build/`.

## State

- **1.2.0** released 2026-11-02 (GitHub release, latest; tag `v1.2.0` at `e5cc932`): the display code of 2068-Forth
  2.0, platform deltas D25-D29 (`draw()` 4.6-6.1x, `plot()` -25%, `print` 590 T a character, the scroll 1.8x, the
  idle interrupt 2,028 -> 225 T), the same pixels, screens and glyphs; banner `2068 LEAP-C 1.2`; HOME `510023ba…`,
  EXROM `14ee2434…`, cartridge HOME `505d0f79…`, identity `$F6E9`; HOME 607 B free. `make qualify` PASS, `make repro`
  OK. New gates: `make lines` (`tools/linetest.py`), `make display` (`tools/displaytest.py`), both in qualify.
  TSRun `main` serves it (`34b0794`). The Leap IDE was told in `~/Projects/Leap-IDE/docs/requests/LEAP_C_1_2.md`, with
  the six release files beside it in `leapc-1.2.0/` (all uncommitted there). Leap V2 ported D25 and D27 itself
  (`maint/v2.1.1`).
- **1.0.0** released 2026-11-01 (GitHub release, latest at the time); TSRun `main` serves its ROMs (`?rom=leapc`);
  the upstream TSRun PR (josef-jelinek/TSRun) was not opened (the owner asked only for the fast-forward).
- **1.1.0** = 1.0.0's ROM images unchanged + the runtime cartridge: `make cart` (`-DLEAPC_CART`: `src/cart/`,
  the LEAPC_CART parts of `src/rom/home.asm`), `make cart-demo`, `make test-cart` (`tools/carttest.py`),
  `tools/c2cart.py`, `tools/cartpack.py`, `tools/cart_check.py` (in `make check`), `tools/cart_build.py`
  (identity $E90E). Cartridge HOME `034e294d…`.
- The Leap IDE was told: `~/Projects/Leap-IDE/docs/requests/LEAP_C_CARTRIDGE.md` (new, uncommitted in that repo)
  and the Q5.5 edit of `LEAP_C_ANSWERS.md` (uncommitted there).

## Open

- Literal text in a `printf` format still prints a character at a time (`printf("12345")` 5,032 T against
  `print`'s 3,437): a possible later change.
- Not run on a physical TS2068 (neither the ROMs nor the cartridge). TSRun has not run a Leap-C cartridge.
- `tape_save`/`tape_load` from a cartridge are untested.
- The hand-off hazard (M12): an interrupt between the stock ROM's jump and `CART_ENTRY`'s `di`, with BREAK held and
  a nonzero stock-RAM byte at `RUNNING`, would unwind to `RUN_SP` 0. Not seen; a fix would cost release bytes.
- Two orphaned Fuse processes on `build/beta1` images (from 1.0's tapetol rerun) may still be running; this session
  was not allowed to stop them: `pgrep -af "2068-Leap-C/build/beta1"`.
