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
    INCLUDE "include/leapc_tokens.inc"
    INCLUDE "include/leapc_errors.inc"
    INCLUDE "include/leapc_lib.inc"     ; (the constants: LIB, the binding of a loaded library's exports)
    ASSERT LX_TYPE == STORAGE_EXTENSION_TYPE && LX_BASE == LEAPC_IMG3_BASE && LX_END == LEAPC_IMG3_END
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
KTAB_IO_READ_KEY            EQU IO_READ_KEY
KTAB_GFX_INVERT_ATTR        EQU GFX_INVERT_ATTR
KTAB_GFX_SET_BORDER         EQU GFX_SET_BORDER
; The calculator leaves through `jp KTAB_CALC_EXIT_TRAMPOLINE` with its return address pushed; V2's
; HOME trampoline is a bare `jp BANK_PAGE_EXROM_OUT`, so the routine itself is the target.
KTAB_CALC_EXIT_TRAMPOLINE   EQU BANK_PAGE_EXROM_OUT
    DEVICE NOSLOT64K

    ORG LEAPC_EXROM_BASE
; ---------------------------------------------------------------- entry points (fixed addresses)
COMP_XSHELL_BEGIN:
    ASSERT $ == LEAPC_EXROM_SHELL
    jp   SHELL_COLD
COMP_XCOMP_ENTRY:
    ASSERT $ == LEAPC_EXROM_FOLD
    jp   XC_FOLD
    ASSERT $ == LEAPC_EXROM_LIBBIND
    jp   XL_BIND
    ASSERT $ == LEAPC_EXROM_KEYWORD
    jp   XK_KEYWORD
    ASSERT $ == LEAPC_EXROM_TYEQUAL
    jp   XT_EQUAL
    ASSERT $ == LEAPC_EXROM_DIRECTIVE
    jp   XP_DIRECTIVE
COMP_XCOMP_ENTRY_END:
    ASSERT $ == LEAPC_EXROM_BEEP
    jp   AY_BEEP_PLAY                  ; beep() (HOME LIB_BEEP: page in, play, page out)
    ASSERT $ == LEAPC_EXROM_TAPE
    jp   SH_LIBTAPE                    ; tape_save(), tape_load() (HOME LIB_TAPE: page in, call, page out)
COMP_XFP_ENTRY:
    ASSERT $ == LEAPC_EXROM_FLOAT
    jp   XF_OP                         ; the float core (HOME F_X, F_OP; CX_FOLD at compile time)
COMP_XFP_ENTRY_END:
; ---------------------------------------------------------------- shell
    INCLUDE "src/shell/shell.asm"
    INCLUDE "src/shell/tape.asm"
COMP_XSHELL_END:
COMP_XKEYWORDS_BEGIN:
    INCLUDE "src/shell/highlight.asm"
COMP_XKEYWORDS_END:
COMP_XDIAG_BEGIN:
    INCLUDE "src/shell/diag.asm"
COMP_XDIAG_END:

; ---------------------------------------------------------------- compiler parts run through a HOME
; trampoline (bank rule 3: they never touch chunk 6)
COMP_XCOMP_BEGIN:
    INCLUDE "src/compiler/fold.asm"
    INCLUDE "src/compiler/libnames.asm"
    INCLUDE "src/compiler/keywords.asm"
    INCLUDE "src/compiler/tyequal.asm"
    INCLUDE "src/compiler/directives.asm"
COMP_XCOMP_END:

; ---------------------------------------------------------------- retained platform (spec.md 2.1)
COMP_XPLATFORM_BEGIN:
    INCLUDE "rom/exrom_editor.asm"
; the line store's insert and range delete: the editor's only callers (platform delta D11, Phase 8)
    DEFINE MEM_LINE_EDIT_ONLY
    INCLUDE "kernel/memory/memory.asm"
; the editor's text output (bold keywords, strings): its only callers (platform delta D12, Phase 8)
    DEFINE GFX_EDITOR_TEXT_ONLY
    INCLUDE "kernel/graphics/graphics.asm"
; the tape: the header logic here; its block I/O is in HOME (platform delta D9), so the platform's calls of
; STORAGE_SEND_BLOCK / STORAGE_RECEIVE_BLOCK go to the shell's callers of the HOME trampoline TAPE_BLOCK
STORAGE_SEND_BLOCK      EQU SH_TAPE_SEND
STORAGE_RECEIVE_BLOCK   EQU SH_TAPE_RECV
    DEFINE STORAGE_NO_BLOCKS
    INCLUDE "kernel/storage/storage.asm"
    INCLUDE "rom/exrom_sound.asm"
    INCLUDE "rom/v2_ay_beep.asm"
; integer formatting (V2's float formatting is left out: platform delta D10; the float core has its own)
    DEFINE LEAPC_FP_CORE
    INCLUDE "rom/exrom_format.asm"
COMP_XPLATFORM_END:

; ---------------------------------------------------------------- the float core (spec.md 4.9; Phase 8: the
; re-engineered V2 calculator, rom/exrom_calc.asm, which is no longer assembled)
COMP_XFP_BEGIN:
    INCLUDE "src/runtime/fpcore.asm"
COMP_XFP_END:

LEAPC_EXROM_CODE_END:
    ASSERT $ <= LEAPC_EXROM_END
    DS   LEAPC_EXROM_END - $, $FF
    IFDEF LEAPC_TEST
    SAVEBIN "build/test/leapc_exrom.bin", LEAPC_EXROM_BASE, LEAPC_EXROM_END - LEAPC_EXROM_BASE
    ELSE
    SAVEBIN "build/leapc_exrom.bin", LEAPC_EXROM_BASE, LEAPC_EXROM_END - LEAPC_EXROM_BASE
    ENDIF
