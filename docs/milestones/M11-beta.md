# Phase 11, first milestone — Public beta 1.0.0-beta.1: milestone report

**Date:** 2026-10-22. **Status: complete up to the owner's steps.** The repository is prepared for a public beta on emulators, and release v1.0.0-beta.1 is prepared as a draft pre-release. The owner makes the repository public and publishes the release (§9). The ROM images are unchanged from Phase 10: HOME `ba8e0ab6…`, EXROM `9bd71cef…`.

- **Emulator instructions** (`docs/EMULATORS.md`) for Fuse 1.9.1, ZEsarUX 13.0 and TSRun on Windows, macOS and Linux, each procedure verified (on Linux) or marked "not checked by us" (§4). The verification found that **the downloadable ZEsarUX 13.0 cannot run Leap-C**: Leap-C's qualification ran on 13.0 with Leap V2's EXROM patch. By owner decision, Fuse is the recommended emulator, ZEsarUX is documented as 13.0 with the patch, built from source, and the patch is reported upstream.
- **Basic documentation:** `docs/USER_GUIDE.md`, `docs/BETA_TESTING.md`, a public `README.md`; their seven examples are tests (34 documentation examples in all).
- **The audit** of every tracked file and the whole history found no secret, token or absolute home path. Its findings and what was done about each are in §2. `Investigate/`, `spike/improvements/` and the unassembled `platform/rom/exrom_calc.asm` left the tree, by owner decision. The private improvements report is now in the repository. Code derived from the stock ROM is recorded in `NOTICE`.
- **Licensing:** `LICENSE` (MIT) and `NOTICE`.
- **A fresh clone builds** with only sjasmplus 1.23.1 and Python, in a clean environment, to the same hashes (§6). Every tool path is configurable (`LEAPC_*`, `CONTRIBUTING.md`).
- **GitHub files:** issue templates, a pull-request template, `CONTRIBUTING.md`, CI (§7).
- **The release:** `make release` builds the emulator pack and the hardware kit from a clean clone; the draft pre-release carries them with release notes (§8).

- **Baseline:** Phase 10 (`c8eab8f`, `docs/milestones/M10.md`), `spec.md` v0.12, ROMs HOME `ba8e0ab6…`, EXROM `9bd71cef…`.
- **Owner decisions (approval):** MIT for Leap-C, keeping the MIT notices of the vendored V2 platform and of the code derived from ts2068-debug; version v1.0.0-beta.1 as a GitHub pre-release; ZEsarUX 13.0 and Fuse 1.9.1 supported, other emulators untested; the history kept as it is; the owner makes the repository public, publishes the release and changes settings.
- **Owner decisions (during the milestone):** `Investigate/` removed from the tree; `spike/improvements/` removed (Fixes 1-5 are in the ROM, Fix 6 is recorded in M10); the stock-ROM-derived tape routines kept under an Amstrad notice (option A), with a clean rewrite planned after the beta (option C, `project_plan.md` §13); `platform/rom/exrom_calc.asm` removed; Fuse first, ZEsarUX with the patch, the patch reported upstream (a draft for the owner to post); TSRun's `?rom=leapc` prepared in the owner's TSRun fork and pushed with the release.
- **Kept as instructed:** the ROM code (comments only in two files; the images are byte-identical), every test, the history (no rewrite, no force-push); `~/2068-Leap` and `~/ts2068-debug` only read; the repository still private, the release a draft.

## 1. Completion criteria

