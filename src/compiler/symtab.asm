; ============================================================================
; src/compiler/symtab.asm -- the compile workspace and the scoped symbol table (spec.md 3.2; M1.2)
;
; Workspace. The RAM from the end of the source (PROG_END) up to LEAPC_SRC_TOP is used from both
; ends:
;   global area  grows down from LEAPC_SRC_TOP (WS_GLO): file-scope symbols, type nodes and struct
;                members. Nothing in it is reclaimed during a compile.
;   local area   grows up from PROG_END (WS_LOC): block- and prototype-scope symbols. A scope's
;                entries are reclaimed when the scope closes.
; When the two would overlap the compile stops with E_NOMEM. Because the global area can grow
; while blocks are open, a file-scope entry or a type node made inside a block outlives the block
; (block-scope extern declarations; M1.3's implicit function declarations).
;
; Chains (include/leapc_decl.inc has the entry layout). Each area has one chain, newest entry
; first: SYM_GLO for file scope, SYM_LOC for all open block and prototype scopes, innermost
; first. A lookup walks SYM_LOC, then SYM_GLO, and takes the first entry with the name in the
; requested namespace, so an inner declaration shadows an outer one. The entries of the innermost
; open scope are the local entries at addresses >= SCOPE_BASE (0 = no local scope is open).
; Namespaces: ordinary identifiers (objects, functions, typedef names, enum constants), tags,
; members (one list per struct, not a scope chain) and labels.
; ============================================================================

; ============================================================================
; WS_GALLOC -- allocate a block in the global area
; WS_LALLOC -- allocate a block in the local area
; In:  BC = size
; Out: HL = the block (contents undefined)
; Errors: E_NOMEM when the areas would overlap
; Destroys: AF, DE (BC kept)
; ============================================================================
WS_GALLOC:
    ld   hl, (WS_GLO)
    or   a
    sbc  hl, bc
    jr   c, WS_E_NOMEM
    ld   de, (WS_LOC)
    sbc  hl, de
    jr   c, WS_E_NOMEM
    add  hl, de
    ld   (WS_GLO), hl
    ret
WS_LALLOC:
    ld   hl, (WS_LOC)
    push hl
    add  hl, bc
    jr   c, WS_E_NOMEM
    ex   de, hl                        ; DE = new end of the local area
    ld   hl, (WS_GLO)
    sbc  hl, de
    jr   c, WS_E_NOMEM
    ld   (WS_LOC), de
    pop  hl
    ret
WS_E_NOMEM:
    ld   a, E_NOMEM
    jr   CC_ERROR

; ============================================================================
; SYM_MAKE -- allocate a symbol entry for the name NM in the current scope's area
; SYM_MAKE_G -- the same in the global area
; In:  A = kind (SK_*); NM_PTR, NM_LEN
; Out: HL = IX = the entry: link 0, kind A, flags 0, type 0, value 0, the name. Not linked.
; Errors: E_NOMEM
; Destroys: AF, BC, DE
; ============================================================================
SYM_MAKE:
    ld   c, a
    ld   a, (SCOPE_BASE + 1)
    or   a
    ld   a, c
    ld   hl, WS_LALLOC
    jr   nz, SYM_MAKE_IN
SYM_MAKE_G:
    ld   hl, WS_GALLOC
SYM_MAKE_IN:
    push af
    ld   a, (NM_LEN)
    add  a, S_NAME
    ld   c, a
    ld   b, 0
    call CALL_HL                       ; HL = the entry
    push hl
    pop  ix
    ld   b, S_NAME
.zero:
    ld   (hl), 0
    inc  hl
    djnz .zero                         ; HL -> the name
    pop  af
    ld   (ix + S_KIND), a
    ld   a, (NM_LEN)
    ld   (ix + S_LEN), a
    or   a
    jr   z, .done
    ex   de, hl
    ld   hl, (NM_PTR)
    ld   c, a
    ldir
.done:
    push ix
    pop  hl
    ret
CALL_HL         EQU RT_CALLHL       ; `call CALL_HL` = call (hl) (src/runtime/helpers.asm)

; ============================================================================
; SYM_NEW -- a new symbol entry for NM in the current scope (made the head of its chain)
; SYM_NEWG -- the same in file scope (global area, SYM_GLO), whatever scope is open
; In:  A = kind; NM_PTR, NM_LEN
; Out: HL = IX = the entry (flags, type and value 0)
; Errors: E_NOMEM
; Destroys: AF, BC, DE
; ============================================================================
SYM_NEWG:
    call SYM_MAKE_G
    ld   de, SYM_GLO
    jr   SYM_LINK
SYM_NEW:
    call SYM_MAKE
    ld   de, SYM_LOC
    ld   a, (SCOPE_BASE + 1)
    or   a
    jr   nz, SYM_LINK
    ld   de, SYM_GLO
SYM_LINK:                              ; entry HL: link = (DE); (DE) = HL
    ex   de, hl
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    ld   (hl), d
    dec  hl
    ld   (hl), e
    ex   de, hl
    ld   (hl), c
    inc  hl
    ld   (hl), b
    dec  hl
    ret

; ============================================================================
; SYM_FIND -- find the name NM in a chain
; In:  HL = first entry (0 = empty chain), C = namespace (NS_*), DE = lowest address an entry may
;      have to count (0 = any); NM_PTR, NM_LEN (1-31)
; Out: Z: found, HL = IX = the newest entry with the name in the namespace. NZ: none, or the newest
;      one lies below DE (it belongs to an outer scope)
; Destroys: AF, B, HL, IX (C, DE kept)
; ============================================================================
SYM_FIND:
    ld   a, h
    or   l
    jr   z, .none
    push hl
    inc  hl
    inc  hl
    ld   a, (hl)                       ; kind
    and  $F0
    cp   c
    jr   nz, .skip
    inc  hl
    ld   a, (NM_LEN)
    cp   (hl)                          ; length
    jr   nz, .skip
    or   a
    jr   z, .skip                      ; no name: never found
    ld   b, a
    push de
    ld   de, S_NAME - S_LEN
    add  hl, de
    ld   de, (NM_PTR)
.cmp:
    ld   a, (de)
    cp   (hl)
    jr   nz, .differ
    inc  hl
    inc  de
    djnz .cmp
.differ:
    pop  de
    jr   nz, .skip
    pop  hl                            ; found: is it at or above the limit?
    push hl
    pop  ix
    or   a
    sbc  hl, de
    add  hl, de
    jr   c, .none
    cp   a                             ; Z
    ret
.skip:
    pop  hl
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    jr   SYM_FIND
.none:
    or   1                             ; NZ
    ret

; ============================================================================
; SYM_LOOKUP -- find NM in every open scope, innermost first
; SYM_FIND_CUR -- find NM in the innermost open scope only
; In:  C = namespace; NM_PTR, NM_LEN
; Out: Z: found, HL = IX = the entry. NZ: not found
; Destroys: AF, B, DE, HL, IX
; ============================================================================
SYM_LOOKUP:
    ld   de, 0
    ld   hl, (SYM_LOC)
    call SYM_FIND
    ret  z
    ld   hl, (SYM_GLO)
    jr   SYM_FIND
SYM_FIND_CUR:
    ld   de, (SCOPE_BASE)
    ld   hl, (SYM_LOC)
    ld   a, d
    or   e
    jr   nz, SYM_FIND
    ld   hl, (SYM_GLO)
    jr   SYM_FIND

; ============================================================================
; NM_FROM_TOK -- the current token (an identifier) becomes the name NM
; In:  TOK_PTR, TOK_LEN. Out: NM_PTR, NM_LEN. Destroys: AF, HL
; ============================================================================
NM_FROM_TOK:
    ld   hl, (TOK_PTR)
    ld   (NM_PTR), hl
    ld   a, (TOK_LEN)
    ld   (NM_LEN), a
    ret

; ============================================================================
; SCOPE_OPEN -- open a block or prototype scope
; In:  -. Out: SCOPE_BASE = WS_LOC; 4 bytes saved on the stack under the return address. The
;      caller closes the scope with SCOPE_CLOSE at the same stack depth.
; Destroys: BC, DE (AF, HL kept)
; ============================================================================
SCOPE_OPEN:
    pop  bc
    ld   de, (SCOPE_BASE)
    push de
    ld   de, (SYM_LOC)
    push de
    ld   de, (WS_LOC)
    ld   (SCOPE_BASE), de
    push bc
    ret

; ============================================================================
; SCOPE_CLOSE -- close the innermost scope: its entries are reclaimed
; In:  the 4 bytes SCOPE_OPEN saved, under the return address
; Out: WS_LOC = SCOPE_BASE; SYM_LOC and SCOPE_BASE as before the matching SCOPE_OPEN
; Destroys: BC, DE (AF, HL kept)
; ============================================================================
SCOPE_CLOSE:
    pop  bc
    ld   de, (SCOPE_BASE)
    ld   (WS_LOC), de
    pop  de
    ld   (SYM_LOC), de
    pop  de
    ld   (SCOPE_BASE), de
    push bc
    ret
