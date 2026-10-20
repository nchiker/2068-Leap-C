# 2068-Leap-C — Specification

**Version 0.6, 2026-10-20** (v0.1, 2026-10-12: initial; v0.2-v0.5, 2026-10-13). This specification is derived from `docs/C_FEASIBILITY_STUDY.md` (revision 3), whose architecture decisions are approved.

**Changes in v0.2:** the frame's reference point (§5.2) and the `ENTER`/`LEAVE` contracts (§2.3, §5.3), by owner decision during M1.3 (`docs/milestones/M1.3.md`).

**Changes in v0.3 (Phase 2, owner decisions O1/O2 of 2026-10-13):** the retained 16-bit math is cut to what C uses (§2.1, platform delta D3). Multiply and divide are the helper core's own routines (§5.3). `rand()`/`srand()` are a C generator (§7).

**Changes in v0.4 (Phase 2, as built):** the preprocessor's rules and limits (§4.8, §4.10), the `SWITCH` tables (§5.3), and the function → line table's format (§5.9).

**Changes in v0.5 (Phase 3, as built; `docs/milestones/M3.md`):** program start and exit (§5.7), BREAK (§5.8) and runtime errors (§5.9) as built; the heap (§3.2); the library's semantics, its binding to the compiler and its deviations (§7); the library's use of `AF'` (§5.1).

**Changes in v0.6 (Phase 4, as built; `docs/milestones/M4.md`):** the memory map is final (§3.1: baseline layout A, the RAM each region holds, the layout guard); the region rules as built (§3.2: code and data in the image regions, `#pragma hires`, the stack's floor, the heap's bounds); `#pragma hires` (§4.8); the limits measured (§4.10, with the capacity table); `ENTER`'s stack check (§5.3); the platform deltas D5 and D6 (§2.1); runtime-error lines in code continued from image region 3 into region 4 (§5.9).

**What is fixed and what is tuned:**

- Values marked **baseline** are the starting design. They are tuned *with measurements* during implementation; see `project_plan.md`.
- Tuning does not reopen the architecture.
- A change to anything marked **fixed** needs a concrete blocker found in implementation.

**Terms:**

| Term | Meaning |
|---|---|
| **HOME** | the 16 KB replacement HOME ROM, always mapped at `$0000-$3FFF` |
| **EXROM** | the 8 KB replacement extension ROM, mapped into chunk 6 (`$C000-$DFFF`) only while paged in |
| **Chunk 6** | the address range `$C000-$DFFF`: EXROM when paged in, RAM when paged out |
| **Platform** | the reusable services taken from frozen Leap V2 |
| **V2 reference** | Leap V2 release `v2.0.1-emu.1` (`d19b9ea`, HOME `3f13ec2c…`, EXROM `24b1ebb0…`) |

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

