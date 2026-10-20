; ============================================================================
; src/runtime/rtexit.asm -- program start and exit, BREAK, runtime errors (spec.md 5.7-5.9)
;
; A program runs from RT_RUN with chunk 6 paged out (its code and data may be there), on the
; caller's stack: RT_RUN records RUN_SP and calls main. Every end comes back to RT_RUN through
; RUN_SP: main's return, exit(), a runtime error (RT_ERROR) and BREAK (the ISR, RT_BREAKREQ). RT_RUN
; then drops the program's stack, silences the AY, restores the display mode and the paging, and
; maps the failing address to a source line through the function -> line table.
; ============================================================================

; ============================================================================
; RT_RUN -- run the compiled program (spec.md 5.7)
; In:  RUN_MAIN / RUN_VOID from the last successful compile (CC_PROGRAM); any paging depth (the
;      shell's: 1)
; Out: A = 0 and HL = the exit status (main's value, or exit()'s argument; 0 for a void main), or
;      A = the runtime error (RT_ERRNUM; RTE_BREAK for BREAK) and RT_ERRLINE = the line where the
;      definition of the function that failed starts (0: unknown; not meaningful without an error). The program's stack is dropped;
;      IX, BANK_EXROM_DEPTH and the paging are as on entry; the AY's three channels are silent; the
;      display is in normal mode
; Destroys: F, BC, DE (IY not used)
; ============================================================================
RT_RUN:
    push ix
    ld   a, (BANK_EXROM_DEPTH)
    push af
    or   a
    jr   z, .out
    ld   a, 1                          ; page the EXROM out whatever the depth: the program's
    ld   (BANK_EXROM_DEPTH), a         ; code and data may be in chunk 6
    call BANK_PAGE_EXROM_OUT
.out:
    call .main
    di                                 ; every end returns here (RUN_SP). A BREAK accepted before
    xor  a                             ; RUNNING is clear unwinds to here again: its interrupt
    ld   (RUNNING), a                  ; wrote the same return address at RUN_SP
    ei
    push hl                            ; the exit status
    call RT_ERRLOC                     ; (meaningful with a runtime error only)
    ld   bc, PORT_AY_DATA              ; B = 0
    ld   a, 10
.quiet:                                ; the AY's volumes R10, R9, R8 = 0
    out  (PORT_AY_REG), a
    out  (c), b
    dec  a
    cp   7
    jr   nz, .quiet
    xor  a
    call GFX_SET_MODE                  ; the normal display mode (no change if it is already)
    pop  hl
    pop  af                            ; the paging depth on entry
    or   a
    jr   z, .done
    push af
    xor  a
    ld   (BANK_EXROM_DEPTH), a
    call BANK_PAGE_EXROM_IN            ; (keeps HL)
    pop  af
    ld   (BANK_EXROM_DEPTH), a
.done:
    pop  ix
    ld   a, (RT_ERRNUM)
.leave:                                ; (the test harness reads the run's result here: HOME, whatever
    ret                                ; the caller's paging)
.main:                                 ; every end of the program returns from here (RUN_SP)
    ld   (RUN_SP), sp
    ld   hl, RT_STATE                  ; no error, no BREAK, rand() as after srand(1), the print
    ld   bc, RT_STATE_END - RT_STATE   ; position (0, 0), inverse and over off
    call MEM_FILL_ZERO
    ld   a, ATTR_DEFAULT
    ld   (LIB_ATTR), a
    ld   hl, $8000                     ; the heap (src/runtime/library.asm): one free block from the
    ld   (LIB_HEAP_END), hl            ; end of the source (made even) to LIB_HEAP_END, where a used
    ld   hl, (PROG_END)                ; block of size 0 ends it
    inc  hl
    res  0, l
    ex   de, hl
    ld   hl, LIB_HEAP_END
    or   a
    sbc  hl, de
    ex   de, hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ld   (RUNNING), a                  ; (A = ATTR_DEFAULT: nonzero)
    ld   hl, (RUN_MAIN)
    call RT_CALLHL
.back:                                 ; (main has returned: the test harness checks IX and SP here)
    ld   a, (RUN_VOID)
    or   a
    ret  z
    ld   hl, 0
    ret

; ============================================================================
; RT_ERRLOC -- RT_ERRLINE = the line where the definition of the function containing RT_ERRPC
; starts: the newest record of the function -> line table (spec.md 5.9) that starts at most 8 KB
; before RT_ERRPC (a function's code can continue into the next image region, whose newer
; functions start after it). 0 if none
; Destroys: AF, DE, HL
; ============================================================================
RT_ERRLOC:
    ld   hl, (RUN_FNLINES)
.rec:
    ld   a, h
    or   l
    ret  z
    push hl
    inc  hl
    inc  hl
    rst  $08                           ; LDI: HL = the function's address
    ex   de, hl
    ld   hl, (RT_ERRPC)
    or   a
    sbc  hl, de
    ld   a, h
    pop  hl
    cp   $20
    jr   c, .found
    rst  $08                           ; LDI: the next record
    jr   .rec
.found:
    ld   de, 4
    add  hl, de
    rst  $08                           ; LDI: its line
    ld   (RT_ERRLINE), hl
    ret

; ============================================================================
; RT_BREAKREQ -- BREAK (CAPS SHIFT + SPACE) was pressed: KBD_ISR_TICK calls this when it accepts the
; key (platform delta D4; spec.md 5.8)
; In:  interrupts off; above the return address, the ISR's frame: HL, DE, BC, AF, the IM 1 vector's
;      return, the interrupted PC
; Out: no program running: returns (an ordinary key, the editor's). NOBRK > 0: BRK_HALT set, returns
;      (the section's end honours it, RT_NOBRK_END). Else the program ends with runtime error 5 at the
;      interrupted address, or, in the ROM, at its last library call: does not return (the ISR's
;      frame goes with the program's stack)
; Destroys: AF, HL
; RT_BREAK -- end the program for a deferred BREAK (interrupts on). Does not return
; ============================================================================
RT_BREAKREQ:
    ld   a, (RUNNING)
    or   a
    ret  z
    ld   (BRK_HALT), a
    ld   a, (NOBRK)
    or   a
    ret  nz
    ld   hl, 12
    add  hl, sp
    rst  $08                           ; LDI: HL = the interrupted PC
    ei
    ld   a, h
    cp   LEAPC_IMG4_BASE >> 8
    jr   nc, RT_BREAKAT                ; in the program's image
RT_BREAK:
    ld   hl, (LIB_CALLER)
RT_BREAKAT:
    ld   a, RTE_BREAK
    jp   RT_ERROR

; ============================================================================
; RT_ERR_ARG -- end the program with runtime error 4 (a library function's invalid argument)
; RT_LIBERR -- end the program with runtime error A
; Both at the program's last library call (LIB_CALLER). Do not return
; RT_ERR_STACK and RT_ERROR are in the page-zero padding (src/rom/home.asm)
; ============================================================================
RT_ERR_ARG:
    ld   a, RTE_ARG
RT_LIBERR:
    ld   hl, (LIB_CALLER)
    jp   RT_ERROR
VM_ERR_RANGE    EQU RT_ERR_ARG      ; platform name (rom/v2_ay_beep.asm: BEEP semitone range)

; ============================================================================
; RT_NOBRK_END -- the end of a section that defers BREAK (NOBRK, spec.md 5.8): a BREAK pressed
; during it ends the program now
; In:  NOBRK as the section's start left it, plus 1
; Out: NOBRK - 1; returns unless that is 0 with a BREAK pending (then RT_BREAK: does not return)
; Destroys: AF, HL
; ============================================================================
RT_NOBRK_END:
    ld   hl, NOBRK
    dec  (hl)
    ret  nz
    ld   a, (BRK_HALT)
    or   a
    ret  z
    jr   RT_BREAK
