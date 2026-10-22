; ============================================================================
; src/runtime/fpcore.asm -- the float core: Leap-C's floating point (spec.md 4.9; Phase 8), EXROM
;
; The re-engineered V2 calculator (V2's rom/exrom_calc.asm at its tag v2.0.1-emu.1, 1,929 B, and V2's float formatting
; in rom/exrom_format.asm, 236 B: the optional FP component of spec.md 2.1). What is kept:
;   - the number format, the Sinclair 5-byte float: [exponent][sign | mantissa bits 30-24][23-16]
;     [15-8][7-0], value 0.1m x 2^(exponent - 128) (the leading 1 is implicit), 0 for exponent 0.
;     Leap-C always writes the normalised form (never the small-integer form);
;   - its role: the one numerical engine of the ROMs, used by the compiler (floating constants,
;     constant folding, through the HOME trampoline CX_FOLD) and by compiled code (through HOME's
;     F_OP / F_X, src/runtime/float.asm);
;   - its working RAM: the calculator's system variables (CALC_STACK);
;   - V2's exact fixed-point formatting (XF_FTOA: every integer digit, the decimals rounded).
; What changed: C calls each operation directly (A = FOP_*, include/leapc_rom.inc), so the RST $28
; literal-stream interpreter, its 8-slot stack and its stack operations (exchange, duplicate,
; delete, pi) are gone; the arithmetic works on a 40-bit mantissa (32 bits and a guard byte, rounded
; to nearest when packed) with byte loops instead of V2's unrolled byte moves; comparison, negation,
; the conversions both ways, decimal input and a precision for the output are new.
;
; Bank rules: it runs with the EXROM paged in and touches only the cells, the stack (an operand held
; by compiled code, an argument of printf) and the source or the compile workspace (constants): never
; chunk 6. Errors leave through HOME's F_ERR with A = the compile error (E_RANGE: overflow or
; division by zero; E_NUMBER: a malformed constant): a compile error, or runtime error 6 while a
; program runs.
; ============================================================================

FX      EQU CALC_STACK              ; unpacked: [sign $80/0][exponent][m0 m1 m2 m3][guard]
FY      EQU CALC_STACK + 7
FQ      EQU CALC_STACK + 14         ; 5 bytes: a product or quotient being built, big-endian
FDEXP   EQU CALC_STACK + 19         ; XF_ATOF: the decimal exponent (2 bytes) ...
FFLAGS  EQU CALC_STACK + 21         ; ... bit 0: a digit seen, bit 1: after the point
FMT     EQU CALC_STACK + 20         ; XF_FTOA: 20 bytes of fixed point, big-endian: 16 integer bytes,
                                    ; 4 fraction bytes (F_OLD overlaps its end: not live then)
U_S     EQU 0
U_E     EQU 1
U_M     EQU 2                       ; m0 (the most significant) .. m3
U_G     EQU 6                       ; the guard byte
    ASSERT F_OLD == CALC_STACK + 35 && FMT + 20 <= CALC_STACK + 40

; ============================================================================
; XF_OP -- an operation of the float core
; In:  A = FOP_* (include/leapc_rom.inc); F_ACC = the accumulator (packed); HL = the argument: an
;      integer (FRI, FRU), the left operand (packed) of a binary operation (bit 7 of A), the value to
;      format (FTOA, with C = the precision, 0-9), the constant's text (ATOF)
; Out: F_ACC = the result; TOI: HL; CMP, CMPR: C = left < right, Z = equal (NC NZ: greater);
;      FTOA: HL = the text (PRINT_BUF); ATOF: TOK_BUF = the value (packed), HL -> past the constant
; Errors: F_ERR with E_RANGE (overflow, division by zero), E_NUMBER (ATOF)
; Destroys: AF, BC, DE, HL (IX, IY kept)
; ============================================================================
XF_OP:
    or   a
    jp   m, XF_BIN
    push hl
    ld   hl, XF_UTAB
    add  a, a
    ld   e, a
    ld   d, 0
    add  hl, de
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    ex   (sp), hl                      ; HL = the argument again
    ret
XF_UTAB:
    DW   XF_FRI, XF_FRU, XF_TOI, XF_NEG, XF_INC, XF_DEC, XF_PINC, XF_PDEC, XF_FTOA, XF_ATOF
    ASSERT ($ - XF_UTAB) / 2 == FOP_ATOF + 1

