; ============================================================================
; src/runtime/library.asm -- the built-in library (spec.md 7; Phase 3 completes it)
;
; Library functions follow the C calling convention (spec.md 5.2): arguments on the stack, the
; first lowest, removed by the caller; the result in HL; IX and IY kept.
; ============================================================================

; ============================================================================
; LIB_SRAND -- void srand(unsigned seed): restart the sequence of rand(). Seeds 0 and 1 give the
; same sequence (the generator's state may not be 0)
; LIB_RAND -- int rand(void): the next number of the sequence, 0 .. 32767 (RAND_MAX). Without
; srand(), a program gets the sequence of srand(1) (RT_RUN clears the state)
; The generator: a 16-bit xorshift (shifts 7, 9, 8), period 65535; the result is the state
; without its top bit. RND_STATE is the platform's cell (include/sysvars.inc)
; Destroys: AF, BC (srand), AF (rand)
; ============================================================================
LIB_SRAND:
    pop  bc
    pop  hl
    push hl
    push bc
    ld   (RND_STATE), hl
    ret
LIB_RAND:
    ld   hl, (RND_STATE)
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
    ld   (RND_STATE), hl
    res  7, h
    ret
