; ============================================================================
; src/compiler/codegen.asm -- native code generation (spec.md 5.4-5.5; project_plan.md M1.3)
;
; Single pass, no IR: the expression parser (expr.asm) calls these routines as it recognises each
; operation, and they emit the mixed template set straight into the image: inline frame, global
; and constant access, `add hl,de`, increments, unsigned compares, byte loads and stores; RST
; helpers for word access through pointers (LDI/STI), frames (ENTER/LEAVE) and signed compares
; (CMPLT); CALL helpers for multiply, divide, variable shifts and calls through pointers.
;
; Run-time registers: HL the operand being computed, DE the second operand, BC scratch, IX the
; frame. An operand descriptor (X, Y; include/leapc_decl.inc) is deferred (no code yet: OK_CONST
; .. OK_FUNC) or resident (code emitted: OK_LVAL, OK_RVAL in HL, OK_COND in the flags).
;
; Held operands. While the right operand of an operator is parsed, a resident left operand stays
; in HL (CG_PEND = 1, CX_HOLD). The first instruction emitted after that pushes it (CG_UNIT); the
; operator then finds it on the stack (`pop de`). If the right operand needs no code before the
; operator, `ex de,hl` replaces the push and pop. A held operand is always the newest resident
; one, so the run-time stack follows the parse.
;
; Code regions (spec.md 3.2). Code grows up from the low end of an image region and static data
; down from its high end (IMG_LIM). Each instruction starts with CG_UNIT, which reserves CG_GUARD
; bytes (IMG_LIM low = CG_PC + CG_GUARD), so data allocated meanwhile never meets the code, and
; continues the code in the next region with room, linked by `jp`, when the current one is full.
;
; Fixup chains. A jump to a label not yet placed, and a reference to a function not yet defined,
; is emitted with the previous reference's address as its operand. Resolving a chain walks it and
; writes the address. A chain ends with a value below LEAPC_IMG4_BASE, where no code or data lies:
; 0 for a label, the line of the first use for a function (E_UNDEFFN reports that line).
;
; Muted code (CX_NOEVAL > 0: sizeof, the unused operand of a constant ?: && ||, the counting pass
; of an initialiser) is parsed and typed but emits nothing and links no chain.
;
; Floats (Phase 8): a float value is in F_ACC, a held one in a 3-word stack slot; loads, stores and
; the operations are calls of src/runtime/float.asm (`call F_LD`, `call F_LDX / db d`,
; `call F_LDK / 5 bytes`, `call F_OP / db op`, ...).
; ============================================================================

CG_GUARD        EQU 12          ; a unit (at most 8 bytes) + a spilled push + the linking `jp`

; ============================================================================
; CG_UNIT -- start an instruction (or a unit of at most 8 bytes emitted with CG_B): room in the
; code region, then the push of a held operand (CG_PEND). A full region is left with a `jp` to the
; next region with room (at the start, the dummy region IMG_LIM0 is left that way: its `jp` lands
; in the dummy cells).
; Errors: E_TOOBIG (no image region has room)
; Destroys: F (A, BC, DE, HL kept)
; ============================================================================
CG_UNIT:
    push af
    ld   a, (CX_NOEVAL)
    or   a
    jr   nz, .muted
    push bc
    push de
    push hl
.room:
    ld   hl, (CG_PC)
    ld   de, CG_GUARD
    add  hl, de
    ex   de, hl                        ; DE = CG_PC + CG_GUARD
    ld   bc, (CG_RLIM)                 ; BC -> the code region's [low][high]
    ld   h, b
    ld   l, c
    inc  hl
    inc  hl
    rst  $08                          ; LDI: HL = high (C is clear from the add)
    sbc  hl, de
    jr   c, .chain
    ld   a, e
    ld   (bc), a
    inc  bc
    ld   a, d
    ld   (bc), a                       ; low = CG_PC + CG_GUARD: reserved for the code
    ld   hl, CG_PEND
    xor  a
    or   (hl)
    jr   z, .done
    ld   (hl), 0
    ld   a, $E5                        ; push hl: the held operand
    call CG_B
.done:
    pop  hl
    pop  de
    pop  bc
.muted:
    pop  af
    ret
.chain:                                ; full: after the linking jp it is data space again
    ld   hl, (CG_PC)
    inc  hl
    inc  hl
    inc  hl
    ld   a, l
    ld   (bc), a
    inc  bc
    ld   a, h
    ld   (bc), a
.next:                                 ; BC -> low + 1 of a region without room
    inc  bc
    inc  bc
    inc  bc                            ; -> the next region's low
    ld   hl, -(IMG_LIM + 4 * IMG_REGIONS)
    add  hl, bc
    jp   c, CC_E_TOOBIG                ; no region left
    ld   h, b
    ld   l, c
    ld   e, (hl)
    inc  hl
    ld   d, (hl)                       ; DE = low
    inc  hl
    rst  $08                          ; LDI: HL = high
    or   a
    sbc  hl, de
    ld   a, h
    or   a
    jr   nz, .found
    ld   a, l
    cp   CG_GUARD
    jr   nc, .found
    inc  bc
    jr   .next
.found:
    ld   hl, (CG_PC)                   ; jp the new region
    ld   (hl), $C3
    inc  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d
    ld   (CG_PC), de
    ld   (CG_RLIM), bc
    ld   hl, 0
    ld   (CG_TAILEND), hl              ; a droppable tail cannot span regions
    jr   .room

; ============================================================================
; CG_B -- emit byte A (a later byte of the current unit). Muted: nothing
; CG_OP -- emit opcode A: a new instruction (CG_UNIT first)
; Destroys: F
; CG_OPW -- emit opcode A and the word HL (`ld hl,nn`, `call nn`, ...)
; CG_W -- emit the word HL
; Destroys: AF
; ============================================================================
CG_OP:
    call CG_UNIT
CG_B:
    push hl
    ld   hl, CX_NOEVAL
    inc  (hl)
    dec  (hl)
    jr   nz, .muted
    ld   hl, (CG_PC)
    ld   (hl), a
    inc  hl
    ld   (CG_PC), hl
.muted:
    pop  hl
    ret
CG_OPW:
    call CG_OP
CG_W:
    ld   a, l
    call CG_B
    ld   a, h
    jr   CG_B

; ============================================================================
; CG_SEQ -- emit a template as one unit: HL -> [length][bytes] (at most 8)
; CG_SEQ0 -- the same inside the current unit
; Destroys: AF, B, HL
; ============================================================================
CG_SEQ:
    call CG_UNIT
CG_SEQ0:
    ld   b, (hl)
.byte:
    inc  hl
    ld   a, (hl)
    call CG_B
    djnz .byte
    ret

; ============================================================================
; CG_FRAME -- emit `DD A C`: an (ix+d) instruction with second byte A and displacement C
; Destroys: AF
; ============================================================================
CG_FRAME:
    push af
    ld   a, $DD
    call CG_OP
    pop  af
    call CG_B
    ld   a, c
    jr   CG_B

; ============================================================================
; CG_JP -- emit `jp` (A = $C3) or `jp cc` (A = $C2 + 8 * cc) to a label not yet placed
; In:  HL = the label's chain (0 = no jump to it yet)
; Out: HL = the chain with this jump (unchanged when muted)
; Destroys: AF, DE
; ============================================================================
CG_JP:
    call CG_OP
    ld   de, (CG_PC)
    call CG_W                          ; the operand links to the previous jump
    ld   a, (CX_NOEVAL)
    or   a
    ret  nz
    ex   de, hl
    ret

; ============================================================================
; CG_HERE -- place a label here: resolve chain HL to CG_PC
; CG_PATCH -- resolve chain HL to the address DE
; Destroys: AF, BC, HL (DE kept)
; ============================================================================
CG_HERE:
    ld   de, (CG_PC)
    xor  a
    ld   (CG_LASTLV + 1), a            ; code can arrive here: a final LEAVE is needed
CG_PATCH:
    ld   a, h
    cp   LEAPC_IMG4_BASE >> 8
    ret  c                             ; the end of the chain
    ld   c, (hl)
    inc  hl
    ld   b, (hl)
    ld   (hl), d
    dec  hl
    ld   (hl), e
    ld   h, b
    ld   l, c
    jr   CG_PATCH

; ============================================================================
; CG_FLINK -- the word to store at DE for the address of a function
; In:  HL = the function's file-scope entry, DE = where the word goes
; Out: HL = the address if the function is defined, else the function's chain, which now starts
;      at DE (its first link: the current line). Muted: no link
; Destroys: AF, BC (DE kept)
; CG_FUNCOP -- emit opcode A with the address of function HL (`call f`, `ld hl,f`)
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_FUNCOP:
    call CG_OP
    ld   de, (CG_PC)
    call CG_FLINK
    jr   CG_W
