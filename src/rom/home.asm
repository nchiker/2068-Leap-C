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
; RST $30 LEX_NEXT -- the compiler's next token (src/compiler/lexer.asm), its most frequent call
; (Phase 5, owner decision: 60 call sites, 2 B each; spec.md 2.3). Generated code never uses it:
; the optional size template set (spec.md 5.6) would call its helpers instead.
    ORG $0030
RST_LEX_NEXT:
    jp   LEX_NEXT
; Helpers in the page-zero padding (Phase 2 shrink; nothing falls through into them)
    ASSERT $ == $0033
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
    DEFINE MEM_NO_LINE_EDIT                     ; (MEM_LINE_INSERT, MEM_LINE_DELETE_RANGE: in the EXROM, D11)
    INCLUDE "kernel/memory/memory.asm"
    INCLUDE "kernel/io/io.asm"
    DEFINE GFX_NO_EDITOR_TEXT                   ; (GFX_PUTCHAR_BOLD, GFX_PRINT_STRING: in the EXROM, D12)
    INCLUDE "kernel/graphics/graphics.asm"
    INCLUDE "kernel/math/math.asm"
    INCLUDE "kernel/interrupt/interrupt.asm"
    INCLUDE "rom/v2_ay_beep.asm"
    INCLUDE "kernel/bank/bank.asm"             ; (after the beep: AY_BEEP_TABLE then stays within a
                                               ; 256-byte page, so AY_BEEP_PERIOD has its short form)
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
; CX_XCALL -- call an EXROM-resident compiler routine (bank rule 3: it never touches chunk 6) with the
; EXROM paged in, through the depth count
; In:  BC = the routine's EXROM entry (LEAPC_EXROM_*); its own inputs in DE, HL, IX and the cells (A
;      and F do not survive the paging)
; Out: the routine's AF, BC, DE, HL, IX
; A compile error inside it leaves through CC_ERROR, which pages the EXROM out (src/compiler/cerror.asm)
; ============================================================================
CX_XCALL:
    call BANK_PAGE_EXROM_IN            ; (keeps BC, DE, HL)
    call .go
    push af
    call BANK_PAGE_EXROM_OUT
    pop  af
    ret
.go:
    push bc
    ret
; LEX_KEYWORD -- keyword or identifier (src/compiler/keywords.asm XK_KEYWORD; Phase 8, ledger L42)
; In:  TOK_BUF / TOK_LEN = the identifier. Out: A = TK_KW_FIRST + index for a C89 keyword, else
;      TK_IDENT. Destroys: AF, BC, DE, HL
LEX_KEYWORD:
    ld   bc, LEAPC_EXROM_KEYWORD
    jr   CX_XCALL
; TY_EQUAL -- are types HL and DE compatible (src/compiler/tyequal.asm XT_EQUAL; Phase 8, ledger L42)?
; Out: Z: compatible. Errors: E_NESTING. Destroys: AF, BC, DE, HL
TY_EQUAL:
    ld   bc, LEAPC_EXROM_TYEQUAL
    jr   CX_XCALL
; LIB_BIND -- declare the undeclared identifier NM if it names a library function (spec.md 7.1;
; src/compiler/libnames.asm XL_BIND; Phase 8, ledger L42)
; In:  NM_PTR, NM_LEN. Out: Z: IX = the new file-scope entry, C = NS_ORD. NZ: not a library name
; Errors: E_NOMEM. Destroys: AF, BC, DE, HL, IX
LIB_BIND:
    ld   bc, LEAPC_EXROM_LIBBIND
    jr   CX_XCALL
; ============================================================================
; SH_COMPILE -- the EXROM shell's RUN: compile the program with chunk 6 paged out (bank rule 3:
; the compiler writes the image there), then page the EXROM back in for the shell
; In:  BANK_EXROM_DEPTH 1 (the shell's)
; Out: as CC_PROGRAM: NC compiled (RUN_MAIN), C error (CC_ERRNUM, CC_ERRLINE); BANK_EXROM_DEPTH
;      1 again
; Destroys: AF, BC, DE, HL (IX kept)
; ============================================================================
SH_COMPILE:
    call BANK_PAGE_EXROM_OUT
    call CC_PROGRAM
    push af
    call BANK_PAGE_EXROM_IN
    pop  af
    ret
; ============================================================================
; TAPE_BLOCK -- one tape block with chunk 6 = RAM (spec.md 8.3): the trampoline through which the EXROM's
; STORAGE_SAVE and STORAGE_LOAD reach the HOME block I/O (src/shell/shell.asm SH_TAPE_SEND, SH_TAPE_RECV), so
; a data block is sent from or received into chunk 6 as into any other RAM. The EXROM is paged out for the
; block and in again after it, both through the depth count (bank rule 2: the stack is never in chunk 6)
; In:  HL = TAPE_SEND_BLOCK or TAPE_RECV_BLOCK; A, F, IX, DE as that routine takes them; BANK_EXROM_DEPTH 1
; Out: as that routine (F, DE, IX); BANK_EXROM_DEPTH 1; interrupts on (between blocks)
; Destroys: AF, AF', BC, DE, HL, IX (the block routine's)
; ============================================================================
TAPE_BLOCK:
    push af
    call BANK_PAGE_EXROM_OUT
    pop  af
    call RT_CALLHL
    push af
    call BANK_PAGE_EXROM_IN
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
COMP_LIBRARY_END:
COMP_FLOAT_BEGIN:
    INCLUDE "src/runtime/float.asm"
COMP_FLOAT_END:

; ---------------------------------------------------------------- tape block I/O (spec.md 2.2, 8.3; Phase 7)
; The platform's STORAGE_SEND_BLOCK and STORAGE_RECEIVE_BLOCK (platform delta D9: the header logic stays in
; the EXROM), reached from the EXROM through TAPE_BLOCK with chunk 6 paged out
COMP_TAPE_BEGIN:
    DEFINE STORAGE_BLOCKS_ONLY
    INCLUDE "kernel/storage/storage.asm"
COMP_TAPE_END:
TAPE_SEND_BLOCK     EQU STORAGE_SEND_BLOCK      ; (the EXROM's names for them: there, STORAGE_SEND_BLOCK and
TAPE_RECV_BLOCK     EQU STORAGE_RECEIVE_BLOCK   ; STORAGE_RECEIVE_BLOCK are its trampolines' callers)

LEAPC_HOME_CODE_END:
    IFDEF LEAPC_TEST
COMP_TEST_BEGIN:
    INCLUDE "src/test/test_hooks.asm"
COMP_TEST_END:
    ENDIF
    IFDEF LEAPC_NEGCTL                  ; the layout guard's negative controls (nothing is saved)
    INCLUDE "src/test/layout_negctl.asm"
    ENDIF
    ASSERT $ <= LEAPC_HOME_END
    DS   LEAPC_HOME_END - $, $FF
    IFDEF LEAPC_TEST
    SAVEBIN "build/test/leapc_home.bin", $0000, LEAPC_HOME_END
    ELSE
    IFNDEF LEAPC_NEGCTL
    SAVEBIN "build/leapc_home.bin", $0000, LEAPC_HOME_END
    ENDIF
    ENDIF