| Criterion (the approval) | Result | Evidence |
|---|---|---|
| Emulator instructions for ZEsarUX 13.0 and Fuse 1.9.1 on Windows, macOS and Linux: getting them, ROMs by command line and menus, settings and why, a correct start, the keyboard, tapes both ways, 50/60 Hz, troubleshooting | **done**: `docs/EMULATORS.md`, with TSRun | §3, §4 |
| Every procedure verified, how and on which OS recorded; anything unverified marked | **done**: on Linux; Windows and macOS steps marked "not checked by us" | §4, `EMULATORS.md` §10 |
| The `.dck` verified in ZEsarUX or left out | **left out**: ZEsarUX refuses it | §4 |
| `USER_GUIDE.md`, `BETA_TESTING.md`, a public README; every example with expectations a test | **done**: 7 new examples, 34 in all, pass in every corpus suite | §3, §5 |
| The audit reported before changes; decisions with the owner | **done** | §2 |
| `LICENSE` (MIT) and `NOTICE` | **done** | §2 |
| A fresh clone builds with only the documented prerequisites; paths configurable and documented | **done** (a documentation defect found and fixed on the way) | §6 |
| Issue templates, pull-request template, `CONTRIBUTING.md`, description and topics prepared, CI | **done**; CI green on GitHub | §7 |
| Emulator pack and hardware kit from a clean clone, hashes matching `make repro`; a draft pre-release with notes; the tag | **done** | §8 |
| Qualification: ROM unchanged, but the harness, the doc tests and the kit tool changed, so the full run: `make repro`, then `make qualify`; and `make test-fast`, `make fuse` (in qualify), the fresh clone | **pass**, logs kept | §5 |
| `project_plan.md` updated; this report; committed and pushed (private) | **done** | |

## 2. The audit

**Scope:** every tracked file at `c8eab8f` (1,201 files) and every commit's content and message (14 commits, `git log -p --all`), searched for secrets (tokens, keys, passwords), personal data (names, e-mail addresses, machine names), absolute home paths, private links, and provenance; every binary file; every file ever added and later deleted.

