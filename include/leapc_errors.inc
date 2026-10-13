; ============================================================================
; include/leapc_errors.inc -- compile error numbers (spec.md section 6.3)
;
; Compilation stops at the first error: CC_ERROR records CC_ERRNUM and CC_ERRLINE and unwinds to
; the compile entry (src/compiler/cerror.asm). Numbers are grouped by tens:
;
;     1      not supported (any group)
;    10-19   lexical            50-69   expression        90-99    limit
;    20-39   declaration        70-89   statement         100-109  memory
;    40-49   type
;
; The message texts belong to the EXROM diagnostics component (Phase 6); tools/clex.py mirrors the
; lexical numbers.
; ============================================================================

    IFNDEF LEAPC_ERRORS_INC
    DEFINE LEAPC_ERRORS_INC

E_NOTSUP        EQU 1       ; NOT SUPPORTED (long/float constants here; reserved words in the parser)

; lexical
E_BADCHAR       EQU 10      ; INVALID CHARACTER (outside ASCII 32-126 / not a C token: @ $ `)
E_COMMENT       EQU 11      ; UNTERMINATED COMMENT (reported at the line where it starts)
E_STRING        EQU 12      ; UNTERMINATED STRING (end of line inside "...")
E_CHARCONST     EQU 13      ; BAD CHARACTER CONSTANT (empty, unterminated or more than one char)
E_ESCAPE        EQU 14      ; BAD ESCAPE SEQUENCE (unknown \c, \x without digits, value > 255)
E_NUMBER        EQU 15      ; BAD NUMBER (invalid digit or suffix, 0x without digits)
E_RANGE         EQU 16      ; CONSTANT TOO LARGE (above 65535)
E_TOOLONG       EQU 17      ; TOKEN TOO LONG (string literal beyond TOK_BUF; guard only)

    ENDIF

; ---- runtime errors (spec.md section 5.9) ----
    IFNDEF LEAPC_RTERRORS
    DEFINE LEAPC_RTERRORS
RTE_STACK       EQU 1       ; stack overflow (ENTER)
RTE_HEAP        EQU 2       ; out of heap
RTE_HIRES       EQU 3       ; hi-res mode with the image in $6000-$77FF
RTE_ARG         EQU 4       ; invalid library argument
RTE_BREAK       EQU 5       ; BREAK
    ENDIF
