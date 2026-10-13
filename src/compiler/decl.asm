; ============================================================================
; src/compiler/decl.asm -- declarations (spec.md 4.2, 4.6, 4.7; M1.2)
;
; The compile entry, parser support, declaration specifiers, declarators, parameter lists, struct
; and enum specifiers, declarations at file and block scope, and function bodies (M1.2: blocks of
; declarations; the statements arrive in M1.3 and Phase 2).
;
; Parser convention: TOK_KIND is the current (look-ahead) token. A routine is entered with its first
; token current and returns with the first token after it current.
;
; Declarators are parsed inside out by re-scanning: for `( inner ) suffixes`, the inner part is
; skipped, the suffixes are applied to the type, then the lexer is rewound to the inner part
; (LEX_MARK / LEX_RESTORE), which is parsed with that type, and the suffixes are skipped. Every
; token is parsed once; only the skipped ones are lexed twice.
; ============================================================================

CC_STACK_FLOOR  EQU LEAPC_STACK_LIMIT + 192    ; the guard leaves room for the ISR and CC_ERROR

; ============================================================================
; CC_COMPILE -- compile the program in the line store (M1.2: its declarations)
; In:  line store (PROG_AREA_START..PROG_END); chunk 6 paged out (the image regions are RAM)
; Out: NC: compiled. C: error, CC_ERRNUM / CC_ERRLINE. Either way the workspace (symbols, types)
;      and the static data stay in RAM until the next compile.
; Destroys: AF, BC, DE, HL (IX kept)
; ============================================================================
CC_COMPILE:
    push ix
    call .guarded
    pop  ix
    ret
.guarded:
    ld   hl, CC_CELLS_BEGIN            ; (CC_CELLS_END..CC_ERRNUM: CC_SP, CC_ERRNUM)
    ld   bc, CC_ERRNUM + 1 - CC_CELLS_BEGIN
    call MEM_FILL_ZERO
    ld   (CC_SP), sp
    ld   hl, IMG_TABLE                 ; the image regions, then WS_GLO
    ld   de, IMG_LIM
    ld   bc, IMG_REGIONS * 4 + 2
    ldir
    ld   hl, (PROG_END)
    ld   (WS_LOC), hl
    call LEX_INIT
    call LEX_NEXT
.decl:
    or   a                             ; TK_EOF (NC)
    ret  z
    call DECLARATION
    ld   a, (TOK_KIND)
    jr   .decl

; image regions in allocation order (spec.md 3.2): [low:2][high:2]
IMG_TABLE:
    DW   LEAPC_IMG1_BASE, LEAPC_IMG1_END
    DW   LEAPC_IMG2_BASE, LEAPC_IMG2_END
    DW   LEAPC_IMG3_BASE, LEAPC_IMG3_END
    DW   LEAPC_IMG4_BASE, LEAPC_IMG4_END
    DW   LEAPC_SRC_TOP                 ; WS_GLO
    ASSERT WS_GLO == IMG_LIM + IMG_REGIONS * 4

; ============================================================================
; CC_EXPECT -- the current token must be A; step past it
; In:  A = token kind. Out: A = the next token's kind
; Errors: E_SYNTAX
; Destroys: AF, BC, DE, HL
; ============================================================================
CC_EXPECT:
    ld   hl, TOK_KIND
    cp   (hl)
    jp   z, LEX_NEXT
    jp   CC_E_SYNTAX

; ============================================================================
; CC_STACKCHK -- compiler stack guard for the recursive parsers (spec.md 4.10)
; Errors: E_NESTING when SP is below CC_STACK_FLOOR
; Destroys: F (A, BC, DE, HL kept)
; ============================================================================
CC_STACKCHK:
    push hl
    ld   hl, -CC_STACK_FLOOR
    add  hl, sp
    pop  hl
    ret  c
    ld   a, E_NESTING
    jp   CC_ERROR

; ============================================================================
; NEXT_HL -- LEX_NEXT keeping HL
; Out: A = the next token's kind. Destroys: F, BC, DE
; ============================================================================
NEXT_HL:
    push hl
    call LEX_NEXT
    pop  hl
    ret

; ============================================================================
; CELLS_SAVE -- push B words of cells from IX up (left on the stack under the return address)
; CELLS_LOAD -- pop B such words back into the cells below IX (IX = the end of the cells)
; Destroys: F, B, IX (A, C, DE, HL kept)
; ============================================================================
CELLS_SAVE:
    ex   (sp), hl
    ld   (CELLS_RET), hl
    pop  hl
.word:
    push hl
    ld   l, (ix + 0)
    ld   h, (ix + 1)
    ex   (sp), hl
    inc  ix
    inc  ix
    djnz .word
CELLS_RETURN:
    push hl
    ld   hl, (CELLS_RET)
    ex   (sp), hl
    ret
CELLS_LOAD:
    ex   (sp), hl
    ld   (CELLS_RET), hl
    pop  hl
.word:
    dec  ix
    dec  ix
    ex   (sp), hl
    ld   (ix + 0), l
    ld   (ix + 1), h
    pop  hl
    djnz .word
    jr   CELLS_RETURN

; ============================================================================
; LEX_MARK -- remember the current token (6 bytes pushed under the return address)
; LEX_RESTORE -- pop such a mark: the next LEX_NEXT scans the marked token again
; In:  LEX_RESTORE: the mark directly under its return address
; Destroys: LEX_MARK: BC, DE. LEX_RESTORE: AF, BC, DE (both keep HL)
; ============================================================================
LEX_MARK:
    pop  de
    ld   bc, (TOK_PTR)
    push bc
    ld   bc, (TOK_LINE)
    push bc
    ld   bc, (TOK_FLAGS - 1)           ; B = TOK_FLAGS
    push bc
    push de
    ret
