; ============================================================================
; include/leapc_tokens.inc -- token kinds of the Leap-C lexer (spec.md section 4.1)
;
; One byte per kind (TOK_KIND). The numbering is part of the lexer's contract with the parser and
; with tools/clex.py (the host reference lexer), which mirrors it; change both together.
;
;   $00-$04  EOF, identifier, number, string, end of line
;   $10-$1C  punctuators with no longer form
;   $20-$2D  operators that have an `op=` form; the `op=` token is the operator + TK_ASSIGN_OFS
;   $30-$35  doubled and other multi-character punctuators
;   $40-$4D  the `op=` forms (== != <= >= and the compound assignments)
;   $60-$7F  keywords, in alphabetical order (the order of LEX_KW_TABLE)
; ============================================================================

    IFNDEF LEAPC_TOKENS_INC
    DEFINE LEAPC_TOKENS_INC

TK_EOF          EQU $00
TK_IDENT        EQU $01     ; TOK_BUF/TOK_LEN = name (first 31 characters)
TK_NUM          EQU $02     ; TOK_VAL = value; TF_UNSIGNED, TF_CHARCONST
TK_STR          EQU $03     ; TOK_BUF/TOK_LEN = decoded bytes (no terminator)
TK_EOL          EQU $04     ; only when LEX_MODE has LM_EOL (preprocessor directives)

; punctuators with no longer form (order = LEX_PUNCT_CHARS)
TK_LPAREN       EQU $10     ; (
TK_RPAREN       EQU $11     ; )
TK_LBRACK       EQU $12     ; [
TK_RBRACK       EQU $13     ; ]
TK_LBRACE       EQU $14     ; {
TK_RBRACE       EQU $15     ; }
TK_COMMA        EQU $16     ; ,
TK_SEMI         EQU $17     ; ;
TK_COLON        EQU $18     ; :
TK_QUEST        EQU $19     ; ?
TK_TILDE        EQU $1A     ; ~
TK_DOT          EQU $1B     ; .
TK_HASH         EQU $1C     ; #

; operators with an op= form (order = LEX_PUNCT_CHARS, then the two shifts)
TK_ASSIGN       EQU $20     ; =
TK_NOT          EQU $21     ; !
TK_LT           EQU $22     ; <
TK_GT           EQU $23     ; >
TK_STAR         EQU $24     ; *
TK_SLASH        EQU $25     ; /
TK_PERCENT      EQU $26     ; %
TK_PLUS         EQU $27     ; +
TK_MINUS        EQU $28     ; -
TK_AMP          EQU $29     ; &
TK_CARET        EQU $2A     ; ^
TK_BAR          EQU $2B     ; |
TK_SHL          EQU $2C     ; <<
TK_SHR          EQU $2D     ; >>

TK_ANDAND       EQU $30     ; &&
TK_OROR         EQU $31     ; ||
TK_INC          EQU $32     ; ++
TK_DEC          EQU $33     ; --
TK_ARROW        EQU $34     ; ->
TK_ELLIPSIS     EQU $35     ; ...

TK_ASSIGN_OFS   EQU $20     ; op= = op + TK_ASSIGN_OFS
TK_EQ           EQU TK_ASSIGN + TK_ASSIGN_OFS   ; ==
TK_NE           EQU TK_NOT + TK_ASSIGN_OFS      ; !=
TK_LE           EQU TK_LT + TK_ASSIGN_OFS       ; <=
TK_GE           EQU TK_GT + TK_ASSIGN_OFS       ; >=
TK_MULASSIGN    EQU TK_STAR + TK_ASSIGN_OFS     ; *=
TK_DIVASSIGN    EQU TK_SLASH + TK_ASSIGN_OFS    ; /=
TK_MODASSIGN    EQU TK_PERCENT + TK_ASSIGN_OFS  ; %=
TK_ADDASSIGN    EQU TK_PLUS + TK_ASSIGN_OFS     ; +=
TK_SUBASSIGN    EQU TK_MINUS + TK_ASSIGN_OFS    ; -=
TK_ANDASSIGN    EQU TK_AMP + TK_ASSIGN_OFS      ; &=
TK_XORASSIGN    EQU TK_CARET + TK_ASSIGN_OFS    ; ^=
TK_ORASSIGN     EQU TK_BAR + TK_ASSIGN_OFS      ; |=
TK_SHLASSIGN    EQU TK_SHL + TK_ASSIGN_OFS      ; <<=
TK_SHRASSIGN    EQU TK_SHR + TK_ASSIGN_OFS      ; >>=

; keywords: C89, alphabetical (LEX_KW_TABLE order)
TK_KW_FIRST     EQU $60
TK_AUTO         EQU $60
TK_BREAK        EQU $61
TK_CASE         EQU $62
TK_CHAR         EQU $63
TK_CONST        EQU $64
TK_CONTINUE     EQU $65
TK_DEFAULT      EQU $66
TK_DO           EQU $67
TK_DOUBLE       EQU $68     ; reserved: "not supported" (parser)
TK_ELSE         EQU $69
TK_ENUM         EQU $6A
TK_EXTERN       EQU $6B
TK_FLOAT        EQU $6C     ; reserved: "not supported" (parser)
TK_FOR          EQU $6D
TK_GOTO         EQU $6E
TK_IF           EQU $6F
TK_INT          EQU $70
TK_LONG         EQU $71     ; reserved: "not supported" (parser)
TK_REGISTER     EQU $72
TK_RETURN       EQU $73
TK_SHORT        EQU $74
TK_SIGNED       EQU $75
TK_SIZEOF       EQU $76
TK_STATIC       EQU $77
TK_STRUCT       EQU $78
TK_SWITCH       EQU $79
TK_TYPEDEF      EQU $7A
TK_UNION        EQU $7B     ; reserved: "not supported" (parser)
TK_UNSIGNED     EQU $7C
TK_VOID         EQU $7D
TK_VOLATILE     EQU $7E     ; reserved: "not supported" (parser)
TK_WHILE        EQU $7F
TK_KW_COUNT     EQU 32

; TOK_FLAGS bits
TF_BOL          EQU 0       ; the token is the first on its source line
TF_UNSIGNED     EQU 1       ; TK_NUM: the constant has type unsigned int
TF_CHARCONST    EQU 2       ; TK_NUM: written as a character constant

; LEX_MODE bits
LM_EOL          EQU 0       ; return TK_EOL at each line end (preprocessor directive lines)

IDENT_SIG_LEN   EQU 31      ; significant identifier characters (spec.md section 4.1)

    ENDIF
