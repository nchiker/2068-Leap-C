; ============================================================================
; src/compiler/stmt.asm -- function definitions and statements (spec.md 4.5, 4.6)
;
; M1.2 part: a function definition opens its parameters' scope again and parses the body: blocks
; of declarations (block scope, frame slots for automatic objects, sibling blocks sharing frame
; bytes) and nested blocks. M1.3 adds expression statements and `return`, Phase 2 the other
; statements.
; ============================================================================

; ============================================================================
; FUNC_DEF -- a function definition (spec.md 4.6; M1.2: the body's declarations and blocks)
; In:  HL = the function type, C = storage class, B = const; NM; current token = `{`;
;      LASTP_HEAD / LASTP_END = the function's parameters (the declarator's last parameter list)
; Out: current token after the body
; Errors: E_STORAGE (typedef), E_REDEF (second body), E_PARAM (unnamed parameter), body errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
FUNC_DEF:
    ld   a, c
    cp   SC_TYPEDEF
    jp   z, CC_E_STORAGE
    ld   de, (LASTP_NODE)              ; the declarator itself must give the parameter list
    or   a                             ; (not a typedef of a function type)
    sbc  hl, de
    add  hl, de
    jp   nz, CC_E_BADDECL
    push hl
    call DECLARE                       ; IX = the file-scope entry
    pop  hl
    bit  SF_DEFINED, (ix + S_FLAGS)
    jp   nz, CC_E_REDEF
    set  SF_DEFINED, (ix + S_FLAGS)
    call TY_FIELDS                     ; C = parameter count
    ld   b, c
    inc  b
    ld   hl, (LASTP_HEAD)
    jr   .check
.named:
    push hl
    pop  ix
    ld   a, (ix + S_LEN)
    or   a
    jp   z, CC_E_PARAM
    ld   l, (ix + S_LINK)
    ld   h, (ix + S_LINK + 1)
.check:
    djnz .named
    call SCOPE_OPEN                    ; the parameters' scope again: the body's outer block
    ld   hl, (LASTP_END)
    ld   (WS_LOC), hl
    ld   hl, (LASTP_HEAD)
    ld   (SYM_LOC), hl
    ld   hl, 0
    ld   (FRAME_OFS), hl
    ld   (FRAME_MAX), hl
    call LEX_NEXT
    call BLOCK_ITEMS
    call SCOPE_CLOSE
    jp   LEX_NEXT

; ============================================================================
; BLOCK -- a compound statement (current token `{`): a scope; frame slots reused after it
; BLOCK_ITEMS -- declarations, then statements, up to the closing `}` (not consumed)
; STATEMENT -- one statement (M1.2: a compound statement or `;`; M1.3 and Phase 2 add the rest)
; Errors: E_SYNTAX (end of source; a declaration after a statement), E_NOTSUP (other statements,
;      until M1.3), the declarations' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
BLOCK:
    call LEX_NEXT
    call SCOPE_OPEN
    ld   hl, (FRAME_OFS)
    push hl
    call BLOCK_ITEMS
    pop  hl
    ld   (FRAME_OFS), hl
    call SCOPE_CLOSE
    jp   LEX_NEXT
BLOCK_ITEMS:
    call IS_DECL_START
    jr   z, .stmts
    call DECLARATION
    jr   BLOCK_ITEMS
.stmts:
    ld   a, (TOK_KIND)
    cp   TK_RBRACE
    ret  z
    call STATEMENT
    jr   .stmts
STATEMENT:
    call CC_STACKCHK
    ld   a, (TOK_KIND)
    cp   TK_SEMI
    jp   z, LEX_NEXT
    cp   TK_LBRACE
    jr   z, BLOCK
    or   a
    jp   z, CC_E_SYNTAX
    call IS_DECL_START
    jp   nz, CC_E_SYNTAX               ; declarations come first in a block (C89)
    jp   CC_E_NOTSUP                   ; other statements: M1.3 and Phase 2

