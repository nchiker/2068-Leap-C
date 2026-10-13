; ============================================================================
; src/runtime/helpers.asm -- the runtime helper core (spec.md 5.3; project_plan.md M1.3)
;
; Compiled code reaches these by RST (page zero, src/rom/home.asm: LDI, STI, ENTER, LEAVE, CMPLT)
; or by CALL. Two-operand helpers take the left operand in DE and the right one in HL (the order
; in which the code generator evaluates them) and return the result in HL. Multiply and divide are
; the helper core's own register-only routines (Phase 2; they replace the V2 math, platform delta
; D3): wraparound, division truncating toward zero, the remainder with the dividend's sign,
; division by zero giving 0 (spec.md 4.4). The compiler's constant arithmetic uses the same
; routines (RT_UMUL, RT_UDIV; the EXROM constant folding through the HOME exports).
; ============================================================================

; ============================================================================
; RT_ENTER -- the rest of RST $18 ENTER n
; In:  HL -> n (the byte after the rst), the caller's IX pushed, the return address under it
; Out: IX -> the saved IX, SP = IX - n; continues after n
; Errors: runtime error 1 (stack overflow) when SP would go below LEAPC_RT_STACK_FLOOR
; Destroys: AF, BC, DE, HL
; ============================================================================
RT_ENTER:
    ld   ix, 0
    add  ix, sp
    ld   a, (hl)
    inc  hl
    ex   de, hl                        ; DE = the continuation
    cpl
    ld   l, a
    ld   h, $FF
    inc  hl                            ; HL = -n
    add  hl, sp
    ld   sp, hl
    ld   bc, -LEAPC_RT_STACK_FLOOR
    add  hl, bc                        ; C: SP >= the floor
    ex   de, hl
    jp   nc, RT_ERR_STACK
; RT_CALLHL -- call the function at HL (calls through a function pointer: `call RT_CALLHL`)
RT_CALLHL:
    jp   (hl)

; RT_CMPLT_SAME -- the rest of RST $28 CMPLT, operands of the same sign: carry <=> DE < HL
RT_CMPLT_SAME:
    ex   de, hl
    or   a
    sbc  hl, de
    ret

; ============================================================================
; RT_MUL -- HL = DE * HL (the low 16 bits: the same for signed and unsigned)
; RT_UMUL -- HL = DE * BC (the compiler's constant arithmetic)
; Destroys: AF, BC (RT_UMUL keeps DE)
; ============================================================================
RT_MUL:
    ld   b, h
    ld   c, l
RT_UMUL:
    ld   hl, 0
    ld   a, 16
.bit:                                  ; the multiplier's bits from the top: HL = HL * 2 (+ DE)
    add  hl, hl
    rl   c
    rl   b
    jr   nc, .next
    add  hl, de
.next:
    dec  a
    jr   nz, .bit
    ret

; ============================================================================
; RT_DIVS / RT_MODS -- HL = DE / HL, DE % HL, signed: the quotient truncated toward zero, the
; remainder with the dividend's sign, 0 for a divisor of 0
; Destroys: AF, BC, DE
; ============================================================================
RT_DIVS:
    ld   a, h
    xor  d
    and  $80                           ; bit 7: the quotient's sign; bit 0 clear: the quotient
    jr   RT_SDIV
RT_MODS:
    ld   a, d
    and  $80                           ; bit 7: the dividend's sign
    inc  a                             ; bit 0: the remainder
RT_SDIV:
    push af
    call MATH_ABS16
    ld   b, h
    ld   c, l                          ; BC = |divisor|
    ex   de, hl
    call MATH_ABS16                    ; HL = |dividend|
    call RT_UDIV
    pop  af
    rra                                ; (carry was clear): C = bit 0, bit 7 -> bit 6
    jr   nc, .sign
    ex   de, hl                        ; the remainder
.sign:
    and  $40
    ret  z
    jp   MATH_NEGATE16

; ============================================================================
; RT_DIVU -- HL = DE / HL, unsigned (0 for a divisor of 0). Destroys: AF, BC, DE (DE = DE % HL)
; RT_MODU (page zero, src/rom/home.asm) -- HL = DE % HL, unsigned
; RT_UDIV -- HL = HL / BC, DE = HL % BC, unsigned; HL = DE = 0 for BC = 0 (the compiler's constant
; arithmetic). Restoring division, 16 steps, registers only. Destroys: AF (BC kept)
; ============================================================================
RT_DIVU:
    ld   b, h
    ld   c, l
    ex   de, hl
RT_UDIV:
    ld   a, b
    or   c
    jr   nz, .div
    ld   h, a
    ld   l, a
    ld   d, a
    ld   e, a
    ret
.div:
    ld   de, 0                         ; DE = the remainder
    ld   a, 16
.bit:                                  ; HL = the dividend, shifting out at the top while the
    add  hl, hl                        ; quotient shifts in at the bottom
    ex   de, hl
    adc  hl, hl                        ; remainder = remainder * 2 + the dividend's next bit
    jr   c, .sub                       ; 17 bits: certainly >= the divisor
    sbc  hl, bc                        ; (carry clear)
    jr   nc, .one
    add  hl, bc
    jr   .next
.sub:
    or   a
    sbc  hl, bc
.one:
    inc  e                             ; the quotient's bit
.next:
    ex   de, hl
    dec  a
    jr   nz, .bit
    ret

; ============================================================================
; RT_CPL -- HL = ~HL. Destroys: AF
; ============================================================================
RT_CPL:
    ld   a, h
    cpl
    ld   h, a
    ld   a, l
    cpl
    ld   l, a
    ret

; ============================================================================
; RT_SHL / RT_SHR / RT_SAR -- HL = DE << HL, DE >> HL logical, DE >> HL arithmetic. Counts above 15
; shift every bit out (as the constant folding does)
; Destroys: AF, B, DE
; ============================================================================
RT_SHL:
    call RT_SHCNT
    ret  z
.bit:
    add  hl, hl
    djnz .bit
    ret
RT_SHR:
    call RT_SHCNT
    ret  z
.bit:
    srl  h
    rr   l
    djnz .bit
    ret
RT_SAR:
    call RT_SHCNT
    ret  z
.bit:
    sra  h
    rr   l
    djnz .bit
    ret
; RT_SHCNT -- In: DE = value, HL = count. Out: HL = value, B = the count limited to 16, Z if 0
RT_SHCNT:
    ld   b, 16
    ld   a, h
    or   a
    jr   nz, .limit
    ld   a, l
    cp   b
    jr   nc, .limit
    ld   b, a
.limit:
    ex   de, hl
    ld   a, b
    or   a
    ret
