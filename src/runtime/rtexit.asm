; ============================================================================
; src/runtime/rtexit.asm -- runtime errors (spec.md sections 5.7 and 5.9)
;
; M1.1 holds only the error exit that the retained platform needs (AY_BEEP_PERIOD's range check,
; V2's VM_ERR_RANGE). Program start, normal exit, BREAK and the exit normalisation (sound,
; display, paging) are added by M1.3 and Phase 3 in this file.
; ============================================================================

; ============================================================================
; RT_ERR_ARG -- runtime error 4, invalid library argument
; RT_ERROR -- end the running program with runtime error A
; In:  A = error number (RT_ERROR); RUN_SP = the stack pointer recorded by the program start,
;      whose top is the return address into the shell's run entry
; Out: does not return to its caller: RT_ERRNUM = the error, SP = RUN_SP, `ret`
; Destroys: everything except A
; ============================================================================
RT_ERR_ARG:
    ld   a, RTE_ARG
RT_ERROR:
    ld   (RT_ERRNUM), a
    ld   sp, (RUN_SP)
    ret

VM_ERR_RANGE    EQU RT_ERR_ARG      ; platform name (rom/v2_ay_beep.asm: BEEP semitone range)