CG_FLINK:
    ld   bc, S_VAL
    add  hl, bc
    ld   c, (hl)
    inc  hl
    ld   b, (hl)                       ; BC = the address, or the chain
    dec  hl
    dec  hl
    dec  hl
    dec  hl                            ; -> flags
    bit  SF_DEFINED, (hl)
    jr   nz, .word
    ld   a, (CX_NOEVAL)
    or   a
    jr   nz, .word
    inc  hl
    inc  hl
    inc  hl
    ld   (hl), e
    inc  hl
    ld   (hl), d                       ; the chain starts here now
    ld   a, b
    or   c
    jr   nz, .word
    ld   bc, (TOK_LINE)                ; the first use: the chain ends with its line
.word:
    ld   h, b
    ld   l, c
    ret

; ============================================================================
; CG_FLOAD -- X, a float constant or object, into F_ACC (Phase 8): `call F_LDK / 5 bytes`,
; `ld hl,nn / call F_LD`, `call F_LDX / db d`, or the address in HL and `call F_LD`. X = OK_RVAL
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_FLOAD:
    ld   a, (X_KIND)
    or   a
    jr   z, .const
    cp   OK_LVALF
    call z, CG_NEAR                    ; a far frame object: its address (OK_LVAL)
    ld   a, (X_KIND)
    ld   hl, F_LDX
    cp   OK_LVALF
    jr   z, .frame
    cp   OK_LVALC
    ld   hl, (X_VAL)
    ld   a, $21                        ; ld hl,nn
    call z, CG_OPW
    ld   a, (X_KIND)
    cp   OK_LVAL
    call z, CG_LVADDR
    ld   hl, F_LD
    call CG_CALL
    jr   .rval
.frame:
    call CG_CALL
    ld   a, (X_VAL)
    call CG_B
    jr   .rval
.const:
    ld   hl, F_LDK
    call CG_CALL
    ld   hl, (X_VAL)
    ld   b, FLOAT_SIZE
.k:
    ld   a, (hl)
    call CG_B
    inc  hl
    djnz .k
.rval:
    jp   CX_SET_RVAL

; ============================================================================
; CG_VAL -- X a value in HL unless it is a constant
; CG_LOAD -- X a value in HL (OK_RVAL): the deferred load, the load through the address in HL,
; or a condition made 0/1. A byte object is zero- or sign-extended by its type (spec.md 5.1)
; Errors: E_TOOBIG
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_VAL:
    ld   a, (X_KIND)
    cp   OK_LVALC
    ret  c
CG_LOAD:
    ld   a, (X_KIND)
    cp   OK_RVAL
    ret  z
    jr   nc, .cond
    call CX_XFLT
    jr   z, CG_FLOAD
    ld   a, (X_KIND)
    ld   hl, (X_VAL)
    cp   OK_LVALC
    jr   c, .const
    jr   z, .static
    cp   OK_FUNC
    jr   z, .func
    cp   OK_LVALF
    call z, CG_NEAR                    ; a far frame object becomes OK_LVAL
    ld   a, (X_KIND)
    cp   OK_LVAL
    jr   z, .via
    ld   a, (X_VAL)                    ; ld l,(ix+d) [ ld h,(ix+d+1) ]
    ld   c, a
    ld   a, $6E
    call CG_FRAME
    call CG_XBYTE
    jr   c, .ext
    inc  c
    ld   a, $66
    call CG_FRAME
    jr   .rval
.via:                                  ; ld l,(hl) / rst LDI
    call CG_LVADDR
    call CG_XBYTE
    ld   a, $CF                        ; rst LDI
    jr   nc, .op
    ld   a, $6E                        ; ld l,(hl)
    call CG_OP
    jr   .ext
.static:                               ; ld hl,(nn)
    ld   a, $2A
    call CG_OPW
    call CG_XBYTE
    jr   nc, .rval
.ext:                                  ; a byte in L: extended by its type
    ld   hl, (X_TYPE)
    call TY_CLASS
    call CG_EXT
    jr   .rval
.func:                                 ; ld hl,f
    ld   a, $21
    call CG_FUNCOP
    jr   .rval