LEX_RESTORE:
    pop  de
    pop  bc
    ld   a, b
    and  1 << TF_BOL
    ld   (LEX_BOLP), a
    pop  bc
    ld   (LEX_LINE), bc
    pop  bc
    ld   (LEX_PTR), bc
    push de
    ret

; ============================================================================
; SKIP_GROUP -- skip tokens up to and including the bracket that closes the group
; In:  B = brackets open before the current token (0: the current token opens the group)
; Out: current token = the token after the closing ) or ]
; Errors: E_SYNTAX at the end of the source
; Destroys: AF, BC, DE, HL
; SKIP_SUFFIXES -- skip a run of ( ... ) and [ ... ] groups
; ============================================================================
SKIP_GROUP:
    ld   a, (TOK_KIND)
    or   a
    jp   z, CC_E_SYNTAX
    sub  TK_LPAREN
    cp   TK_RBRACK - TK_LPAREN + 1
    jr   nc, .next
    rra                                ; C: ) or ]
    jr   c, .close
    inc  b
    jr   .next
.close:
    dec  b
    jp   z, LEX_NEXT
.next:
    push bc
    call LEX_NEXT
    pop  bc
    jr   SKIP_GROUP
SKIP_SUFFIXES:
    ld   a, (TOK_KIND)
    cp   TK_LPAREN
    jr   z, .skip
    cp   TK_LBRACK
    ret  nz
.skip:
    ld   b, 0
    call SKIP_GROUP
    jr   SKIP_SUFFIXES

; ============================================================================
; IS_DECL_START -- does the current token start declaration specifiers?
; Out: NZ: yes (a specifier or qualifier keyword, or a typedef name in scope). Z: no
; Destroys: AF, BC, DE, HL, IX; NM (for an identifier)
; ============================================================================
IS_DECL_START:
    ld   a, (TOK_KIND)
    cp   TK_IDENT
    jr   nz, DS_CODE
    call NM_FROM_TOK
    ld   c, NS_ORD
    call SYM_LOOKUP
    jr   nz, .no
    ld   a, (ix + S_KIND)
    cp   SK_TYPEDEF
    jr   nz, .no
    or   a
    ret
.no:
    xor  a
    ret

; ============================================================================
; DS_CODE -- the specifier code of a token (DS_TABLE)
; In:  A = token kind. Out: A = code (0: not a specifier keyword), Z/NZ accordingly
; Destroys: AF, DE, HL
; ============================================================================
DS_CODE:
    sub  TK_KW_FIRST
    jr   c, .no
    ld   e, a
    ld   d, 0
    ld   hl, DS_TABLE
    add  hl, de
    ld   a, (hl)
    or   a
    ret
.no:
    xor  a
    ret

; specifier codes: 1-5 storage class (SC_*), DSC_CONST, DSC_NOTSUP, DSC_STRUCT, DSC_ENUM, or
; $80 + the DS_MASK bit of a type specifier
DSC_CONST       EQU $40
DSC_NOTSUP      EQU $41
DSC_STRUCT      EQU $42
DSC_ENUM        EQU $43
DSM_VOID        EQU $01
DSM_CHAR        EQU $02
DSM_SHORT       EQU $04
DSM_INT         EQU $08
DSM_SIGNED      EQU $10
DSM_UNSIGNED    EQU $20
DSM_OTHER       EQU $40             ; struct, enum or typedef name
DS_TABLE:
    DB   SC_AUTO, 0, 0, $80 + DSM_CHAR                  ; auto break case char
    DB   DSC_CONST, 0, 0, 0                             ; const continue default do
    DB   DSC_NOTSUP, 0, DSC_ENUM, SC_EXTERN             ; double else enum extern
    DB   DSC_NOTSUP, 0, 0, 0                            ; float for goto if
    DB   $80 + DSM_INT, DSC_NOTSUP, SC_REGISTER, 0      ; int long register return
    DB   $80 + DSM_SHORT, $80 + DSM_SIGNED, 0, SC_STATIC ; short signed sizeof static
    DB   DSC_STRUCT, 0, SC_TYPEDEF, DSC_NOTSUP          ; struct switch typedef union
    DB   $80 + DSM_UNSIGNED, $80 + DSM_VOID, DSC_NOTSUP, 0 ; unsigned void volatile while
    ASSERT $ - DS_TABLE == TK_KW_COUNT

; ============================================================================
; DECL_SPECS -- declaration specifiers (spec.md 4.2)
; In:  current token = the first specifier, or anything else (C89 implicit int)
; Out: HL = base type; C = storage class (SC_*), B = nonzero if `const` was given; current token = the
;      first token after the specifiers
; Errors: E_TYPESPEC, E_STORAGE (two storage classes), E_NOTSUP (long, float, double, union,
;      volatile), and those of STRUCT_SPEC / ENUM_SPEC
; Destroys: AF, DE, IX; NM
; ============================================================================
DECL_SPECS:
    xor  a
    ld   (DS_SC), a
    ld   (DS_CONST), a
    ld   (DS_MASK), a
    ld   hl, TY_INT
    push hl                            ; the type of a struct, enum or typedef name
.loop:
    ld   a, (TOK_KIND)
    cp   TK_IDENT
    jr   z, .ident
    call DS_CODE
    jr   z, .done
    jp   m, .type
    cp   DSC_CONST
    jr   c, .storage
    jr   z, .const
    cp   DSC_STRUCT
    jp   c, CC_E_NOTSUP
    ld   hl, STRUCT_SPEC
    jr   z, .agg
    ld   hl, ENUM_SPEC
.agg:
    ld   ix, DS_SC                     ; struct or enum: the specifier parsers nest DECL_SPECS
    ld   b, 2
    call CELLS_SAVE
    call CALL_HL                       ; HL = struct node / int
    ld   ix, DS_SC + 4
    ld   b, 2
    call CELLS_LOAD
    ex   (sp), hl
    ld   a, DSM_OTHER
    call .bit
    jr   .loop
