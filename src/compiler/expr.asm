; ============================================================================
; src/compiler/expr.asm -- expression parsing and typing (spec.md 4.3-4.4)
;
; M1.2 part: constant expressions (array sizes, enum values, `sizeof`, static initialisers). This
; is the core of M1.3's expression compiler: the same recursive descent, operand descriptors and
; typing rules; M1.3 adds code emission for the operands that are not constant.
;
; The current operand is X (X_KIND, X_TYPE, X_VAL; include/leapc_decl.inc OK_*). A binary operator
; saves the left operand on the machine stack (CX_PUSHX) and gets it back as Y (CX_POPY). Typing:
; integer promotions (char -> int), the usual arithmetic conversions (unsigned if either operand
; is unsigned), pointer arithmetic scaled by the element size, array and function designators
; converted to pointers when used as values (CX_RVAL). Operations on constants are folded
; (CX_FOLD). In M1.2 a non-constant operand is accepted only where its value is not needed
; (`sizeof`); expression forms that are never constant (calls, assignment, ++/--, comma) arrive
; with M1.3.
; ============================================================================

CX_EXPR         EQU CX_COND            ; M1.3: the comma and assignment levels

; ============================================================================
; CX_CONST_INT -- an integer constant expression (array sizes, enum values; M1.3: case labels)
; Out: HL = the value; X = the operand (X_TYPE an integer type)
; Errors: E_CONSTEXPR, the expression errors
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
CX_CONST_INT:
    call CX_COND
    call CX_RVAL
    ld   a, (X_KIND)
    or   a
    jp   nz, CC_E_CONSTEXPR
    call TY_CLASS                      ; (HL = X_TYPE from CX_RVAL)
    dec  a
    cp   TC_UINT
    jp   nc, CC_E_CONSTEXPR
    ld   hl, (X_VAL)
    ret

; ============================================================================
; CX_CONST_INIT -- a static initialiser element: an integer or address constant
; Out: X = the operand (OK_CONST or OK_ADDRC, converted to a value)
; Errors: E_CONSTEXPR, the expression errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_CONST_INIT:
    call CX_COND
    call CX_RVAL
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  c
    jp   CC_E_CONSTEXPR

; ============================================================================
; CX_COND -- a conditional expression (C89 6.3.15)
; Out: X = the operand
; Errors: E_OPERAND, E_SYNTAX, the errors of the operands
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_COND:
    ld   b, 1
    call CX_BINARY
    ld   a, (TOK_KIND)
    cp   TK_QUEST
    ret  nz
    call CX_RVAL
    call CX_SCALAR_X
    call CX_PUSHX                      ; the condition
    call LEX_NEXT
    call CX_EXPR
    call CX_RVAL
    call CX_PUSHX                      ; the second operand
    ld   a, TK_COLON
    call CC_EXPECT
    call CX_COND
    call CX_RVAL                       ; X = the third operand
    call CX_POPY                       ; Y = the second
    pop  hl                            ; the condition: L = kind
    pop  de                            ; D = value low
    pop  bc                            ; C = value high
    ld   a, d
    or   c
    ld   c, a
    ld   a, l
    cp   OK_LVALC
    push af                            ; NC: the condition is not constant
    jr   nc, .types
    ld   a, c
    or   a
    call nz, CX_SWAP                   ; true: the second operand
.types:                                ; both integers: the usual conversions; an integer (a null
    ld   hl, (Y_TYPE)                  ; pointer constant) with a pointer: the pointer's type
    call TY_CLASS
    ld   d, a
    ld   hl, (X_TYPE)
    call TY_CLASS
    ld   e, a
    dec  a
    cp   TC_UINT
    jr   nc, .kind
    ld   a, d
    dec  a
    cp   TC_UINT
    ld   hl, (Y_TYPE)
    jr   nc, .set
    call CX_USUAL
.set:
    ld   (X_TYPE), hl
.kind:
    pop  af
    ret  c
CX_SET_RVAL:
    ld   a, OK_RVAL
    ld   (X_KIND), a
    ret

; ============================================================================
; CX_BINARY -- binary operators of precedence B or higher (precedence climbing)
; In:  B = lowest precedence to parse (1-10; CX_PREC_TABLE)
; Out: X = the operand
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_BINARY:
    push bc
    call CX_UNARY
    pop  bc
