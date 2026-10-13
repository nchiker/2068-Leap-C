; ============================================================================
; src/rom/exrom.asm -- the Leap-C EXROM (8 KB, mapped at $C000-$DFFF while paged in)
;
; Linked against the HOME build it is paired with: build/home_exports.inc (tools/gen_exports.py,
; names from src/rom/home_exports.txt) gives the HOME addresses EXROM code calls.
; ============================================================================
    INCLUDE "include/hardware.inc"
    INCLUDE "include/leapc_layout.inc"
    INCLUDE "include/leapc_rom.inc"
    INCLUDE "include/sysvars.inc"
    INCLUDE "include/leapc_cells.inc"
    INCLUDE "include/keys.inc"
    IFDEF LEAPC_TEST
    INCLUDE "build/test/home_exports.inc"
    ELSE
    INCLUDE "build/home_exports.inc"
    ENDIF
; The platform's EXROM modules call HOME through V2's KTAB names; in V2 production they are the
; HOME routines themselves (include/v2_ktab.inc), as here.
KTAB_MEM_FILL_ZERO          EQU MEM_FILL_ZERO
KTAB_MEM_SHIFT_UP           EQU MEM_SHIFT_UP
KTAB_MEM_SHIFT_DOWN         EQU MEM_SHIFT_DOWN
KTAB_MEM_LINE_DELETE_RANGE  EQU MEM_LINE_DELETE_RANGE
KTAB_IO_READ_KEY            EQU IO_READ_KEY
KTAB_GFX_CLS                EQU GFX_CLS
KTAB_GFX_PRINT_STRING       EQU GFX_PRINT_STRING
KTAB_GFX_INVERT_ATTR        EQU GFX_INVERT_ATTR
KTAB_GFX_SET_BORDER         EQU GFX_SET_BORDER
; The calculator leaves through `jp KTAB_CALC_EXIT_TRAMPOLINE` with its return address pushed; V2's
; HOME trampoline is a bare `jp BANK_PAGE_EXROM_OUT`, so the routine itself is the target.
KTAB_CALC_EXIT_TRAMPOLINE   EQU BANK_PAGE_EXROM_OUT
    DEVICE NOSLOT64K

    ORG LEAPC_EXROM_BASE
; ---------------------------------------------------------------- entry points + shell
COMP_XSHELL_BEGIN:
    ASSERT $ == LEAPC_EXROM_SHELL
    jp   SHELL_COLD
    INCLUDE "src/shell/shell.asm"
COMP_XSHELL_END:

; ---------------------------------------------------------------- retained platform (spec.md 2.1)
COMP_XPLATFORM_BEGIN:
    INCLUDE "rom/exrom_editor.asm"
    INCLUDE "kernel/storage/storage.asm"
    INCLUDE "rom/exrom_sound.asm"
    INCLUDE "rom/v2_ay_beep.asm"
; integer formatting, then (from BASIC_FLOAT_TO_STRING_EXROM) float formatting, which with the
; calculator after it forms the optional FP component (spec.md 4.9)
    INCLUDE "rom/exrom_format.asm"
    INCLUDE "rom/exrom_calc.asm"
COMP_XPLATFORM_END:

LEAPC_EXROM_CODE_END:
    ASSERT $ <= LEAPC_EXROM_END
    DS   LEAPC_EXROM_END - $, $FF
    IFDEF LEAPC_TEST
    SAVEBIN "build/test/leapc_exrom.bin", LEAPC_EXROM_BASE, LEAPC_EXROM_END - LEAPC_EXROM_BASE
    ELSE
    SAVEBIN "build/leapc_exrom.bin", LEAPC_EXROM_BASE, LEAPC_EXROM_END - LEAPC_EXROM_BASE
    ENDIF