.ident:                                ; a typedef name, if no type specifier came before
    ld   a, (DS_MASK)
    or   a
    jr   nz, .done
    call IS_DECL_START
    jr   z, .done
    ld   l, (ix + S_TYPE)
    ld   h, (ix + S_TYPE + 1)
    ex   (sp), hl
    ld   a, DSM_OTHER
    jr   .typebit
.storage:
    ld   hl, DS_SC
    inc  (hl)
    dec  (hl)
    jp   nz, CC_E_STORAGE
    ld   (hl), a
    jr   .next
.const:
    ld   (DS_CONST), a                 ; (DSC_CONST: nonzero)
    jr   .next
.type:
    and  $7F
.typebit:
    call .bit
.next:
    call LEX_NEXT
    jr   .loop
.bit:                                  ; add type specifier bit A (twice: E_TYPESPEC)
    ld   hl, DS_MASK
    ld   c, a
    and  (hl)
    jp   nz, CC_E_TYPESPEC
    ld   a, c
    or   (hl)
    ld   (hl), a
    ret
.done:                                 ; the combination (C89 6.5.2)
    pop  hl
    ld   a, (DS_MASK)
    cp   DSM_OTHER
    jr   z, .ret                       ; struct, enum or typedef name alone
    ld   c, a
    and  DSM_OTHER | DSM_VOID
    jr   z, .arith
    ld   a, c
    cp   DSM_VOID
    jp   nz, CC_E_TYPESPEC             ; void, struct, enum or typedef name with others
    ld   hl, TB_VOID
    jr   .ret
.arith:
    ld   a, c
    and  DSM_SIGNED | DSM_UNSIGNED
    cp   DSM_SIGNED | DSM_UNSIGNED
    jp   z, CC_E_TYPESPEC
    ld   hl, TB_INT
    bit  1, c                          ; DSM_CHAR
    jr   z, .int
    ld   a, c
    and  DSM_SHORT | DSM_INT
    jp   nz, CC_E_TYPESPEC
    ld   l, TB_CHAR
    bit  4, c                          ; DSM_SIGNED
    jr   z, .ret
    inc  l                             ; TB_SCHAR
    jr   .ret
.int:
    bit  5, c                          ; DSM_UNSIGNED
    jr   z, .ret
    inc  l                             ; TB_UINT
.ret:
    ld   bc, (DS_SC)                   ; C = storage class, B = const
    ret

; ============================================================================
; STRUCT_SPEC -- a struct specifier (current token = `struct`)
; Out: HL = the struct node; current token after the specifier
; Errors: E_REDECL (the tag names an enum), E_REDEF (second body), member errors
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
STRUCT_SPEC:
    call LEX_NEXT
    cp   TK_IDENT
    jr   nz, .anon
    call NM_FROM_TOK
    call LEX_NEXT
    ld   c, NS_TAG
    cp   TK_LBRACE
    jr   z, .here
    cp   TK_SEMI
    jr   z, .here
    call SYM_LOOKUP                    ; a reference: the tag in any scope
    jr   z, .found
.new:                                  ; a new (incomplete) struct, its tag in the current scope
    call ST_NODE
    push hl
    ld   a, SK_TAG
    call SYM_NEW
    pop  hl
    call DCL_SETTYPE
    jr   .body
.here:                                 ; a definition or `struct s;`: the current scope only
    call SYM_FIND_CUR
    jr   nz, .new
.found:
    bit  SF_ENUM, (ix + S_FLAGS)
    jp   nz, CC_E_REDECL
    ld   l, (ix + S_TYPE)
    ld   h, (ix + S_TYPE + 1)
.body:
    ld   a, (TOK_KIND)
    cp   TK_LBRACE
    ret  nz
    call TY_FIELDS
    ld   a, b
    or   c
    jp   nz, CC_E_REDEF
    jr   MEMBERS
.anon:
    cp   TK_LBRACE
    jp   nz, CC_E_SYNTAX
    call ST_NODE
    ; fall through: the body
; ============================================================================
; MEMBERS -- a struct body `{ member declarations }` (C89 6.5.2.1; no padding: spec.md 4.2)
; In:  HL = the struct node (incomplete); current token = `{`
; Out: HL = the node, completed (size, first member); current token after `}`
; Errors: E_STORAGE, E_NOTSUP (bit-fields), E_INCOMPLETE (incomplete or function member),
;      E_REDECL (duplicate member), E_TOOLARGE, E_SYNTAX (no members)
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
MEMBERS:
    push hl                            ; the node
    ld   ix, ST_HEAD                   ; members of an enclosing struct definition
    ld   b, 3
    call CELLS_SAVE
    ld   hl, 0
    ld   (ST_HEAD), hl
    ld   (ST_SIZE), hl
    ld   hl, ST_HEAD                   ; the tail's link field: ST_HEAD itself at first
    ld   (ST_TAIL), hl
    call LEX_NEXT
.decl:
    cp   TK_RBRACE
    jr   z, .end
    call DECL_SPECS
    ld   a, c
    or   a
    jp   nz, CC_E_STORAGE
    push hl                            ; base type
.member:
    pop  hl
    push hl
    call DECLARATOR
    call NEED_NAME
    ld   a, (TOK_KIND)
    cp   TK_COLON
    jp   z, CC_E_NOTSUP                ; bit-field
    push hl                            ; member type
    call TY_SIZE
    ex   (sp), hl
    push hl
    ld   c, NS_MEMBER
    ld   de, 0
    ld   hl, (ST_HEAD)
    call SYM_FIND
    jp   z, CC_E_REDECL
    ld   a, SK_MEMBER
    call SYM_MAKE_G                    ; IX = the member entry
    pop  hl
    call DCL_SETTYPE
    ld   hl, (ST_SIZE)
    ld   (ix + S_VAL), l
    ld   (ix + S_VAL + 1), h
    pop  de
    add  hl, de
    jp   c, TY_E_TOOLARGE
    ld   (ST_SIZE), hl
    push ix                            ; append
    pop  de
    ld   hl, (ST_TAIL)
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ld   (ST_TAIL), de
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    jr   nz, .semi
    call LEX_NEXT
    jr   .member