.cond:                                 ; ld hl,0 / jr !cc,$+3 / inc l
    ld   hl, 0
.const:                                ; ld hl,nn
    ld   a, $21
    call CG_OPW
    ld   a, (X_KIND)
    cp   OK_COND
    jr   nz, .rval
    ld   a, (X_VAL)
    xor  1
    add  a, a
    add  a, a
    add  a, a
    add  a, $20                        ; jr !cc
    call CG_B
    ld   a, 1
    call CG_B
    ld   a, $2C                        ; inc l
    call CG_B
    jr   .rval
.op:
    call CG_OP
.rval:
    jp   CX_SET_RVAL

; CG_XBYTE / CG_YBYTE -- C if X / Y has a byte type (char, signed char). Destroys: AF, HL
CG_YBYTE:
    ld   hl, (Y_TYPE)
    jr   CG_BYTE
CG_XBYTE:
    ld   hl, (X_TYPE)
CG_BYTE:
    call TY_CLASS
    dec  a
    cp   2
    ret

; ============================================================================
; CG_EXT -- extend L into HL for the type class A: char `ld h,0`, signed char `ld a,l / rla /
; sbc a,a / ld h,a`; other classes nothing
; CG_EXT0 -- the same inside the current unit
; Destroys: AF, B, HL
; ============================================================================
CG_EXT:
    call CG_UNIT
CG_EXT0:
    ld   hl, TPL_ZEXT
    cp   TC_CHAR
    jp   z, CG_SEQ0
    ld   hl, TPL_SEXT
    cp   TC_SCHAR
    ret  nz
    jp   CG_SEQ0

; ============================================================================
; CG_NEAR -- X is OK_LVALF: if the object (d..d+1) is beyond (ix+d)'s reach (-128..127), its
; address is emitted and X becomes OK_LVAL (CG_FADDR)
; CG_FADDR -- X is OK_LVALF: emit its address (push ix / pop hl / ld bc,d / add hl,bc): OK_LVAL
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_NEAR:
    ld   hl, (X_VAL)
    ld   de, 128
    add  hl, de
    ld   a, h
    or   a
    jr   nz, CG_FADDR
    ld   a, l
    inc  a
    ret  nz                            ; d + 1 <= 127
CG_FADDR:
    ld   hl, TPL_IXHL
    call CG_SEQ
    ld   hl, (X_VAL)
    call CG_W
    ld   a, $09                        ; add hl,bc
    call CG_B
    ld   hl, 0
    ld   (X_VAL), hl
    ld   a, OK_LVAL
    ld   (X_KIND), a
    ret

; ============================================================================
; CG_LVADDR -- X is OK_LVAL: add its offset (member offsets so far) to HL; X_VAL = 0
; CG_ADDK -- emit HL += DE, a constant: `inc hl` / `dec hl` up to 3 times, else `ld bc,k /
; add hl,bc` (DE stays free for an operand). CG_ADDK0: inside the current unit
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_LVADDR:
    ld   de, (X_VAL)
    ld   hl, 0
    ld   (X_VAL), hl
CG_ADDK:
    ld   a, d
    or   e
    ret  z
    call CG_UNIT
CG_ADDK0:
    ld   hl, 3
    add  hl, de
    ld   a, h
    or   a
    jr   nz, .bc
    ld   a, l
    cp   7
    jr   nc, .bc
    sub  3                             ; A = k, -3..3
    ret  z
    ld   b, $23                        ; inc hl
    jp   p, .rep
    neg
    ld   b, $2B                        ; dec hl
.rep:
    ld   c, a
.one:
    ld   a, b
    call CG_B
    dec  c
    jr   nz, .one
    ret
.bc:
    ld   a, $01                        ; ld bc,k
    call CG_B
    ex   de, hl
    call CG_W
    ld   a, $09                        ; add hl,bc
    jp   CG_B

; ============================================================================
; CG_MULK -- emit HL *= DE, a constant: nothing (1), up to 4 `add hl,hl` (2-16), or
; `ld de,k / call RT_MUL`
; CG_DIVK -- emit HL /= DE, a constant element size (pointer differences: exact, signed):
; nothing for 1, else `ex de,hl / ld hl,k / call RT_DIVS`
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_MULK:
    ld   a, d
    or   e
    jr   z, .call
    ld   h, d
    ld   l, e
    ld   b, 0
