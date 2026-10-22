; ============================================================================
; src/compiler/directives.asm -- the preprocessor's directives (spec.md 4.8), EXROM
;
; EXROM-resident since Phase 8 (budget ledger L42; it was in the HOME preprocessor,
; src/compiler/preproc.asm, which keeps the token hook, the macros' expansion and their lookup). It is
; reached through HOME's PP_DIRECTIVE (CX_XCALL) at a `#` that starts a line and reads the directive's
; tokens with the HOME lexer (rst $30), which is mapped whatever the paging. Bank rule 3: it writes only
; the compile workspace (a macro's record) and the cells (#pragma hires: IMG_LIM), never chunk 6; its
; errors leave through CC_ERROR, which pages the EXROM out.
; ============================================================================

; ============================================================================
; XP_DIRECTIVE -- (called through HOME's PP_DIRECTIVE at a `#` that starts a line) the directive,
; up to and including its line end
; Errors: E_NOTSUP (another directive or pragma, a function-like macro, another header), E_SYNTAX, E_REDEF
;      (a macro defined again), E_NOMEM, the lexical errors of the line
; Destroys: AF, BC, DE, HL (IX and NM kept)
; ============================================================================
XP_DIRECTIVE:
    ld   a, 1 << LM_EOL
    ld   (LEX_MODE), a
    rst  $30                          ; LEX_NEXT: the directive's name
    cp   TK_EOL
    ret  z                             ; `#` alone
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
    ld   a, E_NOTSUP
    jp   CC_ERROR
PP_PRAGMA:                             ; #pragma NAME (PP_PRAGMAS; any other: not supported)
    rst  $30                          ; LEX_NEXT
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
    rst  $30                          ; LEX_NEXT
    cp   TK_EOL
    ret  z
    ld   a, E_SYNTAX
    jp   CC_ERROR
PP_DEFINE:                             ; #define NAME replacement
    call PP_NAME
    ld   hl, (LEX_PTR)
    ld   a, (hl)
    cp   '('
    jr   z, PP_E_NOTSUP                ; a function-like macro
    call PP_FIND
    jr   nz, .new
    xor  a                             ; (Phase 10: a macro's ALREADY DEFINED names nothing; NM held the last
    ld   (NM_LEN), a                   ; identifier looked up, which the report would show)
    ld   a, E_REDEF
    jp   CC_ERROR
.new:
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
    rst  $30                          ; LEX_NEXT
    cp   TK_EOL
    jr   nz, .text
    ret
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
    jr   nz, PP_E_NOTSUP
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
    jr   PP_LINE_END

; PP_NAME -- the next token: an identifier (TOK_BUF). Errors: E_SYNTAX. Destroys: AF, BC, DE, HL
PP_NAME:
    rst  $30                          ; LEX_NEXT
    cp   TK_IDENT
    ret  z
    ld   a, E_SYNTAX
    jp   CC_ERROR

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