| # | Finding | What was done |
|---|---|---|
| A1 | **No secret, token, key or password** in any file or commit. No binary file is tracked. | nothing to do |
| A2 | **The commits' author** is `charlie.day <charlie.day@pop-os.lan>` (14 commits; `pop-os.lan` is the development machine's local domain). The commit messages' trailers name `noreply@anthropic.com`. | reported, not rewritten (owner instruction). New commits keep the configured identity; the owner may set a GitHub no-reply address for future commits |
| A3 | **No absolute home path** (`/home/...`) anywhere in the history. `~/` defaults for sibling repositories and emulators in 9 tools and several documents. | the tools take `LEAPC_ZESARUX`, `LEAPC_TS2068_DEBUG`, `LEAPC_V2_REPO`, `LEAPC_FUSE` (defaults unchanged), documented in `CONTRIBUTING.md` (§6). Historical mentions in the milestone reports are kept |
| A4 | **A private link:** the improvements report (`https://claude.ai/artifact/...`, a private document) in `docs/milestones/M10.md`, `spike/improvements/README.md` and `PHASE10_PROMPT.md`. | the report's text is now `docs/history/IMPROVEMENTS_REPORT.md`, without its one diagram, which its own list describes; M10 points there. The two spike files left the tree (A6). The link stays in the history |
| A5 | **`Investigate/`**: one pre-specification planning document (27 KB), referenced by nothing. | removed from the tree (owner decision; it stays in the history) |
| A6 | **`spike/`**: the feasibility spike (needed: `make test`'s statement benchmark reads `spike/results/spike_results.json`, and the documents cite it) and `spike/improvements/` (the Phase 10 prototypes, their README and the owner's approval prompt). | `spike/improvements/` removed (owner decision: Fixes 1-5 are in the ROM and its history, Fix 6 is in M10); the rest stays as evidence |
| A7 | **Provenance: the vendored V2 platform** (`platform/`, nchiker/2068-Leap, public, MIT, © 2026 Charlie Day) and the tools derived from V2 (`lcharness.py`, `tapes.py`, `sjasm_strict.sh`, `make_dck.sh`) and from ts2068-debug (nchiker/2068-Debug, public, MIT: `lcharness.py` imports and subclasses its ZRCP client and process control). | `NOTICE` §1-2 |
| A8 | **Code derived from the stock ROM, in the shipped images:** `STORAGE_SEND_BLOCK` / `STORAGE_RECEIVE_BLOCK` (331 B of HOME) are V2's instruction-by-instruction port of the TS2068 ROM's SA-BYTES/LD-BYTES, which are Spectrum ROM code (Amstrad copyright; Timex's changes public domain per Fuse's ROM notes). A byte comparison of both images with the 48K, TC2068 HOME and EXROM ROMs found 7 runs of 12 B or more: five in these routines (119 B), two 12-byte block-graphics sequences (the stock PO-GR-2), and one 15-byte character test in the EXROM that is Leap-C's own `SH_IDCHAR` (the usual range-test idiom, written in Phase 5). Nothing else. | **owner decision: option A** — kept, under a `NOTICE` exception (Amstrad's permission to redistribute its ROM code free of charge; not for sale), with **option C** planned: a rewrite from the tape format's specification after the beta (`project_plan.md` §13). The same code is already public in 2068-Leap, whose `NOTICE.md` claims MIT for all of it: a suggested addition for V2 was drafted for the owner |
| A9 | **The font** (V2's `FONT_TABLE`, 94 glyphs): declared V2's own design. Compared with the 48K and TS2068 fonts: no glyph identical; six simple 5-pixel shapes (`a o x y z` and one punctuation mark) equal a stock glyph shifted one pixel. | recorded in `NOTICE` §1 as an original design |
| A10 | **`platform/rom/exrom_calc.asm`** (V2's calculator, 64 KB of source, not assembled since Phase 8): its header says the literal decoding and some operations are ported from the Spectrum ROM calculator. | removed from the tree (owner decision): `platform/MANIFEST`, `UPSTREAM.md` ("Not vendored"), the citations in `spec.md`, `fpcore.asm` and `exrom.asm` (comments) point at V2's tag. The float core that replaced it keeps only the 5-byte number format |
| A11 | **`tools/fuse/fuseshim.c`** loads into Fuse (GPL) at run time and declares one Fuse structure's layout; no Fuse source. | `NOTICE` §2 |
| A12 | **References only:** David Anderson's TS2068 ROM disassembly (2023) and skoolkid's Spectrum ROM disassembly are cited in comments; no content copied, no stock ROM image tracked. | `NOTICE` §4 |
| A13 | **The repository's links:** nchiker/2068-Leap, 2068-Debug and z80-skills are public. `docs/milestones/M9.md` and others name `~/fuse-build` and the development machine's ZEsarUX folder (historical). | kept: they describe how the qualification ran |

## 3. The documents

| Document | What it is |
|---|---|
| `docs/EMULATORS.md` | the emulators: which to use; Fuse 1.9.1 (getting it on each system, a verified Linux build from source, the command line, the menus, the settings and why); ZEsarUX 13.0 (why the patch, the build, the command line, the menus, the settings and why); TSRun; a correct start (pictures rendered from the emulator's screen memory, the chord) and wrong setups; the PC keyboard in each emulator and C's SYMBOL SHIFT chords; tapes (`LOAD ""`, `LIB "shapes"`, `SAVE` and back, `c2tape.py`, `lib2tape.py`); 50 and 60 Hz; troubleshooting; how each procedure was checked |
| `docs/USER_GUIDE.md` | the first program, the editor and its keys, the commands and their reports, the C subset with the differences from C89, the library (one line a function), floating point, graphics, sound and the keyboard, tapes, libraries, the error reports and the cursor, the limits; built from `spec.md`, `docs/EXAMPLES.md` and the README, no new design |
| `docs/BETA_TESTING.md` | what to try, what a report contains, the known limitations, the hardware kit for those with a TS2068 |
| `README.md` | public: what Leap-C is, the beta's status, a five-minute quick start, the documents, reporting, building, the licence. The previous README's build and layout content moved to `CONTRIBUTING.md` |
| `CONTRIBUTING.md` | prerequisites per target, the `LEAPC_*` variables, the make targets, the rules for changes, the layout |
| `LICENSE`, `NOTICE` | MIT; the provenance (§2) |
| `docs/history/IMPROVEMENTS_REPORT.md` | the Phase 9 improvements report (A4) |
| `docs/releases/v1.0.0-beta.1.md` | the release notes |
| `docs/images/` | the editor's three pictures |
| `project_plan.md` | Phase 11 is "Public beta, documentation and release qualification", this beta its first milestone; the manuals, the tape routines' rewrite, the final qualification and 1.0 after the beta |

**The examples are tests.** `tools/docexamples.py` now reads the three guides too: the README's first program and the user guide's six examples (floating point, graphics and sound, `inkey()` with a key fed, the `shapes` library, a compile error) are `tests/doc/readme_01.c` and `user_guide_01-06.c`, run by the corpus suites (directly, through `RUN`, under the canary, from power-on RAM, and LOADed from tape on Fuse). `tools/hwkit.py` takes only `docs/EXAMPLES.md`'s examples for the kit, so the kit's tapes are unchanged.

## 4. The emulator procedures: what was verified, and how

All on Pop!_OS 24.04 (Linux x86-64), 2026-10-22, with the beta's ROMs. Windows and macOS were not available: those steps are marked "not checked by us" in `docs/EMULATORS.md` §10, which has the full table.

| Finding or procedure | How | Result |
|---|---|---|
| **Stock ZEsarUX 13.0** | built from the tag `ZEsarUX-13.0` (a clone of the source), Leap-C started for 20 M instructions | **blank screen**, never reaches the editor (the harness's patched build: the editor). Leap V2's `EMULATOR_SETUP.md` documented the same; the qualification has always used the patched build |
| ZEsarUX 13.0 with the patch, as documented | a fresh clone from GitHub, the patch downloaded from V2's release tag, `./configure && make` | builds; Leap-C starts |
| The `.dck` cartridge | given to stock and patched ZEsarUX | stock: refused (ZEsarUX takes only DOCK-bank cartridges; ours is EXROM-bank) and blank; patched: no effect. **Left out of the beta** |
| ZEsarUX `SAVE` to a file | a program typed, `SAVE "zs"`, `--outtape` given | `SAVED zs`, **no file**: ZEsarUX's tape output works only through its traps on the stock routines |
| ZEsarUX tapes | the cassette suite (real-tape input; `c2tape.py`'s `.tap` and `.tzx` through ZEsarUX's own conversion) | pass (§5) |
| **Stock Fuse 1.9.1** | built from the official tarball (the harness's Fuse carries V2's ULAplus patch), `fusetest.py` boot, keyboard, typed (39), break, frames, save, wav, lib | **all pass** |
| Fuse built as documented | libspectrum 1.6.3 and Fuse 1.9.1 tarballs into a private prefix, `--with-sdl` (the first draft's `--with-sdl2` failed and was corrected) | builds; the same cases pass |
| Fuse command line, settings, tape steps | the suite's own launch (`--no-traps --no-auto-load`, other settings default) and its tape steps (open; Fuse starts the tape itself; record start/stop; write `.tzx`) | pass |
| Menu paths and labels | Fuse 1.9.1's `menu_data.dat` and manual; ZEsarUX 13.0's menu sources | from the sources, not clicked through |
| PC keys | Fuse's `keyboard.c`, ZEsarUX's keyboard handling, TSRun's `keyboard.js` | from the sources |
| **TSRun** | its emulation core run headless (Node) with the beta's ROMs; a program typed through its keyboard matrix; `LOAD ""` of a `.tzx` and a `.tap` | the editor and `RUN` work; tapes stop after 0.1 s (TSRun issue #3, open since V2 reported it) |
| The pictures | rendered from ZEsarUX's screen memory: cold start, the first program typed, after `RUN` | `docs/images/` |
| Download locations and versions | the projects' release pages | ZEsarUX 13.0 (9 June 2026) is the latest; Fuse 1.9.1 has Windows builds, Fuse for macOS 1.9.1, no Linux binary (most distributions package 1.6.0; 1.9.2 and 1.10.0 are newer) |

## 5. Qualification

The ROM images did not change (two ROM source files changed in comments only; the images are byte-identical: §8). But the harness (`tools/lcharness.py`: configurable paths), the documentation tests (`tools/docexamples.py`: seven new cases) and the kit tool (`tools/hwkit.py`) did, so the full qualification ran, as for a ROM change: **`make repro`, then `make qualify`, then `make test-fast`**, by a test subagent, on the working tree with every change. The logs are kept outside `build/`. **0 failures.**

| Step | Result |
|---|---|
| `make repro` | **reproducible**: images, libraries and tapes identical in two clean builds |
| `make qualify` (3,265 s) | **QUALIFY: PASS** |
| — `make test` with ROM coverage (1,405 s, 7 emulators) | **0 failures.** Lexer 113/113; declarations 215/215; the executable corpus **719/719** (doc 34, experr 66, expr 173, float 96, golden 47, lib 106, mem 30, pp 8, pperr 24, rt 18, run 13, stmt 68, stmterr 36); the float core against its model 5,451/5,451; shell 44/44; the workflow 47/47 (39 typed programs) and the corpus through `RUN` 921/921, every one of the 40 compile error numbers reported with the cursor on its line, 13.67 ms per line through `RUN`; the cassette suite; power-on RAM: 8 patterns, boot checks 144/144, corpus slices 706/706; the canary over 921 cases. **ROM coverage: HOME 7,572 of 7,588 instructions (99.8%), 437/437 routines; EXROM 3,401 of 3,420 (99.4%), 155/155 routines** |
| — `make fuse` (129 s) | **pass:** boot, keyboard, typed, BREAK, frames, SAVE, WAV, `lib`, and the corpus **780/780** LOADed from tape and RUN (578,159 frames: 161 emulated minutes at 60 Hz) |
| — `make timing` | pass: every report identical on both emulators; the documentation examples compile in 7.89 ms a line on ZEsarUX, 8.10 on Fuse |
| — `--ram warm`, `--ram random:7` | **0 failures** each (the corpus through `RUN` 921/921 from each) |
| — `make capacity` | pass (the Phase 10 table unchanged) |
| — the kit's verification with its 30-minute soak | **pass** on both emulators (H1-H11 from their WAVs; the soak's round count, which depends on wall time, updated in `docs/hardware/EMULATOR_RESULTS.md`) |
| — `make check` | **pass:** budgets (HOME 455 B free, EXROM 186 B), the platform (2 pristine, 12 with deltas, against the V2 tag), the RAM layout guard with its 8 negative controls, 34 documentation examples in step |
| `make test-fast` (171 s) | **pass** (0 failures) |
| Emulator-procedure checks (§4) | stock Fuse 1.9.1 and the documented Fuse build: boot, keyboard, typed 39/39, break, frames, save, wav, lib all pass; the documented ZEsarUX build boots; stock ZEsarUX 13.0 blank |

The production hashes (`build/SHA256SUMS`, unchanged since Phase 10):

```
ba8e0ab6bf277c03f969f8ac9e829a0c32665efe6bed1a12613555196e10a04a  leapc_home.bin
9bd71cefbd78fd80d449609c94d349a2671625f3b3642fd0380b6c8dbfbca47a  leapc_exrom.bin
f5f8eaff73928520bf2a971004bb42f06580071179445fd4336c6c1d8ab82af2  leapc_zesarux.bin
085d2725421cf4aef0854eae563c33cfd6bc46abdd36b0af4a170b45c8f5ae42  leapc_exrom.dck
```

The libraries: `shapes.bin` `c4c145cd…`, `shapes.tap` `a9129a8e…`, `shapes.tzx` `7fc9b555…`, `shapes.wav` `54da5796…`; `testlib.bin` `484c1bb8…`; `tiny.bin` `f8a93b5b…`.

## 6. The fresh clone

A clone of the release content into a scratch directory, built in an empty environment (`env -i`, a scratch `HOME` with no sibling repositories, `PATH` = system directories and a sjasmplus 1.23.1 built from source exactly as `CONTRIBUTING.md` says), following only the documents:

| Step | Result |
|---|---|
| sjasmplus 1.23.1 from source | the documented clone lacked `--recursive` and failed (LuaBridge is a submodule): corrected in `CONTRIBUTING.md` and the CI workflow, then built |
| `make` | pass |
| `make libs` | pass |
| `make check` | pass; the platform check without a V2 repository verifies every file and delta; with a fresh public clone of 2068-Leap (`LEAPC_V2_REPO`, as CI does) it also verifies the upstream hashes against the tag |
| `make repro` | pass, identical to the working tree's: HOME `ba8e0ab6…`, EXROM `9bd71cef…`, combined `f5f8eaff…`, and the libraries |

The release assets were then built the same way from a second fresh clone of the release content (`make`, `make kit`, `make release` in the empty environment): the zips are byte-identical to the working tree's, their ROMs have the hashes above, and the emulator pack's own `SHA256SUMS` verifies after unpacking.

## 7. GitHub project files

- `.github/ISSUE_TEMPLATE/bug_report.yml` (the emulator, its version and how it was started, the OS, the ROM hashes, the program or tape, the steps, what happened, a screenshot), `question.yml`, `config.yml` (blank issues off; links to the beta guide and the emulator guide);
- `.github/pull_request_template.md`;
- `.github/workflows/ci.yml`: Python 3.11, sjasmplus v1.23.1 built from its tag (cached), a clone of 2068-Leap for the platform check, `make`, `make check`, `make repro`. The emulator suites stay local.

CI ran on GitHub (the private repository) on this milestone's content (run 39805337750, Ubuntu 24.04): **success**: sjasmplus 1.23.1 built from its tag, `make`, `make check` (the platform verified against a fresh clone of 2068-Leap), `make repro`, and the release images' hashes as above.

**Repository settings, prepared, not applied** (the owner applies them):

- Description: `A C compiler and full-screen editor in the ROMs of the Timex Sinclair 2068: type C, RUN compiles it to native Z80 on the machine. Public beta.`
- Website: `https://nchiker.github.io/TSRun/?rom=leapc`
- Topics: `timex-sinclair-2068`, `ts2068`, `zx-spectrum`, `z80`, `c-compiler`, `retrocomputing`, `rom`, `z80-assembly`, `sjasmplus`, `8-bit`, `emulator`

## 8. The release

`make release` (`tools/release.py`) builds two reproducible zips (sorted entries, fixed times and modes) in `build/release/`:

| Asset | Size | SHA-256 |
|---|---:|---|
| `leapc-1.0.0-beta.1-emulators.zip` | 126,513 B | `bdfdb3a8ecf6005e1c8dc2f68106b8f4f3f508dd05c3cea535d4038cd9401b47` |
| `leapc-1.0.0-beta.1-hardware-kit.zip` | 420,809 B | `2681b488f520b1cad7d0dea80243bcdf8e44b173b5e3118eeb08c34613e0287d` |
| `SHA256SUMS` | | the two lines above |

- **The emulator pack** (106 files): `roms/` (`leapc_home.bin`, `leapc_exrom.bin`, `leapc_zesarux.bin`), `tapes/examples/` (`ex01-27` from `EXAMPLES.md`, `ug01-06` from `USER_GUIDE.md`, as `.tap` and `.tzx`), `tapes/checks/` (H1-H11), `libs/` (`shapes.tap`, `.tzx`, `.asm`), `docs/` (EMULATORS, USER_GUIDE, BETA_TESTING, EXAMPLES, the pictures), `TAPES.md` (each tape's name, source and needs), `README.txt`, `LICENSE`, `NOTICE`, `SHA256SUMS`. The `.dck` is left out (§4).
- **The hardware kit** (127 files): `build/kit` as Phase 9-10 built it (the EPROM images `leapc_home_27128.bin`/`.hex` and `leapc_exrom_2764.bin`/`.hex`, every tape as `.tap`, `.tzx`, `.wav`, `HARDWARE_CHECKLIST.md`, `EMULATOR_RESULTS.md`, `CHECKSUMS.txt`), `LICENSE`, `NOTICE`.
- **Release notes:** `docs/releases/v1.0.0-beta.1.md` (what Leap-C does, how it was qualified, what is known not to work, how to report, the licence), from `docs/milestones/M1.1-M10.md` and this report.
- **The draft pre-release** `v1.0.0-beta.1` (`gh release create --draft --prerelease`) carries the two zips and `SHA256SUMS`; the annotated tag `v1.0.0-beta.1` is on this milestone's commit. A draft is visible only to the repository's owner and collaborators.

## 9. What the owner does next

Prepared for the owner (`docs/milestones/M11-beta.md` is the record; the commands are in the hand-off): the list of what becomes public, the commands that make the repository public, apply the description and topics, publish the release, and push and propose TSRun's `?rom=leapc`; a draft issue for ZEsarUX's EXROM mapping and a suggested `NOTICE.md` addition for 2068-Leap, both for the owner to post.

Posted during the milestone at the owner's request (upstream TSRun, from the owner's account): PR #4, the 2068-Leap V2 v2.0.2-emu.1 ROMs replacing the preview ROMs (josef-jelinek/TSRun#4), and issue #5, a request for recording the tape output (josef-jelinek/TSRun#5), since no emulator but Fuse can save Leap-C's tapes to a file (ZEsarUX's tape output is trap-only; TSRun has no recorder).