| Module | V2 size | Bank | Leap-C status |
|---|---:|---|---|
| Graphics: text, attributes, scrolling, pixels, line, sprite capture/draw, font | 2,071 | HOME | kept. **Delta:** 8 glyphs `[ ] { } \| ~ ^ \` (§6.2). **Delta D6 (v0.6):** V2's sprite-slot invalidation removed (no sprite slots in Leap-C; 25 B) |
| Memory: line store, fill, shift, cold init | 485 | HOME | kept. **Delta:** re-pointed to the Leap-C memory map (§3); **D5 (v0.6):** `MEM_INIT` no longer clears V2's string-pool, package and sprite-slot cells (25 B) |
| Keyboard I/O | 434 | HOME | kept. **Delta:** symbol-shift map for the 8 C characters (§6.2) |
| 16-bit math (`MATH_NEGATE16`, `ABS16`, `COMPARE16`) | 390 → 39 | HOME | **Delta D3 (v0.3):** multiply and divide moved to the helper core's register-only routines (§5.3); `SQRT16`, `SGN16`, `MULTIPLY16` removed (no Release 1 caller); `RND16` replaced by the library's `rand()` (§7) |
| Interrupt (IM 1, `FRAMES`, keyboard scan) | 154 | HOME | kept. **Delta D4 (v0.5):** BREAK request for native programs (§5.8): V2's BREAK latch (14 B) replaced by a call to the runtime (8 B) |
| Bank switching (`BANK_PAGE_EXROM_IN/OUT`, depth-counted) | 46 | HOME | kept unchanged |
| AY beep (HOME part) | 58 | HOME | kept |
| `FOLD_UPPER` (was in the BASIC compiler) | 9 → 0 | HOME | not built: C is case-sensitive and nothing calls it |
| Editor engine | 737 | EXROM | kept unchanged |
| Tape: `STORAGE_*` | 793 | EXROM | kept. **Phase 7:** block send/receive (331 B) move to HOME (§8.3) |
| Shell: editor/screen glue, command loop, tape commands, messages, chime, entry slots | 2,754 | EXROM | adapted into the Leap-C shell; BASIC-only parts removed |
| Integer formatting | 79 | EXROM | kept |
| Sound, AY beep (EXROM part) | 59 | EXROM | kept |
| FP calculator + float formatting | 2,165 | EXROM | **retained as an optional component** (§4.9). Not used by Release 1 code generation |

**Removed:**

- V2 VM core (6,033), BASIC compiler (5,139), BASIC symbol table (576);
- SAVE ALL / identity CRC / session undo (591);
- Array Store (701), BASIC-only shell parts (878);
- package registry (263; V2 packages are BASIC-statement extensions).

### 2.2 ROM budget (baseline; enforced by the build)

**Per-component budgets.** Every component has a budget, recorded in `budget.toml`.

- `make budget` reports the assembled size of each component from the listings.
- `make check` fails when a component exceeds its budget, unless the budget ledger records a reallocation with its justification.
- The **reserve floor** (HOME 512 B, EXROM 256 B at release) can be drawn below only with owner approval.

**HOME (16,384 B):**

| Component | Budget |
|---|---:|
| Page zero (reset, RST vectors and helper bodies that fit, IM 1, NMI), cold start, trampolines | 160 |
| Retained platform (graphics, memory, keyboard, math, interrupt, bank, AY) incl. deltas | 3,800 |
| Tape block send/receive (moved from EXROM in Phase 7) | 340 |
| **Compiler:** lexer + source streaming + keyword table | 1,100 |
| **Compiler:** declarations and type system | 2,000 |
| **Compiler:** scoped symbol table | 800 |
| **Compiler:** typed expressions | 1,800 |
| **Compiler:** code generator (templates, fixups, constant folding) | 1,200 |
| **Compiler:** statements and functions | 1,400 |
| **Compiler:** preprocessor (object-like `#define`) | 300 |
| **Runtime:** helper core (§5.3) | 500 |
| **Runtime:** library (§7) | 1,300 |
| **Runtime:** start, exit, BREAK, runtime errors | 200 |
| **Allocated** | **14,900** |
| **Reserve** | **1,484** |

**EXROM (8,192 B):**

| Component | Budget |
|---|---:|
| Retained platform (editor engine, tape headers, integer formatting, sound) | 1,340 |
| Leap-C shell (adapted editor glue, command loop, tape commands, messages, chime, entry slots) | 2,900 |
| C keyword highlighting table | 250 |
| Compiler diagnostics (message texts, error reporting) | 650 |
| FP calculator + float formatting (optional component; §4.9) | 2,165 |
| **Allocated** | **7,305** |
| **Reserve** | **887** |

**Bank rules (fixed):**

1. Anything that compiled programs call (runtime helpers, library, trampolines) is in **HOME**.
2. **EXROM services are reached only through HOME trampolines** that page EXROM in, call, and page it out again. Neither the trampoline nor the stack may be in chunk 6.
3. The compiler core runs in **HOME with chunk 6 paged out**, because it writes the program image there. EXROM-resident compiler parts (diagnostics) run only through a trampoline and never touch chunk 6.
4. The editor and shell run in **EXROM**. While they run, chunk 6 RAM is invisible.

### 2.3 Page zero and RST assignment (baseline)

| Vector | Use | Body placement |
|---|---|---|
| `$00` | reset → cold start | fixed |
| `$08` | `LDI` (HL = word at HL) | body in the slot (5 B) |
| `$10` | `STI` (word at DE = HL; HL kept) | body in the slot (6 B) |
| `$18` | `ENTER n` (frame setup, stack check) | starts in the slot, `jp` to the rest |
| `$20` | `LEAVE` (frame teardown, return) | body in the slot (5 B) |
| `$28` | `CMPLT` (signed DE < HL → carry) | `jp` to the body |
| `$30` | reserved: `LDL`/`STL` for the optional size template set (§5.6) | `jp` to the body |
| `$38` | IM 1 interrupt (`call KBD_ISR_TICK; ei; reti`) | fixed |
| `$66` | NMI | fixed |

