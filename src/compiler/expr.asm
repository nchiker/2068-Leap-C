; ============================================================================
; src/compiler/expr.asm -- expressions: parsing, typing and code (spec.md 4.3-4.4)
;
; Recursive descent over C89's expression grammar: comma, assignment, conditional, the binary
; operators by precedence climbing, unary, postfix, primary. The current operand is X (X_KIND,
; X_TYPE, X_VAL, X_FLAGS; include/leapc_decl.inc OK_*). A binary operator holds its left operand
; (CX_HOLD) while the right one is parsed and gets it back as Y (CX_POPY).
;
; Typing: integer promotions (char -> int), the usual arithmetic conversions (unsigned if either
; operand is unsigned), pointer arithmetic scaled by the element size, array and function
; designators converted to pointers when used as values (CX_RVAL). Operations on constants are
; folded (CX_FOLD); the others emit code as they are recognised (codegen.asm). A deferred object
; keeps its own type until it is loaded, so its load has the object's width.
;
; The same parser evaluates the constant expressions of declarations (M1.2): array sizes, enum
; values, static initialisers, `sizeof`. There an operand that is not constant is an error
; (E_CONSTEXPR) and `sizeof` emits nothing (CX_MUTE).
;
; Floating point (Phase 8, spec.md 4.9): a float value is computed in F_ACC (src/runtime/float.asm),
; a held one is a 3-word stack slot. Floating constants are compile-time constants (OK_CONST with
; their 5 bytes in the compile workspace): negation, casts and + - * / of constants are folded by the
; float core (CX_FOLD), so constant float expressions initialise static data.
; ============================================================================

