# Handoff: 1.0.0 and 1.1.0 (the runtime cartridge) released

Written 2026-11-01. Read `docs/milestones/M12-cart.md` (the cartridge's milestone report), `docs/CARTRIDGE.md`,
`docs/milestones/M11-release.md` and the auto-memory.

**Owner rules in force:** lower-cost subagents for routine work and testing, always (`model: "haiku"` for runs,
`make` targets and mechanical edits; `"sonnet"` for doc writing, tools and tests); the main session keeps design,
analysis and debugging. Ask before publishing anything unless the owner has said to. Check
`pgrep -af "zesarux|/fuse"` before emulator runs; never kill another project's emulators. `make repro` runs
`make clean` in the working tree: never run it while another suite uses `build/`.

## State

- **1.0.0** released 2026-11-01 (GitHub release, latest at the time); TSRun `main` serves its ROMs (`?rom=leapc`);
  the upstream TSRun PR (josef-jelinek/TSRun) was not opened (the owner asked only for the fast-forward).
- **1.1.0** = 1.0.0's ROM images unchanged + the runtime cartridge: `make cart` (`-DLEAPC_CART`: `src/cart/`,
  the LEAPC_CART parts of `src/rom/home.asm`), `make cart-demo`, `make test-cart` (`tools/carttest.py`),
  `tools/c2cart.py`, `tools/cartpack.py`, `tools/cart_check.py` (in `make check`), `tools/cart_build.py`
  (identity $E90E). Cartridge HOME `034e294d…`.
- The Leap IDE was told: `~/Projects/Leap-IDE/docs/requests/LEAP_C_CARTRIDGE.md` (new, uncommitted in that repo)
  and the Q5.5 edit of `LEAP_C_ANSWERS.md` (uncommitted there).

## Open

- Not run on a physical TS2068 (neither the ROMs nor the cartridge). TSRun has not run a Leap-C cartridge.
- `tape_save`/`tape_load` from a cartridge are untested.
- The hand-off hazard (M12): an interrupt between the stock ROM's jump and `CART_ENTRY`'s `di`, with BREAK held and
  a nonzero stock-RAM byte at `RUNNING`, would unwind to `RUN_SP` 0. Not seen; a fix would cost release bytes.
- Two orphaned Fuse processes on `build/beta1` images (from 1.0's tapetol rerun) may still be running; this session
  was not allowed to stop them: `pgrep -af "2068-Leap-C/build/beta1"`.
