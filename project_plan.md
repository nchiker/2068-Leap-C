# 2068-Leap-C — Project Plan

**Version 0.1, 2026-10-12.**

**Inputs:**

- `spec.md` v0.1 (what is built);
- `docs/C_FEASIBILITY_STUDY.md` rev 3 (why; measured baselines);
- `spike/` (measured template and helper reference code; evidence, not production).

**Feasibility is closed.** Budget overruns, measured surprises and design questions are handled by the engineering rules in §1. They are not a reason to restart feasibility work. The architecture in `spec.md` §1-5 changes only for a concrete implementation blocker, and that change is an owner decision.

---

## 1. Engineering rules (all phases)

### 1.1 Every milestone delivers both

1. **Assembled size measurements.** `make budget` reports per-component sizes from the listings. `make check` fails on any component over its `budget.toml` limit.
2. **Executable tests** in ZEsarUX 13.0, run by `make test`. Every case compiles and/or runs a C program on the production ROM images and checks its result: exit value, memory, screen text, compile error and line, or runtime error.

A milestone is complete only when its tests pass, its components are within budget (or the ledger records a reallocation), and both results are written to `docs/milestones/Mx.y.md`: sizes, test counts, measured speeds.

### 1.2 Budget discipline

`budget.toml` holds the `spec.md` §2.2 budgets per component, plus a ledger of changes.

When a component would exceed its budget, apply these in order:

1. **Shrink.** Measured optimisation, for example with the z80-skills shrink/optimize methods, keeping behaviour identical under the tests.
2. **Move cold code to EXROM** (for example diagnostics), subject to the bank rules (`spec.md` §2.2).
3. **Reallocate** from another component's unused budget or from the reserve. Record it in the ledger with the measured reason.
4. **Owner decision** if the reserve would fall below its floor (HOME 512 B, EXROM 256 B; since Phase 10, by owner decision, HOME 384 B and EXROM 128 B: ledger L73-L74): defer a feature or accept a smaller reserve.

### 1.3 Production code standards from the first line

- **Symbolic layout only:** no literal RAM addresses outside `include/leapc_layout.inc`.
- **Register contracts:** every routine header states In / Out / Destroys (as in V2).
- **Tests:** every routine reachable from compiled code or the shell has a test path in the corpus.
- **Code review:** run the z80-skills audit (register clobbers, stack balance) on each milestone's new code before closing it. Wire it into `make check` if a scriptable form exists.

**Test-only hooks** (token dump, symbol dump) exist only in a separate test build (`-DLEAPC_TEST`). Budgets and release tests always use the **production** images.

### 1.4 Frozen V2 is read-only

- Platform sources are **vendored** into `platform/` from tag `v2.0.1-emu.1`.
- `platform/UPSTREAM.md` records the commit and each Leap-C delta. A check script verifies that unlisted files are byte-identical to the tag.
- The V2 test harness is copied, not imported, so nothing is written into `~/2068-Leap`.

### 1.5 Repository

- `2068-Leap-C` becomes a local git repository at M1.1. Remote and publication are an owner decision.
- **Layout:**
  - `platform/` (vendored);
  - `src/compiler/`, `src/runtime/`, `src/shell/`, `src/rom/` (top-level HOME/EXROM images);
  - `include/`, `tests/` (C corpus + harness), `tools/`, `docs/`;
  - `spike/` (kept as evidence).

---

## 2. Phase overview

| Phase | Content | Main ROM budget (spec §2.2) | Depends on |
|---|---|---|---|
| **1** | **Compiler front end:** declarations and types, scoped symbols, typed expressions, native code generation with the measured templates | HOME 6,900 compiler + 500 helper core + 200 start/exit | — |
| 2 | Statements, functions, preprocessor | HOME 1,400 + 300 | 1 |
| 3 | Runtime helpers and platform integration (library, BREAK, runtime errors) | HOME 1,300 + ISR delta | 1, 2 |
| 4 | Memory layout and EXROM banking (finalise, guard, image regions, capacity) | — | 1-3 |
| 5 | Editor and C punctuation | EXROM 2,900 shell + 250 keywords; HOME ≈ 80 glyphs/keys | 1 (parallel with 2-4) |
| 6 | Compile/run workflow | EXROM 650 diagnostics | 2, 3, 5 |
| 7 | Cassette SAVE/LOAD (resolves chunk-6 loading) | HOME +340 (block I/O moved), EXROM −331 | 4, 6 |
| 8 | Language library completion and language polish | within existing budgets | 3, 7 |
| 9 | Emulator and physical hardware validation | — | 8 |
| 10 | Recommended fixes and library loading (owner-approved after Phase 9) | HOME +133, EXROM +125; floors 384 / 128 | 9 |
| 11 | Documentation and release qualification | — | 10 |

