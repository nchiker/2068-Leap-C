; ============================================================================
; src/runtime/float.asm -- floating point: the helpers compiled code calls (spec.md 4.9, 5.3; Phase 8)
;
; A float value is computed in F_ACC, the float accumulator (5 bytes, a Leap-C cell: always
; visible). A float operand held while another is computed, and a float argument, is a 3-word slot
; on the machine stack: F_PUSH puts the 5 bytes at SP+0..4 under its return address (SP+5 is
; padding), so a held operand is never in chunk 6. The arithmetic is the EXROM's float core
; (src/runtime/fpcore.asm), reached through F_OP (`call F_OP / db op`) with chunk 6 paged out
; around it: a BREAK-deferring section, as every EXROM trampoline (spec.md 5.8). What may address
; chunk 6 (the loads and stores of float objects) runs here, with chunk 6 = RAM.
;
; Float values are the Sinclair 5-byte format (spec.md 4.9): [exponent][sign | mantissa ...].
; ============================================================================

; ============================================================================
; F_OP -- `call F_OP / db op`: an operation of the float core (FOP_*, include/leapc_rom.inc)
; In:  F_ACC; a unary operation (bit 7 of op clear): HL = its argument (FRI, FRU: an integer); a
;      binary one (bit 7 set): its left operand in the slot under the return address (F_PUSH)
; Out: F_ACC = the result (TOI: HL); CMP, CMPR: the flags (C less, Z equal); a binary operation
;      pops its slot. LIB_CALLER = the call (a runtime error's line, BREAK's)
; Errors: runtime error 6 (NUMBER TOO BIG: overflow, division by zero) through F_ERR
; Destroys: AF, BC, DE, HL (IX kept)
; ============================================================================
F_OP:
    ex   (sp), hl                      ; HL -> the op byte, (SP) = the argument
    ld   a, (hl)
    inc  hl
    ld   (LIB_CALLER), hl
    ex   (sp), hl                      ; the return past the byte
    or   a
    jp   p, F_X                        ; unary
    ld   hl, 2
    add  hl, sp                        ; binary: HL -> the left operand's slot
    call F_X
; F_DROP -- pop the 3-word slot under the return address (flags kept)
F_DROP:
    pop  hl
    pop  bc
    pop  bc
    pop  bc
    jp   (hl)
; F_POP -- F_ACC = the slot under the return address, popped (flags not kept)
F_POP:
    ld   hl, 2
    add  hl, sp
    call F_LD
    jr   F_DROP

; ============================================================================
; F_X -- operation A of the float core with the EXROM paged in: a BREAK-deferring section (NOBRK,
; spec.md 5.8; the program's printf calls it too)
; In:  A = the operation, HL (and C for FTOA) its argument. Out: as XF_OP (flags, HL; BC kept)
; Destroys: AF, BC, DE, HL
; ============================================================================
F_X:
    push hl
    ld   hl, NOBRK
    inc  (hl)
    push af
    call BANK_PAGE_EXROM_IN            ; (keeps BC, DE, HL)
    pop  af
    pop  hl
    call LEAPC_EXROM_FLOAT
    push af
    push hl
    call BANK_PAGE_EXROM_OUT
    call RT_NOBRK_END                  ; (a BREAK meanwhile: the program ends here)
    pop  hl
    pop  af
    ret

; ============================================================================
; F_ERR -- the float core's error exit (the EXROM jumps here): runtime error 6 while a program runs,
; else (compile time: a constant) compile error A
; In:  A = E_RANGE or E_NUMBER; the EXROM paged in. Out: does not return (RT_ERROR / CC_ERROR unwind)
; ============================================================================
F_ERR:
    push af
    call BANK_PAGE_EXROM_OUT
    ld   a, (RUNNING)
    or   a
    jr   z, .cc
    ld   a, RTE_FLOAT
    jp   RT_LIBERR
.cc:
    pop  af
    jp   CC_ERROR

; ============================================================================
; F_PUSH -- push F_ACC as a 3-word slot under the return address
; Destroys: BC, DE (AF, HL kept)
; ============================================================================
F_PUSH:
    pop  bc
    ld   de, (F_ACC + 4)               ; (D: the padding byte)
    push de
    ld   de, (F_ACC + 2)
    push de
    ld   de, (F_ACC)
    push de
    push bc
    ret

; ============================================================================
; Loads and stores of float objects (5 bytes), anywhere in RAM (chunk 6 = RAM: the program's state)
; F_LD -- F_ACC = the float at HL. Out: HL past it
; F_ST -- the float at HL = F_ACC
; F_LDX, F_STX -- `call F_LDX / db d`: the same for the frame object at IX + d (d signed)
; F_LDK -- `call F_LDK / db 5 bytes`: F_ACC = the constant that follows
; Destroys: BC, DE, HL (F_LDX, F_STX: and AF)
; ============================================================================
F_LDX:
    call F_IXD
F_LD:
    ld   de, F_ACC
F_CP5:
    ld   bc, 5
    ldir
    ret
F_STX:
    call F_IXD
F_ST:
    ex   de, hl
    ld   hl, F_ACC
    jr   F_CP5
F_LDK:
    pop  hl
    call F_LD
    jp   (hl)
F_IXD:                                 ; HL = IX + the displacement after our caller's call (skipped)
    pop  bc
    pop  hl
    ld   e, (hl)
    inc  hl
    push hl
    push bc
    ld   a, e
    rla
    sbc  a, a
    ld   d, a
    push ix
    pop  hl
    add  hl, de
    ret

; F_TST -- Z if F_ACC is 0. Destroys: AF
F_TST:
    ld   a, (F_ACC)
    or   a
    ret

; F_REST -- F_ACC = F_OLD (the value before FOP_PINC / FOP_PDEC: postfix ++ and --). Destroys: BC, DE, HL
F_REST:
    ld   hl, F_OLD
    jr   F_LD