.semi:
    pop  hl
    ld   a, TK_SEMI
    call CC_EXPECT
    jr   .decl
.end:
    ld   hl, (ST_HEAD)
    ld   a, h
    or   l
    jp   z, CC_E_SYNTAX                ; a struct needs a member
    ld   de, (ST_SIZE)
    ld   ix, ST_HEAD + 6
    ld   b, 3
    call CELLS_LOAD
    ld   b, h
    ld   c, l
    pop  hl
    call TY_SETAB                      ; complete: size, first member
    jp   NEXT_HL

; ST_NODE -- HL = a new incomplete struct node. Destroys: AF, BC, DE
ST_NODE:
    ld   a, TN_STRUCT
    ld   bc, TN_NODE_SIZE
    jp   TY_NEW

; ============================================================================
; ENUM_SPEC -- an enum specifier (current token = `enum`; spec.md 4.2: the type is int)
; Out: HL = int; current token after the specifier
; Errors: E_REDECL (the tag names a struct; an enumerator name in use), E_REDEF (second body),
;      E_INCOMPLETE (enum tag without a definition), E_CONSTEXPR
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
ENUM_SPEC:
    call LEX_NEXT
    cp   TK_IDENT
    jr   nz, .body
    call NM_FROM_TOK
    call LEX_NEXT
    ld   c, NS_TAG
    cp   TK_LBRACE
    jr   z, .def
    call SYM_LOOKUP                    ; a reference: must name an enum
    jp   nz, TY_E_INCOMPLETE
    bit  SF_ENUM, (ix + S_FLAGS)
    jp   z, CC_E_REDECL
.int:
    ld   hl, TY_INT
    ret
.def:
    call SYM_FIND_CUR
    jr   nz, .tag
    bit  SF_ENUM, (ix + S_FLAGS)
    jp   z, CC_E_REDECL
    jp   CC_E_REDEF
.tag:
    ld   a, SK_TAG
    call SYM_NEW
    ld   (ix + S_FLAGS), 1 << SF_ENUM | 1 << SF_DEFINED
    ld   (ix + S_TYPE), TY_INT
    ld   a, (TOK_KIND)
.body:
    cp   TK_LBRACE
    jp   nz, CC_E_SYNTAX
    ld   hl, -1                        ; the previous value
.item:                                 ; current token `{` or `,`
    call NEXT_HL
    inc  hl                            ; the default value
    cp   TK_RBRACE
    jr   z, .close
    cp   TK_IDENT
    jp   nz, CC_E_SYNTAX
    push hl
    ld   hl, (TOK_PTR)                 ; the name, kept over its value expression
    push hl
    ld   a, (TOK_LEN)
    push af
    call LEX_NEXT
    cp   TK_ASSIGN
    jr   nz, .named
    call LEX_NEXT
    call CX_CONST_INT                  ; HL = value
    pop  af
    pop  de
    pop  bc
    push hl
    jr   .declare
.named:
    pop  af
    pop  de
.declare:                              ; the value is on the stack
    ld   (NM_PTR), de
    ld   (NM_LEN), a
    ld   a, SK_ENUMC
    call DCL_NEWCUR
    ld   (ix + S_TYPE), TY_INT
    pop  hl
    ld   (ix + S_VAL), l
    ld   (ix + S_VAL + 1), h
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    jr   z, .item
.close:
    ld   a, TK_RBRACE
    call CC_EXPECT
    jr   .int

; ============================================================================
; DECLARATOR -- a declarator, named or abstract (C89 6.5.4)
; In:  HL = the specifiers' type; current token = the first token of the declarator
; Out: HL = the declared type; NM_PTR / NM_LEN = the name (NM_LEN 0: abstract); current token =
;      the first token after the declarator
; Errors: E_SYNTAX, E_NESTING, E_NOTSUP (volatile), the errors of SUFFIXES
; Destroys: AF, BC, DE, IX
; ============================================================================
DECLARATOR:
    call CC_STACKCHK
.ptr:
    ld   a, (TOK_KIND)
    cp   TK_STAR
    jr   nz, .direct
    call TY_PTR
.qual:
    push hl
    call LEX_NEXT
    pop  hl
    cp   TK_CONST                      ; `* const`: accepted (spec.md 4.2: const is enforced
    jr   z, .qual                      ; for objects declared const only)
    cp   TK_VOLATILE
    jp   z, CC_E_NOTSUP
    jr   .ptr
.direct:
    cp   TK_LPAREN
    jr   nz, .name
    push hl
    call LEX_NEXT                      ; the token after `(`
    call DCL_NESTED
    pop  hl
    jr   nz, .fsuffix
    call LEX_MARK                      ; `( declarator ) suffixes`
    push hl
    ld   b, 1
    call SKIP_GROUP
    pop  hl
    call SUFFIXES                      ; the type with the outer suffixes
    call LEX_RESTORE
    push hl
    call LEX_NEXT
    pop  hl
    call DECLARATOR                    ; the inner declarator, with that type
    push hl
    ld   a, TK_RPAREN
    call CC_EXPECT
    call SKIP_SUFFIXES                 ; (parsed already)
    pop  hl
    ret
.fsuffix:                              ; an abstract `( parameters )`: `(` consumed
    call SUFFIX_FUNC
    xor  a
    ld   (NM_LEN), a
    ret
