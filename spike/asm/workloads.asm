; 2068-Leap-C code-shape spike -- the four workloads, written once with the templates.
; The C each function stands for is in the comment above it. Every statement is translated
; with the same naive single-pass templates in both forms; nothing is hand-optimised.

; int sum(int n) { int s; s = 0; while (n) { s += n; --n; } return s; }
;   locals: s @0 (N=2)   args: n @6
SUM:
        ENTERF 2
        ld hl,0                 ; s = 0
        STLOC 0
.while:
        LDLOC 6                 ; while (n)
        ld a,h
        or l
        jp z,.end
        LDLOC 0                 ; s += n
        push hl
        LDLOC 6
        pop de
        add hl,de
        STLOC 0
        LDLOC 6                 ; --n
        dec hl
        STLOC 6
        jp .while
.end:
        LDLOC 0                 ; return s
        EPILOGUE 2
SUM_END:

; void copy(char *d, char *s, unsigned n) { while (n--) *d++ = *s++; }
;   no locals (N=0)   args: d @4, s @6, n @8
COPY:
        ENTERF 0
.while:
        LDLOC 8                 ; n-- (value context: old value tested)
        push hl
        dec hl
        STLOC 8
        pop hl
        ld a,h
        or l
        jp z,.end
        LDLOC 4                 ; d++ -> address of the left side
        push hl
        inc hl
        STLOC 4
        pop hl
        push hl
        LDLOC 6                 ; *s++
        push hl
        inc hl
        STLOC 6
        pop hl
        ld l,(hl)               ; unsigned char load
        ld h,0
        pop de                  ; store byte
        ld a,l
        ld (de),a
        jp .while
.end:
        EPILOGUE 0
COPY_END:

; int a[100];
; int asum(int n) { int i; int t; t = 0; for (i = 0; i < n; i++) t += a[i]; return t; }
;   locals: i @0, t @2 (N=4)   args: n @8
;   single-pass for-loop layout: init; cond; jp body; step; jp cond; body; jp step
ASUM:
        ENTERF 4
        ld hl,0                 ; t = 0
        STLOC 2
        ld hl,0                 ; i = 0
        STLOC 0
.cond:
        LDLOC 0                 ; i < n
        push hl
        LDLOC 8
        pop de
        CMPLT
        jp nc,.end
        jp .body
.step:
        LDLOC 0                 ; i++
        inc hl
        STLOC 0
        jp .cond
.body:
        LDLOC 2                 ; t += a[i]
        push hl
        LDLOC 0
        add hl,hl
        ld de,ARR_A
        add hl,de
        LDIND
        pop de
        add hl,de
        STLOC 2
        jp .step
.end:
        LDLOC 2                 ; return t
        EPILOGUE 4
ASUM_END:

; struct pt { int x; int y; char c; };        /* 5 bytes */
; struct pt pts[20];
; void move(struct pt *p, int n, int dx) { while (n--) { p->x += dx; p->y += p->x; p++; } }
;   no locals   args: p @4, n @6, dx @8
MOVE:
        ENTERF 0
.while:
        LDLOC 6                 ; n--
        push hl
        dec hl
        STLOC 6
        pop hl
        ld a,h
        or l
        jp z,.end
        LDLOC 4                 ; p->x += dx  (offset 0)
        push hl
        LDIND
        push hl
        LDLOC 8
        pop de
        add hl,de
        pop de
        STIND
        LDLOC 4                 ; p->y += p->x
        ld de,2
        add hl,de
        push hl
        LDIND
        push hl
        LDLOC 4
        LDIND
        pop de
        add hl,de
        pop de
        STIND
        LDLOC 4                 ; p++  (statement: p = p + sizeof(struct pt))
        ld de,5
        add hl,de
        STLOC 4
        jp .while
.end:
        EPILOGUE 0
MOVE_END:

; int fact(int n) { int r; if (n <= 1) return 1; r = n * fact(n - 1); return r; }
;   locals: r @0 (N=2)   args: n @6.  Multiply = the kept V2 kernel routine (both forms).
FACT:
        ENTERF 2
        LDLOC 6                 ; if (n <= 1)  ==  !(1 < n)
        push hl
        ld hl,1
        pop de
        ex de,hl
        CMPLT
        jp c,.skip
        ld hl,1                 ; return 1
        RETJ 2, FACT_EPI
.skip:
        LDLOC 6                 ; r = n * fact(n - 1)
        push hl
        LDLOC 6
        push hl
        ld hl,1
        pop de
        ex de,hl
        or a
        sbc hl,de
        push hl
        call FACT
        pop bc
        pop de
        call MATH_MULTIPLY16
        STLOC 0
        LDLOC 0                 ; return r
FACT_EPI:
        EPILOGUE 2
FACT_END:

; Banking probe 1 (not a workload): from code in this segment, call a HOME platform service
; that does not page (GFX_PUTCHAR), then the package ABI's EXROM-paging service
; (PKG_NUM_TO_TEXT_SAFE: pages chunk 6 in, converts, pages it back out), and copy its text.
PSVC:
        ld a,"C"
        ld b,0
        ld c,0
        call GFX_PUTCHAR
        ld hl,12345
        xor a                   ; TAG_INT
        call PKG_NUM_TO_TEXT_SAFE
        ld de,PSVC_TXT
.copy:
        ld a,(hl)
        ld (de),a
        inc hl
        inc de
        or a
        jr nz,.copy
        ld hl,(BANK_EXROM_DEPTH)
        ret

; Banking probe 2 (negative control): page EXROM in WITHOUT a HOME trampoline. The next
; instruction fetch comes from EXROM, not from this code: expected never to reach `ret`.
HAZARD:
        call BANK_PAGE_EXROM_IN
        ld hl,$1234
        ret

; Soak (test scaffolding, not a workload): 200 x { sum(255), checked; PSVC } with interrupts on,
; all from code in this segment. HL = number of wrong sums.
SOAK:
        ld hl,0
        ld (SOAK_FAIL),hl
        ld b,200
.loop:
        push bc
        ld hl,255
        push hl
        call SUM
        pop bc
        ld de,32640
        or a
        sbc hl,de
        jr z,.ok
        ld hl,(SOAK_FAIL)
        inc hl
        ld (SOAK_FAIL),hl
.ok:
        call PSVC
        pop bc
        djnz .loop
        ld hl,(SOAK_FAIL)
        ret
CODE_END:
