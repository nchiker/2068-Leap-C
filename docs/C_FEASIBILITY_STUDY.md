# 2068-Leap-C — Architecture Feasibility Study

> **Closed 2026-10-12.** The architecture below is approved and specified in `spec.md`; implementation follows `project_plan.md`. This document is kept as the evidence record.

**Revision 3, 2026-10-12.**

- Revision 2 corrected the premise: Leap-C is a separate language ROM that replaces BASIC.
- **Revision 3 adds the approved code-shape spike (§4).** Its figures replace revision 2's counted estimates for code size, speed, helper cost, stack, banking and runtime RAM.

No compiler was written, nothing was installed, and frozen V2 was not modified. All experimental code is under `spike/` (§11).

## Status at a glance

| Question | Answer | Basis |
|---|---|---|
| ROM reclaimable from V2 | HOME ≈ 12.4 KB; EXROM ≈ 1.6 KB with floating point kept, ≈ 3.8 KB if deferred. **Separate banks, not one pool** | measured, listings |
| Compact native + ROM helpers vs inline native | **49% of the code bytes, 2.7-3.3× slower** on local-variable-heavy loops; 1.35× slower on a call-heavy recursive function | measured, ZEsarUX |
| Mixed template set (locals inline, everything else via helpers) | **80% of the bytes, 0-26% slower** than inline | measured |
| Native vs V2 BASIC (same task) | inline 6-19×, mixed 5.4-17×, compact 3.8-7.2× faster | measured |
| Helper-call cost | CALL+RET 27 T; RST via a `jp` vector + RET **31 T** (4 T *more* than CALL; it saves 2 bytes per site) | measured |
| Code in `$C000-$DFFF` with EXROM paged out | correct and full speed. Interrupts safe (≈ 750 frames). ROM services callable, including EXROM ones through a HOME trampoline (239 T round trip) | measured |
| Runtime RAM left untouched by the kept platform services | **38,059 bytes** outside display and system variables, plus the stack area | measured, canary |
| Preferred architecture | **native Z80 + shared ROM helpers (C), mixed template set by default** | §4.8 |
| Next experiment justified? | **yes:** compiler front-end sizing (declarations, types, symbols, expressions) is now the largest unknown | §7, §9 |

**Evidence tags:**

- **[M]** measured in this study: built images, listings, or ZEsarUX runs.
- **[S]** read from V2 source, or from V2's own recorded measurements.
- **[D]** derived arithmetically from [M] figures.
- **[E]** estimate.

**Reference platform:** frozen V2 release `v2.0.1-emu.1` (`d19b9ea`), HOME `3f13ec2c…`, EXROM `24b1ebb0…`. `spike/tools/get_v2_ref.sh` rebuilds it from the tag with `git archive` (read-only) and checks those hashes.

---

## 1. Premise and method

**2068-Leap-C is a separate language ROM:** a sibling of the planned Leap Pascal and Forth V2 systems. It keeps the proven V2 platform services and replaces the BASIC compiler, VM, shell language parts and BASIC runtime with its own editor integration, compiler and runtime. The target is still the original 48 KB TS2068 with its HOME/EXROM banking.

The primary investigation is an on-machine compiler. Cross-compilation is an alternative or development tool. Revision 1 analysed C *inside* the unchanged V2 ROM; that framing and its "19 bytes of ROM" conclusion are withdrawn.

**Component classification [M]:**

- A routine-level map of both release images was built from the sjasmplus listings: **611 routines** (24,527 of 24,531 used bytes) and **1,206 references** between them.
- **Platform code depends on BASIC code in exactly two places,** both trivial:
  - `EXT2_LOOKUP` → `FOLD_UPPER` (9 B, in the compiler file);
  - `IO_KEY_SCAN_ALL` → `IO_KEY_SCAN_ROW` (3 B, in the RST-padding file).
- The editor engine reaches language code only through the shell's two callback hooks [S].

---

## 2. ROM: what is reclaimable, by bank

### HOME ROM (16,384 B, always visible)

| Component | Bytes [M] | Class |
|---|---:|---|
| VM core | 6,033 | **remove** (BASIC VM, tagged values, BASIC built-ins) |
| BASIC compiler | 5,139 | **remove**, except `FOLD_UPPER` (9). Breakdown: lexer 796, keyword table 342, expressions 1,117, statements 2,445, built-in table 304, emitter and errors 135 |
| Symbol table | 576 | **remove** |
| SAVE ALL, identity CRC, session undo | 591 | **remove** |
| Glue and page-zero padding | 121 | **adapt**: the vectors stay; the six RST slots are reassigned (§4.5) |
| Graphics 2,071 · memory/line store 485 · keyboard 434 · 16-bit math 390 · interrupt, bank switching, AY beep 258 | 3,638 | **keep** (the keyboard map gains C punctuation, §2.3) |
| Package registry | 263 | **optional** (BASIC-statement-shaped) |
| Free | 19 | |

**Reclaimable HOME: ≈ 12.4 KB** [M] (+263 if the package registry goes). **Retained HOME platform: ≈ 4.0 KB.**

### EXROM (8,192 B, chunk 6 `$C000-$DFFF`, visible only while paged in)

| Component | Bytes [M] | Class |
|---|---:|---|
| Array Store | 701 | **remove** |
| Shell: BASIC-only parts (tokenizer, keyword spans, sessions, arrays, run/compile glue) | 878 | **remove** |
| Shell: editor/screen glue 1,319 · command loop 448 · tape commands 433 · messages and chime 471 · entry slots 83 | 2,754 | **keep / adapt** |
| Editor engine 737 · tape 793 · sound 59 · integer number formatting 79 | 1,668 | **keep** |
| FP calculator 1,929 + float formatting 236 | 2,165 | **retain as a candidate component.** Floating point is optional or later-release, not removed from the architecture |
| Free | 26 | |

**Reclaimable EXROM:** **≈ 1.6 KB** with the FP calculator kept. **≈ 3.8 KB** only if floating point is deferred out of the ROM, for example to a later release or a package [M].

### 2.1 Measured supply vs estimated demand, per bank

The banks are **not interchangeable**:

- **HOME** must hold everything compiled programs call. Program code may run in chunk 6, which cannot see the EXROM (§4.7).
- **EXROM** suits code that runs while the editor/shell has chunk 6 paged in.

| | HOME | EXROM |
|---|---:|---:|
| **Supply** (measured, reclaimable) | ≈ 12.4 KB | ≈ 1.6 KB (FP kept) / ≈ 3.8 KB (FP deferred) |
| Runtime helpers | 0.9-1.8 KB [E]; spike core set **92 B** [M] | — |
| Compiler | 6.9-10.8 KB total [E]. Hot parts must be in HOME: lexer, expressions, statements, code generator | cold parts can go here: preprocessor, diagnostics, messages, keyword table (≈ 0.6-1.0 KB [E]) |
| Shell adaptations, C keyword highlighting, punctuation glyphs | ≈ 0.1 KB (glyphs + key map) [E] | ≈ 0.5-0.9 KB [E] |
| **Fit** | 6.9-12.1 KB of 12.4 KB with the cold compiler parts in EXROM (6.9-12.7 KB with everything in HOME) | 1.1-1.9 KB of 1.6 / 3.8 KB |

**Verdict:**

- **Fits** at the low and middle of the estimates.
- At the high end, **HOME is about 0.3 KB short** if the whole compiler sits in HOME. It fits narrowly (12.1 of 12.4 KB) once the cold parts move to EXROM. With FP kept, **EXROM is then up to 0.3 KB over** in the worst case.
- The compiler estimate (§3) is now the deciding unknown.
- A DOCK cartridge (stock TS2068 banked ROM) would remove the limit; that remains an owner decision.

### 2.2 Reuse

**Reused directly as runtime [M][S]:**

