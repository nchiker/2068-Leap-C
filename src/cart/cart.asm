; ============================================================================
; src/cart/cart.asm -- the runtime cartridge (-DLEAPC_CART, make cart; docs/milestones/M12-cart.md)
;
; One compiled Leap-C program runs from the DOCK of a stock TS2068 (stock HOME ROM and EXROM installed).
; The stock ROM finds the LROS header at DOCK $0000 (src/rom/home.asm's page zero under the flag) and
; jumps to CART_ENTRY. Every release label keeps its address (tools/cart_check.py), so a program the
; release ROM compiled runs here; the EXROM is the release's, byte for byte.
;
;   DOCK chunk  address  content                          mapped (HSR, port $F4)
;   0-1         $0000    this HOME image                  always ($03, $43)
;   2           $4000    the image past its first 16 KB   only in CART_LOAD, interrupts off ($37)
;   4-5         $8000    the program image                only in CART_LOAD, interrupts off ($37, $33)
;   6           $C000    the release EXROM                while BANK_EXROM_DEPTH > 0 ($43); else RAM
;
; The program image (tools/cartpack.py writes it; little-endian words):
;   +0   4  "LCPG"           +4  1  format (CART_FORMAT)
;   +5   2  identity: CRC-16/CCITT ($1021, init $FFFF) of the release HOME then EXROM (CART_IDENTITY)
;   +7   2  RUN_MAIN         +9  1  RUN_VOID          +10  16  IMG_LIM     +26  1  LIB_LOADED
;   +27     blocks [length:2][address:2][bytes], ended by a length of 0 (a block is at most 8 KB)
;   end  2  CRC-16/CCITT of every byte before it, high byte first (the CRC over all of it is then 0)
; The stream continues at DOCK $4000 when it reaches $C000.
; ============================================================================

    IFNDEF SRC_CART_CART_ASM
    DEFINE SRC_CART_CART_ASM

    INCLUDE "build/cart/cart_exrom.inc"     ; tools/cart_build.py: CART_IDENTITY, the EXROM addresses

CART_HSR_LOAD   EQU %00110111       ; chunks 0-1, 2, 4-5 DOCK; chunks 3, 6, 7 (the destinations) HOME
CART_HSR_HDR    EQU %00110011       ; chunks 0-1, 4-5 DOCK; chunk 2 HOME (the cells)
CART_CHUNK_SPEC EQU ~CART_HSR_EXROM & $FF  ; the LROS header's chunk byte, 0 = DOCK: chunks 0, 1, 6 ($BC)
CART_IMAGE      EQU $8000
CART_FORMAT     EQU 1
CART_HDR_MAIN   EQU 7               ; RUN_MAIN, RUN_VOID
CART_HDR_LIM    EQU 10              ; IMG_LIM
CART_HDR_LIB    EQU 26              ; LIB_LOADED
CART_HDR_SIZE   EQU 27
    ASSERT RUN_VOID == RUN_MAIN + 2 && IMG_REGIONS * 4 == CART_HDR_LIB - CART_HDR_LIM
    ASSERT PORT_AY_DATA < 256

; ============================================================================
; CART_ENTRY -- the LROS entry: the stock ROM jumps here (interrupts on, its stack in chunk 3,
; HSR $43); a key after the report jumps here again. Quiets the AY (the stock ROM wrote it) and runs
; the release cold start, which ends in CART_RUN (COLD_START's last jump under the flag)
; ============================================================================
CART_ENTRY:
    di
    ld   sp, LEAPC_STACK_TOP
    ld   a, CART_HSR_HOME
    out  (PORT_BANK_HOME), a
    ld   bc, PORT_AY_DATA           ; B = 0
    ld   a, 13
.ay:                                ; AY registers 13 .. 0 = 0
    out  (PORT_AY_REG), a
    out  (c), b
    dec  a
    jp   p, .ay
    jp   COLD_START

; ============================================================================
; CART_RUN -- COLD_START's end (interrupts on, BANK_EXROM_DEPTH 1, the EXROM paged in): load the
; image and run it as the shell's RUN does after a compile (SH_RUN.compiled: a cleared screen, RT_RUN,
; the one-row report on row 23, a key). RUN_FNLINES is 0 (the cold start's), so RT_ERRLINE is 0 and
; the report never looks for a source line. No image or a bad one: NO PROGRAM and a key. Then a cold
; start again: the image is copied afresh
; ============================================================================
CART_RUN:
    call CART_LOAD
    jr   c, .none
    ld   de, SH_REPORT_BUF
    call CART_X_SH_RUN_COMPILED
    jp   CART_ENTRY
.none:
    ld   hl, CART_TXT_NONE
    call CART_X_SH_SHOW_MESSAGE
    jp   CART_ENTRY

; ============================================================================
; CART_LOAD -- check the program image and copy it (interrupts off throughout; on at the end)
; Out: NC: the blocks copied, RUN_MAIN, RUN_VOID, IMG_LIM and LIB_LOADED set. C: no image or a bad
;      one (signature, format, identity, a block over 8 KB, CRC). HSR CART_HSR_EXROM either way
; Destroys: AF, BC, DE, HL
; ============================================================================
CART_LOAD:
    di
    ld   a, CART_HSR_LOAD           ; (chunk 2 DOCK: the cells are hidden until .cells)
    out  (PORT_BANK_HOME), a
    ld   hl, CART_IMAGE
    ld   de, $FFFF                  ; the CRC
    ld   bc, CART_SIG
.sig:                               ; signature, format, identity
    call CART_NEXT
    push hl
    ld   h, b
    ld   l, c
    cp   (hl)
    pop  hl
    jr   nz, .bad
    inc  bc
    ld   a, c
    cp   CART_SIG_END & $FF
    jr   nz, .sig
    ld   b, CART_HDR_SIZE - (CART_SIG_END - CART_SIG)
.hdr:
    call CART_NEXT
    djnz .hdr
.blk:                               ; pass 1: the blocks' lengths and the CRC
    call CART_NEXT
    ld   c, a
    call CART_NEXT
    ld   b, a
    or   c
    jr   z, .crc
    ld   a, b
    cp   $21
    jr   nc, .bad                   ; over 8 KB
    call CART_NEXT
    call CART_NEXT                  ; (the address)
.skip:
    call CART_NEXT
    dec  bc
    ld   a, b
    or   c
    jr   nz, .skip
    jr   .blk
.crc:
    call CART_NEXT
    call CART_NEXT
    ld   a, d
    or   e
    jr   nz, .bad
    ld   hl, CART_IMAGE + CART_HDR_SIZE
.cblk:                              ; pass 2: copy
    call CART_GETB
    ld   c, a
    call CART_GETB
    ld   b, a
    or   c
    jr   z, .cells
    call CART_GETB
    ld   e, a
    call CART_GETB
    ld   d, a
.copy:
    call CART_GETB
    ld   (de), a
    inc  de
    dec  bc
    ld   a, b
    or   c
    jr   nz, .copy
    jr   .cblk
.cells:
    ld   a, CART_HSR_HDR
    out  (PORT_BANK_HOME), a
    ld   hl, CART_IMAGE + CART_HDR_MAIN
    ld   de, RUN_MAIN
    ld   bc, 3
    ldir                            ; RUN_MAIN, RUN_VOID
    ld   de, IMG_LIM
    ld   c, IMG_REGIONS * 4
    ldir
    ld   a, (hl)
    ld   (LIB_LOADED), a
    or   a
    jr   .done
.bad:
    scf
.done:
    ld   a, CART_HSR_EXROM
    out  (PORT_BANK_HOME), a
    ei
    ret

; CART_GETB -- A = the image byte at HL, HL past it (at $C000 the stream goes on at $4000). Destroys: F
CART_GETB:
    ld   a, h
    cp   $C0
    jr   nz, .read
    ld   h, $40
.read:
    ld   a, (hl)
    inc  hl
    ret

; CART_NEXT -- CART_GETB, and the byte into the CRC in DE (CRC-16/CCITT, MSB first). Keeps BC
CART_NEXT:
    call CART_GETB
    push bc
    push af
    xor  d
    ld   d, a
    ld   b, 8
.bit:
    sla  e
    rl   d
    jr   nc, .next
    ld   a, d
    xor  $10
    ld   d, a
    ld   a, e
    xor  $21
    ld   e, a
.next:
    djnz .bit
    pop  af
    pop  bc
    ret

CART_SIG:
    DB   "LCPG", CART_FORMAT
    DW   CART_IDENTITY
CART_SIG_END:

CART_TXT_NONE:
    DB   "NO PROGRAM", 0

    ENDIF