.loop:
    ld   a, (TOK_KIND)
    call CX_PREC
    cp   b
    ret  c                             ; not a binary operator, or a lower precedence
    push bc                            ; the lowest precedence
    ld   c, a
    ld   a, (TOK_KIND)
    ld   b, a
    push bc                            ; B = operator, C = its precedence
    call CX_RVAL
    call LEX_NEXT
    pop  bc
    push bc
    ld   a, c
    call CX_PUSHX                      ; the left operand
    inc  a
    ld   b, a
    call CX_BINARY                     ; the right operand: higher precedence (left assoc.)
    call CX_RVAL
    call CX_POPY
    pop  bc
    ld   a, b
    call CX_BINOP
    pop  bc
    jr   .loop

; CX_PREC -- A = precedence of binary operator token A (0: not one). Destroys: F, DE, HL
CX_PREC:
    sub  TK_ASSIGN
    cp   TK_GE - TK_ASSIGN + 1
    jr   nc, .none
    ld   e, a
    ld   d, 0
    ld   hl, CX_PREC_TABLE
    add  hl, de
    ld   a, (hl)
    ret
.none:
    xor  a
    ret
CX_PREC_TABLE:                         ; tokens TK_ASSIGN ($20) .. TK_GE ($43)
    DB   0, 0, 7, 7, 10, 10, 10, 9, 9, 5, 4, 3, 8, 8, 0, 0     ; = ! < > * / % + - & ^ | << >>
    DB   2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0        ; && ||
    DB   6, 6, 7, 7                                            ; == != <= >=
    ASSERT $ - CX_PREC_TABLE == TK_GE - TK_ASSIGN + 1

; ============================================================================
; CX_BINOP -- apply binary operator A to Y (left) and X (right), both values
; Out: X = the result: its type by C89 6.3.5-6.3.14; folded when both operands are constant
; Errors: E_OPERAND, E_INCOMPLETE (arithmetic on a pointer to an incomplete type)
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_BINOP:
    ld   (CX_OP), a
    ld   hl, (Y_TYPE)
    call TY_CLASS
    ld   d, a
    ld   hl, (X_TYPE)
    call TY_CLASS
    ld   e, a                          ; D = left class, E = right class
    ld   a, (CX_OP)
    cp   TK_PLUS
    jr   z, .add
    cp   TK_MINUS
    jp   z, .sub
    cp   TK_ANDAND
    jr   z, .logic
    cp   TK_OROR
    jr   z, .logic
    cp   TK_LT
    jr   z, .compare
    cp   TK_GT
    jr   z, .compare
    cp   TK_EQ
    jr   nc, .compare                  ; == != <= >=
    call .ints                         ; * / % & ^ | << >>: integers
    ld   a, (CX_OP)
    cp   TK_SHL
    jr   c, .usual
    ld   hl, (Y_TYPE)                  ; << >>: the promoted left operand's type
    call TY_PROMOTE
    ld   d, h
    ld   e, l
    jp   .do
.arith:
    call .ints
.usual:
    call CX_USUAL                      ; HL = DE = int or unsigned
    jp   .do
.logic:
    ld   a, d
    call CX_SCALAR_A
    ld   a, e
    call CX_SCALAR_A
    ld   hl, TY_INT
    jr   .intres
.compare:
    ld   a, d
    cp   TC_PTR
    jr   z, .cmpptr
    ld   a, e
    cp   TC_PTR
    jr   z, .cmpptr
    call .ints
    call CX_USUAL                      ; HL = the operation's type
    jr   .intres
.cmpptr:
    ld   a, d
    call CX_SCALAR_A
    ld   a, e
    call CX_SCALAR_A
    ld   hl, TY_UINT                   ; addresses compare unsigned
.intres:
    ld   de, TY_INT                    ; the result is an int
    jr   .do
.add:
    ld   a, d
    cp   TC_PTR
    jr   z, .ptrint
    ld   a, e
    cp   TC_PTR
    jr   nz, .arith
    push de                            ; integer + pointer: as pointer + integer
    call CX_SWAP
    pop  de
    ld   a, d
    ld   d, e
    ld   e, a
.ptrint:                               ; Y pointer, X integer: X scaled by the element size
    ld   a, e
    cp   TC_PTR
    jr   z, .arith                     ; (pointer + pointer: E_OPERAND from .ints)
    call CX_INT_A
    call .esize
    ld   de, (X_VAL)
    ld   b, h
    ld   c, l
    call MATH_UMUL16
    ld   (X_VAL), hl
    ld   hl, (Y_TYPE)
    ld   d, h
    ld   e, l
    jr   .do
