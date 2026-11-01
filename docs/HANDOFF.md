# Handoff: finish Leap-C 1.0.0, then the runtime cartridge

Written 2026-11-01 at the end of the 1.0 session. Read this, then `CHANGELOG.md`, `spec.md` (v0.14 changes line at
the top), and the auto-memory (`release-1-0-decisions`, `delegate-test-runs`, `leapc-test-harness`, `fuse-harness`).

**Owner decisions in force:** the 1.0 work is **accepted by the owner** (2026-11-01). Release 1.0 is qualified on
emulators only. Use lower-cost subagents (pass `model: "haiku"` for runs and mechanical work, `"sonnet"` where
judgement is needed) for routine work, with results reported back. 2068-Forth's tests use the same ZEsarUX ports
(10760-10766): check `pgrep -af "zesarux|/fuse"` first and run Leap-C suites with `--port 11760` when needed; never
kill another project's emulators (the long-lived one on port 10330 is unrelated).

## State at handoff

- `main` = `289576d` (pushed). The ROM work is `34420c2`: HOME `d2b18eaa…`, EXROM `02790ebe…`
  (`build/leapc_zesarux.bin` hash: see `build/SHA256SUMS` after `make build`).
- 1.0 contents: `NULL` predefined; one-row reports (row 23); the version banner `2068 LEAP-C 1.0`; platform deltas
  D22 (hi-res colour address), D23 (50-frame gap between tape blocks), D24 (`p`/`q`/`g` glyphs); scroll colours;
  the manual audited, corrected and with new screenshots; version strings 1.0.0; `CHANGELOG.md`.
