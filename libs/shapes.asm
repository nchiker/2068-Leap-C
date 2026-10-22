; ============================================================================
; libs/shapes.asm -- the example library: circles, boxes and integer square roots (spec.md 7.2; Phase 10)
;
; Build its tapes with tools/lib2tape.py (make libs: build/libs/shapes.tap, .tzx, .wav), load it with
; LIB "shapes" and call its functions from C like the built-in ones; no declaration is needed:
;
;   void circle(int x, int y, int r)          the circle of radius r about (x, y)
;   void box(int x0, int y0, int x1, int y1)  the rectangle with these corners
;   unsigned isqrt(unsigned n)                the integer square root of n (0-255)
;
; circle and box draw like plot(): pixels x 0-255, y 0-191 from the top, in the print attribute and over
; mode; each point once, so over(1) draws and undraws them exactly. circle leaves out the points off the
; screen; box moves coordinates off the screen to its edge, as draw() does. A negative radius is runtime
; error 4 (BAD ARGUMENT), reported at the line of the function that called circle.
;
; The library reaches the ROM only through the jump table (LX_ARGS, LX_PLOT, LX_ERROR), so it runs on every
; ROM with ABI 1 or later. Its working cells are its own, in image region 3 after its code.
; ============================================================================
    INCLUDE "leapc_lib.inc"
    ORG  LX_BASE
    LX_HEADER 3
    LX_EXPORT "circle", circle, LXR_VOID, LXP_III
    LX_EXPORT "box", box, LXR_VOID, LXP_IIII
    LX_EXPORT "isqrt", isqrt, LXR_UINT, LXP_I
    LX_EXPORTS_END

; ============================================================================
; void circle(int x, int y, int r) -- the midpoint algorithm: from (r, 0) round the first octant, each point
; drawn in all eight octants (P_SYM)
; ============================================================================
circle:
    call LX_ARGS                       ; HL = x, DE = y, BC = r
    bit  7, b
    jr   z, .ok
    ld   a, RTE_ARG                    ; r < 0
    jp   LX_ERROR
.ok:
    ld   (cx), hl
    ld   (cy), de
    ld   (px), bc
    ld   hl, 0
    ld   (py), hl
    inc  hl
    sbc  hl, bc                        ; (carry clear) the error term: 1 - r
    ld   (err), hl
.loop:                                 ; while py <= px
    ld   hl, (px)
    ld   de, (py)
    or   a
    sbc  hl, de
    ret  c
    call p_sym
    ld   hl, (py)
    inc  hl
    ld   (py), hl
    ld   de, (err)
    bit  7, d
    jr   nz, .inside                   ; err < 0: err += 2 py + 1
    ld   hl, (px)                      ; else px--; err += 2 (py - px) + 1
    dec  hl
    ld   (px), hl
    ex   de, hl
    ld   hl, (py)
    or   a
    sbc  hl, de
.inside:
    add  hl, hl
    inc  hl
    ld   de, (err)
    add  hl, de
    ld   (err), hl
    jr   .loop

; p_sym -- the points (cx +- px, cy +- py) and (cx +- py, cy +- px), each once
p_sym:
    ld   hl, (px)
    ld   de, (py)
    call p_four
    ld   hl, (px)
    ld   de, (py)
    or   a
    sbc  hl, de
    ret  z                             ; px = py: the same points
    ld   hl, (py)
    ld   de, (px)
; p_four -- the points (cx +- HL, cy +- DE), each once
p_four:
    ld   (ox), hl
    ld   (oy), de
    call .two
    ld   hl, (ox)
    ld   a, h
    or   l
    ret  z                             ; ox = 0: one column
    call neg_hl
    ld   (ox), hl
.two:                                  ; (cx + ox, cy + oy) and, unless oy = 0, (cx + ox, cy - oy)
    ld   de, (oy)
    call .point
    ld   hl, (oy)
    ld   a, h
    or   l
    ret  z
    call neg_hl
    ex   de, hl
.point:                                ; (cx + ox, cy + DE)
    ld   hl, (cy)
    add  hl, de
    ex   de, hl
    ld   hl, (cx)
    ld   bc, (ox)
    add  hl, bc
    jp   LX_PLOT                       ; HL = x, DE = y: clipped to the screen

