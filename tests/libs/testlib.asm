; ============================================================================
; tests/libs/testlib.asm -- the test library (Phase 10; tests/lib/loaded/): one function per ROM service of
; the jump table (include/leapc_lib.inc), the four parameter lists LIB_PARAMS gained for libraries, a name the
; ROM's library also has (abs: the ROM's is bound), a loop for BREAK in a library's code, its own data
; ============================================================================
    INCLUDE "leapc_lib.inc"
    ORG  LX_BASE
    LX_HEADER 24
    LX_EXPORT "t_args", t_args, LXR_INT, LXP_III        ; a * 100 + b * 10 + c (LX_ARGS, LX_MUL)
    LX_EXPORT "t_putc", t_putc, LXR_INT, LXP_I          ; prints c (LX_PUTC), returns it
    LX_EXPORT "t_puts", t_puts, LXR_VOID, LXP_P         ; prints s (LX_PUTS)
    LX_EXPORT "t_malloc", t_malloc, LXR_VOIDP, LXP_I    ; LX_MALLOC
    LX_EXPORT "t_free", t_free, LXR_VOID, LXP_P         ; LX_FREE
    LX_EXPORT "t_divs", t_divs, LXR_INT, LXP_II         ; a / b, signed (LX_DIVS)
    LX_EXPORT "t_divu", t_divu, LXR_UINT, LXP_II        ; a / b, unsigned (LX_DIVU)
    LX_EXPORT "t_modu", t_modu, LXR_UINT, LXP_II        ; a % b, unsigned (LX_DIVU's remainder)
    LX_EXPORT "t_fadd", t_fadd, LXR_FLOAT, LXP_II       ; (float) a + b (LX_FOP: FRI, ADD; F_ACC)
    LX_EXPORT "t_fdiv", t_fdiv, LXR_FLOAT, LXP_II       ; (float) a / b: b = 0 is runtime error 6
    LX_EXPORT "t_error", t_error, LXR_VOID, LXP_I       ; runtime error n (LX_ERROR)
    LX_EXPORT "t_key", t_key, LXR_INT, LXP_NONE         ; waits for a key (LX_KEY)
    LX_EXPORT "t_inkey", t_inkey, LXR_INT, LXP_NONE     ; the key latched, or 0 (LX_INKEY)
    LX_EXPORT "t_frames", t_frames, LXR_UINT, LXP_NONE  ; the frame counter (LX_FRAMES)
    LX_EXPORT "t_plot", t_plot, LXR_VOID, LXP_II        ; a pixel (LX_PLOT)
    LX_EXPORT "t_reserved", t_reserved, LXR_VOID, LXP_NONE ; calls reserved slot 14: runtime error 4
    LX_EXPORT "t_spin", t_spin, LXR_INT, LXP_I          ; n * 256 turns of a loop in the library; returns n
    LX_EXPORT "abs", t_abs, LXR_INT, LXP_I              ; 12345: never bound (the ROM's abs comes first)
    LX_EXPORT "t_count", t_count, LXR_INT, LXP_NONE     ; 1, 2, 3, ...: the library's own data
    LX_EXPORT "t_five", t_five, LXR_INT, LXP_IIIII      ; e - a (the fifth argument from the stack)
    LX_EXPORT "t_store", t_store, LXR_VOID, LXP_IIP     ; *p = a + b
    LX_EXPORT "t_poke", t_poke, LXR_VOID, LXP_IP        ; *(char *)p = c
    LX_EXPORT "t_name", t_name, LXR_CHARP, LXP_NONE     ; "TESTLIB": a string in the library
    LX_EXPORT "t_ch", t_ch, LXR_CHAR, LXP_I             ; c & 255 + 1 (a char result)
    LX_EXPORTS_END

t_args:
    call LX_ARGS                       ; HL = a, DE = b, BC = c
    push bc
    push hl
    ex   de, hl
    ld   de, 10
    call LX_MUL                        ; HL = b * 10 (DE kept)
    ex   (sp), hl                      ; [b * 10], HL = a
    ld   de, 100
    call LX_MUL
    pop  de
    add  hl, de
    pop  de
    add  hl, de
    ret

t_putc:
    call LX_ARGS
    ld   a, l
    push hl
    call LX_PUTC
    pop  hl
    ret

t_puts:
    call LX_ARGS
    jp   LX_PUTS

t_malloc:
    call LX_ARGS
    jp   LX_MALLOC

t_free:
    call LX_ARGS
    jp   LX_FREE

t_divs:
    call LX_ARGS
    ex   de, hl                        ; DE = a, HL = b
    jp   LX_DIVS

t_divu:
    call LX_ARGS
    ex   de, hl
    jp   LX_DIVU

t_modu:
    call LX_ARGS
    ex   de, hl
    call LX_DIVU
    ex   de, hl                        ; the remainder
    ret

t_fadd:
    ld   a, FOP_ADD
    jr   fbin
t_fdiv:
    ld   a, FOP_DIV
fbin:                                  ; F_ACC = (float) a OP (float) b
    ld   (fop), a
    call LX_ARGS                       ; HL = a, DE = b
    push de
    ld   a, FOP_FRI
    call LX_FOP                        ; F_ACC = a
    ld   hl, F_ACC
    ld   de, fleft
    ld   bc, 5
    ldir                               ; the left operand
    pop  hl
    ld   a, FOP_FRI
    call LX_FOP                        ; F_ACC = b
    ld   a, (fop)
    ld   hl, fleft
    jp   LX_FOP                        ; F_ACC = left OP F_ACC

t_error:
    call LX_ARGS
    ld   a, l
    jp   LX_ERROR

t_key:
    call LX_ARGS                       ; (LIB_CALLER: BREAK while waiting)
    call LX_KEY
    ld   l, a
    ld   h, 0
    ret

t_inkey:
    call LX_INKEY
    ld   l, a
    ld   h, 0
    ret

t_frames:
    jp   LX_FRAMES

t_plot:
    call LX_ARGS                       ; HL = x, DE = y
    jp   LX_PLOT

t_reserved:
    call LX_ARGS
    jp   LX_SLOTS + 3 * 14

t_spin:
    call LX_ARGS                       ; HL = n
    push hl
    ld   a, h
    or   l
    jr   z, spin_end
spin_loop:                             ; (BREAK lands here: tests/lib/loaded/break_*.c)
    ld   b, 0
spin_inner:
    djnz spin_inner                    ; 256 turns
    dec  hl
    ld   a, h
    or   l
    jr   nz, spin_loop
spin_end:
    pop  hl
    ret

t_abs:
    ld   hl, 12345
    ret

t_count:
    ld   hl, (count)
    inc  hl
    ld   (count), hl
    ret

t_five:
    call LX_ARGS                       ; HL = a
    ex   de, hl
    ld   hl, 10
    add  hl, sp                        ; -> e: the return into the program, then a, b, c, d, e
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    or   a
    sbc  hl, de
    ret

t_store:
    call LX_ARGS                       ; HL = a, DE = b, BC = p
    add  hl, de
    ld   a, l
    ld   (bc), a
    inc  bc
    ld   a, h
    ld   (bc), a
    ret

t_poke:
    call LX_ARGS                       ; HL = c, DE = p
    ld   a, l
    ld   (de), a
    ret

t_name:
    ld   hl, name
    ret

t_ch:
    call LX_ARGS
    ld   h, 0
    inc  l
    ret

; ---- data (image region 3) ----
count:  DW 0
fop:    DB 0
fleft:  DS 5
name:   DB "TESTLIB", 0
