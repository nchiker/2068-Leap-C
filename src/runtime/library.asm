; ============================================================================
; src/runtime/library.asm -- the built-in library, leap.h (spec.md 7; Phase 3)
;
; Library functions follow the C calling convention (spec.md 5.2): arguments on the stack, the
; first lowest, removed by the caller; the result in HL; IX and IY kept; AF, BC, DE, HL destroyed.
; Most start with `call LIB_ARGS`, which loads the first three arguments and records the call's
; address in the program (LIB_CALLER) for runtime-error and BREAK reports.
;
; The library is built on the retained platform: text through GFX_PRINT_STRING_ATTR (wrapping and
; scrolling), pixels and lines through GFX_PLOT_CLIPPED and GFX_LINE, sprites, the keyboard latch
; (IO_READ_KEY), the AY beep (AY_BEEP_PERIOD in HOME, AY_BEEP_PLAY in the EXROM through a
; trampoline), MEM_FILL / MEM_SHIFT_* for memset / memmove, and the helper core's divide for the
; number texts. The compiler's binding of the names (LIB_BIND) is in src/runtime/libbind.asm.
;
; Screen coordinates: rows 0-23 and columns 0-31 for text and cells; pixels x 0-255, y 0-191 from
; the top (the platform's convention).
; ============================================================================

; ============================================================================
; LIB_ARGS -- the arguments of the library function that calls it first thing
; In:  under LIB_ARGS's return address: the library function's return address into the program,
;      then the arguments, the first lowest
; Out: HL = the first argument, DE = the second, BC = the third (whatever words follow, for fewer
;      arguments); LIB_CALLER = the program's address of the call (runtime errors, BREAK)
; Destroys: AF
; ============================================================================
LIB_ARGS:
    ld   hl, 2
    add  hl, sp
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   (LIB_CALLER), de
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    push de
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    pop  hl
    ret

; ---------------------------------------------------------------- text
; void cls(void) -- the screen cleared to the current colours; the print position (0, 0)
LIB_CLS:
    call GFX_CLS
    ld   a, (LIB_ATTR)
    call GFX_PAINT_ATTR                ; (BC = 0: its LDIR's count)
    ld   (LIB_COL), bc
    ret

; void print(const char *s) -- s (no new line)
LIB_PRINT:
    call LIB_ARGS
; LIB_PUTS0 -- print the string at HL (LIB_PUTC). Destroys: AF, BC, DE, HL
LIB_PUTS0:
    ld   a, (hl)
    or   a
    ret  z
    push hl
    call LIB_PUTC
    pop  hl
    inc  hl
    jr   LIB_PUTS0

; ============================================================================
; LIB_PUTC -- character A at the print position, in the print attribute and over mode (LIB_OVATTR);
; 10 ('\n') moves to the start of the next line. Printing continues on the next line after column
; 31, and the screen scrolls up below row 23 (GFX_PRINT_STRING_ATTR, GFX_SCROLL_OUTPUT_UP).
; Characters without a glyph show as spaces
; Destroys: AF, BC, DE, HL
; ============================================================================
LIB_PUTC:
    cp   10
    jr   z, LIB_NEWLINE
    ld   (LIB_CHBUF), a                ; (LIB_CHBUF + 1 stays 0: a one-character string)
    call LIB_OVATTR
    ld   d, b
    ld   bc, (LIB_COL)                 ; B = row, C = column
    ld   hl, LIB_CHBUF
    call GFX_PRINT_STRING_ATTR         ; B, C = the position after it
    ld   (LIB_COL), bc
    ret
LIB_NEWLINE:
    ld   bc, (LIB_COL)
    ld   c, 0
    inc  b
    ld   a, b
    cp   24
    jr   c, .row
    dec  b
    push bc
    call GFX_SCROLL_OUTPUT_UP
    pop  bc
.row:
    ld   (LIB_COL), bc
    ret

; LIB_BACK -- the print position one character back (from column 0: the end of the row above; not
; above row 0). Destroys: F, HL
LIB_BACK:
    ld   hl, LIB_COL
    dec  (hl)
    ret  p
    ld   (hl), 31
    inc  hl
    dec  (hl)
    ret  p
    inc  (hl)
    ret

; ============================================================================
; LIB_OVATTR -- A = the print attribute: LIB_ATTR, with ink and paper swapped while inverse is on
; (the platform's swap, GFX_ATTR_SWAP after its cell lookup); B = the over flag
; Destroys: F, C, HL
; ============================================================================
LIB_OVATTR:
    ld   hl, LIB_ATTR
    ld   a, (LIB_INVF)
    or   a
    ld   a, (hl)
    call nz, GFX_ATTR_SWAP_HL
    ld   hl, LIB_OVERF
    ld   b, (hl)
    ret
GFX_ATTR_SWAP_HL EQU GFX_ATTR_SWAP + 4  ; past `call GFX_CELL_ATTR_ADDR / ret c`: A = (HL) swapped

; void ink(int n), paper(int n), bright(int n), flash(int n) -- that field of the attribute:
; ink and paper n & 7, bright and flash n & 1
LIB_INK:
    ld   a, $07
    DB   $01                           ; (`ld bc,nn` swallows the next `ld a,n`)
LIB_PAPER:
    ld   a, $38
    DB   $01
LIB_BRIGHT:
    ld   a, $40
    DB   $01
LIB_FLASH:
    ld   a, $80
    ex   af, af'                       ; (the selector in A': LIB_ARGS keeps it)
    call LIB_ARGS
    ex   af, af'
    ld   b, a                          ; B = the field's bits
    ld   a, l
    ld   c, b
.align:                                ; n moved up to the field
    srl  c
    jr   c, .put
    rlca
    jr   .align
.put:
    ld   hl, LIB_ATTR
    xor  (hl)
    and  b
    xor  (hl)
    ld   (hl), a
    ret

; void inverse(int n), over(int n) -- on (n & 1 = 1) or off
LIB_OVER:
    ld   a, LIB_OVERF - LIB_INVF
    DB   $FE                           ; (`cp n` swallows the next `xor a`)
LIB_INVERSE:
    xor  a
    ex   af, af'
    call LIB_ARGS
    ex   af, af'
    ld   c, a
    ld   b, 0
    ld   a, l
    and  1
    ld   hl, LIB_INVF
    add  hl, bc
    ld   (hl), a
    ret

; void at(int row, int col) -- the print position: row 0-23 (beyond: 23), column col & 31
LIB_AT:
    call LIB_ARGS
    ld   a, l
    cp   24
    jr   c, .row
    ld   a, 23
.row:
    ld   (LIB_ROW), a
    ld   l, e
    jr   LIB_TABL
; void tab(int col) -- the print position's column: col & 31
LIB_TAB:
    call LIB_ARGS
LIB_TABL:
    ld   a, l
    and  31
    ld   (LIB_COL), a
    ret

; void border(int n) -- the border colour n & 7
LIB_BORDER:
    call LIB_ARGS
    ld   a, l
    jp   GFX_SET_BORDER

; ============================================================================
; int printf(const char *fmt, ...) -- fmt's characters (LIB_PUTC), each conversion replaced by the
; next argument: %d (int), %u (unsigned), %x (unsigned, lowercase hexadecimal), %c (a character),
; %s (a string), %f (a float, Phase 8: 6 decimals, or .N of them, N 0-9: more count as 9), %% (a
; '%'). A width (decimal digits after the %) right-aligns the text with spaces; flags (- 0 + space
; #) are not supported. Another conversion character prints the next argument as a character
; Out: HL undefined (deviation from C89, which returns the number of characters: spec.md 7)
; ============================================================================
LIB_PRINTF:
    call LIB_ARGS                      ; HL = fmt
    ld   (LIB_FMT), hl
    ld   hl, 4
    add  hl, sp
    ld   (LIB_AP), hl                  ; -> the first value
    jr   .next
.text:                                 ; HL = a conversion's text; [width]
    pop  bc
    push hl
    push bc
    call LIB_STRLEN0                   ; HL = its length
    pop  bc
    ld   a, h
    or   a
    jr   nz, .str
    ld   a, b
    sub  l
    jr   c, .str
    ld   b, a
    inc  b
.pad:                                  ; width - length spaces first
    dec  b
    jr   z, .str
    push bc
    ld   a, ' '
    call LIB_PUTC
    pop  bc
    jr   .pad
.str:
    pop  hl
    call LIB_PUTS0
.next:
    ld   hl, (LIB_FMT)
    ld   a, (hl)
    inc  hl
    or   a
    ret  z
    cp   '%'
    jr   z, .conv
.put:
    ld   (LIB_FMT), hl
    call LIB_PUTC
    jr   .next
.conv:
    call .num
    ld   b, a                          ; B = the width
    ld   c, 6                          ; C = the precision (%f)
    ld   a, (hl)
    cp   '.'
    jr   nz, .spec
    inc  hl
    call .num
    ld   c, a
    ld   a, (hl)
.spec:                                 ; A = the conversion character
    inc  hl
    cp   '%'
    jr   z, .put
    ld   (LIB_FMT), hl
    push bc                            ; [width]
    ld   hl, (LIB_AP)
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   (LIB_AP), hl
    ex   de, hl                        ; HL = the value
    cp   'f'
    jr   z, .float
    ld   de, LIB_NUM
    ld   c, 10
    cp   'd'
    jr   z, .signed
    cp   'u'
    jr   z, .unsigned
    cp   's'
    jr   z, .text
    ld   c, 16
    cp   'x'
    jr   z, .unsigned
    ex   de, hl                        ; a character: the text LIB_NUM = [c][0]
    ld   (hl), e
    inc  hl
    ld   (hl), 0
    dec  hl
    jr   .text
.signed:
    call LIB_ITOAS
    jp   .text
.unsigned:
    call LIB_UTOA
    jp   .text
.float:                                ; a float's 3-word slot (Phase 8): its text from the float core
    ld   hl, (LIB_AP)
    dec  hl
    dec  hl
    push hl
    ld   de, 6
    add  hl, de
    ld   (LIB_AP), hl
    pop  hl
    ld   a, c
    cp   10
    jr   c, .prec
    ld   c, 9
.prec:
    ld   a, FOP_FTOA
    call F_X                           ; HL = the text (PRINT_BUF)
    jp   .text
.num:                                  ; A = the decimal number at HL (0: none), HL past it. Destroys: F, DE
    ld   d, 0
.nd:
    ld   a, (hl)
    sub  '0'
    cp   10
    jr   nc, .ne
    inc  hl
    ld   e, a
    ld   a, d
    add  a, a
    add  a, a
    add  a, d
    add  a, a
    add  a, e
    ld   d, a
    jr   .nd
.ne:
    ld   a, d
    ret

; ============================================================================
; LIB_ITOAS -- the text of HL in base C at DE; in base 10 signed ('-' and the magnitude)
; LIB_UTOA -- the same, unsigned
; In:  HL = the value, C = the base (2-36), DE = where the text goes
; Out: HL = the text: digits (from 10: lowercase letters), then a NUL
; Destroys: AF, BC, DE
; ============================================================================
LIB_ITOAS:
    ld   a, c
    cp   10
    jr   nz, LIB_UTOA
    bit  7, h
    jr   z, LIB_UTOA
    ld   a, '-'
    ld   (de), a
    inc  de
    call MATH_NEGATE16
    call LIB_UTOA
    dec  hl                            ; the text starts at the '-'
    ret
LIB_UTOA:
    ld   (LIB_PTR), de
    ld   b, 0
    xor  a
    push af                            ; the end mark (0)
.div:
    call RT_UDIV                       ; HL = HL / BC, E = the digit (BC kept)
    ld   a, e
    add  a, '0'
    cp   '9' + 1
    jr   c, .dig
    add  a, 'a' - '9' - 1
.dig:
    push af
    ld   a, h
    or   l
    jr   nz, .div
    ld   hl, (LIB_PTR)
    ld   d, h
    ld   e, l
.put:                                  ; the digits, the most significant first, then the NUL
    pop  af
    ld   (de), a
    inc  de
    or   a
    jr   nz, .put
    ret

; char *itoa(int n, char *buf, int base) -- the text of n in base 2-36 at buf (lowercase letters;
; negative only in base 10); returns buf. Another base: runtime error 4
LIB_ITOA:
    call LIB_ARGS                      ; HL = n, DE = buf, BC = base
    ld   a, c
    sub  2
    cp   35
    sbc  a, a
    inc  a
    or   b
    jp   nz, RT_ERR_ARG
    jr   LIB_ITOAS

; int atoi(const char *s) -- the decimal number at the start of s: leading spaces and control
; characters skipped, an optional sign, the digits (wrapping around beyond 16 bits)
LIB_ATOI:
    call LIB_ARGS
.space:
    ld   a, (hl)
    inc  hl
    dec  a
    cp   ' '
    jr   c, .space                     ; 1-32
    inc  a                             ; A = the first other character, HL past it
    ld   c, a
    cp   '-'
    jr   z, .sign
    cp   '+'
    jr   z, .sign
    dec  hl
.sign:
    ex   de, hl                        ; DE -> the digits
    ld   hl, 0
.dig:
    ld   a, (de)
    sub  '0'
    cp   10
    jr   nc, .end
    inc  de
    push de
    ld   d, h
    ld   e, l
    add  hl, hl
    add  hl, hl
    add  hl, de
    add  hl, hl                        ; HL * 10
    ld   e, a
    ld   d, 0
    add  hl, de
    pop  de
    jr   .dig
.end:
    ld   a, c
    cp   '-'
    ret  nz
    jp   MATH_NEGATE16

; int abs(int n)
LIB_ABS:
    call LIB_ARGS
    jp   MATH_ABS16

; ---------------------------------------------------------------- strings and memory
; unsigned strlen(const char *s)
LIB_STRLEN:
    call LIB_ARGS
; LIB_STRLEN0 -- HL = the length of the string at HL. Destroys: AF, BC
LIB_STRLEN0:
    xor  a
    ld   b, a
    ld   c, a
    cpir                               ; BC = -(length + 1)
    ld   h, b
    ld   l, c
    jp   RT_CPL

; char *strcpy(char *d, const char *s) -- returns d
LIB_STRCPY:
    call LIB_ARGS
    push hl
    ex   de, hl
LIB_STRCPY0:                           ; HL -> the source, DE -> the destination; [d]
    ld   a, (hl)
    ld   (de), a
    inc  hl
    inc  de
    or   a
    jr   nz, LIB_STRCPY0
LIB_RETD:                              ; return the first argument: [d]
    pop  hl
    ret

; char *strcat(char *d, const char *s) -- s appended to d; returns d
LIB_STRCAT:
    call LIB_ARGS
    push hl
    xor  a
    ld   b, a
    ld   c, a
    cpir
    dec  hl                            ; -> d's NUL
    ex   de, hl
    jr   LIB_STRCPY0

; char *strncpy(char *d, const char *s, unsigned n) -- n characters of s to d, padded with NULs;
; returns d
LIB_STRNCPY:
    call LIB_ARGS
    push hl
    ex   de, hl
.copy:
    ld   a, b
    or   c
    jr   z, LIB_RETD
    ld   a, (hl)
    ld   (de), a
    inc  de
    dec  bc
    or   a
    jr   z, .copy                      ; at s's NUL: the rest are NULs too
    inc  hl
    jr   .copy

; void *memset(void *p, int c, unsigned n) -- returns p
LIB_MEMSET:
    call LIB_ARGS
    push hl
    ld   a, b
    or   c
    jr   z, LIB_RETD
    ld   a, e
    call MEM_FILL
    jr   LIB_RETD

; void *memcpy(void *d, const void *s, unsigned n), void *memmove(...) -- n bytes from s to d
; (overlapping blocks too: MEM_SHIFT_UP / MEM_SHIFT_DOWN); return d
LIB_MEMCPY:
LIB_MEMMOVE:
    call LIB_ARGS
    push hl
    or   a
    sbc  hl, de                        ; d - s
    ex   de, hl                        ; HL = s, DE = d - s
    jr   c, .down
    call MEM_SHIFT_UP
    jr   LIB_RETD
.down:
    call NEG_DE                        ; DE = s - d
    call MEM_SHIFT_DOWN
    jr   LIB_RETD

; char *strchr(const char *s, int c) -- the first c in s (c may be the NUL), or NULL
LIB_STRCHR:
    call LIB_ARGS
.find:
    ld   a, (hl)
    cp   e
    ret  z
    inc  hl
    or   a
    jr   nz, .find
LIB_NULL:
    ld   h, a
    ld   l, a
    ret

; int strcmp(const char *a, const char *b) -- < 0, 0, > 0 as a is below, equal to or above b
; (the characters compared unsigned)
LIB_STRCMP:
    call LIB_ARGS
.cmp:
    ld   a, (de)
    cp   (hl)
    jr   nz, LIB_CMPNE
    or   a
    jr   z, LIB_RETA                   ; (A = 0)
    inc  hl
    inc  de
    jr   .cmp
LIB_CMPNE:                             ; C: a's character is the larger
    ld   hl, 1
    ret  c
    dec  hl
    dec  hl
    ret

; int memcmp(const void *a, const void *b, unsigned n) -- as strcmp, for n bytes
LIB_MEMCMP:
    call LIB_ARGS
.cmp:
    ld   a, b
    or   c
    jr   z, LIB_RETA
    ld   a, (de)
    cp   (hl)
    jr   nz, LIB_CMPNE
    inc  hl
    inc  de
    dec  bc
    jr   .cmp

; int putchar(int c) -- prints c (LIB_PUTC); returns c
LIB_PUTCHAR:
    call LIB_ARGS
    ld   a, l
LIB_PUTCA:                             ; print A; HL = A
    push af
    call LIB_PUTC
    pop  af
LIB_RETA:                              ; HL = A (zero-extended)
    ld   l, a
    ld   h, 0
    ret

; int puts(const char *s) -- s, then a new line; returns 10 (non-negative)
LIB_PUTS:
    call LIB_ARGS
    call LIB_PUTS0
    ld   a, 10
    jr   LIB_PUTCA

; ---------------------------------------------------------------- keyboard
; int getkey(void) -- waits for a key and returns its code: ASCII, or the editor's control codes
; (1-4 cursor keys, 8 DELETE, 13 ENTER)
LIB_GETKEY:
    call LIB_ARGS                      ; (LIB_CALLER: a BREAK while waiting)
    call IO_READ_KEY
    jr   LIB_RETA
; int inkey(void) -- the key pressed since the last getkey(), inkey() or gets(); 0 if none
LIB_INKEY:
    call IO_READ_KEY_NONBLOCK
    jr   LIB_RETA

; int inp(int port) -- the byte read from the port (16-bit address)
LIB_INP:
    call LIB_ARGS
    ld   b, h
    ld   c, l
    in   a, (c)
    jr   LIB_RETA

; int point(int x, int y) -- 1 if the pixel at (x, y) is set, else 0 (also off the screen)
LIB_POINT:
    call LIB_ARGS
    ld   a, h
    or   d
    jr   nz, LIB_RET0
    ld   a, e
    cp   192
    jr   nc, LIB_RET0
    ld   b, l
    ld   c, e
    call GFX_READ_PIXEL
    jr   LIB_RETA
LIB_RET0:
    xor  a
    jr   LIB_RETA

; int attr(int row, int col) -- the attribute of the cell (row 0-23, column 0-31); 0 outside
LIB_ATTRF:
    call LIB_ARGS
    ld   a, h
    or   d
    jr   nz, LIB_RET0
    ld   b, l
    ld   c, e
    call GFX_CELL_ATTR_ADDR            ; C: outside
    jr   c, LIB_RET0
    ld   a, (hl)
    jr   LIB_RETA

; ============================================================================
; char *gets(char *buf, int max) -- a line typed at the keyboard: printable characters (at most
; max - 1) are stored and echoed at the print position, DELETE removes the last one, ENTER ends
; the line with a new line; buf then holds the characters and a NUL. Returns buf. max < 1 counts
; as 1
; ============================================================================
LIB_GETS:
    call LIB_ARGS                      ; HL = buf, DE = max
    push hl                            ; [buf]
    dec  de                            ; DE = room left
    bit  7, d
    jr   z, .key
    ld   de, 0
.key:
    ld   (hl), 0
    call IO_READ_KEY
    cp   KEY_ENTER
    jr   z, .enter
    cp   KEY_DELETE
    jr   z, .del
    cp   ' '
    jr   c, .key
    cp   127
    jr   nc, .key
    ld   b, a
    ld   a, d
    or   e
    jr   z, .key                       ; full
    ld   (hl), b
    inc  hl
    dec  de
    push hl
    push de
    ld   a, b
    call LIB_PUTC
    jr   .shown
.del:
    pop  bc                            ; BC = buf
    push bc
    or   a
    sbc  hl, bc
    add  hl, bc
    jr   z, .key                       ; nothing to delete
    dec  hl
    inc  de
    push hl
    push de
    call LIB_BACK
    ld   a, ' '
    call LIB_PUTC
    call LIB_BACK
.shown:
    pop  de
    pop  hl
    jr   .key
.enter:
    call LIB_NEWLINE
    pop  hl
    ret

; ---------------------------------------------------------------- graphics
; void plot(int x, int y) -- the pixel at (x, y) in the print attribute and over mode (its cell
; takes the attribute); off the screen: nothing
LIB_PLOT:
    call LIB_ARGS
    push de
    push hl
    call LIB_OVATTR                    ; A = the attribute, B = over
    pop  hl
    pop  de
    jp   GFX_PLOT_CLIPPED

; void draw(int x0, int y0, int x1, int y1) -- a line from (x0, y0) to (x1, y1) in the print
; attribute and over mode; coordinates off the screen are moved to its edge (x 0-255, y 0-191)
LIB_DRAW:
    call LIB_ARGS
    ld   hl, 2
    add  hl, sp                        ; -> x0
    ld   de, GFX_LINE_X0
.arg:                                  ; GFX_LINE_X0, Y0, X1, Y1 = the arguments, clamped
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    inc  hl
    push hl
    ld   h, b
    ld   l, c
    call LIB_CLAMPX
    bit  0, e                          ; Y0, Y1: the odd addresses
    call nz, LIB_CLAMPY
    ld   (de), a
    pop  hl
    inc  e
    ld   a, e
    cp   (GFX_LINE_Y1 + 1) & $FF
    jr   nz, .arg
    call LIB_OVATTR
    ld   (GFX_LINE_ATTR), a
    ld   a, b
    ld   (GFX_LINE_OVER), a
    jp   GFX_LINE
    ASSERT (GFX_LINE_X0 & $FF) % 2 == 0 && GFX_LINE_Y0 == GFX_LINE_X0 + 1
    ASSERT GFX_LINE_X1 == GFX_LINE_X0 + 2 && GFX_LINE_Y1 == GFX_LINE_X0 + 3
    ASSERT (GFX_LINE_X0 >> 8) == (GFX_LINE_Y1 >> 8)
; LIB_CLAMPX -- A = HL limited to 0-255. LIB_CLAMPY -- A limited to 0-191. Destroys: F
LIB_CLAMPX:
    ld   a, h
    or   a
    ld   a, l
    ret  z
    ld   a, h
    rla
    ld   a, 0
    ret  c
    dec  a
    ret
LIB_CLAMPY:
    cp   192
    ret  c
    ld   a, 191
    ret

; void mode(int n) -- the display mode: 0 normal, 1 hi-res colour (the second display file at
; $6000-$77FF holds an attribute for every 8 pixels). n = 1 while the program's image uses
; $6000-$77FF (image region 4, spec.md 3.2): runtime error 3. Another n: runtime error 4
LIB_MODE:
    call LIB_ARGS
    ld   a, l
    and  $FE
    or   h
    jp   nz, RT_ERR_ARG
    or   l
    jp   z, GFX_SET_MODE               ; (A = 0)
    ld   hl, (IMG_LIM + 4 * 3 + 2)     ; region 4 [low][high] (the compiler's limits): unused while
    ld   de, (IMG_LIM + 4 * 3)         ; it is [LEAPC_IMG4_BASE][LEAPC_IMG4_END], or reserved by
    sbc  hl, de                        ; #pragma hires: [LEAPC_IMG4_END][LEAPC_IMG4_END] (NC)
    ld   a, d
    jr   z, .full                      ; [X][X]: reserved when X is the region's end
    ld   de, LEAPC_IMG4_BASE - LEAPC_IMG4_END
    add  hl, de
    ld   a, h
    or   l
    DB   $01                           ; (`ld bc,nn` swallows the `cp`)
.full:
    cp   LEAPC_IMG4_END >> 8
    ld   a, RTE_HIRES
    jp   nz, RT_LIBERR
    ld   a, 1
    jp   GFX_SET_MODE

; void sprite_get(int row, int col, int w, int h, void *buf) -- the screen's w x h cells from (row,
; col) into buf (9 bytes a cell: 8 pixel rows and the attribute)
; void sprite_put(int row, int col, int w, int h, void *buf) -- buf back onto the screen at (row,
; col). A rectangle not wholly on the screen, or empty: runtime error 4
LIB_SPGET:
    xor  a
    DB   $01                           ; (`ld bc,nn` swallows the next `ld a,n`)
LIB_SPPUT:
    ld   a, 1
    ex   af, af'
    call LIB_ARGS                      ; HL = row, DE = col, BC = w
    ld   d, c                          ; D = w
    ld   b, l                          ; B = row
    ld   c, e                          ; C = col
    ld   hl, 8
    add  hl, sp                        ; -> h ([return][row][col][w][h][buf])
    ld   e, (hl)                       ; E = h
    inc  hl
    inc  hl
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a                          ; HL = buf
    ex   af, af'
    or   a
    jr   z, .get
    call GFX_SPRITE_DRAW
    jr   .done
.get:
    call GFX_SPRITE_CAPTURE
.done:
    ret  nc
    jp   RT_ERR_ARG

; ---------------------------------------------------------------- sound
; void beep(int frames, int semitone) -- a note on the AY's channel A for frames display frames
; (unsigned), semitone above middle C (-60 to 69: runtime error 4 beyond). BREAK ends it
; The EXROM's AY_BEEP_PLAY through a trampoline (bank rule 2) that defers BREAK (NOBRK): its wait
; ends early on BREAK and the trampoline's end then stops the program
LIB_BEEP:
    call LIB_ARGS                      ; HL = frames, DE = semitone
    ex   de, hl
    call AY_BEEP_PERIOD                ; HL = the tone period (DE kept); semitone: RT_ERR_ARG
    push hl
    ld   hl, NOBRK
    inc  (hl)
    call BANK_PAGE_EXROM_IN
    pop  hl
    call LEAPC_EXROM_BEEP
    call BANK_PAGE_EXROM_OUT
    jp   RT_NOBRK_END

; void sound(int reg, int value) -- AY register reg (0-15; beyond: runtime error 4) = value & 255
LIB_SOUND:
    call LIB_ARGS
    ld   a, l
    and  $F0
    or   h
    jp   nz, RT_ERR_ARG
    ld   a, l
    out  (PORT_AY_REG), a
    ld   a, e
    out  (PORT_AY_DATA), a
    ret

; ---------------------------------------------------------------- time, random, ports
; unsigned frames(void) -- the display frame counter (FRAMES)
LIB_FRAMES:
    ld   hl, (FRAMES)
    ret

; void pause(unsigned n) -- waits n display frames (BREAK ends the program)
LIB_PAUSE:
    call LIB_ARGS
    ex   de, hl
    ld   a, d
    or   e
    ret  z
    jp   AY_WAIT_FRAMES

; void outp(int port, int value) -- value & 255 written to the port
LIB_OUTP:
    call LIB_ARGS
    ld   b, h
    ld   c, l
    out  (c), e
    ret

; ============================================================================
; void srand(unsigned seed) -- restart the sequence of rand(). Seeds 0 and 1 give the same sequence
; (the generator's state may not be 0)
; int rand(void) -- the next number of the sequence, 0 .. 32767 (RAND_MAX). Without srand(), a
; program gets the sequence of srand(1) (RT_RUN clears the state)
; The generator: a 16-bit xorshift (shifts 7, 9, 8), period 65535; the result is the state without
; its top bit
; Destroys: AF, BC (srand), AF (rand)
; ============================================================================
LIB_SRAND:
    pop  bc
    pop  hl
    push hl
    push bc
    ld   (LIB_RND), hl
    ret
LIB_RAND:
    ld   hl, (LIB_RND)
    ld   a, h
    or   l
    jr   nz, .step
    inc  l                             ; state 0: seed 1
.step:                                 ; HL ^= HL << 7; HL ^= HL >> 9; HL ^= HL << 8
    ld   a, h
    rra
    ld   a, l
    rra
    xor  h
    ld   h, a
    ld   a, l
    rra
    ld   a, h
    rra
    xor  l
    ld   l, a
    xor  h
    ld   h, a
    ld   (LIB_RND), hl
    res  7, h
    ret

; ---------------------------------------------------------------- heap and program
; ============================================================================
; void *malloc(unsigned n) -- a block of n bytes from the heap, or NULL if no free block is large
; enough. First fit; free blocks next to each other are joined as the search passes them
; The heap (RT_RUN): blocks [size:2][data], from PROG_END (made even) to the end mark at
; LIB_HEAP_END, a used block of size 0. A size counts its header and is even; bit 15 is set while
; the block is in use
; ============================================================================
LIB_MALLOC:
    call LIB_ARGS                      ; HL = n
    ld   bc, 3
    add  hl, bc
    jr   c, .none                      ; (n > $FFFC)
    bit  7, h
    jr   nz, .none                     ; 32 KB or more: never
    res  0, l
    ld   b, h
    ld   c, l                          ; BC = the size needed: n + 2, even
    ld   hl, (PROG_END)
    inc  hl
    res  0, l                          ; the first block
.block:
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    dec  hl                            ; DE = its header
    bit  7, d
    jr   nz, .used
.join:                                 ; free: join the free blocks after it
    push hl
    add  hl, de                        ; -> the next block
    ld   a, (hl)
    inc  hl
    bit  7, (hl)
    jr   nz, .joined                   ; in use (the end mark is)
    add  a, e
    ld   e, a
    ld   a, (hl)
    adc  a, d
    ld   d, a                          ; DE = both sizes
    pop  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    dec  hl
    jr   .join
.joined:
    pop  hl
    push hl
    ex   de, hl                        ; HL = the free size, DE -> the block
    or   a
    sbc  hl, bc                        ; HL = the rest
    jr   c, .small
    ex   de, hl
    jr   z, .mark                      ; exactly: the whole block
    push hl
    add  hl, bc                        ; -> the rest: a free block
    ld   (hl), e
    inc  hl
    ld   (hl), d
    pop  hl
.mark:                                 ; HL -> the block, BC = its size: in use
    set  7, b
    ld   (hl), c
    inc  hl
    ld   (hl), b
    inc  hl                            ; -> the data
    pop  de
    ret
.small:
    add  hl, bc                        ; (the free size again)
    ex   de, hl
    pop  hl
.used:
    res  7, d
    ld   a, d
    or   e
    jr   z, .none                      ; the end mark
    add  hl, de
    jr   .block
.none:
    xor  a
    jp   LIB_NULL

; void free(void *p) -- p's block (from malloc) is free again; NULL: nothing
LIB_FREE:
    call LIB_ARGS
    ld   a, h
    or   l
    ret  z
    dec  hl
    res  7, (hl)
    ret

; void exit(int status) -- the program ends with this status (as if main returned it)
LIB_EXIT:
    call LIB_ARGS
    xor  a
    jp   RT_ERROR

; ---------------------------------------------------------------- tape (Phase 7; spec.md 7, 8.3)
; void tape_save(const char *name, const void *addr, unsigned len) -- len bytes from addr to tape as a data
; tape (header type 3, version LEAPC_TAPE_VERSION) named name (1-10 characters; else, or for len 0, runtime
; error 4)
; int tape_load(const char *name, void *addr, unsigned max) -- the next data tape named name ("": any) into
; addr, at most max bytes: its length; -1 when nothing was loaded (no such tape found, longer than max, a bad
; block before the data), -2 when its data block failed after part of it was written, -3 for a tape whose
; version word is not Leap-C's (nothing loaded). A name longer than 10 characters: runtime error 4
; Both: any address (chunk 6 too: the EXROM's header logic, SH_LIBTAPE, moves the blocks with chunk 6 paged
; out, TAPE_BLOCK); BREAK or SPACE stops the transfer and the program (runtime error 5). A section that
; defers BREAK (NOBRK, spec.md 5.8). Interrupts are off while a block moves (FRAMES does not count)
LIB_TAPE_SAVE:
    DB   $3E                           ; (`ld a, n`: n is the `xor a` below, so A = $AF: tape_save)
LIB_TAPE_LOAD:
    xor  a                             ; A = 0: tape_load
    ex   af, af'                       ; (the selector in A': LIB_ARGS keeps it)
    call LIB_ARGS                      ; HL = the name
    ld   de, TAPE_NAME                 ; its first 11 bytes, read with chunk 6 = RAM
    ld   bc, TAPE_NAME_LEN + 1
    ldir
    call LIB_ARGS                      ; DE = the address, BC = the length
    push ix
    ld   hl, NOBRK
    inc  (hl)
    call BANK_PAGE_EXROM_IN
    ex   af, af'
    call LEAPC_EXROM_TAPE              ; A = 0: HL = the result; else A = the runtime error
    push af
    call BANK_PAGE_EXROM_OUT
    pop  af
    pop  ix
    or   a
    jp   nz, RT_LIBERR
    push hl
    call RT_NOBRK_END
    pop  hl
    ret