---

## 3. Phase 1 — Compiler front end

This is the first implementation phase. Everything in it is production code.

**Goal.** A working core of the on-machine compiler, running from the production HOME image:

- parses Release 1 declarations and types (`spec.md` §4.2-4.3);
- keeps scoped symbols;
- compiles typed expressions;
- emits native Z80 into the image region with the **mixed templates** measured in the spike, calling the HOME helper core.

The milestone ends with minimal function definitions, so every test is executable.

### M1.1 — Foundation and lexer

**Deliverables:**

1. **Repository.**
   - `git init`.
   - Directory layout (§1.5).
   - `platform/` vendored from the V2 tag with `UPSTREAM.md` and the delta check.
2. **ROM images that boot.**
   - `src/rom/home.asm` and `src/rom/exrom.asm` assemble the retained platform (`spec.md` §2.1) with all BASIC components removed.
   - A minimal EXROM shell stub boots to an idle prompt; the editor comes in Phase 5.
   - **Memory layout:** apply the baseline layout (`spec.md` §3.1: system variables relocated to `$5B00`). Use fallback B if the relocation hits a concrete blocker during this milestone. Record which, with the reason.
3. **Build and budget.**
   - `make` builds `build/leapc_home.bin`, `leapc_exrom.bin`, a ZEsarUX combined image and `.dck`.
   - `make budget` prints the per-component table and ROM map.
   - `budget.toml` holds the §2.2 limits; `make check` enforces them, runs the vendored-platform delta check and runs the assembler in strict mode.
4. **Test harness.**
   - `tools/lcharness.py`: derived from V2's `qharness` (copied, with attribution). It handles ZEsarUX ZRCP, snapshot restore, writing C source into the line store, calling compiler and runtime entry points, and reading results and the screen.
   - Test case format: `tests/c/**/*.c` with `// expect:` headers.
   - `tools/c2src.py` turns a host `.c` file into line-store records for the harness. The same records are later used for tapes.
5. **Lexer and source streaming** (`src/compiler/lexer.asm`).
   - Chunked streaming over the line store, after V2's 264-byte window design.
   - Token kinds per `spec.md` §4.1, with line tracking.
   - Lexical errors with error code and line number.
   - Keyword table (C89 set).

**Completion criteria:**

- [ ] Clean-checkout `make` reproduces identical image hashes on two consecutive builds.
- [ ] The images boot to the idle prompt in ZEsarUX (harness boot test).
- [ ] `make check` passes: budgets, delta check, strict assembly.
- [ ] **≥ 60 lexer cases pass** (test build token dump): every token kind, every escape, number bases and limits, comments across lines, lines of 127 characters, and every lexical error with the correct line.
- [ ] Measured size of lexer + streaming + keyword table recorded against its budget (1,100 B).
- [ ] Throughput measured: T-states per source byte on a 2 KB sample (feeds the compile-speed target).

### M1.2 — Declarations, types and scoped symbols

**Deliverables:**

- **Type descriptors.** Compact encoding (base type, pointer depth, array dimensions, struct index, function signature) stored in the compile workspace.
- **Declarator parser:**
  - pointers, arrays (multi-dimensional), functions, function pointers;
  - `struct` (tags, members, byte offsets, nesting, self-reference through pointers), `enum`, `typedef`;
  - storage classes and qualifiers per `spec.md` §4.2.
- **Scoped symbol table** (`src/compiler/symtab.asm`):
  - file scope, function scope and block scope;
  - separate namespaces (tags, members per struct, ordinary identifiers incl. typedef names and enum constants);
  - shadowing; reclaim on scope exit;
  - workspace allocated top-down with *out of memory* errors.