; ---- FRI, FRU: F_ACC = HL (signed / unsigned) ----
XF_FRI:
    ld   a, h
    and  $80
    jr   z, XF_FROM
    ex   de, hl
    ld   hl, 0
    sbc  hl, de                        ; the magnitude (C is clear from `and`)
    jr   XF_FROM
XF_FRU:
    xor  a
XF_FROM:                               ; A = the sign, HL = the magnitude
    call FFROM
    jp   FPACK
; FFROM -- FX = sign A, magnitude HL, normalised. Destroys: AF, BC, HL
FFROM:
    push hl
    push af
    call FZEROX
    pop  af
    ld   (FX + U_S), a
    pop  hl
    ld   a, h
    ld   (FX + U_M), a
    ld   a, l
    ld   (FX + U_M + 1), a
    ld   a, 128 + 16
    ld   (FX + U_E), a
    jp   FNORM

; ---- TOI: HL = F_ACC truncated toward 0, its low 16 bits (int and unsigned alike) ----
XF_TOI:
    ld   hl, F_ACC
    ld   de, FX
    call FUNPK
    ld   hl, 0
    ld   a, (FX + U_E)
    sub  128
    ret  c                             ; below 0.5 (and 0)
    ret  z                             ; 0.5 .. 1
    cp   49
    jr   c, .n
    ld   a, 48                         ; beyond 2^48 the low 16 bits are 0
.n:
    ld   b, a
.bit:                                  ; the integer part's bits into HL, the top one first
    push bc
    push hl
    ld   hl, FX + U_G
    ld   b, 5
    or   a
    call FSHL
    pop  hl
    adc  hl, hl
    pop  bc
    djnz .bit
    ld   a, (FX + U_S)
    or   a
    ret  z
    ex   de, hl
    ld   hl, 0
    sbc  hl, de                        ; (C is clear from `or`)
    ret

; ---- NEG: F_ACC = -F_ACC ----
XF_NEG:
    ld   hl, F_ACC
    ld   a, (hl)
    or   a
    ret  z                             ; (0 has no sign)
    inc  hl
    ld   a, (hl)
    xor  $80
    ld   (hl), a
    ret

; ---- INC, DEC: F_ACC +- 1; PINC, PDEC: the same, F_OLD = the value before (HOME F_REST) ----
XF_PDEC:
    call XF_SAVE
XF_DEC:
    ld   hl, XF_MONE
    jr   XF_ADDK
XF_PINC:
    call XF_SAVE
XF_INC:
    ld   hl, XF_ONE
XF_ADDK:
    ld   a, FOP_ADD
    jr   XF_BIN
XF_SAVE:
    ld   hl, F_ACC
    ld   de, F_OLD
    ld   bc, 5
    ldir
    ret
XF_ONE:  DB $81, $00, 0, 0, 0          ; 1.0
XF_MONE: DB $81, $80, 0, 0, 0          ; -1.0
XF_POW10:                              ; 10^1 .. 10^13, exact (5^13 < 2^32)
    DB   $84, $20, $00, $00, $00
    DB   $87, $48, $00, $00, $00
    DB   $8A, $7A, $00, $00, $00
    DB   $8E, $1C, $40, $00, $00
    DB   $91, $43, $50, $00, $00
    DB   $94, $74, $24, $00, $00
    DB   $98, $18, $96, $80, $00
    DB   $9B, $3E, $BC, $20, $00
    DB   $9E, $6E, $6B, $28, $00
    DB   $A2, $15, $02, $F9, $00
    DB   $A5, $3A, $43, $B7, $40
    DB   $A8, $68, $D4, $A5, $10
    DB   $AC, $11, $84, $E7, $2A

; ============================================================================
; XF_BIN -- a binary operation: F_ACC = left op right, or a comparison
; In:  A = FOP_ADD .. FOP_CMPR: bits 1-3 the operation (0 +, 1 -, 2 *, 3 /, 4 compare), bit 0: the
;      left operand is F_ACC and the right one (HL) (else the left one is (HL), the right F_ACC)
; ============================================================================
XF_BIN:
    ld   de, F_ACC
    rra                                ; C: reversed
    jr   nc, .ord
    ex   de, hl