.even:                                 ; k = odd * 2^B
    bit  0, l
    jr   nz, .odd
    srl  h
    rr   l
    inc  b
    jr   .even
.odd:
    dec  hl
    ld   a, h
    or   l
    jr   nz, .call                     ; not a power of 2
    ld   a, b
    cp   5
    jr   nc, .call
    or   a
    ret  z                             ; * 1
    call CG_UNIT
.add:
    ld   a, $29                        ; add hl,hl
    call CG_B
    djnz .add
    ret
.call:
    ex   de, hl
    ld   a, $11                        ; ld de,k
    call CG_OPW
    ld   hl, RT_MUL
    jr   CG_CALL
CG_DIVK:
    ld   a, d
    or   a
    jr   nz, .call
    ld   a, e
    dec  a
    ret  z                             ; / 1
.call:
    push de
    ld   a, $EB                        ; ex de,hl
    call CG_OP
    pop  hl
    ld   a, $21                        ; ld hl,k
    call CG_OPW
    ld   hl, RT_DIVS
; CG_CALL -- emit `call HL`. Destroys: AF
CG_CALL:
    ld   a, $CD
    jp   CG_OPW

; ============================================================================
; CG_JTRUE / CG_JFALSE -- jump to a label when X (a value) is true / false
; In:  HL = the label's chain
; Out: HL = the chain with the jump (a constant: an unconditional jump, or none); X = OK_COND
;      (unless constant)
; Destroys: AF, BC, DE
; CG_TEST -- X (a value) as a condition: X = OK_COND; A = the condition that means true
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_JTRUE:
    ld   b, 0
    jr   CG_JCOND
CG_JFALSE:
    ld   b, 1
CG_JCOND:
    push hl
    call CX_TRUTH                      ; C: a constant, A = its truth
    pop  hl
    jr   nc, .test
    xor  b                             ; 1: it jumps
    ret  z
    ld   a, $C3
    jp   CG_JP
.test:
    push hl
    push bc
    call CG_TEST
    pop  bc
    xor  b                             ; jump on false: the opposite condition
    add  a, a
    add  a, a
    add  a, a
    add  a, $C2                        ; jp cc
    pop  hl
    jp   CG_JP
CG_TEST:
    ld   a, (X_KIND)
    cp   OK_COND
    ld   a, (X_VAL)
    ret  z
    call CG_LOAD
    call CX_XFLT
    jr   z, .flt
    ld   hl, TPL_TEST                  ; ld a,h / or l
    call CG_SEQ
    jr   .nz
.flt:                                  ; a float (Phase 8): Z if F_ACC is 0
    ld   hl, F_TST
    call CG_CALL
.nz:
    xor  a                             ; NZ: true
; CG_SETCOND -- X = OK_COND with the condition A. Out: A kept. Destroys: F
CG_SETCOND:
    ld   (X_VAL), a
    push af
    ld   a, OK_COND
    ld   (X_KIND), a
    pop  af
    ret

; ============================================================================
; CG_BINOP -- code for Y op X: two values, not both constant (CX_BINOP folds those)
; In:  CX_OP = the operator token (not && ||), C = 1 for an unsigned operation
; Out: X = OK_RVAL (HL), or OK_COND (a comparison)
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_BINOP:
    ld   a, c
    ld   (CG_UNS), a
    ld   a, (X_KIND)
    cp   OK_LVALC
    jr   nc, .xvar
    call CG_YHL                        ; the right operand is a constant k
    ld   de, (X_VAL)
    ld   a, (CX_OP)
    cp   TK_PLUS
    jr   z, .addk
    cp   TK_MINUS
    jr   z, .subk
    cp   TK_STAR
    jr   z, .mulk
    cp   TK_EQ
    jr   z, .eqk
    cp   TK_NE
    jr   nz, .genk
.eqk:
    ld   a, d
    or   e
    jr   nz, .genk
    ld   hl, TPL_TEST                  ; == 0, != 0: ld a,h / or l
    call CG_SEQ
    ld   a, (CX_OP)
    sub  TK_EQ
    xor  1                             ; == : Z (1), != : NZ (0)
    jr   CG_SETCOND
.genk:                                 ; ld de,k: HL = left, DE = right
    ex   de, hl
    ld   a, $11
    call CG_OPW
    ld   b, 1
    jr   .op
.subk:
    call NEG_DE
