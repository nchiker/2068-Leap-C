; ============================================================================
; src/compiler/libnames.asm -- the names and signatures of the built-in library (spec.md 7), EXROM
;
; Compile-time data and the binding itself (XL_BIND, Phase 8: it was in HOME, budget ledger L42),
; reached through the HOME trampoline LIB_BIND (src/rom/home.asm). Bank rule 3: LIB_FIND reads only the
; identifier (NM_PTR: the source in the line store) and its own table; XL_BIND writes only the compile
; workspace (the declaration), and its one error (E_NOMEM) leaves through CC_ERROR, which pages the
; EXROM out.
;
; The binding (spec.md 7.1). The library's names are not declared in advance. When the expression
; compiler meets an identifier that no declaration in scope names (CX_PRIMARY), XL_BIND looks it up
; among the library's names and, if it is a library function, declares it there and then: a defined
; file-scope function at its ROM address, with its prototype. A program's own declaration of the
; same name comes first and hides the library function (the names are not reserved);
; `#include <leap.h>` is a no-op.
;
; LIB_NAMES: one record per function, [name][address][signature], then a 0:
;   name       the characters, the last with bit 7 set
;   address    the HOME routine (src/runtime/library.asm, through the HOME exports)
;   signature  [return type:4][parameters:4]: the return type is [pointer:1][scalar base:3]
;              (spec.md 4.2: void, int, unsigned, char * or void *); the parameters are an index
;              into LIB_PARAMS
; LIB_PARAMS: one byte per parameter list, the last parameter in bit 0: a bit is set if that
;   parameter is a pointer (void *: any object pointer converts to it), clear for an int; a 1 above
;   the first parameter ends the list. 0: printf, whose arguments are variadic (no prototype: no
;   checks, the default promotions)
; ============================================================================

; ============================================================================
; LIB_FIND -- the library function named NM
; In:  NM_PTR, NM_LEN (1-31)
; Out: Z: HL = its address, D = its signature, E = its parameter list (LIB_PARAMS). NZ: none
; Destroys: AF, BC, DE, HL
; ============================================================================
LIB_FIND:
    ld   hl, LIB_NAMES
.entry:
    ld   a, (hl)
    or   a
    jr   z, .none
    ld   de, (NM_PTR)
    ld   a, (NM_LEN)
    ld   b, a
.cmp:
    ld   a, (de)
    xor  (hl)
    inc  hl
    inc  de
    add  a, a                          ; C: the name's last character; Z: the same character
    jr   c, .last
    jr   nz, .skip
    djnz .cmp
.skip:                                 ; past the name's last character
    ld   a, (hl)
    inc  hl
    rla
    jr   nc, .skip
    jr   .next
.last:
    jr   nz, .next
    dec  b
    jr   nz, .next                     ; NM is longer
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    inc  hl
    ld   d, (hl)                       ; D = the signature
    ld   a, d
    and  $0F
    add  a, LIB_PARAMS & $FF
    ld   l, a
    ld   h, LIB_PARAMS >> 8
    ld   e, (hl)                       ; E = the parameter list
    ld   h, b
    ld   l, c                          ; HL = the address
    cp   a                             ; Z
    ret
.next:
    inc  hl
    inc  hl
    inc  hl                            ; past the address and the signature
    jr   .entry
.none:
    dec  a                             ; NZ
    ret

; ============================================================================
; XL_BIND -- declare the undeclared identifier NM if it names a library function (EXROM; HOME: the
; trampoline LIB_BIND)
; In:  NM_PTR, NM_LEN (not declared in any scope)
; Out: Z: IX = the new file-scope entry (SK_FUNC, defined, extern; value = the address, type = its
;      prototype), C = NS_ORD. NZ: not a library name, nothing changed
; Errors: E_NOMEM
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
XL_BIND:
    call LIB_FIND                      ; HL = the address, D = the signature, E = the parameters
    ret  nz
    push hl                            ; [address]
    ld   a, e
    ld   bc, TN_NODE_SIZE - 2
