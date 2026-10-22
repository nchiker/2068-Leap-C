# 2068-Leap-C — Recommended easy improvements after Phase 9

**2026-10-21.** The improvements report after Phase 9, as written then (a private document; this copy, made for the public repository in Phase 11, is its text, without its one diagram of library loading Stage 1, which the Stage 1 list below describes). Phase 10 built Fixes 1-5 and Stage 1: `docs/milestones/M10.md`. The prototypes it cites (`spike/improvements/`) were removed from the tree in Phase 11; they are in the history at commit `f209f21`.

## Summary

Phase 9 leaves **HOME at 15,796 B of 16,384 (588 B free, floor 512)** and **EXROM at 7,881 B of 8,192 (311 B free, floor 256)**. Five easy fixes are recommended, in this priority order. Together they add 67 B to HOME and free 95 B in the EXROM:

1. `?:` with a float and an integer arm compiles, as C89 requires: HOME +55 B.
2. Five more errors name the identifier, among them `UNDEFINED FUNCTION`: HOME +17 B, EXROM +18 B.
3. Unsigned division loses a branch that can never run: HOME −5 B, every `/` and `%` 112 T faster.
4. Unreachable code in the EXROM's vendored editor, storage and sound is removed: EXROM −154 B.
5. After a compile error, the cursor lands at the error's column: EXROM +41 B, RAM +2 B.

With all five, **HOME is 15,863 B (521 B free, 9 B above its floor)** and **EXROM 7,786 B (406 B free)**. That leaves HOME almost full. A sixth change is held in reserve until HOME needs the room: moving the editor's line store to the EXROM gives HOME 212 B and costs the EXROM the same, but would put the EXROM 62 B below its floor.

## How the costs were measured

Every byte figure below is measured, not estimated: each fix is built at its smallest in a scratch copy of the Phase 9 tree, assembled with the production build, and its size read from `make budget`. The Phase 9 ROM itself stays frozen and qualified.

- **Starting point:** the final Phase 9 production images, after its last fix (platform delta D14: float code no longer loses frame interrupts; HOME −2 B): HOME `e8da395a…`, EXROM `cef49d74…`.
- **Smallest first:** each design reuses code already in the ROM (for example `CX_TOFLT` for the float conversion) before adding any.
- **Tested:** each prototype is assembled and its own new tests run on ZEsarUX. The full suite runs only when a fix is adopted.
- **Cumulative:** the sizes after each fix assume the fixes above it in the table are applied, in priority order.

## Priority and sizes

| # | Fix | What it improves | HOME B | EXROM B | HOME after (free) | EXROM after (free) |
| --- | --- | --- | --: | --: | --: | --: |
| — | Phase 9, as qualified |  |  |  | 15,796 (588) | 7,881 (311) |
| 1 | `?:` with float and integer arms | C89 conformance: valid programs compile | +55 | 0 | 15,851 (533) | 7,881 (311) |
| 2 | Name in errors 21, 22, 52, 70, 76 | Finding a misspelt or missing name | +17 | +18 | 15,868 (516) | 7,899 (293) |
| 3 | `RT_UDIV` dead branch | Every `/` and `%` 112 T faster | −5 | 0 | 15,863 (521) | 7,899 (293) |
| 4 | Unreachable vendored EXROM code | EXROM room | 0 | −154 | 15,863 (521) | 7,745 (447) |
| 5 | Cursor at the error's column | Finding the fault in a long line | 0 | +41 | 15,863 (521) | 7,786 (406) |
| 6 (reserve) | Editor's line store to the EXROM | HOME room, when needed | −212 | +212 | 15,651 (733) | 7,998 (194) |

Fix 1 comes first because it is the only one that changes which valid C programs compile. Fixes 2 and 5 are usability. Fixes 3 and 4 only remove code, so they can go in with any of the others. Fix 6 is a move, not a fix: the two ROMs' combined free space stays 927 B.

## Each fix in detail

### Fix 1: `?:` with a float and an integer operand (HOME +55 B)

**Problem.** `k ? 1.5 : 2` and `k ? 2 : 1.5` are `ERROR 40: TYPE MISMATCH` today, a documented deviation from C89 6.3.15. C converts the integer arm to float. Programs have to write `k ? 1.5 : 2.0` or cast.

**Smallest design.** One pass, so the integer arm is converted on its own path, reusing the existing `CX_TOFLT` (it already emits the 4-byte `F_OP` int-to-float call):