.addk:
    call CG_ADDK
    jp   .rval
.mulk:
    call CG_MULK
    jp   .rval
.xvar:                                 ; the right operand is not constant
    ld   a, (Y_KIND)
    cp   OK_LVAL
    jr   c, .ydef
    call CG_YDE                        ; the left operand is held
    jr   .normal
.ydef:                                 ; the left operand is deferred
    call CG_LOAD
    ld   a, (Y_KIND)
    cp   OK_LVALC
    jr   nc, .yload
    ld   hl, (Y_VAL)                   ; a constant: ld de,k
    ld   a, $11
    call CG_OPW
.normal:                               ; DE = left, HL = right
    ld   b, 0
    jr   .op
.yload:                                ; ex de,hl, then the left operand: HL = left, DE = right
    ld   a, $EB
    call CG_OP
    call CG_LOADY
    ld   b, 1
.op:                                   ; B = 1: swapped (HL = left, DE = right)
    ld   a, (CX_OP)
    cp   TK_PLUS
    jr   z, .add
    cp   TK_MINUS
    jr   z, .sub
    ld   hl, TPL_AND
    cp   TK_AMP
    jr   z, .seq
    ld   hl, TPL_OR
    cp   TK_BAR
    jr   z, .seq
    ld   hl, TPL_XOR
    cp   TK_CARET
    jr   z, .seq
    ld   hl, CG_HTAB - 5
    ld   c, a
.helper:                               ; * / % << >>: CALL helpers (DE = left, HL = right)
    inc  hl
    inc  hl
    inc  hl
    inc  hl
    inc  hl
    ld   a, (hl)
    or   a
    jr   z, CG_CMP
    cp   c
    jr   nz, .helper
    ld   a, c
    cp   TK_STAR
    jr   z, .comm
    ld   a, b
    or   a
    ld   a, $EB                        ; swapped: ex de,hl
    call nz, CG_OP
.comm:
    inc  hl
    ld   a, (CG_UNS)
    add  a, a
    ld   e, a
    ld   d, 0
    add  hl, de
    rst  $08                          ; LDI: HL = (HL)
    call CG_CALL
    jr   .rval
.add:
    ld   a, $19                        ; add hl,de
    call CG_OP
    jr   .rval
.sub:                                  ; or a / sbc hl,de: HL = left - right
    ld   a, b
    or   a
    ld   a, $EB
    call z, CG_OP
    ld   hl, TPL_SBC
.seq:
    call CG_SEQ
.rval:
    jp   CX_SET_RVAL

; CG_CMP -- the comparisons (CG_BINOP; B = 1: swapped): X = OK_COND. Signed < > <= >= use RST
; CMPLT (carry <=> DE < HL), everything else `or a / sbc hl,de` (CG_CMPTAB)
CG_CMP:
    ld   a, c
    cp   TK_EQ
    jr   c, .lg
    sub  TK_EQ - 2
    jr   .row
.lg:
    sub  TK_LT
.row:
    ld   e, a
    ld   d, 0
    ld   hl, CG_CMPTAB
    add  hl, de
    ld   a, (hl)
    ld   e, a
    and  3                             ; the condition
    cp   2
    jr   c, .sbc                       ; == !=
    ld   a, e
    rlca                               ; bit 0: the signed form needs ex de,hl
    xor  b
    ld   hl, CG_UNS
    xor  (hl)                          ; the unsigned form: the opposite
    rra
    ld   a, $EB
    call c, CG_OP
    ld   a, (CG_UNS)
    or   a
    jr   nz, .sbc
    ld   a, $EF                        ; rst CMPLT
    call CG_OP
    jr   .cond
.sbc:
    ld   hl, TPL_SBC
    call CG_SEQ
.cond:
    ld   a, e
    and  3
    jp   CG_SETCOND

; CG_HTAB -- the helper operators: [token][signed helper][unsigned helper], 0 ends
CG_HTAB:
    DB   TK_STAR
    DW   RT_MUL, RT_MUL
    DB   TK_SLASH
    DW   RT_DIVS, RT_DIVU
    DB   TK_PERCENT
    DW   RT_MODS, RT_MODU
    DB   TK_SHL
    DW   RT_SHL, RT_SHL
    DB   TK_SHR
    DW   RT_SAR, RT_SHR
    DB   0