Measured costs:

- CALL+RET 27 T; RST through a `jp` vector + RET 31 T.
- A body at the vector saves the `jp` (derived 21 T + body).
- The RST map is confirmed against operation frequencies measured on the Phase 2 test corpus.

---

## 3. Memory map (final, Phase 4)

### 3.1 Layout

Two principles:

1. **Source is resident and must be visible to the EXROM editor.**
2. **The program image** (compiled code and static data) prefers chunk 6, which is otherwise useless to a ROM language system.

The baseline moves the system variables to `$5B00` (assembly-time relocation; the kernel is symbolic apart from literals such as `MEM_COLD_INIT`'s `$8000`, which become symbols). That leaves one contiguous source region above the second display file.

| Range | Bytes | Use | Visible |
|---|---:|---|---|
| `$4000-$5AFF` | 6,912 | display file 1 + attributes | always |
| `$5B00-$5D59` | 602 | kernel system variables (V2 layout, relocated) | always |
| `$5D5A-$5FFF` | 678 | Leap-C fixed cells: shell/editor state, compiler state, 264-B source chunk window, runtime cells | always |
| `$6000-$77FF` | 6,144 | display file 2 (dual-screen/hi-res mode) **or** program-image overflow | always |
| `$7800-$BFFF` | 18,432 | **source store ↑** (line records); compile workspace ↓ (compile); heap (run) | always |
| `$C000-$DFFF` | 8,192 | **program image region 1** (chunk 6: code ↑ from `$C000`, static data ↓ from `$DFFF`) | EXROM paged out |
| `$E000-$F17F` | 4,480 | program image region 2 | always |
| `$F180-$F3FF` | 640 | UDGs, edit buffer, misc. platform cells (V2 addresses) | always |
| `$F400-$F7FF` | 1,024 | program image region 3 (no V2 packages) | always |
| `$F800-$FEFF` | 1,792 | machine stack (top `$FF00`); C locals live here | always |
| `$FF00-$FFFF` | 256 | unused by the ROM (test harness return slot) | always |

**Fallback layout B.** If the relocation meets a concrete blocker in Phase 4, the system variables stay at `$8000` and the source starts at `$825A`. The image regions are unchanged.

**All code refers to the layout only through symbols** in `include/leapc_layout.inc`, so tuning it means changing symbols, not rewriting code.

**As built (v0.6, final).** Baseline layout A is final: the relocation met no blocker (M1.1), so fallback B is not used. What each range holds:

| Range | Holds (measured, `docs/milestones/M4.md`) |
|---|---|
| `$5B00-$5D59` | the platform system variables (602 B) |
| `$5D5A-$5FFF` | the Leap-C cells: 384 B used (`LEAPC_CELLS_END` `$5EDA`), 294 B free for Phase 5's shell |
| `$F180-$F3FF` | the V2 platform cells Leap-C keeps at their V2 addresses: `UDG_TABLE` (`$F180`, 168 B), `EDIT_LINE_BUF` (`$F228`, 128 B), `GFX_LINE_X0..Y1` (`$F3C4`, 4 B). The other 340 B are V2 cells nothing in Leap-C uses |
| `$F800-$FEFF` | the stack; `ENTER`'s floor `$F900` (§5.3) |

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

Leap-C Release 1 is a **documented subset of C89**, roughly Small-C 2.1 plus `unsigned`, `struct`, `enum`, `typedef`, function pointers and multi-dimensional arrays. Anything not listed is a compile error with a clear message ("not supported"), never silently miscompiled.

### 4.1 Lexical

- **Character set:** ASCII 32-126 plus CR line ends.
- **Case:** identifiers and keywords are **case-sensitive** (C semantics; unlike V2 BASIC).
- **Identifiers:** letter or `_`, then letters, digits and `_`. **31 significant characters.**
- **Keywords recognised:** the C89 set. `long`, `float`, `double`, `union`, `volatile` are reserved; `long`, `float`, `double` and `union` give "not supported".
- **Comments:** `/* … */` (may span lines) and `// …` (Leap-C extension).
- **Integer constants:**
  - decimal, `0x` hex, `0` octal, character constants;
  - value range 0-65535, typed per C89 rules for a 16-bit `int`;
  - suffixes `u`/`U` accepted; `l`/`L` gives "not supported".
- **Character and string escapes:** `\n \t \r \0 \\ \' \" \a \b \f \v`, `\xhh`, `\ooo`.
- **String literals:** adjacent literals concatenate. Stored in static data, NUL-terminated.
- **Line length:** 127 characters (editor limit).

### 4.2 Types

| Type | Size | Notes |
|---|---:|---|
| `char` | 1 | **unsigned** (Z80-cheap zero-extension). `signed char` / `unsigned char` accepted; `signed char` sign-extends on promotion |
| `int`, `short`, `signed` | 2 | two's complement, wraparound |
| `unsigned`, `unsigned int`, `unsigned short` | 2 | |
| pointers | 2 | flat 16-bit address space; no far pointers |
| `void` | — | function results, `void *` |
| arrays | n × element | any element type, including arrays (multi-dimensional) and structs |
| `struct` | sum of members | no padding (byte-aligned); members of any complete type; self-referential via pointers |
| `enum` | 2 | constants are `int` |
| function | — | definitions, prototypes, pointers to functions |
| `typedef` | — | names for any of the above |

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
- **Casts:** between integer types and between integer and pointer types.
- Assignment between incompatible pointer types needs a cast, except to and from `void *`. Violations are errors.

### 4.4 Expressions

All C89 operators except those on unsupported types:

- primary, postfix (`[] () . -> ++ --`);
- unary (`& * + - ~ ! ++ -- sizeof` and casts);
- multiplicative, additive, shifts, relational, equality, bitwise, logical (short-circuit);
- conditional `?:`, simple and compound assignment, and comma.

**Constant expressions** are evaluated at compile time where C requires them: array sizes, `case` labels, `enum` values, static initialisers, and `sizeof`. The compiler also folds constant operands of `+ - * & | ^ << >>` where the template set allows.

**Implementation-defined choices:**

| Operation | Behaviour |
|---|---|
| Signed `/` | truncates toward zero; the sign of `%` follows the dividend |
| Division by zero | quotient 0, remainder 0 (the ROM math routines); no trap |
| `>>` on a signed value | arithmetic shift |
| Signed overflow | wraps |

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
- **Parameters and return values:** scalars and pointers. Struct parameters and struct return values are "not supported" (use pointers).
- **Recursion:** supported. About 10 B of stack per level for a one-parameter function with one local (measured).
- **Function pointers:** declaration, assignment, call through the pointer, arrays of function pointers.
- **Variadic functions:** only the library's `printf` family (§7). User-defined `...` functions are "not supported".
- **`main`:** `int main(void)` or `void main(void)`. Its return value becomes the program's exit status, shown by the shell.

### 4.7 Initialisers

- Scalars; arrays (including multi-dimensional) and structs of constant expressions, with brace elision allowed.
- `char` arrays from string literals.
- Automatic (local) scalars may use any expression. Automatic arrays and structs with initialisers are "not supported" in Release 1.

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

### 4.9 Floating point (optional, later)

Floating point is **not** part of Release 1 code generation, but it is **not removed from the architecture**.

- The V2 FP calculator and float formatting (2,165 B, EXROM) stay in the ROM image as a retained component.
- A future `float` would use the calculator through HOME trampolines (measured round trip 239 T plus the calculator's own cost). That means 5-byte Sinclair-format values, documented as non-IEEE.
- The decision to implement it, and in which release, is an owner decision informed by its measured cost.
- If floating point is dropped instead, its 2,165 EXROM bytes return to the EXROM reserve.

### 4.10 Limits (baseline; all memory-bound unless stated)

| Item | Limit |
|---|---|
| Identifier significance | 31 characters |
| Line length | 127 characters |
| Nesting depth (blocks, expressions) | bounded by the compiler's stack guard; at least 32 levels guaranteed (measured, v0.6: §4.10.1) |
| Function parameters | 16 |
| Argument words pending at once (v0.6) | 32: the arguments a call pushes and those already pushed by the calls whose arguments contain it ("nesting too deep"). A single call to a function without a prototype (or `printf`) can pass 32 words. It bounds the stack between two frame checks (§3.2) |
| Local frame size | 255 bytes (8-bit frame offsets; larger locals → "frame too large"; use `static` or the heap) |
| `switch` cases | memory-bound (6 B of compile workspace per case) |
| Macro expansions nested in one another | 8 ("nesting too deep") |
| Tokens produced by one macro expansion, nested ones included | 255 ("nesting too deep") |
| String literal length | one line, 126 characters (adjacent literals concatenate) |

#### 4.10.1 Measured capacity (v0.6)

Measured on the production ROM (`tools/capacity.py`, `make capacity`; every limit is a verified pair: the largest that compiles or runs, and one more that fails with the error shown):

| Item | Measured limit | One more |
|---|---|---|
| Source, minimal program (comments and `main`) | 18,412 B of line store (`PROG_END` $BFEC); workspace 20 B | E_NOMEM |
| Source, typical program (76 modules: a global array, a function with a loop, locals, a call) | 15,087 B of line store, 851 lines (13,385 B of text); workspace 3,255 B; image 11,059 B of code, 1,678 B of data; compile 8.38 ms per line | E_NOMEM |
| Image: code (macro-expanded statements, 43 functions) | 19,411 B of code and 266 B of data of 19,840 B (region 1: 8,074 code, 116 data, 2 free; region 2: 4,419 code, 60 data, 1 free; region 3: 1,010 code, 12 data, 2 free; region 4: 5,908 code, 78 data, 158 free) | E_TOOBIG |
| Image: the largest single object | 8,192 B (region 1; an object never spans regions) | E_TOOBIG |
| Image: all static data, with a minimal program | 19,817 B | E_TOOBIG |
| Recursion: reference: 1 int parameter, 1 int local | 190 levels from `main` | stack overflow (runtime error 1) |
| Recursion: no parameter, no local | 381 levels from `main` | stack overflow (runtime error 1) |
| Recursion: 4 int parameters, 10 int locals | 47 levels from `main` | stack overflow (runtime error 1) |
| Heap: the largest block, minimal program | 18,316 B (first block's data at $7872) | NULL |
| Heap: the largest block with a large source | 234 B (18,193 B of source, 300 B below the minimal program's limit; at the limit itself 16 B) | NULL |
| Nesting: parentheses | 112 levels | E_NESTING |
| Nesting: held operands | 60 levels | E_NESTING |
| Nesting: blocks | 154 levels | E_NESTING |
| Nesting: if | 386 levels | E_NESTING |
| Nesting: while | 193 levels | E_NESTING |
| Nesting: nested calls | 60 levels | E_NESTING |
| Nesting: struct members | 274 levels | E_NOMEM |

- **The source region is the binding limit for ordinary programs.** Source and compile workspace share `$7800-$BFFF` (18,432 B); the image has its own 19,840 B. The typical program above reaches *out of memory* with 12.7 KB of image, so about 7 KB of image stays unused. (The feasibility study's 21.5 KB assumed source and code shared one pool.) Its workspace is about 43 B per module; per declaration: 13 B for a global scalar, a local or a struct member (with a 4-character name), 20 B for an array, 24 B for a two-parameter prototype.
- Locals are on the stack: frames from `main` down to `$F900` (1,522 B from the harness's call; the shell's own frames reduce it slightly).
- Every nesting limit is above the 32 levels guaranteed; *nesting too deep* is the compiler's stack guard.

---

## 5. Runtime ABI (fixed unless a measured blocker appears)

### 5.1 Registers

| Register | Role |
|---|---|
| HL | primary accumulator, return value (`char` in L with H = 0, or H = sign for `signed char`) |
| DE | secondary operand |
| BC, A, flags | scratch |
| IX | frame base |
| IY | reserved (unused by compiled code and the kernel) |
| Alternate set | unused by compiled code. Library routines may use `AF'` within a call (v0.5); nothing keeps a value there |

The V2 kernel uses no IX/IY (verified).

### 5.2 Calling convention and frame

- **Arguments** are pushed **right to left** as 16-bit words (`char` promoted). The **caller removes them** (`pop bc` per word).
- `call f`; the result is in HL.
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

| Helper | Entry | Contract |
|---|---|---|
| `LDI` | RST `$08` | HL = (HL); destroys A |
| `STI` | RST `$10` | (DE) = HL; HL kept; DE = address + 1 |
| `ENTER n` | RST `$18` + byte | push IX; IX = SP; SP -= n; **stack check** against `STACK_LIMIT` (runtime error *stack overflow*). As built (v0.6): the new SP is checked before SP moves, against the page-aligned floor `LEAPC_RT_STACK_FLOOR` = `$F900` (the margin above `$F800` covers what runs between two frame checks, §3.2) |
| `LEAVE` | RST `$20` | SP = IX; pop IX; return to the caller; HL kept |
| `CMPLT` | RST `$28` | signed compare: carry ⇔ DE < HL |
| `CMPULT` | inline | unsigned `or a; sbc hl,de` (3 B) |
| Shifts by a variable count (`SHL`, `SHR`, `SAR`) | CALL | |
| `MUL`, `DIVS`, `DIVU`, `MODS`, `MODU` | CALL | the helper core's register-only shift-and-add multiply and restoring divide (v0.3; they replace the V2 math). The compiler's constant arithmetic uses the same routines |
| `SWITCH` | CALL + inline table address | `call RT_SWITCH / dw table`. The table is static data, made after the switch's body. Sparse: `[n][default]` then `[value][address]` pairs. Dense, when smaller (highest − lowest ≤ 2n − 3): `[range \| $8000][default][lowest]` then one address per value |
| `CALLHL` | CALL | indirect function call |
| `LDL`/`STL` (size set only) | RST `$30` + byte | local word load/store, as measured in the spike |

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

All-compact templates (local access through RST `LDL`/`STL`) were measured at 49% of the inline bytes and 2.7-3.3× slower. They are reserved as an optional size mode (`#pragma size`), implemented only if Phase 8 measurements show a capacity need.

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
- `NOBRK` sections: the EXROM trampoline of `beep()` (the only EXROM service programs use in Release 1; Phase 7 adds the tape). The beep's wait ends early on `BRK_HALT`, the trampoline pages the EXROM out and silences the AY, and its end (`RT_NOBRK_END`) then stops the program. **Heap updates are not deferred** (deviation): the heap belongs to one run and is set up again at the next start, so an interrupted `malloc` leaves nothing that must be consistent. AY register writes are single `OUT` pairs that the exit's silencing re-selects.
- `pause()` and every other wait end on BREAK through the immediate unwind.
- Cost (measured): the ISR delta is 8 B (V2's BREAK latch, 14 B, removed); the runtime's request and BREAK exit 32 B, the section end 12 B. The ISR's per-frame cost is unchanged: the delta runs only on the frame that accepts a key.

### 5.9 Runtime errors

| Code | Error |
|---|---|
| 1 | stack overflow (from `ENTER`) |
| 2 | out of heap (`malloc` returns NULL; error only for library calls that cannot report NULL) |
| 3 | hi-res mode with the image in `$6000-$77FF` |
| 4 | invalid library argument (where checked) |
| 5 | BREAK |

The shell shows `RUNTIME ERROR n` with the source line of the failing function's call site where available. The line mapping comes from a function → line table the compiler emits: one record per function definition in the image's static data, `[link][address][line where the definition starts]`, newest first, from `RUN_FNLINES` (as built in Phase 2: 6 B per function).

**As built (v0.5):** every error records an address in the failing code (`RT_ERRPC`); at the end, `RT_ERRLOC` takes the newest record of the table that starts at most 8 KB before it, and `RT_ERRLINE` is the line where that function's definition starts (0 if none). The address is:

- stack overflow: the code of the function being entered;
- a library error (codes 3, 4): the program's address of the library call (`LIB_CALLER`, recorded by every library function that takes arguments, and by `getkey()`), so the line is that of the function that called the library;
- BREAK: the interrupted address if it is in the program's image; in the ROM (a library or platform routine, a helper), the last library call.

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

| Command | Action |
|---|---|
| `RUN` | compile and execute |
| `LIST` | list the source |
| `NEW` | clear the source |
| `SAVE "name"` | save the source to tape |
| `LOAD "name"` / `LOAD ""` | load source from tape |
| `VERIFY "name"` | verify a saved tape |
| `FREE` | show free source space and the last image size |

- No immediate-statement mode in Release 1 (C has no statements outside functions).

### 6.2 C punctuation (baseline mapping; physical legends need owner confirmation)

The V2 key map cannot produce the 8 characters C needs, and the font lacks their glyphs. Leap-C adds both, using symbol-shift positions that V2 leaves unmapped and that match the Spectrum-family legends where they exist:

| Key (SYMBOL SHIFT +) | Y | U | F | G | S | A | H | D |
|---|---|---|---|---|---|---|---|---|
| Character | `[` | `]` | `{` | `}` | `\|` | `~` | `^` | `\` |

Cost: 8 glyphs × 8 B + 16 B of glyph table + in-place key-table entries ≈ 80 B HOME (estimate).

### 6.3 Compile and run behaviour

**Compile errors:**

- Compilation stops at the first error.
- The shell shows `ERROR n: message` and the line number, and positions the editor at that line.
- Error numbers and texts are listed in the manual. Groups: lexical, declaration, type, expression, statement, limit, memory.

**Compile speed target:** ≤ 25 ms per source line on average over the qualification corpus. V2's compiler measures about 18 ms per line.

**Memory report:** after a successful compile the shell reports image size and free heap. `FREE` reports the same.

---

## 7. Platform library (`leap.h`, built in)

All functions are HOME-ROM runtime routines with C prototypes known to the compiler without any header file. Release 1:

| Area | Functions |
|---|---|
| Text | `cls()`, `putchar(c)`, `puts(s)`, `print(s)` (no newline), `at(row, col)`, `tab(col)`, `ink(n)`, `paper(n)`, `border(n)`, `bright(n)`, `flash(n)`, `inverse(n)`, `over(n)`, `printf(fmt, …)` with `%d %u %x %c %s %%` and width |
| Keyboard | `getkey()` (wait), `inkey()` (0 if none), `gets(buf, max)` (editor-style line input) |
| Graphics | `plot(x, y)`, `draw(x0, y0, x1, y1)`, `point(x, y)`, `attr(row, col)`, `mode(n)` (0 normal / 1 dual-screen hi-res; §3.2), `sprite_get(row, col, w, h, buf)`, `sprite_put(row, col, w, h, buf)` |
| Sound | `beep(frames, semitone)`, `sound(reg, value)` |
| Time and random | `frames()`, `pause(n)`, `rand()`, `srand(n)`: `rand()` returns 0-32767 (`RAND_MAX`) from a 16-bit xorshift generator (period 65,535); `srand(n)` restarts its sequence, with seeds 0 and 1 giving the same one; every run starts with the sequence of `srand(1)` |
| Low level | `inp(port)`, `outp(port, value)`; memory is accessed with pointers |
| Strings and memory | `strlen`, `strcpy`, `strncpy`, `strcmp`, `strcat`, `strchr`, `memcpy`, `memmove`, `memset`, `memcmp` |
| Conversion | `atoi`, `itoa(n, buf, base)`, `abs` |
| Heap | `malloc`, `free` (first-fit free list in the heap region) |
| Program | `exit(n)` |
| Tape (Phase 7) | `tape_save(name, addr, len)`, `tape_load(name, addr, max)` (data blocks; §8.3) |

**Not built in:** circle and flood fill (V2 has them only as BASIC packages; implementable in C), ULAplus palette, printer. These are candidates for a later library-loading mechanism (§9).

---


### 7.1 As built (v0.5)

**Binding.** The library's names are not declared in advance and are not reserved. An identifier that no declaration in scope names is looked up among them (`LIB_BIND`, through the EXROM's name table) and, if it is one, becomes a defined file-scope function at its ROM address with its prototype. A program's own declaration of a name comes first and hides the library function. A program's own prototype of a library function declares a new function that must then be defined (deviation: C89 7.1.7 lets a program declare library functions itself). `#include <leap.h>` is a no-op.

**Prototypes.** Pointer parameters are `void *` (any object pointer converts); integer parameters are `int`. Return types: `void`, `int`, `unsigned` (`frames`, `strlen`), `char *` (`gets`, `strcpy`, `strncpy`, `strcat`, `strchr`, `itoa`), `void *` (`malloc`, `memcpy`, `memmove`, `memset`). `printf` has no prototype: any arguments, the default promotions. Library functions have addresses (function pointers).

**Screen.** Text rows 0-23, columns 0-31; pixels x 0-255, y 0-191 **from the top** (the platform's convention). Text continues on the next row after column 31; below row 23 the screen scrolls up. `'\n'` moves to the next row's start. Characters without a glyph show as spaces.

| Function | As built |
|---|---|
| `cls()` | clears to the current colours (inverse not applied); print position (0, 0) |
| `putchar(c)`, `puts(s)`, `print(s)` | `putchar` returns `c`; `puts` adds `'\n'` and returns 10 |
| `at(row, col)`, `tab(col)` | row beyond 23 → 23; column & 31 |
| `ink(n)`, `paper(n)`, `bright(n)`, `flash(n)` | n & 7, n & 7, n & 1, n & 1; used by printing, `plot`, `draw` and `cls` |
| `inverse(n)`, `over(n)` | n & 1. Inverse swaps ink and paper for printing and plotting; over XORs characters and pixels |
| `border(n)` | n & 7 |
| `printf(fmt, …)` | `%d %u %x %c %s %%`, a decimal width (right-aligned with spaces). **Deviations:** no flags (`- 0 + #` space); another conversion character prints the next argument as a character; the return value is undefined |
| `getkey()` | waits; ASCII or the editor's control codes (1-4 cursor, 8 DELETE, 13 ENTER) |
| `inkey()` | the key pressed since the last read (the ISR's latch), else 0 |
| `gets(buf, max)` | at most `max - 1` printable characters, echoed; DELETE edits; ENTER ends with a new line; returns `buf`; `max` < 1 counts as 1 |
| `plot(x, y)`, `point(x, y)` | off the screen: nothing / 0. `plot` gives the cell the print attribute |
| `draw(x0, y0, x1, y1)` | both ends included; off-screen coordinates move to the screen's edge |
| `attr(row, col)` | the cell's attribute; 0 outside |
| `mode(n)` | 0 normal, 1 hi-res colour; error 3 if the image uses `$6000-$77FF`; other n: error 4. The end of the program restores mode 0 |
| `sprite_get/put(row, col, w, h, buf)` | 9 B per cell (8 pixel rows, the attribute), row by row; a rectangle not wholly on the screen, or empty: error 4 |
| `beep(frames, semitone)` | frames unsigned (0: nothing); semitone -60..69 above middle C (below -39: A0), else error 4; AY channel A, through the EXROM trampoline (§5.8) |
| `sound(reg, value)` | register 0-15 (else error 4), value & 255 |
| `frames()`, `pause(n)` | `unsigned`; `pause(0)` returns at once |
| `inp(port)`, `outp(port, value)` | 16-bit port addresses |
| `str*`, `mem*` | C89 semantics; characters compared unsigned; `memcpy` is `memmove` (overlap safe) |
| `atoi(s)` | skips spaces and control characters (1-32), optional sign, decimal digits; wraps beyond 16 bits |
| `itoa(n, buf, base)` | bases 2-36 (lowercase), negative only in base 10; returns `buf`; another base: error 4 |
| `abs(n)` | `abs(-32768)` = -32768 |
| `malloc(n)`, `free(p)` | §3.2; NULL when nothing fits and for n ≥ 32 KB; `free(NULL)` does nothing |
| `exit(n)` | ends the program with status n, from any depth |

## 8. Storage

### 8.1 Program tapes

- **Format:** header type 0 with the V2 line store verbatim.
- **Version word** (autostart field): `$8C00` (bit 15 = Leap-tagged, major `$0C` = Leap-C source, minor 0).
- V2 ROMs refuse Leap-C tapes and Leap-C refuses V2 BASIC tapes with `BAD TAPE VERSION` (V2's acceptance rule).
- `LOAD` writes into the source region only, never chunk 6.

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

---

## 9. Extensibility (later)

- V2 packages are not supported.
- A C-oriented library-loading mechanism (precompiled C or assembly libraries in RAM, registered with the compiler's symbol table) is a candidate for a later release.
- Image region 3 (`$F400-$F7FF`) keeps that option open.

---

## 10. Toolchain and repository

- **Assembler:** sjasmplus (as V2), with strict warnings. The ROM images are built by `make`.
- **Emulator:** ZEsarUX 13.0 is the qualification emulator (as V2). Fuse and EightyOne are courtesy only.
- **Test harness:** Python over ZEsarUX ZRCP, derived from V2's `qharness` (vendored with attribution). Test cases are C sources with expectations in header comments (exit value, screen text, memory, compile error and line, runtime error).
- **Budget tooling:** per-component sizes from the listings; `budget.toml` limits; ROM map report.
- **Platform vendoring:** `platform/` pinned to the V2 reference with a delta list. V2 itself is never modified.
- **Cross tools (development only):**
  - a host tool to turn `.c` files into Leap-C program tapes;
  - optionally SDCC as a test oracle (installing it needs owner approval).

---

## 11. Validation (summary; detail in `project_plan.md`)

Every milestone delivers both:

- **assembled size measurements** checked against `budget.toml`;
- **executable tests** in ZEsarUX.

Release qualification covers:

- the corpus;
- the emulator qualification on ZEsarUX;
- the physical TS2068 hardware checklist: EPROM HOME + EXROM, keyboard, tape, timing at 60 Hz, display contention.
