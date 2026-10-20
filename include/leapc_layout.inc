; ============================================================================
; include/leapc_layout.inc -- the Leap-C RAM map (spec.md section 3.1, baseline layout A: final,
; Phase 4, docs/milestones/M4.md)
;
; Every Leap-C module refers to RAM only through the symbols defined here (or the platform's own
; sysvars.inc, which this file relocates). Tuning the layout means changing this file only.
; tools/check_ram_layout.py (make check) proves from the listings that every RAM cell the ROMs
; reference lies where this map allows it.
;
; Include order in both images:
;   include/hardware.inc        (platform)
;   include/leapc_layout.inc    (this file: region symbols; must come before sysvars.inc)
;   include/sysvars.inc         (platform, relocated to LEAPC_SYSVARS_BASE by Leap-C delta D1)
;   include/leapc_cells.inc     (Leap-C fixed cells, placed after the platform system variables)
;
;   $4000-$5AFF  display file 1 + attributes
;   $5B00-...    platform system variables (V2 layout, relocated)      LEAPC_SYSVARS_BASE
;   ...-$5FFF    Leap-C fixed cells (leapc_cells.inc)                  LEAPC_CELLS_LIMIT
;   $6000-$77FF  display file 2 (hi-res mode) or image region 4        LEAPC_IMG4_*
;   $7800-$BFFF  source store (up), compile workspace (down), heap     LEAPC_SRC_BASE/TOP
;   $C000-$DFFF  image region 1 (chunk 6, EXROM paged out)             LEAPC_IMG1_*
;   $E000-$F17F  image region 2                                        LEAPC_IMG2_*
;   $F180-$F3FF  UDGs, edit buffer, platform cells (V2 addresses)      LEAPC_PLAT_*
;   $F400-$F7FF  image region 3                                        LEAPC_IMG3_*
;   $F800-$FEFF  machine stack (top $FF00)                             LEAPC_STACK_*
;   $FF00-$FFFF  not used by the ROM (test harness return slot)
; ============================================================================

    IFNDEF LEAPC_LAYOUT_INC
    DEFINE LEAPC_LAYOUT_INC

LEAPC_SYSVARS_BASE  EQU $5B00   ; platform sysvars (V2: $8000)
LEAPC_CELLS_LIMIT   EQU $6000   ; Leap-C fixed cells end below display file 2

LEAPC_IMG4_BASE     EQU $6000   ; display file 2 / image region 4
LEAPC_IMG4_END      EQU $7800

LEAPC_SRC_BASE      EQU $7800   ; first byte of the line store (PROG_AREA_START)
LEAPC_SRC_TOP       EQU $C000   ; first byte above the source region (= PROG_AREA_MAX)

LEAPC_IMG1_BASE     EQU $C000   ; chunk 6
LEAPC_IMG1_END      EQU $E000
LEAPC_IMG2_BASE     EQU $E000
LEAPC_IMG2_END      EQU $F180
LEAPC_PLAT_BASE     EQU $F180   ; the V2 platform cells that keep their V2 addresses (UDG_TABLE,
LEAPC_PLAT_END      EQU $F400   ; EDIT_LINE_BUF, GFX_LINE_X0..Y1; tools/check_ram_layout.py)
LEAPC_IMG3_BASE     EQU $F400
LEAPC_IMG3_END      EQU $F800

LEAPC_STACK_LIMIT   EQU $F800   ; lowest stack byte
LEAPC_STACK_TOP     EQU $FF00   ; initial SP

; ENTER's stack check (spec.md 5.3): a frame may not take SP below this. ENTER checks before it
; moves SP (src/runtime/helpers.asm), so only what runs between two frame checks can go further
; down, and the margin above LEAPC_STACK_LIMIT bounds it (measured, docs/milestones/M4.md):
;   held operands       2 B per expression level: at most 124 B (the compiler's nesting guard)
;   pending arguments   2 B per word, at most LEAPC_ARGS_MAX words (expr.asm CX_CALL): 64 B
;   a library routine   at most 40 B below its arguments (puts/print scrolling the screen)
;   the IM 1 handler    18 B; the call and ENTER's push of IX: 4 B
; 250 B in all: the stack never leaves $F800-$FEFF. The floor is page-aligned (ENTER compares
; the high byte only).
LEAPC_RT_STACK_FLOOR EQU LEAPC_STACK_LIMIT + 256
LEAPC_ARGS_MAX      EQU 32      ; argument words pending at once in the calls being evaluated
    ASSERT (LEAPC_RT_STACK_FLOOR & $FF) == 0
    ASSERT 124 + 2 * LEAPC_ARGS_MAX + 40 + 18 + 4 <= LEAPC_RT_STACK_FLOOR - LEAPC_STACK_LIMIT

; The heap (spec.md 3.2, 7): at run time, from the end of the source (PROG_END) to LIB_HEAP_END,
; the last word of the source region, which holds the heap's end mark (src/runtime/library.asm).
LIB_HEAP_END        EQU LEAPC_SRC_TOP - 2

; MEM_COLD_INIT (platform delta D2) clears the system variables, the Leap-C cells, display file 2
; and the source region: LEAPC_COLD_CLEAR_BASE .. LEAPC_SRC_TOP-1.
LEAPC_COLD_CLEAR_BASE EQU LEAPC_SYSVARS_BASE

; Program tapes (spec.md section 8.1): bit 15 = Leap-tagged, major $0C = Leap-C source, minor 0.
LEAPC_TAPE_VERSION  EQU $8C00

; ---- layout guards (assembly time): the regions tile RAM in the order of the map above ----
    ASSERT LEAPC_SYSVARS_BASE == $4000 + 6912
    ASSERT LEAPC_CELLS_LIMIT == LEAPC_IMG4_BASE && LEAPC_IMG4_END == LEAPC_SRC_BASE
    ASSERT LEAPC_SRC_TOP == LEAPC_IMG1_BASE && LEAPC_IMG1_END == LEAPC_IMG2_BASE
    ASSERT LEAPC_IMG2_END == LEAPC_PLAT_BASE && LEAPC_PLAT_END == LEAPC_IMG3_BASE
    ASSERT LEAPC_IMG3_END == LEAPC_STACK_LIMIT && LEAPC_STACK_LIMIT < LEAPC_RT_STACK_FLOOR
    ASSERT LEAPC_RT_STACK_FLOOR < LEAPC_STACK_TOP && LEAPC_STACK_TOP == $FF00
    ASSERT LEAPC_IMG1_BASE == $C000 && LEAPC_IMG1_END == $E000    ; chunk 6 exactly
    ASSERT (LEAPC_IMG4_BASE & $FF) == 0 && (LEAPC_IMG4_END & $FF) == 0  ; LIB_MODE's compare

    ENDIF