.name:
    ld   de, 0
    cp   TK_IDENT
    jr   nz, .anon
    ld   de, (TOK_PTR)                 ; the name, kept over the suffixes
    ld   a, (TOK_LEN)
    push de
    push af
    call NEXT_HL
    jr   .suffixes
.anon:
    xor  a
    push de
    push af
.suffixes:
    call SUFFIXES
    pop  af
    pop  de
    ld   (NM_PTR), de
    ld   (NM_LEN), a
    ret

; DCL_NESTED -- after `(` in a declarator: Z if a nested declarator starts (`*`, `(`, or an
; identifier that is not a typedef name), NZ if a parameter list does. Destroys: AF, BC, DE, HL, IX
DCL_NESTED:
    cp   TK_STAR
    ret  z
    cp   TK_LPAREN
    ret  z
    cp   TK_IDENT
    ret  nz
    jp   IS_DECL_START

; ============================================================================
; SUFFIXES -- the array and function suffixes of a direct declarator, applied right to left
; SUFFIX_FUNC -- the same after a consumed `(` (a parameter list comes first)
; In:  HL = type; current token = the first possible suffix
; Out: HL = the derived type; current token after the suffixes
; Errors: E_ARRAYSIZE, E_BADDECL (array of functions, function returning an array or a function),
;      E_NOTSUP (function returning a struct), E_INCOMPLETE, E_TOOLARGE, E_CONSTEXPR
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
SUFFIXES:
    call CC_STACKCHK
    ld   a, (TOK_KIND)
    cp   TK_LBRACK
    jr   z, SUFFIX_ARRAY
    cp   TK_LPAREN
    ret  nz
    push hl
    call LEX_NEXT
    pop  hl
SUFFIX_FUNC:
    push hl
    call PARAMS                        ; HL = the function node
    ex   (sp), hl
    call SUFFIXES                      ; HL = the return type
    call TY_CLASS
    cp   TC_ARRAY
    jp   z, CC_E_BADDECL
    cp   TC_FUNC
    jp   z, CC_E_BADDECL
    cp   TC_STRUCT
    jp   z, CC_E_NOTSUP                ; struct return values (spec.md 4.6)
    ex   de, hl
    pop  hl
    push hl
    inc  hl
    inc  hl
    inc  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    pop  hl
    ret
SUFFIX_ARRAY:
    push hl
    call LEX_NEXT
    ld   hl, 0
    cp   TK_RBRACK
    jr   z, .count                     ; `[]`
    call CX_CONST_INT                  ; HL = the size: 1-32767, or up to 65535 if unsigned
    ld   a, h
    or   l
    jp   z, CC_E_ARRAYSIZE
    bit  7, h
    jr   z, .count
    ld   a, (X_TYPE)
    cp   TB_UINT
    jp   nz, CC_E_ARRAYSIZE            ; negative
.count:
    push hl
    ld   a, TK_RBRACK
    call CC_EXPECT
    pop  bc
    pop  hl
    push bc
    call SUFFIXES                      ; HL = the element type
    pop  bc
    call TY_CLASS
    cp   TC_FUNC
    jp   z, CC_E_BADDECL
    jp   TY_ARRAY

; ============================================================================
; PARAMS -- a parameter list, up to and including `)` (C89 6.5.4.3; spec.md 4.6)
; In:  current token = the first token after `(`
; Out: HL = a new function node (return type 0: the caller sets it); LASTP_NODE = HL;
;      LASTP_HEAD / LASTP_END = its parameter entries, reclaimed but intact for FUNC_DEF. The
;      node lists the parameter types last parameter first.
; Errors: E_NOTSUP (`...`, K&R identifier lists), E_STORAGE, E_BADDECL (void misused),
;      E_REDECL (two parameters with one name), E_PARAMS (more than 16)
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
PARAMS:
    call SCOPE_OPEN                    ; the prototype scope
    ld   bc, 0                         ; B = flags, C = parameter count
    ld   a, (TOK_KIND)
    cp   TK_RPAREN
    jr   z, .end                       ; `()`: no prototype
    inc  b                             ; TFF_PROTO
.param:
    push bc
    call IS_DECL_START
    jr   nz, .specs
    ld   a, (TOK_KIND)
    cp   TK_IDENT
    jp   z, CC_E_NOTSUP                ; K&R identifier list
    cp   TK_ELLIPSIS
    jp   z, CC_E_NOTSUP                ; user variadic functions (spec.md 4.6)
    jp   CC_E_SYNTAX
.specs:
    call DECL_SPECS
    ld   a, c
    or   a
    jr   z, .sc_ok
    cp   SC_REGISTER
    jp   nz, CC_E_STORAGE
.sc_ok:
    call DECLARATOR
    call TY_CLASS                      ; array -> pointer, function -> pointer (C89 6.7.1)
    cp   TC_ARRAY
    jr   nz, .notarray
    call TY_DEREF
    ld   a, TC_FUNC
.notarray:
    cp   TC_FUNC
    call z, TY_PTR
    ld   a, h
    or   l
    jr   nz, .notvoid
    pop  bc                            ; void: only `(void)`
    ld   a, (NM_LEN)
    or   c
    jp   nz, CC_E_BADDECL
    ld   a, (TOK_KIND)
    cp   TK_RPAREN
    jp   nz, CC_E_BADDECL
    jr   .end
.notvoid:
    ld   b, 0                          ; (not const)
    ld   a, SK_OBJ
    call DCL_LOCAL
    ld   (ix + S_FLAGS), 1 << SF_PARAM
    pop  bc
    ld   a, c
    add  a, a
    ld   (ix + S_VAL), a               ; argument offset: 2 per parameter
    inc  c
    ld   a, c
    cp   16 + 1
    jp   nc, CC_E_PARAMS
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    jr   nz, .end
    push bc
    call LEX_NEXT
    pop  bc
    jr   .param
