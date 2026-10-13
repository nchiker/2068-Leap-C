# 2068-Leap-C — HOME ROM inventory and Z80 size audit (Phase 1 close)

**Date:** 2026-10-13. **Baseline:** commit `5b062b3` (M1.3, Phase 1 complete), production images `leapc_home.bin` `cf77885f…` and `leapc_exrom.bin` `e821ff7d…`, rebuilt from the clean tree and identical to the hashes in `docs/milestones/M1.3.md` §5.7.

**Scope.** A read-only engineering checkpoint before Phase 2: what occupies the HOME ROM, what is allocated and what is free, which retained V2 routines are used, how much size optimisation has been done, and where safe bytes remain. No production code, `budget.toml` entry or reserve policy is changed. The approved decisions (saved-IX frame, `spec.md` v0.2; internal calling convention; the provisional 269 B transfer L8; frozen `~/2068-Leap`) are taken as given.

**Tools.** `tools/rom_inventory.py` (new, read-only: every byte of the image classified from the assembler listing, with a cross-reference and reachability; `make inventory`), `tools/budget.py`, and the z80-skills `shrink-z80` scanners (`production_reachability.py`, `z80_pattern_scan.py`, `literal_dup_scan.py`, `deadcode_scan.py`), run against the fresh build.

Evidence classes, as in the `shrink-z80` skill: **EXACTO** = counted from the current listing; **ESTIMADO** = a local count whose final size depends on the rewrite; **[E]** = an estimate of work not yet written.


## 1. Principal findings

1. **The inventory reconciles exactly.** HOME holds 12,739 B of production code and data at `$0000-$31C2`: 11,309 B of instructions, 1,400 B of tables and data, 30 B of page-zero padding. The 3,645 B above `$31C2` are all `$FF`. The per-routine sums equal `tools/budget.py`'s component sizes for every component, and no byte is unaccounted (§2).
2. **Physical free space is 3,645 B, but only 512 B of it is unallocated.** The other 3,133 B are unused component budgets that Phases 2-8 are expected to fill (§3).
3. **38 retained V2 routines (1,474 B, 40% of the platform) have no caller yet.** 1,361 B of them are needed later: the Phase 5 shell (line store, bold characters, status rows, 425 B) and the Phase 3 library (scrolling, pixels, lines, sprites, attributes, `inkey`, random, 936 B). **113 B have no planned caller in Release 1:** `MATH_SQRT16` (81), `MATH_SGN16` (21), `MATH_MULTIPLY16` (11) (§5).
4. **The `shrink-z80` skill had not been run on Leap-C before this checkpoint.** Phase 1's size work was done by hand under the plan's protocol (M1.2 −309 B; M1.3 −429 B, of which 210 B by shrinking and 219 B by moving constant folding to the EXROM), with the project's jump-relaxation tool and the `audit-z80` pattern scan. The retained platform had never been reviewed for size in Leap-C (§6).
5. **The mechanical micro level is nearly exhausted.** Only 2 relaxable jumps and no convertible tail call remain in HOME. The scan did find 10 inline copies of the `RST $08` (`LDI`) body in the compiler, 30 B. **Safe mechanical candidates total 78 B** (§6.4, S1-S7). The 4 open M1.2 restructuring candidates add about 90 B (M1).
6. **Larger savings need an owner decision** (§6.4, O1-O4): trim the retained math to what C uses (113 B, plus 62 B if `rand()` replaces `MATH_RND16`), give RST `$30` to the compiler's `LEX_NEXT` (92 B now, more in Phase 2), and a linear ASCII font for Phase 5 (106 B against the Phase 5 plan, 178 B if block graphics and UDGs go).
7. **Phase 2 readiness.** The statements component has 685 B left after the 269 B lent to M1.3 (L8), against an estimated 650-700 B of Phase 2 statement code. The safe candidates (78 B, plus about 90 B from M1) cannot repay the whole 269 B. With O1 they can (§8).
8. **Forecast for Phases 2-8 (§7).** The mid estimate fits the current allocation with 134 B to spare. The high estimate is 436 B over: Phase 3's library carries most of that risk, with Phase 2's preprocessor and `SWITCH` helper behind it. Policy B (a 256 B release minimum) does not cover the high case alone. The recovery list does.
9. **Reserve recommendation: keep policy A (512 B) now** (§9). Decide on B at the Phase 8 owner decision point, with the library measured.


## 2. HOME image: address map and reconciliation

### 2.1 Address map

| Range | Bytes | Contents | Component |
|---|---:|---|---|
| `$0000-$0067` | 104 | Reset, RST `$08-$30` helper bodies, IM 1 vector, cold start, NMI (74 B of code, 30 B of padding) | page0 |
| `$0068-$0EB5` | 3,662 | Retained V2 platform: memory 485, keyboard 434, graphics 2,071, 16-bit math 390, interrupt 154, bank switching 46, AY beep (HOME pieces) 82 | platform |
| `$0EB6-$12F7` | 1,090 | Lexer, keyword table, `CC_ERROR` exits | lexer |
| `$12F8-$141E` | 295 | Scoped symbol table, workspace allocator | symtab |
| `$141F-$1FB3` | 2,965 | Compile entry, declarations, types, initialisers, static data | decl |
| `$1FB4-$2A04` | 2,641 | Typed expressions | expr |
| `$2A05-$2F40` | 1,340 | Code generator and code templates | codegen |
| `$2F41-$2F4B` | 11 | `CX_FOLD`, the EXROM trampoline for constant folding | page0 |
| `$2F4C-$3109` | 446 | Function definitions, blocks, `return`, end-of-compile checks, `CC_PROGRAM` | stmt |
| `$310A-$3174` | 107 | Runtime helper core (the rest of `ENTER`, `CMPLT`; `MUL`, `DIV*`, `MOD*`, shifts, `CPL`, `CALLHL`) | helpers |
| `$3175-$31C2` | 78 | `RT_RUN`, runtime error exits | rtexit |
| `$31C3-$3FFF` | 3,645 | free, all `$FF` | — |

`LEAPC_HOME_CODE_END` = `$31C3`. The test image appends its hooks there; `make check` verifies that it is byte-identical to production up to that address.

### 2.2 Page zero

| Address | Bytes | Item | Padding after it |
|---|---:|---|---:|
| `$0000` | 4 | `di` / `jp COLD_START` | — |
| `$0004` | 3 | `IO_KEY_SCAN_ROW` (`in a,(PORT_ULA)` / `ret`, as in V2 production) | 1 |
| `$0008` | 5 | RST `LDI`, body in the slot | 3 |
| `$0010` | 6 | RST `STI`, body in the slot | 2 |
| `$0018` | 6 | RST `ENTER`, continues in `RT_ENTER` | 2 |
| `$0020` | 5 | RST `LEAVE`, body in the slot | 3 |
| `$0028` | 8 | RST `CMPLT`, continues in `RT_CMPLT_SAME` | — |
| `$0030` | 2 | RST `$30` unassigned: `di` / `halt` (reserved for the optional `LDL`/`STL`) | 6 |
| `$0038` | 6 | IM 1: `call KBD_ISR_TICK` / `ei` / `reti` | — |
| `$003E` | 27 | `COLD_START` | 13 |
| `$0066` | 2 | NMI: `retn` | — |
| `$2F41` | 11 | `CX_FOLD` trampoline (counted in page0, outside page zero) | — |

**Padding: 30 B** in seven runs of 1, 3, 2, 2, 3, 6 and 13 B, assembled as `$00` by the `ORG`s. Page0 is measured as its address range, so the padding counts against its 160 B budget (115 B used).

### 2.3 Reconciliation

| Check | Result |
|---|---|
| Image size | 16,384 B |
| Code end (`LEAPC_HOME_CODE_END`) | `$31C3`: 12,739 B used |
| Bytes by listing class | instructions 11,309 + DB/DW data 1,400 + `ORG` padding 30 + `DS` fill 0 = **12,739** |
| Bytes after the code end | 3,645, **all `$FF`** (the `DS` fill) |
| Sum of routine sizes per component | page0 115, platform 3,662, lexer 1,090, symtab 295, decl 2,965, expr 2,641, codegen 1,340, stmt 446, helpers 107, rtexit 78 = **12,739**, equal to `tools/budget.py` |
| Bytes outside every component | 0 |
| Constants | `EQU`s only: they occupy no ROM. Every literal in code is an operand byte, counted with its instruction |

**Data (1,400 B).** 32 tables (1,382 B) and 18 one-byte `DB $21` skip opcodes in the chained error exits (`CC_E_*`, `RT_ERR_STACK`):

| Table | Bytes | Component | Use |
|---|---:|---|---|
| `FONT_TABLE` | 688 | platform | 86 glyphs: space, digits, both cases, 23 punctuation characters |
| `LEX_KW_TABLE` + `LEX_KW_INDEX` | 166 + 24 | lexer | 32 C keywords: a first-letter index and length-prefixed suffixes |
| `KEY_ASCII_TABLE`, `_UPPER`, `_SYMBOL` | 3 × 40 | platform | keyboard maps (Phase 5 edits the symbol map in place) |
| `ROW_BASE_TABLE` | 48 | platform | screen row addresses |
| `PUNCT_CHAR_TABLE` | 46 | platform | character → glyph index for punctuation, 23 pairs |
| `CX_PREC_TABLE` | 36 | expr | operator precedences |
| `DS_TABLE` | 32 | decl | type specifier keywords |
| `CG_HTAB` | 26 | codegen | runtime helper addresses per operator |
| `LEX_PUNCT_CHARS`, `LEX_ESC_TABLE`, `LEX_DOUBLE_TABLE`, `LEX_EOF_BYTE` | 25 + 23 + 13 + 1 | lexer | punctuators, escapes, doubled punctuators |
| `AY_BEEP_TABLE` | 24 | platform | semitone periods |
| `IMG_TABLE` | 22 | decl | image regions |
| `TPL_*` (11 templates), `CG_CMPTAB` | 62 + 6 | codegen | code templates copied into the image |
| `ROW_TABLE`, `BIT_MASK_TABLE` | 8 + 8 | platform | keyboard rows, pixel masks |
| `CC_MAIN_NAME` | 4 | stmt | `"main"` |

The only string data in HOME is the keyword table and `"main"`. All compiler messages are deferred to the EXROM diagnostics (Phase 6).


## 3. Physical space, allocations and reserve

| | HOME | EXROM |
|---|---:|---:|
| Bank size | 16,384 | 8,192 |
| Used (production code and data) | 12,739 | 4,107 |
| **Physical free** | **3,645** | **4,085** |
| Allocated to components (base budgets + ledger) | 15,872 | 7,858 |
| of which unused (component budget not yet filled) | 3,133 | 3,751 |
| **Unallocated reserve** | **512** | **334** |
| Reserve floor | 512 | 256 |
| Reserve above the floor | **0** | 78 |

Physical free = unused budgets + reserve: 3,133 + 512 = 3,645 B (HOME), 3,751 + 334 = 4,085 B (EXROM). A byte saved by shrinking becomes free physically at once. It reaches the reserve only when a ledger entry returns it, as L2 and L4 did.

### 3.1 Components against their allocations (HOME)

