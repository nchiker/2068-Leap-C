# platform/ — vendored Leap V2 platform sources

**Upstream:** 2068-Leap (`~/2068-Leap`, github.com/nchiker/2068-Leap), release tag **`v2.0.1-emu.1`**, commit **`d19b9ead9880b31c5fee59e71519a42f4c0263b0`**. The release images are HOME `3f13ec2c…` and EXROM `24b1ebb0…`.

These are copies, not a link. Frozen V2 is never modified and never imported from: nothing in this repository reads or writes `~/2068-Leap` except `tools/check_platform.py`, which only runs `git show` on the tag.

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
| `kernel/memory/memory.asm` | line store, fill, shift, cold init | HOME | **delta D2** |
| `kernel/io/io.asm` | keyboard | HOME | pristine |
| `kernel/graphics/graphics.asm` | text, attributes, scroll, pixels, line, sprites, font | HOME | pristine |
| `kernel/math/math.asm` | 16-bit negate, absolute value, signed compare | HOME | **delta D3** |
| `kernel/interrupt/interrupt.asm` | IM 1 handler: FRAMES, keyboard scan, BREAK latch | HOME | pristine |
| `kernel/bank/bank.asm` | EXROM paging (depth-counted) | HOME | pristine |
| `rom/v2_ay_beep.asm` | AY beep (HOME pieces; the EXROM piece `AY_BEEP`) | both | pristine |
| `kernel/storage/storage.asm` | tape | EXROM | pristine |
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

The V2 shell (`rom/exrom_v2_shell.asm`) is adapted into `src/shell/` in Phase 5, with its own provenance note.

## Configuration

The modules are assembled in V2's production configuration (`include/leapc_rom.inc`): `V2_PRODUCTION`, `V2_COMPACT_SYSVARS`, `V2_MAINT_AY_BEEP`, `V2_MAINT_SHARED_WAIT`, `V2_MAINT_AYB_PERIOD_HOME`, `V2_MAINT_SOUND0`, `V2_FAST_REDRAW` and `STORAGE_VERSIONED`.

## Deltas

| Id | File | Change | Reason |
|---|---|---|---|
| D1 | `include/sysvars.inc` | `ORG $8000` → `ORG LEAPC_SYSVARS_BASE`. Before `PROG_AREA_START`: `LEAPC_SYSVARS_END:` and `ORG LEAPC_SRC_BASE` | Baseline memory layout (`spec.md` §3.1): system variables at `$5B00`, line store from `$7800` |
| D2 | `kernel/memory/memory.asm` | `MEM_COLD_INIT` clears from `LEAPC_COLD_CLEAR_BASE` instead of the literal `$8000` | The same layout: the cold clear covers the relocated system variables |
| D3 | `kernel/math/math.asm` | Deletions only: `MATH_UMUL16`, `MATH_UDIV16`, `MATH_MULTIPLY16`, `MATH_SIGN_PREP`, `MATH_APPLY_SIGN`, `MATH_DIVIDE16`, `MATH_SGN16`, `MATH_MOD16`, `MATH_SQRT16`, `MATH_RND16`, `MATH_RND_SEED` (351 B). Kept: `MATH_NEGATE16`, `MATH_ABS16`, `MATH_COMPARE16` | Owner decisions O1/O2 (Phase 2, `spec.md` v0.3). C's multiply and divide are the helper core's register-only routines (`src/runtime/helpers.asm`: about 1.4-2.3× faster). `SQRT16`, `SGN16` and `MULTIPLY16` have no Release 1 caller. `rand()`/`srand()` are the library's xorshift generator (`src/runtime/library.asm`). The system variables the removed routines used (`DIV_*`, `MATH_SIGN`, `SQRT_*`) stay defined in `sysvars.inc`, unused; `RND_STATE` is the library generator's state |

## Names the platform expects from Leap-C

These names are defined by Leap-C files, so the platform files themselves do not need changing.

| Name | Defined in | Meaning |
|---|---|---|
| `IO_KEY_SCAN_ROW` | `src/rom/home.asm` (page zero) | V2 production placed it in page-zero padding too |
| `VM_HALTED`, `VM_ERROR_CODE` | `include/leapc_cells.inc` (= `BRK_HALT`, `BRK_CODE`) | the BREAK latch that the ISR sets and that `AY_WAIT_FRAMES` tests (the full mechanism comes in Phase 3, `spec.md` §5.8) |
| `VM_ERR_RANGE` | `src/runtime/rtexit.asm` (= `RT_ERR_ARG`) | the beep semitone range error |
| `V2_REDRAW_SCOPE`, `V2_RD_*` | `include/leapc_cells.inc` | V2 placed these editor cells at `$BEC0`, which is source RAM in the Leap-C layout |
| `V2_FORMAT_WORD`, `PKG_ABI_WORD` | `include/leapc_rom.inc` (= `LEAPC_TAPE_VERSION` `$8C00`) | tape version word (`spec.md` §8.1) |
| `KTAB_*` | `src/rom/exrom.asm` (= the HOME routines) | as in V2 production |
| `KTAB_CALC_EXIT_TRAMPOLINE` | `src/rom/exrom.asm` (= `BANK_PAGE_EXROM_OUT`) | V2's trampoline was a bare `jp BANK_PAGE_EXROM_OUT` |

## Platform facts found while vendoring (M1.1)

- `STORAGE_SAVE`/`STORAGE_LOAD` take IX as the data pointer and destroy it, and `rom/exrom_editor.asm` uses IX too. The HOME platform modules use neither IX nor IY, which confirms `spec.md` §5.1 for the code that compiled programs call. The Phase 7 `tape_save`/`tape_load` trampolines must preserve IX (the frame base).
- The relocated system variables occupy `$5B00-$5D59` (602 B), exactly as `spec.md` §3.1 predicted.
