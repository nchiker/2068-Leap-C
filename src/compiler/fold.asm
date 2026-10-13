; ============================================================================
; src/compiler/fold.asm -- constant folding (spec.md 4.4)
;
; The arithmetic of the binary operators on 16-bit constants, as the generated code computes it at
; run time: two's complement wraparound, signed or unsigned division, comparisons and shifts by the
; operation's type, division by zero gives 0 (the kept ROM math routines; spec.md 4.4).
;
; EXROM-resident since M1.3 (budget ledger L5): it is pure arithmetic on registers that touches no
; RAM in chunk 6, so it runs with the EXROM paged in, through the HOME trampoline CX_FOLD
; (src/compiler/codegen.asm), like the diagnostics of bank rule 3.
; ============================================================================

; ============================================================================
; XC_FOLD -- the value of `left op right` for constants (called through CX_FOLD)
; In:  A = operator token (TK_PLUS .. TK_GE), DE = left, HL = right, C bit 0 = 1: unsigned
;      operation (division, modulus, >>, comparisons)
; Out: HL = the result (comparisons and && ||: 0 or 1)
; Destroys: AF, BC, DE
; ============================================================================
XC_FOLD:
    ld   b, a
    cp   TK_PLUS
    jr   z, .add
    cp   TK_MINUS
    jr   z, .sub
    cp   TK_STAR
    jr   z, .mul
    cp   TK_SLASH
    jr   z, .div
    cp   TK_PERCENT
    jr   z, .div
    cp   TK_AMP
    jr   z, .and
    cp   TK_BAR
    jr   z, .or
    cp   TK_CARET
    jr   z, .xor
    cp   TK_SHL
    jp   z, .shift
    cp   TK_SHR
    jr   z, .shift
    cp   TK_ANDAND
    jr   z, .andand
    cp   TK_OROR
    jr   z, .oror
    bit  0, c                          ; comparisons: signed = unsigned with the sign bits flipped
    jr   nz, .ucmp
    ld   a, d
    xor  $80
    ld   d, a
    ld   a, h
    xor  $80
    ld   h, a
.ucmp:
    ex   de, hl
    or   a
    sbc  hl, de                        ; left - right
    ld   a, 4                          ; less
    jr   c, .outcome
    ld   a, 2                          ; equal
    jr   z, .outcome
    ld   a, 1                          ; greater
.outcome:
    ld   c, a
    ld   hl, CX_CMP_TABLE
.find:
    ld   a, (hl)
    inc  hl
    cp   b
    ld   a, (hl)
    inc  hl
    jr   nz, .find
    and  c                             ; true for this outcome?
.bool:                                 ; HL = NZ ? 1 : 0
    ld   hl, 0
    ret  z
    inc  l
    ret
.add:
    add  hl, de
    ret
.sub:
    ex   de, hl
    or   a
    sbc  hl, de
    ret
.mul:
    ld   b, h
    ld   c, l
    jp   MATH_UMUL16                   ; (the low 16 bits are the same signed or unsigned)
.and:
    ld   a, h
    and  d
    ld   h, a
    ld   a, l
    and  e
    ld   l, a
    ret
.or:
    ld   a, h
    or   d
    ld   h, a
    ld   a, l
    or   e
    ld   l, a
    ret
.xor:
    ld   a, h
    xor  d
    ld   h, a
    ld   a, l
    xor  e
    ld   l, a
    ret
.andand:
    ld   a, d
    or   e
    jr   z, .bool
    ld   a, h
    or   l
    jr   .bool
.oror:
    ld   a, d
    or   e
    or   h
    or   l
    jr   .bool
.div:                                  ; A = TK_SLASH or TK_PERCENT
    ex   de, hl                        ; HL = dividend, DE = divisor
    bit  0, c
    jr   nz, .udiv
    cp   TK_SLASH
    jp   z, MATH_DIVIDE16              ; truncates toward zero
    jp   MATH_MOD16                    ; the sign of the dividend
.udiv:
    ld   b, d
    ld   c, e
    push af
    call MATH_UDIV16                   ; HL = quotient, DE = remainder
    pop  af
    cp   TK_SLASH
    ret  z
    ex   de, hl
    ret
.shift:                                ; counts above 15 shift everything out
    ld   a, h
    or   a
    ld   a, 16
    jr   nz, .count
    ld   a, l
    cp   16
    jr   c, .count
    ld   a, 16
.count:
    ex   de, hl                        ; HL = the value
    or   a
    ret  z
    ld   e, a
.bit:
    ld   a, b
    cp   TK_SHL
    jr   nz, .right
    add  hl, hl
    jr   .next
.right:
    bit  0, c
    jr   z, .arith
    srl  h                             ; unsigned: logical
    jr   .low
.arith:
    sra  h                             ; signed: arithmetic (spec.md 4.4)
.low:
    rr   l
.next:
    dec  e
    jr   nz, .bit
    ret

; comparison operator, outcomes for which it is true: 4 = less, 2 = equal, 1 = greater
CX_CMP_TABLE:
    DB   TK_LT, 4, TK_GT, 1, TK_EQ, 2, TK_NE, 5, TK_LE, 6, TK_GE, 3