- 16-bit multiply/divide/mod/sqrt/random/compare (the spike's `fact` calls `MATH_MULTIPLY16` directly);
- `MEM_FILL`, `MEM_SHIFT_*`;
- character, string, attribute, scroll, pixel, line and sprite output;
- keyboard and the `FRAMES` counter; AY sound;
- integer formatting; tape;
- the editor engine and line store.

**Not reusable:** BASIC's 32-byte string slots, the tagged VM stack, float promotion, and the symbol-table layout.

**New runtime [E], about 0.9-1.8 KB:**

| Part | Bytes |
|---|---:|
| Frame, local and indirect helpers | **92** measured |
| Compare and shift extras | 50-150 |
| Switch dispatch | 50-100 |
| `str*`/`mem*` | 150-250 |
| Small `printf` | 250-400 |
| Line input | 100-200 |
| Platform bindings | 200-400 |
| Startup, exit and errors | 100-200 |

32-bit `long` adds 0.6-0.9 KB.

### 2.3 Editor

V2 stores programs as **plain text lines without line numbers** (`[len:2][text][CR]`, 127 characters at most) [S]. C source fits as is, so the editor, navigation, error-line jump, LIST and the program tape format carry over.

Needed changes:

- **C keyword highlighting** (≈ 200-250 B [E]).
- **C punctuation.** The key map cannot type `{ } [ ] | ~ ^ \`, and the font has no glyphs for them (V2 defect Q-26) [M]. Adding 9 glyphs and their keys costs about 90 B [E].
- **Compile and run commands** in place of BASIC's.

---

## 3. Compiler size estimate (unchanged; not measured by this spike)

| Component | Estimate [E] | Anchor |
|---|---:|---|
| Lexer + source streaming | 0.8-1.1 KB | V2: 796 B [M] |
| Keyword table (32 keywords) | 0.2-0.25 KB | V2: 342 B [M] |
| Expressions (15 levels, lvalues, pointer scaling, `?:`, compound assignment, calls) | 1.4-2.0 KB | V2: 1,117 B, untyped [M] |
| **Declarations and types** (`char`/`int`/`unsigned`, pointers, arrays, `struct`, functions, parameters, locals) | 1.5-2.5 KB | **no V2 analogue** |
| Statements | 1.0-1.5 KB | V2: 2,445 B for more statement forms [M] |
| Symbol table with scopes | 0.6-0.9 KB | V2: 576 B [M] |
| Code generator: template table + fixups | 0.8-1.4 KB | the spike's templates are 1-12 B each [M] |
| Preprocessor (object-like `#define`) | 0.2-0.4 KB | |
| Diagnostics, compile/run glue | 0.4-0.7 KB | |
| **Total** | **6.9-10.8 KB** | |

---

## 4. The code-shape spike (measured)

### 4.1 Method

**The C being stood for.** Four workloads from the investigation plan are written in conventional C in `spike/c/workloads.c`:

| Function | What it exercises |
|---|---|
| `sum(255)` | local-variable loop |
| `copy(d,s,256)` | pointer walk |
| `asum(100)` | indexed `int` array |
| `move(pts,20,3)` | `struct` field updates |
| `fact(7)`, `fact(20)` | recursion with locals |

**Templates.** Each C statement was translated by hand with **fixed templates of a naive single-pass Small-C-style code generator**: HL primary, DE secondary, temporaries pushed, IX frame base, arguments pushed right to left, caller cleanup, the single-pass `for` layout. Nothing was optimised by hand (`spike/asm/templates.inc`, `workloads.asm`).

**One source, four template sets:**

| Form | Locals | Other templates | Helpers entered by |
|---|---|---|---|
| A | inline | inline | — |
| C-call | helper | helper | CALL (runs on the unmodified V2 ROM) |
| C-rst | helper | helper | RST (needs an experimental V2 image whose six RST vectors hold `jp helper`, V2's own vector pattern) |
| Mixed | inline | helper | RST |

**Runs:**

- Release ROM in ZEsarUX 13.0 through 2068-Leap's own `qharness` (ZRCP: exact `get-tstates-partial`, breakpoints, memory access).
- Helpers at `$5B00`, standing in for HOME ROM. Code at **`$C000`** and data at `$D000`, with **EXROM paged out**. A second copy at `$8400` ran with EXROM paged in.
- Interrupts off for timing, then repeated with them on.
- Stack high-water by canary over `$F800-$FEFF`.
- Every result checked: return values, copied bytes, struct contents, screen text. **All 86 native runs correct** (6 form/location variants × 7 cases × interrupts off and on, plus 2 soaks), and all 5 BASIC equivalents.

**V2 BASIC equivalents:**

- Compiled and run from `V2_RUN_STORED`; the run phase is timed from `VM_RUN`, with interrupts on as in normal use.
- Each program's result was verified.
- They are idiomatic equivalents, not identical semantics: a `FOR` loop, a `PEEK`/`POKE` copy, parallel arrays instead of a struct, a `PROC` with a global accumulator.
- Array setup was subtracted by running a setup-only program.

### 4.2 Code size [M]

| Function | A inline | C-call | **C-rst** | **Mixed** |
|---|---:|---:|---:|---:|
| `sum` | 79 | 55 | 35 | 67 |
| `copy` | 73 | 56 | 40 | 64 |
| `asum` | 122 | 83 | 57 | 97 |
| `move` | 112 | 84 | 54 | 86 |
| `fact` | 92 | 66 | 50 | 70 |
| **Total** | **478** | **344 (72%)** | **236 (49%)** | **384 (80%)** |
| Code bytes per byte of stored source (719 B line store, 53 lines) | 0.66 | 0.48 | **0.33** | **0.53** |

Helper bodies [M]: LDL 17 · STL 17 · ENTER 18 · LEAVE 16 · LDI 5 · STI 6 · CMPLT 13 = **92 B**. The dispatcher and its table add 21 B.

### 4.3 Execution time [M]

Interrupts off, code at `$C000`, T-states including argument passing and caller cleanup:

| Case | A inline | Mixed | C-call | C-rst | V2 BASIC loop* | BASIC compile* |
|---|---:|---:|---:|---:|---:|---:|
| `sum(255)` | 75,258 | 75,415 | 241,553 | 249,371 | 1,005,344 | 391,744 |
| `copy(256)` | 98,363 | 98,587 | 268,402 | 273,790 | 1,706,387 | 347,992 |
| `asum(100)` | 47,850 | 55,945 | 132,343 | 135,342 | 511,571 | 551,589 |
| `move(20)` | 13,009 | 16,413 | 33,861 | 34,569 | 249,746 | 784,864 |
| `fact(7)` | 12,596 | 13,874 | 16,841 | 17,051 | 75,162 | 499,195 |
| `fact(20)` | 39,786 | 43,975 | 53,849 | 54,495 | — | — |

\* BASIC runs with interrupts on; the interrupt handler takes about 2.9% of the time in this emulator model.

| Ratio [D] | sum | copy | asum | move | fact7 |
|---|---:|---:|---:|---:|---:|
| C-rst ÷ A | 3.31 | 2.78 | 2.83 | 2.66 | 1.35 |
| Mixed ÷ A | 1.00 | 1.00 | 1.17 | 1.26 | 1.10 |
| BASIC ÷ C-rst | 4.0 | 6.2 | 3.8 | 7.2 | 4.4 |
| BASIC ÷ Mixed | 13.3 | 17.3 | 9.1 | 15.2 | 5.4 |
| BASIC ÷ A | 13.4 | 17.3 | 10.7 | 19.2 | 6.0 |

**Location.** Code at `$8400` with EXROM paged in timed the same as at `$C000`: identical for A, within 0.34% for C-rst. ZEsarUX models no display contention for `$6000`/`$7000` either: 1,000 NOPs = 4,004 T everywhere [M]. Real-hardware contention is still unverified.

### 4.4 Helper-call overhead [M]

Single invocations, interrupts off. Site bytes are the bytes at the call site:

| Operation | Inline | CALL helper | RST helper (`jp` in vector) |
|---|---:|---:|---:|
| Reach an empty helper and return | — | 27 T / 3 B | **31 T / 1 B** |
| Load local word (IX + offset) | 38 T / 6 B | 130 T / 4 B | 134 T / 2 B |
| Store local word | 38 T / 6 B | 130 T / 4 B | 134 T / 2 B |
| Load word through HL | 24 T / 4 B | 51 T / 3 B | 55 T / 1 B |
| Store word through DE | 28 T / 5 B | 55 T / 3 B | 59 T / 1 B |
| Signed compare | 53 T / 12 B | 80 T / 3 B | 217 T / 2 B via the dispatcher |
| Empty function with 2 B of locals (call + prologue + epilogue) | 125 T, 19 B | 274 T, 11 B | 282 T, 7 B |
| EXROM round trip (page out + page in; the trampoline cost) | — | 239 T / 6 B | — |

**What a helper call really costs:**

- **RST is not a one-byte call in time.**
  - RST 11 T + the vector's `jp` 10 T + RET 10 T = 31 T, against CALL 17 T + RET 10 T = 27 T. So RST is **4 T slower than CALL** and saves 2 bytes per site.
  - A helper that takes an operand byte needs a 2-byte site plus about 100 T inside the helper to fetch the operand and form the address. That is why local access via a helper costs 134 T against 38 T inline.
- **Removing the `jp` [D].** A helper body that fits its 8-byte vector slot (LDI 5 B, STI 6 B) can sit at the vector itself. That saves the `jp`'s 10 T, making it 6 T faster than CALL: LDI 45 T, STI 49 T.
- **The generic dispatcher** (RST + function-number byte, for helpers beyond six) costs 137 T more than a CALL to save 1 byte. It is only worth it for cold helpers.

### 4.5 RST vectors [M]

From the V2 page-zero dump and source:

| Vector | V2 use | Leap-C |
|---|---|---|
| `$00` | reset (`di; jp V2_COLD_START`) | fixed |
| `$08` | `jp LEX_NEXT_TOKEN` | **free** |
| `$10` | `jp VM_POP` | **free** |
| `$18` | `jp VM_POP_COERCE_INT` | **free** |
| `$20` | `jp EMIT_BYTE` | **free** |
| `$28` | `jp V2_CALC_ENTRY` (FP calculator) | **free**: the calculator can be CALLed |
| `$30` | `inc sp ×2; jp COMPILE_RAISE_ERROR` | **free** |
| `$38` | IM 1 interrupt: `call KBD_ISR_TICK; ei; reti` | fixed |
| `$66` | NMI | fixed |

**Six RSTs are available.** The spike assigned them to the six helpers with the most call sites (LDL, STL, ENTER, LEAVE, LDI, STI) and ran them end to end on the experimental image. Every other helper is a CALL.

### 4.6 Stack [M]

Measured with interrupts off:

| Workload | Stack used |
|---|---:|
| `sum`, `copy`, `asum`, `move` | 10-14 B inline; +4 B with helpers (one helper return address and one push) |
| `fact` | **10 B per recursion level** in every form; `fact(20)` 200 B |

With interrupts on, the handler adds up to 16 B. The kept platform services reached a high-water of **28 B including the interrupt handler** (§5.1).

**Consequence:** in the existing 1,792-byte stack area, C recursion of this shape goes about 170 levels deep. Large local arrays or deeper recursion would need a bigger stack area, which is a layout choice in a C ROM.

### 4.7 Banking validation [M]

| Check | Result |
|---|---|
| V2's state at the command loop | EXROM paged in: depth counter 1, port `$FF` shadow `$80` |
| Code at `$C000` and data at `$D000`, EXROM paged out (`BANK_PAGE_EXROM_OUT` takes the depth to 0) | all workloads correct in every form, interrupts on and off |
| Interrupts during chunk-6 execution | **soak:** 200 × (`sum` + service call) with interrupts on: **742-763 frames, 0 errors**, C-call and C-rst. The handler and stack live in HOME/high RAM |
| HOME service from chunk-6 code (`GFX_PUTCHAR`) | correct |
| EXROM service from chunk-6 code through a HOME trampoline (`PKG_NUM_TO_TEXT_SAFE`) | correct 200× in the soak. Returns to chunk 6 with depth 0. Round trip 239 T |
| **Negative control:** chunk-6 code pages EXROM in *without* a trampoline | the next fetch came from EXROM: its byte-copy loop at `$C179` ran, writing through DE, and the program's own code never ran. **Rule confirmed:** every EXROM service is reached only through a HOME trampoline, and neither the trampoline nor the stack may live in chunk 6 |
| Loading chunk-6 RAM | ZRCP writes to `$C000-$DFFF` while EXROM is paged in are lost: the spike's first run failed this way. The kept tape routines are *EXROM-resident*, so they cannot load directly into the RAM underneath themselves (expected from the hardware rule; not run). A Leap-C loader must stage the load or put the loader in HOME |
| `BANK_PAGE_EXROM_IN/OUT` | nest by depth count and **always end with `EI`** [S]: runtime critical sections must allow for that |

### 4.8 Interpretation

1. **Compact native code works, and the helper mechanism is sound.**
   - RST dispatch, inline operand bytes, frames, recursion, chunk-6 execution and ROM service calls all ran correctly on the real ROM image.
   - The full-compact form halves code size and is still 3.8-7.2× faster than V2 BASIC.
   - It is also 2.7-3.3× slower than inline code on local-variable-heavy loops, because each local access is a 134 T helper call against 38 T inline.
2. **Density matters less than revision 2 assumed.**
   - Measured code is only 0.33-0.66 bytes per byte of resident source (small sample), so source text dominates program RAM.
   - Going from mixed (0.53) to full compact (0.33) adds only about 15% of source capacity (§5.2), at a 2.5-3× speed cost.
3. **The mixed template set is the best default.**
   - Inline locals (6 B, 38 T) plus 1-byte RST helpers for indirect access, frame entry and exit, ROM calls for compare/multiply/divide and platform services.
   - Measured: within 0-26% of inline speed at 80% of the bytes.
   - Full-compact templates stay possible as a size option. A vs C is a **template-table choice inside one compiler**, not a separate architecture.
4. **Revision 2's decision rule** ("≤ 1.5× bytecode density and ≥ 4× V2 speed") is met by C-rst on density, but only borderline on speed (`asum` 3.8×). It is met by mixed on speed, but not on density. Point 2 shows the density threshold was set too strictly, so the rule is resolved in favour of mixed. The "under 2× V2: revisit" condition was not triggered by any form.

### 4.9 Architecture comparison, updated

| | Status after the spike |
|---|---|
| **A** on-machine, inline native | measured. Fastest; 1.25× mixed's bytes. Kept as the speed end of the template table |
| **B** on-machine, C-specific bytecode VM | **not built** (outside the approved scope). Its estimated density is close to the *measured* full-compact native form (7 vs 9 B per typical statement). Its speed would lie between C-rst and V2 BASIC, and it needs a VM in HOME (1.5-3 KB [E]). No measured reason to pursue it |
| **C** on-machine, native + shared ROM helpers | **measured; preferred.** Mixed templates by default |
| **D** cross-compiler | unchanged: a development tool and oracle against the same runtime ABI. SDCC not installed |

Historical basis for C: Small-C. Single-pass recursive descent, no IR, HL/DE primary/secondary registers, assembler runtime library [S, sources]. Leap-C moves that library into ROM and reaches the hottest entries by RST.

---

## 5. RAM (measured where possible)

### 5.1 Runtime RAM untouched by the kept platform services [M]

`spike/ram_probe.py` fills every candidate region with a canary. Chunk 6 is filled by the probe itself while paged out. It then exercises the kept services:

- clear screen, 704 characters, a string, two scrolls;
- 192 pixels, a line, clipped plots, sprite capture/draw;
- multiply, divide, mod, sqrt, random; `MEM_FILL`; key poll;
- 50 interrupt frames;
- number formatting through the EXROM trampoline, AY beep, and a tape `SAVE` (EXROM paged in).

| Region | Bytes | Changed by the platform |
|---|---:|---|
| `$5B00-$7FFF` | 9,472 | nothing |
| `$825A-$BFFF` | 15,782 | 2 bytes (`VM_PRINT_TEXT_TMP`, used by V2's VM number printer, which Leap-C replaces) |
| `$C000-$DFFF` (chunk 6, EXROM out) | 8,192 | nothing |
| `$E000-$F17F` | 4,480 | nothing |
| `$F328-$F3AE` | 135 | nothing |
| **Total untouched** | **38,059** | |
| Stack area `$F800-$FEFF` | 1,792 | 28 B high-water |

System-variable bytes written by the services: 13 short runs in `$80B0-$8184` plus `FRAMES`. The 602-byte block stays as is; trimming it is future work.

**Not exercised by the probe:**

- the editor engine (uses the edit buffer `$F228-$F327` and shell cells);
- the FP calculator, tape `LOAD`;
- dual-screen/hi-res `MODE` (6,144 B of `$6000-$77FF`);
- the SPRITE package buffers (2,304 B at `$E800`);
- the package window (`$F400`).

**Net for a C system** ≈ 38.1 KB minus its own shell/editor/compiler cells (0.5-1.2 KB [E]) ≈ **36.9-37.6 KB**. That confirms revision 2's map estimate with a measurement.

### 5.2 Program capacity [D]

Assumptions: 37 KB net, about 2 KB globals, about 2 KB minimum heap. That leaves about 33 KB for resident source plus code, with code = k × source (k measured in §4.2):

| Template set | k | Source capacity | Code at that size |
|---|---:|---:|---:|
| Full compact (C-rst) | 0.33 | ≈ 25 KB | ≈ 8 KB |
| **Mixed** | 0.53 | **≈ 21.5 KB** | ≈ 11.5 KB |
| Inline (A) | 0.66 | ≈ 20 KB | ≈ 13 KB |

At this sample's 13.6 B per stored line, 21.5 KB is about 1,500 lines. Denser source with longer lines reaches fewer. The k values come from a 53-line sample and need confirming on larger programs.

Generated code (8-13 KB) fits the 8 KB of chunk 6 for most programs. Larger code continues in low RAM.

### 5.3 Staged compilation

1. **Edit:** source plus the edit buffer.
2. **Compile:** single pass.
   - Source is streamed through V2's 264-byte chunk window [S].
   - Code is emitted directly.
   - Workspace: global and local symbols, string literals, labels, and forward-call fixups chained through the emitted operands. About 2-3.5 KB [E].
3. **Run:** the workspace becomes heap/stack. An optional function → line table costs about 4 B per function.

**No intermediate representation is retained or needed.** A second pass over the resident source costs time, not RAM. Compile speed at V2's rate is about 62,000 T (about 18 ms) per line [S]. The spike's 5-10 line BASIC programs compiled in 0.35-0.78 M T [M].

### 5.4 RAM constraints

1. **Resident source dominates:** 60-75% of program RAM [D].
2. **Chunk 6 is conditional.** It is ideal for code and data at run time, but:
   - EXROM services need the trampoline;
   - loading into it needs a staging step or a HOME loader (§4.7);
   - it cannot hold the source while the EXROM editor runs.
3. **The stack is 1.8 KB:** about 170 levels at 10 B per level.
4. **Graphics modes and sprites borrow 6 KB and 2.3 KB.**
5. **Real-hardware contention and 60 Hz timing are unverified.** ZEsarUX's TS2068 model ran about 70,000 T per frame in the soak, with the interrupt handler taking 2.0-2.5 kT per frame.

---

## 6. Realistic initial C capability

| Area | Expectation |
|---|---|
| Types | `char` (8-bit), `int`/`short`, `unsigned`, 16-bit pointers, arrays (1-D; multi-dimensional desirable), `struct` (desirable), `enum`, `typedef` (moderate) |
| Floating point | **optional or later-release feature, not removed from the architecture.** The V2 calculator (1,929 B + 236 B formatting, EXROM) is retained as a candidate, reached through the measured trampoline (239 T per round trip plus the calculator's own cost). Costs and benefits are not yet evaluated |
| Deferred | `long` (runtime 0.6-0.9 KB), `union`, bitfields, struct copy and return |
| Statements, functions | all C89 control flow; parameters, locals, recursion (measured 10 B per level), function pointers |
| Expressions | all integer operators, `sizeof`, integer/pointer casts |
| Strings, library | literals, `char` arrays, ROM `str*`/`mem*`, a small `printf`, the platform library (text, colours, keys, line input, plot/line, sprites, sound, frames, random, tape) |
| Preprocessor | object-like `#define`; an implicit platform header |
| Not planned | file `stdio`, separate compilation and linking (cassette workflow) |

---

## 7. Remaining uncertainties

1. **Largest: compiler size in HOME.** In particular the declaration/type front end, the scoped symbol table, and typed expressions (pointer scaling, lvalues, struct members). None has a V2 analogue (§3). The code generator's templates are now known (§4), so this is the remaining term of the per-bank fit (§2.1).
2. **Code/source ratio on realistic programs.** The k values come from 53 lines (§5.2).
3. **Loading code or data into chunk 6** given EXROM-resident tape routines: needs a design choice (§4.7).
4. **Floating-point cost and benefit** (owner priority; the component is retained).
5. Real-hardware contention and frame timing; keyboard ergonomics of the added punctuation.

## 8. Recommendation

- **Architecture C confirmed by measurement.** An on-machine, non-optimizing, single-pass Small-C-style compiler emitting native Z80, with a shared HOME-ROM helper library:
  - **mixed templates by default:** locals inline; RST helpers for frame entry and exit and indirect access; CALLs for compare/multiply/divide/platform;
  - full-compact templates as an optional size mode.
- **Bank rules:**
  - runtime helpers and anything compiled code calls → HOME;
  - EXROM services only via HOME trampolines;
  - program code and data may use chunk 6 while EXROM is paged out.
- **Keep** the V2 platform services as classified in §2. Floating point stays a retained optional component.
- **Cross-compiler (D)** remains a development and test companion, not the product.

## 9. Proposed next experiment: compiler front-end sizing spike

**Justified:** yes. It is now the largest unknown, and it decides whether HOME holds the compiler.

**Smallest form (one session):**

1. Assemble, with sjasmplus and against the V2 kernel, only the front-end pieces that have no V2 analogue:
   - declaration parsing for `char`/`int`/`unsigned`, pointers, 1-D arrays and `struct`;
   - the type representation;
   - the scoped symbol table;
   - typed lvalue/expression handling (pointer scaling, member offsets, `*`/`&`/`[]`/`->`).
2. Emit the spike's measured mixed templates. Stub the lexer and statements (V2 anchors exist for those).
3. Measure assembled bytes. Run a handful of declaration/expression cases in ZEsarUX to confirm the pieces work, not merely assemble.

This is a sizing prototype, not the compiler.

**Decision rule:**

- **≤ 4.5 KB:** the compiler fits HOME with at least 1 KB margin; proceed to specification.
- **4.5-6 KB:** plan the HOME/EXROM compiler split.
- **> 6 KB:** revisit the language subset (for example `struct` later) or the DOCK option.

---

## 10. Retained findings and tools

- **The V2 BASIC VM is unsuitable for C** [S]: tagged values, float promotion, no frames, bitwise operators, unsigned or indirection, bytecode without a load path.
- **The V2 kernel uses no IX/IY** [M]; the spike's IX frames ran alongside kernel calls and interrupts without conflict [M].

**Tools used:**

- sjasmplus;
- ZEsarUX 13.0 through 2068-Leap's `tools/qual/qharness.py` (imported read-only), which uses ts2068-debug's ZRCP client;
- the `benchmark-z80` method (exact ZRCP T-states, result verification, completion checks).

**Not used:** z80sim (no T-state counting). **Not installed:** SDCC (apt 4.2.0 candidate), z88dk.

## 11. Spike files and reproduction

| File | Purpose |
|---|---|
| `spike/tools/get_v2_ref.sh` | export and build the frozen release from its tag; verify hashes → `spike/v2ref/build/` |
| `spike/asm/templates.inc` | the code-generation templates, forms A / C / mixed, CALL or RST |
| `spike/asm/helpers.asm` | the helper library (92 B core + dispatcher) |
| `spike/asm/workloads.asm` | the workloads, banking probes, soak |
| `spike/c/workloads.c` | the C those stand for (also the code/source ratio sample) |
| `spike/run_spike.py` | assembles every variant, builds the two RST-patched experimental images in `spike/build/`, runs and verifies all cases plus V2 BASIC equivalents. `--micro-only` reruns the helper micro-benchmarks |
| `spike/ram_probe.py` | the platform RAM canary probe |
| `spike/tools/probe.py` | banking state at the command loop, T-state exactness, contention check, ROM write test |
| `spike/tools/romdeps.py`, `classify.py` | the routine-level ROM map and BASIC/platform classification (§1-2): `python3 spike/tools/romdeps.py spike/v2ref/build > deps.json && python3 spike/tools/classify.py deps.json` (`get_v2_ref.sh` copies the listings) |
| `spike/results/` | `spike_results.json`, `spike_run.log`, `ram_probe.json` |

To reproduce:

```
spike/tools/get_v2_ref.sh && python3 spike/run_spike.py && python3 spike/ram_probe.py
```

That takes about 15 minutes and needs `~/2068-Leap`, `~/ts2068-debug` and ZEsarUX 13.0.

---

**Sources** (external facts only):

- Small-C 2.1 subset and assembler runtime library: [comp.lang.c review, 1985](https://www.tuhs.org/Usenet/comp.lang.c/1985-April/003959.html), [Small-C (Wikipedia)](https://en.wikipedia.org/wiki/Small-C)
- z88dk TS2068 target: [Z88DK (Wikipedia)](https://www.wikipedia.org/wiki/Z88DK), [C Programming and the Timex/Sinclair 2068](https://www.timexsinclair.com/article/c-programming-and-the-timex-sinclair-2068/)
- Historical on-machine compiler sizes: [HiSoft BASIC](https://spectrumcomputing.co.uk/pub/sinclair/games-info/h/HiSoftBASIC.txt), [HiSoft Pascal review](https://zxart.ee/eng/software/pressa/disk-magazine/spectrum-expert-02/soft)
