; ============================================================================
; src/runtime/rtexit.asm -- program start, exit and runtime errors (spec.md 5.7, 5.9)
;
; M1.3 part: the minimal program start and exit: the compiled program runs from RT_RUN with
; chunk 6 paged out, and returns there from main, or from anywhere through a runtime error.
; Phase 3 adds the exit normalisation (sound, display), BREAK and the shell's stack.
; ============================================================================

; ============================================================================
; RT_RUN -- run the compiled program (spec.md 5.7, minimal)
; In:  RUN_MAIN / RUN_VOID from the last successful compile (CC_PROGRAM); any paging depth
; Out: A = 0 and HL = main's return value (0 for void main), or A = the runtime error (RT_ERRNUM).
;      BANK_EXROM_DEPTH and the paging are as on entry; IX kept.
; Destroys: F, BC, DE, IY not used
; ============================================================================
RT_RUN:
    push ix
    ld   a, (BANK_EXROM_DEPTH)
    push af
    or   a
    jr   z, .out
    ld   a, 1                          ; page the EXROM out whatever the depth: the program's
    ld   (BANK_EXROM_DEPTH), a         ; code and data may be in chunk 6
    call BANK_PAGE_EXROM_OUT
.out:
    call .main
    pop  af
    or   a
    jr   z, .done
    push af
    xor  a
    ld   (BANK_EXROM_DEPTH), a
    call BANK_PAGE_EXROM_IN            ; (keeps HL)
    pop  af
    ld   (BANK_EXROM_DEPTH), a
.done:
    pop  ix
    ld   a, (RT_ERRNUM)
    ret
.main:                                 ; a runtime error returns from here (RUN_SP)
    ld   (RUN_SP), sp
    xor  a
    ld   (RT_ERRNUM), a
    ld   hl, (RUN_MAIN)
    call RT_CALLHL
.back:                                 ; (main has returned: the test harness checks IX and SP here)
    ld   a, (RUN_VOID)
    or   a
    ret  z
    ld   hl, 0
    ret

; ============================================================================
; RT_ERR_STACK -- runtime error 1, stack overflow (ENTER)
; RT_ERR_ARG -- runtime error 4, invalid library argument
; RT_ERROR -- end the running program with runtime error A
; In:  A = error number (RT_ERROR); RUN_SP = the stack pointer recorded by the program start,
;      whose top is the return address into the run entry
; Out: does not return to its caller: RT_ERRNUM = the error, SP = RUN_SP, `ret`
; Destroys: everything except A
; ============================================================================
RT_ERR_STACK:
    ld   a, RTE_STACK
    DB   $21                           ; (`ld hl,nn` swallows the next `ld a,n`)
RT_ERR_ARG:
    ld   a, RTE_ARG
RT_ERROR:
    ld   (RT_ERRNUM), a
    ld   sp, (RUN_SP)
    ret

VM_ERR_RANGE    EQU RT_ERR_ARG      ; platform name (rom/v2_ay_beep.asm: BEEP semitone range)