; CG_CMPTAB -- < > == != <= >=: bits 0-1 the condition (0 NZ, 1 Z, 2 NC, 3 C), bit 7 the signed
; form with DE = left, HL = right needs ex de,hl
CG_CMPTAB:
    DB   3, $83, 1, 0, $82, 2

; CG_YHL -- the left operand Y (a value) into HL: it is there (held), on the stack (`pop hl`) or
; deferred (loaded). Destroys: AF, BC, DE, HL
CG_YHL:
    ld   a, (Y_KIND)
    cp   OK_LVAL
    jr   c, CG_LOADY
    ld   hl, CG_PEND
    ld   a, (hl)
    ld   (hl), 0
    or   a
    ret  nz
    ld   a, $E1                        ; pop hl
    jp   CG_OP
; CG_YDE -- Y (a value or an address) is held, in HL (CG_PEND) or pushed: X into HL and Y into
; DE (`ex de,hl` + X, or X + `pop de`). Destroys: AF, BC, DE, HL
CG_YDE:
    ld   hl, CG_PEND
    ld   a, (hl)
    ld   (hl), 0
    or   a
    jr   z, .stacked
    ld   a, $EB                        ; still in HL: ex de,hl
    call CG_OP
    jp   CG_LOAD
.stacked:                              ; pushed: X, then pop de
    call CG_LOAD
    ld   a, $D1
    jp   CG_OP
; CG_LOADY -- Y a value in HL (CG_LOAD on Y). Destroys: AF, BC, DE, HL
CG_LOADY:
    call CX_SWAP
    call CG_LOAD
    jp   CX_SWAP

; ============================================================================
; CX_SWAPCG -- exchange X and Y (CX_SWAP), keeping the held-operand state right: the held one is
; always the left operand Y
; Destroys: AF, BC, DE, HL
; ============================================================================
CX_SWAPCG:
    ld   a, (Y_KIND)
    cp   OK_LVAL
    jr   nc, .yres
    call CX_SWAP
    ld   a, (Y_KIND)
    cp   OK_LVAL
    ret  c
    ld   a, 1                          ; the operand in HL is now the left one: held
    ld   (CG_PEND), a
    ret
.yres:
    ld   hl, CG_PEND
    ld   a, (hl)
    ld   (hl), 0
    push af
    call CX_SWAP
    pop  af
    or   a
    ret  nz                            ; it was in HL: now the right (current) operand
    ld   a, $E3                        ; pushed: ex (sp),hl
    jp   CG_OP

; ============================================================================
; CG_STORE -- store the value X into the object Y: OK_LVALC, a near OK_LVALF, or OK_LVAL whose
; address is held (in HL: CG_PEND, else on the stack). Out: X = OK_RVAL, the value in HL
; Destroys: AF, BC, DE, HL
; ============================================================================
CG_STORE:
    ld   hl, (Y_TYPE)
    call TY_CLASS
    cp   TC_FLOAT
    jr   z, CG_FSTORE
    ld   a, (Y_KIND)
    cp   OK_LVAL
    jr   nz, .direct
    call CG_YDE                        ; the value in HL, the address in DE
    call CG_YBYTE
    ld   a, $D7                        ; rst STI
    jp   nc, CG_OP
    ld   hl, TPL_STDE                  ; ld a,l / ld (de),a
    jp   CG_SEQ
.direct:
    call CG_LOAD
    call CG_YBYTE
    push af                            ; C: a byte object
    ld   hl, (Y_VAL)
    ld   a, (Y_KIND)
    cp   OK_LVALC
    jr   nz, .frame
    pop  af
    ld   a, $22                        ; ld (nn),hl
    jp   nc, CG_OPW
    ld   a, $7D                        ; ld a,l / ld (nn),a
    call CG_OP
    ld   a, $32
    jp   CG_OPW
.frame:                                ; ld (ix+d),l [ / ld (ix+d+1),h ]
    ld   c, l
    ld   a, $75
    call CG_FRAME
    pop  af
    ret  c
    inc  c
    ld   a, $74
    jp   CG_FRAME
; CG_FSTORE -- the float object Y = X (a float value: the caller converts it; Phase 8): `call F_ST`
; with the address in HL (`ld hl,nn`, or held: `pop hl`), or `call F_STX / db d`. Out: X = OK_RVAL,
; the value in F_ACC. Destroys: AF, BC, DE, HL
CG_FSTORE:
    call CG_LOAD
    ld   a, (Y_KIND)
    cp   OK_LVAL
    jr   nz, .direct
    call CG_YHL                        ; the address
    jr   .st