- **Constant-expression evaluator** (shared with M1.3 folding): array sizes, enum values, `sizeof`.
- **Static data allocation** in the image regions (top-down per region, region order per `spec.md` §3.2).
- **Global initialisers:** scalars, arrays, strings, structs, with brace elision.

**Completion criteria:**

- [ ] **≥ 80 declaration cases pass.**
  - Test build symbol/type dump checked for: kinds, sizes, struct member offsets, `sizeof`, enum values.
  - Initialised static data verified **byte-for-byte in the image**.
- [ ] **≥ 30 declaration error cases** give the specified error and line: redeclaration, incomplete type, bad declarator, "not supported" features, out of memory.
- [ ] Symbol capacity measured: workspace bytes per global scalar, per struct member, per local. Recorded for the capacity table (Phase 4).
- [ ] Sizes within budget: declarations and types 2,000; symbol table 800.

### M1.3 — Typed expressions and native code generation

**Deliverables:**

- **Expression compiler** (`src/compiler/expr.asm`):
  - every operator of `spec.md` §4.4;
  - lvalue/rvalue handling and type checking;
  - integer promotions and usual conversions, signed vs unsigned operation selection;
  - pointer arithmetic scaling and pointer differences;
  - member access, casts, `sizeof`, `?:`, comma, compound assignment, pre/post `++`/`--`, short-circuit `&&`/`||`;
  - constant folding.
- **Code generator** (`src/compiler/codegen.asm`):
  - the mixed template table, taken from `spike/asm/templates.inc` and frozen as golden byte sequences;
  - emission into image region 1, with region chaining (`jp` link);
  - forward-reference fixup chains.
- **Helper core** (`src/runtime/helpers.asm`, HOME):
  - RST helpers: `LDI` and `STI` with their bodies in the vector slots, `ENTER` (with stack check), `LEAVE`, `CMPLT`;
  - `CALLHL`; variable shifts;
  - `MUL`/`DIV`/`MOD` wrappers (signed/unsigned) over the kept ROM math routines.
- **Minimal functions** (completed in Phase 2):
  - ANSI definitions with parameters and locals;
  - expression statements; `return expr`;
  - calls including recursion and calls before definition.
- **Program start and exit** (`spec.md` §5.7, minimal): the harness can run `main` and read its exit value.

**Completion criteria:**

- [ ] **≥ 150 executable expression cases pass.** Results checked through `main`'s exit value and global memory. They cover:
  - every operator at `char`/`int`/`unsigned`/pointer types, signed/unsigned boundaries (−32768, 32767, 65535);
  - pointer scaling over `char`/`int`/struct/array elements;
  - multi-dimensional indexing, struct member chains, function-pointer calls;
  - recursion.
- [ ] **≥ 40 expression error cases** give the specified error and line (type mismatch, non-lvalue, unsupported operation).
- [ ] **≥ 30 golden code tests:** the generated bytes for template-covered snippets equal the frozen template sequences.
- [ ] Helper core measured: sizes against the spike reference (92 B core) and T-states per helper (micro tests as in the spike). LDI/STI with their bodies at the vector confirmed at 45/49 T or better.
- [ ] `ENTER`'s stack check raises *stack overflow* in a deep-recursion test, and the machine returns to a sane state.
- [ ] Compile speed measured on the M1.3 corpus (ms per line), recorded against the 25 ms target.
- [ ] Sizes within budget: expressions 1,800; code generator 1,200; helper core 500; start/exit (partial) 200.

**Phase 1 exit:** M1.1-M1.3 complete; the Phase 1 ROM map and budget report recorded in `docs/milestones/`.

---

## 4. Phase 2 — Statements, functions, preprocessor

**Deliverables:**

- **Statements:** `if`/`else`, `while`, `do`/`while`, `for` (single-pass layout), `switch`/`case`/`default` (the `SWITCH` helper; dense table where shorter), `break`/`continue`, `goto` and labels, and `return` anywhere through `LEAVE`.
- **Blocks** with local declarations at any level.
- **Functions complete:**
  - prototypes; argument count checks and conversions;
  - implicit declarations resolved by fixup chains;
  - `static` locals; local scalar initialisers;
  - `main`'s exit status;
  - the function → source-line table (`spec.md` §5.9).
- **Preprocessor:** object-like `#define` and `#undef`; `#include <leap.h>` accepted as a no-op; "not supported" for other directives.