; ============================================================================
; CX_CONST_INT -- an integer constant expression (array sizes, enum values; Phase 2: case labels)
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
; CX_CONST_INIT -- a static initialiser element: an integer or address constant, or the address
; of a function (OK_FUNC: stored through the function's fixup chain)
; Out: X = the operand, converted to a value
; Errors: E_CONSTEXPR, the expression errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_CONST_INIT:
    call CX_COND
    call CX_RVAL
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  c
    cp   OK_FUNC
    ret  z
    jp   CC_E_CONSTEXPR

; ============================================================================
; CX_EXPR -- an expression (C89 6.3.17): assignment expressions separated by commas; the value of
; each but the last is not used
; Out: X = the operand
; Errors: the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_EXPR:
    call CX_ASSIGN
.comma:
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    ret  nz
    call CX_DISCARD
    call CX_NEXTV
    jr   .comma

; CX_NEXTV -- step past the current token, then an assignment expression as a value (CX_RVAL)
; Destroys: AF, BC, DE, HL, IX; NM
CX_NEXTV:
    rst  $30                          ; LEX_NEXT
    call CX_ASSIGN
    jp   CX_RVAL

; ============================================================================
; CX_ASSIGN -- an assignment expression (C89 6.3.16): `lvalue = value`, `lvalue op= value`
; Out: X = the operand; an assignment's value in HL (OK_RVAL), with the left operand's type
; Errors: E_LVALUE, E_CONST, E_NOTSUP (struct assignment), E_TYPE, E_OPERAND, the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_ASSIGN:
    call CX_COND
    ld   a, (TOK_KIND)
    cp   TK_ASSIGN
    jr   z, .assign
    cp   TK_MULASSIGN
    ret  c
    cp   TK_SHRASSIGN + 1
    ret  nc
.assign:
    push af
    call CX_LVALUE
    call CX_LVHOLD
    pop  af
    cp   TK_ASSIGN
    jr   z, .simple
    push af                            ; op=: the object's value is the left operand
    ld   a, (X_KIND)
    cp   OK_LVAL
    ld   a, $E5                        ; push hl: its address, for the store
    call z, CG_OP
    pop  af
    call CX_PUSHX                      ; [lvalue]
    push af                            ; [op][lvalue]
    ld   a, (X_KIND)
    cp   OK_LVAL
    call z, CG_LOAD
    call CX_HOLDV                      ; [left][op][lvalue]
    call CX_NEXTV
    call CX_POPY
    pop  af
    sub  TK_ASSIGN_OFS
    call CX_BINOP                      ; X = the result
    jr   .store
.simple:
    call CX_HOLD                       ; [lvalue] (an address in HL is held)
    call CX_NEXTV
.store:
    call CX_POPY                       ; Y = the lvalue
    ld   hl, (Y_TYPE)
    call CX_CHECK_ASSIGN
    ld   hl, (Y_TYPE)
    call CX_CONV                       ; a constant: converted now; int <-> float
    call CG_STORE
    ld   hl, (Y_TYPE)
    ld   (X_TYPE), hl
    call TY_CLASS
    call CG_TAILON                     ; the value as a byte object holds it (char: H = 0 or the
    call CG_EXT0                       ; sign)
    jp   CG_TAILOFF

; ============================================================================
; CX_LVALUE -- X must be a modifiable lvalue (C89 6.2.2.1): an object, not an array, a function,
; a struct (assignment of structs is not supported) or a const object
; Errors: E_LVALUE, E_CONST, E_NOTSUP
; Destroys: AF, HL
; ============================================================================
CX_LVALUE:
    ld   a, (X_KIND)
    cp   OK_LVALC
    jr   c, .bad
    cp   OK_FUNC
    jr   z, .bad
    cp   OK_RVAL
    jr   nc, .bad
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_STRUCT
    jp   z, CC_E_NOTSUP
    cp   TC_ARRAY
    jr   nc, .bad
    ld   a, (X_FLAGS)
    or   a
    ret  z
    ld   a, E_CONST
    jp   CC_ERROR
.bad:
    jp   CC_E_LVALUE

; ============================================================================
; CX_LVHOLD -- prepare the lvalue X to be held: a frame object beyond (ix+d)'s reach gets its
; address in HL, and an address in HL gets its offset added (X: OK_LVALC, near OK_LVALF, OK_LVAL
; with offset 0)
; CX_HOLD -- hold X while another operand is parsed: a resident operand stays in HL (CG_PEND; a
; condition is made 0/1 first); then X is pushed on the machine stack (CX_PUSHX)
; Destroys: AF, BC, DE, HL (CX_HOLD: AF, DE, HL; X is under the return address)
; ============================================================================
CX_LVHOLD:
    ld   a, (X_KIND)
    cp   OK_LVALF
    call z, CG_NEAR
    ld   a, (X_KIND)
    cp   OK_LVAL
    ret  nz
    jp   CG_LVADDR
CX_HOLD:
    ld   a, (X_KIND)
    cp   OK_COND
    jr   nz, .res
    push bc
    call CG_LOAD
    pop  bc
.res:
    ld   a, (X_KIND)
    cp   OK_LVAL
    jp   c, CX_PUSHX
    ld   a, 1
    ld   (CG_PEND), a
    jp   CX_PUSHX
; CX_HOLDV -- hold the value X for a binary operator: CX_HOLD, but a resident float (in F_ACC) is
; pushed now, a 3-word slot counted in CX_PEND (Phase 8). Destroys: AF, BC, DE, HL
CX_HOLDV:
    call CX_XFLT
    jr   nz, CX_HOLD
    ld   a, (X_KIND)
    cp   OK_LVAL
    jr   c, CX_HOLD                    ; deferred: a constant or an object
    push bc
    call CG_PUSHX
    pop  bc
    jp   CX_PUSHX

; ============================================================================
; CX_MUTE / CX_UNMUTE -- start and end code that is parsed but not emitted (CX_NOEVAL): the held
; operand state (CG_PEND) is restored when the outermost muted part ends
; Destroys: AF
; CX_MAYBE -- parse with routine HL, muted when A = 0 (an operand that is not evaluated)
; Destroys: what the routine destroys
; ============================================================================
CX_MAYBE:
    or   a
    push af
    call z, CX_MUTE
    call CALL_HL
    pop  af
    ret  nz
CX_UNMUTE:
    ld   a, (CX_NOEVAL)
    dec  a
    ld   (CX_NOEVAL), a
    ret  nz
    ld   a, (CG_PENDSV)
    ld   (CG_PEND), a
    ret
CX_MUTE:
    ld   a, (CX_NOEVAL)
    or   a
    jr   nz, .in
    ld   a, (CG_PEND)
    ld   (CG_PENDSV), a
    xor  a
.in:
    inc  a
    ld   (CX_NOEVAL), a
    ret

; ============================================================================
; CX_COND -- a conditional expression (C89 6.3.15)
; Out: X = the operand. A run-time condition: both operands' code with jumps, the value in HL.
;      A constant condition: only the chosen operand is evaluated
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
    rst  $30                          ; LEX_NEXT
    call CX_TRUTH                      ; C: constant, A = its truth
    jr   c, .const
    ld   hl, 0
    call CG_JFALSE                     ; to the third operand
    push hl
    call .second
    call CG_LOAD
    ld   a, $C3
    ld   hl, 0
    call CG_JP                         ; over the third operand
    ex   (sp), hl
    call CG_HERE                       ; the third operand
    call CX_PUSHX
    ld   a, TK_COLON
    call CC_EXPECT
    call .third
    call CG_LOAD
    call CX_POPY
    pop  hl
    call CG_HERE
    jr   .types
.const:                                ; only the chosen operand is evaluated
    push af
    ld   hl, .second
    call CX_MAYBE
    pop  af
    ld   (X_FLAGS), a                  ; (free in a value: the condition)
    call CX_PUSHX
    ld   a, TK_COLON
    call CC_EXPECT
    ld   a, (X_FLAGS)
    xor  1
    ld   hl, .third
    call CX_MAYBE
    call CX_POPY
    ld   a, (Y_FLAGS)
    or   a
    call nz, CX_SWAP                   ; X = the second operand
    call CG_VAL                        ; (retyped below: a deferred object is loaded first)
.types:                                ; both integers: the usual conversions; an integer (a null
    ld   hl, (Y_TYPE)                  ; pointer constant) with a pointer: the pointer's type; two
    call TY_CLASS                      ; floats: float; a float and another type: E_TYPE (deviation)
    ld   d, a
    ld   hl, (X_TYPE)
    call TY_CLASS
    ld   e, a
    cp   TC_FLOAT
    jr   z, .flt
    ld   a, d
    cp   TC_FLOAT
    jp   z, CC_E_TYPE
    ld   a, e
    dec  a
    cp   TC_UINT
    ret  nc
    ld   a, d
    dec  a
    cp   TC_UINT
    ld   hl, (Y_TYPE)
    jr   nc, .set
    call CX_USUAL
.set:
    ld   (X_TYPE), hl
    ret
.flt:
    cp   d
    ret  z
    jp   CC_E_TYPE
.second:
    call CX_EXPR
    jr   .value
.third:
    call CX_COND
.value:
    call CX_RVAL
    jp   CX_SCALARV

; CX_TRUTH -- C: X is a constant, A = 1 if it is nonzero, else 0. NC: not constant.
; Destroys: AF, HL
CX_TRUTH:
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  nc
    call CX_XFLT
    ld   hl, (X_VAL)
    jr   nz, .int
    ld   l, (hl)                       ; a float constant: its exponent (0: zero)
    ld   h, 0
.int:
    ld   a, h
    or   l
    scf
    ret  z
    ld   a, 1
    ret

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
    rst  $30                          ; LEX_NEXT
    pop  bc
    push bc
    ld   a, b
    cp   TK_ANDAND
    jr   z, .logic
    cp   TK_OROR
    jr   z, .logic
    inc  c
    ld   b, c
    call CX_HOLDV                      ; the left operand (BC kept)
    call CX_BINARY                     ; the right operand: higher precedence (left assoc.)
    call CX_RVAL
    call CX_POPY
    pop  bc
    ld   a, b
    call CX_BINOP
    pop  bc
    jr   .loop
.logic:
    call CX_LOGIC
    pop  bc
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
; CX_LOGIC -- `X && right`, `X || right` (C89 6.3.13-14): the right operand only when X does not
; decide; the value is an int, 0 or 1
; In:  B = the operator, C = its precedence; X = the left operand (a value); current token = the
;      right operand's first
; Errors: E_OPERAND, the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_LOGIC:
    push bc
    call CX_SCALAR_X
    pop  bc
    call CX_TRUTH
    jr   c, .const
    push bc
    ld   hl, 0
    call .jump                         ; X decides: to the value it decides
    pop  bc
    push hl
    push bc
    call .right
    pop  bc
    pop  hl
    push bc
    call .jump                         ; so does the right operand
    pop  bc
    push hl
    ld   hl, TPL_AND01
    ld   a, b
    cp   TK_ANDAND
    jr   z, .tpl
    ld   hl, TPL_OR10
.tpl:
    call CG_SEQ                        ; ld hl,x / jr / L: ld hl,!x
    ld   hl, (CG_PC)
    dec  hl
    dec  hl
    dec  hl
    ex   de, hl
    pop  hl
    call CG_PATCH
    ld   a, OK_RVAL
    jr   .int
.jump:                                 ; && jumps on false, || on true
    ld   a, b
    cp   TK_ANDAND
    jp   z, CG_JFALSE
    jp   CG_JTRUE
.right:                                ; the right operand (B = operator, C = precedence)
    inc  c
    ld   b, c
    call CX_BINARY
    call CX_RVAL
    jp   CX_SCALAR_X
.const:                                ; a constant left operand, truth A: it decides (0 &&,
    ld   e, a                          ; 1 ||) and the right operand is not evaluated, or the
    ld   a, b                          ; value is the right operand's truth
    cp   TK_OROR
    ld   a, e
    jr   nz, .and
    xor  1
.and:                                  ; A = 0: it decides
    push de
    push af
    ld   hl, .right
    call CX_MAYBE
    pop  af
    pop  hl                            ; L = the left operand's truth
    or   a
    jr   z, .value
    call CX_TRUTH
    jr   nc, .test
    ld   l, a
.value:
    ld   h, 0
    ld   (X_VAL), hl
    xor  a                             ; OK_CONST
    jr   .int
.test:
    call CG_TEST
    ld   a, OK_COND
.int:
    ld   (X_KIND), a
CX_SET_INT:                            ; X_TYPE = int
    ld   hl, TY_INT
    ld   (X_TYPE), hl
    ret

; ============================================================================
; CX_BINOP -- apply binary operator A to Y (left) and X (right), both values
; Out: X = the result: its type by C89 6.3.5-6.3.14; folded when both operands are constant, else
;      code (CG_BINOP)
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
    cp   TC_FLOAT
    jp   z, CX_FBINOP
    ld   a, d
    cp   TC_FLOAT
    jp   z, CX_FBINOP
    ld   a, (CX_OP)
    cp   TK_PLUS
    jr   z, .add
    cp   TK_MINUS
    jp   z, .sub
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
    call CX_SWAPCG
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
    ld   a, (X_KIND)
    cp   OK_LVALC
    jr   nc, .scale
    ld   de, (X_VAL)
    ld   b, h
    ld   c, l
    call RT_UMUL
    ld   (X_VAL), hl
    jr   .ptrdo
.scale:                                ; at run time: the integer in HL, multiplied
    push hl
    call CG_LOAD
    pop  de
    call CG_MULK
.ptrdo:
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
    jp   nc, CG_DIVK
    ld   hl, (X_VAL)                   ; (exact: the difference is a multiple of the size)
    ex   de, hl
    call RT_DIVS
    ld   (X_VAL), hl
    ret
.do:                                   ; HL = the operation's type, DE = the result's type
    push de
    ld   de, TY_INT
    or   a
    sbc  hl, de
    ld   c, 0
    jr   z, .signed
    inc  c                             ; unsigned (and pointer) operation
.signed:
    ld   a, (Y_KIND)
    ld   b, a
    ld   a, (X_KIND)
    or   b
    cp   OK_LVALC
    jr   nc, .code
    ld   (X_KIND), a                   ; OK_CONST, or OK_ADDRC if either was one
    ld   a, (CX_OP)
    ld   de, (Y_VAL)
    ld   hl, (X_VAL)
    call CX_FOLD
    ld   (X_VAL), hl
    jr   .type
.code:
    call CG_BINOP
.type:
    pop  de
    ld   (X_TYPE), de
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
; CX_SCALAR_X -- X must be a scalar; CX_SCALARV -- X must be a scalar or void
; Errors: E_OPERAND
; Destroys: AF (CX_SCALAR_X, CX_SCALARV: and HL)
; ============================================================================
CX_SCALARV:
    ld   hl, (X_TYPE)
    call TY_CLASS
    or   a
    ret  z
    jr   CX_SCALAR_A
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
; CX_ARITH_A -- class A must be arithmetic: an integer or float (Phase 8). Destroys: AF
CX_ARITH_A:
    dec  a
    cp   TC_FLOAT
    ret  c
    jp   CC_E_OPERAND
; CX_XFLT -- Z if X is a float; A = X's class. Destroys: AF, HL
CX_XFLT:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_FLOAT
    ret

; ============================================================================
; CX_FBINOP -- CX_BINOP with a float operand (Phase 8; spec.md 4.3, 4.9): + - * / and the comparisons
; of two arithmetic operands, an integer one converted. Two constants: + - * / folded by the float
; core. Else `call F_OP / db op`: a resident float left operand is in its stack slot (CX_HOLDV) and
; the right one goes to F_ACC; any other left operand (deferred, or an integer) is loaded after the
; right one is pushed, and the operation reversed (bit 0 of the operation)
; In:  D, E = the classes of Y (left) and X (right); CX_OP = the operator
; Out: X = a float value, or a comparison: OK_COND, int
; Errors: E_OPERAND, E_RANGE (folding)
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_FBINOP:
    ld   a, d
    call CX_ARITH_A
    ld   a, e
    call CX_ARITH_A
    ld   a, (CX_OP)
    ld   hl, CX_FOPS
    ld   bc, CX_FOPS_N
    cpir
    jp   nz, CC_E_OPERAND
    ld   hl, CX_FOPS + 2 * CX_FOPS_N - 1
    or   a
    sbc  hl, bc
    ld   a, (hl)
    ld   (CX_OP), a                    ; the operation (a comparison: its condition in bits 4-5)
    ld   a, (Y_KIND)
    ld   b, a
    ld   a, (X_KIND)
    or   b
    jr   nz, .code
    bit  3, (hl)
    jr   nz, .code                     ; (comparisons: at run time)
    ld   hl, TY_FLOAT                  ; two constants: folded
    call CX_CAST                       ; (an integer one converted)
    call CX_SWAP
    ld   hl, TY_FLOAT
    call CX_CAST                       ; X = the left, Y = the right constant
    ld   hl, (Y_VAL)
    call F_LD
    ld   hl, (X_VAL)
    ld   a, (CX_OP)
    call CX_FOLD                       ; F_ACC = left op right
    ld   hl, F_ACC
    jp   CX_FCONST
.code:
    ld   a, d
    cp   TC_FLOAT
    jr   nz, .rev
    ld   a, (Y_KIND)
    cp   OK_RVAL
    jr   nz, .rev
    call CX_TOFLT                      ; the left operand in its slot, the right one in F_ACC
    ld   hl, CX_PEND                   ; (the operation pops the slot)
    dec  (hl)
    dec  (hl)
    dec  (hl)
    xor  a
    jr   .op
.rev:
    call CX_TOFLT                      ; the right operand to F_ACC ...
    ld   a, (Y_KIND)
    cp   OK_LVAL
    call nc, CG_YHL                    ; (a resident integer left operand: into HL first)
    ld   hl, F_PUSH
    call CG_CALL                       ; ... and to its slot (HL kept)
    call CX_SWAP
    call CX_TOFLT                      ; the left operand to F_ACC
    ld   a, 1                          ; reversed
.op:
    ld   hl, CX_OP
    xor  (hl)
    ld   (hl), a
    call CG_FOP
    ld   a, (CX_OP)
    bit  3, a
    jr   nz, .cmp
    ld   hl, TY_FLOAT
    ld   (X_TYPE), hl
    jp   CX_SET_RVAL
.cmp:
    rra
    rra
    rra
    rra
    and  3
    call CG_SETCOND
    jp   CX_SET_INT
; the operators, then the operations: FOP_*; a comparison's condition (0 NZ, 1 Z, 2 NC, 3 C) in
; bits 4-5, which the float core ignores; > and <= compare reversed
CX_FOPS:
    DB   TK_PLUS, TK_MINUS, TK_STAR, TK_SLASH, TK_LT, TK_GT, TK_LE, TK_GE, TK_EQ, TK_NE
CX_FOPS_N EQU $ - CX_FOPS
    DB   FOP_ADD, FOP_SUB, FOP_MUL, FOP_DIV, FOP_CMP | $30, FOP_CMPR | $30, FOP_CMPR | $20
    DB   FOP_CMP | $20, FOP_CMP | $10, FOP_CMP
    ASSERT $ - CX_FOPS == 2 * CX_FOPS_N

; ============================================================================
; CX_TOFLT -- X (a value) as a float in F_ACC: loaded; an integer converted (`call F_OP / db FRI`,
; FRU for unsigned)
; CX_FCONST -- X = the float constant whose 5 bytes are at HL: a copy in the compile workspace
; (the local area: reclaimed with its scope)
; Errors: E_NOMEM (CX_FCONST)
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_TOFLT:
    call CG_LOAD
    call CX_XFLT
    ret  z
    cp   TC_UINT
    ld   a, FOP_FRU
    jr   z, .c
    xor  a                             ; FOP_FRI
.c:
    call CG_FOP
    ld   hl, TY_FLOAT
    ld   (X_TYPE), hl
    ret
CX_FCONST:
    push hl
    ld   bc, FLOAT_SIZE
    call WS_LALLOC
    ld   (X_VAL), hl
    ex   de, hl
    pop  hl
    ldir
    ld   hl, TY_FLOAT
    ld   (X_TYPE), hl
    xor  a                             ; OK_CONST
    ld   (X_KIND), a
    ret

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
; Errors: E_OPERAND, E_LVALUE, E_CONST, E_SYNTAX, E_INCOMPLETE, E_NESTING, the operands' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_UNARY:
    call CC_STACKCHK
    ld   a, (TOK_KIND)
    ld   hl, .arith
    cp   TK_MINUS
    jr   z, .pre
    cp   TK_PLUS
    jr   z, .pre
    cp   TK_TILDE
    jr   z, .pre
    cp   TK_NOT
    jr   z, .pre
    ld   hl, .deref
    cp   TK_STAR
    jr   z, .pre
    ld   hl, .addr
    cp   TK_AMP
    jr   z, .pre
    ld   hl, .incdec
    cp   TK_INC
    jr   z, .pre
    cp   TK_DEC
    jr   z, .pre
    cp   TK_SIZEOF
    jp   nz, CX_POSTFIX
    call CX_MUTE                       ; sizeof: the operand is not evaluated
    rst  $30                          ; LEX_NEXT
    cp   TK_LPAREN
    jr   nz, .sz_unary
    rst  $30                          ; LEX_NEXT
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
    call CX_UNMUTE
    call TY_SIZE
    ld   (X_VAL), hl
    ld   hl, TY_UINT                   ; size_t: unsigned int
    ld   (X_TYPE), hl
    xor  a
    ld   (X_KIND), a
    ret
.pre:                                  ; a prefix operator A: its operand first, then HL
    push af
    push hl
    rst  $30                          ; LEX_NEXT
    call CX_UNARY
    pop  hl
    pop  af
    jp   (hl)
.incdec:                               ; ++x --x
    ld   c, 0
    jp   CX_INCDEC
.arith:                                ; - + ~ !
    push af
    call CX_RVAL                       ; HL = X_TYPE
    pop  af
    cp   TK_NOT
    jr   z, .not
    push af
    call TY_CLASS
    cp   TC_FLOAT
    jr   z, .float
    call CX_INT_A
    call CG_VAL                        ; a run-time operand: its value (its own width) first
    ld   hl, (X_TYPE)
    call TY_PROMOTE
    ld   (X_TYPE), hl
    pop  af
    cp   TK_PLUS
    ret  z
    ld   de, 0
    ld   b, TK_MINUS                   ; -x = 0 - x
    ld   hl, MATH_NEGATE16
    cp   b
    jr   z, .fold
    dec  de
    ld   b, TK_CARET                   ; ~x = $FFFF ^ x
    ld   hl, RT_CPL
.fold:                                 ; B = operator, DE = left; HL = the helper at run time
    ld   a, (X_KIND)
    cp   OK_LVALC
    jp   nc, CG_CALL
    ld   hl, (X_VAL)
.cfold:                                ; B = operator, DE = left, HL = right
    ld   a, b
    call CX_FOLD
    ld   (X_VAL), hl
    ret
.not:                                  ; !x = (x == 0), an int
    call CX_SCALAR_X
    call CX_TRUTH
    jr   c, .cnot
    call CG_TEST                       ; at run time: the opposite condition
    xor  1
    call CG_SETCOND
    jr   .int
.cnot:                                 ; a constant (A = its truth)
    xor  1
    ld   l, a
    ld   h, 0
    ld   (X_VAL), hl
    xor  a
    ld   (X_KIND), a                   ; OK_CONST
.int:
    jp   CX_SET_INT
.float:                                ; a float (Phase 8): + nothing, - negated (a constant now), ~ E_OPERAND
    pop  af
    cp   TK_TILDE
    jp   z, CC_E_OPERAND
    cp   TK_PLUS
    ret  z
    ld   a, (X_KIND)
    or   a
    jr   z, .fneg
    call CG_LOAD
    ld   a, FOP_NEG
    jp   CG_FOP
.fneg:
    ld   hl, (X_VAL)
    ld   a, (hl)
    or   a
    ret  z                             ; (0 has no sign)
    inc  hl
    ld   a, (hl)
    xor  $80
    ld   (hl), a
    ret
.deref:
    call CX_RVAL
    jp   CX_DEREF
.addr:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_FUNC
    jp   z, CX_RVAL                    ; &function: the function's pointer
    ld   a, (X_KIND)
    cp   OK_LVALC
    ld   b, OK_ADDRC
    jr   z, .addr_k
    cp   OK_LVALF
    call z, CG_FADDR                   ; a frame object: its address at run time
    ld   a, (X_KIND)
    cp   OK_LVAL
    jp   nz, CC_E_LVALUE
    call CG_LVADDR
    ld   b, OK_RVAL
.addr_k:
    ld   a, b
    ld   (X_KIND), a
    ld   hl, (X_TYPE)
    call TY_PTR
    ld   (X_TYPE), hl
    ret

; ============================================================================
; CX_INCDEC -- ++ / -- on the lvalue X (C89 6.3.2.4, 6.3.3.1): the object plus or minus 1, or a
; pointer's element size, stored back
; In:  A = TK_INC / TK_DEC, C = 1: postfix (the value is the old one), 0: prefix (the new one)
; Out: X = OK_RVAL with the lvalue's type
; Errors: E_LVALUE, E_CONST, E_NOTSUP, E_INCOMPLETE (a pointer to an incomplete type)
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_INCDEC:
    push bc
    push af
    call CX_LVALUE
    call CX_LVHOLD
    ld   a, (X_KIND)
    cp   OK_LVAL
    ld   a, $E5                        ; push hl: the address, for the store
    call z, CG_OP
    call CX_PUSHX
    call CG_LOAD                       ; HL = the value
    call CX_POPY                       ; Y = the lvalue
    ld   hl, (Y_TYPE)
    call TY_CLASS
    cp   TC_FLOAT
    jr   z, .float
    cp   TC_PTR
    ld   de, 1
    jr   nz, .step
    call TY_DEREF
    call TY_SIZE
    ex   de, hl                        ; DE = the element size
.step:
    pop  af
    cp   TK_DEC
    call z, NEG_DE
    push de
    call CG_ADDK
    call CG_STORE
    ld   hl, (Y_TYPE)
    ld   (X_TYPE), hl
    pop  de
    pop  bc
    call CG_TAILON                     ; the value: undo for postfix, extend a byte for prefix
    dec  c
    jr   nz, .pre
    call NEG_DE
    call CG_ADDK0
    jp   CG_TAILOFF
.pre:
    call TY_CLASS
    call CG_EXT0
    jp   CG_TAILOFF
.float:                                ; a float (Phase 8): F_ACC +- 1, stored; postfix: the value before
    pop  af                            ; (FOP_PINC / FOP_PDEC keep it in F_OLD: F_REST)
    pop  bc
    push bc
    ld   b, FOP_INC
    cp   TK_DEC
    jr   nz, .fop
    inc  b                             ; FOP_DEC
.fop:
    ld   a, c
    add  a, a
    add  a, b                          ; postfix: FOP_PINC, FOP_PDEC
    call CG_FOP
    call CG_STORE
    pop  bc
    dec  c
    ret  nz
    ld   hl, F_REST
    jp   CG_CALL

; ============================================================================
; CX_POSTFIX -- a primary expression and its postfix operators [ ] ( ) . -> ++ --
; CX_POSTFIX_LOOP -- the postfix operators after an operand already in X
; Out: X = the operand
; Errors: E_OPERAND, E_MEMBER, E_INCOMPLETE, E_SYNTAX, E_ARGS, the operands' errors
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
    cp   TK_LPAREN
    jr   z, .call
    cp   TK_INC
    jr   z, .post
    cp   TK_DEC
    jr   z, .post
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
    rst  $30                          ; LEX_NEXT
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
    add  hl, de                        ; the member's address, displacement or offset
    ld   (X_VAL), hl
.next:
    rst  $30                          ; LEX_NEXT
    jr   CX_POSTFIX_LOOP
.call:
    call CX_CALL
    jr   CX_POSTFIX_LOOP
.post:
    ld   c, 1
    call CX_INCDEC
    jr   .next
.index:                                ; a[i] = *(a + i)
    call CX_RVAL
    ld   a, (X_FLAGS)                  ; (an element of a const array is const)
    push af
    call CX_HOLD
    rst  $30                          ; LEX_NEXT
    call CX_EXPR
    ld   a, TK_RBRACK
    call CC_EXPECT
    call CX_RVAL
    call CX_POPY
    ld   a, TK_PLUS
    call CX_BINOP
    call CX_DEREF
    pop  af
    ld   (X_FLAGS), a
    jp   CX_POSTFIX_LOOP

; ============================================================================
; CX_CALL -- a function call: X = the called expression; current token `(` (C89 6.3.2.2,
; spec.md 5.2). The arguments are evaluated and pushed right to left: a first pass marks where
; each starts (LEX_MARK), then each is parsed from its mark, last first, and the lexer skips the
; others again to the `)`. With a prototype the number of arguments must match and each is
; checked against its parameter's type. The words pushed at run time and not yet popped, by this
; call and the calls whose arguments contain it, are at most LEAPC_ARGS_MAX (CX_PEND): the stack
; between two frame checks stays within ENTER's margin (include/leapc_layout.inc).
; Out: X = OK_RVAL, the function's return type; current token after `)`
; Errors: E_OPERAND (not a function), E_ARGS, E_TYPE, E_SYNTAX, E_NESTING (also: more than
;      LEAPC_ARGS_MAX argument words pending), the arguments' errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_CALL:
    call CX_RVAL                       ; a function: its pointer
    call TY_DEREF
    jp   nc, CC_E_OPERAND
    call TY_CLASS
    cp   TC_FUNC
    jp   nz, CC_E_OPERAND
    call TY_FIELDS                     ; DE = return type, C = parameters, B = flags
    ld   (CX_FRET), de
    ld   de, TN_PARAMS
    add  hl, de
    bit  TFF_PROTO, b
    jr   nz, .proto
    ld   hl, 0                         ; no prototype: nothing to check
.proto:
    ld   (CX_PARAMP), hl
    ld   a, c
    ld   (CX_ARGT), a                  ; (the parameter count, until counted)
    call CX_HOLD                       ; [callee]
    xor  a
    ld   (CX_ARGN), a
    rst  $30                          ; LEX_NEXT
    cp   TK_RPAREN
    jr   z, .counted
.arg:                                  ; [mark]...[callee]
    call LEX_MARK
    call CC_STACKCHK
    ld   hl, CX_ARGN
    inc  (hl)
    ld   a, (CX_PEND)                  ; the words the enclosing calls have pushed, and this
    add  a, (hl)                       ; call's: their bound is the stack floor's margin
    cp   LEAPC_ARGS_MAX + 1            ; (include/leapc_layout.inc)
    jp   nc, PP_E_NESTING
    call .skip
    jr   z, .arg
.counted:                              ; current token `)`
    ld   hl, CX_ARGN
    ld   a, (CX_PARAMP + 1)
    or   a
    jr   z, .nocheck
    ld   a, (CX_ARGT)
    cp   (hl)
    ld   a, E_ARGS
    jp   nz, CC_ERROR
.nocheck:
    ld   a, (hl)
    ld   (CX_ARGT), a
.eval:                                 ; the arguments, last first
    ld   a, (CX_ARGN)
    or   a
    jr   z, .end
    call LEX_RESTORE
    ld   ix, CX_ARGN
    ld   b, CX_CALLW
    call CELLS_SAVE
    call CX_NEXTV
    ld   ix, CX_ARGN + 2 * CX_CALLW
    ld   b, CX_CALLW
    call CELLS_LOAD
    ld   hl, (CX_PARAMP)
    ld   a, h
    or   a
    jr   z, .default
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   (CX_PARAMP), hl
    ex   de, hl
    push hl
    call CX_CHECK_ASSIGN               ; to the parameter's type (a char parameter is read as a
    pop  hl                            ; byte by the callee) ...
    call CX_CONV                       ; ... and converted between integer and float
    jr   .push