.direct:
    ld   hl, (Y_VAL)
    cp   OK_LVALC
    jr   nz, .frame
    ld   a, $21                        ; ld hl,nn
    call CG_OPW
.st:
    ld   hl, F_ST
    call CG_CALL
    jr   .rval
.frame:
    ld   hl, F_STX
    call CG_CALL
    ld   a, (Y_VAL)
    call CG_B
.rval:
    jp   CX_SET_RVAL

; ============================================================================
; CG_PUSHX -- push the value X: `push hl`, or a float's 3-word slot (`call F_PUSH`; Phase 8). CX_PEND
; counts the words: at most LEAPC_ARGS_MAX (spec.md 4.10; else E_NESTING)
; Out: A = the words. Destroys: AF, BC, DE, HL
; CG_FOP -- emit `call F_OP / db A` (an operation of the float core; Phase 8). Destroys: AF, HL
; ============================================================================
CG_PUSHX:
    call CG_LOAD
    call CX_XFLT
    jr   z, .float
    ld   a, $E5                        ; push hl
    call CG_OP
    ld   b, 1
    jr   .count
.float:
    ld   hl, F_PUSH
    call CG_CALL
    ld   b, 3
.count:
    ld   hl, CX_PEND
    ld   a, (hl)
    add  a, b
    ld   (hl), a
    cp   LEAPC_ARGS_MAX + 1
    ld   a, b
    ret  c
    jp   PP_E_NESTING
CG_FOP:
    push af
    ld   hl, F_OP
    call CG_CALL
    pop  af
    jp   CG_B

; ============================================================================
; CG_TAILON -- start code that only computes the value just stored (a new unit; at most 4 bytes
; follow, by CG_B); CG_TAILOFF -- end it. CX_DISCARD drops it when the value is not used
; Destroys: F (CG_TAILON), - (CG_TAILOFF)
; CX_DISCARD -- the value of X is not used
; Destroys: AF, DE, HL
; ============================================================================
CG_TAILON:
    call CG_UNIT
    push hl
    ld   hl, (CG_PC)
    ld   (CG_TAIL), hl
    pop  hl
    ret
CG_TAILOFF:
    push hl
    ld   hl, (CG_PC)
    ld   (CG_TAILEND), hl
    pop  hl
    ret
CX_DISCARD:
    ld   a, (CX_NOEVAL)
    or   a
    ret  nz
    ld   hl, (CG_TAILEND)
    ld   de, (CG_PC)
    sbc  hl, de
    ret  nz
    ld   (CG_TAILEND), hl              ; (0)
    ld   hl, (CG_TAIL)
    ld   (CG_PC), hl
    ret

; NEG_DE -- DE = -DE. Destroys: AF
NEG_DE:
    xor  a
    sub  e
    ld   e, a
    sbc  a, a
    sub  d
    ld   d, a
    ret

; ---- templates: [length][bytes] ----
TPL_ZEXT:   DB 2, $26, $00                      ; ld h,0
TPL_SEXT:   DB 4, $7D, $17, $9F, $67            ; ld a,l / rla / sbc a,a / ld h,a
TPL_IXHL:   DB 4, $DD, $E5, $E1, $01            ; push ix / pop hl / ld bc,(d follows)
TPL_TEST:   DB 2, $7C, $B5                      ; ld a,h / or l
TPL_SBC:    DB 3, $B7, $ED, $52                 ; or a / sbc hl,de
TPL_STDE:   DB 2, $7D, $12                      ; ld a,l / ld (de),a
TPL_AND:    DB 6, $7C, $A2, $67, $7D, $A3, $6F  ; ld a,h / and d / ld h,a / ld a,l / and e / ld l,a
TPL_OR:     DB 6, $7C, $B2, $67, $7D, $B3, $6F
TPL_XOR:    DB 6, $7C, $AA, $67, $7D, $AB, $6F
TPL_AND01:  DB 8, $21, 1, 0, $18, 3, $21, 0, 0  ; ld hl,1 / jr $+5 / ld hl,0 (the false label)
TPL_OR10:   DB 8, $21, 0, 0, $18, 3, $21, 1, 0  ; ld hl,0 / jr $+5 / ld hl,1 (the true label)