.sub:
    ld   a, d
    cp   TC_PTR
    jr   nz, .arith
    ld   a, e
    cp   TC_PTR
    jr   nz, .ptrint
    call .esize                        ; pointer - pointer: the difference in elements
    push hl
    ld   hl, TY_INT
    ld   d, h
    ld   e, l
    call .do
    pop  de
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  nc
    ld   hl, (X_VAL)
    call MATH_DIVIDE16
    ld   (X_VAL), hl
    ret
.do:                                   ; HL = the operation's type, DE = the result's type
    ld   (X_TYPE), de
    ld   a, (Y_KIND)
    ld   b, a
    ld   a, (X_KIND)
    or   b
    cp   OK_LVALC
    jp   nc, CX_SET_RVAL               ; not constant (M1.3: code)
    ld   (X_KIND), a                   ; OK_CONST, or OK_ADDRC if either was one
    ld   de, TY_INT
    or   a
    sbc  hl, de
    ld   c, 0
    jr   z, .signed
    inc  c                             ; unsigned (and pointer) operation
.signed:
    ld   a, (CX_OP)
    ld   de, (Y_VAL)
    ld   hl, (X_VAL)
    call CX_FOLD
    ld   (X_VAL), hl
    ret
.ints:                                 ; both operands integers
    ld   a, d
    call CX_INT_A
    ld   a, e
    jr   CX_INT_A
.esize:                                ; HL = size of the type Y points to
    ld   hl, (Y_TYPE)
    call TY_DEREF
    jp   TY_SIZE

; ============================================================================
; CX_INT_A / CX_SCALAR_A -- class A must be an integer / a scalar (integer or pointer)
; CX_SCALAR_X -- X must be a scalar
; Errors: E_OPERAND
; Destroys: AF (CX_SCALAR_X: and HL)
; ============================================================================
CX_SCALAR_X:
    ld   hl, (X_TYPE)
    call TY_CLASS
CX_SCALAR_A:
    dec  a
    cp   TC_PTR
    ret  c
    jp   CC_E_OPERAND
CX_INT_A:
    dec  a
    cp   TC_UINT
    ret  c
    jp   CC_E_OPERAND

; ============================================================================
; CX_USUAL -- the usual arithmetic conversions of two integer classes (spec.md 4.3)
; In:  D, E = the operands' classes. Out: HL = DE = unsigned if either is unsigned, else int
; Destroys: AF
; ============================================================================
CX_USUAL:
    ld   hl, TY_UINT
    ld   a, d
    cp   TC_UINT
    jr   z, .done
    ld   a, e
    cp   TC_UINT
    jr   z, .done
    dec  l                             ; TY_INT
.done:
    ld   d, h
    ld   e, l
    ret

; ============================================================================
; TY_PROMOTE -- the integer promotion of a type: char and signed char become int
; In:  HL = type. Out: HL = promoted type. Destroys: AF
; ============================================================================
TY_PROMOTE:
    ld   a, h
    or   a
    ret  nz
    ld   a, l
    cp   TB_INT
    ret  nc
    ld   l, TB_INT
    ret

; ============================================================================
; CX_UNARY -- a unary expression (C89 6.3.3), including casts reached through CX_PRIMARY
; Out: X = the operand (not converted to a value)
; Errors: E_OPERAND, E_LVALUE, E_SYNTAX, E_INCOMPLETE, E_NESTING, the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_UNARY:
    call CC_STACKCHK
    ld   a, (TOK_KIND)
    cp   TK_MINUS
    jr   z, .arith
    cp   TK_PLUS
    jr   z, .arith
    cp   TK_TILDE
    jr   z, .arith
    cp   TK_NOT
    jr   z, .arith
    cp   TK_STAR
    jp   z, .deref
    cp   TK_AMP
    jp   z, .addr
    cp   TK_SIZEOF
    jp   nz, CX_POSTFIX
    ld   hl, CX_NOEVAL                 ; sizeof: the operand is not evaluated
    inc  (hl)
    call LEX_NEXT
    cp   TK_LPAREN
    jr   nz, .sz_unary
    call LEX_NEXT
    call IS_DECL_START
    jr   z, .sz_paren
    call TYPE_NAME                     ; sizeof ( type-name )
    push hl
    ld   a, TK_RPAREN
    call CC_EXPECT
    pop  hl
    jr   .sz