- **Second arm float, third integer:** the third is converted before the end label is patched.
- **Second arm integer, third float:** the third's path jumps over a small block that converts the second's value; the second's `jp` is redirected to that block.
- **Constant condition:** only the chosen arm is compiled; it is converted if the other arm is a float.
- A pointer or `void` with a float stays `TYPE MISMATCH`.

The patched-`jp` sequence the operator already used is now a shared routine (`.jpover`), which pays for most of the new branch. First prototype: 64 B; after the shrink pass: **55 B**, all in the expression compiler. A program pays 4 B of code per converted arm, plus a 3-byte `jp` when the second arm is the integer.

**Tested (prototype).** A new corpus case covers both orders, both outcomes, a constant condition, `unsigned`, and use in `printf`; two new error cases cover a pointer with a float. All of `tests/expr`, `tests/float` and `tests/stmt` pass. The two old deviation tests (`cond_mixed.c`, `cond_mixed_int_first.c`) would be retired, and `spec.md` §4.9's deviation removed.

### Fix 2: name the identifier in five more errors (HOME +17 B, EXROM +18 B)

**Problem.** Since Phase 9, only `ERROR 23: UNDECLARED IDENTIFIER` shows the name (`LINE 3  'l'`). `UNDEFINED FUNCTION` is the most useful to extend: it is reported at the end of the compile, at the line of first use, so a misspelt call such as `prnt(...)` gives no clue which name failed.

**Smallest design.** The compiler already holds the name in `NM` for four of them; measured on all 26 corpus cases of these errors:

| Error | `NM` holds the right name today | Change |
| --- | --- | --- |
| 21 `REDECLARED` | 10 of 10 | shell list only |
| 22 `ALREADY DEFINED` | 5 of 5 C names; empty for a `#define` | shell list; an empty name shows no name |
| 52 `NO SUCH MEMBER` | 2 of 2 | shell list only |
| 70 `UNDEFINED FUNCTION` | wrong when another name came last (`main` for `g`) | `UNDEF_CHECK` loads `NM` from the symbol's entry |
| 76 `UNDEFINED LABEL` | wrong (`x` for `nowhere`) | the same |

- **HOME, +17 B:** on its error path, `UNDEF_CHECK` points `NM` at the undefined symbol's stored name (`S_NAME`, `S_LEN`).
- **EXROM, +18 B:** the shell's single `cp E_UNDECL` becomes a 6-byte list searched with `cpir`, plus a guard that skips an empty name. The guard also protects the copy from a zero length.

**Tested (prototype).** All 26 cases through the shell's `RUN` show the right name or none: `ERROR 70: UNDEFINED FUNCTION` / `LINE 5  'prnt'`; `ERROR 76: UNDEFINED LABEL` / `LINE 5  'nowhere'`.

### Fix 3: unsigned division's dead branch (HOME −5 B, divisions about 7% faster)

**Problem.** The ROM coverage found a branch of `RT_UDIV`, the helper behind every `/` and `%`, that never runs. It cannot run: before step i of the 16, the remainder is below 2^(i−1), so doubling it never needs a 17th bit. A 3,000-pair test confirmed it stays unexecuted.

**Smallest design.** Delete the `jr c` and its 3-byte target. That saves **5 B**, and the untaken `jr c` cost 7 T on every one of the 16 steps: **112 T** less per division, about 7% of the 1,591 T Phase 2 measured for 60000/7.

**Tested (prototype).** All 110 division-related corpus cases pass, including `udiv_identity.c` (3,000 generated pairs checked against `q × b + r`).

### Fix 4: unreachable code in the EXROM's vendored platform (EXROM −154 B)

**Problem.** The editor engine, storage and sound code came from V2 with options Leap-C never uses. Phase 9's ROM coverage showed this code never ran. Reading its callers shows it cannot run:

- **Editor fallbacks:** the built-in navigation and redraw run only when no hook is set, but the shell always sets both hooks. `EDITOR_INIT`'s clearing of the hooks goes too.
- **Editor keys:** no Leap-C key produces the NEXT ERROR, PREV ERROR, HOME or END codes.
- **`EDITOR_BLOCK_DELETE` and `AY_BEEP`:** entry points with no caller (the coverage report's two never-entered routines). `AY_BEEP` is only V2's 3-byte combined entry to the AY beep. Leap-C's `beep()` calls its two halves directly: `AY_BEEP_PERIOD` in HOME, then `AY_BEEP_PLAY` in the EXROM. The larger port-$FE beeper `BEEP` was already left out, so the ROM holds only the smaller AY beep, and `beep()` is unchanged.
- **`STORAGE_VERSION_WORD`:** chose between the program and the V2 package version words. Leap-C has no packages, so both callers load `V2_FORMAT_WORD` directly.
- **`STORAGE_SAVE`'s name clamp and padding:** the shell always passes a 10-character name, already padded.
- **`SOUND_EXROM`'s upper range check (registers 17 and above):** its only caller is the shell's error chime, which writes fixed registers. `SOUND_EXROM` itself stays. C's `sound(reg, value)` is unaffected: it is `LIB_SOUND` in HOME, which writes the AY chip directly and keeps its own 0-15 check (error 4).

**Smallest design.** Delete the code. Nothing replaces it, and HOME is untouched. Each removal would be recorded as a delta of the vendored copy in `platform/UPSTREAM.md`, as D1-D14 are; the frozen `~/2068-Leap` is not touched.

**Risk.** Each removal relies on a Leap-C rule: the hooks are always set, no key gives those codes, and the name is fixed-length. A later feature that breaks one of these rules, such as a library calling the editor without hooks, would need the code back.

**Tested (prototype, with fixes 1-3).** Shell suite 43/43, cassette suite all pass, end-to-end 0 failures.

### Fix 5: the cursor on the error, not at the start of its line (EXROM +41 B, RAM +2 B)

**Problem.** After a compile error the editor shows the right line with the cursor at column 0. On a long line the user has to find the fault by eye; for a missing `;` the report names the right line, but the cursor is not where the `;` belongs.

**Smallest design.** The compiler already leaves `TOK_PTR` on the token where it stopped. The report computes the column from it (the token's address minus the line's text) and clamps it to the line's end when that token is on a later line, which is exactly the missing-`;` case. A 2-byte cell carries the column to the next `SH_LOAD_EDIT`, which applies it once; runtime errors and normal runs keep column 0. Shrink pass: a column before the line needs no test of its own, because it reads as a large number and the end clamp catches it.

**Tested (prototype).**

| Program line | Error | Cursor lands |
| --- | --- | --- |
| `     int x = 1 ` (no `;`) | 20 `SYNTAX ERROR` | column 13, where the `;` goes |
| `     int a = 3 @ 4; ` | 10 `BAD CHARACTER` | column 14, on the `@` |
| `     k = p * 2; ` | 51 `BAD OPERAND TYPE` | column 13, after the operands |
| `     totl = 5; ` | 23 `UNDECLARED IDENTIFIER` | column 9, just after the name |
| `     beep(1, 99); ` | runtime error 4 | column 0, as now |

Putting the cursor *on* an undeclared name (column 4 above), not after it, would cost about 8 B more: it would read `NM_PTR` for error 23.

### Fix 6, in reserve: the editor's line store to the EXROM (HOME −212 B, EXROM +212 B)

**Problem.** After fixes 1-5, HOME has 521 B free, only 9 B above its floor. The next feature that needs HOME, such as library loading's jump table, has no room.

**Smallest design.** No new code: five routines move from HOME to the EXROM.

- `MEM_LINE_STORE` (158 B) is called only by the shell, which runs from the EXROM.
- Its four helpers (`MEM_FITS_CHECK`, `MEM_BLOCK_LEN_TO_END`, `MEM_READ_STORE_NEW_LEN` and `MEM_COPY_NEW_STMT`, 54 B together) are called only by it and by `MEM_LINE_INSERT`, which delta D11 already assembles in the EXROM.

Moving D11's boundary up, so that all five assemble only in the EXROM, moves 212 B. `MEM_SHIFT_UP` and `MEM_SHIFT_DOWN` stay in HOME, because the library uses them.

**The cost.** It is a move, not a saving. After fixes 1-5, the EXROM would have 194 B free, 62 B below its 256 B floor. Moving `MEM_LINE_STORE` alone (158 B, with the helpers left in HOME) leaves 248 B, still 8 B below the floor. Either version needs the floors rebalanced, or more EXROM savings first.

**Tested (prototype, with fixes 1-5).** Shell suite 42/43 and the corpus through `RUN` 884/886. All three failures are intended changes from fixes 1 and 5, not from the move:

- `D4-typed-run-path` expects the cursor at column 0, but Fix 5 now places it on the error's token, at column 14.
- `cond_mixed.c` and `cond_mixed_int_first.c` are the deviation tests that Fix 1 retires.

## Considered but not recommended as easy

- **The cursor *on* an undeclared name rather than just after it:** about 8 B more on top of Fix 5, for one error. The column after the name is close enough.
- **An identical macro redefinition** (C89 allows `#define N 3` twice): the preprocessor would have to compare replacement lists in HOME, where room is shortest. Writing `#undef` first is the workaround. Not measured.
- **Automatic arrays and structs with initialisers, struct parameters and returns, `long`, function-like macros and `#if`:** each is a language feature with its own parsing and code generation. Each would cost hundreds of bytes, so none is a fix. They belong to Release 2 planning (`spec.md` §9).
- **HOME's 19 instructions that never ran:** mostly carries into an address's high byte, which run only when an address crosses a 256-byte boundary, plus a few rare comparison and error outcomes. This is correct code for inputs the suite does not reach, not dead code, so tests are the right follow-up, not deletion.

## Library loading: the plan

**C extends through functions, so a Leap-C library needs no new syntax: only a table of functions the compiler can find, which its existing binding already searches.** V2's packages had to add statements to BASIC (keywords, parsing, VM hooks); none of that machinery is needed here. Of V2's design only two ideas are kept: the 1 KB window at `$F400-$F7FF` (Leap-C's image region 3) and a version check before anything is stored. A library function is called exactly like `printf`: a `call` to a fixed address with the C ABI. This is a later-release plan (`spec.md` §9); nothing here is built.

**Stage 1: assembly libraries built on a host (estimate: about 100-130 B, mostly EXROM).**

- **The image.** A position-fixed binary for `$F400`: an ABI word, an export table, then code and data. The export table uses the same record as the ROM's `LIB_NAMES` (name, address, signature byte), so no new parser is needed.
- **The tape.** A data tape with its own version word; `tools/lib2tape.py` builds `.tap`, `.tzx` and `.wav` from an sjasmplus source and an ABI include, as `c2tape.py` does for programs.
- **`LIB "name"`.** A shell command that loads through the existing tape path into region 3. It refuses a wrong ABI word before storing a byte, records the table's address in one cell, and reports `LIBRARY name: n FUNCTIONS`. `LIB` alone unloads it; a reset clears it.
- **The compiler.** While a library is loaded, region 3 is closed to program images (as `#pragma hires` closes region 4). On an undeclared name, `XL_BIND` searches the ROM table, then the library's, with the same loop.
- **The ABI.** V2's lesson (finding R1): a library built against one ROM must not call into another. The cheapest guard is the ROM's identity word in the library's header, checked by `LIB`. A fixed jump table of ROM services (V2's 16 slots) costs about 48 B of HOME and lets a library outlive ROM updates.

**Stage 2: libraries written in C on the machine (estimate: 150-250 B more).** `#pragma library` would compile a source into region 3 only and export its non-`static` functions; `SAVE "name" LIB` would write region 3 and the table. It reuses the compiler's region limits and the tape code, but it is a feature of its own, not an easy fix.

**Why region 3.** It is 1 KB, never contended, always visible (chunk 6 can be EXROM or RAM, region 3 is neither), and unused by most programs. A larger window would be region 4 (6 KB), but that is the hi-res display file and runs code 23% slower on a TS2068 (Phase 9's timing).

## Next steps and decisions for you

> **Decided (owner, 2026-10-21).** Fixes 1-5 and library loading Stage 1 with V2-style jump-table slots go into the next phase, Phase 10 (before documentation and release, which becomes Phase 11). The reserve floors may be lowered as far as that needs, but not below 128 B in either ROM, so Fix 6 is not required. The approval prompt is `spike/improvements/PHASE10_PROMPT.md`, and the prototypes are `spike/improvements/fix1-6*.patch` (one patch per fix, applied in order; its README lists what each still needs). The options below are kept for the record.

None of these fixes is applied: the Phase 9 images stay as qualified. Any fix changes the images, so it needs the requalification Phase 9 automated: `make test`, `make fuse`, the kit check with its 30-minute soak, `make check` and `make repro`. That is about 1.5 hours, unattended.

1. **When to apply fixes 1-5.** I recommend all five together as one maintenance release before Phase 10: one requalification covers them all, and Phase 10 starts from the corrected `?:` and the larger EXROM reserve. The alternative is to fold them into Phase 10's first step.
2. **Fix 6 and the floors.** I recommend keeping it in reserve. Apply it only when HOME needs the room, and then lower the EXROM floor to about 192 B, or pair it with further EXROM savings.
3. **Library loading, Stage 1.** Choose between the ROM identity word alone (about 2 B, but each library must be rebuilt for each ROM) and V2-style jump-table slots for ROM services (about 48 B of HOME, so libraries survive ROM updates). With HOME at 521 B free after fixes 1-5, the jump table needs Fix 6 first.
