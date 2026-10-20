; ============================================================================
; src/test/layout_negctl.asm -- negative controls for the RAM layout guard (-DLEAPC_NEGCTL=n;
; tools/check_ram_layout.py --negative, make check; project_plan.md section 6)
;
; Each control references one deliberately misplaced cell from code appended after the production
; HOME code (the production bytes keep their addresses; nothing is saved). The census must report
; every one; the text in backquotes must appear in its report.
; ============================================================================

    IF LEAPC_NEGCTL == 1                ; control 1: expect `in the source region`
NEGCTL_CELL     EQU LEAPC_SRC_BASE + 16
    ENDIF
    IF LEAPC_NEGCTL == 2                ; control 2: expect `in the image region 2`
NEGCTL_CELL     EQU LEAPC_IMG2_BASE + $100
    ENDIF
    IF LEAPC_NEGCTL == 3                ; control 3: expect `in the stack`
NEGCTL_CELL     EQU LEAPC_STACK_LIMIT + $200
    ENDIF
    IF LEAPC_NEGCTL == 4                ; control 4: expect `in the image region 4`
NEGCTL_CELL     EQU LEAPC_IMG4_BASE + $100
    ENDIF
    IF LEAPC_NEGCTL == 5                ; control 5: expect `in the image region 1`
NEGCTL_CELL     EQU LEAPC_IMG1_BASE + $100
    ENDIF
    IF LEAPC_NEGCTL == 6                ; control 6: expect `EXTENSION_MAGIC`
NEGCTL_CELL     EQU EXTENSION_MAGIC     ; a V2 cell Leap-C does not use (MEM_INIT's old clear, D5)
    ENDIF
    IF LEAPC_NEGCTL == 7                ; control 7: expect `in the unused top`
NEGCTL_CELL     EQU LEAPC_STACK_TOP + 8
    ENDIF
    IF LEAPC_NEGCTL == 8                ; control 8: expect `in the image region 3`
NEGCTL_CELL     EQU LEAPC_IMG3_BASE + 4
    ENDIF

NEGCTL_CODE:
    ld   (NEGCTL_CELL), a
    ret
