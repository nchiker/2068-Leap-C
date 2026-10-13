; ============================================================================
; src/runtime/libbind.asm -- the compiler's binding of the built-in library (spec.md 7: leap.h)
;
; The library's names are not declared in advance. When the expression compiler meets an
; identifier that no declaration in scope names (CX_PRIMARY), LIB_BIND looks it up among the
; library's names and, if it is a library function, declares it there and then: a defined
; file-scope function at its ROM address, with its prototype. A program's own declaration of the
; same name comes first and hides the library function (the names are not reserved);
; `#include <leap.h>` is a no-op.
;
; The names and signatures are compile-time data: they are in the EXROM (LIB_FIND,
; src/compiler/libnames.asm), reached through the trampoline CX_LIBFIND (bank rule 3: the search
; reads only the identifier in the source and its own table). LIB_BIND builds the declaration in
; HOME, where the workspace errors (E_NOMEM) can be raised.
; ============================================================================

; ============================================================================
; LIB_BIND -- declare the undeclared identifier NM if it names a library function
; In:  NM_PTR, NM_LEN (not declared in any scope)
; Out: Z: IX = the new file-scope entry (SK_FUNC, defined, extern; value = the address, type = its
;      prototype), C = NS_ORD. NZ: not a library name, nothing changed
; Errors: E_NOMEM
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
LIB_BIND:
    call CX_LIBFIND                    ; HL = the address, D = the signature, E = the parameters
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
