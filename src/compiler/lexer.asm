; ============================================================================
; src/compiler/lexer.asm -- the C lexer and source streaming (spec.md section 4.1; M1.1)
;
; Source streaming. The lexer reads the line store in place: records [len:2][text][CR] from
; PROG_AREA_START up to PROG_END. LEX_PTR walks the text of a record; at its CR, LEX_NEWLINE steps
; over the next record's length word (or, at PROG_END, onto LEX_EOF_BYTE, a $00 in ROM) and counts
; the line. The source region is always visible to the HOME compiler (chunk 6 paged out does not
; affect $7800-$BFFF), so no copy window is needed. Because the stream is the line store itself, a
; caller can save and restore LEX_PTR / LEX_LINE / LEX_BOLP to re-scan from a known point.
;
; Tokens (include/leapc_tokens.inc): LEX_NEXT scans one token and leaves its kind in A and TOK_KIND,
; the line it starts on in TOK_LINE, TF_* bits in TOK_FLAGS, and its value in TOK_VAL (numbers and
; character constants) or TOK_BUF/TOK_LEN (identifiers: first 31 characters; string literals:
; decoded bytes, no terminator). Blanks, CR line ends, /* */ (across lines) and // comments
; separate tokens. Adjacent string literals are separate TK_STR tokens; the parser concatenates.
;
; Integer constants: decimal, 0x hex, 0 octal, character constants; 0-65535. Type: int if the value
; is at most 32767 and there is no u/U suffix, otherwise unsigned int (TF_UNSIGNED). A decimal
; constant above 32767 is unsigned int here (C89 would make it long, which Leap-C does not have).
;
; Errors (include/leapc_errors.inc) go through CC_ERROR at TOK_LINE: the line of the token, or of
; the start of an unterminated comment.
; ============================================================================

; ============================================================================
; LEX_INIT -- open the source for LEX_NEXT
; In:  PROG_AREA_START / PROG_END (the line store)
; Out: LEX_PTR = first text byte (LEX_EOF_BYTE if the store is empty), LEX_LINE = 1,
;      LEX_BOLP = first token is at a line start, LEX_MODE = 0, PP_SP = PP_STACK
; Destroys: AF, DE, HL
; ============================================================================
LEX_INIT:
    ld   hl, PP_STACK                  ; no macro expansion open (preproc.asm)
    ld   (PP_SP), hl
    xor  a
    ld   (LEX_MODE), a
    inc  a
    ld   (LEX_BOLP), a
    ld   hl, 1
    ld   (LEX_LINE), hl
    ld   hl, PROG_AREA_START
    call LEX_SEEK
    ld   (LEX_PTR), hl
    ret

