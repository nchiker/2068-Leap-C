# Handoff: 1.0.0 ready to publish; the runtime cartridge's plan awaits approval

Written 2026-11-01, end of the release session. Read this, then `docs/milestones/M11-release.md` (the
qualification report), `docs/milestones/M12-cart.md` (the cartridge plan) and the auto-memory
(`release-1-0-decisions`, `delegate-test-runs`, `leapc-test-harness`, `fuse-harness`).

**Owner rules in force:** lower-cost subagents for routine work, always: every Agent call passes `model`
explicitly (`"haiku"` for test runs, `make` targets, searches and mechanical edits; `"sonnet"` for doc writing and
test updates); design, analysis and debugging stay in the main session. **Ask the owner before publishing
anything** (pushes, tags, releases, PRs, TSRun's Pages). 2068-Forth's tests use ports 10760-10766: check
`pgrep -af "zesarux|/fuse"` first and use `--port 11760` when needed; never kill another project's emulators.

## Done this session (local; nothing pushed)

- **The qualification checked:** `build/qualify_summary.log` says FAIL only because steps were killed and
  rerun by hand; every step passes (record per step: M11-release §3.2).
- **Today's issues confirmed fixed in Leap-C** (2068-Leap and 2068-Forth untouched): D22 (`set 5,h` at
  `GFX_WRITE_PIXEL.ext_attr`) and D24 (the p/q/g glyphs) are in the built HOME. New tests:
  `tests/lib/text/glyph_pqg.c` (D24) and `tests/lib/gfx/plot_below_screen.c` (`plot(10,200)`,
  `draw(0,180,10,250)` leave `$5800-$5ABF` and `$7800-$7FFF` unchanged in both modes; Leap-C is safe from
  2068-Forth `734a966`'s second fix).
- **Worker pools hardened** (`run_tests.py`, `fusetest.py`, `lcharness.py`): queue timeouts, dead workers'
  tasks fail as "worker on port N died", the parent stops only its own emulators (pid, then a port /
  working-directory fallback). Verified with a simulated worker death (`os._exit` in a task): the run ends, the
  task fails, no emulator left.
- After these: fast suite PASS, `make fuse` PASS (corpus 1017/1017), `make repro` OK on `12bbc34` (the same four
  hashes), `make release` built `build/release/` (emulator pack with `symbols/`, hardware kit, two Word manuals,
  `SHA256SUMS`).
- **Release documents:** `docs/releases/v1.0.0.md`, `docs/milestones/M11-release.md`, `project_plan.md` §13.
- **Tag `v1.0.0`** (annotated, naming the hashes) on the release commit, **local only**.
- **TSRun:** branch `leapc-1.0.0` (`9f9bbc5`, from `origin/main` `11731e1`) with `roms/leapc-0.rom` /
  `leapc-1.rom` = the release's `leapc_home.bin` / `leapc_exrom.bin`, `roms/README.md` and `README.md`. Local only.
- **Leap IDE:** `docs/requests/LEAP_C_ANSWERS.md` updated for 1.0 (one-row report; committed by someone in the
  IDE repo as `9d0a9f5`); a later edit to Q5.5 (the cartridge's report) is left uncommitted there.

## Waiting for the owner

1. **Push** `main` and the tag `v1.0.0` to origin.
2. **Create the GitHub release** `v1.0.0` as a **draft** (not a pre-release), notes `docs/releases/v1.0.0.md`,
   assets: everything in `build/release/`. Then the owner publishes it (and marks it latest).
3. **TSRun:** push `leapc-1.0.0`, fast-forward `main` (publishes the Pages site), check `?rom=leapc` boots to
   `2068 LEAP-C 1.0`, then the upstream PR to josef-jelinek/TSRun (beta.2's was #6).
4. **Approve (or change) the cartridge plan** `docs/milestones/M12-cart.md`; its §9 lists four decisions. Build
   nothing before that.

## Loose ends

- Two orphaned Fuse processes of this repository (from the tapetol rerun's beta1 images, parent pid 1, full CPU)
  were still running at the end of the session; the session was not allowed to kill them. Check
  `pgrep -af "2068-Leap-C/build/beta1"` and stop them.