**Completion criteria:**

- [ ] **The four spike workloads, compiled by the real compiler,** run correctly. Their code size is **within ±10% of the spike's hand-assembled mixed output** (sum 67, copy 64, asum 97, move 86, fact 70; 384 B total) and their T-states within ±10% of the spike's mixed measurements. Any deviation beyond that is explained in the milestone report.
- [ ] **Corpus ≥ 300 programs** (Phase 1 + 2) passing, including:
  - every statement form;
  - nested loops with `break`/`continue`;
  - `switch` with sparse and dense cases;
  - `goto` across blocks; mutual recursion; forward calls;
  - `static` local persistence;
  - preprocessor cases and the statement/function error cases.
- [ ] RST assignment confirmed or retuned from operation frequencies counted over the corpus, and recorded.
- [ ] Sizes within budget: statements and functions 1,400; preprocessor 300.

---

## 5. Phase 3 — Runtime helpers and platform integration

**Deliverables:**

- **Remaining helpers.**
- **The `leap.h` library** of `spec.md` §7 (tape functions excepted):
  - text and attributes, `printf` subset;
  - keyboard and line input;
  - graphics including `mode()` with hi-res protection, and sprite get/put;
  - sound and beep; frames, pause, random; port I/O;
  - strings and memory, conversions, `malloc`/`free`, `exit`.
- **Full start/exit normalisation** (`spec.md` §5.7).
- **EXROM trampolines** for EXROM-resident services (AY beep, formatting where used), honouring `NOBRK`.
- **BREAK mechanism** (`spec.md` §5.8): ISR delta in the vendored interrupt module, `RUN_SP` unwind, `NOBRK`/`BRKPEND`.
- **Runtime errors** with the function → line mapping.

**Completion criteria:**

- [ ] Library test suite: every function has executable cases. Screen output is verified with the harness screen reader; sound with port-write capture or AY register reads; keyboard through ISR latch injection.
- [ ] **BREAK tests pass in every state.** For each state, the harness checks the shell state afterwards: paging depth 0 → editor state, AY silent, stack sane, source intact. The states:
  - tight loop in chunk 6;
  - deep recursion;
  - during an EXROM trampoline;
  - during beep; during pause;
  - inside `malloc`.
- [ ] **Soak:** ≥ 500 interrupt frames of mixed library calls from chunk-6 code, with 0 failures (as in the spike).
- [ ] ISR delta size and per-frame cost measured. The ISR cost stays within +10% of V2's measured 2.0-2.5 kT per frame.
- [ ] Sizes within budget: library 1,300; start/exit/BREAK/errors 200; platform deltas inside the retained-platform 3,800.

---

## 6. Phase 4 — Memory layout and EXROM banking

**Deliverables:**

- **Final layout** in `include/leapc_layout.inc`, confirming the baseline or fallback chosen in M1.1.
- **Layout guard** tools, modelled on V2's `check_ram_layout.py` and `qcanary.py`, in `make check`:
  - a static census of the RAM symbols that HOME and EXROM reference;
  - a canary run over the corpus.
- **All image regions exercised:** region chaining and data allocation across regions; the hi-res reservation (`#pragma hires`) and the runtime refusal.
- **Stack and heap:** stack limit and heap bounds finalised.
- **Banking invariants as regression tests:**
  - depth 0 during program run;
  - trampoline nesting;
  - ISR during chunk-6 execution;
  - no stack in chunk 6;
  - EXROM-resident compiler parts never touching chunk 6.

**Completion criteria:**

- [ ] The layout guard runs in `make check`, with negative controls (a deliberately misplaced cell is reported).
- [ ] The canary over the full corpus shows no writes outside the allowed regions.
- [ ] **Capacity table measured and recorded:**
  - largest compilable source;
  - largest image; workspace at the limit;
  - deepest recursion for a reference function;
  - largest heap block.

  These replace the feasibility estimates (about 21 KB of source with mixed templates).
- [ ] Image-region overflow tests pass for every region transition.

---

## 7. Phase 5 — Editor and C punctuation

Phase 5 can start after M1.1, in parallel with Phases 2-4.

**Deliverables:**

