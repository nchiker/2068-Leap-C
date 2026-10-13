; ============================================================================
; include/leapc_decl.inc -- type handles, type nodes, symbol entries and operand kinds of the
; compiler front end (spec.md sections 4.2-4.4; project_plan.md M1.2)
;
; The encoding is part of the contract between the declaration parser, the symbol table, the
; expression compiler and tools/declcheck.py (the test harness decodes the workspace with it).
;
; TYPE HANDLES (16 bits)
;   H < TY_NODE_H   a scalar base with pointer depth H: L = TB_* (0..4), H = number of `*`.
;                   int = $0003, char * = $0101, void ** = $0200. Pointers to scalar bases never
;                   use a node, so equal handles <=> equal types for them.
;   H >= TY_NODE_H  the address of a type node in the compile workspace (global area).
;
; TYPE NODES (global area, never reclaimed during a compile)
;   +0 kind         TN_*
;   +1 cache:2      handle of "pointer to this type" (0 until first needed; TY_PTR makes it), so
;                   every type has exactly one pointer type
;   +3 A:2          PTR: target   ARRAY: element   FUNC: return type   STRUCT: size in bytes
;   +5 B:2          ARRAY: element count (0 = unknown, `[]`)
;                   FUNC: [parameter count:1][TFF_* flags:1]
;                   STRUCT: first member entry (0 = incomplete: no body yet)
;   +7 ...          FUNC: the parameter types, 2 bytes each, LAST parameter first
;
; SYMBOL ENTRIES (local or global area; see src/compiler/symtab.asm)
;   +0 link:2       next entry of the chain (scope chains: older entry; member lists: next member)
;   +2 kind         SK_* (the high nibble is the namespace)
;   +3 len          name length, 0-31 (0 = unnamed parameter)
;   +4 flags        SF_* bits
;   +5 type:2       type handle (SK_TAG: the struct node, or int for an enum tag)
;   +7 value:2      SK_OBJ: address (static storage), frame offset (SF_AUTO) or argument offset
;                   (SF_PARAM). SK_ENUMC: the value. SK_MEMBER: byte offset. SK_FUNC: 0 until
;                   code generation (M1.3)
;   +9 name         len bytes (the first 31 characters of the identifier)
;   An entry takes 9 + len bytes.
; ============================================================================

    IFNDEF LEAPC_DECL_INC
    DEFINE LEAPC_DECL_INC

; ---- scalar bases (L of a scalar handle) and type classes (TY_CLASS) ----
TB_VOID         EQU 0
TB_CHAR         EQU 1       ; char = unsigned char (spec.md 4.2)
TB_SCHAR        EQU 2       ; signed char
TB_INT          EQU 3       ; int, short, signed, enum
TB_UINT         EQU 4       ; unsigned, unsigned short
TY_NODE_H       EQU $40     ; handles with H >= this are node addresses (the workspace is >= $7800)
TY_PTR_MAX      EQU $10     ; pointer levels on a scalar base are limited to 15
TY_INT          EQU TB_INT
TY_UINT         EQU TB_UINT

TC_VOID         EQU 0       ; TC_VOID..TC_UINT equal TB_*
TC_CHAR         EQU 1
TC_SCHAR        EQU 2
TC_INT          EQU 3
TC_UINT         EQU 4
TC_PTR          EQU 5
TC_ARRAY        EQU 6
TC_FUNC         EQU 7
TC_STRUCT       EQU 8

; ---- type nodes ----
TN_PTR          EQU 1       ; class = kind + TC_PTR - TN_PTR
TN_ARRAY        EQU 2
TN_FUNC         EQU 3
TN_STRUCT       EQU 4
TN_KIND         EQU 0
TN_CACHE        EQU 1
TN_A            EQU 3
TN_B            EQU 5
TN_PARAMS       EQU 7
TN_FFLAGS       EQU TN_B + 1
TN_NODE_SIZE    EQU 7       ; PTR, ARRAY, STRUCT; FUNC: 7 + 2 * parameters
TFF_PROTO       EQU 0       ; FUNC flags: declared with a parameter list (a prototype)

; ---- symbol entries ----
S_LINK          EQU 0
S_KIND          EQU 2
S_LEN           EQU 3
S_FLAGS         EQU 4
S_TYPE          EQU 5
S_VAL           EQU 7
S_NAME          EQU 9

SK_OBJ          EQU $01     ; ordinary identifiers: namespace $00
SK_FUNC         EQU $02
SK_TYPEDEF      EQU $03
SK_ENUMC        EQU $04
SK_TAG          EQU $10     ; struct and enum tags (SF_ENUM)
SK_MEMBER       EQU $20     ; struct members (one list per struct)
SK_LABEL        EQU $30     ; goto labels (Phase 2)
NS_ORD          EQU $00
NS_TAG          EQU $10
NS_MEMBER       EQU $20
NS_LABEL        EQU $30

SF_STATIC       EQU 0       ; static: internal linkage (file scope) or static storage (block)
SF_EXTERN       EQU 1       ; declared with extern (or a function declaration)
SF_CONST        EQU 2       ; the object is const (direct assignment refused, M1.3)
SF_DEFINED      EQU 3       ; function body seen / object initialised / struct-or-enum body seen
SF_AUTO         EQU 4       ; automatic storage: value = frame offset (IX+value)
SF_PARAM        EQU 5       ; parameter: value = argument offset (2 * index)
SF_ENUM         EQU 6       ; SK_TAG: an enum tag
SF_NOADDR       EQU 7       ; static object without storage yet (incomplete-type extern)

; ---- declaration specifiers (DECL_SPECS) ----
SC_NONE         EQU 0
SC_TYPEDEF      EQU 1
SC_EXTERN       EQU 2
SC_STATIC       EQU 3
SC_AUTO         EQU 4
SC_REGISTER     EQU 5

; ---- expression operands (X_KIND; src/compiler/expr.asm) ----
OK_CONST        EQU 0       ; integer constant: X_VAL (an integer constant expression)
OK_ADDRC        EQU 1       ; constant computed from an address: X_VAL (static initialisers only)
OK_LVALC        EQU 2       ; object at the constant address X_VAL (static storage)
OK_LVAL         EQU 3       ; object at an address known only at run time (locals, *p)
OK_RVAL         EQU 4       ; value known only at run time

; ---- image regions (spec.md 3.2): region order and the IMG_LIM table ----
IMG_REGIONS     EQU 4

    ENDIF
