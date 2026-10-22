# platform/ — vendored Leap V2 platform sources

**Upstream:** 2068-Leap (`~/2068-Leap`, github.com/nchiker/2068-Leap), release tag **`v2.0.1-emu.1`**, commit **`d19b9ead9880b31c5fee59e71519a42f4c0263b0`**. The release images are HOME `3f13ec2c…` and EXROM `24b1ebb0…`.

These are copies, not a link. Frozen V2 is never modified and never imported from: nothing in this repository reads or writes `~/2068-Leap` except `tools/check_platform.py`, which only runs `git show` on the tag, and (Phase 7) `tools/v2ref.sh`, which only runs `git archive` of the tag and builds the V2 reference ROM from that copy in `build/v2ref/` (checked against the release hashes) for the cross-version tape tests.

Copied 2026-10-13 (M1.1) with `git archive v2.0.1-emu.1`. Paths below `platform/` are the V2 paths.

## Files

`MANIFEST` lists each file with its sha256 at the tag, its current sha256 and its status. `make check` runs `tools/check_platform.py`, which checks four things (and, since Phase 11, the cut records of deltas D20 and D21: removed upstream text verified by its hash, never stored here):

- Every file is listed.
- Each pristine file is byte-identical to the tag.
- Each modified file is exactly its recorded patch (`deltas/*.patch`) away from the tag.
- When `~/2068-Leap` is present, the recorded upstream hashes still match the tag.

| File | Leap-C use | Image | Status |
|---|---|---|---|
| `include/hardware.inc` | ports, screen geometry | both | pristine |
| `include/keys.inc` | key codes | EXROM | pristine |
| `include/sysvars.inc` | platform system variables | both | **delta D1** |
| `kernel/memory/memory.asm` | line store, fill, shift, cold init (the editor's insert and range delete: EXROM) | both | **deltas D2, D5, D11** |
| `kernel/io/io.asm` | keyboard | HOME | **delta D7** |
| `kernel/graphics/graphics.asm` | text, attributes, scroll, pixels, line, sprites, font (the editor's bold and string output: EXROM) | both | **deltas D6, D8, D12, D13, D21** |
| `kernel/math/math.asm` | 16-bit negate, absolute value, signed compare | HOME | **delta D3** |
| `kernel/interrupt/interrupt.asm` | IM 1 handler: FRAMES, keyboard scan, BREAK latch | HOME | **delta D4** |
| `kernel/bank/bank.asm` | EXROM paging (depth-counted) | HOME | **delta D14** |
| `rom/v2_ay_beep.asm` | AY beep (HOME pieces; the EXROM piece `AY_BEEP_PLAY`) | both | **delta D17** |
| `kernel/storage/storage.asm` | tape: the header logic (EXROM); the block I/O is Leap-C's own since D20 | EXROM | **deltas D9, D18, D20** |
| `rom/exrom_editor.asm` | editor engine | EXROM | **deltas D15, D16, D17** |
| `rom/exrom_sound.asm` | `SOUND` register write | EXROM | **delta D19** |
| `rom/exrom_format.asm` | integer formatting (V2's float formatting not assembled) | EXROM | **delta D10** |

**Not vendored:**

- `rom/exrom_calc.asm`, the FP calculator: vendored pristine until Phase 11 as the reference the float core (`src/runtime/fpcore.asm`, `spec.md` §4.9) was re-engineered from, though not assembled since Phase 8; removed for the public beta because parts of it are ported from the Spectrum ROM's calculator (Amstrad copyright, `NOTICE`). It is at the V2 tag;
- the BASIC VM, compiler and symbol table;
- SAVE ALL, session undo and the Array Store;
- the package registry and the package ABI;
- `v2_layout.inc` (BASIC's compile and run layout) and `v2_ktab.inc`;
- the port-$FE `kernel/sound` (V2 production uses the AY beep instead).

The V2 shell (`rom/exrom_v2_shell.asm` at the tag) is adapted into `src/shell/shell.asm` (Phase 5), with its own provenance note in that file's header: it is Leap-C source, not a vendored file, so it is not in `MANIFEST`. V2's current release `v2.0.2-emu.1` (`77f1baa`) differs from the tag in that file and in `rom/exrom_editor.asm` only in comments (checked in Phase 5).

## Configuration

The modules are assembled in V2's production configuration (`include/leapc_rom.inc`): `V2_PRODUCTION`, `V2_COMPACT_SYSVARS`, `V2_MAINT_AY_BEEP`, `V2_MAINT_SHARED_WAIT`, `V2_MAINT_AYB_PERIOD_HOME`, `V2_MAINT_SOUND0`, `V2_FAST_REDRAW` and `STORAGE_VERSIONED`; Leap-C's own conditionals select the deltas D9-D12 (`STORAGE_BLOCKS_ONLY`/`STORAGE_NO_BLOCKS`, `LEAPC_FP_CORE`, `MEM_NO_LINE_EDIT`/`MEM_LINE_EDIT_ONLY`, `GFX_NO_EDITOR_TEXT`/`GFX_EDITOR_TEXT_ONLY`).

## Deltas

| Id | File | Change | Reason |
|---|---|---|---|
| D1 | `include/sysvars.inc` | `ORG $8000` → `ORG LEAPC_SYSVARS_BASE`. Before `PROG_AREA_START`: `LEAPC_SYSVARS_END:` and `ORG LEAPC_SRC_BASE` | Baseline memory layout (`spec.md` §3.1): system variables at `$5B00`, line store from `$7800` |
| D2 | `kernel/memory/memory.asm` | `MEM_COLD_INIT` clears from `LEAPC_COLD_CLEAR_BASE` instead of the literal `$8000` | The same layout: the cold clear covers the relocated system variables |
| D3 | `kernel/math/math.asm` | Deletions only: `MATH_UMUL16`, `MATH_UDIV16`, `MATH_MULTIPLY16`, `MATH_SIGN_PREP`, `MATH_APPLY_SIGN`, `MATH_DIVIDE16`, `MATH_SGN16`, `MATH_MOD16`, `MATH_SQRT16`, `MATH_RND16`, `MATH_RND_SEED` (351 B). Kept: `MATH_NEGATE16`, `MATH_ABS16`, `MATH_COMPARE16` | Owner decisions O1/O2 (Phase 2, `spec.md` v0.3). C's multiply and divide are the helper core's register-only routines (`src/runtime/helpers.asm`: about 1.4-2.3× faster). `SQRT16`, `SGN16` and `MULTIPLY16` have no Release 1 caller. `rand()`/`srand()` are the library's xorshift generator (`src/runtime/library.asm`). The system variables the removed routines used (`DIV_*`, `MATH_SIGN`, `SQRT_*`) stay defined in `sysvars.inc`, unused; `RND_STATE` is the library generator's state |
| D4 | `kernel/interrupt/interrupt.asm` | In `KBD_ISR_TICK`'s key acceptance, V2's BREAK latch (`cp KEY_BREAK` … `ld (VM_ERROR_CODE),a` / `ld (VM_HALTED),a`, 14 B, under `IFDEF V2_PRODUCTION`) is replaced by `sub KEY_BREAK / ld b,a` before the latch and `ld a,b / or a / call z,RT_BREAKREQ` after it (8 B) | BREAK for native programs (Phase 3, `spec.md` §5.8): the runtime decides (an ordinary key while no program runs; the end of the program, or a deferred request during a `NOBRK` section). The idle per-frame path is unchanged |
| D5 | `kernel/memory/memory.asm` | Deletions only: `MEM_INIT` no longer clears V2's string-function pool index (`STR_FUNC_POOL_NEXT`), package registry (`EXTENSION_MAGIC`, `EXTENSION_SLOT_COUNT`) and sprite slots (`SPRITE_SLOT_DEFINED/SHOWN`, `SPRITE_DISPLAY_DEPTH`) (25 B) | Phase 4 (`docs/milestones/M4.md`, ledger L24): Leap-C has none of these V2 features and nothing reads the cells (`tools/check_ram_layout.py`; the `$F3xx` package cells are outside the Leap-C map's use). `MEM_COLD_INIT` zeroes the system variables before the cold start calls `MEM_INIT` |
| D6 | `kernel/graphics/graphics.asm` | Deletions only: `GFX_SPRITE_INVALIDATE` and its calls in `GFX_CLS`, `GFX_SCROLL_TEXT_UP`, `GFX_SCROLL_TEXT_DOWN` (not assembled in production) and `GFX_SET_MODE` (25 B) | Phase 4 (ledger L24): it cleared V2's sprite-slot display state for BASIC's sprite slots; Leap-C's `sprite_get`/`sprite_put` use the program's buffers, and nothing reads those cells |
| D7 | `kernel/io/io.asm` | `KEY_ASCII_TABLE_SYMBOL`: SYMBOL SHIFT + A S D F G give `~ \| \ { }`, + U Y give `] [`, + H gives `^` (zeros before). `IO_DECODE_KEY` no longer turns SYMBOL SHIFT + A/S into `KEY_NEXT_ERROR`/`KEY_PREV_ERROR` (−19 B) | Phase 5: the C punctuation key map (`spec.md` §6.2, owner-approved baseline). V2's error-navigation codes had no handler in Leap-C (the editor engine passes them to the shell's navigation hook, which ignores them) |
| D8 | `kernel/graphics/graphics.asm` | `PUNCT_CHAR_TABLE`: 8 entries for `[ ] { } \| ~ ^ \` (font indices 86-93) and the entries reordered by their frequency in C (each keeps its V2 font index); `FONT_TABLE`: the 8 glyphs (64 B); `GFX_CLEAR_ROW_TEXT` deleted (16 B); the file header's glyph count | Phase 5: the C characters' glyphs (`spec.md` §6.2). The table is scanned linearly for every punctuation character drawn, so C's frequent ones first make the editor's redraw faster (measured with the typing cost). `GFX_CLEAR_ROW_TEXT` was V2's status-bar clear; the Leap-C shell clears rows itself (6 kT instead of 23 kT) and nothing else calls it |
| D9 | `kernel/storage/storage.asm` | Conditional assembly only (no instruction changes): `IFNDEF STORAGE_NO_BLOCKS` around `STORAGE_SEND_BLOCK` and `STORAGE_RECEIVE_BLOCK`, `IFNDEF STORAGE_BLOCKS_ONLY` around the rest (`STORAGE_VERSION_WORD` onwards), and a comment. HOME defines `STORAGE_BLOCKS_ONLY` and assembles the block I/O (331 B, byte for byte the vendored routines); the EXROM defines `STORAGE_NO_BLOCKS` and names its trampolines' callers `STORAGE_SEND_BLOCK` / `STORAGE_RECEIVE_BLOCK` (`src/shell/tape.asm`) | Phase 7 (`spec.md` §8.3, `docs/milestones/M7.md`, ledger L37-L38): the data blocks move with chunk 6 paged out, so `tape_save` / `tape_load` reach any address; the header logic stays in the EXROM |
| D10 | `rom/exrom_format.asm` | Conditional assembly only: `IFNDEF LEAPC_FP_CORE` around V2's float formatting (`BASIC_FLOAT_TO_STRING_EXROM`, 236 B) | Phase 8 (`spec.md` §4.9, ledger L43): Leap-C's float core has its own formatter (`XF_FTOA`, V2's exact fixed-point method with a precision); the integer formatting stays |
| D11 | `kernel/memory/memory.asm` | Conditional assembly only: `IFNDEF MEM_NO_LINE_EDIT` around `MEM_LINE_INSERT` and `MEM_LINE_DELETE_RANGE` (144 B), `IFNDEF MEM_LINE_EDIT_ONLY` around the rest (after the format constants) | Phase 8 (ledger L44-L45): the EXROM editor is their only caller, so the EXROM assembles them (`MEM_LINE_EDIT_ONLY`) and HOME does not (`MEM_NO_LINE_EDIT`): 144 B of HOME for the float work |
| D12 | `kernel/graphics/graphics.asm` | Conditional assembly only: `IFNDEF GFX_NO_EDITOR_TEXT` around `GFX_PUTCHAR_BOLD` and `GFX_PRINT_STRING` (32 B), `IFNDEF GFX_EDITOR_TEXT_ONLY` around the rest | Phase 8 (ledger L44-L45): the same for the editor's bold keywords and string output; they call HOME's `GFX_CHAR_SETUP` and `GFX_PUTCHAR`, exported to the EXROM |
| D13 | `kernel/graphics/graphics.asm` | `FONT_TABLE`: the glyphs of the digit `1` (`$20,$60,$A0,$20,$20,$20,$F8,$00`: a flag and a full-width base) and the letter `l` (`$60,$20,$20,$20,$20,$20,$18,$00`: a tail to the right, no base). Data only, no size change | Phase 9 (owner-approved): V2's `1` and `l` differed in two pixels, and a user typing `l.0` for `1.0` could not tell them apart on the screen (`docs/milestones/M9.md`). Both stay distinct from `I`, `|` and `!`, in plain and in bold (the editor's keywords) |
| D14 | `kernel/bank/bank.asm` | `BANK_PAGE_EXROM_IN` and `BANK_PAGE_EXROM_OUT` lose their `di` (−2 B); each keeps its `ei`, so interrupts are on at the return as before | Phase 9, a defect found by Fuse at the TS2068's own timing (ledger L60): the routines ran about 120 T with interrupts off and the TS2068's INT lasts 32 T, so a frame interrupt arriving then was lost. Float code pages the EXROM in and out for every operation, and `FRAMES` (`frames()`, the keyboard's timing) counted 5,966 of 6,024 frames in a float loop. The ISR touches none of the banking state (the depth, `PORT_FF_SHADOW`, the ports, chunk 6), and a BREAK cannot unwind inside them (every runtime page-in is under `NOBRK`) |
| D15 | `rom/exrom_editor.asm` | Deletions only: `EDITOR_INIT` no longer clears `EDITOR_REDRAW_HOOK` and `EDITOR_NAV_HOOK`; the built-in UP/DOWN handling and the second dispatch block for an unset navigation hook go (UP, DOWN, delete line and insert line share one dispatch through the hook); `EDITOR_REDRAW_SCREEN`'s default rendering for an unset redraw hook goes (it jumps to the hook). Comments mark each place | Phase 10, Fix 4 (ledger L65; the improvements report): the Leap-C shell sets both hooks before every editing session (`SH_LOOP`), so the fallbacks could never run (the ROM coverage of Phase 9 showed them unexecuted). A later caller of the editor engine without hooks would need them back: no library slot serves the editor (`spec.md` §2.4) |
| D16 | `rom/exrom_editor.asm` | Deletions only: `EDITOR_LOOP`'s cases for `KEY_NEXT_ERROR` and `KEY_PREV_ERROR`, `EDITOR_MOVE_CURSOR`'s cases for `EDIR_HOME` and `EDIR_END` | Phase 10, Fix 4: no key of Leap-C's map gives these codes (delta D7 removed NEXT/PREV ERROR's; HOME and END were never mapped) |
| D17 | `rom/exrom_editor.asm`, `rom/v2_ay_beep.asm` | Deletions only: `EDITOR_BLOCK_DELETE`; the EXROM's `AY_BEEP` entry (`call AY_BEEP_PERIOD`) | Phase 10, Fix 4: no caller (the coverage report's two never-entered routines). The shell deletes lines through its navigation hook; `beep()` calls `AY_BEEP_PERIOD` in HOME, then `AY_BEEP_PLAY` (unchanged) |
| D18 | `kernel/storage/storage.asm` | Deletions only: `STORAGE_SAVE`'s clamp of the name's length and its padding with spaces | Phase 10, Fix 4: both callers (the shell's SAVE and the library's `tape_save`) pass 10 characters already padded (`SH_NAME`). `STORAGE_VERSION_WORD` stays: its package branch gives Leap-C's library tapes (type 4) their own version word (`spec.md` §8.4) |
| D19 | `rom/exrom_sound.asm` | `SOUND_EXROM` loses its range check (registers 17 and above) and its carry result | Phase 10, Fix 4: its only caller is the shell's start-up chime, which writes registers 0-10. C's `sound()` is `LIB_SOUND` in HOME, which writes the AY itself and keeps its own 0-15 check (runtime error 4) |
| D20 | `kernel/storage/storage.asm` | Removed: V2's block I/O (`STORAGE_SEND_BLOCK`, `STORAGE_RECEIVE_BLOCK`), their timing constants, D9's `IFNDEF STORAGE_NO_BLOCKS` around them and the file header that described them (V2's lines 1-106 and 188-592 at the tag), recorded by hash only (`deltas/kernel__storage__storage.asm.cut`; the patch is the delta from the tag's file without those lines). A new header says what is left | Phase 11, M11-tape: they were V2's port of the stock ROM's SA-BYTES / LD-BYTES (Amstrad copyright, `NOTICE`). Leap-C's clean-room `TAPE_SEND_BLOCK` and `TAPE_RECV_BLOCK` (`src/runtime/tapeblock.asm`, HOME, written from `docs/TAPE_SIGNAL_SPEC.md`; `docs/TAPE_CLEANROOM.md`) replace them; the EXROM's `STORAGE_SEND_BLOCK` / `STORAGE_RECEIVE_BLOCK` names still point at the shell's trampoline callers. HOME no longer includes this file |
| D21 | `kernel/graphics/graphics.asm` | `GFX_CHAR_TO_FONT_OFFSET.is_block_graphics` (the glyph of a block-graphics code 128-143 built in `BLOCK_GFX_SCRATCH`) rewritten: V2's 54 lines (the tag's lines 474-527, recorded by hash only in `deltas/kernel__graphics__graphics.asm.cut`) replaced by a clean-room version (36 B), the same contract and glyphs | Phase 11, M11-tape: V2's version contained the stock ROM's PO-GR-2 sequence twice (`NOTICE`). Written from the screen format alone (`docs/TAPE_CLEANROOM.md`) |

## Names the platform expects from Leap-C

These names are defined by Leap-C files, so the platform files themselves do not need changing.

| Name | Defined in | Meaning |
|---|---|---|
| `IO_KEY_SCAN_ROW` | `src/rom/home.asm` (page zero) | V2 production placed it in page-zero padding too |
| `VM_HALTED` | `include/leapc_cells.inc` (= `BRK_HALT`) | the BREAK request that `AY_WAIT_FRAMES` tests (set by the runtime's `RT_BREAKREQ` during a `NOBRK` section, `spec.md` §5.8) |
| `RT_BREAKREQ` | `src/runtime/rtexit.asm` | called by the ISR (delta D4) when it accepts the BREAK key |
| `VM_ERR_RANGE` | `src/runtime/rtexit.asm` (= `RT_ERR_ARG`) | the beep semitone range error (runtime error 4 at the program's `beep()` call) |
| `V2_REDRAW_SCOPE`, `V2_RD_*` | `include/leapc_cells.inc` | V2 placed these editor cells at `$BEC0`, which is source RAM in the Leap-C layout |
| `V2_FORMAT_WORD`, `PKG_ABI_WORD` | `include/leapc_rom.inc` (`V2_FORMAT_WORD` = `LEAPC_TAPE_VERSION` `$8C00`; `PKG_ABI_WORD` = `LX_WORD` `$8D01`, Phase 10) | tape version words: program and data tapes (`spec.md` §8.1), library tapes (header type 4, V2's package type, §8.4) |
| `KTAB_*` | `src/rom/exrom.asm` (= the HOME routines) | as in V2 production |
| `KTAB_CALC_EXIT_TRAMPOLINE` | `src/rom/exrom.asm` (= `BANK_PAGE_EXROM_OUT`) | V2's trampoline was a bare `jp BANK_PAGE_EXROM_OUT` |

## Platform facts found while vendoring (M1.1)

- `STORAGE_SAVE`/`STORAGE_LOAD` take IX as the data pointer and destroy it, and `rom/exrom_editor.asm` uses IX too. The HOME platform modules use neither IX nor IY, which confirms `spec.md` §5.1 for the code that compiled programs call. The Phase 7 `tape_save`/`tape_load` trampolines must preserve IX (the frame base).
- The relocated system variables occupy `$5B00-$5D59` (602 B), exactly as `spec.md` §3.1 predicted.
