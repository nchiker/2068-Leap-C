; ============================================================================
; src/compiler/init.asm -- static data and initialisers (spec.md 3.2, 4.7; M1.2)
;
; Static data (globals, static locals, string literals) is allocated in the image regions, top
; down in each region, first fit in the region order of spec.md 3.2 (IMG_LIM: [low][high] per
; region; M1.3's code grows up from low). The compiler writes the initial values straight into
; the image and zeroes the rest, so the image holds the program's initial static data.
;
; Initialisers follow C89 6.5.7 with brace elision: scalars (optionally in braces), arrays and
; structs of constant expressions, char arrays from string literals. With CX_NOEVAL > 0 (the
; counting pass for a `[]` array) nothing is stored or allocated.
; ============================================================================

; ============================================================================
; DATA_ALLOC -- allocate static data
; In:  BC = size (>= 1)
; Out: HL = address of BC zeroed bytes
; Errors: E_TOOBIG (no region has room)
; Destroys: AF, BC, DE
; ============================================================================
DATA_ALLOC:
    ld   hl, IMG_LIM
    ld   a, IMG_REGIONS
.region:
    push af
    ld   e, (hl)
    inc  hl
    ld   d, (hl)                       ; DE = low
    inc  hl
    push hl
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a                          ; HL = high
    or   a
    sbc  hl, bc
    jr   c, .next
    sbc  hl, de
    jr   c, .next
    add  hl, de                        ; HL = high - size >= low
    ex   de, hl
    pop  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    pop  af
    ex   de, hl
    push hl
    call MEM_FILL_ZERO
    pop  hl
    ret
.next:
    pop  hl
    inc  hl
    inc  hl
    pop  af
    dec  a
    jr   nz, .region
    ld   a, E_TOOBIG
    jp   CC_ERROR

; ============================================================================
; STR_STAGE -- adjacent string literals, concatenated in the free workspace (spec.md 4.1)
; In:  current token = TK_STR
; Out: HL = the bytes (at WS_LOC, followed by a NUL), BC = their number without the NUL; current
;      token after the last literal. The staging area is not allocated: use it before the next
;      local allocation.
; Errors: E_NOMEM
; Destroys: AF, DE
; ============================================================================
STR_STAGE:
    ld   de, (WS_LOC)
.literal:
    ld   a, (TOK_LEN)
    ld   c, a
    ld   b, 0
    ld   hl, (WS_GLO)
    scf
    sbc  hl, de                        ; free bytes - 1 (room for the NUL)
    jp   c, WS_E_NOMEM
    sbc  hl, bc
    jp   c, WS_E_NOMEM
    or   a
    jr   z, .empty
    ld   hl, TOK_BUF
    ldir
.empty:
    push de
    call LEX_NEXT
    pop  de
    cp   TK_STR
    jr   z, .literal
    xor  a
    ld   (de), a
    ld   hl, (WS_LOC)
    ex   de, hl
    or   a
    sbc  hl, de
    ld   b, h
    ld   c, l
    ex   de, hl
    ret

; ============================================================================
; INIT_TOP -- the initialiser of a declared object: an aggregate needs braces or, for a char
; array, a string literal
; INIT -- an initialiser for an object of type HL at address DE (C89 6.5.7)
; In:  HL = type, DE = address; current token = the initialiser's first token
; Out: BC = elements given at the outermost level of an array (a string: its length + 1);
;      current token after the initialiser
; Errors: E_INIT (too many elements, string too long, missing braces), E_TYPE, E_CONSTEXPR,
;      E_NESTING, the expression errors
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
INIT_TOP:
    push hl
    call TY_CLASS
    pop  hl
    cp   TC_ARRAY
    jr   c, INIT
    ld   a, (TOK_KIND)
    cp   TK_LBRACE
    jr   z, INIT
    cp   TK_STR
    jp   nz, CC_E_INIT
INIT:
    call CC_STACKCHK
    push de
    push hl
    call TY_CLASS
    cp   TC_ARRAY
    jr   nc, .aggregate
    ld   a, (TOK_KIND)                 ; scalar
    cp   TK_LBRACE
    jr   z, .braced_scalar
    call CX_CONST_INIT                 ; X = a constant (integer or address)
    pop  hl
    push hl
    call CX_CHECK_ASSIGN
    pop  hl
    call TY_SIZE                       ; 1 or 2
    pop  de
    ld   a, (CX_NOEVAL)
    or   a
    ret  nz
    ld   a, l
    ld   hl, (X_VAL)
    ex   de, hl
    ld   (hl), e
    dec  a
    ret  z
    inc  hl
    ld   (hl), d
    ret
.braced_scalar:
    call LEX_NEXT
    pop  hl
    pop  de
    call INIT
    jr   INIT_CLOSE
.aggregate:
    ld   b, 0                          ; B = 1: braced
    ld   a, (TOK_KIND)
    cp   TK_LBRACE
    jr   nz, .open
    call LEX_NEXT
    ld   b, 1
.open:
    pop  hl
    pop  de
    push bc
    call INIT_STRING                   ; C: done (a char array from a string literal)
    jr   c, .close
    pop  af                            ; A = B: braced
    push af
    call INIT_LIST
.close:
    pop  af
    or   a
    ret  z
INIT_CLOSE:                            ; `[,] }` after a braced initialiser
    push bc
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    call z, LEX_NEXT
    ld   a, TK_RBRACE
    call CC_EXPECT
    pop  bc
    ret

; ============================================================================
; INIT_STRING -- a char array from a string literal, if the current token is one
; In:  HL = array or struct type, DE = address
; Out: C: done, BC = string length + 1. NC: not a char array with a string (HL, DE kept)
; Errors: E_INIT (the string is longer than the array), E_NOMEM, E_TOOLARGE
; Destroys: AF, BC (and DE, HL when done)
; ============================================================================
INIT_STRING:
    ld   a, (TOK_KIND)
    cp   TK_STR
    jr   nz, .no
    push de
    push hl
    call TY_DEREF                      ; NC: a struct
    jr   nc, .no2
    call TY_CLASS
    dec  a
    cp   TC_SCHAR                      ; char, unsigned char, signed char
    jr   nc, .no2
    pop  hl
    call TY_FIELDS                     ; BC = the array's count (0: `[]`)
    push bc
    call STR_STAGE                     ; HL = bytes, BC = length
    inc  bc                            ; with the NUL
    pop  de                            ; DE = count
    ld   a, d
    or   e
    jr   z, .copy                      ; `[]`: all of it
    push hl
    ex   de, hl
    sbc  hl, bc                        ; count - (length + 1)   (C clear from `or e`)
    jr   nc, .fits
    inc  hl
    ld   a, h
    or   l
    jp   nz, CC_E_INIT                 ; longer than the array (exactly full: no NUL, C89)
    dec  bc
.fits:
    pop  hl
.copy:                                 ; HL = bytes, BC = bytes to copy, (SP) = address
    pop  de
    push bc
    ld   a, (CX_NOEVAL)
    or   a
    jr   nz, .counted
    ldir
.counted:
    pop  bc
    scf
    ret
.no2:
    pop  hl
    pop  de
.no:
    or   a
    ret

; ============================================================================
; INIT_LIST -- the elements of an array or struct initialiser list, with brace elision
; In:  HL = array or struct type, DE = address, A = nonzero if the list is in braces (then it may
;      not have more elements than the object; without braces it stops when the object is full)
; Out: BC = elements given (meaningful for an array of unknown size); current token = `}` or the
;      token after the last element
; Errors: E_INIT, the errors of INIT
; Destroys: AF, DE, HL, IX
; ============================================================================
INIT_LIST:
    ld   ix, IL_CELLS                  ; the enclosing list's state
    ld   b, IL_WORDS
    call CELLS_SAVE
    ld   (IL_BRACED), a
    ld   (IL_ADDR), de
    call TY_FIELDS                     ; DE = element / size, BC = count / first member
    ld   a, (hl)
    cp   TN_STRUCT
    jr   z, .struct
    ld   (IL_ELEM), de
    ld   a, b
    or   c
    jr   nz, .limit
    dec  bc                            ; `[]`: no limit
.limit:
    ld   (IL_LEFT), bc
    ex   de, hl
    call TY_SIZE
    jr   .esize
.struct:
    ld   (IL_ELEM), bc
    ld   h, b
    ld   l, c
    ld   bc, 0
.members:                              ; elements = members
    inc  bc
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    or   h
    jr   nz, .members
    ld   (IL_LEFT), bc
.esize:                                ; (HL = 0 for a struct)
    ld   (IL_ESIZE), hl
.loop:
    ld   a, (TOK_KIND)
    cp   TK_RBRACE
    jr   z, .done
    call .left
    jr   nz, .element
    ld   a, (IL_BRACED)
    or   a
    jp   nz, CC_E_INIT                 ; more elements than the object has
    jr   .done
.element:
    ld   hl, (IL_ELEM)
    ld   de, (IL_ADDR)
    ld   bc, (IL_ESIZE)
    ld   a, b
    or   c
    jr   nz, .init
    push hl                            ; a member: its type, the struct's address + its offset
    ld   c, S_VAL
    add  hl, bc
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    add  hl, de
    ex   de, hl
    pop  hl
    ld   c, S_TYPE
    add  hl, bc
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
.init:
    call INIT
    ld   hl, (IL_LEFT)
    dec  hl
    ld   (IL_LEFT), hl
    ld   hl, (IL_ESIZE)
    ld   a, h
    or   l
    jr   nz, .advance
    ld   hl, (IL_ELEM)                 ; the next member
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    ld   (IL_ELEM), hl
    jr   .comma
.advance:
    ld   de, (IL_ADDR)
    add  hl, de
    ld   (IL_ADDR), hl
.comma:
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    jr   nz, .done
    ld   a, (IL_BRACED)
    or   a
    jr   nz, .more
    call .left
    jr   z, .done                      ; elided braces: the `,` belongs to the outer list
.more:
    call LEX_NEXT
    jr   .loop
.done:
    ld   hl, (IL_LEFT)                 ; given = $FFFF - left (for `[]`)
    ld   a, l
    cpl
    ld   l, a
    ld   a, h
    cpl
    ld   h, a
    ld   ix, IL_CELLS + 2 * IL_WORDS
    ld   b, IL_WORDS
    call CELLS_LOAD
    ld   b, h
    ld   c, l
    ret
.left:                                 ; NZ: an element is left
    ld   hl, (IL_LEFT)
    ld   a, h
    or   l
    ret
