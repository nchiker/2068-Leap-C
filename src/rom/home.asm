; ============================================================================
; src/rom/home.asm -- the Leap-C HOME ROM (16 KB, $0000-$3FFF)
;
; Components are delimited by COMP_<name>_BEGIN / _END labels; budget.toml maps them to the
; budgets of spec.md section 2.2 and tools/budget.py measures them from the symbol file.
; A test build (-DLEAPC_TEST) appends the test hooks after the production code, so every
; production byte has the same address in both builds (tools/check_test_image.py).
; ============================================================================
    INCLUDE "include/hardware.inc"
    INCLUDE "include/leapc_layout.inc"
    INCLUDE "include/leapc_rom.inc"
    INCLUDE "include/sysvars.inc"
    INCLUDE "include/leapc_cells.inc"
    INCLUDE "include/leapc_tokens.inc"
    INCLUDE "include/leapc_errors.inc"
    INCLUDE "include/leapc_decl.inc"
    DEFINE V2_KTAB_HOME                 ; rom/v2_ay_beep.asm: assemble the HOME pieces
    DEVICE NOSLOT64K

; ---------------------------------------------------------------- page zero (spec.md 2.3)
    ORG $0000
COMP_PAGE0_BEGIN:
    di
    jp   COLD_START
; IO_KEY_SCAN_ROW (kernel/io/io.asm; V2 production also places it in page-zero padding)
; In: A = row select byte. Out: A = the row's key bits. Destroys: AF
IO_KEY_SCAN_ROW:
    in   a, (PORT_ULA)
    ret
; RST $08-$30: the runtime helper vectors (spec.md 2.3, 5.3). Bodies that fit their 8-byte slot sit
; at the vector (no `jp`); the others start there and continue in src/runtime/helpers.asm.
; RST $08 LDI -- HL = the word at HL. Destroys: A
    ORG $0008
RST_LDI:
    ld   a, (hl)
    inc  hl
    ld   h, (hl)
    ld   l, a
    ret
; RST $10 STI -- the word at DE = HL. Out: HL kept, DE = address + 1. Destroys: -
    ORG $0010
RST_STI:
    ex   de, hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ex   de, hl
    ret
; RST $18 ENTER n (`rst $18 / db n`) -- function prologue: push IX; IX = SP (the saved IX);
; SP -= n (the locals); stack check (runtime error 1). Owner decision 2026-10-13: IX points at
; the saved IX, locals at IX-1..IX-n, arguments at IX+4... (spec.md 5.2 as amended in M1.3).
; Destroys: AF, BC, DE, HL
    ORG $0018
RST_ENTER:
    pop  hl                            ; HL -> n
    push ix
    jp   RT_ENTER
; RST $20 LEAVE -- function epilogue: SP = IX; pop IX; return to the caller. HL kept
    ORG $0020
RST_LEAVE:
    ld   sp, ix
    pop  ix
    ret
; RST $28 CMPLT -- signed compare: carry <=> DE < HL. Destroys: AF, DE, HL
    ORG $0028
RST_CMPLT:
    ld   a, h
    xor  d
    jp   p, RT_CMPLT_SAME              ; same signs: an unsigned compare
    ld   a, d
    rla                                ; signs differ: DE < HL <=> DE is negative
    ret
; RST $30 is reserved for the optional size template set (LDL/STL, spec.md 5.6): it stops the
; machine until then
    ORG $0030
RST_UNASSIGNED:
    di
    halt
; Helpers in the page-zero padding (Phase 2 shrink; nothing falls through into them). $0030-$0032
; stay free for a three-byte RST $30 vector.
    ORG $0033
; RT_MODU -- HL = DE % HL, unsigned (src/runtime/helpers.asm). Destroys: AF, BC, DE
RT_MODU:
    call RT_DIVU
    ex   de, hl
    ret
; IM 1 interrupt: FRAMES and the keyboard scan (kernel/interrupt/interrupt.asm)
    ORG $0038
    call KBD_ISR_TICK
    ei
    reti
; Cold start (in the gap between the IM 1 vector and the NMI vector)
; In: power-on or reset (any RAM contents). Out: does not return: the EXROM shell runs with
; chunk 6 = EXROM (BANK_EXROM_DEPTH 1), interrupts on (IM 1), SP = LEAPC_STACK_TOP.
COLD_START:
    ld   sp, LEAPC_STACK_TOP
    call MEM_COLD_INIT                 ; RAM LEAPC_COLD_CLEAR_BASE .. LEAPC_SRC_TOP-1 = 0
    xor  a
    ld   (PORT_FF_SHADOW), a
    out  (PORT_SCLD), a                ; normal video mode, EXROM select bit clear
    call MEM_INIT                      ; empty line store, source ceiling = LEAPC_SRC_TOP
    call KBD_ISR_INIT
    im   1
    ei
    call BANK_PAGE_EXROM_IN
    jp   LEAPC_EXROM_SHELL