.ord:
    push af
    push de                            ; the right operand
    ld   de, FX
    call FUNPK                         ; FX = the left operand
    pop  hl
    ld   de, FY
    call FUNPK                         ; FY = the right operand
    pop  af
    and  7
    jr   z, .add
    dec  a
    jr   z, .sub
    dec  a
    jr   z, .mul
    dec  a
    jp   nz, FCMP                      ; (flags: the result)
    call FDIV
    jr   .pack
.mul:
    call FMUL
    jr   .pack
.sub:
    ld   hl, FY + U_S
    ld   a, (hl)
    xor  $80
    ld   (hl), a
.add:
    call FADD
.pack:
    jp   FPACK

; ============================================================================
; FUNPK -- unpack a float
; In:  HL -> 5 packed bytes, DE -> 7 bytes for it unpacked. Out: HL -> its sign byte
; Destroys: AF, BC, DE
; ============================================================================
FUNPK:
    push de
    inc  de
    ld   bc, 5
    ldir                               ; [e][sign | m0][m1][m2][m3]
    xor  a
    ld   (de), a                       ; the guard
    pop  hl
    inc  hl
    or   (hl)                          ; A = e: Z for 0
    inc  hl
    jr   z, .zero
    ld   a, (hl)
    set  7, (hl)                       ; m0's leading 1
    and  $80
.zero:                                 ; (0: sign 0)
    dec  hl
    dec  hl
    ld   (hl), a
    ret

; ============================================================================
; FPACK -- F_ACC = FX, rounded to nearest on the guard's top bit
; Errors: E_RANGE (the rounding carries the exponent beyond 255)
; Destroys: AF, BC, DE, HL
; ============================================================================
FPACK:
    ld   hl, FX + U_G
    bit  7, (hl)
    jr   z, .pack
    ld   b, 4
.rnd:
    dec  hl
    inc  (hl)
    jr   nz, .pack
    djnz .rnd
    ld   (hl), $80                     ; 0.111...1 + 1 ulp = 1.000: the mantissa $80000000, e + 1
    dec  hl
    inc  (hl)
    jr   z, XF_E_RANGE
.pack:
    ld   de, F_ACC
    ld   hl, FX + U_E
    ld   a, (hl)
    or   a
    jr   z, .zero
    ld   bc, 5
    ldir                               ; e, m0 .. m3
    ld   hl, F_ACC + 1
    ld   a, (hl)
    and  $7F
    ld   b, a
    ld   a, (FX + U_S)
    or   b
    ld   (hl), a                       ; the sign in m0's top bit
    ret
.zero:                                 ; (A = 0)
    ex   de, hl
    ld   b, 5
FZERO:                                 ; HL -> B bytes = 0. Destroys: AF, B, HL
    xor  a
.z:
    ld   (hl), a
    inc  hl
    djnz .z
    ret
FZEROX:                                ; FX = 0. Destroys: AF, B, HL
    ld   hl, FX
    ld   b, 7
    jr   FZERO
XF_E_RANGE:
    ld   a, E_RANGE
    jp   F_ERR

; ============================================================================
; FNORM -- FX normalised: the mantissa shifted left until its top bit is set, the exponent lowered;
; 0 when the mantissa is 0 or the exponent falls below 1
; Destroys: AF, BC, HL
; ============================================================================
FNORM:
    ld   hl, FX + U_M
    ld   b, 5
    xor  a
.t:
    or   (hl)
    inc  hl
    djnz .t
    jr   z, FZEROX
.l:
    ld   a, (FX + U_M)
    rla
    ret  c
    ld   hl, FX + U_E
    dec  (hl)
    jr   z, FZEROX
    ld   hl, FX + U_G
    ld   b, 5
    or   a
    call FSHL
    jr   .l

; ============================================================================
; Multi-byte helpers on big-endian numbers
; FSHL -- (HL) = the least significant byte of B bytes: shift them left one bit, carry in and out
; FSHR -- (HL) = the most significant byte of B bytes: shift them right one bit, carry in and out
; FADDN, FSUBN -- (DE) += / -= (HL), B bytes, HL and DE at the least significant bytes: C = the
;      carry or borrow out
; Destroys: F, B, DE, HL (FADDN, FSUBN: and A)
; ============================================================================
FSHL:
    rl   (hl)
    dec  hl
    djnz FSHL
    ret
FSHR:
    rr   (hl)
    inc  hl
    djnz FSHR
    ret