.default:
    call CX_SCALAR_X                   ; no prototype: scalars (char already promoted)
.push:
    call CG_PUSHX                      ; A = the words pushed (a float: 3; CX_PEND counts them)
    ld   hl, CX_ARGT
    dec  a
    add  a, (hl)
    ld   (hl), a                       ; the words to pop afterwards
    dec  hl
    dec  (hl)                          ; CX_ARGN: one argument less
    ASSERT CX_ARGT == CX_ARGN + 1
    jr   .eval
.end:                                  ; after the first argument: the others again, to `)`
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    jr   nz, .close
    rst  $30                          ; LEX_NEXT
.again:
    call .skip
    jr   z, .again
.close:
    ld   a, TK_RPAREN
    call CC_EXPECT
    call CX_POPY                       ; Y = the callee
    ld   a, (CX_ARGT)
    ld   c, a                          ; C = the words to pop afterwards
    ld   hl, CX_PEND                   ; (popped after the call: no longer pending for the code
    ld   a, (hl)                       ; compiled from here on)
    sub  c
    ld   (hl), a
    push bc
    ld   a, (Y_KIND)
    cp   OK_FUNC
    jr   nz, .ptr
    ld   hl, (Y_VAL)                   ; call f
    ld   a, $CD
    call CG_FUNCOP
    jr   .pop
