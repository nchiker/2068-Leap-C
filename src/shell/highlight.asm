; ============================================================================
; src/shell/highlight.asm -- C keyword highlighting (spec.md 6.1; EXROM, budget component xkeywords)
;
; The keyword table is the compiler's own (LEX_KEYWORD and LEX_KW_TABLE in HOME,
; src/compiler/lexer.asm): HOME is mapped whatever the paging, and the lookup reads only TOK_BUF,
; TOK_LEN and its table, so the shell calls it with the EXROM paged in; no keyword list is
; duplicated here. A word is a run of letters, digits and '_'; one of at most 8 characters (the
; longest keyword) is copied to TOK_BUF and looked up. Keywords are case-sensitive, as C's.
; The characters of a keyword get bit 7 set (source text is ASCII 32-126); SH_DRAW_TEXT draws
; them bold. Never keywords: the text of string literals and character constants (with their
; escapes) and comments: `//` to the end of the line, `/* ... */` within the line. Each line is
; scanned on its own: a line that continues a comment begun on an earlier line is scanned as code.
; ============================================================================

; ============================================================================
; SH_KW_MARK -- mark the C keywords of a line (bit 7 of each of their characters)
; In:  HL = the NUL-terminated line (RAM)
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_KW_MARK:
    ld   a, (hl)
    or   a
    ret  z
    call SH_IDCHAR
    jr   c, .word
    inc  hl
    cp   '"'
    jr   z, .quoted
    cp   $27                           ; '
    jr   z, .quoted
    cp   '/'
    jr   nz, SH_KW_MARK
    ld   a, (hl)
    cp   '/'
    ret  z                             ; `//`: a comment to the end of the line
    cp   '*'
    jr   nz, SH_KW_MARK
    inc  hl
.comment:                              ; in `/* ... */`: up to its `*/`
    ld   a, (hl)
    or   a
    ret  z
    inc  hl
    cp   '*'
    jr   nz, .comment
    ld   a, (hl)
    cp   '/'
    jr   nz, .comment
    inc  hl
    jr   SH_KW_MARK
.quoted:                               ; A = the quote: up to the same quote; '\' escapes a character
    ld   c, a
.q1:
    ld   a, (hl)
    or   a
    ret  z
    inc  hl
    cp   c
    jr   z, SH_KW_MARK
    cp   $5C
    jr   nz, .q1
    ld   a, (hl)
    or   a
    ret  z
    inc  hl
    jr   .q1
.word:                                 ; HL -> its first character
    ld   d, h
    ld   e, l
    ld   b, 0
.w1:
    inc  b
    inc  hl
    ld   a, (hl)
    call SH_IDCHAR
    jr   c, .w1
    ld   a, b                          ; B = its length, DE -> it, HL -> the character after it
    cp   9
    jr   nc, SH_KW_MARK                ; longer than any keyword
    push hl
    push de
    ld   (TOK_LEN), a
    ex   de, hl
    ld   de, TOK_BUF
    ld   c, b
    ld   b, 0
    ldir
    call LEX_KEYWORD                   ; HOME: TK_IDENT, or a keyword's token
    pop  hl                            ; HL -> the word
    pop  de                            ; DE -> the character after it
    cp   TK_IDENT
    jr   z, .next
    ld   a, (TOK_LEN)
    ld   b, a
.mark:
    set  7, (hl)
    inc  hl
    djnz .mark
.next:
    ex   de, hl
    jr   SH_KW_MARK

; ============================================================================
; SH_IDCHAR -- C: A is a letter, a digit or '_' (a character of a C word)
; Destroys: F (A kept)
; ============================================================================
SH_IDCHAR:
    cp   '_'
    scf
    ret  z
    cp   '0'
    ccf
    ret  nc                            ; below '0'
    cp   '9' + 1
    ret  c                             ; a digit
    cp   'A'
    ccf
    ret  nc
    cp   'Z' + 1
    ret  c                             ; upper case
    cp   'a'
    ccf
    ret  nc
    cp   'z' + 1
    ret
