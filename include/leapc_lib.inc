; ============================================================================
; include/leapc_lib.inc -- the loaded-library ABI (spec.md 7.2; Phase 10), the single source of truth
;
; A library is an assembly image for image region 3 ($F400-$F7FF, 1 KB), loaded from tape by the shell's
; LIB "name" (src/shell/tape.asm SH_LIB). Its functions are bound by the compiler like the built-in
; library's (src/compiler/libnames.asm LIB_FIND: the ROM's table, then the library's) and called with the C
; calling convention (spec.md 5.2). It reaches the ROM's services only through the jump table below, whose
; slots never move, so a library built against this file runs on every ROM with the same ABI or a later one.
;
; Included three ways (V2's package ABI, include/v2_package_abi.inc at the V2 reference tag, as the model):
;   LEAPC_LIB_HOME defined (src/rom/home.asm): LX_SLOT_LIST emits the slots' `jp`s, and LX_PIN_LIST ASSERTs
;       that the ROM's own symbols still have the pinned values;
;   by the EXROM (src/rom/exrom.asm): the constants only (LIB, the binding);
;   by a library's source (tools/lib2tape.py; no ROM include before it): each slot name is its slot's
;       address, each pin its value. A library can name only what is listed here.
;
; RULES: never reorder, remove or repurpose a slot or a pin. A new service takes the next reserved slot
; and raises LX_ABI by one; a library then declares the ABI it needs (its header), and LIB refuses it on a
; ROM with a lower one. Anything else is a new LX_MAGIC: every older library tape is then refused.
; ============================================================================
    IFNDEF LEAPC_LIB_INC
    DEFINE LEAPC_LIB_INC

; ---- the version: the image header's first two bytes, and the tape header's version word ----
LX_MAGIC        EQU $8D     ; bit 7: Leap-tagged; $0D: a Leap-C library (program and data tapes: $8C)
LX_ABI          EQU 1       ; this ROM's ABI: slots 0-13
LX_WORD         EQU LX_MAGIC << 8 | LX_ABI  ; the tape's version word (its header's autostart field)
LX_TYPE         EQU 4       ; the tape header's type (V2's package tapes)

; ---- the image (image region 3) ----
LX_BASE         EQU $F400
LX_END          EQU $F800
LX_HDR_COUNT    EQU LX_BASE + 2     ; the header: [magic][ABI][export count] ...
LX_TABLE        EQU LX_BASE + 3     ; ... then the export table: per function [name][address][signature],
                                    ; the name's last character with bit 7 set (LIB_NAMES's records), then 0
    MACRO LX_HEADER lxcount             ; (macro arguments are substituted inside identifiers too:
    DB   LX_MAGIC, LX_ABI, lxcount      ; hence the unusual names)
    ENDM
    MACRO LX_EXPORT lxname, lxroutine, lxret, lxparams
    DC   lxname
    DW   lxroutine
    DB   lxret << 4 | lxparams
    ENDM
    MACRO LX_EXPORTS_END
    DB   0
    ENDM