| Component | Base | Ledger | Budget | Used | Left | Code / data | Routines | Phase that fills the rest |
|---|---:|---:|---:|---:|---:|---|---:|---|
| page0 | 160 | | 160 | 115 | 45 | 85 / 0 + 30 padding | 19 | 3, 7: EXROM trampolines |
| platform | 3,800 | | 3,800 | 3,662 | 138 | 2,720 / 942 | 85 | 3: ISR BREAK delta; 5: glyphs, key map |
| tape_block | 340 | | 340 | 0 | 340 | — | — | 7: block I/O moved from EXROM |
| lexer | 1,100 | | 1,100 | 1,090 | 10 | 838 / 252 | 23 | (2: preprocessor hooks, paid by preproc) |
| decl | 2,000 | +1,000 L3 | 3,000 | 2,965 | 35 | 2,894 / 71 | 82 | — |
| symtab | 800 | −400 L2 | 400 | 295 | 105 | 295 / 0 | 16 | 2: label lookup |
| expr | 1,800 | +841 L6 | 2,641 | 2,641 | 0 | 2,605 / 36 | 38 | — |
| codegen | 1,200 | +140 L7 | 1,340 | 1,340 | 0 | 1,246 / 94 | 57 | — |
| stmt | 1,400 | −269 L8 | 1,131 | 446 | 685 | 442 / 4 | 8 | 2: statements |
| preproc | 300 | | 300 | 0 | 300 | — | — | 2 |
| helpers | 500 | −340 L4 | 160 | 107 | 53 | 107 / 0 | 13 | 2: `SWITCH` |
| library | 1,300 | | 1,300 | 0 | 1,300 | — | — | 3, 7, 8 |
| rtexit | 200 | | 200 | 78 | 122 | 77 / 1 | 4 | 3: start/exit, BREAK |
| **Total** | **14,900** | **+972** | **15,872** | **12,739** | **3,133** | 11,309 / 1,400 + 30 | 345 | |


## 4. Budget ledger

| Id | Milestone | Bank | Component | Δ budget | Reserve after | Effect |
|---|---|---|---|---:|---:|---|
| — | spec | HOME | — | — | 1,484 | `spec.md` §2.2 baseline |
| — | spec | EXROM | — | — | 887 | `spec.md` §2.2 baseline |
| L1 | M1.1 | EXROM | xtape_block | +331 | EXROM 556 | Tape block I/O stays in the EXROM until Phase 7 moves it to HOME (`tape_block` 340). **Transitional:** Phase 7 removes it |
| L2 | M1.2 | HOME | symtab | −400 | (with L3) | Symbol table measured 295 B; 105 B kept for Phase 2 labels |
| L3 | M1.2 | HOME | decl | +1,000 | HOME 884 | Declarations 2,949 B after shrinking (initialisers, static data, parser support had no `spec.md` line) |
| L4 | M1.3 | HOME | helpers | −340 | (with L6-L8) | Helper core measured 107 B; 160 B kept for `SWITCH` (53 B left) |
| L5 | M1.3 | EXROM | xcomp | +222 | EXROM 334 | Constant folding moved to the EXROM (shrink protocol step 2) |
| L6 | M1.3 | HOME | expr | +841 | (with L4, L7, L8) | Expressions 2,641 B after shrinking |
| L7 | M1.3 | HOME | codegen | +140 | (with L4, L6, L8) | Code generator 1,340 B after shrinking and L5 |
| L8 | M1.3 | HOME | stmt | −269 | HOME **512** | **PROVISIONAL** (owner decision 2026-10-13): Phase 2 statement budget lent to M1.3. Not a saving. Still identified as provisional in `budget.toml` |

HOME: 1,484 + 400 − 1,000 + 340 − 841 − 140 + 269 = **512 B**. EXROM: 887 − 331 − 222 = **334 B**.

**Net effect of the ledger on HOME:** +972 B allocated (decl, expr and codegen +1,981; symtab and helpers −740; stmt −269). L8 is the only provisional entry. L1 is the only transitional one: when Phase 7 moves the block I/O, it frees 331 B of EXROM and fills HOME's `tape_block` budget.


## 5. Retained V2 platform: what is used

The platform is vendored from V2 tag `v2.0.1-emu.1` with two deltas, D1 and D2 (`platform/UPSTREAM.md`). "Used" means reachable through the cross-reference from page zero (cold start, RST vectors, IM 1), from the production entries `CC_PROGRAM` and `RT_RUN`, or from an EXROM routine. Indirect references through `CG_HTAB` and `EQU` aliases count. The skill's `production_reachability.py` agrees (§6.3). It takes a stricter view of the EXROM: since the shell stub does not call the editor engine or the AY beep yet, it also lists `MEM_SHIFT_UP/DOWN`, `MEM_LINE_DELETE_RANGE`, `GFX_ATTR_SWAP`, `GFX_INVERT_ATTR` and the AY beep pieces as unreached.

| Status | Bytes | Routines |
|---|---:|---|
| **Used now: compiler, runtime, cold start, ISR** | 834 | `MEM_COLD_INIT`, `MEM_INIT`, `MEM_FILL(_ZERO)`; the keyboard scan and decode with its tables (`IO_KEY_SCAN_ALL`, `IO_FIND_KEY`, `IO_KEY_STILL_DOWN`, `IO_DECODE_KEY`, `ROW_TABLE`, `KEY_ASCII_TABLE*`); `MATH_UMUL16`, `MATH_UDIV16`, `MATH_DIVIDE16`, `MATH_MOD16`, `MATH_SIGN_PREP`, `MATH_APPLY_SIGN`, `MATH_ABS16`, `MATH_NEGATE16`; `KBD_ISR_INIT`, `KBD_ISR_TICK`; `BANK_PAGE_EXROM_IN/OUT` |
| **Used now only through the EXROM** (shell stub, editor engine, AY beep) | 572 | `IO_READ_KEY`, `IO_LATCH_AND_CLEAR`, `GFX_CLS`, `GFX_PAINT_ATTR`, `GFX_SPRITE_INVALIDATE`, `GFX_ROW_BASE_ADDR`, `GFX_SET_BORDER`, the character renderer (`GFX_CHAR_TO_FONT_OFFSET`, `GFX_CHAR_SETUP`, `GFX_PUTCHAR`, `GFX_PRINT_STRING`), `GFX_ATTR_SWAP`, `GFX_INVERT_ATTR`, `GFX_CELL_ATTR_ADDR`, `MEM_SHIFT_UP/DOWN`, `MEM_LINE_DELETE_RANGE`, `AY_BEEP_PERIOD`, `AY_WAIT_FRAMES`, `AY_BEEP_TABLE` |
| Font and its tables (used through the renderer) | 782 | `FONT_TABLE` 688, `PUNCT_CHAR_TABLE` 46, `ROW_BASE_TABLE` 48 |
| **Needed by the Phase 5 shell** (V2's shell called them) | 425 | the line store: `MEM_LINE_STORE` 158, `MEM_LINE_INSERT` 57, `MEM_LINE_FIRST` 20, `MEM_LINE_NEXT` 25 and their helpers (`MEM_FITS_CHECK`, `MEM_BLOCK_LEN_TO_END`, `MEM_READ_STORE_NEW_LEN`, `MEM_COPY_NEW_STMT`) 54; `GFX_PUTCHAR_BOLD` 18 (keyword highlighting); `GFX_CLEAR_ROW` 23 and `GFX_CLEAR_ROW_TEXT` 16 (status rows); `GFX_SET_MODE` 54 (display reset; also `mode()`) |
| **Needed by the Phase 3 library** (`spec.md` §7) | 936 | text output scrolling (`GFX_SCROLL_OUTPUT_UP`, `GFX_SCROLL_TEXT_UP`, `GFX_COPY_ROW_BITMAP`) 108; `GFX_PRINT_STRING_ATTR` 64; `GFX_PUTCHAR_OVER` 16 (`over`); `GFX_SET_ATTR`, `GFX_SET_ATTR_EXT` 41 (colours, `attr`); `plot`/`draw`/`point` (`GFX_PIXEL_ADDR_SETUP`, `GFX_WRITE_PIXEL`, `GFX_READ_PIXEL`, `GFX_LINE`, `GFX_PLOT_CLIPPED`, `BIT_MASK_TABLE`, `MATH_COMPARE16`) 411; `sprite_get`/`sprite_put` (`GFX_CELL_BITMAP_ADDR`, `GFX_SPRITE_*`) 202; `IO_READ_KEY_NONBLOCK` 7 (`inkey`); `MATH_RND16` 87 (`rand`; see O2) |
| **No caller planned in Release 1** | **113** | `MATH_SQRT16` 81, `MATH_SGN16` 21 (BASIC's `SQR` and `SGN`; `spec.md` §7 has neither), `MATH_MULTIPLY16` 11 (`RT_MUL` calls `MATH_UMUL16` directly: the low 16 bits of a product do not depend on sign; V2's shell used it only for the array store) |

Total: 834 + 572 + 782 + 425 + 936 + 113 = **3,662 B** (the 3,662 B are the 85 platform items of Appendix A).

**Partly needed code inside used routines.** `GFX_CHAR_TO_FONT_OFFSET` (158 B) also generates block-graphics glyphs (codes 128-143, 48 B) and maps UDGs (codes 144-164, 15 B, to `UDG_TABLE` at `$F180`). `spec.md` §7 has no character set above 127. These paths are reachable only if a program prints such codes. Keeping or dropping them is part of O4.

**Discrepancy with `spec.md` §2.1.** The table lists `FOLD_UPPER` (9 B, "moved into the platform"). It is not in the build: Leap-C is case-sensitive and nothing calls it. The actual cost is 0 B. The spec text can be corrected when §2.1 is next amended.


## 6. Z80 shrinking audit

### 6.1 What has been used so far

| Tool or method | Used? | Where |
|---|---|---|
| z80-skills `shrink-z80` skill (its scanners and method) | **No, until this checkpoint** | Not cited in any milestone report. The plan (§1.2) names "the z80-skills shrink/optimize methods" as an example only |
| Manual shrink passes under the plan's protocol (§1.2 step 1) | Yes | M1.2 (declarations 3,258 → 2,949 B), M1.3 (expressions + code generator 4,410 → 3,981 B, including the 219 B moved to the EXROM) |
| Cold code to the EXROM (§1.2 step 2) | Yes | M1.3: constant folding (219 B + 3 B entry, L5) |
| `tools/relax_jumps.py` (project tool, jump relaxation) | Yes | M1.2 (8 jumps); now at a fixed point except 2 jumps in codegen (S3) |
| `tools/routine_sizes.py` (per-routine sizes) | Yes | M1.2, M1.3 |
| `audit-z80` pattern scan (`make audit`) | Yes, for correctness hints | M1.1-M1.3 §audit |
| `optimize-z80` (speed) | No | Speed was measured against the spike, not optimised |

### 6.2 Optimisation status by component

| Component | Size work done | Remaining evidence (this checkpoint) |
|---|---|---|
| lexer (1,090) | Written to its budget in M1.1 (13 B left then), no recorded shrink pass. Jumps at a fixed point | Keyword table already indexed by first letter with length-prefixed suffixes. No candidate found |
| decl / types / init (2,965) | M1.2 pass, −309 B; four restructuring candidates left open (M1) | S1 (6 `LDI` copies), S2 (dead entry) |
| symtab (295) | Compact from the start (295 B against 800) | S1b, S6 |
| expr (2,641) | M1.3 pass (with codegen: −210 B by shrinking) | S4, S5 |
| codegen (1,340) | M1.3 pass (with expr: −210 B); constant folding moved to the EXROM (−219 B) | S1 (3 copies), S3, S4 |
| stmt (446) | Built in M1.2/M1.3, not shrunk separately | S1 (1 copy) |
| helpers, page0, rtexit (300) | Sized at design: bodies in the RST slots, the core measured at 60 B against the spike's 92 B | S6, S7 (padding reuse) |
| **Retained platform (3,662)** | **Not reviewed in Leap-C.** Vendored unchanged; no relaxable jump left in it (consistent with V2's earlier passes) | Reviewed here for use (§5) and for evidence-led candidates (O1, O2, O4); a full micro pass was not done (§6.5) |

### 6.3 The scan run at this checkpoint

| Scanner | Input | Result |
|---|---|---|
| `tools/rom_inventory.py` (new) | production listings | Inventory, cross-reference, reachability (§2, §5, Appendix A) |
| `production_reachability.py` | both production listings, roots: page zero, `CC_PROGRAM`, `RT_RUN`, the EXROM entries | The unreferenced platform set of §5, plus the routines reached only through the not-yet-called EXROM editor, minus `GFX_CELL_BITMAP_ADDR` (13 B), which it does not list |
| `deadcode_scan.py` | `src/` | One true positive: `CC_E_UNDECL` (S2). The rest are tables, component markers and vectors reached by address |
| `z80_pattern_scan.py` | `src/`, `platform/kernel/` | `LDI` body repeated 11× (S1); repeated tails (S4); a repeated call triple (S5); 46 calls of `LEX_NEXT` and 36 of `TY_CLASS` (RST candidates, O3); platform: shared prologue/epilogue of the three `GFX_PUTCHAR` variants, an unrolled block-graphics writer (§6.5) |
| `literal_dup_scan.py` | `src/` | No duplicate literals; three short run-length candidates (`CX_PREC_TABLE`'s 14 zeros, the keyword index) below decoder cost |
| Byte scan of the image (call/ret pairs, `jp` in `jr` range) | `leapc_home.bin` | 1 `call`/`ret` pair, which must stay (`SCOPE_CLOSE` pops its caller's frame); 3 `jp`s in range, one of them at `$0000` (no gain: page zero is fixed) |
| `artifact_freshness.py` | `build/` | Did not recognise the sjasmplus sources (`NO_SOURCES`). Freshness was established by rebuilding from the clean tree and matching M1.3's recorded hashes |

### 6.4 Candidates, prioritised

**Safe, mechanical (no owner decision; behaviour identical; the corpus re-run proves it).**

| Id | Change | Bytes | Evidence | Speed | Risk |
|---|---|---:|---|---|---|
| S1 | Replace the 10 inline copies of `ld a,(hl) / inc hl / ld h,(hl) / ld l,a` with `rst $08` (the same instructions, plus `ret`, at the `LDI` vector): `TY_EQUAL`, `DATA_ALLOC`, `INIT_LIST` ×4, `CG_UNIT` ×2, `CG_BINOP`, `CC_FINISH` | **30** (decl 18, codegen 9, stmt 3) | EXACTO | +21 T per execution; `CG_UNIT` runs once per emitted unit: < 0.5% of compile time [E] | Low. Registers and flags identical; 2 B of stack. If Phase 2 counts RST frequencies by breakpoint, count only during `RT_RUN` |
| S1b | The same in `SYM_FIND`'s chain walk | 3 (symtab) | EXACTO | +21 T per symbol passed over, about 1% of compile time [E] | Low; optional, as it sits in the hottest compiler loop |
| S2 | Remove the dead error entry `CC_E_UNDECL`: nothing references it, and `E_UNDECL` is raised through `CC_ERROR_AT` in `CX_PRIMARY` | **3** (decl) | EXACTO | none | None |
| S3 | `jp .room` (`CG_UNIT`) and `jp CG_SETCOND` (`CG_BINOP`) → `jr` | **2** (codegen) | EXACTO | +2 T each | None |
| S4 | Shared tails: the two `ld a,OK_RVAL / ld (X_KIND),a / ret` in codegen → `jp CX_SET_RVAL`; the two `ld hl,TY_INT / ld (X_TYPE),hl / ret` in expr → one copy | **10** (codegen 6, expr 4) | EXACTO | +10 T on those paths | None |
| S5 | `call LEX_NEXT / call CX_ASSIGN / call CX_RVAL` occurs 4× in expr → one 9-byte helper | **15** (expr) | ESTIMADO: check that `CX_ASSIGN` and `CX_RVAL` leave nothing under their return address (cf. `CX_PUSHX`) | +27 T per use | Low |
| S6 | One `jp (hl)` for `CALL_HL` (symtab) and `RT_CALLHL` (helpers): label the `jp (hl)` that ends `RT_ENTER` | **2** | EXACTO | none | None |
| S7 | Page-zero padding reuse: `RT_CPL` (7) + `RT_MUL` (5) in the 13 B before the NMI vector; `RT_DIVS` (4) at `$0033` (`$0030-$0032` stay available for a future `jp` at RST `$30`). Nothing falls through into these gaps | **16** (helpers) | EXACTO | none | Low. The `di/halt` trap at `$30` resumes into `$0032` only after an NMI, which the TS2068 does not wire; that is no worse than today's padding |
| | **Subtotal** | **78** (+3 with S1b) | | | |

**Safe, restructuring.**

| Id | Change | Bytes | Evidence | Risk |
|---|---|---:|---|---|
| M1 | The four candidates M1.2 left open: a shared `struct`/`enum` tag lookup (≈40), table-driven specifier combinations (≈15), `TY_EQUAL` restructuring (≈20), an operator-class nibble in `CX_PREC_TABLE` to shorten `CX_BINOP`'s dispatch (≈15) | **≈90** (decl, expr) | ESTIMADO (M1.2 §3.2) | Medium: parser restructuring, covered by 191 declaration, 230 expression and 47 golden cases. Speed neutral |

**Owner-level (larger; each changes a spec statement or reserved resource).**

| Id | Change | Bytes | Evidence | Speed | Risk / what it gives up |
|---|---|---:|---|---|---|
| O1 | Drop `MATH_SQRT16`, `MATH_SGN16`, `MATH_MULTIPLY16` from the vendored platform (delta D3) | **113** (platform) | EXACTO: unreferenced, no Release 1 caller (§5) | none | Low. Amends `spec.md` §2.1 ("16-bit math kept unchanged") |
| O2 | `rand()`/`srand()` as a 16-bit xorshift in the library (≈25 B) instead of `MATH_RND16` (87 B), which is BASIC's `RND(n)`: a one-bit LFSR step followed by a `MOD` | **≈62** net (platform −87, library +25) | ESTIMADO | `rand()` ≈ 100 T instead of ≈ 4 kT (the `MOD16` call) | Low; better sequence quality (each LFSR value is the previous one shifted by one bit). Amends `spec.md` §2.1. Phase 3 writes `rand` anyway |
| O3 | RST `$30` → `jp LEX_NEXT`; the compiler's 46 `call LEX_NEXT` become `rst $30` | **92** now (46 call sites × 2 B: decl 50, expr 36, stmt 6; the `jp` fits in the slot's padding), plus 2 B per Phase 2 call site | EXACTO for the current image | +4 T per token (negligible) | Gives up the vector `spec.md` §2.3/§5.6 reserve for the optional size templates (`LDL`/`STL`, Phase 8, built only if capacity needs them). Phase 2 must confirm or retune the RST map anyway |
| O4 | Phase 5 font as a linear ASCII font (codes 32-126, 760 B) with a direct index (≈35 B), replacing the compare chain, the 23-entry punctuation search and `PUNCT_CHAR_TABLE` | **26** now; **106** against the Phase 5 plan (8 glyphs + 8 table entries ≈ 80 B); **178** if block graphics and UDGs (63 B) are dropped too | ESTIMADO | Faster for every character (no compare chain, no table search) | Medium: platform delta in `graphics.asm` (Phase 5 changes the font anyway); every glyph re-verified by the screen reader. Owner: keep or drop codes 128-164 |

**Totals.** Safe: 78 B mechanical + ≈ 90 B (M1) ≈ **168 B**. Owner-level: O1 + O2 ≈ 175 B, O3 92 B, O4 26 B now (106 B against the Phase 5 plan). **Overlaps:** S5 and O3 share 4 `call LEX_NEXT` sites (together 101 B, not 107); M1's `TY_EQUAL` rework would absorb S1's `TY_EQUAL` site (3 B). Everything else touches different bytes. Net: safe + O1-O3 ≈ **426 B** now.

### 6.5 Considered and not recommended

| Idea | Why not |
|---|---|
| Compute screen row addresses instead of `ROW_BASE_TABLE` (48 B) | About 38 B saved, but slower for every character and pixel row; output speed matters to compiled programs |
| Merge the three `GFX_PUTCHAR` variants (shared prologue and loop tail) | 10-20 B [E], but a mode test inside the per-row loop slows all text output; reconsider only with the O4 font work |
| Loop the unrolled block-graphics writer | 8-10 B [E]; moot if O4 drops block graphics |
| Move more compiler code to the EXROM | The type checks raise compile errors, which unwind with the EXROM paged in (bank rule 3), and the EXROM reserve is 78 B above its floor. Revisit only if the Phase 8 FP decision frees the calculator's 2,165 B |
| A further RST for `TY_CLASS` (36 calls) | No vector left: `$00` reset, `$08-$28` runtime helpers, `$38` IM 1 |
| A helper for `ld e,(hl) / inc hl / ld d,(hl) / inc hl` (5 sites) | Net 0 B after the helper's own bytes |
| Pack the keyword table harder (5-bit) | Decoder cost exceeds the saving on 166 B |
| More jump relaxation or tail calls | At a fixed point: only S3's two jumps remain |

### 6.6 Platform review status

The platform has now been checked for use (reachability, §5) and scanned for evidence-led candidates (O1, O2, O4, §6.5). **No full micro pass of the 3,662 B was done.** The scanners found no relaxable jumps and only small repeated tails. Every change there costs a recorded delta and a `tools/check_platform.py` update, so a full pass is worth it only together with the planned Phase 3 (ISR) and Phase 5 (font, key map) deltas.


## 7. Remaining ROM obligations, Phases 2-8 (forecast)

| Phase | Obligation | Component (left now) | Estimate [E] | Basis |
|---|---|---|---:|---|
| 2 | Statements and functions: `if`/`else`, `while`, `do`, `for`, `switch`, `break`/`continue`, `goto`/labels, local initialisers, `static` locals, function → line table | stmt (685) | 650-700 | M1.3 §11 |
| 2 | Label lookup for `goto` | symtab (105) | 30-60 | Reuses `SYM_FIND`/`SYM_MAKE` |
| 2 | `SWITCH` helper | helpers (53) | 50-100 | Feasibility study §2.2 |
| 2 | Preprocessor (`#define`, `#undef`, `#include <leap.h>`, refusals) and its lexer hooks | preproc (300) | 200-400 | Feasibility study §3; M1.1 §11 |
| 3 | Library, `spec.md` §7 without tape: text and `printf`, keyboard and `gets`, graphics and sprites, sound, time and random, port I/O, `str*`/`mem*`, `atoi`/`itoa`/`abs`, `malloc`/`free` | library (1,300) | 930-1,550 | Feasibility study §2.2 (`str*`/`mem*` 150-250, `printf` 250-400, line input 100-200, bindings 200-400) + conversions and heap |
| 3 | Start/exit normalisation, BREAK exit, runtime-error line mapping | rtexit (122) | 30-120 | Feasibility study: 100-200 for the whole; 78 built |
| 3 | ISR BREAK delta | platform (138, shared) | 20-40 | `spec.md` §5.8 |
| 3 | EXROM trampolines (AY beep, formatting) | page0 (45) | 22-44 | `CX_FOLD` = 11 B measured |
| 5 | 8 glyphs, key map entries | platform (shared) | 80-90 | `spec.md` §6.2 |
| 7 | Tape block I/O moved to HOME | tape_block (340) | 331-340 | Measured 331 (L1) |
| 7 | `tape_save`/`tape_load` bindings, header trampolines | library, page0 | 40-80 | — |
| 8 | Remaining library items, polish | within budgets | — | `project_plan.md` §10 |
| 8 | Optional: size templates (`LDL`/`STL` at RST `$30`), peephole stage | only if measured to pay | — | `project_plan.md` §10 |

| | Low | Mid | High |
|---|---:|---:|---:|
| Estimated need, Phases 2-8 | 2,383 | 2,954 | 3,524 |
| Budget left in those components | 3,088 | 3,088 | 3,088 |
| **Margin, policy A (512 B floor)** | **+705** | **+134** | **−436** |
| Margin, policy B (256 B more at release) | +961 | +390 | −180 |

The decl (35 B) and lexer (10 B) leftovers are not counted. In the high case the overruns sit in the library (≈ −330 B with the tape bindings), the preprocessor (−100), `SWITCH` (−47) and statements (−15). Symtab (+45) and platform (+8) are under. A component's surplus helps another only through a ledger reallocation.

**EXROM obligations, for completeness.** Shell 2,848 B left (Phase 5), keywords 250 B, diagnostics 650 B (Phase 6), with 334 B of reserve (78 B above the floor). Phase 7 frees 331 B (L1). The Phase 8 FP decision decides the calculator's 2,165 B.


## 8. Phase 2 readiness

- **Statements: 685 B left** (1,400 − 269 L8 − 446 built), against an estimated **650-700 B**. Phase 2 can start, but the estimate straddles the remaining budget, and expressions and the code generator have 0 B left for any Phase 2 change there (for example, testing `&&`/`||` conditions directly in `if`). `SWITCH` has 53 B against 50-100 B [E].
- **Credible low-risk recovery before Phase 2:** S1-S7 give **78 B** (decl 21, codegen 17, expr 19, stmt 3, symtab 1, helpers 17), all mechanical and proven by the existing corpus. With M1, ≈ 168 B. **That does not repay the 269 B loan alone.** S + O1 gives 191 B; with M1 as well ≈ 278 B (net of the 3 B overlap), enough; with O2 too ≈ 340 B.
- **The candidates land where Phase 2 needs room.** S1 and S3-S5 free bytes in expr and codegen, the two components with nothing left, and S7 frees bytes in helpers, where `SWITCH` will go.
- **Bookkeeping:** a saving in decl, expr or codegen becomes free physically at once. To repay L8 it is returned by a ledger entry that lowers that component's budget, and L8 is reduced by the same amount. No budget or ledger entry is changed at this checkpoint.

**Recommended order (engineering):**

1. Phase 2's first step applies S1-S7 (one commit, the full corpus re-run).
2. Then measure the statement compiler against 685 B, as the owner decided for L8.
3. If it overruns, apply M1, then bring O1/O2 (or O3) to the owner before any reserve-floor question.


## 9. HOME reserve policy

| | A: 512 B minimum, always | B: 512 B development target, 256 B release minimum |
|---|---|---|
| Unallocated bytes above the floor today | 0 | 0 now; 256 B can be allocated at release with owner approval |
| Budget for Phases 2-8 | 3,088 B in components | 3,088 B + 256 B release contingency = 3,344 B |
| Forecast margin (low / mid / high) | +705 / +134 / −436 | +961 / +390 / −180 |
| Room for post-release fixes (Phase 9 hardware, maintenance) | 512 B | as little as 256 B |
| Covers the high case alone? | No | No (−180 B) |

**Recommendation: keep A now and take the B question to the Phase 8 owner decision point.**

- The mid forecast fits under A.
- The high case exceeds both policies. Only shrinking or an owner-level item closes it, and the recovery list (≈ 426 B) is larger than what B offers (256 B), without costing maintenance headroom.
- The open risk is Phase 3's library (930-1,550 B [E]). After Phase 3 it is a measurement, not an estimate.
- Phase 8 is already the owner's decision point for floating point, which also changes the bank picture.
- A thin reserve makes every maintenance change a shrink study: V2's v2.0.1 changes were fitted into its last 13-35 B of HOME, and the release ships with 19 B free (`~/2068-Leap` `docs/V2_AY_BEEP_STUDY.md`, `docs/V2_CLASSICBEEP_STUDY.md`).

If B is adopted at Phase 8, it should cover only a measured shortfall that remains after S, M1 and the owner-level items.


## 10. Decisions for the owner

None is needed to start Phase 2. These are the items that, by `spec.md` or the plan, need the owner:

| # | Decision | Effect | Recommended |
|---|---|---|---|
| 1 | **O1:** drop the three unused math routines (`spec.md` §2.1 amendment, platform delta D3) | 113 B HOME | Yes, when Phase 2 needs bytes |
| 2 | **O2:** `rand()`/`srand()` as a C xorshift, `MATH_RND16` dropped (`spec.md` §2.1 amendment) | ≈ 62 B HOME, `rand()` ≈ 40× faster | Yes, in Phase 3 |
| 3 | **O3:** RST `$30` for the compiler's `LEX_NEXT` instead of the optional size templates (`spec.md` §2.3, §5.6) | 92 B HOME now, more with Phase 2 | Only if O1/O2 and M1 are not enough; decide with Phase 2's RST frequency count |
| 4 | **O4:** keep or drop block graphics and UDGs (codes 128-164) when Phase 5 rebuilds the font | 63 B HOME (on top of the linear font's 106 B against the plan) | Decide in Phase 5 |
| 5 | **Reserve policy B** | 256 B at release | Not now; decide at Phase 8 (§9) |


## 11. Regenerating this inventory

```
make inventory                          # HOME: summary, padding, per-component routine list
python3 tools/rom_inventory.py --md     # Appendix A tables
python3 tools/rom_inventory.py --bank exrom
python3 tools/rom_inventory.py --json build/home_inventory.json
```

The tool reads `build/leapc_home.lst`, `.sym`, `.bin`, the EXROM listing and `budget.toml`. It writes only its report (and the `--json` file when asked). Roots for reachability: page zero, `CC_PROGRAM`, `RT_RUN`, and every EXROM operand that names a HOME export.


## Appendix A. Every HOME routine and table

Generated by `python3 tools/rom_inventory.py --md` from the production build at `5b062b3`. *Kind:* code, table (data only), code+data, padding. **Unreferenced** = not reachable from the roots of §11. *Code/data* = instruction bytes / DB-DW bytes. *Referenced by* lists the routines whose operands name it (first five), callers through the EXROM as `EXROM:name`, and fall-through from the routine before it. The roots of §11 (page zero, `CC_PROGRAM`, `RT_RUN`) show `—` without the mark.

#### `page0` — Page zero, cold start, trampolines: 115 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$0000` | 4 | `COMP_PAGE0_BEGIN` | code | 4/0 | — |
| `$0004` | 3 | `IO_KEY_SCAN_ROW` | code | 3/0 | `IO_KEY_SCAN_ALL` |
| `$0007` | 1 | `(padding)` | padding | 0/0 +1 gap | — |
| `$0008` | 5 | `RST_LDI` | code | 5/0 | — |
| `$000D` | 3 | `(padding)` | padding | 0/0 +3 gap | — |
| `$0010` | 6 | `RST_STI` | code | 6/0 | — |
| `$0016` | 2 | `(padding)` | padding | 0/0 +2 gap | — |
| `$0018` | 6 | `RST_ENTER` | code | 6/0 | — |
| `$001E` | 2 | `(padding)` | padding | 0/0 +2 gap | — |
| `$0020` | 5 | `RST_LEAVE` | code | 5/0 | — |
| `$0025` | 3 | `(padding)` | padding | 0/0 +3 gap | — |
| `$0028` | 8 | `RST_CMPLT` | code | 8/0 | — |
| `$0030` | 2 | `RST_UNASSIGNED` | code | 2/0 | — |
| `$0032` | 6 | `(padding)` | padding | 0/0 +6 gap | — |
| `$0038` | 6 | `(IM 1 vector)` | code | 6/0 | — |
| `$003E` | 27 | `COLD_START` | code | 27/0 | `COMP_PAGE0_BEGIN` |
| `$0059` | 13 | `(padding)` | padding | 0/0 +13 gap | — |
| `$0066` | 2 | `(NMI vector)` | code | 2/0 | — |
| `$2F41` | 11 | `CX_FOLD` (= `COMP_CODEGEN_END`, `COMP_TRAMP_BEGIN`) | code | 11/0 | `CX_BINOP`, `CX_UNARY` |

#### `platform` — Retained platform (graphics, memory, keyboard, math, interrupt, bank, AY) + deltas: 3662 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$0068` | 8 | `MEM_COLD_INIT` (= `COMP_PAGE0_END`, `COMP_PLATFORM_BEGIN`) | code | 8/0 | `COLD_START` |
| `$0070` | 41 | `MEM_INIT` | code | 41/0 | `COLD_START` |
| `$0099` | 1 | `MEM_FILL_ZERO` | code | 1/0 | `CC_COMPILE`, `DATA_ALLOC`, `MEM_COLD_INIT`, `MEM_INIT`, `TY_NEW` +1 |
| `$009A` | 11 | `MEM_FILL` | code | 11/0 | `MEM_FILL_ZERO` |
| `$00A5` | 11 | `MEM_SHIFT_UP` | code | 11/0 | `MEM_LINE_INSERT`, `MEM_LINE_STORE`, `EXROM:EDITOR_INSERT_CHAR` |
| `$00B0` | 12 | `MEM_SHIFT_DOWN` | code | 12/0 | `MEM_LINE_DELETE_RANGE`, `MEM_LINE_STORE`, `EXROM:EDITOR_DELETE_CHAR` |
| `$00BC` | 20 | `MEM_LINE_FIRST` | code, **unreferenced** | 20/0 | — |
| `$00D0` | 25 | `MEM_LINE_NEXT` | code, **unreferenced** | 25/0 | — |
| `$00E9` | 11 | `MEM_FITS_CHECK` | code, **unreferenced** | 11/0 | `MEM_LINE_INSERT`, `MEM_LINE_STORE` |
| `$00F4` | 11 | `MEM_BLOCK_LEN_TO_END` | code, **unreferenced** | 11/0 | `MEM_LINE_INSERT`, `MEM_LINE_STORE` |
| `$00FF` | 18 | `MEM_READ_STORE_NEW_LEN` | code, **unreferenced** | 18/0 | `MEM_LINE_INSERT`, `MEM_LINE_STORE` |
| `$0111` | 14 | `MEM_COPY_NEW_STMT` | code, **unreferenced** | 14/0 | `MEM_LINE_INSERT`, `MEM_LINE_STORE` |
| `$011F` | 158 | `MEM_LINE_STORE` | code, **unreferenced** | 158/0 | — |
| `$01BD` | 57 | `MEM_LINE_INSERT` | code, **unreferenced** | 57/0 | — |
| `$01F6` | 87 | `MEM_LINE_DELETE_RANGE` | code | 87/0 | `EXROM:EDITOR_BLOCK_DELETE` |
| `$024D` | 30 | `IO_KEY_SCAN_ALL` | code | 30/0 | `KBD_ISR_TICK` |
| `$026B` | 90 | `IO_FIND_KEY` | code | 90/0 | `KBD_ISR_TICK` |
| `$02C5` | 28 | `IO_KEY_STILL_DOWN` | code | 28/0 | `KBD_ISR_TICK` |
| `$02E1` | 133 | `IO_DECODE_KEY` | code | 133/0 | `KBD_ISR_TICK` |
| `$0366` | 10 | `IO_LATCH_AND_CLEAR` | code | 10/0 | `IO_READ_KEY`, `IO_READ_KEY_NONBLOCK` |
| `$0370` | 8 | `IO_READ_KEY` | code | 8/0 | `EXROM:EDITOR_LOOP`, `EXROM:SHELL_IDLE` |
| `$0378` | 7 | `IO_READ_KEY_NONBLOCK` | code, **unreferenced** | 7/0 | — |
| `$037F` | 8 | `ROW_TABLE` | table | 0/8 | `IO_KEY_SCAN_ALL` |
| `$0387` | 40 | `KEY_ASCII_TABLE` | table | 0/40 | `IO_DECODE_KEY` |
| `$03AF` | 40 | `KEY_ASCII_TABLE_UPPER` | table | 0/40 | `IO_DECODE_KEY` |
| `$03D7` | 40 | `KEY_ASCII_TABLE_SYMBOL` | table | 0/40 | `IO_DECODE_KEY` |
| `$03FF` | 18 | `GFX_CLS` | code | 18/0 | `EXROM:EDITOR_REDRAW_SCREEN`, `EXROM:SHELL_COLD` |
| `$0411` | 13 | `GFX_PAINT_ATTR` | code | 13/0 | `GFX_CLS` |
| `$041E` | 14 | `GFX_SPRITE_INVALIDATE` | code | 14/0 | `GFX_CLS`, `GFX_SCROLL_TEXT_UP`, `GFX_SET_MODE` |
| `$042C` | 13 | `GFX_ROW_BASE_ADDR` | code | 13/0 | `GFX_CELL_BITMAP_ADDR`, `GFX_CHAR_SETUP`, `GFX_COPY_ROW_BITMAP`, `GFX_PIXEL_ADDR_SETUP` |
| `$0439` | 36 | `GFX_COPY_ROW_BITMAP` | code, **unreferenced** | 36/0 | `GFX_SCROLL_OUTPUT_UP`, `GFX_SCROLL_TEXT_UP` |
| `$045D` | 40 | `GFX_SCROLL_TEXT_UP` | code, **unreferenced** | 40/0 | `GFX_SCROLL_OUTPUT_UP` |
| `$0485` | 32 | `GFX_SCROLL_OUTPUT_UP` | code, **unreferenced** | 32/0 | `GFX_PRINT_STRING_ATTR` |
| `$04A5` | 15 | `GFX_SET_BORDER` | code | 15/0 | `EXROM:SHELL_COLD` |
| `$04B4` | 158 | `GFX_CHAR_TO_FONT_OFFSET` | code | 158/0 | `GFX_CHAR_SETUP` |
| `$0552` | 39 | `GFX_CHAR_SETUP` | code | 39/0 | `GFX_PUTCHAR`, `GFX_PUTCHAR_BOLD`, `GFX_PUTCHAR_OVER` |
| `$0579` | 15 | `GFX_PUTCHAR` | code | 15/0 | `GFX_CLEAR_ROW`, `GFX_CLEAR_ROW_TEXT`, `GFX_PRINT_STRING`, `GFX_PRINT_STRING_ATTR` |
| `$0588` | 16 | `GFX_PUTCHAR_OVER` | code, **unreferenced** | 16/0 | `GFX_PRINT_STRING_ATTR` |
| `$0598` | 18 | `GFX_PUTCHAR_BOLD` | code, **unreferenced** | 18/0 | — |
| `$05AA` | 14 | `GFX_PRINT_STRING` | code | 14/0 | `EXROM:EDITOR_REDRAW_SCREEN`, `EXROM:SHELL_COLD` |
| `$05B8` | 64 | `GFX_PRINT_STRING_ATTR` | code, **unreferenced** | 64/0 | — |
| `$05F8` | 26 | `GFX_ATTR_SWAP` | code | 26/0 | `GFX_INVERT_ATTR` |
| `$0612` | 8 | `GFX_INVERT_ATTR` | code | 8/0 | `EXROM:EDITOR_LOOP`, `EXROM:EDITOR_REDRAW_SCREEN` |
| `$061A` | 11 | `GFX_SET_ATTR` | code, **unreferenced** | 11/0 | `GFX_CLEAR_ROW`, `GFX_PRINT_STRING_ATTR`, `GFX_WRITE_PIXEL` |
| `$0625` | 30 | `GFX_SET_ATTR_EXT` | code, **unreferenced** | 30/0 | `GFX_WRITE_PIXEL` |
| `$0643` | 54 | `GFX_SET_MODE` | code, **unreferenced** | 54/0 | — |
| `$0679` | 23 | `GFX_CLEAR_ROW` | code, **unreferenced** | 23/0 | `GFX_SCROLL_OUTPUT_UP` |
| `$0690` | 16 | `GFX_CLEAR_ROW_TEXT` | code, **unreferenced** | 16/0 | — |
| `$06A0` | 64 | `GFX_PIXEL_ADDR_SETUP` | code, **unreferenced** | 64/0 | `GFX_READ_PIXEL`, `GFX_WRITE_PIXEL` |
| `$06E0` | 66 | `GFX_WRITE_PIXEL` | code, **unreferenced** | 66/0 | `GFX_LINE`, `GFX_PLOT_CLIPPED` |
| `$0722` | 10 | `GFX_READ_PIXEL` | code, **unreferenced** | 10/0 | — |
| `$072C` | 206 | `GFX_LINE` | code, **unreferenced** | 206/0 | — |
| `$07FA` | 31 | `GFX_PLOT_CLIPPED` | code, **unreferenced** | 31/0 | — |
| `$0819` | 8 | `BIT_MASK_TABLE` | table, **unreferenced** | 0/8 | `GFX_PIXEL_ADDR_SETUP` |
| `$0821` | 46 | `PUNCT_CHAR_TABLE` | table | 0/46 | `GFX_CHAR_TO_FONT_OFFSET` |
| `$084F` | 48 | `ROW_BASE_TABLE` | table | 0/48 | `GFX_ROW_BASE_ADDR` |
| `$087F` | 688 | `FONT_TABLE` | table | 0/688 | `GFX_CHAR_SETUP`, `GFX_CHAR_TO_FONT_OFFSET` |
| `$0B2F` | 13 | `GFX_CELL_BITMAP_ADDR` | code, **unreferenced** | 13/0 | `GFX_SPRITE_TRANSFER` |
| `$0B3C` | 29 | `GFX_CELL_ATTR_ADDR` | code | 29/0 | `GFX_ATTR_SWAP`, `GFX_SET_ATTR`, `GFX_SPRITE_TRANSFER` |
| `$0B59` | 28 | `GFX_SPRITE_BOUNDS_CHECK` | code, **unreferenced** | 28/0 | `GFX_SPRITE_SETUP` |
| `$0B75` | 17 | `GFX_SPRITE_CELL_ROWCOL` | code, **unreferenced** | 17/0 | `GFX_SPRITE_TRANSFER` |
| `$0B86` | 28 | `GFX_SPRITE_SETUP` | code, **unreferenced** | 28/0 | `GFX_SPRITE_CAPTURE`, `GFX_SPRITE_DRAW` |
| `$0BA2` | 95 | `GFX_SPRITE_TRANSFER` | code, **unreferenced** | 95/0 | `GFX_SPRITE_CAPTURE`, `GFX_SPRITE_DRAW` |
| `$0C01` | 10 | `GFX_SPRITE_CAPTURE` | code, **unreferenced** | 10/0 | — |
| `$0C0B` | 11 | `GFX_SPRITE_DRAW` | code, **unreferenced** | 11/0 | — |
| `$0C16` | 22 | `MATH_UMUL16` | code | 22/0 | `CX_BINOP`, `MATH_MULTIPLY16`, `RT_MUL`, `TY_SIZE0`, `EXROM:XC_FOLD` |
| `$0C2C` | 74 | `MATH_UDIV16` | code | 74/0 | `MATH_DIVIDE16`, `MATH_MOD16`, `RT_DIVU`, `TY_ARRAY`, `EXROM:XC_FOLD` |
| `$0C76` | 16 | `MATH_SIGN_PREP` | code | 16/0 | `MATH_DIVIDE16`, `MATH_MULTIPLY16` |
| `$0C86` | 7 | `MATH_APPLY_SIGN` | code | 7/0 | `MATH_DIVIDE16`, `MATH_MOD16`, `MATH_MULTIPLY16` |
| `$0C8D` | 11 | `MATH_MULTIPLY16` | code, **unreferenced** | 11/0 | — |
| `$0C98` | 10 | `MATH_DIVIDE16` | code | 10/0 | `CX_BINOP`, `RT_DIVS`, `EXROM:XC_FOLD` |
| `$0CA2` | 26 | `MATH_COMPARE16` | code, **unreferenced** | 26/0 | `GFX_LINE` |
| `$0CBC` | 8 | `MATH_NEGATE16` | code | 8/0 | `CX_PRIMARY`, `CX_UNARY`, `GFX_LINE`, `MATH_ABS16`, `MATH_APPLY_SIGN` |
| `$0CC4` | 5 | `MATH_ABS16` | code | 5/0 | `MATH_MOD16`, `MATH_SIGN_PREP` |
| `$0CC9` | 21 | `MATH_SGN16` | code, **unreferenced** | 21/0 | — |
| `$0CDE` | 22 | `MATH_MOD16` | code | 22/0 | `MATH_RND16`, `RT_MODS`, `EXROM:XC_FOLD` |
| `$0CF4` | 81 | `MATH_SQRT16` | code, **unreferenced** | 81/0 | — |
| `$0D45` | 87 | `MATH_RND16` | code, **unreferenced** | 87/0 | — |
| `$0D9C` | 22 | `KBD_ISR_INIT` | code | 22/0 | `COLD_START` |
| `$0DB2` | 132 | `KBD_ISR_TICK` | code | 132/0 | `(IM 1 vector)` |
| `$0E36` | 28 | `BANK_PAGE_EXROM_IN` | code | 28/0 | `COLD_START`, `CX_FOLD`, `RT_RUN` |
| `$0E52` | 18 | `BANK_PAGE_EXROM_OUT` | code | 18/0 | `CX_FOLD`, `RT_RUN`, `EXROM:CALC_ABORT_STREAM`, `EXROM:CALC_OP_END_CALC` |
| `$0E64` | 24 | `AY_BEEP_TABLE` | table | 0/24 | `AY_BEEP_PERIOD` |
| `$0E7C` | 46 | `AY_BEEP_PERIOD` | code | 46/0 | `EXROM:AY_BEEP` |
| `$0EAA` | 12 | `AY_WAIT_FRAMES` | code | 12/0 | `EXROM:AY_BEEP_PLAY` |

#### `lexer` — Compiler: lexer + source streaming + keyword table (+ compile error exit): 1090 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$0EB6` | 24 | `LEX_INIT` (= `COMP_PLATFORM_END`, `COMP_LEXER_BEGIN`) | code | 24/0 | `CC_COMPILE` |
| `$0ECE` | 17 | `LEX_SEEK` | code | 17/0 | `LEX_INIT`, `LEX_NEWLINE` |
| `$0EDF` | 20 | `LEX_NEWLINE` | code | 20/0 | `LEX_NEXT` |
| `$0EF3` | 510 | `LEX_NEXT` | code | 510/0 | `CC_COMPILE`, `CC_EXPECT`, `CX_ASSIGN`, `CX_BINARY`, `CX_CALL` +24 |
| `$10F1` | 15 | `LEX_BEGIN` | code | 15/0 | `LEX_NEXT` |
| `$1100` | 9 | `LEX_MARK_LINE` | code | 9/0 | `LEX_BEGIN`, `LEX_NEXT` |
| `$1109` | 22 | `LEX_DIGIT` | code | 22/0 | `LEX_ACCUM`, `LEX_NEXT` |
| `$111F` | 44 | `LEX_ACCUM` | code | 44/0 | `LEX_CHAR`, `LEX_NEXT` |
| `$114B` | 54 | `LEX_CHAR` | code | 54/0 | `LEX_NEXT` |
| `$1181` | 5 | `LEX_E_ESCAPE` | code | 5/0 | `LEX_CHAR` |
| `$1186` | 5 | `LEX_E_BADCHAR` | code | 5/0 | `LEX_NEXT` |
| `$118B` | 5 | `LEX_E_STRING` | code | 5/0 | `LEX_NEXT` |
| `$1190` | 5 | `LEX_E_RANGE` | code | 5/0 | `LEX_NEXT` |
| `$1195` | 5 | `LEX_E_TOOLONG` | code | 5/0 | `LEX_NEXT` |
| `$119A` | 83 | `LEX_KEYWORD` | code | 83/0 | `LEX_NEXT` |
| `$11ED` | 1 | `LEX_EOF_BYTE` | table | 0/1 | `LEX_NEXT`, `LEX_SEEK` |
| `$11EE` | 25 | `LEX_PUNCT_CHARS` | table | 0/25 | `LEX_NEXT` |
| `$1207` | 13 | `LEX_DOUBLE_TABLE` | table | 0/13 | `LEX_NEXT` |
| `$1214` | 23 | `LEX_ESC_TABLE` | table | 0/23 | `LEX_CHAR` |
| `$122B` | 24 | `LEX_KW_INDEX` | table | 0/24 | `LEX_KEYWORD` |
| `$1243` | 166 | `LEX_KW_TABLE` | table | 0/166 | `LEX_KEYWORD` |
| `$12E9` | 3 | `CC_ERROR` (= `LEX_KW_TABLE_END`) | code | 3/0 | `CC_E_PARAMS`, `CC_E_TOOBIG`, `CC_STACKCHK`, `CX_CALL`, `CX_LVALUE` +10 |
| `$12EC` | 12 | `CC_ERROR_AT` | code | 12/0 | `CC_ERROR`, `CC_FINISH`, `CX_PRIMARY` |

#### `decl` — Compiler: declarations and type system: 2965 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$141F` | 56 | `CC_COMPILE` (= `COMP_SYMTAB_END`, `COMP_DECL_BEGIN`) | code | 56/0 | `CC_PROGRAM` |
| `$1457` | 22 | `IMG_TABLE` | table | 0/22 | `CC_COMPILE` |
| `$146D` | 10 | `CC_EXPECT` | code | 10/0 | `CX_CALL`, `CX_COND`, `CX_PAREN_REST`, `CX_POSTFIX_LOOP`, `CX_PRIMARY` +9 |
| `$1477` | 12 | `CC_STACKCHK` | code | 12/0 | `CX_CALL`, `CX_UNARY`, `DECLARATOR`, `INIT`, `STATEMENT` +2 |
| `$1483` | 6 | `NEXT_HL` | code | 6/0 | `DECLARATOR`, `ENUM_SPEC`, `MEMBERS` |
| `$1489` | 19 | `CELLS_SAVE` | code | 19/0 | `CX_CALL`, `DECL_SPECS`, `INIT_LIST`, `MEMBERS` |
| `$149C` | 6 | `CELLS_RETURN` | code | 6/0 | `CELLS_LOAD`, `CELLS_SAVE` |
| `$14A2` | 21 | `CELLS_LOAD` | code | 21/0 | `CX_CALL`, `DECL_SPECS`, `INIT_LIST`, `MEMBERS` |
| `$14B7` | 18 | `LEX_MARK` | code | 18/0 | `CX_CALL`, `DCL_STATIC`, `DECLARATOR` |
| `$14C9` | 20 | `LEX_RESTORE` | code | 20/0 | `CX_CALL`, `DCL_STATIC`, `DECLARATOR` |
| `$14DD` | 30 | `SKIP_GROUP` | code | 30/0 | `DECLARATOR`, `SKIP_SUFFIXES` |
| `$14FB` | 17 | `SKIP_SUFFIXES` | code | 17/0 | `DECLARATOR` |
| `$150C` | 28 | `IS_DECL_START` | code | 28/0 | `BLOCK_ITEMS`, `CX_PRIMARY`, `CX_UNARY`, `DCL_NESTED`, `DECL_SPECS` +2 |
| `$1528` | 16 | `DS_CODE` | code | 16/0 | `DECL_SPECS`, `IS_DECL_START` |
| `$1538` | 32 | `DS_TABLE` | table | 0/32 | `DS_CODE` |
| `$1558` | 201 | `DECL_SPECS` | code | 201/0 | `DECLARATION`, `MEMBERS`, `PARAMS`, `TYPE_NAME` |
| `$1621` | 85 | `STRUCT_SPEC` | code | 85/0 | `DECL_SPECS` |
| `$1676` | 166 | `MEMBERS` | code | 166/0 | `STRUCT_SPEC` |
| `$171C` | 8 | `ST_NODE` | code | 8/0 | `STRUCT_SPEC` |
| `$1724` | 155 | `ENUM_SPEC` | code | 155/0 | `DECL_SPECS` |
| `$17BF` | 123 | `DECLARATOR` | code | 123/0 | `DECLARATION`, `MEMBERS`, `PARAMS`, `TYPE_NAME` |
| `$183A` | 12 | `DCL_NESTED` | code | 12/0 | `DECLARATOR` |
| `$1846` | 18 | `SUFFIXES` | code | 18/0 | `DECLARATOR`, `SUFFIX_ARRAY`, `SUFFIX_FUNC` |
| `$1858` | 37 | `SUFFIX_FUNC` | code | 37/0 | `DECLARATOR`, `SUFFIXES` |
| `$187D` | 55 | `SUFFIX_ARRAY` | code | 55/0 | `SUFFIXES` |
| `$18B4` | 203 | `PARAMS` | code | 203/0 | `SUFFIX_FUNC` |
| `$197F` | 19 | `TYPE_NAME` | code | 19/0 | `CX_PRIMARY`, `CX_UNARY` |
| `$1992` | 80 | `DECLARATION` | code | 80/0 | `BLOCK_ITEMS`, `CC_COMPILE` |
| `$19E2` | 152 | `DECLARE` | code | 152/0 | `DECLARATION`, `FUNC_DEF` |
| `$1A7A` | 9 | `DCL_NOINIT` | code | 9/0 | `DECLARE` |
| `$1A83` | 10 | `DCL_LOCAL` | code | 10/0 | `DECLARE`, `PARAMS` |
| `$1A8D` | 5 | `IS_BLOCK` | code | 5/0 | `DCL_ALIAS`, `DECLARATION`, `DECLARE` |
| `$1A92` | 126 | `DCL_STATIC` | code | 126/0 | `DECLARE` |
| `$1B10` | 7 | `DCL_ALLOCIF` | code | 7/0 | `DCL_STATIC` |
| `$1B17` | 12 | `DCL_ALLOC` | code | 12/0 | `DCL_ALLOCIF`, `DCL_STATIC` |
| `$1B23` | 8 | `NEED_NAME` | code | 8/0 | `DECLARE`, `MEMBERS` |
| `$1B2B` | 7 | `DCL_GETTYPE` | code | 7/0 | `CC_FINISH`, `CX_POSTFIX_LOOP`, `CX_PRIMARY`, `DCL_GLOBAL`, `DCL_STATIC` +1 |
| `$1B32` | 7 | `DCL_SETTYPE` | code | 7/0 | `CX_PRIMARY`, `DCL_GLOBAL`, `DCL_STATIC`, `DCL_TYPE`, `MEMBERS` +1 |
| `$1B39` | 26 | `DCL_TYPE` | code | 26/0 | `DCL_GLOBAL`, `DCL_LOCAL` |
| `$1B53` | 13 | `DCL_NEWCUR` | code | 13/0 | `DCL_LOCAL`, `ENUM_SPEC` |
| `$1B60` | 97 | `DCL_GLOBAL` | code | 97/0 | `DECLARE` |
| `$1BC1` | 26 | `DCL_PARTIAL` | code | 26/0 | `DCL_GLOBAL` |
| `$1BDB` | 44 | `DCL_ALIAS` | code | 44/0 | `DECLARE` |
| `$1C07` | 3 | `CC_E_NOTSUP` | code+data | 2/1 | `CX_LVALUE`, `DECLARATOR`, `DECLARE`, `DECL_SPECS`, `MEMBERS` +3 |
| `$1C0A` | 3 | `CC_E_SYNTAX` | code+data | 2/1 | `CC_EXPECT`, `CC_E_NOTSUP`, `CX_CALL`, `CX_POSTFIX_LOOP`, `CX_PRIMARY` +8 |
| `$1C0D` | 3 | `CC_E_REDECL` | code+data | 2/1 | `CC_E_SYNTAX`, `DCL_ALIAS`, `DCL_GLOBAL`, `DCL_NEWCUR`, `ENUM_SPEC` +2 |
| `$1C10` | 3 | `CC_E_REDEF` | code+data | 2/1 | `CC_E_REDECL`, `DCL_STATIC`, `ENUM_SPEC`, `FUNC_DEF`, `STRUCT_SPEC` |
| `$1C13` | 3 | `CC_E_UNDECL` | code+data | 2/1 | `CC_E_REDEF` |
| `$1C16` | 3 | `CC_E_TYPESPEC` | code+data | 2/1 | `CC_E_UNDECL`, `DECL_SPECS` |
| `$1C19` | 3 | `CC_E_BADDECL` | code+data | 2/1 | `CC_E_TYPESPEC`, `FUNC_DEF`, `PARAMS`, `SUFFIX_ARRAY`, `SUFFIX_FUNC` |
| `$1C1C` | 3 | `CC_E_STORAGE` | code+data | 2/1 | `CC_E_BADDECL`, `DECLARE`, `DECL_SPECS`, `FUNC_DEF`, `MEMBERS` +2 |
| `$1C1F` | 3 | `CC_E_PARAM` | code+data | 2/1 | `CC_E_STORAGE`, `FUNC_DEF` |
| `$1C22` | 3 | `CC_E_INIT` | code+data | 2/1 | `CC_E_PARAM`, `DCL_NOINIT`, `INIT_LIST`, `INIT_STRING`, `INIT_TOP` |
| `$1C25` | 3 | `CC_E_ARRAYSIZE` | code+data | 2/1 | `CC_E_INIT`, `SUFFIX_ARRAY` |
| `$1C28` | 3 | `CC_E_TYPE` | code+data | 2/1 | `CC_E_ARRAYSIZE`, `CX_CHECK_ASSIGN`, `DCL_GLOBAL`, `RETURN` |
| `$1C2B` | 3 | `CC_E_CONSTEXPR` | code+data | 2/1 | `CC_E_TYPE`, `CX_CONST_INIT`, `CX_CONST_INT` |
| `$1C2E` | 3 | `CC_E_OPERAND` | code+data | 2/1 | `CC_E_CONSTEXPR`, `CX_CALL`, `CX_CAST`, `CX_DEREF`, `CX_INT_A` +2 |
| `$1C31` | 3 | `CC_E_MEMBER` | code+data | 2/1 | `CC_E_OPERAND`, `CX_POSTFIX_LOOP` |
| `$1C34` | 3 | `CC_E_LVALUE` | code+data | 2/1 | `CC_E_MEMBER`, `CX_LVALUE`, `CX_UNARY` |
| `$1C37` | 3 | `CC_E_FRAME` | code+data | 2/1 | `CC_E_LVALUE`, `DECLARE` |
| `$1C3A` | 5 | `CC_E_PARAMS` | code | 5/0 | `CC_E_FRAME`, `PARAMS` |
| `$1C3F` | 14 | `TY_CLASS` | code | 14/0 | `CG_BYTE`, `CG_LOAD`, `CX_ASSIGN`, `CX_BINOP`, `CX_CALL` +24 |
| `$1C4D` | 13 | `TY_FIELDS` | code | 13/0 | `CC_FINISH`, `CX_CALL`, `CX_POSTFIX_LOOP`, `DCL_PARTIAL`, `FUNC_DEF` +6 |
| `$1C5A` | 13 | `TY_SETAB` | code | 13/0 | `CX_PRIMARY`, `MEMBERS`, `TY_ARRAY`, `TY_PTR` |
| `$1C67` | 12 | `TY_NEW` | code | 12/0 | `CX_PRIMARY`, `PARAMS`, `ST_NODE`, `TY_ARRAY`, `TY_PTR` |
| `$1C73` | 6 | `TY_SIZE` | code | 6/0 | `CX_BINOP`, `CX_INCDEC`, `CX_PRIMARY`, `CX_UNARY`, `DCL_STATIC` +5 |
| `$1C79` | 5 | `TY_E_INCOMPLETE` | code | 5/0 | `CX_POSTFIX_LOOP`, `CX_PRIMARY`, `DCL_STATIC`, `ENUM_SPEC`, `TY_SIZE` |
| `$1C7E` | 51 | `TY_SIZE0` | code | 51/0 | `DCL_STATIC`, `TY_SIZE` |
| `$1CB1` | 26 | `TY_DEREF` | code | 26/0 | `CX_BINOP`, `CX_CALL`, `CX_CHECK_ASSIGN`, `CX_DEREF`, `CX_INCDEC` +5 |
| `$1CCB` | 42 | `TY_PTR` | code | 42/0 | `CX_RVAL`, `CX_UNARY`, `DECLARATOR`, `PARAMS` |
| `$1CF5` | 5 | `TY_E_NESTING` | code | 5/0 | `TY_PTR` |
| `$1CFA` | 39 | `TY_ARRAY` | code | 39/0 | `CX_PRIMARY`, `DCL_STATIC`, `SUFFIX_ARRAY` |
| `$1D21` | 5 | `TY_E_TOOLARGE` | code | 5/0 | `MEMBERS`, `TY_ARRAY` |
| `$1D26` | 140 | `TY_EQUAL` | code | 140/0 | `CX_CHECK_ASSIGN`, `DCL_GLOBAL` |
| `$1DB2` | 45 | `DATA_ALLOC` | code | 45/0 | `CX_PRIMARY`, `DCL_ALLOC` |
| `$1DDF` | 5 | `CC_E_TOOBIG` | code | 5/0 | `CG_UNIT` |
| `$1DE4` | 54 | `STR_STAGE` | code | 54/0 | `CX_PRIMARY`, `INIT_STRING` |
| `$1E1A` | 21 | `INIT_TOP` | code | 21/0 | `DCL_STATIC` |
| `$1E2F` | 98 | `INIT` | code | 98/0 | `INIT_LIST`, `INIT_TOP` |
| `$1E91` | 16 | `INIT_CLOSE` | code | 16/0 | `INIT` |
| `$1EA1` | 67 | `INIT_STRING` | code | 67/0 | `INIT` |
| `$1EE4` | 208 | `INIT_LIST` | code | 208/0 | `INIT` |

#### `symtab` — Compiler: scoped symbol table: 295 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$12F8` | 21 | `WS_GALLOC` (= `COMP_LEXER_END`, `COMP_SYMTAB_BEGIN`) | code | 21/0 | `SYM_MAKE_G`, `TY_NEW` |
| `$130D` | 21 | `WS_LALLOC` | code | 21/0 | `SYM_MAKE` |
| `$1322` | 4 | `WS_E_NOMEM` | code | 4/0 | `STR_STAGE`, `WS_GALLOC`, `WS_LALLOC` |
| `$1326` | 11 | `SYM_MAKE` | code | 11/0 | `SYM_NEW` |
| `$1331` | 3 | `SYM_MAKE_G` | code | 3/0 | `MEMBERS`, `SYM_NEWG` |
| `$1334` | 46 | `SYM_MAKE_IN` | code | 46/0 | `SYM_MAKE`, `SYM_MAKE_G` |
| `$1362` | 1 | `CALL_HL` | code | 1/0 | `CX_MAYBE`, `DECL_SPECS`, `SYM_MAKE_IN` |
| `$1363` | 8 | `SYM_NEWG` | code | 8/0 | `CX_PRIMARY`, `DCL_GLOBAL` |
| `$136B` | 15 | `SYM_NEW` | code | 15/0 | `DCL_ALIAS`, `DCL_NEWCUR`, `ENUM_SPEC`, `STRUCT_SPEC` |
| `$137A` | 13 | `SYM_LINK` | code | 13/0 | `SYM_NEW`, `SYM_NEWG` |
| `$1387` | 66 | `SYM_FIND` | code | 66/0 | `CC_FINISH`, `CX_POSTFIX_LOOP`, `CX_PRIMARY`, `DCL_GLOBAL`, `MEMBERS` +2 |
| `$13C9` | 15 | `SYM_LOOKUP` | code | 15/0 | `CX_PRIMARY`, `ENUM_SPEC`, `IS_DECL_START`, `STRUCT_SPEC` |
| `$13D8` | 16 | `SYM_FIND_CUR` | code | 16/0 | `DCL_ALIAS`, `DCL_NEWCUR`, `ENUM_SPEC`, `STRUCT_SPEC` |
| `$13E8` | 13 | `NM_FROM_TOK` | code | 13/0 | `CX_POSTFIX_LOOP`, `CX_PRIMARY`, `ENUM_SPEC`, `IS_DECL_START`, `STRUCT_SPEC` |
| `$13F5` | 21 | `SCOPE_OPEN` | code | 21/0 | `FUNC_DEF`, `PARAMS` |
| `$140A` | 21 | `SCOPE_CLOSE` | code | 21/0 | `FUNC_DEF`, `PARAMS` |

#### `expr` — Compiler: typed expressions: 2641 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$1FB4` | 26 | `CX_CONST_INT` (= `COMP_DECL_END`, `COMP_EXPR_BEGIN`) | code | 26/0 | `ENUM_SPEC`, `SUFFIX_ARRAY` |
| `$1FCE` | 18 | `CX_CONST_INIT` | code | 18/0 | `INIT` |
| `$1FE0` | 23 | `CX_EXPR` | code | 23/0 | `CX_COND`, `CX_PAREN_REST`, `CX_POSTFIX_LOOP`, `RETURN`, `STATEMENT` |
| `$1FF7` | 128 | `CX_ASSIGN` | code | 128/0 | `CX_CALL`, `CX_EXPR` |
| `$2077` | 43 | `CX_LVALUE` | code | 43/0 | `CX_ASSIGN`, `CX_INCDEC` |
| `$20A2` | 17 | `CX_LVHOLD` | code | 17/0 | `CX_ASSIGN`, `CX_INCDEC` |
| `$20B3` | 28 | `CX_HOLD` | code | 28/0 | `CX_ASSIGN`, `CX_BINARY`, `CX_CALL`, `CX_POSTFIX_LOOP` |
| `$20CF` | 10 | `CX_MAYBE` | code | 10/0 | `CX_COND`, `CX_LOGIC` |
| `$20D9` | 15 | `CX_UNMUTE` | code | 15/0 | `CX_MAYBE`, `CX_UNARY` |
| `$20E8` | 18 | `CX_MUTE` | code | 18/0 | `CX_MAYBE`, `CX_UNARY` |
| `$20FA` | 164 | `CX_COND` | code | 164/0 | `CX_ASSIGN`, `CX_CONST_INIT`, `CX_CONST_INT` |
| `$219E` | 16 | `CX_TRUTH` | code | 16/0 | `CX_COND`, `CX_LOGIC` |
| `$21AE` | 6 | `CX_SET_RVAL` | code | 6/0 | `CX_CALL`, `CX_CAST` |
| `$21B4` | 66 | `CX_BINARY` | code | 66/0 | `CX_COND`, `CX_LOGIC` |
| `$21F6` | 17 | `CX_PREC` | code | 17/0 | `CX_BINARY` |
| `$2207` | 36 | `CX_PREC_TABLE` | table | 0/36 | `CX_PREC` |
| `$222B` | 131 | `CX_LOGIC` | code | 131/0 | `CX_BINARY` |
| `$22AE` | 281 | `CX_BINOP` | code | 281/0 | `CX_ASSIGN`, `CX_BINARY`, `CX_POSTFIX_LOOP` |
| `$23C7` | 10 | `CX_SCALARV` | code | 10/0 | `CX_COND` |
| `$23D1` | 6 | `CX_SCALAR_X` | code | 6/0 | `CX_CALL`, `CX_COND`, `CX_LOGIC`, `CX_UNARY` |
| `$23D7` | 7 | `CX_SCALAR_A` | code | 7/0 | `CX_BINOP`, `CX_CAST`, `CX_SCALARV`, `CX_SCALAR_X` |
| `$23DE` | 7 | `CX_INT_A` | code | 7/0 | `CX_BINOP`, `CX_UNARY` |
| `$23E5` | 17 | `CX_USUAL` | code | 17/0 | `CX_BINOP`, `CX_COND` |
| `$23F6` | 10 | `TY_PROMOTE` | code | 10/0 | `CX_BINOP`, `CX_UNARY` |
| `$2400` | 300 | `CX_UNARY` | code | 300/0 | `CX_BINARY`, `CX_PRIMARY` |
| `$252C` | 92 | `CX_INCDEC` | code | 92/0 | `CX_POSTFIX_LOOP`, `CX_UNARY` |
| `$2588` | 3 | `CX_POSTFIX` | code | 3/0 | `CX_UNARY` |
| `$258B` | 153 | `CX_POSTFIX_LOOP` | code | 153/0 | `CX_POSTFIX`, `CX_UNARY` |
| `$2624` | 330 | `CX_CALL` | code | 330/0 | `CX_POSTFIX_LOOP` |
| `$276E` | 309 | `CX_PRIMARY` | code | 309/0 | `CX_POSTFIX` |
| `$28A3` | 8 | `CX_PAREN_REST` | code | 8/0 | `CX_PRIMARY`, `CX_UNARY` |
| `$28AB` | 79 | `CX_RVAL` | code | 79/0 | `CX_ASSIGN`, `CX_BINARY`, `CX_CALL`, `CX_COND`, `CX_CONST_INIT` +7 |
| `$28FA` | 52 | `CX_DEREF` | code | 52/0 | `CX_POSTFIX_LOOP`, `CX_UNARY` |
| `$292E` | 88 | `CX_CAST` | code | 88/0 | `CX_ASSIGN`, `CX_PRIMARY`, `RETURN` |
| `$2986` | 79 | `CX_CHECK_ASSIGN` | code | 79/0 | `CX_ASSIGN`, `CX_CALL`, `INIT`, `RETURN` |
| `$29D5` | 15 | `CX_PUSHX` | code | 15/0 | `CX_ASSIGN`, `CX_COND`, `CX_HOLD`, `CX_INCDEC` |
| `$29E4` | 15 | `CX_POPY` | code | 15/0 | `CX_ASSIGN`, `CX_BINARY`, `CX_CALL`, `CX_COND`, `CX_INCDEC` +1 |
| `$29F3` | 18 | `CX_SWAP` | code | 18/0 | `CG_LOADY`, `CX_COND`, `CX_SWAPCG` |

#### `codegen` — Compiler: code generator (templates, fixups, constant folding): 1340 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$2A05` | 130 | `CG_UNIT` (= `COMP_EXPR_END`, `COMP_CODEGEN_BEGIN`) | code | 130/0 | `CG_ADDK`, `CG_EXT`, `CG_MULK`, `CG_OP`, `CG_SEQ` +2 |
| `$2A87` | 3 | `CG_OP` | code | 3/0 | `CG_BINOP`, `CG_CMP`, `CG_DIVK`, `CG_FRAME`, `CG_FUNCOP` +12 |
| `$2A8A` | 18 | `CG_B` | code | 18/0 | `CG_ADDK0`, `CG_FADDR`, `CG_FRAME`, `CG_LOAD`, `CG_MULK` +6 |
| `$2A9C` | 3 | `CG_OPW` | code | 3/0 | `CG_BINOP`, `CG_CALL`, `CG_DIVK`, `CG_LOAD`, `CG_MULK` +2 |
| `$2A9F` | 7 | `CG_W` | code | 7/0 | `CG_ADDK0`, `CG_FADDR`, `CG_FUNCOP`, `CG_JP`, `CG_OPW` |
| `$2AA6` | 3 | `CG_SEQ` | code | 3/0 | `CG_BINOP`, `CG_CMP`, `CG_FADDR`, `CG_STORE`, `CG_TEST` +1 |
| `$2AA9` | 9 | `CG_SEQ0` | code | 9/0 | `CG_EXT0`, `CG_SEQ` |
| `$2AB2` | 13 | `CG_FRAME` | code | 13/0 | `CG_LOAD`, `CG_STORE` |
| `$2ABF` | 17 | `CG_JP` | code | 17/0 | `CG_JCOND`, `CX_COND` |
| `$2AD0` | 8 | `CG_HERE` | code | 8/0 | `CX_COND` |
| `$2AD8` | 14 | `CG_PATCH` | code | 14/0 | `CG_HERE`, `CX_LOGIC`, `FUNC_DEF` |
| `$2AE6` | 12 | `CG_FUNCOP` | code | 12/0 | `CG_LOAD`, `CX_CALL` |
| `$2AF2` | 38 | `CG_FLINK` | code | 38/0 | `CG_FUNCOP`, `INIT` |
| `$2B18` | 6 | `CG_VAL` | code | 6/0 | `CX_COND`, `CX_UNARY` |
| `$2B1E` | 149 | `CG_LOAD` | code | 149/0 | `CG_BINOP`, `CG_LOADY`, `CG_STORE`, `CG_TEST`, `CG_VAL` +11 |
| `$2BB3` | 5 | `CG_YBYTE` | code | 5/0 | `CG_STORE` |
| `$2BB8` | 3 | `CG_XBYTE` | code | 3/0 | `CG_LOAD` |
| `$2BBB` | 7 | `CG_BYTE` | code | 7/0 | `CG_XBYTE`, `CG_YBYTE` |
| `$2BC2` | 3 | `CG_EXT` | code | 3/0 | `CG_LOAD`, `CX_CAST` |
| `$2BC5` | 17 | `CG_EXT0` | code | 17/0 | `CG_EXT`, `CX_ASSIGN`, `CX_INCDEC` |
| `$2BD6` | 14 | `CG_NEAR` | code | 14/0 | `CG_LOAD`, `CX_LVHOLD` |
| `$2BE4` | 29 | `CG_FADDR` | code | 29/0 | `CG_NEAR`, `CX_RVAL`, `CX_UNARY` |
| `$2C01` | 10 | `CG_LVADDR` | code | 10/0 | `CG_LOAD`, `CX_LVHOLD`, `CX_RVAL`, `CX_UNARY` |
| `$2C0B` | 6 | `CG_ADDK` | code | 6/0 | `CG_BINOP`, `CG_LVADDR`, `CX_INCDEC` |
| `$2C11` | 48 | `CG_ADDK0` | code | 48/0 | `CG_ADDK`, `CX_INCDEC` |
| `$2C41` | 53 | `CG_MULK` | code | 53/0 | `CG_BINOP`, `CX_BINOP` |
| `$2C76` | 22 | `CG_DIVK` | code | 22/0 | `CX_BINOP` |
| `$2C8C` | 5 | `CG_CALL` | code | 5/0 | `CG_BINOP`, `CG_DIVK`, `CG_MULK`, `CX_CALL`, `CX_UNARY` |
| `$2C91` | 4 | `CG_JTRUE` | code | 4/0 | `CX_LOGIC` |
| `$2C95` | 2 | `CG_JFALSE` | code | 2/0 | `CX_COND`, `CX_LOGIC` |
| `$2C97` | 42 | `CG_JCOND` | code | 42/0 | `CG_JFALSE`, `CG_JTRUE` |
| `$2CC1` | 19 | `CG_TEST` | code | 19/0 | `CG_JCOND`, `CX_LOGIC`, `CX_UNARY` |
| `$2CD4` | 11 | `CG_SETCOND` | code | 11/0 | `CG_BINOP`, `CG_CMP`, `CG_TEST`, `CX_UNARY` |
| `$2CDF` | 234 | `CG_BINOP` | code | 234/0 | `CX_BINOP` |
| `$2DC9` | 64 | `CG_CMP` | code | 64/0 | `CG_BINOP` |
| `$2E09` | 26 | `CG_HTAB` | table | 0/26 | `CG_BINOP` |
| `$2E23` | 6 | `CG_CMPTAB` | table | 0/6 | `CG_CMP` |
| `$2E29` | 20 | `CG_YHL` | code | 20/0 | `CG_BINOP` |
| `$2E3D` | 25 | `CG_YDE` | code | 25/0 | `CG_BINOP`, `CG_STORE` |
| `$2E56` | 9 | `CG_LOADY` | code | 9/0 | `CG_BINOP`, `CG_YHL`, `CX_CALL` |
| `$2E5F` | 40 | `CX_SWAPCG` | code | 40/0 | `CX_BINOP` |
| `$2E87` | 71 | `CG_STORE` | code | 71/0 | `CX_ASSIGN`, `CX_INCDEC` |
| `$2ECE` | 12 | `CG_TAILON` | code | 12/0 | `CX_ASSIGN`, `CX_INCDEC` |
| `$2EDA` | 9 | `CG_TAILOFF` | code | 9/0 | `CX_ASSIGN`, `CX_INCDEC` |
| `$2EE3` | 25 | `CX_DISCARD` | code | 25/0 | `CX_EXPR`, `STATEMENT` |
| `$2EFC` | 7 | `NEG_DE` | code | 7/0 | `CG_BINOP`, `CX_INCDEC` |
| `$2F03` | 3 | `TPL_ZEXT` | table | 0/3 | `CG_EXT0` |
| `$2F06` | 5 | `TPL_SEXT` | table | 0/5 | `CG_EXT0` |
| `$2F0B` | 5 | `TPL_IXHL` | table | 0/5 | `CG_FADDR` |
| `$2F10` | 3 | `TPL_TEST` | table | 0/3 | `CG_BINOP`, `CG_TEST` |
| `$2F13` | 4 | `TPL_SBC` | table | 0/4 | `CG_BINOP`, `CG_CMP` |
| `$2F17` | 3 | `TPL_STDE` | table | 0/3 | `CG_STORE` |
| `$2F1A` | 7 | `TPL_AND` | table | 0/7 | `CG_BINOP` |
| `$2F21` | 7 | `TPL_OR` | table | 0/7 | `CG_BINOP` |
| `$2F28` | 7 | `TPL_XOR` | table | 0/7 | `CG_BINOP` |
| `$2F2F` | 9 | `TPL_AND01` | table | 0/9 | `CX_LOGIC` |
| `$2F38` | 9 | `TPL_OR10` | table | 0/9 | `CX_LOGIC` |

#### `stmt` — Compiler: statements and functions: 446 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$2F4C` | 180 | `FUNC_DEF` (= `COMP_TRAMP_END`, `COMP_STMT_BEGIN`) | code | 180/0 | `DECLARATION` |
| `$3000` | 21 | `BLOCK_ITEMS` | code | 21/0 | `FUNC_DEF` |
| `$3015` | 49 | `STATEMENT` | code | 49/0 | `BLOCK_ITEMS` |
| `$3046` | 44 | `RETURN` | code | 44/0 | `STATEMENT` |
| `$3072` | 5 | `STMT_END` | code | 5/0 | `RETURN`, `STATEMENT` |
| `$3077` | 120 | `CC_FINISH` | code | 120/0 | `CC_COMPILE` |
| `$30EF` | 4 | `CC_MAIN_NAME` | table | 0/4 | `CC_FINISH` |
| `$30F3` | 23 | `CC_PROGRAM` | code | 23/0 | — |

#### `helpers` — Runtime: helper core: 107 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$310A` | 25 | `RT_ENTER` (= `COMP_STMT_END`, `COMP_HELPERS_BEGIN`) | code | 25/0 | `RST_ENTER` |
| `$3123` | 5 | `RT_CMPLT_SAME` | code | 5/0 | `RST_CMPLT` |
| `$3128` | 1 | `RT_CALLHL` | code | 1/0 | `CX_CALL`, `RT_RUN` |
| `$3129` | 5 | `RT_MUL` | code | 5/0 | `CG_HTAB`, `CG_MULK` |
| `$312E` | 4 | `RT_DIVS` | code | 4/0 | `CG_DIVK`, `CG_HTAB` |
| `$3132` | 4 | `RT_MODS` | code | 4/0 | `CG_HTAB` |
| `$3136` | 5 | `RT_MODU` | code | 5/0 | `CG_HTAB` |
| `$313B` | 6 | `RT_DIVU` | code | 6/0 | `CG_HTAB`, `RT_MODU` |
| `$3141` | 7 | `RT_CPL` | code | 7/0 | `CX_UNARY` |
| `$3148` | 8 | `RT_SHL` | code | 8/0 | `CG_HTAB` |
| `$3150` | 11 | `RT_SHR` | code | 11/0 | `CG_HTAB` |
| `$315B` | 11 | `RT_SAR` | code | 11/0 | `CG_HTAB` |
| `$3166` | 15 | `RT_SHCNT` | code | 15/0 | `RT_SAR`, `RT_SHL`, `RT_SHR` |

#### `rtexit` — Runtime: start, exit, BREAK, runtime errors: 78 B

| Address | Bytes | Routine | Kind | Code/data | Referenced by |
|---|---:|---|---|---|---|
| `$3175` | 65 | `RT_RUN` (= `COMP_HELPERS_END`, `COMP_RTEXIT_BEGIN`) | code | 65/0 | — |
| `$31B6` | 3 | `RT_ERR_STACK` | code+data | 2/1 | `RT_ENTER` |
| `$31B9` | 2 | `RT_ERR_ARG` | code | 2/0 | `AY_BEEP_PERIOD`, `RT_ERR_STACK` |
| `$31BB` | 8 | `RT_ERROR` | code | 8/0 | `RT_ERR_ARG` |