.end:
    push bc
    ld   a, TK_RPAREN
    call CC_EXPECT
    pop  bc
    push bc
    ld   a, c
    add  a, a
    add  a, TN_NODE_SIZE
    ld   c, a
    ld   b, 0
    ld   a, TN_FUNC
    call TY_NEW
    pop  bc
    ld   (LASTP_NODE), hl
    push hl
    ld   de, TN_B
    add  hl, de
    ld   (hl), c                       ; parameter count
    inc  hl
    ld   (hl), b                       ; flags
    inc  hl
    ex   de, hl                        ; DE -> the parameter types: last parameter first,
    ld   hl, (SYM_LOC)                 ; the order of the chain
    ld   a, c
.fill:
    or   a
    jr   z, .done
    push hl
    ld   bc, S_TYPE
    add  hl, bc
    ldi
    ldi
    pop  hl
    ld   c, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, c
    dec  a
    jr   .fill
.done:
    ld   hl, (SYM_LOC)
    ld   (LASTP_HEAD), hl
    ld   hl, (WS_LOC)
    ld   (LASTP_END), hl
    pop  hl
    call SCOPE_CLOSE
    ret

; ============================================================================
; TYPE_NAME -- a type name (casts, sizeof): specifiers and an abstract declarator
; Out: HL = the type; current token after it
; Errors: E_STORAGE, E_SYNTAX (a name), the errors of DECL_SPECS and DECLARATOR
; Destroys: AF, BC, DE, IX; NM
; ============================================================================
TYPE_NAME:
    call DECL_SPECS
    ld   a, c
    or   a
    jp   nz, CC_E_STORAGE
    call DECLARATOR
    ld   a, (NM_LEN)
    or   a
    ret  z
    jp   CC_E_SYNTAX

; ============================================================================
; DECLARATION -- a declaration, or at file scope a function definition
; In:  current token = its first token
; Out: current token after the `;` (or after the function body)
; Errors: those of the parts
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
DECLARATION:
    ld   hl, 0
    ld   (LASTP_NODE), hl
    call DECL_SPECS                    ; HL = base type, C = storage class, B = const
    ld   a, (TOK_KIND)
    cp   TK_SEMI
    jp   z, LEX_NEXT                   ; `struct s { ... };`, `enum { ... };`
    ld   e, 1                          ; first declarator
.next:
    push hl
    push bc
    push de
    call DECLARATOR
    pop  de
    pop  bc
    dec  e
    jr   nz, .declare                  ; a definition only for the first declarator ...
    ld   a, (TOK_KIND)
    cp   TK_LBRACE
    jr   nz, .declare
    call IS_BLOCK                      ; ... at file scope ...
    jr   nz, .declare
    call TY_CLASS
    cp   TC_FUNC                       ; ... of a function
    jr   nz, .declare
    pop  de
    jp   FUNC_DEF
.declare:
    push bc
    call DECLARE
    pop  bc
    pop  hl
    ld   a, (TOK_KIND)
    cp   TK_COMMA
    ld   a, TK_SEMI
    jp   nz, CC_EXPECT
    push hl
    push bc
    call LEX_NEXT
    pop  bc
    pop  hl
    ld   e, 0
    jr   .next

; ============================================================================
; DECLARE -- declare NM with type HL (and parse the initialiser that may follow)
; In:  HL = type, C = storage class, B = const flag; NM; current token after the declarator
; Out: IX = the entry (functions: the file-scope entry); current token after the initialiser
; Errors: E_SYNTAX (no name), E_STORAGE, E_REDECL, E_TYPE, E_REDEF, E_INCOMPLETE, E_FRAME,
;      E_INIT, E_NOTSUP (initialised automatic objects), and the initialiser's errors
; Destroys: AF, BC, DE, HL, IX; NM
; ============================================================================
DECLARE:
    call NEED_NAME
    ld   a, c
    cp   SC_TYPEDEF
    jr   z, .typedef
    call TY_CLASS
    cp   TC_FUNC
    jr   z, .func
    call IS_BLOCK
    jr   z, .file
    ld   a, c
    cp   SC_EXTERN
    jr   z, .extern
    cp   SC_STATIC
    jr   z, .static
    ld   a, SK_OBJ                     ; automatic: a frame slot (spec.md 5.2)
    call DCL_LOCAL
    set  SF_AUTO, (ix + S_FLAGS)
    call DCL_GETTYPE
    call TY_SIZE
    ld   de, (FRAME_OFS)
    ld   (ix + S_VAL), e
    add  hl, de
    jp   c, CC_E_FRAME
    ld   a, h
    or   a
    jp   nz, CC_E_FRAME                ; more than 255 bytes (spec.md 4.10)
    ld   (FRAME_OFS), hl
    ld   de, (FRAME_MAX)
    sbc  hl, de
    jr   c, .auto_init
    add  hl, de
    ld   (FRAME_MAX), hl
.auto_init:
    ld   a, (TOK_KIND)
    cp   TK_ASSIGN
    ret  nz
    jp   CC_E_NOTSUP                   ; automatic initialisers: scalars in Phase 2, aggregates
                                       ; not supported (spec.md 4.7)
.typedef:
    ld   a, SK_TYPEDEF
    call DCL_LOCAL
    jr   DCL_NOINIT
.func:
    ld   a, c
    cp   SC_AUTO
    jp   nc, CC_E_STORAGE              ; auto, register
    call IS_BLOCK
    jr   z, .fn
    ld   a, c
    cp   SC_STATIC
    jp   z, CC_E_STORAGE               ; static function at block scope
.fn:
    call DCL_NOINIT
    ld   a, SK_FUNC
    call DCL_GLOBAL
    jp   DCL_ALIAS