.ptr:                                  ; through a pointer: call RT_CALLHL
    cp   OK_LVAL
    jr   nc, .resident
    call CG_LOADY                      ; a variable: loaded now
    jr   .callhl
.resident:                             ; computed before the arguments: pushed under them
    call CG_UNIT                       ; (no arguments: the push now)
    pop  bc
    inc  c                             ; its slot is popped too
    push bc
    ld   a, c
    dec  a
    add  a, a
    ld   l, a
    ld   h, 0
    ld   a, $21                        ; ld hl,2n / add hl,sp / rst LDI
    call CG_OPW
    ld   a, $39
    call CG_B
    ld   a, $CF
    call CG_OP
.callhl:
    ld   hl, RT_CALLHL
    call CG_CALL
.pop:
    pop  bc
    inc  c
.popw:                                 ; the caller removes the arguments: pop bc each
    dec  c
    jr   z, .result
    ld   a, $C1
    call CG_OP
    jr   .popw
.result:
    ld   hl, (CX_FRET)
    ld   (X_TYPE), hl
    jp   CX_SET_RVAL
.skip:                                 ; past one argument: Z if a `,` follows (consumed)
    ld   b, 0                          ; brackets open
.tok:
    ld   a, (TOK_KIND)
    or   a
    jp   z, CC_E_SYNTAX                ; the end of the source, or a `;`: the list is not closed
    cp   TK_SEMI
    jp   z, CC_E_SYNTAX
    sub  TK_LPAREN                     ; ( ) [ ] = 0 1 2 3
    cp   TK_RBRACK - TK_LPAREN + 1
    jr   nc, .comma
    rra                                ; C: ) or ]
    jr   nc, .open
    ld   a, b
    or   a
    jr   z, .last                      ; the list's `)`
    dec  b
    jr   .step
