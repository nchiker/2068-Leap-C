; ============================================================================
; src/runtime/helpers.asm -- the runtime helper core (spec.md 5.3; project_plan.md M1.3)
;
; Compiled code reaches these by RST (page zero, src/rom/home.asm: LDI, STI, ENTER, LEAVE, CMPLT)
; or by CALL. Two-operand helpers take the left operand in DE and the right one in HL (the order
; in which the code generator evaluates them) and return the result in HL. The arithmetic is the
; kept V2 math (kernel/math/math.asm): wraparound, division truncating toward zero, the remainder
; with the dividend's sign, division by zero giving 0 (spec.md 4.4).
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
    jp   (hl)

; RT_CMPLT_SAME -- the rest of RST $28 CMPLT, operands of the same sign: carry <=> DE < HL
RT_CMPLT_SAME:
    ex   de, hl
    or   a
    sbc  hl, de
    ret

; ============================================================================
; RT_CALLHL -- call the function at HL (calls through a function pointer: `call RT_CALLHL`)
; ============================================================================
RT_CALLHL:
    jp   (hl)

; ============================================================================
; RT_MUL -- HL = DE * HL (the low 16 bits: the same for signed and unsigned)
; RT_DIVS / RT_MODS -- HL = DE / HL, DE % HL, signed
; RT_DIVU / RT_MODU -- the same, unsigned
; Destroys: AF, BC, DE
; ============================================================================
RT_MUL:
    ld   b, h
    ld   c, l
    jp   MATH_UMUL16
RT_DIVS:
    ex   de, hl
    jp   MATH_DIVIDE16
RT_MODS:
    ex   de, hl
    jp   MATH_MOD16
RT_MODU:
    call RT_DIVU
    ex   de, hl
    ret
RT_DIVU:
    ld   b, h
    ld   c, l
    ex   de, hl
    jp   MATH_UDIV16

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
