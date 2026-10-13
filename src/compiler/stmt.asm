; ============================================================================
; src/compiler/stmt.asm -- function definitions and statements (spec.md 4.5, 4.6, 5.2, 5.7, 5.9)
;
; M1.2 part: a function definition opens its parameters' scope again and parses the body: blocks
; of declarations (block scope, frame slots for automatic objects, sibling blocks sharing frame
; bytes) and nested blocks. M1.3 part: the function's code (prologue, epilogue, the fixup chain of
; earlier references), expression statements and `return`, and the end of the compile (undefined
; functions, main). Phase 2: every other C89 statement, labels, the function -> line table.
;
; Frame (spec.md 5.2 as amended by the owner decision of 2026-10-13): `rst ENTER / db n` pushes
; IX and points IX at the saved IX; the locals are below it (IX-1 .. IX-n), the return address at
; IX+2 and the arguments from IX+4, first argument lowest. `rst LEAVE` returns from anywhere.
;
; Jumps (codegen.asm fixup chains). A statement's forward jumps (out of a loop, over an `else`, to
; a label not yet seen) are chains resolved when the target is placed; backward jumps go straight
; to the known address. Single-pass layouts, as in the spike (docs/C_FEASIBILITY_STUDY.md 4):
;   while (c) s       top: c / jp !c,out / s / jp top / out:
;   do s while (c);   top: s / cont: c / jp c,top / out:
;   for (i; c; n) s   i / top: c / jp !c,out / jp body / step: n / jp top / body: s / jp step / out:
;   switch (e) s      e / call RT_SWITCH / dw table / s / out:   (the table is static data)
; `break` and `continue` add a `jp` to the innermost loop's (or switch's) chain (BRK_CH, CNT_CH).
; ============================================================================

; ============================================================================
; FUNC_DEF -- a function definition (spec.md 4.6)
; In:  HL = the function type, C = storage class, B = const; NM; current token = `{`;
;      LASTP_HEAD / LASTP_END = the function's parameters (the declarator's last parameter list);
;      DCL_LINE = the line where the definition starts
; Out: current token after the body; the function's code emitted, earlier references resolved, its
;      record added to the function -> line table (RUN_FNLINES)
; Errors: E_STORAGE (typedef), E_REDEF (second body), E_PARAM (unnamed parameter), E_UNDEFLABEL,
;      body errors
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
    push de                            ; the function -> line table (spec.md 5.9): a record
    ld   bc, 6                         ; [link][address][line] in the image's static data
    call DATA_ALLOC
    ld   de, (RUN_FNLINES)
    ld   (RUN_FNLINES), hl
    call SW_PUT
    pop  de
    call SW_PUT
    ld   de, (DCL_LINE)
    call SW_PUT
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
    ld   hl, (FN_LABELS)               ; every label a goto names must be defined
    ld   bc, E_UNDEFLABEL << 8 | SK_LABEL
    call UNDEF_CHECK
    ld   (FN_LABELS), hl               ; (0)
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

; SW_PUT -- the word DE at HL; HL += 2. Destroys: -
SW_PUT:
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    ret