.open:
    inc  b
    jr   .step
.comma:
    cp   TK_COMMA - TK_LPAREN
    jr   nz, .step
    ld   a, b
    or   a
    jr   nz, .step
    rst  $30                          ; LEX_NEXT
    xor  a                             ; Z: a `,` (consumed)
    ret
.step:
    push bc
    rst  $30                          ; LEX_NEXT
    pop  bc
    jr   .tok
.last:
    or   1                             ; NZ: `)`
    ret

; ============================================================================
; CX_PRIMARY -- a primary expression, or a cast (C89 6.3.1, 6.3.4)
; Out: X = the operand (X_FLAGS 0, or X_FLAGS_CONST for a const object)
; Errors: E_UNDECL, E_SYNTAX, E_OPERAND, E_INCOMPLETE, E_TOOBIG, E_NOMEM
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
CX_PRIMARY:
    xor  a
    ld   (X_FLAGS), a
    ld   a, (TOK_KIND)
    cp   TK_NUM
    jr   z, .number
    cp   TK_FNUM
    jr   z, .fnum
    cp   TK_STR
    jp   z, .string
    cp   TK_IDENT
    jr   z, .ident
    cp   TK_LPAREN
    jp   nz, CC_E_SYNTAX
    rst  $30                          ; LEX_NEXT
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
.fnum:                                 ; a floating constant (Phase 8): TOK_BUF = its value
    ld   hl, TOK_BUF
    call CX_FCONST
    jp   LEX_NEXT
.ident:
    call NM_FROM_TOK
    ld   c, NS_ORD
    call SYM_LOOKUP
    jr   z, .found
    call LIB_BIND                      ; a library function (src/runtime/libbind.asm)
    jr   z, .found
    ld   hl, (TOK_LINE)                ; undeclared: only a call declares it, as int f()
    push hl                            ; (C89 6.3.2.2)
    rst  $30                          ; LEX_NEXT
    pop  hl
    cp   TK_LPAREN
    ld   a, E_UNDECL
    jp   nz, CC_ERROR_AT
    ld   a, TN_FUNC
    ld   bc, TN_NODE_SIZE
    call TY_NEW
    ld   de, TY_INT
    ld   bc, 0
    call TY_SETAB
    push hl
    ld   a, SK_FUNC
    call SYM_NEWG                      ; IX = HL = the file-scope entry
    ld   (ix + S_FLAGS), 1 << SF_EXTERN
    ld   (X_VAL), hl
    pop  hl
    call DCL_SETTYPE
    ld   (X_TYPE), hl
    ld   a, OK_FUNC
    ld   (X_KIND), a
    ret
.found:
    call DCL_GETTYPE
    ld   (X_TYPE), hl
    ld   e, (ix + S_VAL)
    ld   d, (ix + S_VAL + 1)
    ld   (X_VAL), de
    ld   a, (ix + S_KIND)
    cp   SK_ENUMC
    ld   a, OK_CONST
    jr   z, .kind
    ld   a, (ix + S_KIND)
    cp   SK_FUNC
    jr   z, .func
    cp   SK_OBJ
    jp   nz, CC_E_SYNTAX               ; a typedef name
    ld   a, (ix + S_FLAGS)
    and  X_FLAGS_CONST
    ld   (X_FLAGS), a
    bit  SF_PARAM, (ix + S_FLAGS)
    jr   nz, .param
    bit  SF_AUTO, (ix + S_FLAGS)
    jr   nz, .auto
    ld   a, d
    or   e
    jp   z, TY_E_INCOMPLETE            ; static storage not allocated yet (extern, incomplete)
    ld   a, OK_LVALC
    jp   .kind