FADDN:
    or   a
.l:
    ld   a, (de)
    adc  a, (hl)
    ld   (de), a
    dec  hl
    dec  de
    djnz .l
    ret
FSUBN:
    or   a
.l:
    ld   a, (de)
    sbc  a, (hl)
    ld   (de), a
    dec  hl
    dec  de
    djnz .l
    ret

; ============================================================================
; FADD -- FX += FY (signed magnitudes)
; Errors: E_RANGE. Destroys: AF, BC, DE, HL
; ============================================================================
FADD:
    ld   a, (FY + U_E)
    or   a
    ret  z                             ; x + 0
    ld   a, (FX + U_E)
    or   a
    jr   z, .y                         ; 0 + y
    ld   hl, FX + U_E                  ; the larger magnitude in FX
    ld   de, FY + U_E
    ld   b, 6
.c:
    ld   a, (de)
    cp   (hl)
    jr   nz, .cd
    inc  hl
    inc  de
    djnz .c
    jr   .al
.cd:
    call nc, FSWAP                     ; FY's is larger
.al:
    ld   a, (FY + U_E)
    ld   b, a
    ld   a, (FX + U_E)
    sub  b                             ; the exponents' difference
    cp   40
    ret  nc                            ; FY lies below the guard byte
    or   a
    jr   z, .same
    ld   b, a
.sh:
    push bc
    ld   hl, FY + U_M
    ld   b, 5
    or   a
    call FSHR
    pop  bc
    djnz .sh
.same:
    ld   a, (FY + U_S)
    ld   hl, FX + U_S
    xor  (hl)
    ld   hl, FY + U_G
    ld   de, FX + U_G
    ld   b, 5
    jr   nz, .sub
    call FADDN
    ret  nc
    ld   hl, FX + U_M                  ; a carry: one bit more
    ld   b, 5
    call FSHR                          ; (the carry comes in at the top)
    ld   hl, FX + U_E
    inc  (hl)
    ret  nz
    jp   XF_E_RANGE
.sub:
    call FSUBN
    jp   FNORM
.y:
    ld   hl, FY
    ld   de, FX
    ld   bc, 7
    ldir
    ret
FSWAP:                                 ; FX <-> FY
    ld   hl, FX
    ld   de, FY
    ld   b, 7
.s:
    ld   a, (de)
    ld   c, (hl)
    ld   (hl), a
    ld   a, c
    ld   (de), a
    inc  hl
    inc  de
    djnz .s
    ret

; ============================================================================
; FMUL -- FX *= FY: 32 x 32 bits, the product's top 40 bits
; FDIV -- FX /= FY: 40 quotient bits by restoring division
; Errors: E_RANGE (overflow; FDIV: division by 0). Destroys: AF, BC, DE, HL
; ============================================================================
FMUL:
    ld   a, (FX + U_E)
    or   a
    ret  z
    ld   a, (FY + U_E)
    or   a
    jp   z, FZEROX
    call FSIGN
    add  hl, de
    push hl                            ; ex + ey
    ld   hl, FQ
    ld   b, 5
    call FZERO
    ld   b, 32
.bit:
    push bc
    ld   hl, FY + U_M
    ld   b, 4
    or   a
    call FSHR                          ; C = the multiplier's next bit, the lowest first
    jr   nc, .no
    ld   hl, FX + U_M + 3
    ld   de, FQ + 3
    ld   b, 4
    call FADDN                         ; (C = the carry out)
.no:
    ld   hl, FQ
    ld   b, 5
    call FSHR
    pop  bc
    djnz .bit
    ld   de, -128
    jr   FDONE
FDIV:
    ld   a, (FY + U_E)
    or   a
    jp   z, XF_E_RANGE                 ; division by 0
    ld   a, (FX + U_E)
    or   a
    ret  z
    call FSIGN
    or   a
    sbc  hl, de
    push hl                            ; ex - ey
    ld   hl, FQ
    ld   b, 5
    call FZERO
    ld   bc, 40 << 8                   ; B = the bits, C = the remainder's 33rd bit
.bit:
    push bc
    ld   hl, FY + U_M + 3
    ld   de, FX + U_M + 3
    ld   b, 4
    call FSUBN                         ; R -= D
    pop  bc
    jr   nc, .one
    bit  0, c
    jr   nz, .one                      ; R had a 33rd bit: it was larger
    push bc
    ld   hl, FY + U_M + 3
    ld   de, FX + U_M + 3
    ld   b, 4
    call FADDN                         ; restored
    pop  bc
    or   a                             ; this bit: 0
    jr   .q
