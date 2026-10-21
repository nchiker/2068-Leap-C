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
LEAPC_EXROM_LIBBIND EQU LEAPC_EXROM_BASE + 6    ; the library's binding (jp XL_BIND; HOME trampoline LIB_BIND)
LEAPC_EXROM_KEYWORD EQU LEAPC_EXROM_BASE + 9    ; keyword lookup (jp XK_KEYWORD; HOME trampoline LEX_KEYWORD)
LEAPC_EXROM_TYEQUAL EQU LEAPC_EXROM_BASE + 12   ; type compatibility (jp XT_EQUAL; HOME trampoline TY_EQUAL)
LEAPC_EXROM_DIRECTIVE EQU LEAPC_EXROM_BASE + 15 ; the preprocessor's directives (jp XP_DIRECTIVE; HOME PP_DIRECTIVE)
LEAPC_EXROM_BEEP    EQU LEAPC_EXROM_BASE + 18   ; AY_BEEP_PLAY (the library's beep(), LIB_BEEP)
LEAPC_EXROM_TAPE    EQU LEAPC_EXROM_BASE + 21   ; SH_LIBTAPE (the library's tape_save/tape_load, LIB_TAPE)
LEAPC_EXROM_FLOAT   EQU LEAPC_EXROM_BASE + 24   ; the float core (jp XF_OP; HOME F_X / F_OP, Phase 8)

; Operations of the float core (src/runtime/fpcore.asm XF_OP; src/runtime/float.asm F_OP at run time,
; CX_FOLD at compile time). Bit 7: a binary operation (its left operand at HL: a stack slot); bit 0
; of a binary one: reversed (the left operand is F_ACC, the right one at HL)
FOP_FRI         EQU 0       ; F_ACC = HL (int)
FOP_FRU         EQU 1       ; F_ACC = HL (unsigned)
FOP_TOI         EQU 2       ; HL = F_ACC truncated (its low 16 bits)
FOP_NEG         EQU 3       ; F_ACC = -F_ACC
FOP_INC         EQU 4       ; F_ACC += 1
FOP_DEC         EQU 5       ; F_ACC -= 1
FOP_PINC        EQU 6       ; F_OLD = F_ACC; F_ACC += 1
FOP_PDEC        EQU 7       ; F_OLD = F_ACC; F_ACC -= 1
FOP_FTOA        EQU 8       ; HL = the text of the float at HL with C decimals (PRINT_BUF)
FOP_ATOF        EQU 9       ; TOK_BUF = the constant at HL (compile time); HL past it
FOP_ADD         EQU $80
FOP_SUB         EQU $82
FOP_SUBR        EQU $83
FOP_MUL         EQU $84
FOP_DIV         EQU $86
FOP_DIVR        EQU $87
FOP_CMP         EQU $88     ; C: left < right, Z: equal
FOP_CMPR        EQU $89

; Tape version words the platform's STORAGE_VERSION_WORD stamps and checks (spec.md section 8.1).
; Leap-C has no package tapes; both names give the Leap-C word.
V2_FORMAT_WORD      EQU LEAPC_TAPE_VERSION
PKG_ABI_WORD        EQU LEAPC_TAPE_VERSION

    ENDIF
