; ============================================================================
; src/test/test_hooks.asm -- test-build-only entry points (-DLEAPC_TEST; project_plan.md 1.3)
;
; Appended after the production code of the HOME image: the production bytes keep their addresses.
; The harness (tools/lcharness.py) calls these with SP = $FF00 and a return slot, as V2's qharness
; does, and stops at the return. Results go to image region 2 (always visible RAM).
; ============================================================================

TEST_AREA       EQU LEAPC_IMG2_BASE
TEST_DUMP_PTR   EQU TEST_AREA           ; 2: next free byte of the token dump
TEST_LEX_MODE   EQU TEST_AREA + 2       ; 1: LEX_MODE to use (written by the harness)
TEST_COUNT      EQU TEST_AREA + 3       ; 2: tokens counted by TEST_LEX_COUNT, incl. EOF
TEST_DUMP_DATA  EQU TEST_AREA + 8       ; token records
TEST_DUMP_LIMIT EQU LEAPC_IMG2_END - (4 + 1 + TOK_BUF_LEN)   ; room for one more record
TEST_E_FULL     EQU $FE                 ; dump buffer full (reported like an error)

; ============================================================================
; TEST_LEX_DUMP -- lex the whole line store into a token dump
; In:  line store; TEST_LEX_MODE
; Out: records from TEST_DUMP_DATA to (TEST_DUMP_PTR):
;        token: [kind][flags][line:2] + TK_NUM: [value:2]; TK_IDENT/TK_STR: [len][bytes];
;               TK_FNUM: [5][its value's 5 bytes] (Phase 8)
;        error: [$FF][error number][line:2] (last record)
;      the token records end with the TK_EOF record unless an error record ends them
; Destroys: everything except IX, IY
; ============================================================================
TEST_LEX_DUMP:
    call BANK_PAGE_EXROM_OUT           ; as the compiler: chunk 6 = RAM
    xor  a
    ld   (CC_ERRNUM), a
    ld   hl, TEST_DUMP_DATA
    ld   (TEST_DUMP_PTR), hl
    call .guarded
    jr   nc, .end
    ld   hl, (TEST_DUMP_PTR)
    ld   (hl), $FF
    inc  hl
    ld   a, (CC_ERRNUM)
    ld   (hl), a
    inc  hl
    ld   de, (CC_ERRLINE)
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    ld   (TEST_DUMP_PTR), hl
.end:
    jp   BANK_PAGE_EXROM_IN
.guarded:
    ld   (CC_SP), sp
    call LEX_INIT
    ld   a, (TEST_LEX_MODE)
    or   1 << LM_RAW                   ; the plain lexer: no preprocessing
    ld   (LEX_MODE), a
.loop:
    call LEX_NEXT
    ld   hl, (TEST_DUMP_PTR)
    ld   de, TEST_DUMP_LIMIT
    or   a
    sbc  hl, de
    add  hl, de
    ld   a, TEST_E_FULL
    jp   nc, CC_ERROR
    ld   a, (TOK_KIND)
    ld   (hl), a
    inc  hl
    ld   a, (TOK_FLAGS)
    ld   (hl), a
    inc  hl
    ld   de, (TOK_LINE)
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    ld   a, (TOK_KIND)
    cp   TK_NUM
    jr   nz, .text
    ld   de, (TOK_VAL)
    ld   (hl), e
    inc  hl
    ld   (hl), d
    inc  hl
    jr   .stored
.text:
    cp   TK_IDENT
    jr   z, .copy
    cp   TK_FNUM
    ld   a, FLOAT_SIZE                 ; a floating constant: its 5 bytes (Phase 8)
    jr   z, .bytes
    ld   a, (TOK_KIND)
    cp   TK_STR
    jr   nz, .stored
.copy:
    ld   a, (TOK_LEN)
.bytes:
    ld   (hl), a
    inc  hl
    or   a
    jr   z, .stored
    ld   c, a
    ld   b, 0
    ex   de, hl
    ld   hl, TOK_BUF
    ldir
    ex   de, hl
.stored:
    ld   (TEST_DUMP_PTR), hl
    ld   a, (TOK_KIND)
    or   a
    jr   nz, .loop
    ret                                ; NC

; ============================================================================
; TEST_LEX_COUNT -- lex the whole line store, counting tokens (throughput measurement)
; In:  line store
; Out: TEST_COUNT = tokens including TK_EOF; CC_ERRNUM = 0 or the error. The harness measures
;      T-states from TEST_LEX_COUNT.t0 to TEST_LEX_COUNT.t1 (interrupts on, as in a compile).
; Destroys: everything except IX, IY
; ============================================================================
TEST_LEX_COUNT:
    call BANK_PAGE_EXROM_OUT
    xor  a
    ld   (CC_ERRNUM), a
    ld   h, a
    ld   l, a
    ld   (TEST_COUNT), hl
.t0:
    call .guarded
.t1:
    jp   BANK_PAGE_EXROM_IN
.guarded:
    ld   (CC_SP), sp
    call LEX_INIT
    ld   a, 1 << LM_RAW                ; the plain lexer (the preprocessor's hook still runs)
    ld   (LEX_MODE), a
.loop:
    call LEX_NEXT
    ld   hl, (TEST_COUNT)
    inc  hl
    ld   (TEST_COUNT), hl
    ld   a, (TOK_KIND)
    or   a
    jr   nz, .loop
    ret