; ============================================================================
; RT_ERR_STACK -- ENTER: stack overflow, runtime error 1, in the function being entered
; RT_ERROR -- end the running program (spec.md 5.7, 5.9; src/runtime/rtexit.asm): unwind to RT_RUN
; In:  A = the runtime error (0: exit(), with the status in HL), HL = an address in the code that
;      failed (RT_ERR_STACK: the function's; RT_ERRLOC finds its source line)
; Out: does not return to its caller: RT_ERRNUM = A, RT_ERRPC = HL, SP = RUN_SP, `ret` into RT_RUN
;      with HL kept
; Destroys: everything except A and HL
; ============================================================================
RT_ERR_STACK:
    ld   a, RTE_STACK
RT_ERROR:
    ld   (RT_ERRNUM), a
    ld   (RT_ERRPC), hl
    ld   sp, (RUN_SP)
    ret
    ASSERT $ <= $0066
    ORG $0066
    retn

COMP_PAGE0_END:

; ---------------------------------------------------------------- retained platform (spec.md 2.1)
COMP_PLATFORM_BEGIN:
    INCLUDE "kernel/memory/memory.asm"
    INCLUDE "kernel/io/io.asm"
    INCLUDE "kernel/graphics/graphics.asm"
    INCLUDE "kernel/math/math.asm"
    INCLUDE "kernel/interrupt/interrupt.asm"
    INCLUDE "kernel/bank/bank.asm"
    INCLUDE "rom/v2_ay_beep.asm"
COMP_PLATFORM_END:

; ---------------------------------------------------------------- compiler
COMP_LEXER_BEGIN:
    INCLUDE "src/compiler/lexer.asm"
    INCLUDE "src/compiler/cerror.asm"
COMP_LEXER_END:
COMP_SYMTAB_BEGIN:
    INCLUDE "src/compiler/symtab.asm"
COMP_SYMTAB_END:
COMP_DECL_BEGIN:
    INCLUDE "src/compiler/decl.asm"
    INCLUDE "src/compiler/types.asm"
    INCLUDE "src/compiler/init.asm"
COMP_DECL_END:
COMP_EXPR_BEGIN:
    INCLUDE "src/compiler/expr.asm"
COMP_EXPR_END:
COMP_CODEGEN_BEGIN:
    INCLUDE "src/compiler/codegen.asm"
COMP_CODEGEN_END:

; ---------------------------------------------------------------- EXROM trampolines (page0 budget)
COMP_TRAMP_BEGIN:
; ============================================================================
; CX_FOLD -- the value of `left op right` for constants: the trampoline to XC_FOLD in the EXROM
; (src/compiler/fold.asm; bank rule 3: it touches nothing in chunk 6)
; In:  A = operator token, DE = left, HL = right, C bit 0 = 1: unsigned operation
; Out: HL = the result
; Destroys: AF, BC, DE
; ============================================================================
CX_FOLD:
    push af
    call BANK_PAGE_EXROM_IN
    pop  af
    call LEAPC_EXROM_FOLD
    jp   BANK_PAGE_EXROM_OUT
; ============================================================================
; CX_LIBFIND -- the library function named NM: the trampoline to LIB_FIND in the EXROM
; (src/compiler/libnames.asm; bank rule 3: it reads only the source and its own table)
; Out: Z: HL = its address, D = its signature, E = its parameter list. NZ: not a library name
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_LIBFIND:
    call BANK_PAGE_EXROM_IN
    call LEAPC_EXROM_LIBFIND
    push af
    call BANK_PAGE_EXROM_OUT
    pop  af
    ret
COMP_TRAMP_END:
COMP_STMT_BEGIN:
    INCLUDE "src/compiler/stmt.asm"
COMP_STMT_END:
COMP_PREPROC_BEGIN:
    INCLUDE "src/compiler/preproc.asm"
COMP_PREPROC_END:

; ---------------------------------------------------------------- runtime
COMP_HELPERS_BEGIN:
    INCLUDE "src/runtime/helpers.asm"
COMP_HELPERS_END:
COMP_RTEXIT_BEGIN:
    INCLUDE "src/runtime/rtexit.asm"
COMP_RTEXIT_END:
COMP_LIBRARY_BEGIN:
    INCLUDE "src/runtime/library.asm"
    INCLUDE "src/runtime/libbind.asm"
COMP_LIBRARY_END:

LEAPC_HOME_CODE_END:
    IFDEF LEAPC_TEST
COMP_TEST_BEGIN:
    INCLUDE "src/test/test_hooks.asm"
COMP_TEST_END:
    ENDIF
    ASSERT $ <= LEAPC_HOME_END
    DS   LEAPC_HOME_END - $, $FF
    IFDEF LEAPC_TEST
    SAVEBIN "build/test/leapc_home.bin", $0000, LEAPC_HOME_END
    ELSE
    SAVEBIN "build/leapc_home.bin", $0000, LEAPC_HOME_END
    ENDIF
