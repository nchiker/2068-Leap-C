# Phase 11, third milestone — Release 1.0.0: qualification report

**Date:** 2026-11-01. **Status: complete.** Leap-C 1.0.0 is qualified on emulators. `make repro` reproduces the ROM hashes and every `make qualify` step passes; no ROM defect was found. The tag `v1.0.0` is made here; the GitHub release is created as a draft, and publishing it is the owner's step.

- **Baseline:** M11-tape (v1.0.0-beta.2), `spec.md` v0.13, ROMs HOME `043becf4…`, EXROM `97fe9523…`.
- **Result:** ROMs HOME `d2b18eaa6b3e100e80b1159aedc3a382a8c7ae552566205dab301739e8f3ef98`, EXROM `02790ebe3bf851a749b8ff6810db5bf76bd39518ebda7731b47b4a5239bc4847`, combined `leapc_zesarux.bin` `c0f7f76fbc3b89626a09db9a6ec8cc268525103a5fbb70c6ad527d805df39b7b`, `leapc_exrom.dck` `936ce1aab87cd4b54453c9ccfbfddf312816cb51ccf54f40760e2f68528f882b`. `spec.md` v0.14. The ROM work is commit `34420c2`.

## 1. Scope: the owner decisions of 2026-11-01

- **Emulator-only qualification.** No physical TS2068 is available. The hardware kit and checklist ship as in the betas; real-hardware results are welcome and not a condition of 1.0.
- **`NULL` predefined** as `0`.
- **The banner `2068 LEAP-C 1.0`** on the status row from power-on to the first key.
- **The screenshots retaken** for the manual (the manual audit, `docs/manual/`).
- **The runtime cartridge (`make cart`) after 1.0.**

The same day the user's manual was audited against the ROM and corrected (eight parts, Markdown and Word edition); the audit found the defects behind D22, D24 and `NULL`.

## 2. Changes

Ledger entries are in `budget.toml`; platform deltas in `platform/UPSTREAM.md`; the behaviour in `spec.md` v0.14.

| Change | Ledger | Platform | Bytes |
|---|---|---|---:|
| `NULL` predefined as `0`: `CC_COMPILE` puts a macro record in the global area before the first token, from a ROM template; `#undef NULL` can clear it | L78 (HOME, decl) | | +28 |
| A program may define `NULL` itself once: `PP_DEFINE` clears the oldest record and makes the new definition; a second definition is `ALREADY DEFINED` as before | L79 (EXROM, xcomp) | | +9 |
| Hi-res colour: `GFX_WRITE_PIXEL.ext_attr` writes the colour byte at the bitmap byte's address + `$2000` (`set 5,h`); V2's `GFX_SET_ATTR_EXT` and the y reconstruction are removed | L80 (HOME, platform) | D22 | −42 |
| A report is one row (row 23): `RUN` shows `ERROR n MESSAGE`, `RUNTIME ERROR n MESSAGE`, `BREAK` or `EXIT n`; the cursor shows the line; the undeclared name and the image size and heap are dropped; `FREE` shows `SOURCE s B  FREE f B` | L81 (EXROM, xshell) | | −212 |
| `DG_APPEND` writes `n MESSAGE` without a colon so the longest report (`ERROR 13 BAD CHARACTER CONSTANT`) fits the row in 31 characters | L82 (EXROM, xdiag) | | −4 |
| Output that scrolls paints the new row 23 in the print colours (`LIB_ATTR`) | L83 (HOME, library) | | +15 |
| The version on the status row from power-on, through the chime, to the first key (`SHELL_COLD`, `SH_VER_FLAG`, `SH_DRAW_STATUS`, `SH_REDRAW`) | L84 (EXROM, xshell) | | +54 |
| `STORAGE_SAVE` waits 50 frames between the header and the data block | L85 (EXROM, xplatform) | D23 | +6 |
| The glyphs of `p`, `q` and `g` on the x-height (rows 2-5), descender in rows 6-7 | none (data only) | D24 | 0 |
| Labels `STMT_DO.cond` and `SH_WAIT_KEY.key_ret`; the emulator pack carries `symbols/leapc_home.sym` and `symbols/leapc_exrom.sym` | none (zero bytes) | | 0 |

