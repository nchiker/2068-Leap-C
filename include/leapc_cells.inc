; ============================================================================
; include/leapc_cells.inc -- Leap-C fixed RAM cells (spec.md section 3.1: "Leap-C fixed cells")
;
; Placed directly after the relocated platform system variables (LEAPC_SYSVARS_END) and below
; LEAPC_CELLS_LIMIT ($6000). Addresses are computed by the assembler (DEFS chain), as in the
; platform's sysvars.inc. Include after include/sysvars.inc.
; ============================================================================

    IFNDEF LEAPC_CELLS_INC
    DEFINE LEAPC_CELLS_INC
    INCLUDE "include/leapc_decl.inc"

LEAPC_CELLS_RETURN_ORG EQU $
    ORG LEAPC_SYSVARS_END
LEAPC_CELLS_BASE:

; ---- compiler: lexer and source streaming (src/compiler/lexer.asm) ----
TOK_BUF_LEN     EQU 128             ; identifier (31 significant) or decoded string literal
LEX_PTR:        DEFS 2              ; next source byte (line store, or LEX_EOF_BYTE at the end)
LEX_LINE:       DEFS 2              ; 1-based line number of the byte at LEX_PTR
LEX_BOLP:       DEFS 1              ; 1 << TF_BOL while the next token is the first on its line
TOK_PTR:        DEFS 2              ; first source byte of the current token (LEX_MARK, names)
TOK_LINE:       DEFS 2              ; line on which the current token starts
PP_TOKN:        DEFS 1              ; the current token's number in a macro expansion (0: main
                                    ; text); before TOK_FLAGS for LEX_MARK (preproc.asm)
TOK_FLAGS:      DEFS 1              ; TF_* bits (include/leapc_tokens.inc)
TOK_KIND:       DEFS 1              ; current token kind (include/leapc_tokens.inc)
TOK_VAL:        DEFS 2              ; number / character constant value
TOK_LEN:        DEFS 1              ; bytes in TOK_BUF (identifier or string literal)
TOK_BUF:        DEFS TOK_BUF_LEN    ; identifier text or decoded string literal (no terminator)
LEX_MODE:       DEFS 1              ; LM_* bits (include/leapc_tokens.inc)
; ---- preprocessor (Phase 2: src/compiler/preproc.asm) ----
PP_MAX          EQU 8               ; macros nested in one expansion
PP_LEVEL        EQU 9               ; bytes per PP_STACK level
PP_SP:          DEFS 2              ; the next free PP_STACK level (= PP_STACK: the main text)
PP_STACK:       DEFS PP_LEVEL * PP_MAX ; per level: LEX_PTR, LEX_LINE, LEX_BOLP and TOK_PTR as at
                                    ; the macro's name, then the macro (preproc.asm)
    ASSERT LEX_LINE == LEX_PTR + 2 && LEX_BOLP == LEX_PTR + 4 && TOK_PTR == LEX_PTR + 5

; ---- compiler: declarations, symbols, constant expressions (M1.2) ----
; CC_COMPILE zeroes CC_CELLS_BEGIN..CC_CELLS_END before every compile.
CC_CELLS_BEGIN:
WS_LOC:         DEFS 2              ; first free byte of the local area (grows up from PROG_END)
SYM_GLO:        DEFS 2              ; newest file-scope symbol entry (0 = none)
SYM_LOC:        DEFS 2              ; newest block- or prototype-scope symbol entry (0 = none)
SCOPE_BASE:     DEFS 2              ; WS_LOC when the innermost scope opened; 0 = file scope
NM_PTR:         DEFS 2              ; the name being declared or looked up (source text) ...
NM_LEN:         DEFS 1              ; ... and its length (0 = no name)
LASTP_HEAD:     DEFS 2              ; the last parameter list parsed: its newest entry ...
LASTP_END:      DEFS 2              ; ... the end of its entries (FUNC_DEF reopens it) ...
LASTP_NODE:     DEFS 2              ; ... and its function node (0 at the start of a declaration)
FRAME_OFS:      DEFS 2              ; next free frame offset of the function being compiled
FRAME_MAX:      DEFS 2              ; frame size so far (the largest FRAME_OFS)
ST_HEAD:        DEFS 2              ; struct being defined: first member ...
ST_TAIL:        DEFS 2              ; ... last member ...
ST_SIZE:        DEFS 2              ; ... and size so far
DS_SC:          DEFS 1              ; DECL_SPECS: storage class (SC_*) ...
DS_CONST:       DEFS 1              ; ... const seen ...
DS_MASK:        DEFS 1              ; ... type specifier bits seen
X_KIND:         DEFS 1              ; expression operand: OK_* ...
X_TYPE:         DEFS 2              ; ... type ...
X_VAL:          DEFS 2              ; ... value, address, displacement or offset ...
X_FLAGS:        DEFS 1              ; ... X_FLAGS_CONST (X is saved as three words)
Y_KIND:         DEFS 1              ; left operand of a binary operator (same layout as X)
Y_TYPE:         DEFS 2
Y_VAL:          DEFS 2
Y_FLAGS:        DEFS 1
CX_NOEVAL:      DEFS 1              ; > 0: operands are not evaluated (sizeof, initialiser count pass)
CX_OP:          DEFS 1              ; CX_BINOP: the operator
CELLS_RET:      DEFS 2              ; CELLS_SAVE / CELLS_LOAD: their return address
IL_ADDR:        DEFS 2              ; INIT_LIST (saved around nested lists): next element's
                                    ; address (arrays) or the struct's address ...