.file:
    ld   a, c
    cp   SC_AUTO
    jp   nc, CC_E_STORAGE              ; auto, register at file scope
    jr   .global
.extern:                               ; block-scope extern: the file-scope object, and a
    call DCL_NOINIT                    ; local name for it
.global:
    ld   a, SK_OBJ
    call DCL_GLOBAL
    call DCL_STATIC
    jp   DCL_ALIAS                     ; (nothing at file scope)
.static:
    ld   a, SK_OBJ
    call DCL_LOCAL
    set  SF_STATIC, (ix + S_FLAGS)
    jr   DCL_STATIC

; DCL_NOINIT -- no initialiser may follow. Errors: E_INIT. Destroys: AF
DCL_NOINIT:
    ld   a, (TOK_KIND)
    cp   TK_ASSIGN
    ret  nz
    jp   CC_E_INIT

; DCL_LOCAL -- a new entry of kind A for NM in the current scope, type HL, const flag B
; Out: IX = the entry. Errors: E_REDECL. Destroys: AF, BC, DE, HL
DCL_LOCAL:
    push hl
    push bc
    call DCL_NEWCUR
    pop  bc
    pop  hl
    jp   DCL_TYPE

; IS_BLOCK -- NZ if a block or prototype scope is open (Z: file scope). Destroys: AF
IS_BLOCK:
    ld   a, (SCOPE_BASE + 1)
    or   a
    ret

; ============================================================================
; DCL_STATIC -- static storage for the object IX, then its initialiser if `=` follows
; In:  IX = object entry (type, flags); current token after the declarator
; Out: storage allocated unless the object is extern with an incomplete type (value 0 = none)
; Errors: E_INCOMPLETE, E_REDEF (second initialiser), E_TOOBIG, the initialiser's errors
; Destroys: AF, BC, DE, HL (IX kept unless an initialiser is parsed)
; ============================================================================
DCL_STATIC:
    ld   a, (TOK_KIND)
    cp   TK_ASSIGN
    jr   z, .init
    ld   a, (ix + S_VAL)
    or   (ix + S_VAL + 1)
    ret  nz                            ; storage exists
    call DCL_GETTYPE
    call TY_SIZE0
    ld   a, h
    or   l
    jr   nz, DCL_ALLOC
    bit  SF_EXTERN, (ix + S_FLAGS)
    ret  nz                            ; extern of an incomplete type: storage later
    jp   TY_E_INCOMPLETE
.init:
    bit  SF_DEFINED, (ix + S_FLAGS)
    jp   nz, CC_E_REDEF
    set  SF_DEFINED, (ix + S_FLAGS)
    call LEX_NEXT                      ; the initialiser's first token
    push ix
    call DCL_GETTYPE
    push hl
    call TY_SIZE0
    ld   a, h
    or   l
    jr   nz, .sized
    pop  hl                            ; `[]`: a counting pass sizes the array
    push hl
    call LEX_MARK
    ld   a, 1
    ld   (CX_NOEVAL), a
    ld   de, 0
    call INIT_TOP                      ; BC = elements
    xor  a
    ld   (CX_NOEVAL), a
    ld   h, b
    ld   l, c
    call LEX_RESTORE
    push hl
    call LEX_NEXT
    pop  bc
    pop  hl
    push bc
    call TY_DEREF
    pop  bc
    call TY_ARRAY
    pop  ix
    push ix
    call DCL_SETTYPE
    push hl
    call TY_SIZE
.sized:                                ; HL = size; stack: type, entry
    pop  de
    pop  ix
    push de
    call DCL_ALLOCIF
    pop  hl
    ld   e, (ix + S_VAL)
    ld   d, (ix + S_VAL + 1)
    jp   INIT_TOP

; DCL_ALLOCIF -- static storage of HL bytes for the object IX unless it has storage
; DCL_ALLOC -- the same, unconditionally. Destroys: AF, BC, DE, HL (IX kept)
DCL_ALLOCIF:
    ld   a, (ix + S_VAL)
    or   (ix + S_VAL + 1)
    ret  nz
DCL_ALLOC:
    ld   b, h
    ld   c, l
    call DATA_ALLOC
    ld   (ix + S_VAL), l
    ld   (ix + S_VAL + 1), h
    ret

; NEED_NAME -- the declarator must have named something. Errors: E_SYNTAX. Destroys: AF
NEED_NAME:
    ld   a, (NM_LEN)
    or   a
    ret  nz
    jp   CC_E_SYNTAX

; DCL_GETTYPE -- HL = the type of entry IX. DCL_SETTYPE -- the type of entry IX = HL.
; Destroys: -
DCL_GETTYPE:
    ld   l, (ix + S_TYPE)
    ld   h, (ix + S_TYPE + 1)
    ret
DCL_SETTYPE:
    ld   (ix + S_TYPE), l
    ld   (ix + S_TYPE + 1), h
    ret

; ============================================================================
; DCL_TYPE -- set the type of entry IX, and SF_CONST if a const object (spec.md 4.2: const in
; the specifiers makes the object const unless it is a pointer; arrays: their elements)
; In:  IX = entry, HL = type, B = const flag
; Destroys: AF, BC, DE, HL
; ============================================================================
DCL_TYPE:
    call DCL_SETTYPE
    ld   a, b
    or   a
    ret  z
.strip:
    call TY_CLASS
    cp   TC_ARRAY
    jr   nz, .class
    call TY_DEREF
    jr   .strip
.class:
    cp   TC_PTR
    ret  z
    set  SF_CONST, (ix + S_FLAGS)
    ret

