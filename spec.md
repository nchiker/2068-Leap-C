# 2068-Leap-C — Specification

**Version 0.12, 2026-10-22** (v0.1, 2026-10-12: initial; v0.2-v0.5, 2026-10-13; v0.6-v0.9, 2026-10-20; v0.10-v0.11, 2026-10-21). This specification is derived from `docs/C_FEASIBILITY_STUDY.md` (revision 3), whose architecture decisions are approved.

**Changes in v0.2:** the frame's reference point (§5.2) and the `ENTER`/`LEAVE` contracts (§2.3, §5.3), by owner decision during M1.3 (`docs/milestones/M1.3.md`).

**Changes in v0.3 (Phase 2, owner decisions O1/O2 of 2026-10-13):** the retained 16-bit math is cut to what C uses (§2.1, platform delta D3). Multiply and divide are the helper core's own routines (§5.3). `rand()`/`srand()` are a C generator (§7).

**Changes in v0.4 (Phase 2, as built):** the preprocessor's rules and limits (§4.8, §4.10), the `SWITCH` tables (§5.3), and the function → line table's format (§5.9).

**Changes in v0.5 (Phase 3, as built; `docs/milestones/M3.md`):** program start and exit (§5.7), BREAK (§5.8) and runtime errors (§5.9) as built; the heap (§3.2); the library's semantics, its binding to the compiler and its deviations (§7); the library's use of `AF'` (§5.1).

**Changes in v0.6 (Phase 4, as built; `docs/milestones/M4.md`):** the memory map is final (§3.1: baseline layout A, the RAM each region holds, the layout guard); the region rules as built (§3.2: code and data in the image regions, `#pragma hires`, the stack's floor, the heap's bounds); `#pragma hires` (§4.8); the limits measured (§4.10, with the capacity table); `ENTER`'s stack check (§5.3); the platform deltas D5 and D6 (§2.1); runtime-error lines in code continued from image region 3 into region 4 (§5.9).

**Changes in v0.7 (Phase 5, as built; `docs/milestones/M5.md`):** the editor and shell (§6.1), the C punctuation's keys and glyphs, confirmed by the owner (§6.2), RUN's recovery as built in Phase 5 (§6.3), RST `$30` given to the compiler's `LEX_NEXT` by owner decision (§2.3, §5.3, §5.6), the platform deltas D7 and D8 (§2.1).

**Changes in v0.8 (Phase 6, as built; `docs/milestones/M6.md`):** the compile/run workflow (§6.3): the reports on rows 22-23 (compile errors and runtime errors with their messages, BREAK, the exit status, the image's size and the free heap), the error messages (§5.9, §6.3, from `include/leapc_errors.inc`), `FREE` (§6.1), the compile speed measured through `RUN`.

**Changes in v0.9 (Phase 7, as built; `docs/milestones/M7.md`):** the cassette. The tape block I/O in HOME behind the trampoline `TAPE_BLOCK`, the header logic in the EXROM (§2.1 platform delta D9, §2.2, §8.3); the tape cells (§3.1); `SAVE`, `LOAD`, `VERIFY` (§6.1); `tape_save`, `tape_load` and their BREAK section (§5.8, §7, §7.1); the program and data tapes, their version word and refusal rules, LOAD's staging and record check (§8); the host tool `tools/c2tape.py` (§10).

**Changes in v0.10 (Phase 8, as built; `docs/milestones/M8.md`):** floating point in Release 1: `float` and `double` as one 5-byte type, floating constants, conversions, expressions, arguments and results, `printf`'s `%f` (§4.1-§4.4, §4.6, §4.9, §5.1-§5.3, §5.8, §5.9, §7). The V2 FP calculator is re-engineered into the float core, which replaces it (§2.1 platform delta D10, §2.2). Cold compiler parts move to the EXROM and two groups of editor-only platform routines with them (deltas D11, D12; §2.1, §2.2). Initialisers: braces around an automatic scalar's (§4.7). Diagnostics: a missing token is reported at the line it belongs to (§6.3). The documentation's examples are tests (§11, `docs/EXAMPLES.md`).

**Changes in v0.11 (Phase 9, as built; `docs/milestones/M9.md`):** emulator qualification on ZEsarUX and Fuse, and the hardware kit. The font tells the digit `1` from the letter `l` (§2.1 platform delta D13). An undeclared identifier's report names it (§6.3). A report or message waits for a key pressed after any held key's release (§6.1, §6.3). The cold start clears the UDG table, so codes 144-164 show as spaces from any power-on RAM (§3.1, §7). The bank switch keeps interrupts on, so float code no longer loses frame interrupts (§2.1 platform delta D14, §7). A frame is 1/60 s on a TS2068; ZEsarUX 13.0 emulates 50 Hz (§7, §10). The validation adds power-on RAM patterns, Fuse, a timing comparison, ROM coverage and the hardware kit (§10, §11). Budgets (§2.2: ledger L56-L60).

**Changes in v0.12 (Phase 10, as built; `docs/milestones/M10.md`):** the five recommended fixes and library loading, owner-approved. `?:` with a float and an integer operand converts the integer (C89 6.3.15; the deviation is gone, §4.4). Errors 21, 22, 52, 70 and 76 name the identifier, as 23 does, and the cursor lands on the error's column (§6.3). Unsigned division is 112 T faster (§5.3). Unreachable vendored EXROM code is removed (§2.1 platform deltas D15-D19). Libraries: an assembly image loaded from tape into image region 3 by `LIB "name"`, its functions bound like the built-in library's, reaching the ROM through a fixed jump table of 16 slots at the end of HOME (§2.4, §3, §5.8, §5.9, §6.1, §7.2, §8.4, §9, §10). A LOAD stopped by BREAK while its program arrived into the source left the partly overwritten source; it now empties it (§6.1). Budgets and the floors (§2.2: ledger L61-L75).

**What is fixed and what is tuned:**

- Values marked **baseline** are the starting design. They are tuned *with measurements* during implementation; see `project_plan.md`.
- Tuning does not reopen the architecture.
- A change to anything marked **fixed** needs a concrete blocker found in implementation.

**Terms:**

| Term             | Meaning                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------- |
| **HOME**         | the 16 KB replacement HOME ROM, always mapped at `$0000-$3FFF`                              |
| **EXROM**        | the 8 KB replacement extension ROM, mapped into chunk 6 (`$C000-$DFFF`) only while paged in |
| **Chunk 6**      | the address range `$C000-$DFFF`: EXROM when paged in, RAM when paged out                    |
| **Platform**     | the reusable services taken from frozen Leap V2                                             |
| **V2 reference** | Leap V2 release `v2.0.1-emu.1` (`d19b9ea`, HOME `3f13ec2c…`, EXROM `24b1ebb0…`)             |

---

## 1. Product definition (fixed)

2068-Leap-C is a **language ROM set** for the original Timex Sinclair 2068:

- 48 KB RAM;
- Z80A at about 3.5 MHz;
- stock HOME/EXROM banking;
- no RAM expansion, no cartridge required.

It replaces Leap V2's BASIC-specific components (compiler, VM, BASIC shell parts, BASIC runtime) with:

- a full-screen **C source editor** (the V2 editor, adapted);
- an **on-machine, single-pass, Small-C-style C compiler** that generates **native Z80 machine code**;
- a **runtime** of shared HOME-ROM helpers and a platform library;
- **cassette storage** of C source (and, from Phase 7, data blocks).

**The user workflow** is edit → `RUN`:

1. `RUN` compiles the whole program from source into RAM.
2. If compilation succeeds, `RUN` executes the program.
3. Compile errors, runtime errors and BREAK return to the editor with the source intact and the cursor at the offending line where known.

**What a program is:** source text is the stored program. Compiled code is regenerated on every `RUN` and is never saved in Release 1.

**Cross-compilation** (for example SDCC) is a development and test tool only. It is not part of the product.

**Non-goals for Release 1:**

- full C89;
- `float`/`double` (optional, later: §4.9);
- `long`;
- separate compilation and linking;
- file-oriented `stdio`;
- V2 BASIC compatibility;
- V2 package (`LOAD … EXT`) compatibility.

---

## 2. ROM architecture

### 2.1 Retained platform (from the V2 reference)

Sources are vendored into `platform/` from the V2 reference tag. `platform/UPSTREAM.md` pins the commit, and every Leap-C modification is listed as a delta.

| Module                                                                               | V2 size  | Bank  | Leap-C status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------ | --------:| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Graphics: text, attributes, scrolling, pixels, line, sprite capture/draw, font       | 2,071    | HOME  | kept. **Delta D13 (v0.11, owner-approved):** the glyphs of the digit `1` (a flag and a full base) and the letter `l` (a tail, no base), which V2's font drew two pixels apart; data only. **Delta D12 (v0.10):** the editor's bold and string output (`GFX_PUTCHAR_BOLD`, `GFX_PRINT_STRING`, 32 B; the EXROM editor is their only caller) assembled in the EXROM, conditional assembly only. **Delta D8 (v0.7):** 8 glyphs `[ ] { } \| ~ ^ \` and their punctuation-table entries (§6.2; 80 B). **Delta D6 (v0.6):** V2's sprite-slot invalidation removed (no sprite slots in Leap-C; 25 B) |
| Memory: line store, fill, shift, cold init                                           | 485      | HOME  | kept. **Delta:** re-pointed to the Leap-C memory map (§3); **D5 (v0.6):** `MEM_INIT` no longer clears V2's string-pool, package and sprite-slot cells (25 B); **D11 (v0.10):** the editor's insert and range delete (`MEM_LINE_INSERT`, `MEM_LINE_DELETE_RANGE`, 144 B) assembled in the EXROM, conditional assembly only                                                                                                                                                                                                                                                                     |
| Keyboard I/O                                                                         | 434      | HOME  | kept. **Delta D7 (v0.7):** symbol-shift map for the 8 C characters (§6.2), in place in the table; SYMBOL SHIFT + A/S no longer give V2's error-navigation codes, which no Leap-C code handles (−19 B)                                                                                                                                                                                                                                                                                                                                                                                         |
| 16-bit math (`MATH_NEGATE16`, `ABS16`, `COMPARE16`)                                  | 390 → 39 | HOME  | **Delta D3 (v0.3):** multiply and divide moved to the helper core's register-only routines (§5.3); `SQRT16`, `SGN16`, `MULTIPLY16` removed (no Release 1 caller); `RND16` replaced by the library's `rand()` (§7)                                                                                                                                                                                                                                                                                                                                                                             |
| Interrupt (IM 1, `FRAMES`, keyboard scan)                                            | 154      | HOME  | kept. **Delta D4 (v0.5):** BREAK request for native programs (§5.8): V2's BREAK latch (14 B) replaced by a call to the runtime (8 B)                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Bank switching (`BANK_PAGE_EXROM_IN/OUT`, depth-counted)                             | 44       | HOME  | kept. **Delta D14 (v0.11):** no `di` (each `ei` stays). With interrupts off for about 120 T, longer than the TS2068's 32 T INT, float code (a page-in and page-out per operation) lost about 1% of the frame interrupts (`FRAMES`); found on Fuse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| AY beep (HOME part)                                                                  | 58       | HOME  | kept                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `FOLD_UPPER` (was in the BASIC compiler)                                             | 9 → 0    | HOME  | not built: C is case-sensitive and nothing calls it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Editor engine                                                                        | 737      | EXROM | kept. **Deltas D15-D17 (v0.12):** the fallbacks for unset hooks (the shell sets both before every session) and the second dispatch block (D15), the NEXT ERROR, PREV ERROR, HOME and END keys, which no Leap-C key gives (D16), `EDITOR_BLOCK_DELETE`, which had no caller (D17): deletions only |
| Tape: `STORAGE_*`                                                                    | 793      | EXROM | kept. **Delta D9 (v0.9, Phase 7):** block send/receive (331 B, byte for byte) assembled in HOME, the header logic (`STORAGE_SAVE`, `STORAGE_LOAD`, version word, progress) in the EXROM: conditional assembly only (§8.3). **Delta D18 (v0.12):** `STORAGE_SAVE`'s name clamp and padding (the shell passes 10 padded characters). `STORAGE_VERSION_WORD`'s package branch is V2's and serves Leap-C's library tapes (§8.4) |
| Shell: editor/screen glue, command loop, tape commands, messages, chime, entry slots | 2,754    | EXROM | adapted into the Leap-C shell; BASIC-only parts removed (v0.7, Phase 5: §6.1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Integer formatting                                                                   | 79       | EXROM | kept                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Sound, AY beep (EXROM part)                                                          | 59       | EXROM | kept. **Delta D19 (v0.12):** `SOUND_EXROM`'s range check (its only caller, the chime, writes registers 0-10); **D17:** `AY_BEEP`'s own entry, which had no caller (`beep()` calls `AY_BEEP_PERIOD` in HOME, then `AY_BEEP_PLAY`). `beep()` and `sound()` are unchanged |
| FP calculator + float formatting                                                     | 2,165    | EXROM | **v0.10: re-engineered into the float core** (`src/runtime/fpcore.asm`, 1,464 B, §4.9), which replaces it: the calculator is no longer assembled, and V2's float formatting is left out by **delta D10** (conditional assembly; the integer formatting stays)                                                                                                                                                                                                                                                                                                                                 |

**Removed:**

- V2 VM core (6,033), BASIC compiler (5,139), BASIC symbol table (576);
- SAVE ALL / identity CRC / session undo (591);
- Array Store (701), BASIC-only shell parts (878);
- package registry (263; V2 packages are BASIC-statement extensions).

### 2.2 ROM budget (baseline; enforced by the build)

**Per-component budgets.** Every component has a budget, recorded in `budget.toml`.

- `make budget` reports the assembled size of each component from the listings.
- `make check` fails when a component exceeds its budget, unless the budget ledger records a reallocation with its justification.
- The **reserve floor** (HOME 512 B, EXROM 256 B at release; v0.12, owner decision: HOME 384 B, EXROM 128 B, ledger L73-L74) can be drawn below only with owner approval.

**HOME (16,384 B):**

| Component                                                                                     | Budget     |
| --------------------------------------------------------------------------------------------- | ----------:|
| Page zero (reset, RST vectors and helper bodies that fit, IM 1, NMI), cold start, trampolines | 160        |
| Retained platform (graphics, memory, keyboard, math, interrupt, bank, AY) incl. deltas        | 3,800      |
| Tape block send/receive (moved from EXROM in Phase 7)                                         | 340        |
| **Compiler:** lexer + source streaming + keyword table                                        | 1,100      |
| **Compiler:** declarations and type system                                                    | 2,000      |
| **Compiler:** scoped symbol table                                                             | 800        |
| **Compiler:** typed expressions                                                               | 1,800      |
| **Compiler:** code generator (templates, fixups, constant folding)                            | 1,200      |
| **Compiler:** statements and functions                                                        | 1,400      |
| **Compiler:** preprocessor (object-like `#define`)                                            | 300        |
| **Runtime:** helper core (§5.3)                                                               | 500        |
| **Runtime:** library (§7)                                                                     | 1,300      |
| **Runtime:** start, exit, BREAK, runtime errors                                               | 200        |
| **Allocated**                                                                                 | **14,900** |
| **Reserve**                                                                                   | **1,484**  |

**EXROM (8,192 B):**

| Component                                                                                     | Budget    |
| --------------------------------------------------------------------------------------------- | ---------:|
| Retained platform (editor engine, tape headers, integer formatting, sound)                    | 1,340     |
| Leap-C shell (adapted editor glue, command loop, tape commands, messages, chime, entry slots) | 2,900     |
| C keyword highlighting table                                                                  | 250       |
| Compiler diagnostics (message texts, error reporting)                                         | 650       |
| FP calculator + float formatting (optional component; §4.9)                                   | 2,165     |
| **Allocated**                                                                                 | **7,305** |
| **Reserve**                                                                                   | **887**   |

**Bank rules (fixed):**

1. Anything that compiled programs call (runtime helpers, library, trampolines) is in **HOME**.
2. **EXROM services are reached only through HOME trampolines** that page EXROM in, call, and page it out again. Neither the trampoline nor the stack may be in chunk 6.
3. The compiler core runs in **HOME with chunk 6 paged out**, because it writes the program image there. EXROM-resident compiler parts (diagnostics) run only through a trampoline and never touch chunk 6.
4. The editor and shell run in **EXROM**. While they run, chunk 6 RAM is invisible.

**As built (v0.12): budgets.** After Phase 10 (ledger L61-L75): HOME 15,929 B allocated, **reserve 455 B** (floor 384 B): `?:` with mixed operands +55 B (expressions), the names of errors 70 and 76 +17 B (statements), the unsigned division −5 B (helpers), the library jump table +48 B (a pinned component at `$3FD0-$3FFF`, §2.4), region 3 closed while a library is loaded +11 B (declarations), BREAK in a library's code +7 B (runtime exit). EXROM 8,006 B allocated, **reserve 186 B** (floor 128 B): the shell +243 B (the five names' list +18 B, the error's column +41 B, the LOAD defect +4 B, `LIB` +180 B), the binding's search of a loaded library and the four new parameter lists +17 B and a `#define`'s `ALREADY DEFINED` without a name +6 B (compiler parts), the unreachable vendored code −141 B (D15-D19; the report's 154 B less `STORAGE_VERSION_WORD`, which library tapes need). **The floors (owner decision, Phase 10 approval):** the ROM is feature-complete, so the reserve only has to cover defects found in release qualification and on real hardware; the floors may go as low as the phase needs, not below 128 B: HOME 512 → 384 B, EXROM 256 → 128 B.