; neg_hl -- HL = -HL. Destroys: AF
neg_hl:
    xor  a
    sub  l
    ld   l, a
    sbc  a, a
    sub  h
    ld   h, a
    ret

; ============================================================================
; void box(int x0, int y0, int x1, int y1) -- the rectangle's four edges, each point once
; ============================================================================
box:
    call LX_ARGS                       ; HL = x0, DE = y0, BC = x1; the fourth argument after them
    call clampx
    ld   a, l
    ld   (xa), a
    ld   h, b
    ld   l, c
    call clampx
    ld   a, l
    ld   (xb), a
    ex   de, hl
    call clampy
    ld   a, l
    ld   (ya), a
    ld   hl, 8
    add  hl, sp                        ; -> y1: above the return into the program and three arguments
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    call clampy
    ld   a, l
    ld   (yb), a
    ld   hl, (xa)                      ; L = xa, H = xb: in order
    call order
    ld   (xa), hl
    ld   hl, (ya)
    call order
    ld   (ya), hl
    ld   a, (ya)                       ; the top and bottom edges
    call .row
    ld   hl, (ya)
    ld   a, h
    cp   l
    call nz, .row
    ld   hl, (ya)                      ; the sides, between them
.side:
    inc  l
    ld   a, l
    cp   h
    ret  nc
    push hl
    ld   e, l
    ld   d, 0
    push de
    ld   hl, (xa)
    ld   h, d
    call LX_PLOT                       ; (xa, y)
    pop  de
    ld   hl, (xa)
    ld   a, h
    cp   l
    jr   z, .one
    ld   l, h
    ld   h, 0
    call LX_PLOT                       ; (xb, y)
.one:
    pop  hl
    jr   .side
.row:                                  ; the row A from xa to xb
    ld   (by), a
    ld   a, (xa)
.col:
    push af
    ld   l, a
    ld   h, 0
    ld   a, (by)
    ld   e, a
    ld   d, h
    call LX_PLOT
    pop  af
    ld   hl, xb
    cp   (hl)
    ret  z
    inc  a
    jr   .col

; clampx, clampy -- L = HL moved to the screen: 0-255, 0-191. Destroys: AF
clampx:
    ld   a, $FF
    jr   clamp
clampy:
    ld   a, 191
clamp:
    bit  7, h
    jr   nz, .zero                     ; below 0
    inc  h
    dec  h
    jr   nz, .top                      ; 256 or more
    cp   l
    ret  nc
.top:
    ld   l, a
    ret
.zero:
    ld   l, 0
    ret

; order -- L <= H (swapped if not). Destroys: AF
order:
    ld   a, l
    cp   h
    ret  c
    ld   l, h
    ld   h, a
    ret

; ============================================================================
; unsigned isqrt(unsigned n) -- the largest r with r * r <= n: bit by bit from the top (four bits of n each
; step)
; ============================================================================
isqrt:
    call LX_ARGS                       ; HL = n
    ld   de, 0                         ; DE = r
    ld   bc, $4000                     ; BC = the bit: a power of 4
.step:
    push hl
    ex   de, hl
    add  hl, bc                        ; r + bit
    ex   de, hl
    or   a
    sbc  hl, de                        ; n - (r + bit)
    jr   c, .less
    ex   (sp), hl                      ; n -= r + bit
    ex   de, hl
    add  hl, bc                        ; r = (r + bit + bit) / 2 = r / 2 + bit
    ex   de, hl
    jr   .half
.less:
    ex   de, hl
    or   a
    sbc  hl, bc                        ; r again
    ex   de, hl
.half:
    pop  hl
    srl  d
    rr   e                             ; r /= 2
    srl  b
    rr   c
    srl  b
    rr   c                             ; bit /= 4
    ld   a, b
    or   c
    jr   nz, .step
    ex   de, hl                        ; HL = r
    ret

; ---- working cells (image region 3, after the code) ----
cx:     DW 0                           ; circle: the centre ...
cy:     DW 0
px:     DW 0                           ; ... the point in the first octant ...
py:     DW 0
err:    DW 0                           ; ... its error term ...
ox:     DW 0                           ; ... and the offsets drawn
oy:     DW 0
xa:     DB 0                           ; box: the corners on the screen, xa <= xb ...
xb:     DB 0
ya:     DB 0                           ; ... ya <= yb
yb:     DB 0
by:     DB 0                           ; the row being drawn