.param:                                ; IX+4+offset (spec.md 5.2)
    ex   de, hl
    ld   de, 4
    jr   .frame
.auto:                                 ; IX-(offset+size): locals lie below the saved IX
    call TY_SIZE                       ; (HL = the type)
    ld   e, (ix + S_VAL)
    ld   d, 0
    add  hl, de
    call MATH_NEGATE16
    ex   de, hl
    ld   hl, 0
.frame:
    add  hl, de
    ld   (X_VAL), hl
    ld   a, OK_LVALF
    jp   .kind
.func:                                 ; the file-scope entry (a block-scope declaration is an
    ld   de, 0                         ; alias of it)
    ld   hl, (SYM_GLO)
    call SYM_FIND
    ld   (X_VAL), hl
    ld   a, OK_FUNC
    jp   .kind
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
; function a pointer to it; an object at a run-time address is loaded; a deferred object stays
; deferred (its value is loaded when used)
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
    cp   OK_LVAL
    ret  nz
    call CG_LOAD
    ld   hl, (X_TYPE)
    ret
.array:
    call TY_DEREF
    call TY_PTR
    ld   (X_TYPE), hl
    ld   a, (X_KIND)
    cp   OK_LVALC
    ld   a, OK_ADDRC
    jr   z, .set                       ; a static array: a constant address
    ld   a, (X_KIND)
    cp   OK_LVALF
    call z, CG_FADDR
