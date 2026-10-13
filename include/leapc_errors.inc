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
; The message texts belong to the EXROM diagnostics component (Phase 6); tools/clex.py and the
; test runner read the numbers from this file.
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

; declaration
E_SYNTAX        EQU 20      ; SYNTAX ERROR (a token that cannot appear here)
E_REDECL        EQU 21      ; REDECLARED (the name is already declared differently in this scope)
E_REDEF         EQU 22      ; ALREADY DEFINED (second body, initialiser or struct/enum definition)
E_UNDECL        EQU 23      ; UNDECLARED IDENTIFIER
E_TYPESPEC      EQU 24      ; BAD TYPE SPECIFIERS (e.g. `int char`, `signed unsigned`, `int T`)
E_BADDECL       EQU 25      ; BAD DECLARATOR (array of functions, function returning an array or a
                            ;   function, void parameter or member, function definition here)
E_STORAGE       EQU 26      ; BAD STORAGE CLASS (two classes, auto at file scope, typedef = ...)
E_PARAM         EQU 27      ; BAD PARAMETER (unnamed parameter in a function definition)
E_INIT          EQU 28      ; BAD INITIALISER (too many elements, string too long, braces missing)
E_ARRAYSIZE     EQU 29      ; BAD ARRAY SIZE (zero or negative)

; type
E_TYPE          EQU 40      ; TYPE MISMATCH (conflicting declarations, incompatible initialiser)
E_INCOMPLETE    EQU 41      ; INCOMPLETE TYPE (void object, undefined struct, `[]` without size)
E_TOOLARGE      EQU 42      ; TYPE TOO LARGE (an object of more than 65535 bytes)

; expression
E_CONSTEXPR     EQU 50      ; CONSTANT EXPRESSION REQUIRED
E_OPERAND       EQU 51      ; BAD OPERAND TYPE (e.g. `*` of an int, `.` of a non-struct)
E_MEMBER        EQU 52      ; NO SUCH MEMBER
E_LVALUE        EQU 53      ; NOT AN LVALUE (`&` of a value, assignment to a value)
E_CONST         EQU 54      ; ASSIGNMENT TO CONST (a const object assigned or incremented)
E_ARGS          EQU 55      ; WRONG NUMBER OF ARGUMENTS (call of a prototyped function)

; statement and function
E_UNDEFFN       EQU 70      ; UNDEFINED FUNCTION (called or used, never defined; line of first use)
E_NOMAIN        EQU 71      ; NO MAIN FUNCTION (RUN)

; limit
E_NESTING       EQU 90      ; NESTING TOO DEEP (compiler stack guard; more than 15 `*`)
E_FRAME         EQU 91      ; FRAME TOO LARGE (more than 255 bytes of locals; spec.md 4.10)
E_PARAMS        EQU 92      ; TOO MANY PARAMETERS (more than 16; spec.md 4.10)

; memory
E_NOMEM         EQU 100     ; OUT OF MEMORY (compile workspace full)
E_TOOBIG        EQU 101     ; PROGRAM TOO BIG (image regions full)

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
