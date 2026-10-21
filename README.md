# 2068-Leap-C

A C language ROM set for the original Timex Sinclair 2068 (48 KB, stock HOME/EXROM banking). It has a full-screen source editor and an on-machine, single-pass, Small-C-style compiler that generates native Z80 code. It is built on the platform services of Leap V2.

- **What is built:** `spec.md` (v0.10).
- **By example:** `docs/EXAMPLES.md` (every example there is a test).
- **How and in which order:** `project_plan.md` (v0.1).
- **Why:** `docs/C_FEASIBILITY_STUDY.md` (closed).
- **Progress:** one report per milestone in `docs/milestones/`.

**Status:** Phase 8 (language and library completion) is complete (`docs/milestones/M8.md`). **Floating point is in Release 1:** `float` and `double` (one type, the Sinclair 5-byte format: about 9.6 digits, up to 1.7E38), floating constants, conversions, arithmetic and comparisons, float arguments and results, constant folding, and `printf`'s `%f` / `%.Nf`. It runs on the float core, the V2 calculator re-engineered into a smaller engine that replaces it. Phase 8 also completed the initialisers of `spec.md` §4.7, tested the library's remaining edge cases, reports a missing `;` at the line that lacks it, and made the documentation's examples tests.

Phases 1-7 are also complete: the compiler, the runtime and library, the memory layout and banking, the editor with C punctuation and keyword highlighting, the compile/run workflow (`RUN` with its reports, `FREE`), and the cassette (`SAVE`, `LOAD`, `VERIFY`, `tape_save`, `tape_load`, `tools/c2tape.py`). The next phase is Phase 9 (emulator and physical hardware validation).

Typing a program: letters as usual (CAPS SHIFT for capitals), SYMBOL SHIFT for punctuation, with SYMBOL SHIFT + Y `[`, U `]`, F `{`, G `}`, S `|`, A `~`, H `^`, D `\`. CAPS SHIFT + 5/6/7/8 move the cursor, + 0 deletes, + 1 deletes the line, + ENTER inserts a line; `RUN`, `LIST`, `FREE`, `NEW`, `SAVE "name"`, `LOAD "name"` (or `LOAD ""`) and `VERIFY "name"` are typed on the empty line after the last; a key ends a report. SPACE (or BREAK) stops a tape transfer.

## Build and test

Needs sjasmplus 1.23, Python 3.11 or later, and, for `make test`, ZEsarUX 13.0 in `~/Applications/ZEsarUX-13.0`, `~/ts2068-debug`, and the frozen Leap V2 repository `~/2068-Leap` (read only: `tools/v2ref.sh` builds the V2 reference ROM from its tag for the cross-version tape tests).

```sh
make            # build/leapc_home.bin, leapc_exrom.bin, leapc_zesarux.bin, leapc_exrom.dck (+ build/test/)
make check      # strict assembly, ROM budgets (budget.toml), vendored-platform delta check, RAM layout guard,
                # documentation examples in step with tests/doc/
make budget     # per-component budget table and ROM map
make inventory  # every HOME routine, table and gap with its referrers
make test       # ZEsarUX: boot tests (both images), lexer, declaration and executable C tests, measurements,
                # the shell (editor, keys, glyphs, typing cost), the RUN workflow (typed programs, the corpus
                # through RUN, diagnostics, reports), the cassette (real tape signals) and the canary: one
                # pool of emulators
make test-fast  # the development subset (about 2 minutes): no cassette, no corpus through RUN, the canary over
                # every other program; make test stays the acceptance gate
make canary     # the RAM canary and banking invariants over the whole corpus, on its own
make capacity   # the measured capacity table (build/capacity.json)
make repro      # two clean builds must give identical hashes
python3 tools/c2tape.py prog.c prog.tap   # a program tape for LOAD (.tap or .tzx)
```

Run in ZEsarUX: `zesarux --machine TS2068 --romfile build/leapc_zesarux.bin`.

The test harness starts ZEsarUX with `--emulatorspeed 1000 --frameskip 49` (about 2.4 times faster; the emulated machine's timing, and so every T-state measurement, is unchanged); `LEAPC_REALTIME=1` runs it at real speed.

## Layout

| Path | Contents |
|---|---|
| `platform/` | Leap V2 platform sources, vendored from tag `v2.0.1-emu.1` (see `platform/UPSTREAM.md`) |
| `src/rom/` | the HOME and EXROM images |
| `src/compiler/` | the compiler: lexer (M1.1); symbol table, declarations, types, initialisers, function bodies (M1.2); expressions, code generator, constant folding (EXROM) (M1.3); statements, preprocessor (Phase 2); the library's names (EXROM) (Phase 3); the keyword lookup, type equality and directives (EXROM, Phase 8) |
| `src/runtime/` | the helper core (incl. multiply, divide, `switch`), program start and exit, BREAK, runtime errors, the library; floating point: `float.asm` (HOME) and the float core `fpcore.asm` (EXROM, Phase 8) |
| `src/shell/` | the EXROM shell (Phase 5): the editor's glue, commands, RUN and its reports (`shell.asm`), C keyword highlighting (`highlight.asm`), the error messages (`diag.asm`, Phase 6; its table is generated from `include/leapc_errors.inc` by `tools/gen_diag.py`), the cassette commands and the library's tape service (`tape.asm`, Phase 7) |
| `src/test/` | test-build-only hooks (`-DLEAPC_TEST`) |
| `include/` | RAM layout, cells, tokens, errors, build configuration |
| `tests/` | test corpus (C sources with expectation headers): `lexer/`, `decl/`, `expr/` (incl. `gen/`, generated by `tools/gen_exprtests.py`), `experr/`, `golden/`, `run/`, `stmt/` (incl. `gen/`, generated by `tools/gen_stmttests.py`), `stmterr/`, `pp/`, `pperr/`, `lib/` (the library; `lib/tape/` the tape functions without a tape), `rt/` (runtime errors, BREAK, soak), `mem/` (memory layout: image regions, `#pragma hires`, stack, heap), `float/` (floating point; `float/gen/` generated by `tools/gen_floattests.py`), `doc/` (the documentation's examples, generated by `tools/docexamples.py`), `spike/`, `bench/`. The cassette's own cases, which need tapes, are in `tools/tapetest.py` |
| `tools/` | build, budget, check and test tools; `c2tape.py` (host: a `.c` file to a program tape), `tapes.py` (tape files and signals for the tests and the host tools), `fpmodel.py` (a bit-exact model of the float core), `docexamples.py` (the documentation's examples as tests) |
| `spike/` | feasibility code-shape spike, kept as evidence |
