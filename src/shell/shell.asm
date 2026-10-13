; ============================================================================
; src/shell/shell.asm -- the Leap-C shell (EXROM)
;
; M1.1: the minimal shell stub of project_plan.md section 3: cold entry, the start screen and the
; idle prompt (a key wait). Phase 5 replaces it with the shell adapted from V2's shell glue
; (editor screen, command loop, LIST/NEW/SAVE/LOAD/VERIFY/RUN, messages, chime).
; ============================================================================

; ============================================================================
; SHELL_COLD -- shell cold entry (HOME COLD_START jumps here through LEAPC_EXROM_SHELL)
; In:  chunk 6 = EXROM (BANK_EXROM_DEPTH 1), interrupts on, empty line store
; Out: does not return; waits at the idle prompt (SHELL_IDLE)
; Destroys: everything
; ============================================================================
SHELL_COLD:
    call KTAB_GFX_CLS                  ; PAPER 7 / INK 0
    ld   a, 7
    call KTAB_GFX_SET_BORDER
    ld   hl, SHELL_MSG_BANNER
    ld   bc, 0 * 256 + 0
    call KTAB_GFX_PRINT_STRING
    ld   hl, SHELL_MSG_READY
    ld   bc, 2 * 256 + 0
    call KTAB_GFX_PRINT_STRING
SHELL_IDLE:
    call KTAB_IO_READ_KEY
    jr   SHELL_IDLE

SHELL_MSG_BANNER:   DB "2068-LEAP-C",0
SHELL_MSG_READY:    DB "READY",0