LX_EXPORTS_MAX  EQU 99      ; (LIB's report, "LIBRARY name: n FUNCTIONS", fits the row up to 99)

; ---- signatures: [return type:4][parameter list:4] ----
; return types: [pointer:1][base:3] (include/leapc_decl.inc TB_*)
LXR_VOID        EQU 0
LXR_CHAR        EQU 1
LXR_INT         EQU 3
LXR_UINT        EQU 4
LXR_FLOAT       EQU 5       ; the result in F_ACC
LXR_VOIDP       EQU 8
LXR_CHARP       EQU 9
; parameter lists: the ROM's LIB_PARAMS (src/compiler/libnames.asm), never reordered. Integer parameters are
; int, pointers void * (any object pointer converts)
LXP_VARIADIC    EQU 0       ; no prototype: any arguments, the default promotions (a float: a 3-word slot)
LXP_NONE        EQU 1       ; ()
LXP_I           EQU 2       ; (int)
LXP_P           EQU 3       ; (void *)
LXP_II          EQU 4       ; (int, int)
LXP_PI          EQU 5       ; (void *, int)
LXP_PP          EQU 6       ; (void *, void *)
LXP_PPI         EQU 7       ; (void *, void *, int)
LXP_PII         EQU 8       ; (void *, int, int)
LXP_IPI         EQU 9       ; (int, void *, int)
LXP_IIII        EQU 10      ; (int, int, int, int)
LXP_IIIIP       EQU 11      ; (int, int, int, int, void *)
LXP_III         EQU 12      ; (int, int, int)
LXP_IP          EQU 13      ; (int, void *)
LXP_IIP         EQU 14      ; (int, int, void *)
LXP_IIIII       EQU 15      ; (int, int, int, int, int)

; ---- the jump table: 16 slots of `jp` at the end of HOME ($3FD0-$3FFF), never moved ----
; Each slot's contract (In / Out / Destroys) is spec.md 2.4's. An exported function calls LX_ARGS first, so
; that a runtime error or BREAK in it, or in a service it calls, is reported at the program's call.
LX_SLOTS        EQU $3FD0
LX_SLOT_COUNT   EQU 16
LX_SLOT_N       DEFL 0
    MACRO LX_SLOT lxname, lxtarget
    IFDEF LEAPC_LIB_HOME
    ASSERT $ == LX_SLOTS + 3 * LX_SLOT_N, "a library slot moved (include/leapc_lib.inc)"
    jp   lxtarget
    ELSE
lxname EQU LX_SLOTS + 3 * LX_SLOT_N
    ENDIF
LX_SLOT_N       DEFL LX_SLOT_N + 1
    ENDM
    MACRO LX_RESERVED
    IFDEF LEAPC_LIB_HOME
    jp   RT_ERR_ARG                 ; a reserved slot: runtime error 4 at the program's call
    ENDIF
LX_SLOT_N       DEFL LX_SLOT_N + 1
    ENDM
    MACRO LX_SLOT_LIST
LX_SLOT_N       DEFL 0
    LX_SLOT LX_ARGS, LIB_ARGS               ; 0  the arguments; LIB_CALLER = the program's call
    LX_SLOT LX_PUTC, LIB_PUTC               ; 1  a character at the print position
    LX_SLOT LX_PUTS, LIB_PUTS0              ; 2  a string at the print position
    LX_SLOT LX_MALLOC, LIB_MALLOC_HL        ; 3  a heap block
    LX_SLOT LX_FREE, LIB_FREE_HL            ; 4  a heap block freed
    LX_SLOT LX_MUL, RT_MUL                  ; 5  16-bit multiply
    LX_SLOT LX_DIVS, RT_DIVS                ; 6  signed divide
    LX_SLOT LX_DIVU, RT_DIVU                ; 7  unsigned divide and remainder
    LX_SLOT LX_FOP, F_X                     ; 8  an operation of the float core on F_ACC
    LX_SLOT LX_ERROR, RT_LIBERR             ; 9  end the program with a runtime error
    LX_SLOT LX_KEY, IO_READ_KEY             ; 10 wait for a key
    LX_SLOT LX_INKEY, IO_READ_KEY_NONBLOCK   ; 11 the key latched, or 0
    LX_SLOT LX_FRAMES, LIB_FRAMES           ; 12 the frame counter
    LX_SLOT LX_PLOT, LIB_PLOT_HL            ; 13 a pixel in the print attribute and over mode
    LX_RESERVED                             ; 14 reserved
    LX_RESERVED                             ; 15 reserved
    ASSERT LX_SLOT_N == LX_SLOT_COUNT
    ENDM

; ---- pinned RAM cells and constants: a library may use these names ----
    MACRO LX_PIN lxname, lxvalue
    IFDEF LEAPC_LIB_HOME
    ASSERT lxname == lxvalue, "a library ABI pin moved (include/leapc_lib.inc)"
    ELSE
lxname EQU lxvalue
    ENDIF
    ENDM
    MACRO LX_PIN_LIST
    LX_PIN F_ACC, $5ED6             ; the float accumulator (5 bytes): LX_FOP's operand and result
    LX_PIN LIB_COL, $5EC2           ; the print position: column (0-31) ...
    LX_PIN LIB_ROW, $5EC3           ; ... and row (0-23)
    LX_PIN LIB_ATTR, $5EC8          ; the print attribute
    LX_PIN RTE_HEAP, 2              ; runtime errors (LX_ERROR): out of heap ...
    LX_PIN RTE_ARG, 4               ; ... a bad argument ...
    LX_PIN RTE_FLOAT, 6             ; ... a floating overflow
    LX_PIN FOP_FRI, 0               ; float core operations (LX_FOP): F_ACC = HL (int) ...
    LX_PIN FOP_FRU, 1               ; ... HL (unsigned) ...
    LX_PIN FOP_TOI, 2               ; ... HL = F_ACC truncated ...
    LX_PIN FOP_NEG, 3               ; ... F_ACC = -F_ACC ...
    LX_PIN FOP_FTOA, 8              ; ... HL = the text of the float at HL with C decimals ...
    LX_PIN FOP_ADD, $80             ; ... binary: F_ACC = (HL) op F_ACC ...
    LX_PIN FOP_SUB, $82
    LX_PIN FOP_SUBR, $83            ; ... (reversed: F_ACC op (HL)) ...
    LX_PIN FOP_MUL, $84
    LX_PIN FOP_DIV, $86
    LX_PIN FOP_DIVR, $87
    LX_PIN FOP_CMP, $88             ; ... C: (HL) < F_ACC, Z: equal
    ENDM
    IFNDEF LEAPC_ROM_INC                ; (a library's source)
    LX_PIN_LIST
    LX_SLOT_LIST
    ENDIF

    ENDIF