- Passing: `make check`, the fast suite, all 33 tape cases. **`make repro` and `make qualify` were started on
  `34420c2`** by a background agent. Read `build/qualify_summary.log` (each step's log is `build/<step>.log`). If
  it is missing, incomplete or shows a failure, rerun (`make repro`, then `make qualify`, about 70-120 min). The
  Fuse suite (`make fuse`) had been updated for the one-row report but never run before this qualification: a
  failure there is most likely a leftover two-row expectation in `tools/fusetest.py`, not a ROM defect. Check
  which before changing anything.

## 1. Resolve the issues reported today

| Issue | What | Fix |
|---|---|---|
| [nchiker/2068-Leap#5](https://github.com/nchiker/2068-Leap/issues/5) | V2: `MODE 1` colours on the wrong pixel rows (`GFX_SET_ATTR_EXT`) | as Leap-C D22: `.ext_attr` does `set 5,h` and stores the attribute; remove `GFX_SET_ATTR_EXT` |
| [nchiker/2068-Leap#6](https://github.com/nchiker/2068-Leap/issues/6) | V2: `p`, `q`, `g` glyphs one row high | as Leap-C D24 (bytes in the issue) |
| [nchiker/2068-Leap-Forth#18](https://github.com/nchiker/2068-Leap-Forth/issues/18) | Forth: the same glyphs, `kernel/graphics/font.asm` | the same bytes |

The owner asked for these to be resolved. Do each **in its own repository** (`~/2068-Leap`, `~/2068-forth`),
following that project's own rules (read its CLAUDE.md / HANDOFF / CONTRIBUTING first: V2 is a released product
with its own budget ledger, tests and release process; Forth has its own milestone and CHANGELOG conventions). Add a
test that fails before the fix (V2: a `MODE 1` PLOT on rows 1 and 8 with different inks, as Leap-C's
`tests/lib/gfx/hires_colour_rows.c`; glyphs: a screen/glyph check). Run that project's suite, commit with
`Fixes #n`, push, and confirm the issue closed. Leap-C itself is not changed by this step (its copy of V2's
platform is frozen at `v2.0.1-emu.1`; it already has D22 and D24). Also check whether V2 has 2068-Forth's second
fix from `734a966` (`GFX_WRITE_PIXEL` writing RAM for y ≥ 192): V2's `PLOT` clamps x; verify y, `DRAW` and the
shapes module before claiming either way, and mention the result in the #5 fix.

Also reply in the Leap IDE repo if useful: `~/Projects/Leap-IDE/docs/requests/LEAP_C_ANSWERS.md` was written
before the one-row report; its Q2 says the report is detected at `SH_WAIT_KEY.key_ret` (still true) and quotes
the two-row report's figures in Q2.4/Q2.5 context. Update that file for 1.0 (one-row report, no `LINE m`,
`SH_ERR_LINE`/`SH_IMAGE_SIZE` unused) and point to `CHANGELOG.md`'s stable-name list.

## 2. Release v1.0.0

Only after `make qualify` passes and `make repro` matches.

1. **Release notes** `docs/releases/v1.0.0.md`, in the shape of `docs/releases/v1.0.0-beta.2.md` (links pinned to
   the `v1.0.0` tag): what changed since beta.2 (from `CHANGELOG.md`), the assets, the ROM hashes, how it was
   qualified (figures from the qualify logs: corpus counts, Fuse cases, coverage from `build/romcov.md`, tapetol
   result), known limitations (not on a physical TS2068; ZEsarUX needs the EXROM patch and cannot write `SAVE`;
   TSRun cannot load tapes; the language's limits; `draw` clamps off-screen ends to the edge, which changes a
   diagonal's slope).
2. **Qualification report** `docs/milestones/M11-release.md` in the style of `docs/milestones/M11-tape.md`: scope
   (the owner decisions of 2026-11-01), every change with its ledger entry, the test results per suite, hashes,
   deviations (emulator-only), and "accepted by the owner 2026-11-01". Update `project_plan.md` §13 (after the beta:
   done) and its 1.0 completion criteria.
3. `make release` (builds `build/release/`: the emulator pack with `symbols/`, the hardware kit, the Word manual,
   `SHA256SUMS`). Check the emulator zip lists `symbols/leapc_home.sym` and `symbols/leapc_exrom.sym`.
4. Commit, push, then **tag** `v1.0.0` (annotated, message naming the hashes) and push the tag. Create the GitHub
   release `v1.0.0` (not a pre-release) with the notes and the assets from `build/release/`, marked latest. The
   owner reserves publishing: create it as a **draft** and tell the owner it is ready, unless the owner says to
   publish.

## 3. Update TSRun's copy of the ROMs

`~/TSRun` (fork `nchiker/TSRun`, GitHub Pages serves `main`; upstream `josef-jelinek/TSRun`). The beta.2 update was
branch `leapc-beta2`, commit `d203645`: `roms/leapc-0.rom` = `leapc_home.bin`, `roms/leapc-1.rom` =
`leapc_exrom.bin`, copied unchanged from the release's emulator zip; `roms/README.md` (the version, the release
link, the two SHA-256s) and the top `README.md` line. Do the same on a branch `leapc-1.0.0` from `main`, then ask
the owner before fast-forwarding `main` (that publishes the Pages site) and before opening the upstream PR (beta.2's
was josef-jelinek/TSRun#6). Check `?rom=leapc` boots to the `2068 LEAP-C 1.0` banner in the served page if a browser
tool is available.

## 4. The runtime cartridge (`make cart`)

Promised to the Leap IDE (`~/Projects/Leap-IDE/docs/requests/LEAP_C_ANSWERS.md` Q5; the IDE's design for V2:
`~/Projects/Leap-IDE/docs/LEAP_CARTRIDGE_BUILD.md`, `cartridge-build/Docs/CARTRIDGE_STATUS.md`). 2068-Forth built
its own in `82af031` ("make cart runs Forth and a SAVE-LIB program from the DOCK of a stock TS2068"): read it first,
it is the nearest model. Start with a written plan for owner approval (a milestone file), then build. Requirements
already agreed:

- A build flag and `make cart` in this repository; the release ROM images do not change.
- A compiled program runs on a **stock** TS2068 (stock HOME and EXROM installed) from a DOCK cartridge: Leap-C's
  HOME in DOCK chunks 0-1, its EXROM in DOCK chunk 6, an LROS header at DOCK `$0000` (bytes 0-4: type `$01`,
  entry, chunk spec), the program image in DOCK chunks 4-5 (16 KB; chunk 2 too if an image is larger), copied to
  RAM (image regions in chunks 3, 6, 7) and run by `RT_RUN`.
- **Hard constraint:** compiled code calls absolute HOME addresses, and the IDE compiles with the release ROM. The
  cartridge HOME must keep every routine at the release address: same-size patches only, and the build compares
  the two `.sym` files. Known patches: `BANK_PAGE_EXROM_IN` (`$FF` bit 7 left 0, `$F4 = $43`), `BANK_PAGE_EXROM_OUT`
  (`$F4 = $03` at depth 0; today a 1-byte `xor a`: needs a same-size rearrangement), `IO_KEY_SCAN_ROW` moved out of
  `$0004` (the LROS header overlaps it; only the keyboard scan calls it). The entry stub starts with `di`.
- The EXROM is needed at run time (float core, `beep`/`sound`, `tape_save`/`tape_load`); the shell is not. After
  the program: a one-row report as the shell's (`EXIT n`, `RUNTIME ERROR n MESSAGE`, `BREAK`), then a key restarts.
- The image format (IDE proposal): a header (signature, format, ROM identity, entry) then `[address, length,
  bytes]` blocks per used region (code from the low end, static data from the high end) and a loaded library's
  region 3. Identity: a CRC-16 over HOME + EXROM computed at build time (0 ROM bytes), published with the release.
- Tests: boot the cartridge on Fuse with stock ROMs (see `fuse-harness` memory; 2068-Forth's `cartdiff`/Fuse tools
  for the DOCK) and on ZEsarUX; run a corpus slice; compare screens with the same programs under the full ROM.
- When done: tell the Leap IDE (a note in `~/Projects/Leap-IDE/docs/requests/`) with the image format and the
  `make cart` usage.
