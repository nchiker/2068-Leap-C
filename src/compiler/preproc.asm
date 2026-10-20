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
; PP_DIRECTIVE -- (jumped to by PP_HOOK at a `#` that starts a line) the directive; then the
; next token, as LEX_NEXT
; Errors: E_NOTSUP (another directive or pragma, a function-like macro, another header), E_SYNTAX, E_REDEF
;      (a macro defined again), E_NOMEM, the lexical errors of the line
; Destroys: AF, BC, DE, HL (IX and NM kept: a directive can come between any two tokens)
; ============================================================================
PP_DIRECTIVE:
    ld   a, 1 << LM_EOL
    ld   (LEX_MODE), a
    call LEX_NEXT                      ; the directive's name
    cp   TK_EOL
    jr   z, PP_END                     ; `#` alone
    ld   hl, PP_DIRS
PP_DISPATCH:                           ; the current token (A) names a record of the chain HL:
    cp   TK_IDENT                      ; its handler (#if, #else: keywords)
    jr   nz, PP_E_NOTSUP
    call PP_FIND_IN
    jr   nz, PP_E_NOTSUP
    ld   de, PM_TEXT
    add  hl, de
    rst  $08                           ; LDI: the handler
    jp   (hl)
PP_E_NOTSUP:
    jp   CC_E_NOTSUP
PP_PRAGMA:                             ; #pragma NAME (PP_PRAGMAS; any other: not supported)
    call LEX_NEXT
    ld   hl, PP_PRAGMAS
    jr   PP_DISPATCH
PP_HIRES:                              ; #pragma hires (spec.md 3.2): image region 4, display file 2,
    ld   hl, (IMG_LIM + 4 * 3 + 2)     ; is full from here on: its [low] = its [high]. What is already
    ld   (IMG_LIM + 4 * 3), hl         ; there stays (mode(1) then refuses: LIB_MODE)
    jr   PP_LINE_END
PP_UNDEF:                              ; #undef NAME (not defined: nothing to do)
    call PP_NAME
    call PP_FIND
    jr   nz, PP_LINE_END
    inc  hl
    inc  hl
    ld   (hl), 0                       ; its name's length: never found again
PP_LINE_END:                           ; the line must end here
    call LEX_NEXT
    cp   TK_EOL
    jp   nz, CC_E_SYNTAX
PP_END:
    xor  a
    ld   (LEX_MODE), a
    jp   LEX_NEXT                      ; the token after the directive
PP_DEFINE:                             ; #define NAME replacement
    call PP_NAME
    ld   hl, (LEX_PTR)
    ld   a, (hl)
    cp   '('
    jr   z, PP_E_NOTSUP                ; a function-like macro
    call PP_FIND
    jp   z, CC_E_REDEF
    ld   bc, PM_SIZE
    call WS_GALLOC                     ; HL = the record
    ld   de, (PP_MACROS)
    ld   (PP_MACROS), hl
    call SW_PUT                        ; [link]
    ld   a, (TOK_LEN)
    ld   (hl), a                       ; [name length]
    inc  hl
    ld   de, (TOK_PTR)
    call SW_PUT                        ; [name]
    ld   de, (LEX_PTR)
    call SW_PUT                        ; [replacement]: the rest of the line
.text:
    call LEX_NEXT
    cp   TK_EOL
    jr   nz, .text
    jr   PP_END
PP_INCLUDE:                            ; #include <leap.h> or "leap.h"
    ld   hl, (LEX_PTR)
.blank:
    ld   a, (hl)
    inc  hl
    cp   ' '
    jr   z, .blank
    ld   c, '>'
    cp   '<'
    jr   z, .header
    ld   c, a
    cp   '"'
    jp   nz, PP_E_NOTSUP
.header:
    ld   de, PP_LEAPH
    ld   b, PP_LEAPH_N
.cmp:
    ld   a, (de)
    cp   (hl)
    jp   nz, PP_E_NOTSUP
    inc  hl
    inc  de
    djnz .cmp
    ld   a, (hl)
    cp   c
    jp   nz, PP_E_NOTSUP               ; (the closing > or ")
    inc  hl
    ld   (LEX_PTR), hl
    jp   PP_LINE_END

; PP_NAME -- the next token: an identifier (TOK_BUF). Errors: E_SYNTAX. Destroys: AF, BC, DE, HL
PP_NAME:
    call LEX_NEXT
    cp   TK_IDENT
    ret  z
    jp   CC_E_SYNTAX

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

; the directive names, as records for PP_FIND_IN (the "replacement" is the handler)
PP_DIRS:
    DW   .undef
    DB   6
    DW   .n_define, PP_DEFINE
.undef:
    DW   .include
    DB   5
    DW   .n_undef, PP_UNDEF
.include:
    DW   .pragma
    DB   7
    DW   .n_include, PP_INCLUDE
.pragma:
    DW   0
    DB   6
    DW   .n_pragma, PP_PRAGMA
.n_define:
    DB   "define"
.n_undef:
    DB   "undef"
.n_include:
    DB   "include"
.n_pragma:
    DB   "pragma"
; the pragmas (PP_PRAGMA)
PP_PRAGMAS:
    DW   0
    DB   5
    DW   .n_hires, PP_HIRES
.n_hires:
    DB   "hires"
PP_LEAPH:
    DB   "leap.h"
PP_LEAPH_N      EQU $ - PP_LEAPH