.size:                                 ; BC = 7 + 2 * the parameter count (the marker's position)
    inc  c
    inc  c
    srl  a
    jr   nz, .size
    push de
    ld   a, TN_FUNC
    call TY_NEW                        ; HL = the function type node, zeroed
    pop  de
    push hl                            ; [address][node]
    inc  hl
    inc  hl
    inc  hl                            ; -> TN_A: the return type ...
    ld   a, d
    rra
    rra
    rra
    rra
    and  7
    ld   (hl), a                       ; ... its scalar base ...
    inc  hl
    rl   d
    rl   (hl)                          ; ... and its pointer level (0 or 1)
    inc  hl                            ; -> TN_B: the parameter count ...
    ld   a, e
    or   a
    jr   z, .entry                     ; (printf: no parameter list, no checks)
    push hl
    inc  hl
    ld   (hl), 1 << TFF_PROTO          ; ... and the flags: a prototype
    ld   b, 0
.param:                                ; TN_PARAMS: the parameter types, the last first
    inc  hl
    srl  e
    jr   z, .counted                   ; (the marker)
    inc  b
    jr   c, .ptr
    ld   (hl), TB_INT
    inc  hl
    jr   .param
.ptr:
    inc  hl
    ld   (hl), 1                       ; void *: base TB_VOID (0), one pointer level
    jr   .param
.counted:
    pop  hl
    ld   (hl), b
.entry:
    ld   a, SK_FUNC
    call SYM_NEWG                      ; IX = the entry for NM
    ld   (ix + S_FLAGS), 1 << SF_DEFINED | 1 << SF_EXTERN
    pop  hl
    call DCL_SETTYPE
    pop  de
    ld   (ix + S_VAL), e
    ld   (ix + S_VAL + 1), d
    xor  a                             ; Z
    ld   c, a                          ; C = NS_ORD (CX_PRIMARY looks the entry up again)
    ret

; ---- the signatures: return types [pointer:1][base:3] and parameter lists ----
LR_VOID         EQU TB_VOID
LR_INT          EQU TB_INT
LR_UINT         EQU TB_UINT
LR_CHARP        EQU 8 | TB_CHAR
LR_VOIDP        EQU 8 | TB_VOID
LP_VARIADIC     EQU 0       ; printf
LP_NONE         EQU 1       ; ()
LP_I            EQU 2       ; (int)
LP_P            EQU 3       ; (void *)
LP_II           EQU 4       ; (int, int)
LP_PI           EQU 5       ; (void *, int)
LP_PP           EQU 6       ; (void *, void *)
LP_PPI          EQU 7       ; (void *, void *, int)
LP_PII          EQU 8       ; (void *, int, int)
LP_IPI          EQU 9       ; (int, void *, int)
LP_IIII         EQU 10      ; (int, int, int, int)
LP_IIIIP        EQU 11      ; (int, int, int, int, void *)
LIB_PARAMS:
    DB   0, %1, %10, %11, %100, %110, %111, %1110, %1100, %1010, %10000, %100001
    ASSERT (LIB_PARAMS & $FF) + LP_IIIIP < 256

    MACRO LIBFN name, routine, ret, params
    DC   name
    DW   routine
    DB   ret << 4 | params
    ENDM

LIB_NAMES:
    LIBFN "cls", LIB_CLS, LR_VOID, LP_NONE
    LIBFN "putchar", LIB_PUTCHAR, LR_INT, LP_I
    LIBFN "puts", LIB_PUTS, LR_INT, LP_P
    LIBFN "print", LIB_PRINT, LR_VOID, LP_P
    LIBFN "printf", LIB_PRINTF, LR_INT, LP_VARIADIC
    LIBFN "at", LIB_AT, LR_VOID, LP_II
    LIBFN "tab", LIB_TAB, LR_VOID, LP_I
    LIBFN "ink", LIB_INK, LR_VOID, LP_I
    LIBFN "paper", LIB_PAPER, LR_VOID, LP_I
    LIBFN "border", LIB_BORDER, LR_VOID, LP_I
    LIBFN "bright", LIB_BRIGHT, LR_VOID, LP_I
    LIBFN "flash", LIB_FLASH, LR_VOID, LP_I
    LIBFN "inverse", LIB_INVERSE, LR_VOID, LP_I
    LIBFN "over", LIB_OVER, LR_VOID, LP_I
    LIBFN "getkey", LIB_GETKEY, LR_INT, LP_NONE
    LIBFN "inkey", LIB_INKEY, LR_INT, LP_NONE
    LIBFN "gets", LIB_GETS, LR_CHARP, LP_PI
    LIBFN "plot", LIB_PLOT, LR_VOID, LP_II
    LIBFN "draw", LIB_DRAW, LR_VOID, LP_IIII
    LIBFN "point", LIB_POINT, LR_INT, LP_II
    LIBFN "attr", LIB_ATTRF, LR_INT, LP_II
    LIBFN "mode", LIB_MODE, LR_VOID, LP_I
    LIBFN "sprite_get", LIB_SPGET, LR_VOID, LP_IIIIP
    LIBFN "sprite_put", LIB_SPPUT, LR_VOID, LP_IIIIP
    LIBFN "beep", LIB_BEEP, LR_VOID, LP_II
    LIBFN "sound", LIB_SOUND, LR_VOID, LP_II
    LIBFN "frames", LIB_FRAMES, LR_UINT, LP_NONE
    LIBFN "pause", LIB_PAUSE, LR_VOID, LP_I
    LIBFN "rand", LIB_RAND, LR_INT, LP_NONE
    LIBFN "srand", LIB_SRAND, LR_VOID, LP_I
    LIBFN "inp", LIB_INP, LR_INT, LP_I
    LIBFN "outp", LIB_OUTP, LR_VOID, LP_II
    LIBFN "strlen", LIB_STRLEN, LR_UINT, LP_P
    LIBFN "strcpy", LIB_STRCPY, LR_CHARP, LP_PP
    LIBFN "strncpy", LIB_STRNCPY, LR_CHARP, LP_PPI
    LIBFN "strcmp", LIB_STRCMP, LR_INT, LP_PP
    LIBFN "strcat", LIB_STRCAT, LR_CHARP, LP_PP
    LIBFN "strchr", LIB_STRCHR, LR_CHARP, LP_PI
    LIBFN "memcpy", LIB_MEMCPY, LR_VOIDP, LP_PPI
    LIBFN "memmove", LIB_MEMMOVE, LR_VOIDP, LP_PPI
    LIBFN "memset", LIB_MEMSET, LR_VOIDP, LP_PII
    LIBFN "memcmp", LIB_MEMCMP, LR_INT, LP_PPI
    LIBFN "atoi", LIB_ATOI, LR_INT, LP_P
    LIBFN "itoa", LIB_ITOA, LR_CHARP, LP_IPI
    LIBFN "abs", LIB_ABS, LR_INT, LP_I
    LIBFN "malloc", LIB_MALLOC, LR_VOIDP, LP_I
    LIBFN "free", LIB_FREE, LR_VOID, LP_P
    LIBFN "exit", LIB_EXIT, LR_VOID, LP_I
    LIBFN "tape_save", LIB_TAPE_SAVE, LR_VOID, LP_PPI
    LIBFN "tape_load", LIB_TAPE_LOAD, LR_INT, LP_PPI
    DB   0
