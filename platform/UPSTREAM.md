# platform/ — vendored Leap V2 platform sources

**Upstream:** 2068-Leap (`~/2068-Leap`, github.com/nchiker/2068-Leap), release tag **`v2.0.1-emu.1`**, commit **`d19b9ead9880b31c5fee59e71519a42f4c0263b0`**. The release images are HOME `3f13ec2c…` and EXROM `24b1ebb0…`.

These are copies, not a link. Frozen V2 is never modified and never imported from: nothing in this repository reads or writes `~/2068-Leap` except `tools/check_platform.py`, which only runs `git show` on the tag, and (Phase 7) `tools/v2ref.sh`, which only runs `git archive` of the tag and builds the V2 reference ROM from that copy in `build/v2ref/` (checked against the release hashes) for the cross-version tape tests.

Copied 2026-10-13 (M1.1) with `git archive v2.0.1-emu.1`. Paths below `platform/` are the V2 paths.

## Files

`MANIFEST` lists each file with its sha256 at the tag, its current sha256 and its status. `make check` runs `tools/check_platform.py`, which checks four things:

- Every file is listed.
- Each pristine file is byte-identical to the tag.
- Each modified file is exactly its recorded patch (`deltas/*.patch`) away from the tag.
- When `~/2068-Leap` is present, the recorded upstream hashes still match the tag.

| File | Leap-C use | Image | Status |
|---|---|---|---|
| `include/hardware.inc` | ports, screen geometry | both | pristine |
| `include/keys.inc` | key codes | EXROM | pristine |
| `include/sysvars.inc` | platform system variables | both | **delta D1** |
| `kernel/memory/memory.asm` | line store, fill, shift, cold init | HOME | **deltas D2, D5** |
| `kernel/io/io.asm` | keyboard | HOME | **delta D7** |
| `kernel/graphics/graphics.asm` | text, attributes, scroll, pixels, line, sprites, font | HOME | **deltas D6, D8** |
| `kernel/math/math.asm` | 16-bit negate, absolute value, signed compare | HOME | **delta D3** |
| `kernel/interrupt/interrupt.asm` | IM 1 handler: FRAMES, keyboard scan, BREAK latch | HOME | pristine |
| `kernel/bank/bank.asm` | EXROM paging (depth-counted) | HOME | pristine |
| `rom/v2_ay_beep.asm` | AY beep (HOME pieces; the EXROM piece `AY_BEEP`) | both | pristine |
| `kernel/storage/storage.asm` | tape: block I/O (HOME), header logic (EXROM) | both | **delta D9** |
| `rom/exrom_editor.asm` | editor engine | EXROM | pristine |
| `rom/exrom_sound.asm` | `SOUND` register write | EXROM | pristine |
| `rom/exrom_format.asm` | integer formatting; float formatting (FP component) | EXROM | pristine |
| `rom/exrom_calc.asm` | FP calculator (optional component, `spec.md` §4.9) | EXROM | pristine |

**Not vendored:**

- the BASIC VM, compiler and symbol table;
- SAVE ALL, session undo and the Array Store;
- the package registry and the package ABI;
- `v2_layout.inc` (BASIC's compile and run layout) and `v2_ktab.inc`;
- the port-$FE `kernel/sound` (V2 production uses the AY beep instead).

The V2 shell (`rom/exrom_v2_shell.asm` at the tag) is adapted into `src/shell/shell.asm` (Phase 5), with its own provenance note in that file's header: it is Leap-C source, not a vendored file, so it is not in `MANIFEST`. V2's current release `v2.0.2-emu.1` (`77f1baa`) differs from the tag in that file and in `rom/exrom_editor.asm` only in comments (checked in Phase 5).

## Configuration

The modules are assembled in V2's production configuration (`include/leapc_rom.inc`): `V2_PRODUCTION`, `V2_COMPACT_SYSVARS`, `V2_MAINT_AY_BEEP`, `V2_MAINT_SHARED_WAIT`, `V2_MAINT_AYB_PERIOD_HOME`, `V2_MAINT_SOUND0`, `V2_FAST_REDRAW` and `STORAGE_VERSIONED`.

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

## Names the platform expects from Leap-C

These names are defined by Leap-C files, so the platform files themselves do not need changing.

| Name | Defined in | Meaning |
|---|---|---|
| `IO_KEY_SCAN_ROW` | `src/rom/home.asm` (page zero) | V2 production placed it in page-zero padding too |
| `VM_HALTED` | `include/leapc_cells.inc` (= `BRK_HALT`) | the BREAK request that `AY_WAIT_FRAMES` tests (set by the runtime's `RT_BREAKREQ` during a `NOBRK` section, `spec.md` §5.8) |
| `RT_BREAKREQ` | `src/runtime/rtexit.asm` | called by the ISR (delta D4) when it accepts the BREAK key |
| `VM_ERR_RANGE` | `src/runtime/rtexit.asm` (= `RT_ERR_ARG`) | the beep semitone range error (runtime error 4 at the program's `beep()` call) |
| `V2_REDRAW_SCOPE`, `V2_RD_*` | `include/leapc_cells.inc` | V2 placed these editor cells at `$BEC0`, which is source RAM in the Leap-C layout |
| `V2_FORMAT_WORD`, `PKG_ABI_WORD` | `include/leapc_rom.inc` (= `LEAPC_TAPE_VERSION` `$8C00`) | tape version word (`spec.md` §8.1) |
| `KTAB_*` | `src/rom/exrom.asm` (= the HOME routines) | as in V2 production |
| `KTAB_CALC_EXIT_TRAMPOLINE` | `src/rom/exrom.asm` (= `BANK_PAGE_EXROM_OUT`) | V2's trampoline was a bare `jp BANK_PAGE_EXROM_OUT` |

## Platform facts found while vendoring (M1.1)

- `STORAGE_SAVE`/`STORAGE_LOAD` take IX as the data pointer and destroy it, and `rom/exrom_editor.asm` uses IX too. The HOME platform modules use neither IX nor IY, which confirms `spec.md` §5.1 for the code that compiled programs call. The Phase 7 `tape_save`/`tape_load` trampolines must preserve IX (the frame base).
- The relocated system variables occupy `$5B00-$5D59` (602 B), exactly as `spec.md` §3.1 predicted.