; ============================================================================
; UNDEF_CHECK -- every entry of kind C in the chain from HL whose fixup chain is in use (ends with
; a line, not 0) must be defined: functions used (CC_FINISH), labels named by a goto (FUNC_DEF)
; In:  HL = the first entry, C = the kind (SK_*), B = the error
; Out: HL = 0 (the chain's end)
; Errors: B, at the line of the first use
; Destroys: AF, HL, IX
; CHAIN_END -- HL = the end of fixup chain HL (a value below LEAPC_IMG4_BASE). Destroys: AF
; ============================================================================
UNDEF_CHECK:
    ld   a, h
    or   l
    ret  z
    push hl
    pop  ix
    ld   a, (ix + S_KIND)
    cp   c
    jr   nz, .next
    bit  SF_DEFINED, (ix + S_FLAGS)
    jr   nz, .next
    ld   l, (ix + S_VAL)               ; declared only: used? (its chain ends with the line of the
    ld   h, (ix + S_VAL + 1)           ; first use)
    call CHAIN_END
    ld   a, h
    or   l
    ld   a, b
    jp   nz, CC_ERROR_AT
.next:
    ld   l, (ix + S_LINK)
    ld   h, (ix + S_LINK + 1)
    jr   UNDEF_CHECK
CHAIN_END:
    ld   a, h
    cp   LEAPC_IMG4_BASE >> 8
    ret  c
    rst  $08                           ; LDI: the next link
    jr   CHAIN_END

; ============================================================================
; BLOCK -- a compound statement (current token `{`): a scope; frame slots reused after it
; BLOCK_ITEMS -- declarations, then statements, up to the closing `}` (not consumed)
; STATEMENT -- one statement (C89 6.6): compound, empty, expression, selection, iteration, jump,
; labeled
; Errors: E_SYNTAX (end of source; a declaration after a statement), the statements' errors
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
    ld   hl, STMT_KW
    ld   b, STMT_KW_N
.kw:                                   ; [keyword][handler] ...: the handler starts at the keyword
    cp   (hl)
    inc  hl
    jr   z, .handler
    inc  hl
    inc  hl
    djnz .kw
    call IS_DECL_START                 ; declarations come first in a block (C89)
    jp   nz, CC_E_SYNTAX
    ld   a, (TOK_KIND)
    cp   TK_IDENT
    jr   z, .ident
    cp   TK_KW_FIRST
    jr   c, .expr
    cp   TK_SIZEOF
    jp   nz, CC_E_SYNTAX               ; `else` without `if`
.expr:                                 ; an expression statement: its value is not used
    call STMT_EXPR
    jr   STMT_END
.handler:
    rst  $08                           ; LDI: HL = the handler
    jp   (hl)
.ident:                                ; `name :` is a label (NM = the name, from IS_DECL_START)
    call LEX_MARK
    call LEX_NEXT
    cp   TK_COLON
    jr   z, .label
    call LEX_RESTORE
    call LEX_NEXT
    jr   .expr
.label:
    pop  bc                            ; (the mark)
    pop  bc
    pop  bc
    call LABEL_LOOKUP                  ; IX = the label, HL = its gotos' chain
    jp   nz, CC_E_REDEF
    set  SF_DEFINED, (ix + S_FLAGS)
    call CG_HERE                       ; the gotos so far land here (DE = the address)
    ld   (ix + S_VAL), e
    ld   (ix + S_VAL + 1), d
    call LEX_NEXT                      ; past `:`
    jr   STATEMENT


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
; DCL_AUTOINIT -- `= expression` after an automatic object's declarator (spec.md 4.7): the code of
; `object = expression` (a const object too); arrays and structs: not supported
; In:  IX = the object's entry (decl.asm DECLARE); current token `=`
; Errors: E_NOTSUP, E_TYPE, the expression's errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
DCL_AUTOINIT:
    call DCL_GETTYPE
    call TY_CLASS
    cp   TC_ARRAY
    jp   nc, CC_E_NOTSUP
    call CX_PRIMARY.found              ; X = the object; current token after `=`
    call .assign
    jp   CX_DISCARD
.assign:                               ; (the held object under this frame's return address, as
    call CX_LVHOLD                     ; in CX_ASSIGN)
    call CX_HOLD
    call CX_ASSIGN
    call CX_RVAL
    jp   CX_ASSIGN.store

; ============================================================================
; STMT_GOTO -- `goto label ;` (the label may come later in the function)
; STMT_BREAK, STMT_CONTINUE -- `break ;`, `continue ;`
; Errors: E_SYNTAX, E_BREAK, E_CONTINUE
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
STMT_GOTO:
    call LEX_NEXT
    cp   TK_IDENT
    jp   nz, CC_E_SYNTAX
    call NM_FROM_TOK
    call LABEL_LOOKUP
    ld   a, $C3                        ; jp
    jr   nz, .known
    call CG_JP
    ld   (ix + S_VAL), l
    ld   (ix + S_VAL + 1), h
    jr   STMT_NEXT
.known:
    call CG_OPW
STMT_NEXT:                             ; past the statement's last token, then `;`
    call LEX_NEXT
    jr   STMT_END
STMT_BREAK:
    ld   hl, BRK_CH
    ld   b, E_BREAK
    jr   STMT_JUMP
STMT_CONTINUE:
    ld   hl, CNT_CH
    ld   b, E_CONTINUE
STMT_JUMP:                             ; a jp added to the chain in cell HL (0: error B)
    push hl
    rst  $08                           ; LDI: HL = the chain
    ld   a, h
    or   l
    ld   a, b
    jp   z, CC_ERROR
    ld   a, $C3
    call CG_JP
    ex   de, hl
    pop  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    jr   STMT_NEXT

; LABEL_LOOKUP -- IX = the label NM of the current function: found, or made (not defined; its value,
; the chain of the gotos, ends with the current line)
; Out: HL = its value (the address, or the chain); NZ: defined. Destroys: AF, BC, DE
LABEL_LOOKUP:
    ld   c, NS_LABEL
    ld   de, 0
    ld   hl, (FN_LABELS)
    call SYM_FIND
    jr   z, .found
    ld   a, SK_LABEL
    call SYM_MAKE_G                    ; (the global area: the label outlives the blocks)
    ld   de, FN_LABELS
    call SYM_LINK
    ld   hl, (TOK_LINE)
    ld   (ix + S_VAL), l
    ld   (ix + S_VAL + 1), h
.found:
    ld   l, (ix + S_VAL)
    ld   h, (ix + S_VAL + 1)
    bit  SF_DEFINED, (ix + S_FLAGS)
    ret

; ============================================================================
; STMT_IF -- `if ( e ) s` [ `else s` ]
; STMT_WHILE, STMT_DO, STMT_FOR -- the loops (layouts above)
; Errors: E_SYNTAX, E_OPERAND (a condition that is not a scalar), the parts' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
STMT_IF:
    call STMT_COND                     ; HL = the jump when false
    push hl
    call STATEMENT
    ld   a, (TOK_KIND)
    cp   TK_ELSE
    jr   nz, .end
    ld   hl, 1
    ld   a, $C3
    call CG_JP                         ; over the else part
    ex   (sp), hl
    call CG_HERE                       ; the else part
    call LEX_NEXT
    call STATEMENT
.end:
    pop  hl
    jp   CG_HERE
STMT_DO:
    call LOOP_OPEN
    call LEX_NEXT
    ld   hl, (CG_PC)
    push hl                            ; [the top]
    call STATEMENT
    ld   a, (TOK_KIND)
    cp   TK_WHILE
    jp   nz, CC_E_SYNTAX
    ld   hl, (CG_PC)
    ex   (sp), hl
    push hl                            ; [the top][the condition: continue's target]
    call STMT_PAREN
    ld   hl, 1
    call CG_JTRUE                      ; back to the top
    pop  de
    call CG_PATCH
    call STMT_END
    pop  de
    jr   LOOP_CLOSE
STMT_WHILE:
    call LOOP_OPEN
    ld   hl, (CG_PC)
    push hl                            ; the top: the condition
    call STMT_COND
    ld   (BRK_CH), hl                  ; its jump out is the first break
    call STATEMENT
                                       ; fall through
; LOOP_BACK -- (jumped to, [the target] then LOOP_OPEN's words on the stack) `jp target`, which
; is also continue's, then LOOP_CLOSE
LOOP_BACK:
    pop  hl
    push hl
    ld   a, $C3
    call CG_OPW
    pop  de
; LOOP_CLOSE -- (jumped to, LOOP_OPEN's words on top of the stack) the loop ends: continue's chain
; to DE, break's chain here; the enclosing loop's chains again
LOOP_CLOSE:
    ld   hl, (CNT_CH)
    call CG_PATCH
    ld   hl, (BRK_CH)
    call CG_HERE
    pop  hl
    ld   (CNT_CH), hl
    pop  hl
    ld   (BRK_CH), hl
    ret
; LOOP_OPEN -- a loop starts: the enclosing break and continue chains are saved under the return
; address (LOOP_CLOSE restores them), the new ones are empty. Destroys: DE, HL
LOOP_OPEN:
    pop  de
    ld   hl, (BRK_CH)
    push hl
    ld   hl, (CNT_CH)
    push hl
    ld   hl, 1
    ld   (BRK_CH), hl
    ld   (CNT_CH), hl
    ex   de, hl
    jp   (hl)
STMT_FOR:
    call LOOP_OPEN
    call LEX_NEXT
    ld   a, TK_LPAREN
    call CC_EXPECT
    cp   TK_SEMI
    call nz, STMT_EXPR                 ; the initialisation

    call STMT_END
    ld   hl, (CG_PC)
    push hl                            ; [the condition]: each iteration starts here
    cp   TK_SEMI
    jr   z, .forever
    call STMT_TESTF
    ld   (BRK_CH), hl                  ; the jump out is the first break
.forever:
    call STMT_END
    cp   TK_RPAREN
    jr   z, .body                      ; no step: continue goes to the condition
    ld   hl, 1
    ld   a, $C3
    call CG_JP                         ; over the step, to the body
    ld   de, (CG_PC)
    ex   (sp), hl                      ; HL = the condition, [the body's chain]
    push de                            ; [the step][the body's chain]
    push hl                            ; [the condition][the step][the body's chain]
    call STMT_EXPR                     ; the step
    pop  hl
    ld   a, $C3
    call CG_OPW                        ; jp the condition
    pop  de
    pop  hl
    push de                            ; [the step]: continue's target
    call CG_HERE                       ; the body
.body:                                 ; [continue's target]
    ld   a, TK_RPAREN
    call CC_EXPECT
    call STATEMENT
    jp   LOOP_BACK
; STMT_PAREN -- after a keyword: `( expression )`, X a scalar value
; STMT_COND -- the same, then the jump when it is false: HL = its chain
; STMT_TESTF -- an expression, a scalar, and the jump when it is false: HL = its chain
; STMT_EXPR -- an expression whose value is not used
STMT_COND:
    call STMT_PAREN
STMT_JF:
    ld   hl, 1
    jp   CG_JFALSE
STMT_PAREN:
    call LEX_NEXT
    ld   a, TK_LPAREN
    call CC_EXPECT
    call STMT_SCALAR
    ld   a, TK_RPAREN
    jp   CC_EXPECT
STMT_TESTF:
    call STMT_SCALAR
    jr   STMT_JF
STMT_SCALAR:
    call CX_EXPR
    call CX_RVAL
    jp   CX_SCALAR_X
STMT_EXPR:
    call CX_EXPR
    jp   CX_DISCARD

; ============================================================================
; STMT_SWITCH -- `switch ( e ) s` (spec.md 4.5: an int, unsigned or char value). The value goes to
; RT_SWITCH with the address of a table in the image's static data, made at the end from the case
; labels seen in s: sparse [n][default] [value][address]..., or dense when that is smaller,
; [range | $8000][default][lowest value] [address]... (src/runtime/helpers.asm)
; STMT_CASE, STMT_DEFAULT -- `case constant :` and `default :` labels
; Errors: E_OPERAND (not an integer), E_CASE (outside a switch), E_DUPCASE, E_CONSTEXPR, E_SYNTAX
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
STMT_SWITCH:
    call STMT_PAREN
    ld   hl, (X_TYPE)
    call TY_CLASS
    call CX_INT_A
    call CG_LOAD                       ; the value in HL
    ld   hl, RT_SWITCH
    call CG_CALL                       ; call RT_SWITCH / dw table: one unit
    ld   hl, (CG_PC)
    push hl                            ; [the table's word]
    call CG_W
    ld   ix, SW_CASES
    ld   b, 3
    call CELLS_SAVE                    ; the enclosing switch and break chain
    ld   hl, 0
    ld   (SW_CASES), hl
    inc  l
    ld   (SW_DEFAULT), hl              ; in a switch, no default yet
    ld   (BRK_CH), hl
    call STATEMENT
    ld   hl, (BRK_CH)
    call CG_HERE                       ; the end (DE)
    call SW_TABLE                      ; HL = the table
    ld   ix, SW_CASES + 6
    ld   b, 3
    call CELLS_LOAD
    ex   de, hl
    pop  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ret
STMT_CASE:
    call SW_IN
    call LEX_NEXT
    call CX_CONST_INT                  ; HL = the value
    ex   de, hl
    call SW_FIND
    jr   z, SW_E_DUP                   ; not twice in a switch
    push de
    ld   bc, 6
    call WS_GALLOC                     ; HL = the record [link][value][address]
    ld   de, (SW_CASES)
    ld   (SW_CASES), hl
    call SW_PUT
    pop  de
    call SW_PUT
    push hl
    call SW_LABEL                      ; DE = its address
    pop  hl
    call SW_PUT
    jp   STATEMENT
STMT_DEFAULT:
    call SW_IN
    dec  hl
    ld   a, h
    or   l
    jr   nz, SW_E_DUP                  ; a second default
    call LEX_NEXT
    call SW_LABEL
    ld   (SW_DEFAULT), de
    jp   STATEMENT
SW_E_DUP:
    ld   a, E_DUPCASE
    jp   CC_ERROR
; SW_IN -- inside a switch? Out: HL = SW_DEFAULT. Errors: E_CASE. Destroys: AF
SW_IN:
    ld   hl, (SW_DEFAULT)
    ld   a, h
    or   l
    ret  nz
    ld   a, E_CASE
    jp   CC_ERROR
; SW_LABEL -- `:`, then a case label here: DE = its address. Destroys: AF, BC, HL
SW_LABEL:
    ld   a, TK_COLON
    call CC_EXPECT
    ld   hl, 1
    jp   CG_HERE
; SW_FIND -- the case record of the current switch with the value DE
; Out: Z: HL = the record. NZ: none. Destroys: AF, HL
SW_FIND:
    ld   hl, (SW_CASES)
.record:
    ld   a, h
    or   l
    jr   z, .none
    push hl
    inc  hl
    inc  hl
    ld   a, (hl)
    cp   e
    jr   nz, .no
    inc  hl
    ld   a, (hl)
    cp   d
.no:
    pop  hl
    ret  z
    rst  $08                           ; LDI: the next record
    jr   .record
.none:
    inc  a                             ; NZ
    ret

; ============================================================================
; SW_TABLE -- the current switch's table for RT_SWITCH, in the image's static data: dense when
; that is smaller (range <= 2 n - 2), else sparse
; In:  DE = the switch's end (the target when nothing matches and there is no default)
; Out: HL = the table
; Errors: E_TOOBIG
; Destroys: AF, BC, DE, IX
; ============================================================================
SW_TABLE:
    ld   hl, (SW_DEFAULT)
    dec  hl
    ld   a, h
    or   l
    jr   z, .nodef
    inc  hl
    ex   de, hl
.nodef:
    ld   (SW_DEFAULT), de              ; the target without a match
    ld   ix, 0                         ; the number of cases ...
    ld   de, $FFFF                     ; ... the lowest value (bit 15 flipped) ...
    ld   bc, 0                         ; ... and the highest
    ld   hl, (SW_CASES)
.scan:
    ld   a, h
    or   l
    jr   z, .size
    inc  ix
    push hl
    inc  hl
    inc  hl
    rst  $08                           ; LDI: HL = the value
    ld   a, h
    xor  $80
    ld   h, a                          ; in the signed order (any order makes a correct table)
    or   a
    sbc  hl, de
    add  hl, de
    jr   nc, .nlo
    ld   d, h
    ld   e, l
.nlo:
    or   a
    sbc  hl, bc
    add  hl, bc
    jr   c, .nhi
    ld   b, h
    ld   c, l
.nhi:
    pop  hl
    rst  $08                           ; LDI: the next record
    jr   .scan
.size:                                 ; IX = n, DE = the lowest, BC = the highest
    ld   h, b
    ld   l, c
    sbc  hl, de                        ; (C clear) the highest - the lowest
    ld   b, h
    ld   c, l
    ld   a, d
    xor  $80
    ld   d, a                          ; DE = the lowest value
    push ix
    pop  hl
    push hl                            ; [n]
    add  hl, hl
    dec  hl
    dec  hl
    dec  hl
    sbc  hl, bc                        ; (C clear) dense (6 + 2 range bytes) when smaller than
    jr   c, .sparse                    ; sparse (4 + 4 n): highest - lowest <= 2 n - 3
    inc  bc                            ; BC = the range (n = 0: 2)
    pop  af                            ; dense: [range|$8000][default][lowest] [address] ...
    push bc
    ld   h, b
    ld   l, c
    add  hl, hl
    ld   bc, 6
    add  hl, bc
    ld   b, h
    ld   c, l
    push de
    call DATA_ALLOC                    ; HL = the table
    pop  de
    pop  bc
    push hl                            ; [table]
    ld   (hl), c
    inc  hl
    ld   a, b
    or   $80
    ld   (hl), a
    inc  hl
    push de
    ld   de, (SW_DEFAULT)
    call SW_PUT
    pop  de
    call SW_PUT
.fill:                                 ; the entries of the values from the lowest on
    push bc
    push hl
    call SW_FIND
    ld   bc, 4
    add  hl, bc
    jr   z, .case
    ld   hl, SW_DEFAULT
.case:
    rst  $08                           ; LDI: HL = the address
    ld   b, h
    ld   c, l
    pop  hl
    ld   (hl), c
    inc  hl
    ld   (hl), b
    inc  hl
    inc  de
    pop  bc
    dec  bc
    ld   a, b
    or   c
    jr   nz, .fill
    pop  hl
    ret
.sparse:                               ; [n][default] [value][address] ...
    pop  de
    push de
    ex   de, hl
    add  hl, hl
    add  hl, hl
    inc  hl
    inc  hl
    inc  hl
    inc  hl
    ld   b, h
    ld   c, l
    call DATA_ALLOC
    pop  de
    push hl                            ; [table]
    call SW_PUT
    ld   de, (SW_DEFAULT)
    call SW_PUT
    ex   de, hl                        ; DE -> the entries
    ld   hl, (SW_CASES)
.copy:
    ld   a, h
    or   l
    jr   z, .end
    push hl
    inc  hl
    inc  hl
    ld   bc, 4
    ldir
    pop  hl
    rst  $08                           ; LDI: the next record
    jr   .copy
.end:
    pop  hl
    ret

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
    ld   bc, E_UNDEFFN << 8 | SK_FUNC
    call UNDEF_CHECK
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

; statement keywords and their handlers (STATEMENT), the frequent ones first
STMT_KW:
    DB   TK_IF
    DW   STMT_IF
    DB   TK_RETURN
    DW   RETURN
    DB   TK_WHILE
    DW   STMT_WHILE
    DB   TK_FOR
    DW   STMT_FOR
    DB   TK_BREAK
    DW   STMT_BREAK
    DB   TK_SWITCH
    DW   STMT_SWITCH
    DB   TK_CASE
    DW   STMT_CASE
    DB   TK_DEFAULT
    DW   STMT_DEFAULT
    DB   TK_DO
    DW   STMT_DO
    DB   TK_CONTINUE
    DW   STMT_CONTINUE
    DB   TK_GOTO
    DW   STMT_GOTO
STMT_KW_N       EQU ($ - STMT_KW) / 3
