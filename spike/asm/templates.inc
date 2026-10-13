; 2068-Leap-C code-shape spike -- code-generation templates.
;
; Each macro is ONE template of a naive, single-pass, Small-C-style code generator
; (primary register HL, secondary DE, temporaries on the machine stack, IX = frame base).
; The workloads are written once with these macros and assembled in two forms:
;
;   FORM 0  conventional inline native Z80 (architecture A)
;   FORM 1  compact native Z80 + shared helpers (architecture C)
;   FORM 2  mixed: locals inline (as FORM 0), every other template as FORM 1
;             HMODE 0: helpers entered with CALL (runs on the unmodified V2 ROM)
;             HMODE 1: helpers entered with RST (needs the spike's patched ROM image,
;                      whose RST vectors hold `jp helper`, as V2's own vectors do)
;
; Frame layout (both forms):  IX+0 .. IX+N-1   locals (N bytes)
;                             IX+N             saved IX
;                             IX+N+2           return address
;                             IX+N+4 ...       arguments, first argument lowest
; Arguments are pushed right to left; the caller removes them (pop bc per argument).
; Offsets are unsigned bytes, so a helper needs no sign extension.

    IFNDEF FORM
FORM = 1
    ENDIF
    IFNDEF HMODE
HMODE = 0
    ENDIF

; RST assignment for the workloads (HMODE 1). $00 (reset) and $38 (IM 1 interrupt) are fixed.
RST_LDL     EQU $08
RST_STL     EQU $10
RST_ENTER   EQU $18
RST_LEAVE   EQU $20
RST_LDI     EQU $28
RST_STI     EQU $30

    MACRO HCALL vec, target
    IF HMODE == 1
        rst vec
    ELSE
        call target
    ENDIF
    ENDM

; HL = local word at IX+d
    MACRO LDLOC d
    IF FORM == 0 || FORM == 2
        ld l,(ix+d)
        ld h,(ix+d+1)
    ELSE
        HCALL RST_LDL, H_LDL
        db d
    ENDIF
    ENDM

; local word at IX+d = HL (HL is not preserved by the helper; templates never rely on it)
    MACRO STLOC d
    IF FORM == 0 || FORM == 2
        ld (ix+d),l
        ld (ix+d+1),h
    ELSE
        HCALL RST_STL, H_STL
        db d
    ENDIF
    ENDM

; function prologue: save IX, reserve n bytes of locals, IX = SP
    MACRO ENTERF n
    IF FORM == 0
        push ix
      IF n == 0
        ld ix,0
        add ix,sp
      ELSE
        ld ix,-n
        add ix,sp
        ld sp,ix
      ENDIF
    ELSE
        HCALL RST_ENTER, H_ENTER
        db n
    ENDIF
    ENDM

; function epilogue (return value in HL): drop locals, restore IX, return
    MACRO EPILOGUE n
    IF FORM == 0
        ld sp,ix
      IF n > 0
        IF n <= 8
          DUP n/2
            pop bc
          EDUP
        ELSE
            ex de,hl
            ld hl,n
            add hl,sp
            ld sp,hl
            ex de,hl
        ENDIF
      ENDIF
        pop ix
        ret
    ELSE
        HCALL RST_LEAVE, H_LEAVE
        db n
    ENDIF
    ENDM

; an early `return` (not the function's last statement)
    MACRO RETJ n, epi
    IF FORM == 0
        jp epi
    ELSE
        HCALL RST_LEAVE, H_LEAVE
        db n
    ENDIF
    ENDM

; HL = word at (HL)
    MACRO LDIND
    IF FORM == 0
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
    ELSE
        HCALL RST_LDI, H_LDI
    ENDIF
    ENDM

; word at (DE) = HL, HL keeps the value (assignment expression value)
    MACRO STIND
    IF FORM == 0
        ex de,hl
        ld (hl),e
        inc hl
        ld (hl),d
        ex de,hl
    ELSE
        HCALL RST_STI, H_STI
    ENDIF
    ENDM

; signed compare: carry set iff DE < HL (DE = left operand, HL = right operand)
    MACRO CMPLT
    IF FORM == 0
        ld a,d
        xor $80
        ld d,a
        ld a,h
        xor $80
        ld h,a
        ex de,hl
        or a
        sbc hl,de
    ELSE
        call H_CMPLT
    ENDIF
    ENDM