**As built (v0.11): budgets.** After Phase 9 (ledger L56-L60): HOME 15,796 B allocated, **reserve 588 B** (floor 512 B): page zero +12 B (`COLD_CLEAR`, §3.1), the float runtime −9 B (`F_POP`, which had no caller, found by the ROM coverage), the bank switch −2 B (delta D14, §2.1); EXROM 7,881 B allocated, **reserve 311 B** (floor 256 B): the shell +44 B (the undeclared identifier's name, §6.3; the key wait after a report, §6.1), the constant folding −22 B (`XC_FOLD`'s `&&` and `||`, which could not run, found by the ROM coverage).

**As built (v0.10): budgets.** `budget.toml` holds every component's budget, with the ledger of measured changes (L1-L55). After Phase 8: HOME 15,795 B allocated (the float runtime 145 B, the compiler 10,155 B, the platform 3,124 B), **reserve 589 B** (floor 512 B); EXROM 7,859 B allocated (the float core 1,464 B, the EXROM-resident compiler parts 1,481 B), **reserve 333 B** (floor 256 B). Bank rule 3's EXROM-resident compiler parts now include the keyword lookup and its table, `TY_EQUAL`, the library's binding, the directive processor (`#define`, `#undef`, `#include`, `#pragma`) and the float core's compile-time work (floating constants, constant float expressions): HOME reaches them through `CX_XCALL` and `CX_FOLD`, which page the EXROM in through the depth count; none touches chunk 6.

**As built (v0.9): tape blocks.** The EXROM's header logic reaches HOME's block I/O through the trampoline `TAPE_BLOCK` (page zero's trampoline budget, 14 B): it pages the EXROM out through the depth count for the one block and in again after it, so every block moves with chunk 6 = RAM, whether the shell or a program started the transfer. The stack stays outside chunk 6 (rule 2). The test harness checks this as a banking invariant on every transfer: HOME's `STORAGE_SEND_BLOCK` and `STORAGE_RECEIVE_BLOCK` never run with the EXROM paged in.

### 2.3 Page zero and RST assignment (baseline)

| Vector | Use                                                                                                                                              | Body placement                       |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| `$00`  | reset → cold start                                                                                                                               | fixed                                |
| `$08`  | `LDI` (HL = word at HL)                                                                                                                          | body in the slot (5 B)               |
| `$10`  | `STI` (word at DE = HL; HL kept)                                                                                                                 | body in the slot (6 B)               |
| `$18`  | `ENTER n` (frame setup, stack check)                                                                                                             | starts in the slot, `jp` to the rest |
| `$20`  | `LEAVE` (frame teardown, return)                                                                                                                 | body in the slot (5 B)               |
| `$28`  | `CMPLT` (signed DE < HL → carry)                                                                                                                 | `jp` to the body                     |
| `$30`  | **v0.7:** `LEX_NEXT`, the compiler's next token (owner decision, Phase 5). Was reserved for `LDL`/`STL` of the optional size template set (§5.6) | `jp` to the body                     |
| `$38`  | IM 1 interrupt (`call KBD_ISR_TICK; ei; reti`)                                                                                                   | fixed                                |
| `$66`  | NMI                                                                                                                                              | fixed                                |

Measured costs:

- CALL+RET 27 T; RST through a `jp` vector + RET 31 T.
- A body at the vector saves the `jp` (derived 21 T + body).
- The RST map is confirmed against operation frequencies measured on the Phase 2 test corpus.
- **v0.7 (Phase 5, owner decision):** RST `$30` serves the compiler instead of generated code. `LEX_NEXT` is the compiler's most frequent call (60 call sites); `rst $30` replaces each 3-byte `call`, saving 120 B of HOME (127 B with the jumps it brought into relative range), for 4 T per token. Generated code never uses it. The optional size template set (§5.6), if Phase 8 builds it, reaches `LDL`/`STL` by `call`.

### 2.4 The library jump table (v0.12, Phase 10)

A loaded library (§7.2) reaches the ROM's services only through a fixed jump table: **16 slots of `jp` (3 B each, 48 B) at `$3FD0-$3FFF`, the last bytes of HOME**, a pinned budget component above the code (`tools/budget.py`). The table never moves, and an `ASSERT` holds every slot at its address, so a library built against it runs on every ROM that keeps it (owner decision: V2-style slots, not only an identity word). **Rules** (V2's package ABI rules, `include/v2_package_abi.inc` at the V2 reference tag):

- a slot is never reordered, removed or repurposed; the unused slots are reserved (a call of one is runtime error 4);
- a new service takes the next reserved slot and raises the ABI version by one; a library declares the ABI it needs, and `LIB` refuses it on a ROM with a lower one (§8.4);
- anything else is a new magic, which every older library tape fails.

The single source of truth is `include/leapc_lib.inc`: HOME assembles each slot's `jp` from it and asserts the pins; a library's source gets each slot's address and each pin's value from it. **No slot serves the editor engine** (its fallbacks for unset hooks are gone, D15). **ABI 1:**