; ============================================================================
; DCL_NEWCUR -- a new entry for NM in the current scope, which must not declare NM already
; In:  A = kind (an ordinary identifier). Out: IX = HL = the entry
; Errors: E_REDECL
; Destroys: AF, BC, DE
; ============================================================================
DCL_NEWCUR:
    push af
    ld   c, NS_ORD
    call SYM_FIND_CUR
    jp   z, CC_E_REDECL
    pop  af
    jp   SYM_NEW

; ============================================================================
; DCL_GLOBAL -- declare NM in file scope (an object or a function), merging with an earlier
; declaration (single translation unit: block-scope extern declarations share the entry)
; In:  A = SK_OBJ / SK_FUNC, HL = type, C = storage class, B = const flag
; Out: IX = the file-scope entry
; Errors: E_REDECL (another kind of name; `static` after a non-static declaration, or an object
;      defined without `static` after a static declaration), E_TYPE (incompatible types)
; Destroys: AF, BC, DE, HL
; ============================================================================
DCL_GLOBAL:
    push hl
    push bc
    push af
    ld   c, NS_ORD
    ld   de, 0
    ld   hl, (SYM_GLO)
    call SYM_FIND
    jr   nz, .new
    pop  af
    cp   (ix + S_KIND)
    jp   nz, CC_E_REDECL
    pop  bc
    ld   e, a                          ; E = kind
    ld   a, c
    cp   SC_STATIC
    jr   nz, .nonstatic
    bit  SF_STATIC, (ix + S_FLAGS)
    jp   z, CC_E_REDECL                ; static after a non-static declaration
    jr   .types
.nonstatic:
    cp   SC_EXTERN
    jr   z, .types
    dec  e
    jr   nz, .types                    ; (SK_OBJ = 1)
    bit  SF_STATIC, (ix + S_FLAGS)
    jr   nz, CC_E_REDECL               ; an object without static after a static one
    res  SF_EXTERN, (ix + S_FLAGS)     ; a definition now
.types:
    pop  de                            ; the new type
    call DCL_GETTYPE                   ; HL = the old type
    push de
    push hl
    call TY_EQUAL
    pop  hl
    pop  de
    jp   nz, CC_E_TYPE
    call DCL_PARTIAL                   ; take the new type if the old one lacks information
    ret  nz
    ex   de, hl
    jr   DCL_SETTYPE
.new:
    pop  af
    call SYM_NEWG
    pop  bc
    ld   a, c                          ; extern (2) -> SF_EXTERN, static (3) -> SF_STATIC
    or   a
    jr   z, .type
    neg
    add  a, 4
    ld   (ix + S_FLAGS), a
.type:
    pop  hl
    jp   DCL_TYPE

; DCL_PARTIAL -- Z if type HL is an array of unknown size or an unprototyped function
; Destroys: AF, BC (DE, HL kept)
DCL_PARTIAL:
    call TY_CLASS
    cp   TC_ARRAY
    jr   z, .fields
    cp   TC_FUNC
    ret  nz
.fields:
    push de
    call TY_FIELDS
    pop  de
    cp   TC_FUNC
    jr   z, .proto
    ld   a, b
    or   c
    ret
.proto:
    ld   a, b
    and  1 << TFF_PROTO
    ret

; ============================================================================
; DCL_ALIAS -- at block scope, a local name for the file-scope entry IX (block-scope extern and
; function declarations)
; In:  IX = the file-scope entry; NM. Out: at file scope nothing
; Errors: E_REDECL (the name is declared in this block as something else)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
DCL_ALIAS:
    call IS_BLOCK
    ret  z
    push ix
    ld   c, NS_ORD
    call SYM_FIND_CUR
    pop  de
    jr   nz, .new
    bit  SF_EXTERN, (ix + S_FLAGS)     ; declared again in this block: must be another
    ret  nz                            ; extern declaration (DCL_GLOBAL checked the type)
    jr   CC_E_REDECL
.new:
    push de
    inc  de
    inc  de
    ld   a, (de)                       ; the kind
    call SYM_NEW                       ; HL = IX = the local entry
    ld   bc, S_FLAGS
    add  hl, bc
    ex   de, hl
    pop  hl
    add  hl, bc
    ld   c, S_NAME - S_FLAGS
    ldir                               ; flags, type, value
    set  SF_EXTERN, (ix + S_FLAGS)
    ret

; ============================================================================
; Compile error exits (3 bytes each: `ld hl,nn` swallows the next `ld a,n`)
; ============================================================================
CC_E_NOTSUP:
    ld   a, E_NOTSUP
    DB   $21
CC_E_SYNTAX:
    ld   a, E_SYNTAX
    DB   $21
CC_E_REDECL:
    ld   a, E_REDECL
    DB   $21
CC_E_REDEF:
    ld   a, E_REDEF
    DB   $21
CC_E_UNDECL:
    ld   a, E_UNDECL
    DB   $21
CC_E_TYPESPEC:
    ld   a, E_TYPESPEC
    DB   $21
CC_E_BADDECL:
    ld   a, E_BADDECL
    DB   $21
CC_E_STORAGE:
    ld   a, E_STORAGE
    DB   $21
CC_E_PARAM:
    ld   a, E_PARAM
    DB   $21
CC_E_INIT:
    ld   a, E_INIT
    DB   $21
CC_E_ARRAYSIZE:
    ld   a, E_ARRAYSIZE
    DB   $21
CC_E_TYPE:
    ld   a, E_TYPE
    DB   $21
CC_E_CONSTEXPR:
    ld   a, E_CONSTEXPR
    DB   $21
CC_E_OPERAND:
    ld   a, E_OPERAND
    DB   $21
CC_E_MEMBER:
    ld   a, E_MEMBER
    DB   $21
CC_E_LVALUE:
    ld   a, E_LVALUE
    DB   $21
CC_E_FRAME:
    ld   a, E_FRAME
    DB   $21
CC_E_PARAMS:
    ld   a, E_PARAMS
    jp   CC_ERROR
