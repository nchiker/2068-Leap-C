; ============================================================================
; src/compiler/types.asm -- type handles and type nodes (spec.md 4.2; M1.2)
;
; A type is a 16-bit handle (include/leapc_decl.inc): a scalar base with its pointer depth in H, or
; the address of a type node in the global area. Pointer types are canonical: a scalar base's
; pointer is H + 1, a node's pointer is the node's cached TN_PTR node. Array and function types are
; compared structurally (TY_EQUAL); a struct type is its node.
; ============================================================================

; ============================================================================
; TY_CLASS -- the class of a type
; In:  HL = type
; Out: A = TC_*: TC_VOID..TC_FLOAT for a scalar base, TC_PTR, TC_ARRAY, TC_FUNC or TC_STRUCT
; Destroys: F (HL kept)
; ============================================================================
TY_CLASS:
    ld   a, h
    or   a
    ld   a, l
    ret  z                             ; scalar base: TB_* = TC_*
    ld   a, h
    cp   TY_NODE_H
    ld   a, TC_PTR
    ret  c                             ; pointer to a scalar base
    ld   a, (hl)
    add  a, TC_PTR - TN_PTR
    ret

; ============================================================================
; TY_FIELDS -- the A and B fields of a type node
; In:  HL = node. Out: DE = field A (+3), BC = field B (+5). HL kept
; Destroys: -
; ============================================================================
TY_FIELDS:
    push hl
    inc  hl
    inc  hl
    inc  hl
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    pop  hl
    ret

; ============================================================================
; TY_SETAB -- store the A and B fields of a type node
; In:  HL = node, DE = field A, BC = field B. Out: HL kept
; Destroys: -
; ============================================================================
TY_SETAB:
    push hl
    inc  hl
    inc  hl
    inc  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    ld   (hl), c
    inc  hl
    ld   (hl), b
    pop  hl
    ret

; ============================================================================
; TY_NEW -- a new type node in the global area
; In:  A = TN_* kind, BC = node size (>= TN_NODE_SIZE)
; Out: HL = node: kind A, every other byte 0
; Errors: E_NOMEM
; Destroys: AF, BC, DE
; ============================================================================
TY_NEW:
    push af
    call WS_GALLOC
    push hl
    call MEM_FILL_ZERO
    pop  hl
    pop  af
    ld   (hl), a
    ret

; ============================================================================
; TY_SIZE -- the size of an object type
; TY_SIZE0 -- the same, 0 for an incomplete type instead of an error
; In:  HL = type
; Out: HL = size in bytes (1-65535; TY_SIZE0: 0 = incomplete)
; Errors: TY_SIZE: E_INCOMPLETE for void, a function, a struct without its body, an array of
;      unknown size
; Destroys: AF, BC, DE
; ============================================================================
TY_SIZE:
    call TY_SIZE0
    ld   a, h
    or   l
    ret  nz
TY_E_INCOMPLETE:
    ld   a, E_INCOMPLETE
    jp   CC_ERROR
TY_SIZE0:
    call TY_CLASS
    cp   TC_PTR
    jr   z, .word
    jr   nc, .node
    or   a
    jr   z, .none                      ; void
    cp   TC_INT
    ld   hl, 1
    ret  c                             ; char, signed char
    cp   TC_FLOAT
    ld   l, FLOAT_SIZE
    ret  z                             ; float (Phase 8)
.word:
    ld   hl, 2
    ret
.node:                                 ; A = TC_ARRAY / TC_FUNC / TC_STRUCT, HL = node
    cp   TC_FUNC
    jr   z, .none
    call TY_FIELDS                     ; DE = element / size, BC = count / first member
    ld   a, b
    or   c
    jr   z, .none                      ; array of unknown size / struct without a body
    ld   a, (hl)
    cp   TN_STRUCT
    ex   de, hl
    ret  z                             ; struct: HL = its size
    push bc                            ; array: HL = element type, BC = count
    call TY_SIZE0
    pop  bc
    ex   de, hl
    jp   RT_UMUL                       ; HL = count * element size (TY_ARRAY checked the range)
.none:
    ld   hl, 0
    ret

; ============================================================================
; TY_DEREF -- the type a pointer points to, or the element type of an array
; In:  HL = type
; Out: C: HL = target or element type. NC: not a pointer or array (HL kept)
; Destroys: AF, BC, DE
; ============================================================================
TY_DEREF:
    call TY_CLASS
    cp   TC_PTR
    jr   z, .ptr
    cp   TC_ARRAY
    jr   z, .node
    or   a
    ret
.ptr:
    ld   a, h
    cp   TY_NODE_H
    jr   nc, .node
    dec  h                             ; (C is set)
    ret
.node:
    call TY_FIELDS
    ex   de, hl
    scf
    ret

; ============================================================================
; TY_PTR -- the pointer type to a type
; In:  HL = type
; Out: HL = "pointer to HL": H + 1 for a scalar base, else the node's cached TN_PTR node (made and
;      cached on first use, so each type has one pointer type)
; Errors: E_NESTING (more than 15 pointer levels on a scalar base), E_NOMEM
; Destroys: AF, BC, DE
; ============================================================================
TY_PTR:
    ld   a, h
    cp   TY_NODE_H
    jr   nc, .node
    cp   TY_PTR_MAX - 1
    jr   nc, TY_E_NESTING
    inc  h
    ret
.node:
    push hl                            ; target
    inc  hl
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    ld   a, d
    or   e
    jr   nz, .cached
    push hl                            ; -> high byte of the cache
    ld   a, TN_PTR
    ld   bc, TN_NODE_SIZE
    call TY_NEW
    ex   de, hl                        ; DE = the new node
    pop  hl
    ld   (hl), d
    dec  hl
    ld   (hl), e
    ex   de, hl
    pop  de                            ; DE = target
    jp   TY_SETAB                      ; (BC = 0 from TY_NEW's fill)
.cached:
    pop  hl
    ex   de, hl
    ret
TY_E_NESTING:
    ld   a, E_NESTING
    jp   CC_ERROR

; ============================================================================
; TY_ARRAY -- the array type "BC elements of HL"
; In:  HL = element type (complete), BC = count (0 = unknown size, `[]`)
; Out: HL = array node
; Errors: E_INCOMPLETE (the element type has no size), E_TOOLARGE (more than 65535 bytes), E_NOMEM
; Destroys: AF, BC, DE
; ============================================================================
TY_ARRAY:
    push hl
    push bc
    call TY_SIZE                       ; HL = element size (>= 1)
    pop  bc
    ld   a, b
    or   c
    jr   z, .make
    push bc
    ld   b, h
    ld   c, l
    ld   hl, $FFFF
    call RT_UDIV                       ; HL = most elements that fit in 65535 bytes
    pop  bc
    or   a
    sbc  hl, bc
    jr   c, TY_E_TOOLARGE
.make:
    push bc
    ld   a, TN_ARRAY
    ld   bc, TN_NODE_SIZE
    call TY_NEW
    pop  bc
    pop  de
    jp   TY_SETAB
TY_E_TOOLARGE:
    ld   a, E_TOOLARGE
    jp   CC_ERROR
