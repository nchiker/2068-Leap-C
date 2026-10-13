; 2068-Leap-C code-shape spike -- the shared helper library (would live in HOME ROM).
; Entered by CALL or by RST (through a `jp` in the vector). Either way the return address
; on the stack points at the call site's inline operand byte, if the helper takes one.
; Register contract: helpers that take an inline byte destroy A and F only, except as noted.

; HL = word at IX + inline byte.  Destroys A, F.
H_LDL:
        pop hl                  ; HL -> operand byte
        ld a,(hl)
        inc hl
        push hl                 ; continuation
        push ix
        pop hl
        add a,l                 ; HL = IX + A
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret
H_LDL_END:

; word at IX + inline byte = HL.  Destroys A, F, DE (= value), HL.
H_STL:
        ex de,hl                ; DE = value
        pop hl
        ld a,(hl)
        inc hl
        push hl
        push ix
        pop hl
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld (hl),e
        inc hl
        ld (hl),d
        ret
H_STL_END:

; prologue: push IX, SP -= inline byte, IX = SP.  Destroys A, F, DE, HL.
H_ENTER:
        pop hl                  ; HL -> N
        ld a,(hl)
        inc hl
        push ix
        ex de,hl                ; DE = continuation
        cpl                     ; HL = -N (N = 0 gives 0)
        ld l,a
        ld h,$FF
        inc hl
        add hl,sp
        ld sp,hl
        push hl
        pop ix
        ex de,hl
        jp (hl)
H_ENTER_END:

; epilogue: SP = IX + inline byte, pop IX, return to the function's caller.  HL preserved.
H_LEAVE:
        ex de,hl                ; DE = return value
        pop hl                  ; HL -> N (never returned to)
        ld a,(hl)
        push ix
        pop hl
        add a,l
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld sp,hl
        pop ix
        ex de,hl
        ret
H_LEAVE_END:

; HL = word at (HL).  Destroys A.
H_LDI:
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret
H_LDI_END:

; word at (DE) = HL; HL preserved, DE = address + 1.
H_STI:
        ex de,hl
        ld (hl),e
        inc hl
        ld (hl),d
        ex de,hl
        ret
H_STI_END:

; carry iff DE < HL (signed).  Destroys A, DE, HL.
H_CMPLT:
        ld a,d
        xor $80
        ld d,a
        ld a,h
        xor $80
        ld h,a
        ex de,hl
        or a
        sbc hl,de
        ret
H_CMPLT_END:

; empty helper: measures the bare cost of reaching a helper and returning.
H_NOP:
        ret

; generic dispatcher for helpers that have no RST of their own:  rst $30 / db 2*index.
; HL and DE reach the helper unchanged; A and F are destroyed.
H_DISPATCH:
        ex (sp),hl              ; HL -> index byte, (SP) = caller's HL
        ld a,(hl)
        inc hl
        ex (sp),hl              ; HL = caller's HL, (SP) = continuation (the helper's return)
        push hl
        ld hl,HTAB
        add a,l
        ld l,a                  ; HTAB never crosses a 256-byte page (ASSERT below)
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ex (sp),hl              ; HL = caller's HL, (SP) = helper address
        ret                     ; jump to the helper
H_DISPATCH_END:
HTAB:
        dw H_CMPLT, H_NOP
HTAB_END:
    ASSERT (HTAB >> 8) == ((HTAB_END - 1) >> 8)
HELPERS_END:
