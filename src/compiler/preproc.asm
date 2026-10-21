; ============================================================================
; src/compiler/preproc.asm -- the preprocessor (spec.md 4.8): object-like macros, directives
;
; The preprocessor lives in the lexer's token stream: LEX_NEXT hands every token it completes to
; PP_HOOK, and a line end to PP_EOL when LEX_MODE is not 0. The parser never sees it.
;
; Directives. A `#` that is the first token on its line starts a directive;
; its tokens are read with LM_EOL (TK_EOL ends them) and never expanded. `#define NAME replacement`,
; `#undef NAME`, `#include <leap.h>` / `"leap.h"` (a no-op: the library is built in, spec.md 7),
; `#pragma hires` (image region 4 reserved, spec.md 3.2). Any other directive or pragma, a
; function-like macro and any other header are "not supported"; `#` alone is ignored.
;
; Macros. A definition is a record [link][name length][name][replacement] in the global area, on
; the chain PP_MACROS; the name and the replacement (the rest of the line) are pointers into the
; #define line in the line store. The replacement is lexed once at the definition, so its lexical
; errors are reported there. When an identifier names a macro that
; is not being expanded, the lexer reads the replacement instead (LM_MACRO) and comes back after the
; macro's name at the replacement's line end (PP_EOL). Expansions nest up to PP_MAX deep (PP_STACK
; up to PP_SP: per level LEX_PTR, LEX_LINE, LEX_BOLP and TOK_PTR as at its name, then the macro); a
; macro's name inside its own expansion stays an identifier (C89 6.8.3.4). The tokens of an
; expansion carry the line where the macro is used.
;
; Rewinding (decl.asm LEX_MARK / LEX_RESTORE). The mark of a token of an expansion is the outermost
; macro's name (PP_STACK level 0) and the token's number in the expansion (PP_TOKN); LEX_RESTORE
; expands again and skips to the token.
; ============================================================================

; ============================================================================
; PP_HOOK -- (jumped to by LEX_NEXT with a complete token) a directive or a macro's name is replaced
; by what follows it; a token of an expansion is counted
; In:  TOK_* (the token), LEX_MODE
; Out: A = TOK_KIND of the token returned
; Errors: the directives' errors; E_NESTING (macros nested more than PP_MAX deep, an expansion of
;      more than 255 tokens)
; Destroys: AF, BC, DE, HL (IX and NM kept)
; ============================================================================
PP_HOOK:
    ld   a, (LEX_MODE)
    and  (1 << LM_EOL) | (1 << LM_RAW)
    jr   nz, .out                      ; a directive's tokens; the plain lexer
    ld   a, (TOK_KIND)
    cp   TK_IDENT
    jr   z, .ident
    cp   TK_HASH
    jr   nz, .out
    ld   hl, TOK_FLAGS
    bit  TF_BOL, (hl)
    jr   nz, PP_DIRECTIVE
.out:                                  ; the token is returned: in an expansion, it is counted
    ld   hl, LEX_MODE
    bit  LM_MACRO, (hl)
    ld   a, (TOK_KIND)
    ret  z
    ld   hl, PP_TOKN
    inc  (hl)
    ret  nz
    jr   PP_E_NESTING                  ; (more than 255 tokens)
.ident:
    call PP_FIND                       ; HL = the macro
    jr   nz, .out
    ex   de, hl
    ld   hl, PP_STACK
.active:                               ; a macro being expanded: its name stays an identifier
    ld   bc, (PP_SP)
    or   a
    sbc  hl, bc
    add  hl, bc
    jr   z, .push
    ld   bc, PP_LEVEL - 2
    add  hl, bc
    ld   a, (hl)
    inc  hl
    cp   e
    ld   a, (hl)
    inc  hl
    jr   nz, .active
    cp   d
    jr   nz, .active
    jr   .out
.push:                                 ; HL = PP_SP
    ld   bc, PP_STACK + PP_LEVEL * PP_MAX
    sbc  hl, bc                        ; (C clear)
    add  hl, bc
    jr   nc, PP_E_NESTING
    push de
    ex   de, hl
    ld   hl, LEX_PTR
    ld   bc, PP_LEVEL - 2
    ldir                               ; LEX_PTR, LEX_LINE, LEX_BOLP, TOK_PTR (the name's position)
    pop  hl                            ; the macro
    ex   de, hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    ld   (PP_SP), hl
    ex   de, hl
    ld   de, PM_TEXT
    add  hl, de
    rst  $08                           ; LDI: HL = the replacement
    ld   (LEX_PTR), hl
    ld   hl, LEX_MODE
    set  LM_MACRO, (hl)
    jp   LEX_NEXT                      ; its first token (or what follows the macro's name)
PP_E_NESTING:
    ld   a, E_NESTING
    jp   CC_ERROR

; ============================================================================
; PP_DIRECTIVE -- (jumped to by PP_HOOK at a `#` that starts a line) the directive (XP_DIRECTIVE in
; the EXROM, src/compiler/directives.asm: Phase 8, ledger L42); then the next token, as LEX_NEXT
; Errors: those of XP_DIRECTIVE
; Destroys: AF, BC, DE, HL (IX and NM kept: a directive can come between any two tokens)
; ============================================================================
PP_DIRECTIVE:
    ld   bc, LEAPC_EXROM_DIRECTIVE
    call CX_XCALL
    xor  a
    ld   (LEX_MODE), a
    jp   LEX_NEXT                      ; the token after the directive

; ============================================================================
; PP_EOL -- (jumped to by LEX_NEXT at a line end in a directive or a macro's replacement)
; In:  A = LEX_MODE & (LM_EOL | LM_MACRO), HL -> the CR
; Out: LM_EOL: the token TK_EOL. LM_MACRO: the lexer goes on after the macro's name
; ============================================================================
PP_EOL:
    rra
    jr   nc, .macro
    call LEX_BEGIN                     ; LM_EOL: the end-of-line token
    call LEX_NEWLINE
    ld   a, TK_EOL
    jp   LEX_NEXT.done
.macro:                                ; LM_MACRO: the end of a replacement
    ld   hl, (PP_SP)
    ld   de, -PP_LEVEL
    add  hl, de
    ld   (PP_SP), hl
    ld   de, LEX_PTR
    ld   bc, 5
    ldir                               ; LEX_PTR, LEX_LINE, LEX_BOLP: after the macro's name
    ld   de, PP_STACK + 5
    or   a
    sbc  hl, de
    jr   nz, .open
    ld   hl, LEX_MODE                  ; the main text again
    res  LM_MACRO, (hl)
    xor  a
    ld   (PP_TOKN), a
.open:
    ld   hl, (LEX_PTR)
    jp   LEX_NEXT.skip

; ============================================================================
; PP_FIND -- the defined macro named by the current token (TOK_BUF, TOK_LEN)
; PP_FIND_IN -- the same in the chain of records from HL
; Out: Z: HL = its record. NZ: none
; Destroys: AF, BC, DE, HL
; ============================================================================
PP_FIND:
    ld   hl, (PP_MACROS)
PP_FIND_IN:
    ld   a, h
    or   l
    jr   z, .none
    push hl
    inc  hl
    inc  hl
    ld   a, (TOK_LEN)
    cp   (hl)                          ; (#undef sets the length to 0: never found)
    jr   nz, .differ
    ld   b, a
    inc  hl
    ld   e, (hl)
    inc  hl
    ld   d, (hl)                       ; DE -> the name
    ld   hl, TOK_BUF
.cmp:
    ld   a, (de)
    cp   (hl)
    jr   nz, .differ
    inc  hl
    inc  de
    djnz .cmp
.differ:
    pop  hl
    ret  z
    rst  $08                           ; LDI: the next record
    jr   PP_FIND_IN
.none:
    inc  a                             ; NZ
    ret
