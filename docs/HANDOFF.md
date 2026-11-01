# Handoff: finish Leap-C 1.0.0, then the runtime cartridge

Written 2026-11-01 at the end of the 1.0 session. Read this, then `CHANGELOG.md`, `spec.md` (v0.14 changes line at
the top), and the auto-memory (`release-1-0-decisions`, `delegate-test-runs`, `leapc-test-harness`, `fuse-harness`).

**Owner decisions in force:** the 1.0 work is **accepted by the owner** (2026-11-01). Release 1.0 is qualified on
emulators only. **Use lower-cost subagents for routine work and testing, always**: every Agent call passes `model` explicitly,
`"haiku"` for test runs, `make` targets, searches and mechanical edits, `"sonnet"` where judgement is needed (doc
writing, test updates); results come back to the main session, which keeps design, analysis and debugging. Never
omit `model` (it then inherits the expensive main model). The owner has had to repeat this rule several times. 2068-Forth's tests use the same ZEsarUX ports
(10760-10766): check `pgrep -af "zesarux|/fuse"` first and run Leap-C suites with `--port 11760` when needed; never
kill another project's emulators (the long-lived one on port 10330 is unrelated).

## State at handoff

- `main` = `289576d` (pushed). The ROM work is `34420c2`: HOME `d2b18eaa…`, EXROM `02790ebe…`
  (`build/leapc_zesarux.bin` hash: see `build/SHA256SUMS` after `make build`).
- 1.0 contents: `NULL` predefined; one-row reports (row 23); the version banner `2068 LEAP-C 1.0`; platform deltas
  D22 (hi-res colour address), D23 (50-frame gap between tape blocks), D24 (`p`/`q`/`g` glyphs); scroll colours;
  the manual audited, corrected and with new screenshots; version strings 1.0.0; `CHANGELOG.md`.
- Passing: `make check`, the fast suite, all 33 tape cases, and **`make repro`: reproducible OK** on `34420c2`
  (HOME `d2b18eaa…`, EXROM `02790ebe…`, `leapc_zesarux.bin` `c0f7f76fbc3b89626a09db9a6ec8cc268525103a5fbb70c6ad527d805df39b7b`,
  `leapc_exrom.dck` `936ce1aa…`).
- **`make qualify`** was started on `e1aed5d` with `QUALIFY_PORT=12760 make qualify` (about 70-120 min).
  `QUALIFY_PORT` moves every ZEsarUX step off the default ports, so it runs alongside 2068-Forth's emulators;
  Fuse needs no port, and the end-of-run clean-up now kills only this repository's Fuse. Read
  `build/qualify_summary.log` and each failing step's `build/<step>.log`; if it is missing or incomplete, rerun the
  same way on a haiku agent. The Fuse suite (`make fuse`) was updated for the one-row report but had never run: a
  failure there is most likely a leftover two-row expectation in `tools/fusetest.py`, not a ROM defect. Check
  which before changing anything.
- **Interim result (12:30):** `final_test` failed 1 of its cases, everything else passed (exec, lexer, shell 44/44,
  e2e 47/47 + corpus 1164/1164 through RUN, float 5451/5451, poweron 949/949, tape 30/30). The one failure is the
  canary run of `tests/rt/break_malloc.c`: `ZRCPTransportError("timed out waiting for ZRCP reply")`, a harness
  timeout while 2068-Forth's suite was loading the machine; the same case passed in the corpus and e2e runs. Rerun
  that case alone on the canary path (quiet machine) before the release; if it passes, record it as a harness
  timeout in the qualification report. The Fuse step was still running at handoff.

## 1. Confirm today's issues are fixed in Leap-C

| Issue (filed for the other projects) | Leap-C's fix | Test |
|---|---|---|
| [nchiker/2068-Leap#5](https://github.com/nchiker/2068-Leap/issues/5): hi-res colour on the wrong pixel rows | platform delta D22 (`GFX_WRITE_PIXEL.ext_attr`: `set 5,h`) | `tests/lib/gfx/hires_colour_rows.c` |
| [nchiker/2068-Leap#6](https://github.com/nchiker/2068-Leap/issues/6), [nchiker/2068-Leap-Forth#18](https://github.com/nchiker/2068-Leap-Forth/issues/18): `p`, `q`, `g` one row high | platform delta D24 (font data) | none yet: add one |

**Do not change 2068-Leap or 2068-Forth:** the owner will have each project fix its own bugs. In Leap-C only:
confirm D22 and D24 are in the built ROM; add a glyph test for D24 (e.g. print `pqg` and compare the screen bytes
with the glyph table's rows 0-7 for those codes, or check rows 0-1 of each glyph are empty); and confirm Leap-C is
safe from 2068-Forth's second fix in `734a966` (`GFX_WRITE_PIXEL` writing RAM for y >= 192): `plot` goes through
`GFX_PLOT_CLIPPED` (returns for y >= 192), `draw` clamps its ends (`LIB_CLAMPY`), a loaded library's `LX_PLOT` is
`LIB_PLOT_HL`; add a test that `plot(10, 200)` and `draw(0, 180, 10, 250)` leave RAM below the screen unchanged.
Any new test is a test-only change (no new ROM hashes).

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