; ============================================================================
; LEX_SEEK -- enter the record at HL
; In:  HL -> a record's length word, or = PROG_END
; Out: NC: end of source (HL at or past PROG_END), HL = LEX_EOF_BYTE.
;      C: HL -> the record's first text byte
; Destroys: F, DE, HL
; ============================================================================
LEX_SEEK:
    ld   de, (PROG_END)
    or   a
    sbc  hl, de
    add  hl, de                       ; C: HL < PROG_END (the compare's borrow survives the add)
    jr   nc, .eof
    inc  hl
    inc  hl
    ret
.eof:
    ld   hl, LEX_EOF_BYTE
    ret

; ============================================================================
; LEX_NEWLINE -- step from a record's CR to the next record's text
; In:  HL -> the CR that ends a record
; Out: HL -> next text byte, LEX_LINE + 1, LEX_BOLP set; or HL = LEX_EOF_BYTE (line unchanged)
; Destroys: AF, DE, HL
; ============================================================================
LEX_NEWLINE:
    inc  hl
    call LEX_SEEK
    ret  nc
    ld   de, (LEX_LINE)
    inc  de
    ld   (LEX_LINE), de
    ld   a, 1 << TF_BOL
    ld   (LEX_BOLP), a
    ret

; ============================================================================
; LEX_NEXT -- scan the next token
; In:  LEX_PTR, LEX_LINE, LEX_BOLP, LEX_MODE
; Out: A = TOK_KIND; TOK_LINE, TOK_FLAGS; TOK_VAL or TOK_BUF/TOK_LEN; LEX_PTR past the token
; Errors: CC_ERROR (does not return) with E_BADCHAR, E_COMMENT, E_STRING, E_CHARCONST, E_ESCAPE,
;      E_NUMBER, E_RANGE, E_NOTSUP, E_TOOLONG
; Destroys: AF, BC, DE, HL
; ============================================================================
LEX_NEXT:
    ld   hl, (LEX_PTR)
.skip:
    ld   a, (hl)
    cp   ' '
    jr   z, .blank
    cp   LINE_TERMINATOR
    jr   z, .eol
    cp   '/'
    jr   nz, .token
    inc  hl
    ld   a, (hl)
    cp   '*'
    jr   z, .block
    cp   '/'
    jr   z, .line_comment
    dec  hl
    ld   a, '/'
    jr   .token
.blank:
    inc  hl
    jr   .skip
.line_comment:                        ; up to the CR, which .skip then handles
    inc  hl
    ld   a, (hl)
    cp   LINE_TERMINATOR
    jr   nz, .line_comment
    jr   .skip
.block:                               ; HL -> the '*' of "/*"
    call LEX_MARK_LINE                ; E_COMMENT is reported where the comment starts
.block_next:
    inc  hl
.block_chr:
    ld   a, (hl)
    cp   '*'
    jr   z, .block_star
    cp   LINE_TERMINATOR
    jr   z, .block_nl
    or   a
    jr   nz, .block_next
    ld   a, E_COMMENT                 ; end of source inside the comment
    jp   CC_ERROR
.block_nl:
    call LEX_NEWLINE
    jr   .block_chr
.block_star:
    inc  hl
    ld   a, (hl)
    cp   '/'
    jr   nz, .block_chr
    inc  hl
    jr   .skip
.eol:
    ld   a, (LEX_MODE)
    and  (1 << LM_EOL) | (1 << LM_MACRO)
    jp   nz, PP_EOL                    ; a directive's or a macro body's end (preproc.asm)
    call LEX_NEWLINE
    jr   .skip

.token:                               ; A = (HL) = first character of a token
    call LEX_BEGIN
    or   a
    jr   z, .eof
    cp   '"'
    jr   z, .string
    cp   $27                          ; '
    jp   z, .charconst
    cp   '_'
    jr   z, .ident
    call LEX_DIGIT
    jp   c, .punct
    cp   10
    jp   c, .number
                                      ; a letter: identifier or keyword
; ---- identifier / keyword ----
.ident:
    ld   de, TOK_BUF
    ld   b, IDENT_SIG_LEN             ; B = significant characters still to store
.id_loop:
    ld   a, (hl)
    cp   'a'
    jr   c, .id_other
    cp   'z' + 1
    jr   c, .id_chr                   ; a-z, the common case
.id_other:
    cp   '_'
    jr   z, .id_chr
    call LEX_DIGIT
    jr   c, .id_end
    ld   a, (hl)
.id_chr:
    inc  hl
    inc  b
    dec  b
    jr   z, .id_loop                  ; characters after the 31st are not significant
    ld   (de), a
    inc  de
    dec  b
    jr   .id_loop
.id_end:
    ld   a, IDENT_SIG_LEN
    sub  b
    ld   (TOK_LEN), a
    push hl
    call LEX_KEYWORD
    pop  hl
    jr   .done

.eof:                                 ; $00: only LEX_EOF_BYTE may hold it (carry is clear)
    ld   de, LEX_EOF_BYTE
    sbc  hl, de
    jp   nz, LEX_E_BADCHAR
    add  hl, de
    ld   a, TK_EOF
.done:
    ld   (LEX_PTR), hl
    ld   (TOK_KIND), a
    jp   PP_HOOK                       ; directives and macros (preproc.asm)

; ---- string literal ----
.string:
    inc  hl
    xor  a
    ld   (TOK_LEN), a
.str_loop:
    ld   a, (hl)
    cp   '"'
    jr   z, .str_end
    cp   ' '
    jp   c, LEX_E_STRING               ; the line ends inside the literal
    call LEX_CHAR                      ; E = the byte
    push hl
    ld   hl, TOK_LEN
    ld   a, (hl)
    cp   TOK_BUF_LEN
    jp   nc, LEX_E_TOOLONG
    inc  (hl)
    ld   hl, TOK_BUF
    add  a, l
    ld   l, a
    jr   nc, .str_put
    inc  h
.str_put:
    ld   (hl), e
    pop  hl
    jr   .str_loop
.str_end:
    inc  hl
    ld   a, TK_STR
    jr   .done

; ---- character constant ----
.charconst:
    inc  hl
    ld   a, (hl)
    cp   $27
    jr   z, .cc_bad                   ; ''
    cp   ' '
    jr   c, .cc_bad                   ; line end
    call LEX_CHAR
    ld   a, (hl)
    cp   $27
    jr   nz, .cc_bad                  ; unterminated, or more than one character
    inc  hl
    ld   d, 0
    ld   (TOK_VAL), de
    ld   a, (TOK_FLAGS)
    or   1 << TF_CHARCONST
    jr   .num_flags
.cc_bad:
    ld   a, E_CHARCONST
    jp   CC_ERROR

; ---- integer constant ----
.number:                              ; A = value of the first digit, HL -> it
    ld   c, 10
    or   a
    jr   nz, .num_acc                 ; 1-9: decimal
    inc  hl
    ld   a, (hl)
    or   $20
    cp   'x'
    ld   c, 8                         ; 0...: octal (the 0 is consumed; "0" alone is zero)
    jr   nz, .num_acc
    inc  hl
    ld   c, 16
.num_acc:
    ld   b, 255
    call LEX_ACCUM                    ; DE = value; Z: no digits; C: above 65535
    jp   c, LEX_E_RANGE
    jr   nz, .num_ok
    ld   a, c
    cp   16
    jr   z, .num_bad                  ; 0x without digits
.num_ok:
    ld   (TOK_VAL), de
    ld   a, (hl)
    cp   '.'
    jr   z, .num_float                ; 1.5: floating constant
    or   $20
    ld   b, 0                         ; B = flags from the suffix
    cp   'u'
    jr   nz, .num_l
    inc  hl
    ld   b, 1 << TF_UNSIGNED
    ld   a, (hl)
    or   $20
.num_l:
    cp   'l'
    jr   z, .num_float                ; long suffix: not supported
    cp   'e'
    jr   nz, .num_end
    ld   a, c
    cp   16
    jr   nz, .num_float               ; 1e5: floating constant
.num_end:
    ld   a, (hl)                      ; nothing alphanumeric may follow
    cp   '_'
    jr   z, .num_bad
    call LEX_DIGIT
    jr   nc, .num_bad
    ld   a, (TOK_VAL + 1)
    and  $80                          ; above 32767: unsigned int
    jr   z, .num_t
    ld   b, 1 << TF_UNSIGNED
.num_t:
    ld   a, (TOK_FLAGS)
    or   b
.num_flags:
    ld   (TOK_FLAGS), a
    ld   a, TK_NUM
    jp   .done
.num_bad:
    ld   a, E_NUMBER
    jp   CC_ERROR
.num_float:
    ld   a, E_NOTSUP
    jp   CC_ERROR

; ---- punctuators ----
.punct:
    ld   a, (hl)
    ex   de, hl                       ; DE = source
    ld   hl, LEX_PUNCT_CHARS
    ld   bc, LEX_PUNCT_N
    cpir
    ex   de, hl
    jp   nz, LEX_E_BADCHAR
    ld   a, LEX_PUNCT_N - 1
    sub  c                            ; A = index in LEX_PUNCT_CHARS
    cp   LEX_PUNCT_SIMPLE
    jr   c, .p_simple
    add  a, TK_ASSIGN - TK_LPAREN - LEX_PUNCT_SIMPLE
.p_simple:
    add  a, TK_LPAREN
    ld   c, a                         ; C = token
    ld   b, (hl)                      ; B = its character
    inc  hl
    ld   e, (hl)                      ; E = the next character
    cp   TK_DOT
    jr   z, .p_dot
    cp   TK_ASSIGN
    jr   c, .p_done                   ; ( ) [ ] { } , ; : ? ~ #
    ld   a, e
    cp   b
    jr   nz, .p_eq
    push hl                           ; doubled: << >> && || ++ --
    ld   hl, LEX_DOUBLE_TABLE
.p_dl:
    ld   a, (hl)
    inc  hl
    or   a
    jr   z, .p_dnone
    cp   b
    ld   a, (hl)
    inc  hl
    jr   nz, .p_dl
    pop  hl
    inc  hl
    ld   c, a
    cp   TK_SHR + 1
    jr   nc, .p_done                  ; && || ++ -- have no op= form
    ld   e, (hl)                      ; <<= >>=
    jr   .p_eq
.p_dnone:
    pop  hl
.p_eq:                                ; C = operator, E = next character
    ld   a, e
    cp   '='
    jr   nz, .p_arrow
    inc  hl
    ld   a, c
    add  a, TK_ASSIGN_OFS
    ld   c, a
    jr   .p_done
.p_arrow:
    ld   a, c
    cp   TK_MINUS
    jr   nz, .p_done
    ld   a, e
    cp   '>'
    jr   nz, .p_done
    inc  hl
    ld   c, TK_ARROW
.p_done:
    ld   a, c
    jp   .done
.p_dot:                               ; HL -> the character after '.'
    ld   a, e
    cp   '.'
    jr   nz, .p_dot_num
    inc  hl
    ld   a, (hl)
    dec  hl
    cp   '.'
    jr   nz, .p_done                  ; ".." is two dots
    inc  hl
    inc  hl
    ld   c, TK_ELLIPSIS
    jr   .p_done
.p_dot_num:
    sub  '0'
    cp   10
    jr   nc, .p_done
    ld   a, E_NOTSUP                  ; .5: floating constant
    jp   CC_ERROR

; ============================================================================
; LEX_BEGIN -- a token starts at HL: record its position, line and line-start flag
; LEX_MARK_LINE -- record the line only (a comment starts; the line-start state is kept)
; In:  HL -> the token's first byte (LEX_BEGIN); LEX_LINE, LEX_BOLP
; Out: TOK_LINE = LEX_LINE; LEX_BEGIN also: TOK_PTR = HL, TOK_FLAGS = TF_BOL or 0, LEX_BOLP = 0.
;      A, HL kept
; Destroys: DE (LEX_BEGIN: and F)
; ============================================================================
LEX_BEGIN:
    ld   (TOK_PTR), hl
    push af
    ld   a, (LEX_BOLP)
    ld   (TOK_FLAGS), a
    xor  a
    ld   (LEX_BOLP), a
    pop  af
LEX_MARK_LINE:
    ld   de, (LEX_LINE)
    ld   (TOK_LINE), de
    ret

; ============================================================================
; LEX_DIGIT -- value of an alphanumeric character as a digit
; In:  A = character
; Out: NC: A = 0-9 for '0'-'9', 10-35 for 'A'-'Z' / 'a'-'z'.  C: not alphanumeric
; Destroys: AF
; ============================================================================
LEX_DIGIT:
    cp   'a'
    jr   c, .upper
    sub  $20
.upper:
    sub  '0'
    ret  c
    cp   10
    ccf
    ret  nc                           ; 0-9
    sub  'A' - '0' - 10
    cp   10
    ret  c                            ; between '9' and 'A'
    cp   36
    ccf
    ret

; ============================================================================
; LEX_ACCUM -- read the digits of an integer
; In:  HL -> first character, C = base (8, 10 or 16), B = most digits to read (1-255)
; Out: NC: DE = value, HL -> first character not read, A = digits read (Z: none).
;      C: the value exceeds 65535 (DE, HL undefined)
; Destroys: AF, B, DE, HL (C kept)
; ============================================================================
LEX_ACCUM:
    ld   de, 0
    push bc
.loop:
    ld   a, (hl)
    call LEX_DIGIT
    jr   c, .end
    cp   c
    jr   nc, .end
    push hl
    push bc
    ld   hl, 0
    ld   b, c
.mul:
    add  hl, de                       ; HL = DE * base
    jr   c, .ovf
    djnz .mul
    ld   e, a
    ld   d, 0
    add  hl, de                       ; + digit
    jr   c, .ovf
    ex   de, hl
    pop  bc
    pop  hl
    inc  hl
    djnz .loop
.end:
    pop  af                           ; A = the limit
    sub  b                            ; A = digits read, NC
    ret
.ovf:
    pop  bc
    pop  hl
    pop  af
    scf
    ret

; ============================================================================
; LEX_CHAR -- one character of a string literal or character constant, escapes decoded
; In:  HL -> the character (not the closing quote, not a line end)
; Out: E = its value, HL -> after it
; Errors: E_ESCAPE (unknown escape, \x without digits, value above 255)
; Destroys: AF, BC, DE
; ============================================================================
LEX_CHAR:
    ld   a, (hl)
    inc  hl
    ld   e, a
    cp   $5C                          ; backslash
    ret  nz
    ld   e, (hl)                      ; E = the escape letter
    inc  hl
    push hl
    ld   hl, LEX_ESC_TABLE
.esc:
    ld   a, (hl)
    inc  hl
    or   a
    jr   z, .esc_num
    cp   e
    ld   a, (hl)
    inc  hl
    jr   nz, .esc
    pop  hl
    ld   e, a
    ret
.esc_num:
    pop  hl
    ld   a, e
    ld   bc, 255 * 256 + 16           ; \x: any number of hex digits
    cp   'x'
    jr   z, .esc_acc
    sub  '0'
    cp   8
    jr   nc, LEX_E_ESCAPE
    dec  hl                           ; \ooo: up to three octal digits
    ld   bc, 3 * 256 + 8
.esc_acc:
    call LEX_ACCUM
    jr   c, LEX_E_ESCAPE
    jr   z, LEX_E_ESCAPE
    ld   a, d
    or   a
    ret  z
LEX_E_ESCAPE:
    ld   a, E_ESCAPE
    jp   CC_ERROR

LEX_E_BADCHAR:
    ld   a, E_BADCHAR
    jp   CC_ERROR
LEX_E_STRING:
    ld   a, E_STRING
    jp   CC_ERROR
LEX_E_RANGE:
    ld   a, E_RANGE
    jp   CC_ERROR
LEX_E_TOOLONG:
    ld   a, E_TOOLONG
    jp   CC_ERROR

; ============================================================================
; LEX_KEYWORD -- keyword or identifier
; In:  TOK_BUF / TOK_LEN = the identifier
; Out: A = TK_KW_FIRST + index for a C89 keyword, else TK_IDENT
; Destroys: AF, BC, DE, HL
; ============================================================================
LEX_KEYWORD:
    ld   a, (TOK_BUF)
    sub  'a'
    cp   LEX_KW_LETTERS
    jr   nc, .ident                   ; keywords start with a-w
    ld   hl, LEX_KW_INDEX
    add  a, l
    ld   l, a
    jr   nc, .idx
    inc  h
.idx:
    ld   c, (hl)                      ; C = index of the letter's first keyword
    inc  hl
    ld   a, (hl)
    sub  c
    jr   z, .ident
    ld   b, a                         ; B = keywords with this letter
    ld   hl, LEX_KW_TABLE
    ld   a, c
    or   a
    jr   z, .try
    ld   d, c
.skip:
    call .next
    dec  d
    jr   nz, .skip
.try:                                 ; HL -> entry [n][characters 2..n+1], C = its index
    ld   a, (TOK_LEN)
    dec  a
    cp   (hl)
    jr   nz, .no
    push hl
    push bc
    ld   b, a
    ld   de, TOK_BUF + 1
.cmp:
    inc  hl
    ld   a, (de)
    cp   (hl)
    jr   nz, .differ
    inc  de
    djnz .cmp
    pop  bc
    pop  hl
    ld   a, c
    add  a, TK_KW_FIRST
    ret
.differ:
    pop  bc
    pop  hl
.no:
    call .next
    inc  c
    djnz .try
.ident:
    ld   a, TK_IDENT
    ret
.next:                                ; HL -> the entry after HL's
    ld   a, (hl)
    inc  a
    add  a, l
    ld   l, a
    ret  nc
    inc  h
    ret

; ============================================================================
; Tables
; ============================================================================
LEX_EOF_BYTE:
    DB   0                            ; LEX_PTR at end of source points here

; punctuator characters: the first LEX_PUNCT_SIMPLE give TK_LPAREN.., the rest TK_ASSIGN..
LEX_PUNCT_CHARS:
    DB   "()[]{},;:?~.#"
LEX_PUNCT_SIMPLE EQU $ - LEX_PUNCT_CHARS
    DB   "=!<>*/%+-&^|"
LEX_PUNCT_N EQU $ - LEX_PUNCT_CHARS
    ASSERT LEX_PUNCT_SIMPLE == TK_HASH - TK_LPAREN + 1
    ASSERT LEX_PUNCT_N - LEX_PUNCT_SIMPLE == TK_BAR - TK_ASSIGN + 1

; doubled punctuators: character, token; 0 ends the table
LEX_DOUBLE_TABLE:
    DB   '<', TK_SHL, '>', TK_SHR, '&', TK_ANDAND, '|', TK_OROR, '+', TK_INC, '-', TK_DEC, 0

; escape sequences other than octal and \x: letter, value; 0 ends the table
LEX_ESC_TABLE:
    DB   'n', 10, 't', 9, 'r', 13, $5C, $5C, $27, $27, '"', '"', '?', '?'
    DB   'a', 7, 'b', 8, 'f', 12, 'v', 11, 0

; keywords: index of the first keyword starting with each letter a..w, then the count (for x)
LEX_KW_LETTERS EQU 23
LEX_KW_INDEX:
    ;    a  b  c  d  e  f   g   h   i   j   k   l   m   n   o   p   q   r   s   t   u   v   w   x
    DB   0, 1, 2, 6, 9, 12, 14, 15, 15, 17, 17, 17, 18, 18, 18, 18, 18, 18, 20, 26, 27, 29, 31, 32
; keyword entries in TK_* order: [length - 1][characters after the first]
    MACRO LEX_KW name
    DB   .len - 1
    DB   name + 1?
    ENDM
LEX_KW_TABLE:
    DB 3,"uto", 4,"reak", 3,"ase", 3,"har", 4,"onst", 7,"ontinue", 6,"efault", 1,"o"
    DB 5,"ouble", 3,"lse", 3,"num", 5,"xtern", 4,"loat", 2,"or", 3,"oto", 1,"f"
    DB 2,"nt", 3,"ong", 7,"egister", 5,"eturn", 4,"hort", 5,"igned", 5,"izeof", 5,"tatic"
    DB 5,"truct", 5,"witch", 6,"ypedef", 4,"nion", 7,"nsigned", 3,"oid", 7,"olatile", 4,"hile"
LEX_KW_TABLE_END:
