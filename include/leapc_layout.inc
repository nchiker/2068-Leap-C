; ============================================================================
; include/leapc_layout.inc -- the Leap-C RAM map (spec.md section 3.1, baseline layout A)
;
; Every Leap-C module refers to RAM only through the symbols defined here (or the platform's own
; sysvars.inc, which this file relocates). Tuning the layout means changing this file only.
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
;   $F180-$F3FF  UDGs, edit buffer, platform cells (V2 addresses)
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
LEAPC_IMG3_BASE     EQU $F400
LEAPC_IMG3_END      EQU $F800

LEAPC_STACK_LIMIT   EQU $F800   ; lowest stack byte
LEAPC_STACK_TOP     EQU $FF00   ; initial SP
; ENTER's stack check (spec.md 5.3): a frame may not take SP below this. The margin above
; LEAPC_STACK_LIMIT covers what runs without its own check: expression temporaries, argument
; lists, helpers and library routines, the IM 1 handler.
LEAPC_RT_STACK_FLOOR EQU LEAPC_STACK_LIMIT + 128

; The heap (spec.md 3.2, 7): at run time, from the end of the source (PROG_END) to LIB_HEAP_END,
; the last word of the source region, which holds the heap's end mark (src/runtime/library.asm).
LIB_HEAP_END        EQU LEAPC_SRC_TOP - 2

; MEM_COLD_INIT (platform delta D2) clears the system variables, the Leap-C cells, display file 2
; and the source region: LEAPC_COLD_CLEAR_BASE .. LEAPC_SRC_TOP-1.
LEAPC_COLD_CLEAR_BASE EQU LEAPC_SYSVARS_BASE

; Program tapes (spec.md section 8.1): bit 15 = Leap-tagged, major $0C = Leap-C source, minor 0.
LEAPC_TAPE_VERSION  EQU $8C00

    ENDIF