.sz_paren:                             ; sizeof ( expression ) postfix...
    call CX_PAREN_REST
    call CX_POSTFIX_LOOP
    jr   .sz_x
.sz_unary:
    call CX_UNARY
.sz_x:
    ld   hl, (X_TYPE)
.sz:
    ld   a, (CX_NOEVAL)
    dec  a
    ld   (CX_NOEVAL), a
    call TY_SIZE
    ld   (X_VAL), hl
    ld   hl, TY_UINT                   ; size_t: unsigned int
    ld   (X_TYPE), hl
    xor  a
    ld   (X_KIND), a
    ret
.arith:                                ; - + ~ !
    push af
    call LEX_NEXT
    call CX_UNARY
    call CX_RVAL                       ; HL = X_TYPE
    pop  af
    cp   TK_NOT
    jr   z, .not
    push af
    call TY_CLASS
    call CX_INT_A
    call TY_PROMOTE
    ld   (X_TYPE), hl
    pop  af
    cp   TK_PLUS
    ret  z
    ld   de, 0
    ld   b, TK_MINUS                   ; -x = 0 - x
    cp   b
    jr   z, .xfold
    dec  de
    ld   b, TK_CARET                   ; ~x = $FFFF ^ x
.xfold:
    ld   hl, (X_VAL)
.fold:                                 ; B = operator, DE = left, HL = right
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  nc
    ld   a, b
    call CX_FOLD
    ld   (X_VAL), hl
    ret
.not:                                  ; !x = (x == 0), an int
    call CX_SCALAR_X
    ld   hl, TY_INT
    ld   (X_TYPE), hl
    ld   de, (X_VAL)
    ld   hl, 0
    ld   b, TK_EQ
    jr   .fold
.deref:
    call LEX_NEXT
    call CX_UNARY
    call CX_RVAL
    jp   CX_DEREF
.addr:
    call LEX_NEXT
    call CX_UNARY
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_FUNC
    jp   z, CX_RVAL                    ; &function: the function's pointer
    ld   a, (X_KIND)
    cp   OK_LVALC
    ld   b, OK_ADDRC
    jr   z, .addr_k
    cp   OK_LVAL
    jp   nz, CC_E_LVALUE
    ld   b, OK_RVAL
.addr_k:
    ld   a, b
    ld   (X_KIND), a
    call TY_PTR                        ; (HL = X_TYPE)
    ld   (X_TYPE), hl
    ret

; ============================================================================
; CX_POSTFIX -- a primary expression and its postfix operators [ ] . ->
; CX_POSTFIX_LOOP -- the postfix operators after an operand already in X
; Out: X = the operand
; Errors: E_OPERAND, E_MEMBER, E_INCOMPLETE, E_SYNTAX, the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_POSTFIX:
    call CX_PRIMARY
CX_POSTFIX_LOOP:
    ld   a, (TOK_KIND)
    cp   TK_LBRACK
    jr   z, .index
    cp   TK_DOT
    jr   z, .member
    cp   TK_ARROW
    ret  nz
    call CX_RVAL                       ; p->m = (*p).m
    call CX_DEREF
.member:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_STRUCT
    jp   nz, CC_E_OPERAND
    call TY_FIELDS                     ; BC = first member
    ld   a, b
    or   c
    jp   z, TY_E_INCOMPLETE
    push bc
    call LEX_NEXT
    cp   TK_IDENT
    jp   nz, CC_E_SYNTAX
    call NM_FROM_TOK
    pop  hl
    ld   c, NS_MEMBER
    ld   de, 0
    call SYM_FIND
    jp   nz, CC_E_MEMBER
    call DCL_GETTYPE
    ld   (X_TYPE), hl
    ld   e, (ix + S_VAL)
    ld   d, (ix + S_VAL + 1)
    ld   hl, (X_VAL)
    add  hl, de                        ; the member's address (constant for a static struct)
    ld   (X_VAL), hl
    call LEX_NEXT
    jr   CX_POSTFIX_LOOP
.index:                                ; a[i] = *(a + i)
    call CX_RVAL
    call CX_PUSHX
    call LEX_NEXT
    call CX_EXPR
    ld   a, TK_RBRACK
    call CC_EXPECT
    call CX_RVAL
    call CX_POPY
    ld   a, TK_PLUS
    call CX_BINOP
    call CX_DEREF
    jr   CX_POSTFIX_LOOP