| Slot | Address | Name | Service | In | Out | Destroys |
| ---: | ------- | ---- | ------- | -- | --- | -------- |
| 0 | `$3FD0` | `LX_ARGS` | the arguments of the exported function that calls it first thing; records the program's call (`LIB_CALLER`) for runtime errors and BREAK | the function's return address and arguments on the stack | HL, DE, BC = the first three arguments | AF |
| 1 | `$3FD3` | `LX_PUTC` | a character at the print position (print attribute, inverse, over; `'\n'` a new line; wraps and scrolls) | A | | AF, BC, DE, HL |
| 2 | `$3FD6` | `LX_PUTS` | a string, the same | HL = the NUL-terminated text | | AF, BC, DE, HL |
| 3 | `$3FD9` | `LX_MALLOC` | a heap block (as `malloc`) | HL = the size | HL = the block, or 0 | AF, BC, DE |
| 4 | `$3FDC` | `LX_FREE` | a heap block freed (as `free`) | HL = the block (0: nothing) | | AF, HL |
| 5 | `$3FDF` | `LX_MUL` | 16-bit multiply | DE, HL | HL = DE × HL (DE kept) | AF, BC |
| 6 | `$3FE2` | `LX_DIVS` | signed divide (toward zero; 0 for a divisor of 0) | DE, HL | HL = DE / HL | AF, BC, DE |
| 7 | `$3FE5` | `LX_DIVU` | unsigned divide | DE, HL | HL = DE / HL, DE = DE % HL | AF, BC |
| 8 | `$3FE8` | `LX_FOP` | an operation of the float core on `F_ACC` (a BREAK-deferring section; overflow: runtime error 6 at the program's call) | A = `FOP_*`; HL = an integer (`FRI`, `FRU`) or the address of the left operand's 5 bytes (a binary operation) | `F_ACC`; HL (`TOI`, `FTOA`); flags (`CMP`) | AF, BC, DE, HL |
| 9 | `$3FEB` | `LX_ERROR` | end the program with a runtime error, reported at the program's call | A = the error (`RTE_*`) | does not return | |
| 10 | `$3FEE` | `LX_KEY` | wait for a key (BREAK ends the program) | | A = its code | AF |
| 11 | `$3FF1` | `LX_INKEY` | the key latched since the last read | | A = its code, or 0 | AF |
| 12 | `$3FF4` | `LX_FRAMES` | the frame counter | | HL = `FRAMES` | |
| 13 | `$3FF7` | `LX_PLOT` | a pixel in the print attribute and over mode, off the screen nothing (as `plot`) | HL = x, DE = y | | AF, BC, DE, HL |
| 14, 15 | `$3FFA`, `$3FFD` | reserved | runtime error 4 at the program's call | | | |

**Pinned names** (asserted by HOME, defined for libraries): `F_ACC` (`$5ED6`, the float accumulator, 5 bytes), `LIB_COL`/`LIB_ROW` (`$5EC2`/`$5EC3`, the print position), `LIB_ATTR` (`$5EC8`, the print attribute), the runtime errors `RTE_HEAP` 2, `RTE_ARG` 4, `RTE_FLOAT` 6, and the float operations `FOP_FRI` 0, `FRU` 1, `TOI` 2, `NEG` 3, `FTOA` 8, `ADD` `$80`, `SUB` `$82`, `SUBR` `$83`, `MUL` `$84`, `DIV` `$86`, `DIVR` `$87`, `CMP` `$88` (§4.9; a binary operation computes `(HL) op F_ACC`, the reversed ones `F_ACC op (HL)`).

---

## 3. Memory map (final, Phase 4)

### 3.1 Layout

Two principles:

1. **Source is resident and must be visible to the EXROM editor.**
2. **The program image** (compiled code and static data) prefers chunk 6, which is otherwise useless to a ROM language system.

The baseline moves the system variables to `$5B00` (assembly-time relocation; the kernel is symbolic apart from literals such as `MEM_COLD_INIT`'s `$8000`, which become symbols). That leaves one contiguous source region above the second display file.

| Range         | Bytes  | Use                                                                                              | Visible         |
| ------------- | ------:| ------------------------------------------------------------------------------------------------ | --------------- |
| `$4000-$5AFF` | 6,912  | display file 1 + attributes                                                                      | always          |
| `$5B00-$5D59` | 602    | kernel system variables (V2 layout, relocated)                                                   | always          |
| `$5D5A-$5FFF` | 678    | Leap-C fixed cells: shell/editor state, compiler state, 264-B source chunk window, runtime cells | always          |
| `$6000-$77FF` | 6,144  | display file 2 (dual-screen/hi-res mode) **or** program-image overflow                           | always          |
| `$7800-$BFFF` | 18,432 | **source store ↑** (line records); compile workspace ↓ (compile); heap (run)                     | always          |
| `$C000-$DFFF` | 8,192  | **program image region 1** (chunk 6: code ↑ from `$C000`, static data ↓ from `$DFFF`)            | EXROM paged out |
| `$E000-$F17F` | 4,480  | program image region 2                                                                           | always          |
| `$F180-$F3FF` | 640    | UDGs, edit buffer, misc. platform cells (V2 addresses)                                           | always          |
| `$F400-$F7FF` | 1,024  | program image region 3 (no V2 packages); (v0.12) or a loaded library (§7.2)                       | always          |
| `$F800-$FEFF` | 1,792  | machine stack (top `$FF00`); C locals live here                                                  | always          |
| `$FF00-$FFFF` | 256    | unused by the ROM (test harness return slot)                                                     | always          |

**Fallback layout B.** If the relocation meets a concrete blocker in Phase 4, the system variables stay at `$8000` and the source starts at `$825A`. The image regions are unchanged.

**All code refers to the layout only through symbols** in `include/leapc_layout.inc`, so tuning it means changing symbols, not rewriting code.

**As built (v0.6, final).** Baseline layout A is final: the relocation met no blocker (M1.1), so fallback B is not used. What each range holds:

| Range         | Holds (measured, `docs/milestones/M4.md`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$5B00-$5D59` | the platform system variables (602 B)                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `$5D5A-$5FFF` | the Leap-C cells: 507 B used (`LEAPC_CELLS_END` `$5F55`; v0.7: the shell's 63 B; v0.8: the report's 35 B; v0.9: the tape's 14 B: `TAPE_NAME`, `TAPE_ABORT`, `TAPE_DEST`; v0.10: the float accumulator `F_ACC` 6 B and the previous token's line `TOK_PLINE` 2 B; v0.12: a compile error's column `SH_ERR_COL` 2 B and `LIB_LOADED` 1 B, §7.2), 171 B free. The float core works in the platform's calculator variables (`CALC_STACK`, 40 B), which nothing else uses since the calculator is gone. (v0.12) `F_ACC`, `LIB_COL`, `LIB_ROW` and `LIB_ATTR` are pinned by the library ABI (§2.4): they never move |
| `$F180-$F3FF` | the V2 platform cells Leap-C keeps at their V2 addresses: `UDG_TABLE` (`$F180`, 168 B), `EDIT_LINE_BUF` (`$F228`, 128 B), `GFX_LINE_X0..Y1` (`$F3C4`, 4 B). The other 340 B are V2 cells nothing in Leap-C uses. (v0.11) The cold start clears `UDG_TABLE` as well as `$5B00-$BFFF` (`COLD_CLEAR`), so every byte the ROM reads after a boot is defined whatever the RAM held at power-on: from eight power-on patterns the idle prompt's RAM is the zeroed-RAM boot's, to the byte (`tools/poweron.py`) |
| `$F800-$FEFF` | the stack; `ENTER`'s floor `$F900` (§5.3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

**The layout guard.** `make check` proves from the listings that every RAM address the HOME and EXROM code references is a system variable or Leap-C cell, a display-file-1 constant, one of the platform cells above, a region boundary or an EXROM label; a cell anywhere else (source region, image region, stack, `$FF00-$FFFF`, an unused V2 cell) fails the build (`tools/check_ram_layout.py`, with 8 negative controls). `make test` runs a RAM canary over the whole corpus (`tools/canary.py`): neither the compile nor the run writes outside the RAM this map gives them.

### 3.2 Region rules

**Source store.**

- V2 line-store format `[len:2][text][CR]`, 127 characters per line at most, from `SRC_BASE` upward.
- The editor and the kernel's `MEM_LINE_*` routines manage it.

**Compile workspace.**

- Grows **down** from the top of the source region toward the source end: symbol tables, type descriptors, labels, string-literal staging, fixups.
- Workspace exhaustion is compile error *out of memory*.

**Program image.**

- Code grows **up** from the start of the current image region.
- Static data (globals, `static` locals, string literals, initialised arrays) grows **down** from its end.
- When a region is exhausted, the compiler continues in the next region: code with an emitted `jp` link, data by allocation.
- **Region order:** chunk 6 → `$E000-$F17F` → `$F400-$F7FF` → `$6000-$77FF`.
- Exhausting all regions is compile error *program too big*.

As built (v0.6):

- **Code.** Each instruction unit (at most 8 bytes) is placed only when 12 bytes are free below the region's data (`CG_GUARD`: the unit, a held operand's push and a linking `jp`). Otherwise the code continues in the next region in the order with 12 bytes free, linked by `jp`. A function, a loop or a `switch` can span regions; jumps and calls are absolute.
- **Data.** Each object (global, `static` local, string literal, `switch` table, function → line record) goes to the first region in the order with room for all of it, from the top down. An object never spans regions: the largest is 8,192 bytes (region 1). Data can go back to room left in an earlier region.
- Both meet without overlap: code never passes the data's low end, and data never comes below the code's reserved end.

**A loaded library (v0.12).** While a library is loaded (`LIB_LOADED`, §7.2), image region 3 is the library's: the compiler makes it full from the start of every compile (its limits `[end][end]`), as `#pragma hires` makes region 4, so neither code nor data is placed there and what region 3 would have held goes on to region 4. `IMAGE` (§6.3) leaves the region out. The library's own data in the region is not reset between runs.

**Hi-res protection.**

- The runtime's mode switch to dual-screen/hi-res mode fails with a runtime error if the image uses `$6000-$77FF`.
- A compile option (`#pragma hires`) reserves that region so the compiler never allocates it.

As built (v0.6): `#pragma hires` (§4.8) makes region 4 full from its line on (its limits become `[end][end]`); with no room in regions 1-3 the program is *program too big*. `mode(1)` succeeds while region 4 holds nothing: untouched, or reserved by the pragma. A late pragma cannot take back what is already in region 4 (code continues there if it already runs there; data placed there stays): `mode(1)` then gives runtime error 3. Put `#pragma hires` at the top of the program.

**Heap.** At run time, after the compile workspace is released:

- `[source end, source-region top)` is the heap, used by `malloc`/`free` (§7);
- the stack is `$F800-$FEFF`.

**Stack (as built, v0.6).** The program runs on its caller's stack; `ENTER` refuses a frame below `$F900` (§5.3). What runs between two frame checks (held expression operands, pending call arguments, a library routine, the IM 1 handler) is bounded by the compiler (§4.10) to at most 250 bytes, so the stack never leaves `$F800-$FEFF`. The compiler's own recursion stops at `$F8C0` (*nesting too deep*).

As built (v0.5): blocks `[size:2][data]` from the end of the source (made even) up to an end mark in the region's last word (`LIB_HEAP_END` `$BFFE`, a used block of size 0). A size counts its 2-byte header and is even; bit 15 is set while the block is in use. `malloc` searches first fit and joins the free blocks it passes; `free` clears the bit. Every program start sets up a new, empty heap, so a program interrupted inside `malloc` leaves nothing to repair.

**Static data** is zeroed or initialised by the program-start code before `main`.

### 3.3 Program state at run time (fixed)

- Program code and static data may be in chunk 6, so **programs run with EXROM paged out** (`BANK_EXROM_DEPTH = 0`, chunk 6 = RAM).
- Interrupts are enabled (IM 1).
- The ISR lives in HOME and uses the stack and system variables only. The spike measured this as safe over about 750 frames of chunk-6 execution.

---

## 4. Language: Release 1 subset of C

Leap-C Release 1 is a **documented subset of C89**, roughly Small-C 2.1 plus `unsigned`, `struct`, `enum`, `typedef`, function pointers, multi-dimensional arrays and (v0.10) `float`/`double`. Anything not listed is a compile error with a clear message ("not supported"), never silently miscompiled.

### 4.1 Lexical

- **Character set:** ASCII 32-126 plus CR line ends.
- **Case:** identifiers and keywords are **case-sensitive** (C semantics; unlike V2 BASIC).
- **Identifiers:** letter or `_`, then letters, digits and `_`. **31 significant characters.**
- **Keywords recognised:** the C89 set. `long`, `union` and `volatile` are reserved and give "not supported"; so does `long double`. (v0.10: `float` and `double` are supported, §4.9.)
- **Comments:** `/* … */` (may span lines) and `// …` (Leap-C extension).
- **Integer constants:**
  - decimal, `0x` hex, `0` octal, character constants;
  - value range 0-65535, typed per C89 rules for a 16-bit `int`;
  - suffixes `u`/`U` accepted; `l`/`L` gives "not supported".
- **Floating constants (v0.10, §4.9):**
  - digits with a decimal point, an exponent or both (`1.5`, `1.`, `.5`, `1e5`, `2.5E-3`); `08.5` and `09e1` are decimal;
  - suffixes `f`, `F`, `l`, `L` are accepted and change nothing (one floating type);
  - converted at compile time by the float core to the nearest 5-byte value; above about 1.7E38: `NUMBER TOO LARGE`; below about 2.9E-39: 0;
  - a malformed one (`1e`, `1e+`, `0x1.5`, `1.5ff`, `1e5u`, `1..2`): `BAD NUMBER`.
- **Character and string escapes:** `\n \t \r \0 \\ \' \" \a \b \f \v`, `\xhh`, `\ooo`.
- **String literals:** adjacent literals concatenate. Stored in static data, NUL-terminated.
- **Line length:** 127 characters (editor limit).

### 4.2 Types

| Type                                         | Size           | Notes                                                                                                                                          |
| -------------------------------------------- | --------------:| ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `char`                                       | 1              | **unsigned** (Z80-cheap zero-extension). `signed char` / `unsigned char` accepted; `signed char` sign-extends on promotion                     |
| `int`, `short`, `signed`                     | 2              | two's complement, wraparound                                                                                                                   |
| `unsigned`, `unsigned int`, `unsigned short` | 2              |                                                                                                                                                |
| pointers                                     | 2              | flat 16-bit address space; no far pointers                                                                                                     |
| `void`                                       | —              | function results, `void *`                                                                                                                     |
| arrays                                       | n × element    | any element type, including arrays (multi-dimensional) and structs                                                                             |
| `struct`                                     | sum of members | no padding (byte-aligned); members of any complete type; self-referential via pointers                                                         |
| `enum`                                       | 2              | constants are `int`                                                                                                                            |
| `float`, `double` (v0.10)                    | 5              | one type: the Sinclair 5-byte floating format, about 9.6 significant digits, magnitudes to about 1.7E38 (§4.9). `long double` is not supported |
| function                                     | —              | definitions, prototypes, pointers to functions                                                                                                 |
| `typedef`                                    | —              | names for any of the above                                                                                                                     |

**Qualifiers:**

- `const` is accepted and enforced only for direct assignment to a `const` object; it does not place data in ROM.
- `volatile` is reserved and gives "not supported" in Release 1.
- `register` and `auto` are accepted and ignored.

**Storage classes:**

- `static`: file scope = internal; block scope = static storage.
- `extern`: a declaration only; single translation unit.

### 4.3 Conversions

- **Integer promotions:** `char` → `int`.
- **Usual arithmetic conversions:** if either operand is `unsigned`, both are `unsigned`; otherwise `int`.
- **Comparisons, `/`, `%` and `>>`** use signed or unsigned operations according to the converted type.
- **Pointer arithmetic** scales by the element size.
- **Pointer differences** are divided by the element size and give an `int`.
- **Casts:** between integer types and between integer and pointer types; (v0.10) between integer and floating types.
- **Floating point (v0.10):**
  - if either operand of an arithmetic operator is floating, the other is converted to floating (the usual arithmetic conversions);
  - assignments, arguments with a prototype and return values convert between integer and floating types;
  - an integer converts exactly (any `int` or `unsigned` value);
  - a floating value converts to an integer type by truncation toward zero, keeping the low 16 bits of the integer part (8 for `char`). A value outside the type's range gives no error (C89 leaves it undefined);
  - there is no conversion between floating and pointer types, not even with a cast (`TYPE MISMATCH`).
- Assignment between incompatible pointer types needs a cast, except to and from `void *`. Violations are errors.

### 4.4 Expressions

All C89 operators except those on unsupported types:

- primary, postfix (`[] () . -> ++ --`);
- unary (`& * + - ~ ! ++ -- sizeof` and casts);
- multiplicative, additive, shifts, relational, equality, bitwise, logical (short-circuit);
- conditional `?:`, simple and compound assignment, and comma.

**Floating operands (v0.10):** `+ - * /` and their compound assignments, the comparisons, `! && || ?:`, unary `+ -`, `++ --`, casts, `sizeof`. `% << >> & | ^ ~` on a floating operand, a floating `switch` value, `case` label or array size are `BAD OPERAND TYPE` / `CONSTANT REQUIRED`. (v0.12) `?:` with one floating and one integer operand converts the integer operand to floating, as C89 6.3.15 requires (until v0.11 a documented deviation: `TYPE MISMATCH`): at run time on that operand's own path, after a constant condition the chosen operand; a pointer or `void` operand with a floating one is `TYPE MISMATCH`. Floating constant expressions are folded at compile time by the same float core as at run time, so a folded result equals the run-time one; they may initialise static objects and, through a cast to an integer type, size arrays and label `case`s.

**Constant expressions** are evaluated at compile time where C requires them: array sizes, `case` labels, `enum` values, static initialisers, and `sizeof`. The compiler also folds constant operands of `+ - * & | ^ << >>` where the template set allows.

**Implementation-defined choices:**

| Operation                                            | Behaviour                                                                                     |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Signed `/`                                           | truncates toward zero; the sign of `%` follows the dividend                                   |
| Division by zero                                     | quotient 0, remainder 0 (the ROM math routines); no trap                                      |
| `>>` on a signed value                               | arithmetic shift                                                                              |
| Signed overflow                                      | wraps                                                                                         |
| Floating overflow, floating division by zero (v0.10) | runtime error 6, `NUMBER TOO BIG`; in a constant expression, compile error `NUMBER TOO LARGE` |
| Floating underflow (v0.10)                           | 0                                                                                             |

### 4.5 Statements

**All C89 statements:**

- expression statements, compound blocks with declarations at the start of any block;
- `if`/`else`, `while`, `do`/`while`, `for`;
- `switch`/`case`/`default` (on `int`, `unsigned` or `char`);
- `break`, `continue`, `goto` and labels, `return`.

### 4.6 Functions

- **Definitions** in ANSI form (parameter types in the parameter list). K&R-style definitions are "not supported".
- **Prototypes** are optional. A call to an undeclared function declares it implicitly as `int f()` (C89) and is resolved by a fixup chain when the definition appears.
- When a prototype or definition is known, the argument count is checked and arguments are converted to the parameter types.
- **Parameters and return values:** scalars (v0.10: floats included) and pointers. Struct parameters and struct return values are "not supported" (use pointers). A floating argument takes 3 words of the stack (§5.2); without a prototype it is passed as it is (C89's promotion to `double` changes nothing here).
- **Recursion:** supported. About 10 B of stack per level for a one-parameter function with one local (measured).
- **Function pointers:** declaration, assignment, call through the pointer, arrays of function pointers.
- **Variadic functions:** only the library's `printf` family (§7). User-defined `...` functions are "not supported".
- **`main`:** `int main(void)` or `void main(void)`. Its return value becomes the program's exit status, shown by the shell.

### 4.7 Initialisers

- Scalars; arrays (including multi-dimensional) and structs of constant expressions, with brace elision allowed.
- `char` arrays from string literals.
- Automatic (local) scalars may use any expression, optionally in braces with a trailing comma (`int k = { 3 };`, v0.10). Automatic arrays and structs with initialisers are "not supported" in Release 1.
- (v0.10) Floating objects take arithmetic constant expressions (integers converted); integer objects may be initialised from floating constant expressions (truncated).
- **As built (v0.10):** the whole of C89 6.5.7 for static objects is covered by tests (`tests/decl/init/`): brace elision through nested aggregates, trailing commas, partial lists zero-filled, `[]` sized by its list, `char` arrays (and arrays of them, `signed`/`unsigned char` too) from strings, a string exactly filling its array without its NUL, address constants (objects, elements of multi-dimensional arrays, members, a string literal plus an offset, functions defined later), `extern` with an initialiser at file scope (a definition).

### 4.8 Preprocessor (Release 1)

- `#define NAME replacement-tokens` (object-like) and `#undef NAME`.
- `#include <leap.h>` / `#include "leap.h"` are accepted. The platform declarations are always built in (§7), so the directive is a no-op.
- Other directives (function-like macros, `#if` family, `#error`, `#line`, `#pragma` apart from `#pragma hires`) give "not supported". So does `#include` of any other header.
- **As built (v0.4):**
  - A directive is a `#` that is the first token on its line; `#` alone is ignored.
  - A macro's replacement is the rest of its line. It is checked for lexical errors at the `#define` and expanded where the macro is used. Its tokens carry the line of the use.
  - A macro's name inside its own expansion, directly or through other macros, stays an identifier (C89 6.8.3.4).
  - Defining a macro that is already defined is `ALREADY DEFINED`, also for an identical replacement (C89 allows that one; deviation). `#undef` it first.
  - Macro names are identifiers; a keyword cannot be one.
- **`#pragma hires` (as built, v0.6):** reserves image region 4 (display file 2) from its line on (§3.2). The pragma's name is case-sensitive and never macro-expanded (no directive's tokens are); `#pragma` with any other name, or none, is "not supported"; anything after `hires` on the line is a syntax error. It may appear more than once and wherever a directive may.

### 4.9 Floating point (v0.10: Release 1)

Until v0.9 floating point was an optional component deferred to an owner decision. Phase 8 implemented it in Release 1, under the owner's direction to do so if it fits the ROMs without losing existing function (`docs/milestones/M8.md`).

**The type.** `float` and `double` are the same type: the **Sinclair 5-byte format** of the TS2068 and Spectrum ROMs, documented as non-IEEE.

- `[exponent e][sign | mantissa bits 30-24][23-16][15-8][7-0]`: the value is 0.1m × 2^(e − 128) with the mantissa's leading 1 implicit; e = 0 is zero.
- 32 bits of mantissa: about 9.6 significant decimal digits. Largest magnitude 1.7014118E38, smallest 2.9387359E-39. No infinities, NaNs or denormals; −0 is 0.
- Leap-C always writes the normalised form (never the ROM's small-integer form).

**Arithmetic (the float core).**

- `+ - * /` on a 40-bit mantissa (32 bits and a guard byte), rounded to nearest when packed. Comparisons are exact.
- Overflow and division by zero: runtime error 6 (`NUMBER TOO BIG`, Spectrum BASIC's report 6) at the line of the function whose code failed; in a constant expression, compile error 16. Underflow gives 0.
- Integer to float is exact; float to integer truncates toward zero and keeps the low 16 bits of the integer part (§4.3).
- Floating constants: one correctly rounded operation per constant for decimal exponents up to ±13 (an exact table of powers of ten), repeated scaling beyond.
- Output: `printf`'s `%f` (§7.1): every integer digit, the decimals rounded half up from the binary value's exact expansion.

**Measured (production ROM, T-states per operation including the trampoline's paging, about 1,580 T):** add 2,125 (9,773 with a 32-bit alignment shift), subtract 2,942, compare 1,261, multiply 20,090, divide 36,111, negate 629, int → float 1,947, unsigned → float 1,378, float → int 4,883; `%.6f` of 3.14159265 24,463 T, `%.9f` of 1.7E38 (39 digits) 31,787 T.

**Architecture (as built).**

- **The float core** (`src/runtime/fpcore.asm`, EXROM, 1,464 B) is the V2 calculator (`platform/rom/exrom_calc.asm`, 1,929 B, and V2's float formatting, 236 B) re-engineered, so the ROMs keep one numerical engine. Kept: the number format, the calculator's working RAM (`CALC_STACK`), V2's exact fixed-point formatting. Changed: C calls each operation directly (`A` = `FOP_*`), so the RST `$28` literal-stream interpreter and its stack operations are gone; the arithmetic works on a 40-bit mantissa with byte loops; comparison, negation, `++`/`--`, both conversions, decimal input and a precision for the output are new. It saves 701 B of EXROM against the calculator and formatting it replaces.
- **Compiled code** reaches it through HOME's `F_OP` (`call F_OP / db op`) and `F_X`: a `NOBRK` section that pages the EXROM in through the depth count (bank rules 1-2). Values are computed in `F_ACC`; held operands and arguments are 3-word stack slots, never in chunk 6 (§5.1-§5.3).
- **The compiler** converts floating constants and folds constant float expressions through `CX_FOLD` with the same core.
- **ROM cost** (ledger L42-L55): the EXROM float core 1,464 B; HOME's float runtime 145 B; the compiler's float code (expressions +501 B, code generation +197 B, declarations and initialisers +73 B, lexer +43 B) and `printf`'s `%f` (+51 B): 1,010 B of HOME. It is paid by the calculator's 701 B, by moving cold compiler code to the EXROM (HOME: the keyword lookup and table 276 B, `TY_EQUAL` 137 B, the library's binding 93 B, the directives 238 B; 727 B net of the trampoline and stubs) and the editor-only platform routines (deltas D11, D12: 176 B).

**Not in Release 1:** a math library (`sqrt`, `sin`, `exp`, ...: short in C, `docs/EXAMPLES.md`), `long double`, `printf`'s `%e`/`%g`, conversion of text to float at run time (`atof`).

### 4.10 Limits (baseline; all memory-bound unless stated)

| Item                                                         | Limit                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identifier significance                                      | 31 characters                                                                                                                                                                                                                                                                                                                                             |
| Line length                                                  | 127 characters                                                                                                                                                                                                                                                                                                                                            |
| Nesting depth (blocks, expressions)                          | bounded by the compiler's stack guard; at least 32 levels guaranteed (measured, v0.6: §4.10.1)                                                                                                                                                                                                                                                            |
| Function parameters                                          | 16                                                                                                                                                                                                                                                                                                                                                        |
| Argument words pending at once (v0.6)                        | 32: the arguments a call pushes and those already pushed by the calls whose arguments contain it ("nesting too deep"). A single call to a function without a prototype (or `printf`) can pass 32 words. It bounds the stack between two frame checks (§3.2). (v0.10) A float argument, and a float operand held while another is computed, counts 3 words |
| Local frame size                                             | 255 bytes (8-bit frame offsets; larger locals → "frame too large"; use `static` or the heap). A float local takes 5 bytes                                                                                                                                                                                                                                 |
| `switch` cases                                               | memory-bound (6 B of compile workspace per case)                                                                                                                                                                                                                                                                                                          |
| Macro expansions nested in one another                       | 8 ("nesting too deep")                                                                                                                                                                                                                                                                                                                                    |
| Tokens produced by one macro expansion, nested ones included | 255 ("nesting too deep")                                                                                                                                                                                                                                                                                                                                  |
| String literal length                                        | one line, 126 characters (adjacent literals concatenate)                                                                                                                                                                                                                                                                                                  |

#### 4.10.1 Measured capacity (v0.6)

Measured on the production ROM (`tools/capacity.py`, `make capacity`; every limit is a verified pair: the largest that compiles or runs, and one more that fails with the error shown):

| Item                                                                                         | Measured limit                                                                                                                                                                                                 | One more                         |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Source, minimal program (comments and `main`)                                                | 18,412 B of line store (`PROG_END` $BFEC); workspace 20 B                                                                                                                                                      | E_NOMEM                          |
| Source, typical program (76 modules: a global array, a function with a loop, locals, a call) | 15,087 B of line store, 851 lines (13,385 B of text); workspace 3,255 B; image 11,059 B of code, 1,678 B of data; compile 8.38 ms per line                                                                     | E_NOMEM                          |
| Image: code (macro-expanded statements, 43 functions)                                        | 19,411 B of code and 266 B of data of 19,840 B (region 1: 8,074 code, 116 data, 2 free; region 2: 4,419 code, 60 data, 1 free; region 3: 1,010 code, 12 data, 2 free; region 4: 5,908 code, 78 data, 158 free) | E_TOOBIG                         |
| Image: the largest single object                                                             | 8,192 B (region 1; an object never spans regions)                                                                                                                                                              | E_TOOBIG                         |
| Image: all static data, with a minimal program                                               | 19,817 B                                                                                                                                                                                                       | E_TOOBIG                         |
| Recursion: reference: 1 int parameter, 1 int local                                           | 190 levels from `main`                                                                                                                                                                                         | stack overflow (runtime error 1) |
| Recursion: no parameter, no local                                                            | 381 levels from `main`                                                                                                                                                                                         | stack overflow (runtime error 1) |
| Recursion: 4 int parameters, 10 int locals                                                   | 47 levels from `main`                                                                                                                                                                                          | stack overflow (runtime error 1) |
| Heap: the largest block, minimal program                                                     | 18,316 B (first block's data at $7872)                                                                                                                                                                         | NULL                             |
| Heap: the largest block with a large source                                                  | 234 B (18,193 B of source, 300 B below the minimal program's limit; at the limit itself 16 B)                                                                                                                  | NULL                             |
| Nesting: parentheses                                                                         | 112 levels                                                                                                                                                                                                     | E_NESTING                        |
| Nesting: held operands                                                                       | 60 levels                                                                                                                                                                                                      | E_NESTING                        |
| Nesting: blocks                                                                              | 154 levels                                                                                                                                                                                                     | E_NESTING                        |
| Nesting: if                                                                                  | 386 levels                                                                                                                                                                                                     | E_NESTING                        |
| Nesting: while                                                                               | 193 levels                                                                                                                                                                                                     | E_NESTING                        |
| Nesting: nested calls                                                                        | 60 levels                                                                                                                                                                                                      | E_NESTING                        |
| Nesting: struct members                                                                      | 274 levels                                                                                                                                                                                                     | E_NOMEM                          |

- **The source region is the binding limit for ordinary programs.** Source and compile workspace share `$7800-$BFFF` (18,432 B); the image has its own 19,840 B. The typical program above reaches *out of memory* with 12.7 KB of image, so about 7 KB of image stays unused. (The feasibility study's 21.5 KB assumed source and code shared one pool.) Its workspace is about 43 B per module; per declaration: 13 B for a global scalar, a local or a struct member (with a 4-character name), 20 B for an array, 24 B for a two-parameter prototype.
- Locals are on the stack: frames from `main` down to `$F900` (1,522 B from the harness's call; the shell's own frames reduce it slightly).
- Every nesting limit is above the 32 levels guaranteed; *nesting too deep* is the compiler's stack guard.

---

## 5. Runtime ABI (fixed unless a measured blocker appears)

### 5.1 Registers

| Register                           | Role                                                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| HL                                 | primary accumulator, return value (`char` in L with H = 0, or H = sign for `signed char`)                 |
| `F_ACC` (a 5-byte RAM cell, v0.10) | the floating accumulator: a float value being computed, and a function's float result                     |
| DE                                 | secondary operand                                                                                         |
| BC, A, flags                       | scratch                                                                                                   |
| IX                                 | frame base                                                                                                |
| IY                                 | reserved (unused by compiled code and the kernel)                                                         |
| Alternate set                      | unused by compiled code. Library routines may use `AF'` within a call (v0.5); nothing keeps a value there |

The V2 kernel uses no IX/IY (verified).

### 5.2 Calling convention and frame

- **Arguments** are pushed **right to left** as 16-bit words (`char` promoted). The **caller removes them** (`pop bc` per word). (v0.10) A float argument is a 3-word slot: its 5 bytes, lowest address first, and a pad byte (`F_PUSH`); a float parameter's offset counts 6 bytes.
- `call f`; the result is in HL (a float result: in `F_ACC`).
- **The callee preserves IX and IY.** It may destroy AF, BC, DE, HL.

Frame (IX = frame base after the prologue: the saved IX):

```
IX-N … IX-1     locals (N ≤ 255)
IX+0            saved IX
IX+2            return address
IX+4 …          arguments, first argument lowest
```

Calls through a function pointer use `call CALLHL` (`jp (hl)`).

**Owner decision 2026-10-13 (M1.3).** v0.1 put IX at the lowest local (locals at `IX+0`, arguments at `IX+N+4`). Two facts make that unworkable for a single-pass compiler with inline frame access (§5.5): the frame size N is known only at the end of the function body, after its parameters have been used; and the Z80's `(ix+d)` displacement is signed (−128…+127), so arguments beyond `IX+127` cannot be reached inline at all. The stack's memory layout is unchanged; only IX's reference point moved, so argument offsets (`IX+4+2k`) and local offsets are known when they are used. Locals more than 128 bytes below IX are reached through an address template (`push ix / pop hl / ld bc,d / add hl,bc`).

### 5.3 Helper core (HOME)

Measured in the code-shape spike unless marked:

| Helper                                                               | Entry                                                         | Contract                                                                                                                                                                                                                                                                                              |
| -------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LDI`                                                                | RST `$08`                                                     | HL = (HL); destroys A                                                                                                                                                                                                                                                                                 |
| `STI`                                                                | RST `$10`                                                     | (DE) = HL; HL kept; DE = address + 1                                                                                                                                                                                                                                                                  |
| `ENTER n`                                                            | RST `$18` + byte                                              | push IX; IX = SP; SP -= n; **stack check** against `STACK_LIMIT` (runtime error *stack overflow*). As built (v0.6): the new SP is checked before SP moves, against the page-aligned floor `LEAPC_RT_STACK_FLOOR` = `$F900` (the margin above `$F800` covers what runs between two frame checks, §3.2) |
| `LEAVE`                                                              | RST `$20`                                                     | SP = IX; pop IX; return to the caller; HL kept                                                                                                                                                                                                                                                        |
| `CMPLT`                                                              | RST `$28`                                                     | signed compare: carry ⇔ DE < HL                                                                                                                                                                                                                                                                       |
| `CMPULT`                                                             | inline                                                        | unsigned `or a; sbc hl,de` (3 B)                                                                                                                                                                                                                                                                      |
| Shifts by a variable count (`SHL`, `SHR`, `SAR`)                     | CALL                                                          |                                                                                                                                                                                                                                                                                                       |
| `MUL`, `DIVS`, `DIVU`, `MODS`, `MODU`                                | CALL                                                          | the helper core's register-only shift-and-add multiply and restoring divide (v0.3; they replace the V2 math). The compiler's constant arithmetic uses the same routines. (v0.12) The divide's 16 steps lost a branch that could never run (before step i the remainder is below 2^(i−1)): 112 T less a division, 60000 / 7 in 1,479 T |
| `SWITCH`                                                             | CALL + inline table address                                   | `call RT_SWITCH / dw table`. The table is static data, made after the switch's body. Sparse: `[n][default]` then `[value][address]` pairs. Dense, when smaller (highest − lowest ≤ 2n − 3): `[range \| $8000][default][lowest]` then one address per value                                            |
| `CALLHL`                                                             | CALL                                                          | indirect function call                                                                                                                                                                                                                                                                                |
| `F_OP` (v0.10)                                                       | CALL + op byte                                                | an operation of the float core (§4.9) on `F_ACC`; a binary one pops its left operand's slot. Through `F_X`, a `NOBRK` section with the EXROM paged in                                                                                                                                                 |
| `F_PUSH`, `F_POP`, `F_DROP` (v0.10)                                  | CALL                                                          | `F_ACC` to and from a 3-word stack slot under the return address                                                                                                                                                                                                                                      |
| `F_LD`, `F_ST`, `F_LDX`, `F_STX`, `F_LDK`, `F_TST`, `F_REST` (v0.10) | CALL (`F_LDX`/`F_STX` + displacement byte, `F_LDK` + 5 bytes) | `F_ACC` from or to the float at HL or at `IX+d`, from an inline constant; Z when `F_ACC` is 0; the value before a postfix `++`/`--`                                                                                                                                                                   |
| `LDL`/`STL` (size set only)                                          | CALL + byte (v0.7: RST `$30` is `LEX_NEXT`, §2.3)             | local word load/store, as measured in the spike (there through RST `$30`)                                                                                                                                                                                                                             |

### 5.4 Code-generation model (fixed)

- **Single pass**, recursive descent, **no IR**. Code is emitted directly into the image region by fixed **templates**.
- HL/DE primary/secondary; temporaries on the machine stack.

### 5.5 Default template set: "mixed" (fixed default)

**Inline:**

- local and parameter access: `ld l,(ix+d)` / `ld h,(ix+d+1)` and the matching stores;
- globals: `ld hl,(nn)` / `ld (nn),hl`;
- constants, `add hl,de`, increment/decrement, unsigned compare;
- byte loads/stores (`ld l,(hl); ld h,0` / `ld a,l; ld (de),a`);
- conditional jumps.

**Helpers:**

- word load/store through pointers (RST `LDI`/`STI`);
- frame entry and exit (RST `ENTER`/`LEAVE`);
- signed compare (RST `CMPLT`);
- multiply/divide/modulus, variable shifts and `switch` (CALL);
- all platform services (CALL).

**Measured** on the spike workloads: 80% of the bytes of all-inline code, 0-26% slower, 5.4-17× faster than V2 BASIC.

### 5.6 Optional size template set (later)

All-compact templates (local access through RST `LDL`/`STL`) were measured at 49% of the inline bytes and 2.7-3.3× slower. They are reserved as an optional size mode (`#pragma size`), implemented only if Phase 8 measurements show a capacity need. **v0.7:** RST `$30` now serves the compiler (§2.3), so such a set would reach `LDL`/`STL` by `call` (3 B instead of 1 per access, and 6 T more); Phase 4 measured the source region, not the image, as the binding limit (§4.10.1).

### 5.7 Program start and exit

**Start, in HOME runtime (`RT_RUN`):**

1. Page EXROM out.
2. Set SP = `$FF00` and record `RUN_SP`.
3. Zero or initialise static data.
4. Set `STACK_LIMIT`, initialise the heap and set `RUNNING = 1`.
5. `call main`.

**As built (v0.5):**

- The program runs on its caller's stack (the shell's: a few words below `$FF00`), not from `$FF00`, so `RT_RUN` returns to its caller; `RUN_SP` is the stack at its call of `main`. The stack limit is the constant `LEAPC_RT_STACK_FLOOR` (ENTER's check).
- Static data is not copied at the start: the compiler writes it into the image with its initial values (zero by default), and `RUN` always compiles first.
- Every start clears the run state (`RT_STATE`: error, BREAK request, `NOBRK`, `rand()`'s state, the print position, inverse and over), sets the colours to paper 7 / ink 0 and sets up an empty heap.

**Exit.** On return from `main`, `exit(n)`, a runtime error or BREAK, the runtime:

1. silences AY channel A;
2. restores the display state (normal mode, not hi-res) only if the program changed it — baseline behaviour, confirmed in Phase 3;
3. restores `BANK_EXROM_DEPTH` and the paging state the shell expects;
4. clears `RUNNING` and returns to the shell with a status code (exit value, runtime error number, or BREAK).

**As built (v0.5):** every end returns through `RUN_SP` to `RT_RUN`, which clears `RUNNING` (with interrupts off for that instant), maps a failing address to its source line (§5.9), sets the volumes of **all three** AY channels to 0, sets the normal display mode (unconditionally: no visible change when it already is), restores the caller's paging depth and IX, and returns A = 0 with HL = the exit status, or A = the runtime error. Not restored: the border, the screen's contents and colours (the shell redraws them).

### 5.8 BREAK (fixed requirement; baseline mechanism)

**Requirement:** BREAK (CAPS SHIFT + SPACE) stops a running program and returns to the editor with the source intact. Native code has no dispatch loop to poll.

**Baseline mechanism:**

- When the ISR decodes BREAK while `RUNNING = 1` and the no-break counter `NOBRK = 0`, it discards the interrupted context by restoring SP = `RUN_SP` and jumps to the runtime's BREAK exit, which re-normalises paging and sound.
- Runtime sections that must not be interrupted mid-way increment `NOBRK` and set `BRKPEND` on a deferred request; the exit of such a section honours `BRKPEND`. These sections are EXROM trampolines, tape I/O, AY sequences and heap updates.
- Cost: about 20-40 B in the ISR delta (estimate; measured in Phase 3).
- `PAUSE`-style waits in the library end on BREAK.

**As built (v0.5):**

- The ISR (platform delta D4) calls `RT_BREAKREQ` when it accepts the BREAK key, after latching it as usual. With no program running it is an ordinary key. Otherwise `RT_BREAKREQ` sets `BRK_HALT` (`BRKPEND`; the platform's `VM_HALTED`) and, if `NOBRK` is 0, ends the program at once with runtime error 5: the ISR's frame is dropped with the program's stack.
- `NOBRK` sections: the EXROM trampolines of `beep()`, (v0.9) `tape_save()` / `tape_load()` and (v0.10) the float core (`F_X`: every float operation and `printf`'s `%f`), the EXROM services programs use in Release 1. The beep's wait ends early on `BRK_HALT`, the trampoline pages the EXROM out and silences the AY, and its end (`RT_NOBRK_END`) then stops the program. **Heap updates are not deferred** (deviation): the heap belongs to one run and is set up again at the next start, so an interrupted `malloc` leaves nothing that must be consistent. AY register writes are single `OUT` pairs that the exit's silencing re-selects.
- `pause()` and every other wait end on BREAK through the immediate unwind.
- **A loaded library (v0.12, §7.2).** While a library is loaded, image region 3 holds no program code, so BREAK there is BREAK in the library: it ends the program at the library's last call from the program (`LIB_CALLER`, recorded by the library's `LX_ARGS`), as BREAK in the ROM's library does. In a ROM service the library called, the same. The library's float operations (`LX_FOP`) are `NOBRK` sections, as the program's are.
- **Tape (v0.9).** While a tape block moves, interrupts are off (the ROM's tape routines), so the ISR cannot see BREAK; the routines themselves test SPACE (the stock ROM's rule: BREAK is CAPS SHIFT + SPACE) at every edge and after every byte sent, and abort. `tape_save()` / `tape_load()` then end the program with BREAK (runtime error 5, at the line of the function that called them); a BREAK the ISR accepted between two blocks waits for the section's end, as for `beep()`.
- Cost (measured): the ISR delta is 8 B (V2's BREAK latch, 14 B, removed); the runtime's request and BREAK exit 32 B, the section end 12 B. The ISR's per-frame cost is unchanged: the delta runs only on the frame that accepts a key.

### 5.9 Runtime errors

| Code | Error                                                                                     |
| ---- | ----------------------------------------------------------------------------------------- |
| 1    | stack overflow (from `ENTER`)                                                             |
| 2    | out of heap (`malloc` returns NULL; error only for library calls that cannot report NULL) |
| 3    | hi-res mode with the image in `$6000-$77FF`                                               |
| 4    | invalid library argument (where checked)                                                  |
| 5    | BREAK                                                                                     |
| 6    | (v0.10) a floating overflow or division by zero (`F_OP`)                                  |

The shell shows `RUNTIME ERROR n` with the source line of the failing function's call site where available.

**As built (v0.8):** the shell's report is `RUNTIME ERROR n: MESSAGE` with the messages `1: STACK OVERFLOW`, `2: OUT OF HEAP`, `3: HI-RES IN USE`, `4: BAD ARGUMENT`, (v0.10) `6: NUMBER TOO BIG`; BREAK is reported as `BREAK` (§6.3). The line mapping comes from a function → line table the compiler emits: one record per function definition in the image's static data, `[link][address][line where the definition starts]`, newest first, from `RUN_FNLINES` (as built in Phase 2: 6 B per function).

**As built (v0.5):** every error records an address in the failing code (`RT_ERRPC`); at the end, `RT_ERRLOC` takes the newest record of the table that starts at most 8 KB before it, and `RT_ERRLINE` is the line where that function's definition starts (0 if none). The address is:

- stack overflow: the code of the function being entered;
- a library error (codes 3, 4) and (v0.10) a float error (code 6): the program's address of the library call or of the `F_OP` call (`LIB_CALLER`, recorded by every library function that takes arguments, and by `getkey()`), so the line is that of the function that called the library;
- BREAK: the interrupted address if it is in the program's image; in the ROM (a library or platform routine, a helper), the last library call.

**A loaded library (v0.12, §7.2).** A runtime error the library raises (`LX_ERROR`), or one in a ROM service it calls (a float overflow in `LX_FOP`, a reserved slot), is reported at the line of the program's function that called the library (`LIB_CALLER`, which `LX_ARGS` records and the services never change), as for the ROM's library. A library function must call `LX_ARGS` first for this.

No library function raises error 2 in Release 1: `malloc` returns NULL. Error 4 is raised by `beep()` (semitone), `sound()` (register), `mode()` (mode), `itoa()` (base) and `sprite_get()`/`sprite_put()` (rectangle).

No bounds or NULL checks are generated; this is C.

**Image region 4 (v0.6).** Region 4 (`$6000`) lies below region 1 in memory although it comes last in the allocation order, so a failure in the part of a function that started in region 3 and continues in region 4 has no function starting at most 8 KB below it: its line is 0 (unknown), never a wrong line. Functions that start in region 4 report their lines.

---

## 6. Editor, shell and keyboard

### 6.1 Editor and shell

These come from V2's full-screen editor and shell glue, adapted:

- **Editing behaviour kept:** line editing, navigation, scrolling, redraw and flicker safeguards, status bar, error-line jump.
- **Keyword highlighting** uses the C keyword table.
- **Commands:**

| Command                   | Action                                         |
| ------------------------- | ---------------------------------------------- |
| `RUN`                     | compile and execute                            |
| `LIST`                    | list the source                                |
| `NEW`                     | clear the source                               |
| `SAVE "name"`             | save the source to tape                        |
| `LOAD "name"` / `LOAD ""` | load source from tape                          |
| `VERIFY "name"`           | verify a saved tape                            |
| `FREE`                    | show free source space and the last image size |
| `LIB "name"` / `LIB ""` (v0.12) | load a library from tape (§7.2, §8.4)    |
| `LIB` (v0.12)             | unload the library                             |

- No immediate-statement mode in Release 1 (C has no statements outside functions).

**As built (v0.7, Phase 5).** The shell (`src/shell/shell.asm`, EXROM) is V2's shell glue adapted routine by routine; the editor engine (`rom/exrom_editor.asm`) is the vendored one, unchanged.

- **Screen.** Rows 0-22 show the source; row 23 is the status row (`LINE n/m`: the cursor's line and the line count, white on black with V2's red, green and blue swatch), also used for messages. A line longer than 32 characters wraps at its last space (or at 32 characters) onto up to four rows.
- **Keys** (the platform's): CAPS SHIFT + 5/8 move left/right, + 7/6 up/down (between the rows of a wrapped line first), + 0 is DELETE (on an empty line it deletes the line), + 1 deletes the line, + ENTER inserts an empty line before it; ENTER stores the line. BREAK does nothing in the editor.
- **Editing** keeps V2's rules: leaving a line with UP, DOWN or insert line stores an edit first, as ENTER does; a line that does not fit gives `PROGRAM FULL` and stays in the edit buffer.
- **The view** shows up to 20 lines above the cursor's line (V2), fewer when they wrap onto more rows than there are above it: the cursor's line is always whole on the screen (V2 could push it off the screen).
- **Redraw.** Typing redraws only the cursor's line, or, when the line starts or stops wrapping onto another row, that line and the ones below it (V2 redrew the whole screen then); UP and DOWN near the top redraw only the two lines involved; LEFT and RIGHT move only the cursor. A key clears the whole screen only when the view moves (measured: no typed key clears it in any of the test scenarios). Typing costs 47 kT per key on V2's 10-line typing scenario (V2: 72 kT) and at most V2's cost in all of V2's scenarios (`docs/milestones/M5.md` §6).
- **Keyword highlighting.** A line not being edited shows its C keywords in bold as typed, from the compiler's own keyword table (no copy in the EXROM). Not keywords: identifiers that contain one (`int1`, `_if`), case variants (`INT`), and the text of string literals, character constants and comments. Each line is scanned on its own: a line inside a `/* ... */` comment begun on an earlier line is highlighted as code.
- **Commands** are recognised only on the append line (the empty line after the last), alone on the line apart from spaces, in any case; anything else is stored as source. Phase 5 builds `RUN`, `LIST` and `NEW`; Phase 6 `FREE` and the reports (§6.3); Phase 7 `SAVE`, `LOAD` and `VERIFY` (below).
- **`FREE`** (v0.8) reports on rows 22-23 `SOURCE s B  FREE f B` (the source's size in the line store, and the room left for it: up to `VARS_START`, the line store's ceiling) and `IMAGE i B  HEAP h B` (the image of the last successful compile, 0 before any; the heap a program would have with the source as it is). A key returns to the editor as it was.
- **`LIST`** shows the source a page (23 rows) at a time with keywords bold; a line that does not fit starts the next page; a key shows the next page, BREAK ends the listing.
- **`SAVE "name"`, `LOAD "name"`, `LOAD ""`, `VERIFY "name"`, `VERIFY ""`** (v0.9, Phase 7; the tapes: §8.1). The word, in any case, then spaces (or none) and a quote make a tape command (no C line starts so); `SAVE` alone, or `save(x);`, is source. The name is 1-10 characters for `SAVE`, 0-10 for `LOAD` and `VERIFY` (`""`: the next program tape, any name); only spaces may follow its closing quote, else `BAD NAME`. While the tape moves, the status row shows `SAVING name`, `LOADING` / `VERIFYING` while it searches, and `LOADING name` / `VERIFYING name` once the header is found (drawn between the blocks, never inside one). Each command ends with a report on rows 22-23 until a key, as `RUN`'s (§6.3); row 23 is `SOURCE s B  FREE f B` (as `FREE`'s first row) for every outcome:

| Command  | Row 22                                                                                                                                                             |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SAVE`   | `SAVED name`; `BREAK` (SPACE stopped it: no data block follows); `BAD NAME`; `NO PROGRAM` (an empty source: a block of no bytes cannot be loaded)                  |
| `LOAD`   | `LOADED name` (the tape's name): the source is replaced, the cursor on the append line after its last line; `LOAD FAILED`; `BAD TAPE VERSION`; `BREAK`; `BAD NAME` |
| `VERIFY` | `VERIFIED name`: the tape holds exactly the source, and ends where it does; `VERIFY FAILED`; `BAD TAPE VERSION`; `BREAK`; `BAD NAME`. Nothing is written           |

  A failed `LOAD` leaves the source and the editor as they were (§8.1: the program arrives above the source and replaces it only when it is whole and sound), except when the tape's program does not fit above the source and part of it was received: then the source is empty, as after `NEW` (V2's rule: it cannot be trusted). (v0.12) That includes BREAK once part of such a program had arrived: until v0.11 it was reported as BREAK and kept the partly overwritten source.

**As built (v0.12): `LIB`.** `LIB "name"` (1-10 characters) or `LIB ""` (the next library tape, any name), in any case, then spaces and a quote, as the tape commands (§7.2, §8.4). The status row shows `LOADING` and `LOADING name` as for `LOAD`; the report on rows 22-23 until a key:

| Row 22 | When |
| ------ | ---- |
| `LIBRARY name: n FUNCTIONS` | the library arrived whole: its name (the tape's), and its export count |
| `BAD TAPE VERSION` | another magic, or an ABI above this ROM's: refused at the header, nothing written |
| `LOAD FAILED` | no such tape before the search gives up (about 2 minutes), a length above 1,024 B (refused at the header), a bad block |
| `BREAK` | SPACE stopped it |
| `BAD NAME` | more than 10 characters, no closing quote, more after it |

  Row 23 is `SOURCE s B  FREE f B`, as for the tape commands. As `LOAD`'s program, the library arrives above the source when there is room and moves into image region 3 only once it is whole; otherwise it goes straight into the region. A failure that wrote into the region (straight in, and a bad block or BREAK during its data) leaves no library loaded; any other failure keeps the library loaded before it. `LIB` alone (any case, spaces after it) unloads the library: the status row shows `NO LIBRARY` until a key. **`NEW` and `LOAD` keep the library** (decided in Phase 10: it belongs to the machine's session, not to the program; a program LOADed from tape can then use it at once, and `LIB` alone unloads it; V2's `NEW` unloaded its package). **A reset clears it** (the cold start clears `LIB_LOADED`; the region keeps its bytes). A second `LIB` replaces the first library.

**As built (v0.11): the key after a report.** A report or a status-row message (and `LIST`'s pages) waits for a key pressed after every key held before it is released: a key still down from the command (the ENTER of `RUN`, BREAK) is let go first, and a key latched before or meanwhile, its auto-repeat included, is dropped (`SH_WAIT_KEY`). Until Phase 9 a key held past the keyboard's repeat delay (35 frames, about 0.6 s on a TS2068) ended the report itself, before it could be read: Fuse's 60 Hz keyboard showed it (`docs/milestones/M9.md`). The editing keys on the keyboard matrix (CAPS SHIFT + 5 6 7 8 0, + 1 delete line, + ENTER insert line) are tested against their codes; two letters pressed together type nothing.

### 6.2 C punctuation (baseline mapping; physical legends need owner confirmation)

The V2 key map cannot produce the 8 characters C needs, and the font lacks their glyphs. Leap-C adds both, using symbol-shift positions that V2 leaves unmapped and that match the Spectrum-family legends where they exist:

| Key (SYMBOL SHIFT +) | Y   | U   | F   | G   | S    | A   | H   | D   |
| -------------------- | --- | --- | --- | --- | ---- | --- | --- | --- |
| Character            | `[` | `]` | `{` | `}` | `\|` | `~` | `^` | `\` |

Cost: 8 glyphs × 8 B + 16 B of glyph table + in-place key-table entries ≈ 80 B HOME (estimate).

**As built (v0.7, Phase 5; owner confirmation of the baseline mapping, 2026-10-20).** The mapping above, in the platform's symbol-shift table (delta D7); SYMBOL SHIFT + A and S no longer give V2's error-navigation codes, which nothing in Leap-C handled. Every character of C's basic source character set is typed through the keyboard matrix and read back from the screen in the tests. The glyphs (delta D8) are drawn in the columns of the letters, like the rest of the font; `\` is the mirror of `/`, `|` a solid bar (the gap of `!` tells them apart), `{` and `}` braces with a centre point. Measured cost: +61 B HOME (the 8 glyphs 64 B and their table entries 16 B, less 19 B of V2's error-navigation decoding), inside the platform's budget.

### 6.3 Compile and run behaviour

**Compile errors:**

- Compilation stops at the first error.
- The shell shows `ERROR n: message` and the line number, and positions the editor at that line.
- Error numbers and texts are listed in the manual. Groups: lexical, declaration, type, expression, statement, limit, memory.

**Compile speed target:** ≤ 25 ms per source line on average over the qualification corpus. V2's compiler measures about 18 ms per line.

**Memory report:** after a successful compile the shell reports image size and free heap. `FREE` reports the same.

**As built (v0.7, Phase 5).** `RUN` compiles (`CC_PROGRAM` through the HOME trampoline `SH_COMPILE`, chunk 6 paged out) and runs the program (`RT_RUN`) on a cleared screen. When it ends its screen stays until a key. A compile error shows `ERROR n LINE m` on the status row and puts the cursor on the line, with its text in the edit buffer. A runtime error shows `RUNTIME ERROR n LINE m` over the program's screen and BREAK `BREAK LINE m`, with the cursor on the line where the definition of the function that failed starts (§5.9; without `LINE` when unknown). A key then returns to the editor with the source intact, the paging, the stack and the AY as before the run, the border white and the screen redrawn. Phase 6 replaced these reports (v0.8, below).

**As built (v0.8, Phase 6).** `RUN` shows `COMPILING` on the status row while it compiles. Every outcome ends with a report on rows 22 and 23 in the status bar's colours (white on black, row 23 with its swatch), drawn over whatever is on the screen (the editor after a compile error, the program's screen otherwise: its rows 0-21 stay), until a key; the key is not typed, and a key pressed before the report (during the compile, or BREAK) does not end it. Then the editor is redrawn with the source intact.

| Outcome          | Row 22                                                             | Row 23                                                                                            | Cursor                                                                                |
| ---------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| compile error    | `ERROR n: MESSAGE`                                                 | `LINE m`; (v0.11) for error 23, `LINE m  'name'`: the undeclared identifier's first 15 characters; (v0.12) the same for errors 21, 22, 52, 70 and 76 | on line m, its text in the edit buffer (the append line when m is past the last line); (v0.12) at the error's column |
| runtime error    | `RUNTIME ERROR n: MESSAGE`                                         | `LINE m`, or nothing when unknown (§5.9)                                                          | on line m, where the definition of the function that failed starts                    |
| BREAK            | `BREAK`                                                            | `LINE m`                                                                                          | as for a runtime error                                                                |
| the program ends | `EXIT n` (main's value or `exit()`'s, signed; 0 for a void `main`) | `IMAGE i B  HEAP h B`                                                                             | as before `RUN`                                                                       |

- **The image's size** is its code and static data in the four image regions (§3.2): from the compiler's limits after the compile, each region's bytes less the free bytes between its code and its data; region 4 reserved by `#pragma hires` counts only the data placed there before the pragma.
- **The free heap** is the largest block `malloc()` can return in that run: from the end of the source, made even, to `LIB_HEAP_END`, less the block's 2-byte header (`malloc(h)` succeeds and `malloc(h + 1)` returns NULL; tested).
- **The messages** come from a word-compressed table in the EXROM (the diagnostics, 640 B: `src/shell/diag.asm`), built from `include/leapc_errors.inc` by `tools/gen_diag.py`. They run after the compile's trampoline (`SH_COMPILE`) has paged the EXROM back in, read only the compiler's error cells, and never touch chunk 6. Every message fits the report row with its number.

| Group         | Number: message                                                                                                                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| not supported | `1: NOT SUPPORTED`                                                                                                                                                                                                                   |
| lexical       | `10: BAD CHARACTER`; `11: UNTERMINATED COMMENT`; `12: UNTERMINATED STRING`; `13: BAD CHARACTER CONSTANT`; `14: BAD ESCAPE`; `15: BAD NUMBER`; `16: NUMBER TOO LARGE`; `17: STRING TOO LONG`                                          |
| declaration   | `20: SYNTAX ERROR`; `21: REDECLARED`; `22: ALREADY DEFINED`; `23: UNDECLARED IDENTIFIER`; `24: BAD TYPE SPECIFIERS`; `25: BAD DECLARATOR`; `26: BAD STORAGE CLASS`; `27: BAD PARAMETER`; `28: BAD INITIALISER`; `29: BAD ARRAY SIZE` |
| type          | `40: TYPE MISMATCH`; `41: INCOMPLETE TYPE`; `42: TYPE TOO LARGE`                                                                                                                                                                     |
| expression    | `50: CONSTANT REQUIRED`; `51: BAD OPERAND TYPE`; `52: NO SUCH MEMBER`; `53: NOT AN LVALUE`; `54: ASSIGNMENT TO CONST`; `55: WRONG ARGUMENT COUNT`                                                                                    |
| statement     | `70: UNDEFINED FUNCTION`; `71: NO MAIN FUNCTION`; `72: MISPLACED BREAK`; `73: MISPLACED CONTINUE`; `74: MISPLACED CASE`; `75: DUPLICATE CASE`; `76: UNDEFINED LABEL`                                                                 |
| limit         | `90: NESTING TOO DEEP`; `91: FRAME TOO LARGE`; `92: TOO MANY PARAMETERS`                                                                                                                                                             |
| memory        | `100: OUT OF MEMORY`; `101: PROGRAM TOO BIG`                                                                                                                                                                                         |

**As built (v0.12): the name and the column.**

- **The name** (Fix 2). Errors 21 `REDECLARED`, 22 `ALREADY DEFINED`, 23 `UNDECLARED IDENTIFIER`, 52 `NO SUCH MEMBER`, 70 `UNDEFINED FUNCTION` and 76 `UNDEFINED LABEL` show the identifier on row 23: `LINE 5  'prnt'`, at most 15 characters, from the compiler's `NM`. For 70 and 76, which are found at the end of the compile, the compiler points `NM` at the undefined symbol's own stored name (until v0.11 `NM` held whatever name came last). An empty name shows no name: a `#define`'s `ALREADY DEFINED` (`LINE 2`).
- **The column** (Fix 5). After a compile error the cursor lands on the column of the token where the compile stopped (`TOK_PTR` less the line's text), or at the line's end when that token is past it (a missing `;`, which belongs there) or before it (a token from a macro's body on its `#define` line). The column applies once, when the editor resumes; moving off the line and back puts the cursor at its start, as for any line. A runtime error and BREAK keep column 0. Examples: `    int x = 1` without its `;` (column 13), `    int a = 3 @ 4;` (14, the `@`), `    totl = 5;` (9, just after the name).

**As built (v0.10): the line of a missing token.** When the parser expects a token (`;`, `)`, `]`, `}`, `:`, ...) and finds another, the error's line is that of the **previous** token, after which the missing one belongs: a statement or declaration without its `;` is reported at its own line, not at the next line's first token (`tests/stmterr/missing_*.c`). A line that only continues a macro's expansion or follows a directive line may still be reported at the directive's line.

`17: STRING TOO LONG` needs a line longer than the editor makes (a guard). **Compile speed** measured through `RUN` over the corpus: **13.41 ms per line** (10,536 lines; 13.40 ms per line through the direct path), against the target of 25. (v0.10: 13.98 ms per line through `RUN` over 13,670 lines, 13.97 ms through the direct path: the floating constants and the previous token's line cost about 5%.)

---

## 7. Platform library (`leap.h`, built in)

All functions are HOME-ROM runtime routines with C prototypes known to the compiler without any header file. Release 1:

| Area               | Functions                                                                                                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Text               | `cls()`, `putchar(c)`, `puts(s)`, `print(s)` (no newline), `at(row, col)`, `tab(col)`, `ink(n)`, `paper(n)`, `border(n)`, `bright(n)`, `flash(n)`, `inverse(n)`, `over(n)`, `printf(fmt, …)` with `%d %u %x %c %s %%` and width, (v0.10) `%f` and `%.Nf`         |
| Keyboard           | `getkey()` (wait), `inkey()` (0 if none), `gets(buf, max)` (editor-style line input)                                                                                                                                                                             |
| Graphics           | `plot(x, y)`, `draw(x0, y0, x1, y1)`, `point(x, y)`, `attr(row, col)`, `mode(n)` (0 normal / 1 dual-screen hi-res; §3.2), `sprite_get(row, col, w, h, buf)`, `sprite_put(row, col, w, h, buf)`                                                                   |
| Sound              | `beep(frames, semitone)`, `sound(reg, value)`                                                                                                                                                                                                                    |
| Time and random    | `frames()`, `pause(n)`, `rand()`, `srand(n)`: `rand()` returns 0-32767 (`RAND_MAX`) from a 16-bit xorshift generator (period 65,535); `srand(n)` restarts its sequence, with seeds 0 and 1 giving the same one; every run starts with the sequence of `srand(1)` |
| Low level          | `inp(port)`, `outp(port, value)`; memory is accessed with pointers                                                                                                                                                                                               |
| Strings and memory | `strlen`, `strcpy`, `strncpy`, `strcmp`, `strcat`, `strchr`, `memcpy`, `memmove`, `memset`, `memcmp`                                                                                                                                                             |
| Conversion         | `atoi`, `itoa(n, buf, base)`, `abs`                                                                                                                                                                                                                              |
| Heap               | `malloc`, `free` (first-fit free list in the heap region)                                                                                                                                                                                                        |
| Program            | `exit(n)`                                                                                                                                                                                                                                                        |
| Tape (Phase 7)     | `tape_save(name, addr, len)`, `tape_load(name, addr, max)` (data blocks; §7.1, §8.3)                                                                                                                                                                             |

**Not built in:** circle and flood fill (V2 has them only as BASIC packages; implementable in C), ULAplus palette, printer. These are candidates for a later library-loading mechanism (§9). (v0.12) Libraries loaded from tape add functions like these (§7.2); the example library `shapes` has `circle()`, `box()` and `isqrt()`.

---

### 7.1 As built (v0.5)

**Binding.** The library's names are not declared in advance and are not reserved. An identifier that no declaration in scope names is looked up among them (`LIB_BIND`, through the EXROM's name table) and, if it is one, becomes a defined file-scope function at its ROM address with its prototype. A program's own declaration of a name comes first and hides the library function. A program's own prototype of a library function declares a new function that must then be defined (deviation: C89 7.1.7 lets a program declare library functions itself). `#include <leap.h>` is a no-op.

**Prototypes.** Pointer parameters are `void *` (any object pointer converts); integer parameters are `int`. Return types: `void`, `int`, `unsigned` (`frames`, `strlen`), `char *` (`gets`, `strcpy`, `strncpy`, `strcat`, `strchr`, `itoa`), `void *` (`malloc`, `memcpy`, `memmove`, `memset`). `printf` has no prototype: any arguments, the default promotions. Library functions have addresses (function pointers). v0.9: `void tape_save(void *name, void *addr, int len)`, `int tape_load(void *name, void *addr, int max)`; 50 names in all.

**Screen.** Text rows 0-23, columns 0-31; pixels x 0-255, y 0-191 **from the top** (the platform's convention). Text continues on the next row after column 31; below row 23 the screen scrolls up. `'\n'` moves to the next row's start. Characters without a glyph show as spaces. (v0.11) Codes 128-143 are the block graphics (bit 0 the cell's top-right quarter, bit 1 the top-left, bit 2 the bottom-right, bit 3 the bottom-left); codes 144-164 draw the user-defined graphics, eight bytes each from `UDG_TABLE` (`$F180`), which the cold start clears: they show as spaces until a program writes them.

**Time (v0.11).** A frame, the unit of `frames()`, `pause(n)` and `beep(frames, ...)`, is the display's: **1/60 s on a TS2068** (58,688 T at 3.528 MHz; Fuse emulates it). ZEsarUX 13.0 emulates the TS2068 with the 48K Spectrum's 50 Hz frame (69,888 T), so there a program sees 50 frames a second and `pause(60)` lasts 1.2 s; every T-state measurement in this specification is the same on both (`tools/timingcmp.py`). Every frame is counted, also while float code runs (delta D14; `tools/fusetest.py frames`).

| Function                                      | As built                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cls()`                                       | clears to the current colours (inverse not applied); print position (0, 0)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `putchar(c)`, `puts(s)`, `print(s)`           | `putchar` returns `c`; `puts` adds `'\n'` and returns 10                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `at(row, col)`, `tab(col)`                    | row beyond 23 → 23; column & 31                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ink(n)`, `paper(n)`, `bright(n)`, `flash(n)` | n & 7, n & 7, n & 1, n & 1; used by printing, `plot`, `draw` and `cls`                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `inverse(n)`, `over(n)`                       | n & 1. Inverse swaps ink and paper in the attribute printing and plotting give a cell (a plotted pixel is still set: Sinclair BASIC's `INVERSE 1 PLOT` clears it instead); over XORs characters and pixels                                                                                                                                                                                                                                                                                                       |
| `border(n)`                                   | n & 7                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `printf(fmt, …)`                              | `%d %u %x %c %s %%`, a decimal width (right-aligned with spaces). (v0.10) `%f`: a float with 6 decimals, `%.Nf` with N (0-9; more counts as 9), rounded half up, every integer digit printed (up to 39), a width right-aligns. **Deviations:** no flags (`- 0 + #` space); another conversion character prints the next argument as a character; the return value is undefined                                                                                                                                   |
| `getkey()`                                    | waits; ASCII or the editor's control codes (1-4 cursor, 8 DELETE, 13 ENTER)                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `inkey()`                                     | the key pressed since the last read (the ISR's latch), else 0                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `gets(buf, max)`                              | at most `max - 1` printable characters, echoed; DELETE edits; ENTER ends with a new line; returns `buf`; `max` < 1 counts as 1                                                                                                                                                                                                                                                                                                                                                                                   |
| `plot(x, y)`, `point(x, y)`                   | off the screen: nothing / 0. `plot` gives the cell the print attribute                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `draw(x0, y0, x1, y1)`                        | both ends included; off-screen coordinates move to the screen's edge                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `attr(row, col)`                              | the cell's attribute; 0 outside                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `mode(n)`                                     | 0 normal, 1 hi-res colour; error 3 if the image uses `$6000-$77FF`; other n: error 4. The end of the program restores mode 0                                                                                                                                                                                                                                                                                                                                                                                     |
| `sprite_get/put(row, col, w, h, buf)`         | 9 B per cell (8 pixel rows, the attribute), row by row; a rectangle not wholly on the screen, or empty: error 4                                                                                                                                                                                                                                                                                                                                                                                                  |
| `beep(frames, semitone)`                      | frames unsigned (0: nothing); semitone -60..69 above middle C (below -39: A0), else error 4; AY channel A, through the EXROM trampoline (§5.8)                                                                                                                                                                                                                                                                                                                                                                   |
| `sound(reg, value)`                           | register 0-15 (else error 4), value & 255                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `frames()`, `pause(n)`                        | `unsigned`; `pause(0)` returns at once                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `inp(port)`, `outp(port, value)`              | 16-bit port addresses                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `str*`, `mem*`                                | C89 semantics; characters compared unsigned; `memcpy` is `memmove` (overlap safe)                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `atoi(s)`                                     | skips spaces and control characters (1-32), optional sign, decimal digits; wraps beyond 16 bits                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `itoa(n, buf, base)`                          | bases 2-36 (lowercase), negative only in base 10; returns `buf`; another base: error 4                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `abs(n)`                                      | `abs(-32768)` = -32768                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `malloc(n)`, `free(p)`                        | §3.2; NULL when nothing fits and for n ≥ 32 KB; `free(NULL)` does nothing                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `exit(n)`                                     | ends the program with status n, from any depth                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `tape_save(name, addr, len)` (v0.9)           | `len` bytes from `addr` to tape as a data tape (§8.3) named `name` (a C string of 1-10 characters); returns when both blocks are sent (about 7 s, plus 5-7 ms a byte). A longer or empty name, or `len` 0: error 4. Any address, chunk 6 included                                                                                                                                                                                                                                                                |
| `tape_load(name, addr, max)` (v0.9)           | the next data tape named `name` (`""`: any) into `addr`, at most `max` bytes. Returns its length; -1 when nothing was loaded (no such tape before the search gives up, about 2 minutes of silence; a tape longer than `max`; a bad block before the data), `addr` untouched; -2 when the data block failed after part of it was written; -3 for a tape whose version word is not Leap-C's (nothing written). Program tapes are skipped. A name longer than 10 characters: error 4. Any address, chunk 6 included |
| `tape_save`, `tape_load`: BREAK               | BREAK (or SPACE) during the transfer stops it and ends the program with runtime error 5 (§5.8). While a block moves, interrupts are off: `frames()` does not count                                                                                                                                                                                                                                                                                                                                               |

### 7.2 Loaded libraries (v0.12, Phase 10)

**C extends through functions, so a library needs no new syntax:** a library is a table of functions the compiler finds by the same binding as the built-in library's (§7.1), and a call of one is a `call` to a fixed address with the C calling convention (§5.2), exactly as for `printf`. This is Stage 1 of the improvements report's plan: libraries written in assembly and built on a host. (Stage 2, libraries written in C on the machine: `#pragma library`, `SAVE "name" LIB`, is not built.)

**The image.** A library is an image for image region 3 (`$F400-$F7FF`, at most 1,024 B), built by `tools/lib2tape.py` from an sjasmplus source that includes `include/leapc_lib.inc`:

| Offset | Bytes | Contents |
| -----: | ----: | -------- |
| 0 | 1 | the magic `$8D` (`LX_MAGIC`: bit 7 Leap-tagged, `$0D` a Leap-C library; program and data tapes are `$8C`) |
| 1 | 1 | the ABI version it needs (`LX_ABI`, 1 in this ROM) |
| 2 | 1 | the export count, 1-99 |
| 3 | | the export table: per function its name (1-31 characters of a C identifier, the last with bit 7 set), its address (2 B, in the image) and its signature byte; then a 0 (`LIB_NAMES`'s records, §7.1) |
| | | the code and data |

**The signature byte** is `[return type:4][parameter list:4]`. The return type is `[pointer:1][base:3]` with the bases of `include/leapc_decl.inc`: `void` 0, `char` 1, `int` 3, `unsigned` 4, `float` 5 (the result in `F_ACC`), and `void *` 8, `char *` 9. The parameter list is an index into the ROM's 16 lists (`LIB_PARAMS`, never reordered: `include/leapc_lib.inc` `LXP_*`): 0 no prototype (any arguments, the default promotions; a float is a 3-word slot), 1 `()`, 2 `(int)`, 3 `(void *)`, 4 `(int, int)`, 5 `(void *, int)`, 6 `(void *, void *)`, 7 `(void *, void *, int)`, 8 `(void *, int, int)`, 9 `(int, void *, int)`, 10 four ints, 11 `(int, int, int, int, void *)`, and (v0.12, for libraries) 12 `(int, int, int)`, 13 `(int, void *)`, 14 `(int, int, void *)`, 15 five ints. Integer parameters are `int`; pointer parameters `void *`, to which any object pointer converts. A call is type-checked against this prototype: the argument count (`WRONG ARGUMENT COUNT`), the conversions (`TYPE MISMATCH` for a pointer to an `int`).

**Loading.** `LIB "name"` (§6.1) reads a library tape (§8.4) through the existing tape path into the region and sets `LIB_LOADED` (`$F4`). The magic and the ABI are the tape header's version word, so a wrong magic or a later ABI is refused before a byte is stored. While a library is loaded the compiler closes region 3 to the program (§3.2).

**Binding.** An identifier that no declaration in scope names is looked up in the ROM's library table, then in the loaded library's export table, with the same search and the same binding (`LIB_FIND`, `XL_BIND`): it becomes a defined file-scope function at the library's address, with the signature's prototype. **A name both have binds the ROM's function**: the library's export of it is never bound (`tools/lib2tape.py` reports such a name; the test library exports `abs`, and `abs()` is the ROM's). A program's own declaration hides either, as before. Without the library, a call of one of its functions is C89's implicit declaration of an undefined function: `UNDEFINED FUNCTION` with its name.

**Writing a library function** (the ABI's rules, `include/leapc_lib.inc`):

- it is called with the C calling convention: the arguments on the stack, the first lowest, removed by the caller; the result in HL (`F_ACC` for a float); it keeps IX and IY; it may destroy AF, BC, DE, HL;
- it calls `LX_ARGS` first (HL, DE, BC = the first three arguments; a fourth and later ones are at SP+8, +10, ...), so that a runtime error or BREAK in it, or in a service it calls, is reported at the program's call (§5.8, §5.9);
- it reaches the ROM only through the slots (§2.4) and the pinned names; its own cells are in its image, and keep their values between calls and between runs (the region is not reset);
- it uses no more stack below its arguments, the services it calls included, than the ROM's library does (`include/leapc_layout.inc`: ENTER's margin allows 40 B). Measured below the call's first argument, an interrupt included: the test library's print with a scroll (`LX_PUTS`) 40 B, its float division (`LX_FOP`) 30 B, `shapes`' `circle()` and `box()` 30 B; the ROM's own `puts()` with a scroll 42 B.

**The example library** `libs/shapes.asm` (`make libs`: `build/libs/shapes.tap`, `.tzx`, `.wav`; 438 B):

| Function | As built |
| -------- | -------- |
| `void circle(int x, int y, int r)` | the circle of radius r about (x, y), the midpoint algorithm, in the print attribute and over mode; each point once, so `over(1)` draws it and draws it again to nothing; points off the screen left out; r < 0: runtime error 4 |
| `void box(int x0, int y0, int x1, int y1)` | the rectangle's four edges, each point once; coordinates off the screen move to its edge, as `draw()`'s do |
| `unsigned isqrt(unsigned n)` | the largest r with r × r ≤ n (0-255) |

The test libraries `tests/libs/testlib.asm` (one function per slot, the four new parameter lists, `abs`, a loop for BREAK, its own data) and `tests/libs/tiny.asm` (a second library) are built with it.

## 8. Storage

### 8.1 Program tapes

- **Format:** header type 0 with the V2 line store verbatim.
- **Version word** (autostart field): `$8C00` (bit 15 = Leap-tagged, major `$0C` = Leap-C source, minor 0).
- V2 ROMs refuse Leap-C tapes and Leap-C refuses V2 BASIC tapes with `BAD TAPE VERSION` (V2's acceptance rule).
- `LOAD` writes into the source region only, never chunk 6.

**As built (v0.9, Phase 7).** The platform's tape code (V2's port of the stock ROM's SA-BYTES / LD-BYTES: the stock timing, measured on Leap-C's own SAVE: pilot 2,168 T, sync 667 / 735 T, bits 855 / 1,710 T, 8,063 header and 3,223 data pilot pulses) in the stock two-block format:

| Block  | Contents                                                                                                                                                   |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| header | flag `$00`; type 0; the name, 10 characters padded with spaces; the length; `$8C00` (the autostart field); the program length (= the length); XOR checksum |
| data   | flag `$FF`; the line store, `[length:2][text][CR]` per line, exactly as the editor keeps it; XOR checksum                                                  |

- **Acceptance** (V2's rule, `STORAGE_LOAD`): the bit 15 tag and the major must be Leap-C's and the tape's minor at most Leap-C's; anything else (V2's `$8101`, a stock tape's `$8000` or autostart line, a later Leap-C minor) is `BAD TAPE VERSION` before any byte is received. Headers of another type or another name are skipped; the search gives up after 15 headers or blocks, or about 2 minutes of silence.
- **LOAD is staged.** A program that fits in the line store's room above the current source (below `VARS_START`) is received there, then checked and moved down onto the source; otherwise it is received in place. It must be whole (both checksums) and sound: records of 1-128 bytes, each ending in CR, ending exactly at its length, at least one. A tape longer than the line store's room is refused at its header.
- **VERIFY** compares the tape's data with the source byte for byte and requires the tape to end where the source does. It never writes.
- V2 refuses Leap-C's tapes with its own `BAD TAPE VERSION` and leaves its program alone (tested on the V2 reference ROM with a tape made by Leap-C's SAVE, and the reverse).

### 8.2 Compiled images

Not saved in Release 1; source is the program.

### 8.3 Data blocks and loading into chunk 6 (resolution of the known problem)

**The problem.** V2's tape block routines are EXROM-resident. While they run, chunk 6 is EXROM, so they cannot write into chunk-6 RAM.

**Resolution, Phase 7:**

- `STORAGE_SEND_BLOCK` (127 B) and `STORAGE_RECEIVE_BLOCK` (204 B) move to **HOME**: net 0 ROM, budgeted.
- Header building and parsing stay in EXROM and use a header buffer outside chunk 6.
- Data blocks are then sent and received with chunk 6 in the state the caller needs. `tape_load`/`tape_save` from a running program work for any address, chunk 6 included.

**Fallback,** if HOME cannot absorb 331 B: staged loading through a bounce buffer in always-visible RAM, then a copy into chunk 6 with EXROM out. This is slower and bounded by the free buffer size.

The data tape type uses header type 3 with version word `$8C00`.

**As built (v0.9, Phase 7): the resolution, not the fallback.** HOME absorbed the block I/O: 331 B, the vendored routines byte for byte (platform delta D9), within the 340 B budget; the EXROM lost exactly those 331 B. The header logic stays in the EXROM and reaches the blocks through `TAPE_BLOCK` (§2.2), so `tape_save` and `tape_load` move data from and to any address, chunk 6 included (tested: image region 1, `$E000`, the heap, the screen). The library's HOME part copies the name's first 11 bytes out of the program's memory with chunk 6 = RAM before the EXROM is paged in. The data tape is the program tape's format with type 3 and the bytes given; `tape_load` takes the first data tape of that name (any, for `""`), skipping program tapes.

### 8.4 Library tapes (v0.12, Phase 10)

A library tape (`tools/lib2tape.py`; `LIB "name"` reads it, §6.1, §7.2) is a program tape's two blocks with:

| Field | Value |
| ----- | ----- |
| header type | 4 (`LX_TYPE`: V2's package tapes) |
| name | 1-10 characters, padded with spaces |
| length | the image's, 1,024 B at most |
| version word (autostart field) | the image's magic and ABI: `$8D01` (`LX_WORD`) |
| second parameter | the length |
| data block | the image, verbatim |

**Acceptance** is the platform's version rule (`STORAGE_LOAD` with `STORAGE_VERSION_WORD`'s package branch, which gives the library word for type 4): the magic (the tag bit and the major) must be Leap-C's library magic and the tape's ABI at most the ROM's; anything else is `BAD TAPE VERSION` at the header, before a byte is written. A length above 1,024 B is refused at the header too (`LOAD FAILED`). Other header types are skipped, so `LOAD`, `VERIFY` and `tape_load()` skip library tapes and `LIB` skips program and data tapes. V2's package tapes (type 4, `$8200`) and Leap-C's library tapes refuse each other (tested with V2's own `SHAPES` package, built from its tag, and V2's `LOAD "name" EXT`).

---

## 9. Extensibility (later)

- V2 packages are not supported.
- A C-oriented library-loading mechanism (precompiled C or assembly libraries in RAM, registered with the compiler's symbol table) is a candidate for a later release.
- Image region 3 (`$F400-$F7FF`) keeps that option open.
- **(v0.12) Stage 1 is built** (§2.4, §7.2, §8.4): assembly libraries built on a host and loaded by `LIB`. V2's packages and Leap-C's libraries share the tape header type and refuse each other by the version word. **Stage 2** (libraries written in C on the machine: `#pragma library` would compile a source into region 3 only and export its non-`static` functions; `SAVE "name" LIB` would write region 3 and the table) is not built.

---

## 10. Toolchain and repository

- **Assembler:** sjasmplus (as V2), with strict warnings. The ROM images are built by `make`.
- **Emulator:** ZEsarUX 13.0 is the qualification emulator (as V2). Fuse and EightyOne are courtesy only. (v0.11) Fuse 1.9.1 runs a qualification suite of its own (`make fuse`); EightyOne is not used (owner instruction, Phase 9).
- **Test harness:** Python over ZEsarUX ZRCP, derived from V2's `qharness` (vendored with attribution). Test cases are C sources with expectations in header comments (exit value, screen text, memory, compile error and line, runtime error).
- **Budget tooling:** per-component sizes from the listings; `budget.toml` limits; ROM map report.
- **Platform vendoring:** `platform/` pinned to the V2 reference with a delta list. V2 itself is never modified.
- **Cross tools (development only):**
  - a host tool to turn `.c` files into Leap-C program tapes (v0.9: `tools/c2tape.py FILE.c OUT.tap|OUT.tzx [--name NAME]`: the blocks the ROM's own `SAVE` sends for that source, byte for byte; `.tzx` as standard speed blocks);
  - optionally SDCC as a test oracle (installing it needs owner approval).
- **Floating point (v0.10):** `tools/fpmodel.py`, a bit-exact Python model of every float-core operation (the host lexer's floating constants and the float tests' expectations); `tools/floattest.py` (the core against the model on the production ROM), `tools/gen_floattests.py` (generated corpus cases).
- **Phase 9 (v0.11):**
  - `tools/poweron.py`: the boot from power-on RAM patterns (random from a seed, `$00`, `$FF`, `$55AA`, the address's low byte, the reset button after a session) against the boot from zeroed RAM, and a slice of the corpus from each; `run_tests.py --ram PATTERN` runs any suite from one;
  - **Fuse 1.9.1** as a second, independent emulator, headless: `tools/fuse/fuseshim.c` (an `LD_PRELOAD` library answering a Unix socket once a frame: Fuse's keyboard matrix, its debugger, its tape deck, its memory), `tools/fusedrive.py` (the driver), `tools/fusetest.py` (`make fuse`); Fuse emulates the TS2068's 60 Hz frame;
  - `tools/timingcmp.py` (`make timing`): the same programs timed on both emulators (compile and run, in T-states and frames);
  - ROM coverage: `run_tests.py --coverage` collects ZEsarUX's code coverage over every suite and `tools/romcov.py` reports it per routine (`make test` does both);
  - the hardware kit: `tools/hwkit.py` (`make kit`): the EPROM images with checksums, the check programs (`docs/hardware/`) and the examples as `.tap`, `.tzx` and `.wav`, verified on both emulators; `tools/tapes.py` writes and reads WAV;
- **Phase 10 (v0.12):**
  - `include/leapc_lib.inc`: the library ABI (the header, the slots, the pins, the parameter lists), the single source of truth for HOME and for libraries (§2.4, §7.2);
  - `tools/lib2tape.py SRC.asm OUT...`: a library's image (`.bin`, its labels `.sym`) and tapes (`.tap`, `.tzx`, `.wav`) from its sjasmplus source, the image checked (the header, the export table, the sizes); `make libs` builds `libs/shapes.asm` and the test libraries into `build/libs/`;
  - the harness loads a library for a corpus case (`// library: NAME`: `Machine.lib_load`); the cassette suite and Fuse load them from tape (`LIB`); `tools/v2ref.sh` also builds V2's package tapes.
- **Documentation examples (v0.10):** `tools/docexamples.py` copies every example with expectations from `README.md`, `spec.md` and `docs/EXAMPLES.md` into `tests/doc/`; `make check` fails when they differ.

---

## 11. Validation (summary; detail in `project_plan.md`)

Every milestone delivers both:

- **assembled size measurements** checked against `budget.toml`;
- **executable tests** in ZEsarUX.

As built (v0.10): `make test` is the acceptance gate (every suite, the cassette and the canary); `make test-fast` is the development subset (no cassette; the corpus through the shell's `RUN` and the typing-cost measurements left out; the canary over every other program). The documentation's examples (`docs/EXAMPLES.md`) run in the corpus.

Release qualification covers:

- the corpus;
- the emulator qualification on ZEsarUX;
- the physical TS2068 hardware checklist: EPROM HOME + EXROM, keyboard, tape, timing at 60 Hz, display contention.

**As built (v0.11, Phase 9; `docs/milestones/M9.md`):**

- `make test` also boots from eight power-on RAM patterns and runs the corpus from them, and reports the ROM's coverage (`build/romcov.md`).
- The emulator qualification adds Fuse (`make fuse`: the typed programs, BREAK, SAVE and a WAV on Fuse's tape deck, and the corpus LOADed from tape by the ROM's own loader and RUN), the timing comparison (`make timing`) and the hardware kit's verification (`tools/hwkit.py --verify`).
- **The physical hardware checklist** (`docs/HARDWARE_CHECKLIST.md`) is **not run: an owner-accepted qualification deviation** (2026-10-21; no TS2068 was available). Its items are recorded as not tested, with what both emulators show.

**As built (v0.12, Phase 10; `docs/milestones/M10.md`):** every fix and feature has tests that fail without it. Libraries are tested at every level: the corpus's `tests/lib/loaded/` (a case names its library, which the harness puts in the region as `LIB` leaves it; run directly, through `RUN`, under the canary and from the power-on patterns), `LIB` on real tape signals in ZEsarUX's cassette suite (V2's own package tape among them), on Fuse's tape deck (the case `lib`, and every library case of the corpus loaded by `LIB`), and the kit's library tape with check program H11 from their WAVs on both. The final images pass the whole Phase 9 qualification (`make qualify`, then `make repro`).
