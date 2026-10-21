; ============================================================================
; src/compiler/cerror.asm -- the compile error exit (spec.md section 6.3: stop at the first error)
;
; A compile entry stores its stack pointer in CC_SP (with the return address of its guarded call
; on top) and clears CC_ERRNUM. Any compiler routine that detects an error jumps to CC_ERROR,
; which unwinds to that point: the guarded call returns with carry set.
; ============================================================================

; ============================================================================
; CC_ERROR -- stop compilation with an error at the current token's line
; CC_ERROR_AT -- the same at the line in HL
; In:  A = error number (include/leapc_errors.inc); TOK_LINE (CC_ERROR) or HL (CC_ERROR_AT)
; Out: does not return to its caller: CC_ERRNUM = A, CC_ERRLINE = the line, SP = CC_SP, carry
;      set, then `ret` (to the instruction after the compile entry's guarded call); the EXROM paged
;      out (BANK_EXROM_DEPTH 0, the compiler's own paging state: an error can come from an EXROM-
;      resident compiler part, Phase 8)
; Destroys: everything (the error is in CC_ERRNUM)
; ============================================================================
CC_ERROR:
    ld   hl, (TOK_LINE)
CC_ERROR_AT:
    ld   (CC_ERRNUM), a
    ld   (CC_ERRLINE), hl
    xor  a
    ld   (BANK_EXROM_DEPTH), a
    out  (PORT_BANK_HOME), a           ; chunk 6 = RAM
    ld   sp, (CC_SP)
    scf
    ret
