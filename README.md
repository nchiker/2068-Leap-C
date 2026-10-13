# 2068-Leap-C

A C language ROM set for the original Timex Sinclair 2068 (48 KB, stock HOME/EXROM banking). It has a full-screen source editor and an on-machine, single-pass, Small-C-style compiler that generates native Z80 code. It is built on the platform services of Leap V2.

- **What is built:** `spec.md` (v0.1).
- **How and in which order:** `project_plan.md` (v0.1).
- **Why:** `docs/C_FEASIBILITY_STUDY.md` (closed).
- **Progress:** one report per milestone in `docs/milestones/`.

**Status:** M1.1 (foundation and lexer) is complete. The next milestone is M1.2 (declarations, types and scoped symbols).

## Build and test

Needs sjasmplus 1.23, Python 3.11 or later, and, for `make test`, ZEsarUX 13.0 in `~/Applications/ZEsarUX-13.0` and `~/ts2068-debug`.

```sh
make            # build/leapc_home.bin, leapc_exrom.bin, leapc_zesarux.bin, leapc_exrom.dck (+ build/test/)
make check      # strict assembly, ROM budgets (budget.toml), vendored-platform delta check
make budget     # per-component budget table and ROM map
make test       # ZEsarUX: boot tests (both images) and lexer tests, lexer throughput
make repro      # two clean builds must give identical hashes
```

Run in ZEsarUX: `zesarux --machine TS2068 --romfile build/leapc_zesarux.bin`.

## Layout

| Path | Contents |
|---|---|
| `platform/` | Leap V2 platform sources, vendored from tag `v2.0.1-emu.1` (see `platform/UPSTREAM.md`) |
| `src/rom/` | the HOME and EXROM images |
| `src/compiler/` | the compiler (M1.1: lexer and source streaming) |
| `src/runtime/` | runtime helpers, library, start and exit |
| `src/shell/` | the EXROM shell (M1.1: stub) |
| `src/test/` | test-build-only hooks (`-DLEAPC_TEST`) |
| `include/` | RAM layout, cells, tokens, errors, build configuration |
| `tests/` | test corpus (C sources with `// expect:` headers) |
| `tools/` | build, budget, check and test tools |
| `spike/` | feasibility code-shape spike, kept as evidence |