; ============================================================================
; CX_PRIMARY -- a primary expression, or a cast (C89 6.3.1, 6.3.4)
; Out: X = the operand
; Errors: E_UNDECL, E_SYNTAX, E_OPERAND, E_TOOBIG, E_NOMEM
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_PRIMARY:
    ld   a, (TOK_KIND)
    cp   TK_NUM
    jr   z, .number
    cp   TK_STR
    jp   z, .string
    cp   TK_IDENT
    jr   z, .ident
    cp   TK_LPAREN
    jp   nz, CC_E_SYNTAX
    call LEX_NEXT
    call IS_DECL_START
    jp   z, CX_PAREN_REST
    call TYPE_NAME                     ; a cast
    push hl
    ld   a, TK_RPAREN
    call CC_EXPECT
    call CX_UNARY
    call CX_RVAL
    pop  hl
    jp   CX_CAST
.number:                               ; int, or unsigned (u suffix, or above 32767)
    ld   hl, (TOK_VAL)
    ld   (X_VAL), hl
    ld   hl, TY_INT
    ld   a, (TOK_FLAGS)
    and  1 << TF_UNSIGNED
    jr   z, .ntype
    inc  l                             ; TY_UINT
.ntype:
    ld   (X_TYPE), hl
    xor  a                             ; OK_CONST
.kind:
    ld   (X_KIND), a
    jp   LEX_NEXT
.ident:
    call NM_FROM_TOK
    ld   c, NS_ORD
    call SYM_LOOKUP
    jp   nz, CC_E_UNDECL               ; (M1.3: `f(` declares f implicitly)
    call DCL_GETTYPE
    ld   (X_TYPE), hl
    ld   l, (ix + S_VAL)
    ld   h, (ix + S_VAL + 1)
    ld   (X_VAL), hl
    ld   a, (ix + S_KIND)
    cp   SK_ENUMC
    ld   b, OK_CONST
    jr   z, .bkind
    cp   SK_FUNC
    ld   b, OK_RVAL                    ; a function designator (M1.3: its address)
    jr   z, .bkind
    cp   SK_OBJ
    jp   nz, CC_E_SYNTAX               ; a typedef name
    ld   b, OK_LVAL
    ld   a, (ix + S_FLAGS)
    and  1 << SF_AUTO | 1 << SF_PARAM
    jr   nz, .bkind                    ; automatic: its address is not constant
    ld   a, h
    or   l
    jr   z, .bkind                     ; no storage yet
    ld   b, OK_LVALC                   ; static storage: a constant address
.bkind:
    ld   a, b
    jr   .kind
.string:                               ; a string literal: a static char array
    call STR_STAGE                     ; HL = bytes, BC = length
    inc  bc
    push bc
    ld   de, 0
    ld   a, (CX_NOEVAL)
    or   a
    jr   nz, .str_type
    push hl
    call DATA_ALLOC                    ; HL = address
    pop  de
    pop  bc
    push bc
    push hl
    ex   de, hl
    ldir
    pop  de
.str_type:
    ld   (X_VAL), de
    pop  bc
    ld   hl, TB_CHAR
    call TY_ARRAY
    ld   (X_TYPE), hl
    ld   a, OK_LVALC
    ld   (X_KIND), a
    ret

; CX_PAREN_REST -- `expression )` after a consumed `(`
CX_PAREN_REST:
    call CX_EXPR
    ld   a, TK_RPAREN
    jp   CC_EXPECT

; ============================================================================
; CX_RVAL -- use X as a value (C89 6.2.2.1): an array becomes a pointer to its first element, a
; function a pointer to it, an object its (run-time) value
; Out: X converted; HL = X_TYPE
; Destroys: AF, BC, DE
; ============================================================================
CX_RVAL:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_ARRAY
    jr   z, .array
    cp   TC_FUNC
    jr   z, .func
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  c
    jr   .rval                         ; loading an object: a run-time value (M1.3: code)
.array:
    call TY_DEREF
    call TY_PTR
    ld   (X_TYPE), hl
    ld   a, (X_KIND)
    cp   OK_LVALC
    ld   a, OK_ADDRC
    jr   z, .set                       ; a static array: a constant address