.addr:                                 ; OK_LVAL: its address is the value
    call CG_LVADDR
    ld   a, OK_RVAL
.set:
    ld   (X_KIND), a
    ld   hl, (X_TYPE)
    ret
.func:
    call TY_PTR
    ld   (X_TYPE), hl
    ld   a, (X_KIND)
    cp   OK_FUNC
    ret  z
    jr   .addr

; ============================================================================
; CX_DEREF -- *X: X (a value) must be a pointer; X becomes the object it points to (a constant
; pointer: an object at a constant address; the address of a function: the function; else the
; pointer is loaded: OK_LVAL)
; Errors: E_OPERAND
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_DEREF:
    ld   hl, (X_TYPE)
    call TY_CLASS
    cp   TC_PTR
    jp   nz, CC_E_OPERAND
    ld   a, (X_KIND)
    cp   OK_FUNC
    jr   z, .type
    cp   OK_LVALC
    ld   a, OK_LVALC
    jr   c, .set
    call CG_LOAD
    ld   hl, 0
    ld   (X_VAL), hl
    ld   a, OK_LVAL
.set:
    ld   (X_KIND), a
.type:
    ld   hl, (X_TYPE)
    call TY_DEREF
    ld   (X_TYPE), hl
    xor  a
    ld   (X_FLAGS), a
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
    ld   c, a                          ; C = the source class
    pop  hl
    call TY_CLASS
    or   a
    jr   z, .void
    cp   TC_ARRAY
    jp   nc, CC_E_OPERAND
    ld   b, a                          ; B = the target class
    cp   TC_FLOAT
    jr   z, .tof
    ld   a, c
    cp   TC_FLOAT
    jr   z, .fromf
    call CX_SCALAR_A
    ld   a, (X_KIND)
    cp   OK_FUNC
    jr   z, .type                      ; a function's address stays one (address constants)
    cp   OK_LVALC
    jr   nc, .code
    ld   (X_TYPE), hl
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
.code:                                 ; at run time: the value, extended for a byte type
    push hl
    push bc
    call CG_LOAD
    pop  bc
    pop  hl
    ld   (X_TYPE), hl
    ld   a, b
    cp   c
    ret  z
    jp   CG_EXT
.void:                                 ; (void): the value is not used
    ld   (X_TYPE), hl
    jp   CX_SET_RVAL
.type:
    ld   (X_TYPE), hl
    ret
.tof:                                  ; to float (Phase 8): from an integer or a float
    ld   a, c
    call CX_ARITH_A
    ld   a, (X_KIND)
    or   a
    jp   nz, CX_TOFLT                  ; at run time
    ld   a, c
    cp   TC_FLOAT
    ret  z                             ; a float constant
    ld   hl, (X_VAL)                   ; an integer constant: converted now
    cp   TC_UINT
    ld   a, FOP_FRU
    jr   z, .kf
    xor  a                             ; FOP_FRI
.kf:
    call CX_FOLD
    ld   hl, F_ACC
    jp   CX_FCONST
.fromf:                                ; from float to an integer type (B)
    ld   a, b
    call CX_INT_A
    push hl
    ld   a, (X_KIND)
    or   a
    jr   z, .ki
    push bc
    call CG_LOAD
    ld   a, FOP_TOI                    ; at run time: truncated (the low 16 bits), then as an int
    call CG_FOP                        ; value (a char: extended)
    pop  bc
    pop  hl
    jr   .code
.ki:                                   ; a constant: converted now, then as an int constant
    ld   hl, (X_VAL)
    call F_LD
    ld   a, FOP_TOI
    call CX_FOLD
    ld   (X_VAL), hl
    ld   hl, TY_INT
    ld   (X_TYPE), hl
    pop  hl
    jp   CX_CAST

; ============================================================================
; CX_CHECK_ASSIGN -- can X (a value) be assigned to an object of type HL (spec.md 4.3)?
; Arithmetic types (integers, float) take arithmetic values; pointers take compatible pointers,
; void * either way, or the null pointer constant 0.
; Errors: E_TYPE
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_CHECK_ASSIGN:
    call TY_CLASS
    cp   TC_PTR
    jr   z, .ptr
    dec  a
    cp   TC_FLOAT
    jr   nc, .bad                      ; arrays, structs, void
    ld   hl, (X_TYPE)
    call TY_CLASS
    dec  a
    cp   TC_FLOAT
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
; CX_CONV -- convert the value X for an object of type HL (assignment, argument, initialiser): a
; constant now (CX_CAST), an integer to or from float (code; Phase 8); else nothing
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_CONV:
    ld   a, (X_KIND)
    cp   OK_LVALC
    jp   c, CX_CAST
    call TY_CLASS
    cp   TC_FLOAT
    jp   z, CX_CAST
    push hl
    call CX_XFLT
    pop  hl
    jp   z, CX_CAST
    ret

; ============================================================================
; CX_PUSHX -- push X (6 bytes, under the return address); CX_POPY -- pop such a copy into Y
; CX_SWAP -- exchange X and Y
; Destroys: CX_PUSHX: DE, HL (AF, BC kept). CX_POPY: DE, HL (AF, BC kept). CX_SWAP: AF, BC, DE, HL
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