.one:
    scf
.q:
    push bc
    ld   hl, FQ + 4
    ld   b, 5
    call FSHL                          ; Q = Q << 1 | the bit
    ld   hl, FX + U_M + 3
    ld   b, 4
    or   a
    call FSHL                          ; R <<= 1
    pop  bc
    ld   c, 0
    rl   c                             ; C = its 33rd bit
    djnz .bit
    ld   de, 129                       ; the first bit has the weight 2^0
FDONE:                                 ; FX's mantissa = FQ, exponent (SP) + DE
    pop  hl
    add  hl, de
    push hl
    ld   hl, FQ
    ld   de, FX + U_M
    ld   bc, 5
    ldir
    pop  hl
    ld   a, (FX + U_M)                 ; at most one place to normalise
    rla
    jr   c, .n
    dec  hl
    push hl
    ld   hl, FX + U_G
    ld   b, 5
    or   a
    call FSHL
    pop  hl
.n:
    ld   a, h
    or   a
    jr   nz, .out
    or   l
    jp   z, FZEROX                     ; below the range: 0
    ld   (FX + U_E), a
    ret
.out:
    jp   m, FZEROX
    jp   XF_E_RANGE
; FSIGN -- FX's sign = the product's or quotient's; HL = ex, DE = ey. Destroys: AF, DE, HL
FSIGN:
    ld   hl, FX + U_S
    ld   a, (FY + U_S)
    xor  (hl)
    ld   (hl), a
    ld   a, (FX + U_E)
    ld   l, a
    ld   h, 0
    ld   a, (FY + U_E)
    ld   e, a
    ld   d, h
    ret

; ============================================================================
; FCMP -- compare FX with FY. Out: C = FX < FY, Z = equal, NC NZ = FX > FY. Destroys: AF, B, DE, HL
; ============================================================================
FCMP:
    ld   a, (FY + U_S)
    ld   hl, FX + U_S
    cp   (hl)
    ret  nz                            ; the signs differ: the negative one is smaller
    ld   de, FY + U_E
    inc  hl
    or   a
    jr   z, .c
    ex   de, hl                        ; both negative: the larger magnitude is the smaller value
.c:
    ld   b, 5
.byte:
    ld   a, (hl)
    ex   de, hl
    cp   (hl)
    ex   de, hl
    ret  nz
    inc  hl
    inc  de
    djnz .byte
    ret

; ============================================================================
; FMUL10 -- the B bytes big-endian ending at (HL) times 10, plus C. Out: A = the carry out (the
;      digit). Destroys: AF, BC, DE, HL
; FDIV10 -- the B bytes big-endian from (HL) divided by 10. Out: A = the remainder. Destroys: AF,
;      BC, HL
; ============================================================================
FMUL10:
    ld   a, (hl)
    push hl
    ld   l, a
    ld   h, 0
    ld   d, h
    ld   e, l
    add  hl, hl
    add  hl, hl
    add  hl, de
    add  hl, hl                        ; the byte x 10 ...
    ld   e, c
    add  hl, de                        ; ... + the carry
    ld   c, h
    ld   a, l
    pop  hl
    ld   (hl), a
    dec  hl
    djnz FMUL10
    ld   a, c
    ret
FDIV10:
    xor  a
.byte:
    push bc
    ld   c, (hl)
    ld   b, 8
.bit:
    sla  c
    rla
    cp   10
    jr   c, .z
    sub  10
    inc  c
.z:
    djnz .bit
    ld   (hl), c
    inc  hl
    pop  bc
    djnz .byte
    ret

