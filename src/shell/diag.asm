; ============================================================================
; src/shell/diag.asm -- the compiler diagnostics (EXROM; spec.md 6.3; project_plan.md Phase 6)
;
; The message of every compile error and runtime error, from a word-compressed table that
; tools/gen_diag.py builds from include/leapc_errors.inc (build/diag_text.inc: DG_MSGS, DG_WORDS).
; The shell calls DG_APPEND with the EXROM paged in, after the compile's trampoline (SH_COMPILE)
; or the run (RT_RUN) has given the paging back: it reads only its own table and writes the shell's
; report buffer, never chunk 6 (bank rule 3), so it needs no trampoline of its own.
; ============================================================================

; ============================================================================
; DG_APPEND -- append "n: MESSAGE" at DE: the number A, then the text of message key C (a compile
; error's number; DG_RT + a runtime error's). An unknown key appends "n: " only
; Out: DE -> the NUL written after it. Destroys: AF, BC, HL
; ============================================================================
DG_APPEND:
    push bc
    ld   l, a
    ld   h, 0
    call SH_APPEND_NUM
    ld   a, ':'
    ld   (de), a
    inc  de
    ld   a, ' '
    ld   (de), a
    inc  de
    pop  bc
    xor  a
    ld   (de), a                       ; (an unknown key: "n: ")
    ld   b, a                          ; B = the key before the first message's
    ld   hl, DG_MSGS
.find:                                 ; HL -> a message
    inc  b
    ld   a, (hl)
    cp   DG_END
    ret  z                             ; no such message
    inc  a
    jr   nz, .key
    inc  hl                            ; DG_KEY: its key follows
    ld   b, (hl)
    inc  hl
.key:
    ld   a, b
    cp   c
    jr   z, .word
.skip:
    bit  7, (hl)
    inc  hl
    jr   z, .skip
    jr   .find
.word:                                 ; HL -> the number of the message's next word
    push hl
    ld   a, (hl)
    and  $7F
    ld   b, a
    ld   hl, DG_WORDS
    jr   .count
.skipw:
    bit  7, (hl)
    inc  hl
    jr   z, .skipw
.count:
    djnz .skipw
.copy:                                 ; the word, and a space after it
    ld   a, (hl)
    and  $7F
    ld   (de), a
    inc  de
    bit  7, (hl)
    inc  hl
    jr   z, .copy
    ld   a, ' '
    ld   (de), a
    inc  de
    pop  hl
    bit  7, (hl)
    inc  hl
    jr   z, .word
    dec  de                            ; (the last word's space)
    xor  a
    ld   (de), a
    ret

    INCLUDE "build/diag_text.inc"
