; ============================================================================
; src/cart/cart_bank.asm -- the EXROM paging of the cartridge build (-DLEAPC_CART, make cart;
; docs/milestones/M12-cart.md). src/rom/home.asm assembles this in place of kernel/bank/bank.asm.
;
; The cartridge runs this HOME from DOCK chunks 0-1 and the release EXROM from DOCK chunk 6, so the
; paging keeps HSR (port $F4) bits 0-1 set and never writes port $FF (bit 7 stays 0: DOCK, never the
; stock EXROM). Each routine has its release size and its labels their release offsets, so every later
; label keeps its release address (tools/cart_check.py). Padding that runs is `nop` (0), never $FF.
; ============================================================================

    IFNDEF KERNEL_BANK_ASM
    DEFINE KERNEL_BANK_ASM

CART_HSR_HOME   EQU %00000011       ; chunks 0-1 DOCK (this ROM); the rest HOME: chunk 6 is RAM
CART_HSR_EXROM  EQU %01000011       ; and chunk 6 DOCK (the release EXROM)

; BANK_PAGE_EXROM_IN -- as the release's (depth counted, ports written on 0 -> 1 only, ends with EI);
; HSR = CART_HSR_EXROM, port $FF untouched. Destroys: AF
BANK_PAGE_EXROM_IN:
    ld   a, (BANK_EXROM_DEPTH)
    inc  a
    ld   (BANK_EXROM_DEPTH), a
    dec  a
    jr   nz, .already_paged_in
    ld   a, CART_HSR_EXROM
    jr   .out
.home:                              ; BANK_PAGE_EXROM_OUT's step at depth 0: chunk 6 back to RAM
    ld   a, CART_HSR_HOME
.out:
    out  (PORT_BANK_HOME), a
    DS   BANK_PAGE_EXROM_IN + 25 - $, 0     ; (nop) the release's .already_paged_in offset
.already_paged_in:
    ei
    ret
    ASSERT $ == BANK_PAGE_EXROM_IN + 27     ; the release routine's 27 bytes

; BANK_PAGE_EXROM_OUT -- as the release's: depth 1 -> 0 pages chunk 6 back to RAM (HSR CART_HSR_HOME,
; chunks 0-1 kept DOCK: writing 0 would switch this ROM out). Destroys: AF
BANK_PAGE_EXROM_OUT:
    ld   a, (BANK_EXROM_DEPTH)
    or   a
    jr   z, .depth_already_zero
    dec  a
    ld   (BANK_EXROM_DEPTH), a
    jr   z, BANK_PAGE_EXROM_IN.home
    DS   BANK_PAGE_EXROM_OUT + 15 - $, 0    ; (nop) the release's label offsets
.still_nested:
.depth_already_zero:
    ei
    ret
    ASSERT $ == BANK_PAGE_EXROM_OUT + 17    ; the release routine's 17 bytes
BANK_CART_HOME  EQU BANK_PAGE_EXROM_IN.home

    ENDIF
