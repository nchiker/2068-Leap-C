; ============================================================================
; include/leapc_rom.inc -- build configuration and the HOME/EXROM contract, shared by both images
;
; The platform modules are assembled in their V2 production configuration (spec.md section 2.1):
;   V2_PRODUCTION            leave out the legacy-only routines
;   V2_COMPACT_SYSVARS       leave out the V1-only system variables
;   V2_MAINT_AY_BEEP         AY BEEP (the port-$FE beeper module is not used)
;   V2_MAINT_SHARED_WAIT     one frame wait (AY_WAIT_FRAMES, HOME) for pause and beep; BREAK ends it
;   V2_MAINT_AYB_PERIOD_HOME AY_BEEP_PERIOD and its table in HOME
;   V2_MAINT_SOUND0          SOUND accepts register 0
;   V2_FAST_REDRAW           the editor engine's selective redraw
;   STORAGE_VERSIONED        tapes carry and check a version word (LEAPC_TAPE_VERSION)
; ============================================================================

    IFNDEF LEAPC_ROM_INC
    DEFINE LEAPC_ROM_INC

    DEFINE V2_PRODUCTION
    DEFINE V2_COMPACT_SYSVARS
    DEFINE V2_MAINT_AY_BEEP
    DEFINE V2_MAINT_SHARED_WAIT
    DEFINE V2_MAINT_AYB_PERIOD_HOME
    DEFINE V2_MAINT_SOUND0
    DEFINE V2_FAST_REDRAW
    DEFINE STORAGE_VERSIONED

LEAPC_HOME_END      EQU $4000
LEAPC_EXROM_BASE    EQU $C000   ; EXROM is mapped into chunk 6 while paged in
LEAPC_EXROM_END     EQU $E000

; EXROM entry points called from HOME (fixed addresses at the start of the EXROM image)
LEAPC_EXROM_SHELL   EQU LEAPC_EXROM_BASE        ; cold entry of the shell (jp)
LEAPC_EXROM_FOLD    EQU LEAPC_EXROM_BASE + 3    ; constant folding (jp XC_FOLD; HOME trampoline CX_FOLD)

; Tape version words the platform's STORAGE_VERSION_WORD stamps and checks (spec.md section 8.1).
; Leap-C has no package tapes; both names give the Leap-C word.
V2_FORMAT_WORD      EQU LEAPC_TAPE_VERSION
PKG_ABI_WORD        EQU LEAPC_TAPE_VERSION

    ENDIF