IL_ELEM:        DEFS 2              ; ... element type (arrays) or the next member (structs) ...
IL_ESIZE:       DEFS 2              ; ... element size (0: a struct) ...
IL_LEFT:        DEFS 2              ; ... elements left ($FFFF - given for `[]`) ...
IL_BRACED:      DEFS 2              ; ... nonzero: the list is in braces
IL_CELLS        EQU IL_ADDR
IL_WORDS        EQU 5
IMG_LIM0:       DEFS 4              ; a full dummy region before region 1: the code starts here, so
                                    ; its first unit moves to region 1 (CG_UNIT; nothing else uses it)
IMG_LIM:        DEFS 4 * IMG_REGIONS ; per image region: [low:2][high:2]; static data grows down
WS_GLO:         DEFS 2              ; lowest byte of the global area (grows down from LEAPC_SRC_TOP)
; ---- code generation (M1.3: src/compiler/codegen.asm) ----
CG_PC:          DEFS 2              ; next code byte (CC_COMPILE: IMG_LIM0) ...
CG_RLIM:        DEFS 2              ; ... in the region whose IMG_LIM entry this points at
CG_PEND:        DEFS 1              ; nonzero: HL holds a held operand (CG_UNIT pushes it first)
CG_PENDSV:      DEFS 1              ; CG_PEND when the outermost muted part began (CX_MUTE)
CG_UNS:         DEFS 1              ; CG_BINOP: 1 = unsigned operation
CG_TAIL:        DEFS 2              ; code CX_DISCARD may drop: from CG_TAIL ...
CG_TAILEND:     DEFS 2              ; ... to CG_TAILEND (when nothing was emitted after it)
CG_LASTLV:      DEFS 2              ; CG_PC right after the last `rst LEAVE` (0: none since a label)
CG_ENTN:        DEFS 2              ; the current function's ENTER operand (its frame size)
FN_RET:         DEFS 2              ; the current function's return type
CX_PEND:        DEFS 1              ; CX_CALL: argument words pushed and not yet popped by the calls
                                    ; being compiled (at most LEAPC_ARGS_MAX with the current call's)
CX_ARGN:        DEFS 1              ; CX_CALL (saved around each argument): arguments left ...
CX_ARGT:        DEFS 1              ; ... arguments in all ...
CX_PARAMP:      DEFS 2              ; ... next parameter type (0: no prototype) ...
CX_FRET:        DEFS 2              ; ... the function's return type
CX_CALLW        EQU 3               ; (words from CX_ARGN)
RUN_MAIN:       DEFS 2              ; main's address (0: none), set at the end of a compile
RUN_VOID:       DEFS 1              ; nonzero: main returns void (exit status 0)
; ---- statements (Phase 2: src/compiler/stmt.asm) ----
; Chains are fixup chains (codegen.asm); 1 is an empty chain, 0 means "no such statement open".
SW_CASES:       DEFS 2              ; switch: its case records [link][value][address] (global area) ...
SW_DEFAULT:     DEFS 2              ; ... its default's address (1: none yet; 0: no switch open) ...
BRK_CH:         DEFS 2              ; ... the break chain of the innermost loop or switch (0: none)
CNT_CH:         DEFS 2              ; the continue chain of the innermost loop (0: none)
FN_LABELS:      DEFS 2              ; the labels of the function being compiled (global area)
DCL_LINE:       DEFS 2              ; the line of the declaration being parsed (its first token)
RUN_FNLINES:    DEFS 2              ; the function -> line table: newest record [link][address][line]
                                    ; (static data in the image; spec.md 5.9)
PP_MACROS:      DEFS 2              ; newest macro definition (global area; 0: none;
                                    ; src/compiler/preproc.asm)
PM_LEN          EQU 2               ; macro record: [link][name length][name][replacement]
PM_NAME         EQU 3
PM_TEXT         EQU 5
PM_SIZE         EQU 7
CC_CELLS_END:

; ---- compiler: error exit (src/compiler/cerror.asm) ----
CC_SP:          DEFS 2              ; SP to restore on a compile error (set by the compile entry)
CC_ERRNUM:      DEFS 1              ; 0 = no error, else E_* (include/leapc_errors.inc)
CC_ERRLINE:     DEFS 2              ; source line of the error (1-based)

; ---- runtime (src/runtime/rtexit.asm, library.asm; spec.md 5.7-5.9, 7) ----
RUN_SP:         DEFS 2              ; SP to restore when a program ends (its return into RT_RUN)
RUNNING:        DEFS 1              ; nonzero while a program runs: BREAK ends it (spec.md 5.8)
; RT_RUN clears RT_STATE .. RT_STATE_END at every program start
RT_STATE:
RT_ERRNUM:      DEFS 1              ; 0, or the program's runtime error (spec.md 5.9) ...
RT_ERRPC:       DEFS 2              ; ... an address in the code that failed ...
RT_ERRLINE:     DEFS 2              ; ... and the line where its function's definition starts (0: unknown)
BRK_HALT:       DEFS 1              ; nonzero: BREAK requested during a NOBRK section (platform: VM_HALTED,
                                    ; which ends AY_WAIT_FRAMES early)
NOBRK:          DEFS 1              ; > 0: BREAK waits for the end of the section (EXROM trampolines)
LIB_CALLER:     DEFS 2              ; the program's address of the last library call (errors, BREAK)
LIB_RND:        DEFS 2              ; rand()'s state (0 = the sequence of srand(1))
LIB_COL:        DEFS 1              ; the print position: column (0-31) ...
LIB_ROW:        DEFS 1              ; ... and row (0-23)
LIB_INVF:       DEFS 1              ; inverse(): 1 = ink and paper swapped for printing and plotting
LIB_OVERF:      DEFS 1              ; over(): 1 = characters and pixels are XORed onto the screen
LIB_CHBUF:      DEFS 2              ; a one-character string (LIB_PUTC; the second byte stays 0)
RT_STATE_END:
LIB_ATTR:       DEFS 1              ; the attribute: flash, bright, paper, ink (RT_RUN: ATTR_DEFAULT)
LIB_FMT:        DEFS 2              ; printf: the next format character ...
LIB_AP:         DEFS 2              ; ... and the next argument
LIB_PTR:        DEFS 2              ; LIB_UTOA: the text
LIB_NUM:        DEFS 7              ; printf: the text of a number (at most "-32768") or a character
    ASSERT LIB_ROW == LIB_COL + 1 && LIB_OVERF == LIB_INVF + 1

; ---- editor engine selective redraw (platform rom/exrom_editor.asm, V2_FAST_REDRAW) ----
; V2 placed these at $BEC0-$BEC5 (rom/v2_exrom.asm), which is source RAM in the Leap-C map.
V2_REDRAW_SCOPE: DEFS 1             ; 1 = only the active line changed
V2_RD_WRAPS:    DEFS 1              ; wrap-row count of the active line at the last redraw
V2_RD_INDEX:    DEFS 2              ; CUR_EDIT_INDEX at the last redraw
V2_RD_NEWROW:   DEFS 1              ; scratch of the two-line path
V2_RD_NEWH:     DEFS 1

LEAPC_CELLS_END:
    ASSERT LEAPC_CELLS_END <= LEAPC_CELLS_LIMIT
    ORG LEAPC_CELLS_RETURN_ORG

; Platform name for the BREAK request (rom/v2_ay_beep.asm: AY_WAIT_FRAMES ends early).
VM_HALTED       EQU BRK_HALT

    ENDIF
