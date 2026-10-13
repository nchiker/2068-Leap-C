# 2068-Leap-C — Specification

**Version 0.4, 2026-10-13** (v0.1, 2026-10-12: initial; v0.2, v0.3, 2026-10-13). This specification is derived from `docs/C_FEASIBILITY_STUDY.md` (revision 3), whose architecture decisions are approved.

**Changes in v0.2:** the frame's reference point (§5.2) and the `ENTER`/`LEAVE` contracts (§2.3, §5.3), by owner decision during M1.3 (`docs/milestones/M1.3.md`).

**Changes in v0.3 (Phase 2, owner decisions O1/O2 of 2026-10-13):** the retained 16-bit math is cut to what C uses (§2.1, platform delta D3). Multiply and divide are the helper core's own routines (§5.3). `rand()`/`srand()` are a C generator (§7).

**Changes in v0.4 (Phase 2, as built):** the preprocessor's rules and limits (§4.8, §4.10), the `SWITCH` tables (§5.3), and the function → line table's format (§5.9).

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
| Graphics: text, attributes, scrolling, pixels, line, sprite capture/draw, font | 2,071 | HOME | kept. **Delta:** 8 glyphs `[ ] { } \| ~ ^ \` (§6.2) |
| Memory: line store, fill, shift, cold init | 485 | HOME | kept. **Delta:** re-pointed to the Leap-C memory map (§3) |
| Keyboard I/O | 434 | HOME | kept. **Delta:** symbol-shift map for the 8 C characters (§6.2) |
| 16-bit math (`MATH_NEGATE16`, `ABS16`, `COMPARE16`) | 390 → 39 | HOME | **Delta D3 (v0.3):** multiply and divide moved to the helper core's register-only routines (§5.3); `SQRT16`, `SGN16`, `MULTIPLY16` removed (no Release 1 caller); `RND16` replaced by the library's `rand()` (§7) |
| Interrupt (IM 1, `FRAMES`, keyboard scan) | 154 | HOME | kept. **Delta:** BREAK request for native programs (§5.8) |
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

## 3. Memory map (baseline)

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

**Hi-res protection.**

- The runtime's mode switch to dual-screen/hi-res mode fails with a runtime error if the image uses `$6000-$77FF`.
- A compile option (`#pragma hires`) reserves that region so the compiler never allocates it.

**Heap.** At run time, after the compile workspace is released:

- `[source end, source-region top)` is the heap, used by `malloc`/`free` (§7.4);
- the stack is `$F800-$FEFF`.

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
| Nesting depth (blocks, expressions) | bounded by the compiler's stack guard; at least 32 levels guaranteed |
| Function parameters | 16 |
| Local frame size | 255 bytes (8-bit frame offsets; larger locals → "frame too large"; use `static` or the heap) |
| `switch` cases | memory-bound (6 B of compile workspace per case) |
| Macro expansions nested in one another | 8 ("nesting too deep") |
| Tokens produced by one macro expansion, nested ones included | 255 ("nesting too deep") |
| String literal length | one line, 126 characters (adjacent literals concatenate) |

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
| Alternate set | unused |

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
| `ENTER n` | RST `$18` + byte | push IX; IX = SP; SP -= n; **stack check** against `STACK_LIMIT` (runtime error *stack overflow*) |
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

**Start, in HOME runtime:**

1. Page EXROM out.
2. Set SP = `$FF00` and record `RUN_SP`.
3. Zero or initialise static data.
4. Set `STACK_LIMIT`, initialise the heap and set `RUNNING = 1`.
5. `call main`.

**Exit.** On return from `main`, `exit(n)`, a runtime error or BREAK, the runtime:

1. silences AY channel A;
2. restores the display state (normal mode, not hi-res) only if the program changed it — baseline behaviour, confirmed in Phase 3;
3. restores `BANK_EXROM_DEPTH` and the paging state the shell expects;
4. clears `RUNNING` and returns to the shell with a status code (exit value, runtime error number, or BREAK).

### 5.8 BREAK (fixed requirement; baseline mechanism)

**Requirement:** BREAK (CAPS SHIFT + SPACE) stops a running program and returns to the editor with the source intact. Native code has no dispatch loop to poll.

**Baseline mechanism:**

- When the ISR decodes BREAK while `RUNNING = 1` and the no-break counter `NOBRK = 0`, it discards the interrupted context by restoring SP = `RUN_SP` and jumps to the runtime's BREAK exit, which re-normalises paging and sound.
- Runtime sections that must not be interrupted mid-way increment `NOBRK` and set `BRKPEND` on a deferred request; the exit of such a section honours `BRKPEND`. These sections are EXROM trampolines, tape I/O, AY sequences and heap updates.
- Cost: about 20-40 B in the ISR delta (estimate; measured in Phase 3).
- `PAUSE`-style waits in the library end on BREAK.

### 5.9 Runtime errors

| Code | Error |
|---|---|
| 1 | stack overflow (from `ENTER`) |
| 2 | out of heap (`malloc` returns NULL; error only for library calls that cannot report NULL) |
| 3 | hi-res mode with the image in `$6000-$77FF` |
| 4 | invalid library argument (where checked) |
| 5 | BREAK |

The shell shows `RUNTIME ERROR n` with the source line of the failing function's call site where available. The line mapping comes from a function → line table the compiler emits: one record per function definition in the image's static data, `[link][address][line where the definition starts]`, newest first, from `RUN_FNLINES` (as built in Phase 2: 6 B per function).

No bounds or NULL checks are generated; this is C.

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