.rval:
    ld   a, OK_RVAL
.set:
    ld   (X_KIND), a
    ret
.func:
    call TY_PTR
    ld   (X_TYPE), hl
    jr   .rval

; ============================================================================
; CX_DEREF -- *X: X (a value) must be a pointer; X becomes the object it points to
; Errors: E_OPERAND
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_DEREF:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_PTR
    jp   nz, CC_E_OPERAND
    call TY_DEREF
    ld   (X_TYPE), hl
    ld   a, (X_KIND)
    cp   OK_LVALC
    ld   a, OK_LVALC                   ; a constant pointer: an object at a constant address
    jr   c, .set
    ld   a, OK_LVAL
.set:
    ld   (X_KIND), a
    ret

; ============================================================================
; CX_CAST -- convert X (a value) to type HL (spec.md 4.3: between integer and pointer types)
; Errors: E_OPERAND (to or from an array, function or struct type)
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_CAST:
    push hl
    ld   hl, (X_TYPE)
    call TY_CLASS
    pop  hl
    ld   (X_TYPE), hl
    ld   c, a                          ; C = the source class
    call TY_CLASS
    or   a
    jp   z, CX_SET_RVAL                ; (void)
    cp   TC_ARRAY
    jp   nc, CC_E_OPERAND
    ld   b, a
    ld   a, c
    call CX_SCALAR_A
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  nc                            ; (M1.3: code)
    ld   hl, (X_VAL)
    ld   a, b
    cp   TC_CHAR
    jr   z, .uchar
    cp   TC_SCHAR
    ret  nz
    ld   a, l                          ; signed char: sign-extend the low byte
    rla
    sbc  a, a
    ld   h, a
    jr   .store
.uchar:
    ld   h, 0
.store:
    ld   (X_VAL), hl
    ret

; ============================================================================
; CX_CHECK_ASSIGN -- can X (a value) be assigned to an object of type HL (spec.md 4.3)?
; Integers take integers; pointers take compatible pointers, void * either way, or the null
; pointer constant 0.
; Errors: E_TYPE
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_CHECK_ASSIGN:
    call TY_CLASS
    cp   TC_PTR
    jr   z, .ptr
    dec  a
    cp   TC_UINT
    jr   nc, .bad                      ; arrays, structs, void
    ld   hl, (X_TYPE)
    call TY_CLASS
    dec  a
    cp   TC_UINT
    ret  c
.bad:
    jp   CC_E_TYPE
.ptr:
    push hl
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_PTR
    jr   z, .pp
    pop  hl
    dec  a
    cp   TC_UINT
    jr   nc, .bad
    ld   a, (X_KIND)                   ; an integer: only the constant 0
    or   a
    jr   nz, .bad
    ld   hl, (X_VAL)
    ld   a, h
    or   l
    ret  z
    jr   .bad
.pp:
    call TY_DEREF                      ; HL = the source's target
    ld   a, h
    or   l
    jr   z, .void                      ; from void *
    ex   (sp), hl
    call TY_DEREF                      ; HL = the destination's target
    pop  de
    ld   a, h
    or   l
    ret  z                             ; to void *
    call TY_EQUAL
    ret  z
    jr   .bad
.void:
    pop  hl
    ret

; ============================================================================
; CX_PUSHX -- push X (6 bytes, under the return address); CX_POPY -- pop such a copy into Y
; CX_SWAP -- exchange X and Y
; Destroys: CX_PUSHX: DE, HL (AF, BC kept). CX_POPY: DE, HL. CX_SWAP: AF, BC, DE, HL
; ============================================================================
CX_PUSHX:
    pop  de
    ld   hl, (X_KIND + 4)
    push hl
    ld   hl, (X_KIND + 2)
    push hl
    ld   hl, (X_KIND)
    push hl
    ex   de, hl
    jp   (hl)
CX_POPY:
    pop  de
    pop  hl
    ld   (Y_KIND), hl
    pop  hl
    ld   (Y_KIND + 2), hl
    pop  hl
    ld   (Y_KIND + 4), hl
    ex   de, hl
    jp   (hl)
CX_SWAP:
    ld   hl, X_KIND
    ld   de, Y_KIND
    ld   b, 6
.loop:
    ld   a, (de)
    ld   c, (hl)
    ld   (hl), a
    ld   a, c
    ld   (de), a
    inc  hl
    inc  de
    djnz .loop
    ret