- **The Leap-C shell** (`src/shell/`), adapted from V2's shell glue: navigation, redraw with flicker safeguards, status bar, error-line jump, LIST, command loop. BASIC tokenizer, keyword spans, sessions and arrays removed.
- **C keyword highlighting.**
- **Key map and glyphs** for `[ ] { } | ~ ^ \` (`spec.md` §6.2, after the owner confirms the mapping).

**Completion criteria:**

- [ ] Every character of the C basic source character set (letters, digits, space and the 29 graphic characters `! " # % & ' ( ) * + , - . / : ; < = > ? [ \ ] ^ _ { | } ~`) can be typed (keystroke injection through the ISR) and is displayed correctly (screen-reader check of each glyph).
- [ ] Editor regression tests: the applicable V2 editor tests, ported, pass. Typing cost per key measured, at or below V2's about 70 kT per key (V2 feature-cost study).
- [ ] C keyword highlighting verified on a fixture screen.
- [ ] Sizes within budget: shell 2,900 EXROM; keyword table 250; glyphs and key map inside the HOME retained-platform budget.

---

## 8. Phase 6 — Compile/run workflow

**Deliverables:**

- **`RUN`** = compile, then execute.
- **Compile errors:** `ERROR n: message` and line number, cursor at the line (EXROM diagnostics through a trampoline, never touching chunk 6).
- **Runtime errors and BREAK:** a message, then back to the editor.
- **Reports:** exit status, image size and free heap; the `FREE` command.

**Completion criteria:**

- [ ] **End-to-end tests:**
  - ≥ 20 programs typed through keystroke injection, run, with the screen verified;
  - the full corpus through fast source injection plus the shell's real `RUN` path.
- [ ] Every compile error class positions the cursor on the right line (≥ 1 case per class).
- [ ] **Compile speed** over the corpus: **≤ 25 ms per line average**, measured and reported. If it misses, apply measured optimisation; the target is an engineering target, not a gate.
- [ ] Diagnostics size within budget (650 EXROM).

---

## 9. Phase 7 — Cassette SAVE/LOAD (resolves chunk-6 loading)

**Deliverables:**

- **Source tapes:** `SAVE`/`LOAD`/`VERIFY` with version word `$8C00` (`spec.md` §8.1). V2 BASIC tapes are refused, and V2 refuses Leap-C tapes.
- **Chunk-6 resolution** (`spec.md` §8.3):
  - move `STORAGE_SEND_BLOCK` and `STORAGE_RECEIVE_BLOCK` into HOME, keeping headers in EXROM;
  - fallback: staged load through a bounce buffer, if HOME cannot absorb them;
  - `tape_save` / `tape_load` library functions.
- **Host tool** `tools/c2tape.py`: a `.c` file → a Leap-C program tape (`.tap`/`.tzx`).

**Completion criteria:**

- [ ] Real ZEsarUX tape round trip of a source program: save, load, compare the line store.
- [ ] `BAD TAPE VERSION` in both directions, with nothing written.
- [ ] **`tape_load` into a chunk-6 buffer from a running program,** verified byte-for-byte. Also into `$E000` and the heap.
- [ ] A host-built tape loads and runs.
- [ ] HOME +340 / EXROM −331 recorded in the ledger.

---

## 10. Phase 8 — Language library completion and polish

**Deliverables:**

- Remaining library items and edge cases.
- Diagnostics quality pass.
- Initialiser completeness (`spec.md` §4.7).
- Documentation examples compiled as tests.
- **Optional:** the size template set (`#pragma size`, RST `$30` `LDL`/`STL`), *only if* the Phase 4 capacity table shows a real program that needs it.
- **Optional:** a peephole stage, only if measured to pay for its ROM.

**Decision point (owner):** floating point for Release 1 or later (`spec.md` §4.9). Input:

- the retained calculator's size;
- the measured trampoline cost;
- the remaining reserve.

**Completion criteria:**

- [ ] Corpus ≥ 500 programs passing.
- [ ] Every library function documented and tested.
- [ ] All components within budget.
- [ ] Reserve at or above its floor.

---

## 11. Phase 9 — Emulator and physical hardware validation

**Emulator qualification (ZEsarUX):**

- full corpus, soak tests, randomised power-on RAM;
- tape round trips; BREAK matrix; capacity limits.

