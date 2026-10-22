# Contributing to 2068-Leap-C

Bug reports, test results (from emulators and especially from real TS2068s), documentation fixes and code are welcome. For reports, see [docs/BETA_TESTING.md](docs/BETA_TESTING.md) and the issue templates. This page is for building and changing Leap-C.

## Prerequisites

| For | You need |
|---|---|
| `make`, `make libs`, `make check`, `make repro`, `make budget`, `make inventory`, `make kit` | **[sjasmplus](https://github.com/z00m128/sjasmplus) 1.23.1** (exactly: the images are byte-reproducible with it), **Python 3.11** or later, GNU make, a POSIX shell, `sha256sum` |
| `make test`, `make test-fast`, `make canary`, `make capacity`, `make poweron` (the ZEsarUX suites) | ZEsarUX 13.0 **built with the EXROM patch** ([docs/EMULATORS.md](docs/EMULATORS.md) §3.1), [ts2068-debug](https://github.com/nchiker/2068-Debug) (a checkout: its ZRCP client is imported), `stdbuf` (GNU coreutils), Linux |
| `make test` (the cassette suite's cross-version tests), `make v2ref`, the platform check against the V2 tag | a clone of [2068-Leap](https://github.com/nchiker/2068-Leap) (read only: the V2 reference ROM is built from its tag `v2.0.1-emu.1` with `git archive`) |
| `make fuse`, `make timing` | Fuse 1.9.1 built from source and **not stripped** ([docs/EMULATORS.md](docs/EMULATORS.md) §2.1; the harness finds Fuse's internals by symbol), gcc, the SDL2 development files, `nm`; optionally `tzxlist` (fuse-utils) |
| `make kit` verification (`python3 tools/hwkit.py --verify`) | both emulators; optionally `audio2tape` (fuse-utils) |
| `make audit` | [z80-skills](https://github.com/nchiker/z80-skills) |

sjasmplus 1.23.1 from source: `git clone --recursive --branch v1.23.1 https://github.com/z00m128/sjasmplus.git && cd sjasmplus && make && sudo make install` (it needs a C++17 compiler; `--recursive` fetches the submodules it builds with) (or put the `sjasmplus` binary on your `PATH`).

### Where the tools are: environment variables

The tools find the emulators and sibling repositories through these variables. Each defaults to the layout of the original development machine.

| Variable | Default | Used by |
|---|---|---|
| `LEAPC_ZESARUX` | `~/Applications/ZEsarUX-13.0` | the ZEsarUX suites (`tools/lcharness.py`): the folder holding the patched `zesarux` binary and its data files (a built ZEsarUX `src/` folder works) |
| `LEAPC_TS2068_DEBUG` | `~/ts2068-debug` | the ZEsarUX suites: the ts2068-debug checkout (its `ts2068_debug` package is imported) |
| `LEAPC_V2_REPO` | `~/2068-Leap` | `tools/v2ref.sh` (`make v2ref`, `make test`), `tools/check_platform.py` (`make check`: the upstream hashes are re-derived from the tag only when this repository exists; without it the check still verifies every file and delta), `spike/` |
| `LEAPC_FUSE` | `/usr/local/bin/fuse` | `make fuse`, `make timing`, the kit's verification: the unstripped Fuse 1.9.1 binary. If it uses a private libspectrum, set `LD_LIBRARY_PATH` as well |
| `LEAPC_REALTIME` | unset | set to `1` to run ZEsarUX at real speed (the suites otherwise use `--emulatorspeed 1000 --frameskip 49`, which changes no emulated timing) |
| `SKILLS` (make variable) | `~/z80-skills/skills` | `make audit` |

Example: `LEAPC_ZESARUX=$HOME/src/zesarux/src LEAPC_V2_REPO=$HOME/src/2068-Leap make test`.

## Building and testing

```sh
make            # build/leapc_home.bin, leapc_exrom.bin, leapc_zesarux.bin, leapc_exrom.dck, build/SHA256SUMS
                # (+ the test images in build/test/, and the libraries in build/libs/)
make libs       # the libraries (libs/shapes.asm, tests/libs/*.asm) as .bin, .sym, .tap, .tzx, .wav
make check      # strict assembly, ROM budgets (budget.toml), vendored-platform delta check, RAM layout guard,
                # documentation examples in step with tests/doc/
make repro      # two clean builds must give identical hashes (runs make clean: it deletes build/ and its logs)
make budget     # per-component budget table and ROM map
make inventory  # every HOME routine, table and gap with its referrers
make test       # ZEsarUX: every suite on a pool of emulators, with ROM coverage (about 15 minutes on 8 cores)
make test-fast  # the development subset (about 3 minutes)
make canary     # the RAM canary and banking invariants over the whole corpus
make capacity   # the measured capacity table (build/capacity.json)
make fuse       # the ROMs on Fuse 1.9.1, headless: typed programs, BREAK, SAVE/LOAD on its tape deck, the corpus
make timing     # the same programs timed on ZEsarUX (50 Hz) and Fuse (60 Hz)
make poweron    # the boot from power-on RAM patterns
make kit        # the hardware kit in build/kit (python3 tools/hwkit.py --verify checks it on both emulators)
make qualify    # the whole qualification in sequence (about 70 minutes); run make repro first, not after
make release    # the release assets in build/release (from a clean build: run it after make repro)
python3 tools/c2tape.py prog.c prog.tap               # a program tape for LOAD (.tap or .tzx)
python3 tools/lib2tape.py mylib.asm mylib.tap mylib.wav   # a library's tapes for LIB (include/leapc_lib.inc)
```

Continuous integration (`.github/workflows/ci.yml`) installs sjasmplus 1.23.1 and runs `make`, `make check` and `make repro` on every push and pull request. The emulator suites run locally.

## Rules for changes

- **ROM space is the hard limit.** HOME and EXROM have per-component budgets in `budget.toml`; `make check` fails a component over its budget. Include `make budget`'s before/after output with a change that adds ROM code. Reserve floors: HOME 384 B, EXROM 128 B (`budget.toml`'s `reserve_floor` values, 512 and 256, as lowered by the owner in ledger entries L73 and L74).
- **Every change to behaviour comes with tests** (the corpus in `tests/`, the suites in `tools/`) that fail without it. C test cases are C files with `// expect:` headers (`tools/exectest.py` documents them).
- **Documentation examples are tests.** A ```` ```c ```` block with `// expect:` lines in `README.md`, `spec.md` or `docs/*.md` (the list in `tools/docexamples.py`) is copied to `tests/doc/` by `python3 tools/docexamples.py`; `make check` fails when they are out of step.
- **The vendored platform** (`platform/`) is a copy of Leap V2's: change it only as a recorded delta (`platform/UPSTREAM.md`, `MANIFEST`, `deltas/`; `tools/check_platform.py --update`). Never write into a 2068-Leap checkout.
- **Symbolic layout only:** RAM addresses live in `include/leapc_layout.inc`. Every routine's header states In / Out / Destroys.
- **Release images** are the production build (no `-DLEAPC_TEST`), and `make repro` must give identical hashes.
- Commit messages: a short summary line, then what and why. Do not commit `build/`, emulator screenshots of your own sessions, or stock ROM images.

## Layout

| Path | Contents |
|---|---|
| `platform/` | Leap V2 platform sources, vendored from tag `v2.0.1-emu.1` (`platform/UPSTREAM.md`) |
| `src/rom/` | the HOME and EXROM images |
| `src/compiler/` | the compiler: lexer, symbol table, declarations, types, initialisers, expressions, code generator, constant folding, statements, preprocessor, the library's names and the binding of loaded libraries |
| `src/runtime/` | the helper core (multiply, divide, `switch`), program start and exit, BREAK, runtime errors, the library; floating point (`float.asm` in HOME, the float core `fpcore.asm` in the EXROM) |
| `src/shell/` | the EXROM shell: the editor's glue, commands, `RUN` and its reports, keyword highlighting, error messages, the tape commands and `LIB` |
| `src/test/` | test-build-only hooks (`-DLEAPC_TEST`) |
| `include/` | RAM layout, cells, tokens, errors, build configuration, the library ABI (`leapc_lib.inc`) |
| `libs/` | the example library `shapes` |
| `tests/` | the test corpus: C programs with expectation headers, by area (`lexer/`, `decl/`, `expr/`, `stmt/`, `pp/`, `lib/`, `rt/`, `mem/`, `float/`, `doc/`, ...) |
| `tools/` | build, budget, check and test tools; `c2tape.py` and `lib2tape.py` (host tape tools), `tapes.py`, the ZEsarUX harness (`lcharness.py`, `run_tests.py`), the Fuse harness (`fusedrive.py`, `fusetest.py`, `fuse/fuseshim.c`), `hwkit.py`, `release.py` |
| `docs/` | the guides, the examples, the hardware checklist and programs (`hardware/`), the milestone reports (`milestones/`), history (`history/`) |
| `spike/` | the feasibility spike's code and measured results, kept as evidence |
| `.github/` | issue and pull-request templates, CI |

## Licence

By contributing you agree that your contribution is released under the MIT License ([LICENSE](LICENSE)). Do not contribute code copied from the stock TS2068 or Spectrum ROMs or other copyrighted sources; [NOTICE](NOTICE) lists the derived code already present.
