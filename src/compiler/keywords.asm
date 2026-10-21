; ============================================================================
; src/compiler/keywords.asm -- the C89 keyword table and its lookup (spec.md 4.1), EXROM
;
; EXROM-resident since Phase 8 (budget ledger L42; it was in the HOME lexer). The lexer reaches it
; through the HOME trampoline LEX_KEYWORD (src/compiler/lexer.asm), once per identifier; the shell's
; keyword highlighting (src/shell/highlight.asm) calls it directly. Bank rule 3: it reads only TOK_BUF,
; TOK_LEN and its own table, writes nothing and raises no error.
; ============================================================================

; ============================================================================
; XK_KEYWORD -- keyword or identifier (EXROM; HOME: the trampoline LEX_KEYWORD)
; In:  TOK_BUF / TOK_LEN = the identifier
; Out: A = TK_KW_FIRST + index for a C89 keyword, else TK_IDENT
; Destroys: AF, BC, DE, HL
; ============================================================================
XK_KEYWORD:
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
