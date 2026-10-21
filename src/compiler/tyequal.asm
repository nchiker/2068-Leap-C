; ============================================================================
; src/compiler/tyequal.asm -- type compatibility (spec.md 4.3), EXROM
;
; EXROM-resident since Phase 8 (budget ledger L42; it was in the HOME type system, src/compiler/types.asm).
; The compiler reaches it through the HOME trampoline TY_EQUAL (src/rom/home.asm). Bank rule 3: it
; reads only type nodes in the compile workspace, writes nothing; its one error (E_NESTING, the
; compiler's stack guard CC_STACKCHK) leaves through CC_ERROR, which pages the EXROM out.
; ============================================================================

; ============================================================================
; XT_EQUAL -- are two types compatible (spec.md 4.3: the same type, allowing for unknown array
; sizes and unprototyped functions)?
; In:  HL, DE = types
; Out: Z: compatible. NZ: not
; Errors: E_NESTING (compiler stack guard)
; Destroys: AF, BC, DE, HL
; ============================================================================
XT_EQUAL:
    call CC_STACKCHK
.loop:
    or   a
    sbc  hl, de
    add  hl, de
    ret  z                             ; the same handle
    ld   a, h
    cp   TY_NODE_H
    jr   c, .ne                        ; scalar handles are canonical
    ld   a, d
    cp   TY_NODE_H
    jr   c, .ne
    ld   a, (de)
    cp   (hl)
    ret  nz                            ; different kinds
    cp   TN_STRUCT
    jr   z, .ne                        ; different struct nodes are different types
    push hl
    push de
    cp   TN_FUNC
    jr   z, .func
    cp   TN_ARRAY
    jr   nz, .next                     ; pointers: compare the targets
    call .fieldb                       ; arrays: equal counts, or one unknown
    push bc
    ex   de, hl
    call .fieldb
    ex   de, hl
    pop  hl                            ; HL = first count, BC = second count
    ld   a, h
    or   l
    jr   z, .next
    ld   a, b
    or   c
    jr   z, .next
    sbc  hl, bc
    jr   nz, .ne2
    jr   .next
.func:                                 ; both prototyped: same parameter count and types
    ld   bc, TN_FFLAGS
    add  hl, bc
    ld   a, (hl)
    ex   de, hl
    add  hl, bc
    and  (hl)
    rra                                ; C: both have TFF_PROTO
    jr   nc, .next
    dec  hl
    ld   a, (hl)                       ; parameter count (second)
    ex   de, hl
    dec  hl
    cp   (hl)
    jr   nz, .ne2
    or   a
    jr   z, .next
    ld   b, a
    inc  hl
    inc  hl                            ; HL, DE -> the parameter types
    inc  de
    inc  de
.param:
    push bc
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    inc  hl
    push hl
    ex   de, hl
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ex   (sp), hl                      ; (SP) = next second, HL = next first
    push hl
    ld   h, b
    ld   l, c
    call XT_EQUAL
    pop  hl
    pop  de
    pop  bc
    jr   nz, .ne2
    djnz .param
.next:                                 ; compare field A: target, element or return type
    pop  de
    pop  hl
    call .fielda
    ex   de, hl
    call .fielda
    jr   .loop
.ne2:
    pop  de
    pop  hl
.ne:
    or   1
    ret
.fielda:                               ; HL = field A of node HL
    inc  hl
    inc  hl
    inc  hl
    rst  $08                          ; LDI: HL = (HL)
    ret
.fieldb:                               ; BC = field B of node HL (HL kept)
    push de
    call TY_FIELDS
    pop  de
    ret
