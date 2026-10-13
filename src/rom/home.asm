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
; RST $08-$30 are the runtime helper vectors (LDI, STI, ENTER, LEAVE, CMPLT, reserved). The helper
; core arrives in M1.3; until then each vector stops the machine (RST_UNASSIGNED).
    ORG $0008
    jr   RST_UNASSIGNED
    ORG $0010
    jr   RST_UNASSIGNED
    ORG $0018
    jr   RST_UNASSIGNED
    ORG $0020
    jr   RST_UNASSIGNED
    ORG $0028
    jr   RST_UNASSIGNED
    ORG $0030
RST_UNASSIGNED:
    di
    halt
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
    INCLUDE "src/compiler/fold.asm"
COMP_CODEGEN_END:
COMP_STMT_BEGIN:
    INCLUDE "src/compiler/stmt.asm"
COMP_STMT_END:

; ---------------------------------------------------------------- runtime
COMP_RTEXIT_BEGIN:
    INCLUDE "src/runtime/rtexit.asm"
COMP_RTEXIT_END:

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