**Courtesy emulators:** Fuse and EightyOne smoke tests.

**Physical TS2068**, from a hardware checklist modelled on V2's:

- EPROM HOME (27128) and EXROM (2764) builds;
- boot, keyboard including the new punctuation;
- real cassette SAVE/LOAD;
- 60 Hz timing;
- **display contention** measured for code in `$6000-$77FF` and chunk 6 (unverified until now);
- BREAK; soak.

**Completion criteria:**

- [ ] Every emulator qualification case passes.
- [ ] Every item on the hardware checklist passes, or an accepted deviation is recorded by the owner.

---

## 12. Phase 10 — Recommended fixes and library loading

Approved by the owner after Phase 9 (the improvements report, `spike/improvements/`), before documentation and release qualification, which became Phase 11.

**Deliverables:**

- **Fixes 1-5, each at its smallest:** `?:` with a float and an integer operand converts the integer (C89 6.3.15; the deviation retired); errors 21, 22, 52, 70 and 76 name the identifier; `RT_UDIV`'s unreachable branch removed; the unreachable vendored EXROM code removed (platform deltas D15 onward; `beep()` and `sound()` unchanged); the cursor at a compile error's column.
- **Library loading, Stage 1, with V2-style jump-table slots:** an assembly image for image region 3 (a header, an export table in `LIB_NAMES`'s records, code and data); 16 slots of `jp` in HOME at an address that never moves; `tools/lib2tape.py` and the ABI include; `LIB "name"` and `LIB` in the shell; region 3 closed while a library is loaded, the ROM's table then the library's searched by the same binding; BREAK, runtime errors and the canary inside a library as inside the ROM's library; an example library, a library tape and a check program in the hardware kit.
- **Out of scope:** Stage 2 (C libraries compiled on the machine); Fix 6 (the line store to the EXROM) unless HOME would fall below 128 B free.

**Owner decisions:** V2-style slots, not only an identity word; the reserve floors may be lowered as far as the phase needs, not below 128 B in either ROM, each change in the ledger.

**Completion criteria:**

- [ ] Every fix and feature has tests that fail without it.
- [ ] The full Phase 9 qualification on the final images: `make test` with ROM coverage, `make fuse` (the frames case included), `make timing`, the `--ram warm` and `--ram random:7` suites, `make capacity`, the kit's verification with its 30-minute soak, `make check`, `make repro`.
- [ ] Library loading exercised on ZEsarUX (a real tape signal) and on Fuse.
- [ ] `spec.md` v0.12, the budget ledger, `docs/milestones/M10.md`.

---

## 13. Phase 11 — Documentation and release qualification

**Deliverables:**

- **User manual:** editor, workflow, tape, examples.
- **Language reference:** the Release 1 subset, deviations from C89, limits, error lists.
- **Library reference.**
- **Technical reference:** ABI, memory map, ROM map, banking rules.
- **Release notes.**
- **Reproducible build check.**
- **Release assets:** ROM images, `.dck`, example tapes, documents.
- **Qualification report.**

**Completion criteria:**

- [ ] Documentation examples pass as tests.
- [ ] Reproducible release hashes.
- [ ] Qualification report accepted by the owner, then tagged.

---

## 14. Risks managed during implementation (not feasibility gates)

| Risk | Response |
|---|---|
| HOME budget pressure (compiler estimated at 6.9-10.8 KB) | §1.2 protocol; measured at every milestone; cold parts to EXROM |
| Single-pass limits (forward struct use, calls before definition) | fixup chains and incomplete types (M1.2/M1.3); an optional second pass over the resident source costs time only |
| BREAK unwind safety | the `NOBRK`/`BRKPEND` discipline; the BREAK matrix in Phase 3 |
| Compile speed | measured from M1.1 (lexer throughput) onwards |
| System-variable relocation | decided in M1.1 by the boot test; fallback layout B |
| Keyboard legends / ergonomics | owner confirmation before Phase 5 key-map work |
| Real-hardware timing and contention | Phase 9 measurements |

---

## 15. First milestone

**M1.1 — Foundation and lexer** (§3).

It produces production compiler code (the lexer and source streaming) together with the build, budget and test infrastructure every later milestone needs. The milestone after it, M1.2, starts the declarations and type system: the largest component without a V2 anchor.
