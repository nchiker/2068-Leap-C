; ============================================================================
; src/compiler/stmt.asm -- function definitions and statements (spec.md 4.5, 4.6, 5.2, 5.7)
;
; M1.2 part: a function definition opens its parameters' scope again and parses the body: blocks
; of declarations (block scope, frame slots for automatic objects, sibling blocks sharing frame
; bytes) and nested blocks. M1.3 part: the function's code (prologue, epilogue, the fixup chain of
; earlier references), expression statements and `return`, and the end of the compile (undefined
; functions, main). Phase 2 adds the other statements.
;
; Frame (spec.md 5.2 as amended by the owner decision of 2026-10-13): `rst ENTER / db n` pushes
; IX and points IX at the saved IX; the locals are below it (IX-1 .. IX-n), the return address at
; IX+2 and the arguments from IX+4, first argument lowest. `rst LEAVE` returns from anywhere.
; ============================================================================

; ============================================================================
; FUNC_DEF -- a function definition (spec.md 4.6)
; In:  HL = the function type, C = storage class, B = const; NM; current token = `{`;
;      LASTP_HEAD / LASTP_END = the function's parameters (the declarator's last parameter list)
; Out: current token after the body; the function's code emitted, earlier references resolved
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
    call TY_FIELDS                     ; DE = the return type, C = parameter count
    ld   (FN_RET), de
    push bc
    ld   a, $DF                        ; code: the prologue, rst ENTER
    call CG_OP
    ld   hl, (CG_PC)
    ld   (CG_ENTN), hl
    dec  hl                            ; the function's address
    ex   de, hl
    ld   l, (ix + S_VAL)
    ld   h, (ix + S_VAL + 1)
    ld   (ix + S_VAL), e
    ld   (ix + S_VAL + 1), d
    call CG_PATCH                      ; the references made before the definition
    xor  a
    call CG_B                          ; n: the frame size, known at the end
    pop  bc
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
    ld   hl, (CG_PC)                   ; the end: LEAVE, unless the code has just returned
    ld   de, (CG_LASTLV)
    or   a
    sbc  hl, de
    ld   a, $E7                        ; rst LEAVE
    call nz, CG_OP
    ld   a, (FRAME_MAX)
    ld   hl, (CG_ENTN)
    ld   (hl), a
    jp   LEX_NEXT

; ============================================================================
; BLOCK -- a compound statement (current token `{`): a scope; frame slots reused after it
; BLOCK_ITEMS -- declarations, then statements, up to the closing `}` (not consumed)
; STATEMENT -- one statement: a compound statement, `;`, `return`, an expression statement
; (M1.3); the other statements arrive in Phase 2
; Errors: E_SYNTAX (end of source; a declaration after a statement), E_NOTSUP (statements of
;      Phase 2), the declarations' and expressions' errors
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
    cp   TK_RETURN
    jr   z, RETURN
    call IS_DECL_START
    jp   nz, CC_E_SYNTAX               ; declarations come first in a block (C89)
    ld   a, (TOK_KIND)
    cp   TK_KW_FIRST
    jr   c, .expr
    cp   TK_SIZEOF
    jp   nz, CC_E_NOTSUP               ; if, while, do, for, switch, goto, ...: Phase 2
.expr:                                 ; an expression statement: its value is not used
    call CX_EXPR
    call CX_DISCARD
    jr   STMT_END

; ============================================================================
; RETURN -- `return ;` or `return expression ;` (C89 6.6.6.4): the value converted to the
; function's return type, in HL (a char: H = 0, a signed char: H = its sign; spec.md 5.1)
; Errors: E_TYPE (a value in a void function, or one that cannot be converted), the
;      expression's errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
RETURN:
    call LEX_NEXT
    cp   TK_SEMI
    jr   z, .leave
    call CX_EXPR
    call CX_RVAL
    ld   hl, (FN_RET)
    ld   a, h
    or   l
    jp   z, CC_E_TYPE                  ; a value in a void function
    call CX_CHECK_ASSIGN
    ld   hl, (FN_RET)
    call CX_CAST                       ; (a constant: folded; else the conversion's code)
    call CG_LOAD
.leave:
    ld   a, $E7                        ; rst LEAVE
    call CG_OP
    ld   hl, (CG_PC)
    ld   (CG_LASTLV), hl
STMT_END:
    ld   a, TK_SEMI
    jp   CC_EXPECT

; ============================================================================
; CC_FINISH -- the end of a compile: every function used must be defined; RUN_MAIN / RUN_VOID
; for main (0 if there is none: CC_PROGRAM reports it)
; Out: NC
; Errors: E_UNDEFFN (at the line of the function's first use)
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CC_FINISH:
    ld   hl, (CG_PC)                   ; the code's reserve is free again
    ld   de, (CG_RLIM)
    ex   de, hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ld   hl, (SYM_GLO)
.entry:
    ld   a, h
    or   l
    jr   z, .main
    push hl
    pop  ix
    ld   a, (ix + S_KIND)
    cp   SK_FUNC
    jr   nz, .next
    bit  SF_DEFINED, (ix + S_FLAGS)
    jr   nz, .next
    ld   l, (ix + S_VAL)               ; declared only: used? (its chain ends with the line of
    ld   h, (ix + S_VAL + 1)           ; the first use)
.link:
    ld   a, h
    cp   LEAPC_IMG4_BASE >> 8
    jr   c, .end
    rst  $08                          ; LDI: HL = (HL)
    jr   .link
.end:
    ld   a, h
    or   l
    ld   a, E_UNDEFFN
    jp   nz, CC_ERROR_AT
.next:
    ld   l, (ix + S_LINK)
    ld   h, (ix + S_LINK + 1)
    jr   .entry
.main:
    ld   hl, CC_MAIN_NAME
    ld   (NM_PTR), hl
    ld   a, 4
    ld   (NM_LEN), a
    ld   c, NS_ORD
    ld   de, 0
    ld   hl, (SYM_GLO)
    call SYM_FIND
    ret  nz                            ; (NC) no main
    ld   a, (ix + S_KIND)
    cp   SK_FUNC
    ret  nz
    ld   l, (ix + S_VAL)
    ld   h, (ix + S_VAL + 1)
    ld   (RUN_MAIN), hl
    call DCL_GETTYPE
    call TY_FIELDS                     ; DE = the return type
    ld   a, d
    or   e
    jr   nz, .ok
    inc  a
    ld   (RUN_VOID), a
.ok:
    or   a                             ; NC
    ret
CC_MAIN_NAME:
    DB   "main"

; ============================================================================
; CC_PROGRAM -- compile a program to run: CC_COMPILE, and main must be defined
; Out: NC: compiled (RUN_MAIN). C: error, CC_ERRNUM / CC_ERRLINE (E_NOMAIN: at the last line)
; Destroys: AF, BC, DE, HL (IX kept)
; ============================================================================
CC_PROGRAM:
    call CC_COMPILE
    ret  c
    ld   hl, (RUN_MAIN)
    ld   a, h
    or   l
    ret  nz
    ld   a, E_NOMAIN
    ld   (CC_ERRNUM), a
    ld   hl, (TOK_LINE)
    ld   (CC_ERRLINE), hl
    scf
    ret