HOME reserve: 482 B (beta.2) to 481 B (L78 −28, L80 +42, L83 −15). EXROM reserve: 186 B to 333 B (L79 −9, L81 +212, L82 +4, L84 −54, L85 −6).

**Cross-reference.** The issues [nchiker/2068-Leap#5](https://github.com/nchiker/2068-Leap/issues/5) (hi-res colour on the wrong pixel rows), [#6](https://github.com/nchiker/2068-Leap/issues/6) and [nchiker/2068-Leap-Forth#18](https://github.com/nchiker/2068-Leap-Forth/issues/18) (`p`, `q`, `g` one row high) are fixed in Leap-C by D22 and D24. The other projects fix their own.

## 3. Qualification

ROM change: `make repro` first, then `make qualify` (2026-11-01, on `e1aed5d` with the test-tool fixes below), logs kept.

### 3.1 Results per suite

| Suite | Result |
|---|---|
| `make repro` | **reproducible OK** on `34420c2` and again on `12bbc34` (the tests and documents above; later commits change documents only): HOME `d2b18eaa…`, EXROM `02790ebe…`, `leapc_zesarux.bin` `c0f7f76f…`, `leapc_exrom.dck` `936ce1aa…` |
| Lexer | 113/113 |
| Declarations | 215/215 |
| Shell | 44/44 |
| Workflow (e2e) | 47/47 cases |
| Corpus through the shell's `RUN` | 1,164/1,164 |
| Float core against the bit-exact model | 5,451/5,451 |
| Power-on | 949/949 |
| Cassette (tape) | 30/30; with the fast tape all 33 cases |
| Fuse 1.9.1 | boot, keyboard, typed 39/39, break, frames, save, wav, lib, corpus **1,015/1,015** programs LOADed from tape and RUN (7 sessions, 824,529 frames) |
| Timing (Fuse against ZEsarUX) | 1.006-1.074 |
| Hardware kit (`hwkit.py`, 30-minute soak) | H1-H11 pass on both emulators |
| Tape tolerance (`tapetol.py`) | 67 of 71 distorted tapes accepted (beta.1 54; as beta.2) |
| RAM `warm` | pass (1,164/1,164) |
| RAM `random:7` | pass on rerun |
| Capacity | pass |
| `make check` | pass |

**ROM coverage** (`build/romcov.md`): HOME 7,536 of 7,552 instructions (99.8%), 440 of 440 routines entered; EXROM 3,345 of 3,362 (99.5%), 154 of 154 routines.

### 3.2 What happened in each `make qualify` step

`build/qualify_summary.log` says `FAIL`. That is because steps were killed and rerun by hand, not because a step failed on its last run. The record per step:

| Step | What happened | Final |
|---|---|---|
| `final_test` | Everything passed but one canary case, `tests/rt/break_malloc.c`: a `ZRCPTransportError` (no reply within the harness's 50 s) while 2068-Forth's suite loaded the machine. Rerun alone: the canary passes. A harness timeout under load, not the ROM. Exec, lexer, declarations, shell, e2e + corpus, float, power-on and tape results are the figures above | PASS |
| `fuse` | `libsdl2-dev` was missing, so the Fuse shim did not build and `fusetest.py` hung for 4.5 hours until killed. The owner installed the package. Rerun: all cases pass. The `frames` check now allows one frame of sampling jitter (two shim commands; it read +1 and −1) | PASS |
| `timing` | `timingcmp.py` read the old two-row report (row 22). Fixed to row 23 (`484f09a`). Rerun | PASS |
| `kit_verify` | `hwkit.py` read row 22 too. Fixed (`eb496a0`). Rerun, with the 30-minute soak | PASS |
| `tapetol` | `tapetol.py` read row 22 too. Fixed (`eb496a0`); it reads row 22 only for beta.1's two-row ROM, chosen by `SH_VER_FLAG` in the ROM's symbols. Rerun | PASS, 67 of 71 |
| `ram_warm`, `capacity`, `check` | passed in the run | PASS |
| `ram_random7` | The same harness timeout as `final_test` in the e2e step (load average about 7). Rerun with `--ram random:7`, e2e and canary: 3/3 pass | PASS |

No step failed on the ROM. Every rerun used the same ROM images.

## 4. Test-only changes after the qualification

No ROM change, so no new hashes.

- **A glyph test for D24:** `tests/lib/text/glyph_pqg.c`. The screen bytes of printed `p`, `q` and `g` equal the glyph table's, and rows 0 and 1 of each are empty.
- **Safe below the screen:** `tests/lib/gfx/plot_below_screen.c`. `plot(10, 200)` and `draw(0, 180, 10, 250)` leave `$5800-$5ABF` and `$7800-$7FFF` unchanged, in both modes. Leap-C is safe from the second fix 2068-Forth made in `734a966` (`GFX_WRITE_PIXEL` writing RAM for y ≥ 192): `plot` goes through `GFX_PLOT_CLIPPED`, which returns for y ≥ 192; `draw` clamps its ends with `LIB_CLAMPY`; a loaded library's `LX_PLOT` is `LIB_PLOT_HL`.
- **The worker pools hardened**, as 2068-Forth did (`tools/run_tests.py`, `tools/fusetest.py`, with `tools/lcharness.py`): a timeout on the result queue; a dead worker's task fails as "worker on port N died" instead of waiting forever (the cause of the 4.5-hour hang); the parent stops only its own workers' emulators, by pid, with a port and working-directory fallback. Verified by a simulated worker death.
- **Test tools reading row 23:** `timingcmp.py` (`484f09a`); `hwkit.py` and `tapetol.py` (`eb496a0`); the `frames` check's one-frame tolerance (`484f09a`).

After these changes (2026-11-01): the fast suite (`run_tests.py --fast`) **PASS**, 0 failures (exec lib 110/110 with the two new tests, decl 215/215, lexer 113/113, shell 42/42, e2e 47/47, float 1,876/1,876, power-on 144/144 boot checks and 479/479 corpus slices, canary 583 cases); `make fuse` **PASS**, 0 failures (typed 39/39, corpus 1,017/1,017 LOADed from tape and RUN, 7 sessions, 829,946 frames); no emulator left behind by either run. `make repro` on `12bbc34`: reproducible OK, the same four hashes. `make release` on `12bbc34`: the emulator pack (110 files, with `symbols/leapc_home.sym` and `symbols/leapc_exrom.sym`), the hardware kit (127 files), the two Word manuals, `SHA256SUMS`.

## 5. Deviations

- **Emulator-only.** Fuse 1.9.1 and ZEsarUX 13.0 with the EXROM patch. Nothing was run on a physical TS2068; the hardware kit's checks H1-H11 passed on both emulators only. This is the owner's decision (§1).
- The `make qualify` summary says `FAIL`; §3.2 records why.
- ZEsarUX cannot write `SAVE` (only Fuse saves); TSRun cannot load tapes. As in the betas.

## 6. Documents and release

`CHANGELOG.md` (1.0.0); `spec.md` v0.14; `platform/UPSTREAM.md` (D22-D24); `budget.toml` (L78-L85); the user's manual (`docs/manual/`, Markdown and `make manual` Word edition); `project_plan.md` §13; `docs/releases/v1.0.0.md` (the release notes, links pinned to the tag); this report. The assets (`make release`): the emulator pack with `symbols/`, the hardware kit, the Word manual, `SHA256SUMS`.

The annotated tag `v1.0.0` names the hashes; the GitHub release `v1.0.0` (not a pre-release) is created as a draft for the owner to publish; TSRun's copy of the ROMs is updated on a branch `leapc-1.0.0` for the owner to publish. The runtime cartridge follows 1.0.

Accepted by the owner 2026-11-01.