; ============================================================================
; XF_FTOA -- the text of a float with C decimals (printf's %f): [-]digits[.digits]
; In:  HL -> the float (packed), C = the precision (0-9)
; Out: HL -> the text in PRINT_BUF (NUL-terminated): every integer digit, the decimals rounded half
;      up (V2's exact method: the value as 128.32 bits of fixed point, integer arithmetic only)
; ============================================================================
XF_FTOA:
    push bc
    ld   de, FX
    call FUNPK
    ld   hl, FMT
    ld   b, 20
    call FZERO
    ld   a, (FX + U_E)
    or   a
    jr   z, .round                     ; 0
    ld   hl, FX + U_M
    ld   de, FMT + 16
    ld   bc, 4
    ldir                               ; the fraction 0.m
    ld   a, (FX + U_E)
    sub  128
    jr   z, .round
    jr   c, .right
    ld   b, a                          ; x 2^n: n bits left
.sl:
    push bc
    ld   hl, FMT + 19
    ld   b, 20
    or   a
    call FSHL
    pop  bc
    djnz .sl
    jr   .round
.right:
    neg
    cp   33
    jr   nc, .clear                    ; below 2^-32
    ld   b, a
.sr:
    push bc
    ld   hl, FMT + 16
    ld   b, 4
    or   a
    call FSHR
    pop  bc
    djnz .sr
    jr   .round
.clear:
    ld   hl, FMT + 16
    ld   b, 4
    call FZERO
.round:                                ; + 0.5 x 10^-p (2^31 / 10^p as a fraction)
    ld   hl, FQ
    ld   b, 4
    call FZERO
    ld   a, $80
    ld   (FQ), a
    pop  bc
    push bc
    inc  c
.rp:
    dec  c
    jr   z, .radd
    ld   hl, FQ
    ld   b, 4
    push bc
    call FDIV10
    pop  bc
    jr   .rp
.radd:
    ld   hl, FQ + 3
    ld   de, FMT + 19
    ld   b, 4
    call FADDN
    ld   b, 16
.carry:
    ld   a, (de)
    adc  a, 0
    ld   (de), a
    dec  de
    djnz .carry
    pop  bc                            ; C = the precision
    ld   de, PRINT_BUF + 40
    ld   a, c
    or   a
    jr   z, .int                       ; no point
    ld   a, '.'
    ld   (de), a
.frac:                                 ; the decimals: fraction x 10, the carry out
    inc  de
    push bc
    push de
    ld   hl, FMT + 19
    ld   bc, 4 << 8
    call FMUL10
    pop  de
    pop  bc
    add  a, '0'
    ld   (de), a
    dec  c
    jr   nz, .frac
    inc  de
.int:
    xor  a
    ld   (de), a                       ; NUL
    ld   de, PRINT_BUF + 40
.id:                                   ; the integer digits, right to left
    dec  de
    push de
    ld   hl, FMT
    ld   b, 16
    call FDIV10
    pop  de
    add  a, '0'
    ld   (de), a
    ld   hl, FMT
    ld   b, 16
    xor  a
.iz:
    or   (hl)
    inc  hl
    djnz .iz
    jr   nz, .id
    ex   de, hl
    ld   a, (FX + U_S)
    or   a
    ret  z
    dec  hl
    ld   (hl), '-'
    ret

; ============================================================================
; XF_ATOF -- a decimal floating constant (compile time; spec.md 4.1): digits, an optional point
; and digits, an optional exponent (e or E, an optional sign, digits), an optional suffix f F l L
; In:  HL -> its first character (a digit or the point)
; Out: TOK_BUF = its value (packed, rounded to nearest per step), HL -> the character after it
; Errors: E_NUMBER (no digit, an exponent without digits, a letter, digit, `_` or `.` after it),
;      E_RANGE (beyond the range; below it: 0)
; ============================================================================
XF_ATOF:
    push hl
    ld   hl, FQ                        ; N = 0: the digits as a 32-bit integer
    ld   b, 4
    call FZERO
    ld   hl, 0
    ld   (FDEXP), hl
    xor  a
    ld   (FFLAGS), a
    pop  hl
.dig:
    ld   a, (hl)
    cp   '.'
    jr   z, .dot
    sub  '0'
    cp   10
    jr   nc, .mant
    inc  hl
    push hl
    ld   c, a
    ld   hl, FFLAGS
    set  0, (hl)                       ; a digit
    ld   a, (FQ)
    cp   $19                           ; N x 10 + 9 still fits in 32 bits?
    jr   nc, .full
    ld   hl, FQ + 3
    ld   b, 4
    call FMUL10                        ; N = N x 10 + the digit
    ld   a, (FFLAGS)
    and  2
    ld   hl, -1
    jr   nz, .exp                      ; in the fraction: 10^-1 more
    jr   .next
.full:                                 ; N is full: a digit before the point is 10^1 more
    ld   a, (FFLAGS)
    and  2
    ld   hl, 1
    jr   z, .exp
.next:
    pop  hl
    jr   .dig
.exp:
    ld   de, (FDEXP)
    add  hl, de
    ld   (FDEXP), hl
    jr   .next
.dot:
    inc  hl
    ld   a, (FFLAGS)
    xor  2
    ld   (FFLAGS), a
    and  2
    jr   nz, .dig                      ; (a second point: no longer part of it)
    dec  hl
.mant:
    ld   a, (FFLAGS)
    rra
    jp   nc, .bad                      ; no digit
    ld   a, (hl)
    or   $20
    cp   'e'
    jr   nz, .suffix
    inc  hl
    ld   c, 0                          ; the exponent's sign
    ld   a, (hl)
    cp   '+'
    jr   z, .esign
    cp   '-'
    jr   nz, .edig
    dec  c
.esign:
    inc  hl
.edig:
    ld   de, 0                         ; the exponent
    ld   b, d                          ; its digits
.ed:
    ld   a, (hl)
    sub  '0'
    cp   10
    jr   nc, .eend
    inc  hl
    inc  b
    push hl
    ld   h, d
    ld   l, e
    add  hl, hl
    add  hl, hl
    add  hl, de
    add  hl, hl                        ; x 10 ...
    ld   e, a
    ld   d, 0
    add  hl, de                        ; ... + the digit
    ex   de, hl
    pop  hl
    ld   a, d
    cp   4
    jr   c, .ed
    ld   de, 999                       ; (beyond, the value is 0 or too large anyway)
    jr   .ed
.eend:
    inc  b
    dec  b
    jp   z, .bad                       ; an exponent without digits
    ld   a, c
    or   a
    jr   z, .epos
    xor  a
    sub  e
    ld   e, a
    sbc  a, a
    sub  d
    ld   d, a
.epos:
    push hl
    ld   hl, (FDEXP)
    add  hl, de
    ld   (FDEXP), hl
    pop  hl
.suffix:
    ld   a, (hl)
    or   $20
    cp   'f'
    jr   z, .sfx
    cp   'l'
    jr   nz, .after
.sfx:
    inc  hl
.after:                                ; nothing alphanumeric, `_` or `.` may follow
    ld   a, (hl)
    cp   '_'
    jr   z, .bad
    cp   '.'
    jr   z, .bad
    call LEX_DIGIT
    jr   nc, .bad
    push hl
    ld   hl, FQ                        ; FX = N
    ld   de, FX + U_M
    ld   bc, 4
    ldir
    xor  a
    ld   (FX + U_S), a
    ld   (FX + U_G), a
    ld   a, 128 + 32
    ld   (FX + U_E), a
    call FNORM
    call FPACK
.scale:                                ; x or / 10^k, k at most 13 (exact powers: one rounding per
    ld   a, (F_ACC)                    ; step), until the decimal exponent is 0 (or the value)
    or   a
    jr   z, .done
    ld   hl, (FDEXP)
    ld   a, h
    or   l
    jr   z, .done
    ld   c, FOP_MUL
    bit  7, h
    jr   z, .k
    ld   c, FOP_DIVR
    xor  a
    sub  l
    ld   l, a
    sbc  a, a
    sub  h
    ld   h, a                          ; HL = |the exponent|
.k:
    ld   de, 13
    ld   a, h
    or   a
    jr   nz, .chunk
    ld   a, l
    cp   e
    jr   nc, .chunk
    ld   e, a                          ; DE = k
.chunk:
    ld   hl, (FDEXP)
    bit  0, c
    jr   nz, .up                       ; (FOP_DIVR: a negative exponent rises)
    or   a
    sbc  hl, de
    jr   .st
.up:
    add  hl, de
.st:
    ld   (FDEXP), hl
    ld   h, d
    ld   l, e
    dec  hl
    ld   d, h
    ld   e, l
    add  hl, hl
    add  hl, hl
    add  hl, de
    ld   de, XF_POW10
    add  hl, de                        ; HL -> 10^k
    ld   a, c
    call XF_BIN
    jr   .scale
.done:
    ld   hl, F_ACC
    ld   de, TOK_BUF
    ld   bc, 5
    ldir
    pop  hl
    ret
.bad:
    ld   a, E_NUMBER
    jp   F_ERR
