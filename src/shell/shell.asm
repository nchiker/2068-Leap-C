; ============================================================================
; src/shell/shell.asm -- the Leap-C shell (EXROM; spec.md 6.1; project_plan.md Phase 5)
;
; Adapted from Leap V2's shell glue (rom/exrom_v2_shell.asm at the V2 reference tag v2.0.1-emu.1,
; copied, not imported: platform/UPSTREAM.md). Kept from V2, routine by routine (the V2 name is in
; each header): the command loop; storing the edit buffer; navigation that keeps an uncommitted
; edit, with insert and delete line; the redraw with V2's flicker safeguards (only the active
; line's rows while typing, only the two lines involved in a one-line move); the status row
; ("LINE n/m" and the colour swatch); the error-line jump; LIST; the startup chime (V2's chord).
; Not carried over (BASIC only): the tokenizer stage, keyword spans, variable sessions and
; immediate statements, arrays and the Array Store, packages, SAVE ... ALL.
; Changed for C:
;   - a settled line's C keywords are drawn bold as typed (src/shell/highlight.asm; V2 showed its
;     keywords in upper case);
;   - the view keeps the whole cursor line on the screen when the lines above it wrap onto more
;     than one row each (V2 always showed the 20 lines above it, which could push it off);
;   - RUN compiles (SH_COMPILE in HOME: chunk 6 paged out) and runs (RT_RUN); a compile error, a
;     runtime error or BREAK comes back to the editor on the line, with a report on the status row;
;   - LIST never splits a line across two pages.
; Phase 6 adds the error texts, the run reports and FREE; Phase 7 adds SAVE, LOAD and VERIFY.
;
; The shell runs with the EXROM paged in (BANK_EXROM_DEPTH 1): chunk-6 RAM is invisible to it.
; It calls HOME directly (the platform, LEX_KEYWORD, RT_RUN) and compiles through SH_COMPILE.
; ============================================================================

; ============================================================================
; SHELL_COLD -- shell cold entry (HOME COLD_START jumps here through LEAPC_EXROM_SHELL)
; SH_LOOP -- the command loop: edit a line; on ENTER store it, or run the command typed on the
; append line (V2_COMMAND_LOOP)
; In:  chunk 6 = EXROM (BANK_EXROM_DEPTH 1), interrupts on, an empty line store
; Out: does not return
; ============================================================================
SHELL_COLD:
    call SH_RESET_EDIT
    call STARTUP_CHIME
SH_LOOP:
    ld   a, 7
    call GFX_SET_BORDER                ; white (a program may change it; RT_RUN leaves it)
    call EDITOR_INIT
    ld   hl, SH_REDRAW
    ld   (EDITOR_REDRAW_HOOK), hl
    ld   hl, SH_NAV
    ld   (EDITOR_NAV_HOOK), hl
    call SH_LOAD_EDIT
SH_REENTER:
    call EDITOR_ENTER                  ; edits until ENTER (the first redraw is a full one)
    ld   a, (EDIT_LINE_BUF)
    or   a
    jr   z, SH_LOOP                    ; an empty line: nothing to store
    call SH_POS_IS_APPEND
    jr   nz, .store
    call SH_DISPATCH                   ; the append line: a command?
    jr   nc, SH_LOOP
.store:
    call SH_STORE_EDIT
    jr   c, .full
    call SH_POS_IS_APPEND
    jr   nz, .advance
    call SH_COUNT_LINES                ; appended: the cursor stays on the (new) append line
    ld   (CUR_EDIT_INDEX), de
    jr   SH_LOOP
.advance:                              ; a line replaced: the cursor goes to the next one
    ld   hl, (CUR_EDIT_INDEX)
    inc  hl
    ld   (CUR_EDIT_INDEX), hl
    call SH_SET_EDIT_FROM_INDEX
    jr   SH_LOOP
.full:
    ld   hl, SH_MSG_FULL
    call SH_SHOW_MESSAGE
    jr   SH_REENTER                    ; the typed line stays in the buffer (V2 D9b)

; ============================================================================
; SH_DISPATCH -- run the command on the append line: RUN, LIST or NEW, in any case, alone on the
; line apart from spaces (V2_DISPATCH)
; Out: NC: a command ran (the line is not stored). C: not a command
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_DISPATCH:
    ld   de, SH_KW_RUN
    call SH_MATCH
    jr   nc, .run
    ld   de, SH_KW_LIST
    call SH_MATCH
    jr   nc, .list
    ld   de, SH_KW_NEW
    call SH_MATCH
    ret  c
    call MEM_INIT                      ; NEW: an empty line store
    call SH_RESET_EDIT
    or   a
    ret
.list:
    call SH_LIST
    or   a
    ret
.run:
    call SH_RUN
    or   a
    ret

; ============================================================================
; SH_MATCH -- is the edit buffer the command named at DE (upper case), in any case, followed only
; by spaces? (V2_MATCH_EXACT, V2_MATCH_PREFIX)
; Out: NC: yes. Destroys: AF, B, DE, HL
; ============================================================================
SH_MATCH:
    ld   hl, EDIT_LINE_BUF
.char:
    ld   a, (de)
    or   a
    jr   z, .tail
    ld   b, a
    ld   a, (hl)
    cp   'a'
    jr   c, .cmp
    cp   'z' + 1
    jr   nc, .cmp
    sub  32                            ; upper case
.cmp:
    cp   b
    jr   nz, .fail
    inc  hl
    inc  de
    jr   .char
.tail:
    ld   a, (hl)
    inc  hl
    or   a
    ret  z                             ; (carry clear)
    cp   ' '
    jr   z, .tail
.fail:
    scf
    ret

; ============================================================================
; SH_RUN -- RUN: compile the program and, if it compiles, run it (spec.md 1, 6.3)
; A compile error puts the cursor on its line and reports "ERROR n LINE m". The program runs on a
; cleared screen; when it ends the screen stays until a key. A runtime error reports "RUNTIME
; ERROR n" and BREAK "BREAK", with " LINE m" and the cursor on the line where the definition of
; the function that failed starts, where known (spec.md 5.9). Phase 6 adds the error texts and
; the reports (exit status, image size, free heap).
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_RUN:
    call SH_COMPILE                    ; HOME: CC_PROGRAM with chunk 6 = RAM
    jr   nc, .compiled
    ld   hl, (CC_ERRLINE)
    ld   a, (CC_ERRNUM)
    ld   de, SH_MSG_ERROR
    jr   .report
.compiled:
    call GFX_CLS
    call RT_RUN                        ; A = 0 (HL = the exit status), or A = the runtime error
    ld   b, a
    xor  a
    ld   (KBD_KEYHIT), a               ; a key the program left (BREAK) does not end the wait
    or   b
    jr   z, SH_WAIT_KEY                ; it ended: its screen stays until a key
    ld   hl, (RT_ERRLINE)
    ld   de, SH_MSG_RUNTIME
    cp   RTE_BREAK
    jr   nz, .report
    ld   de, SH_MSG_BREAK
    xor  a                             ; (no number)
.report:                               ; A = the error (0: none), DE = the text, HL = the line (0: unknown)
    ld   (SH_ERR_LINE), hl
    ex   de, hl
    ld   de, SH_STATUS_BUF
    push af
    call SH_APPEND
    pop  af
    or   a
    jr   z, .line
    ld   l, a
    ld   h, 0
    ld   a, ' '
    ld   (de), a
    inc  de
    call SH_APPEND_NUM
.line:
    ld   hl, (SH_ERR_LINE)
    ld   a, h
    or   l
    jr   z, .show
    push de
    call SH_JUMP_TO_LINE               ; the cursor on the line, its text in the edit buffer
    pop  de
    ld   hl, SH_TXT_LINE
    call SH_APPEND
    ld   hl, (SH_ERR_LINE)
    call SH_APPEND_NUM
.show:
    ld   hl, SH_STATUS_BUF
    ; falls into SH_SHOW_MESSAGE

; ============================================================================
; SH_SHOW_MESSAGE -- show the text at HL on the status row and wait for a key; the next redraw is a
; full one (V2_SHOW_MESSAGE)
; SH_WAIT_KEY -- wait for a key
; Out: carry clear. Destroys: AF, BC, DE, HL
; ============================================================================
SH_SHOW_MESSAGE:
    xor  a
    ld   (V2_REDRAW_SCOPE), a
    call SH_STATUS_ROW
SH_WAIT_KEY:
    call IO_READ_KEY
    or   a
    ret

; ============================================================================
; SH_STATUS_ROW -- the text at HL on row 23 in the status bar's colours: white on black, with V2's
; red, green and blue swatch in columns 29-31 (V2_STATUS_SET_BAR_ATTR). The bitmap is cleared
; without touching the attributes, against flicker
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_STATUS_ROW:
    push hl
    ld   a, 23
    call SH_CLEAR_ROW
    pop  hl
    ld   bc, 23 * 256
    call GFX_PRINT_STRING
    ld   hl, ATTR_ADDR + 23 * 32
    ld   b, 29
.bar:
    ld   (hl), $07                     ; paper 0, ink 7
    inc  hl
    djnz .bar
    ld   (hl), $10                     ; paper 2 (red)
    inc  hl
    ld   (hl), $20                     ; paper 4 (green)
    inc  hl
    ld   (hl), $08                     ; paper 1 (blue)
    ret

; ============================================================================
; SH_DRAW_STATUS -- "LINE n/m" on the status row: the cursor's line and the lines in the source
; (V2_DRAW_STATUS)
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_DRAW_STATUS:
    ld   de, SH_STATUS_BUF
    ld   hl, SH_TXT_LINE + 1           ; "LINE "
    call SH_APPEND
    ld   hl, (CUR_EDIT_INDEX)
    inc  hl
    call SH_APPEND_NUM
    ld   a, '/'
    ld   (de), a
    inc  de
    ld   hl, (SH_LINE_COUNT)
    call SH_APPEND_NUM
    ld   hl, SH_STATUS_BUF
    jr   SH_STATUS_ROW

; ============================================================================
; SH_APPEND_NUM -- append the decimal text of HL (signed) at DE
; SH_APPEND -- append the NUL-terminated text at HL at DE
; Out: DE -> the NUL written after it. Destroys: AF, BC, HL
; ============================================================================
SH_APPEND_NUM:
    push de
    ex   de, hl
    call BASIC_NUM_TO_STRING_EXROM     ; HL -> its text (PRINT_BUF)
    pop  de
SH_APPEND:
    ld   a, (hl)
    ld   (de), a
    or   a
    ret  z
    inc  hl
    inc  de
    jr   SH_APPEND

; ============================================================================
; SH_LIST -- LIST: the source a page at a time, keywords bold. A line that does not fit on the
; page starts the next one: a key shows it, BREAK ends the listing; a key ends it (V2_LIST)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_LIST:
    call .page
    call MEM_LINE_FIRST
.line:
    ld   a, h
    or   l
    jr   z, SH_WAIT_KEY
    ld   (SH_CMD_PTR), hl
    call SH_SETTLED                    ; HL = TOKEN_BUF
    push hl
    call EDITOR_WRAP_CALC
    pop  hl
    ld   a, (EDIT_WRAP_COUNT)
    ld   b, a
    ld   a, (SH_DRAW_ROW)
    add  a, b
    cp   24
    jr   c, .fits                      ; its rows end above the status row
    push hl
    call IO_READ_KEY
    pop  hl
    cp   KEY_BREAK
    ret  z
    push hl
    call .page
    pop  hl
.fits:
    call SH_DRAW_NEXT
    ld   hl, (SH_CMD_PTR)
    call MEM_LINE_NEXT
    jr   .line
.page:
    call GFX_CLS
    xor  a
    ld   (SH_DRAW_ROW), a
    ret

; ============================================================================
; SH_STORE_EDIT -- store the edit buffer as the cursor's line (replacing it), or after the last
; line from the append line (V2_STORE_EDIT, V2_TOKENIZE: the record [length][text][CR] is built
; in TOKEN_BUF)
; Out: C: no room (PROGRAM FULL; nothing changed). Destroys: AF, BC, DE, HL
; ============================================================================
SH_STORE_EDIT:
    ld   hl, EDIT_LINE_BUF
    ld   de, TOKEN_BUF + 2
    ld   bc, 1                         ; the record's length: the text and its CR
.copy:
    ld   a, (hl)
    or   a
    jr   z, .end
    ld   (de), a
    inc  hl
    inc  de
    inc  c
    jr   .copy
.end:
    ld   a, $0D                        ; CR ends a record
    ld   (de), a
    ld   (TOKEN_BUF), bc
    call SH_POS_IS_APPEND
    jr   nz, .at
    ld   hl, (PROG_END)
.at:
    ld   de, TOKEN_BUF
    jp   MEM_LINE_STORE

; ============================================================================
; SH_POS_IS_APPEND -- Z: the cursor is on the append line (CUR_EDIT_POS = $FFFF) (V2_POS_IS_APPEND)
; Out: HL = CUR_EDIT_POS. Destroys: AF
; ============================================================================
SH_POS_IS_APPEND:
    ld   hl, (CUR_EDIT_POS)
    ld   a, h
    cp   $FF
    ret

; ============================================================================
; SH_RESET_EDIT -- the cursor on the append line of line 0 (V2_RESET_EDIT)
; Destroys: HL
; ============================================================================
SH_RESET_EDIT:
    ld   hl, $FFFF
    ld   (CUR_EDIT_POS), hl
    inc  hl
    ld   (CUR_EDIT_INDEX), hl
    ld   (VIEW_TOP_INDEX), hl
    ret

; ============================================================================
; SH_COUNT_LINES -- the lines in the source (V2_COUNT_LINES)
; Out: DE = the count. Destroys: AF, BC, HL
; ============================================================================
SH_COUNT_LINES:
    call MEM_LINE_FIRST
    ld   de, 0
.loop:
    ld   a, h
    or   l
    ret  z
    inc  de
    push de
    call MEM_LINE_NEXT
    pop  de
    jr   .loop

; ============================================================================
; SH_FIND_INDEX -- the record of line DE (0-based) (V2_FIND_INDEX)
; Out: HL = the record, or 0 when there is no such line. Destroys: AF, BC, DE
; ============================================================================
SH_FIND_INDEX:
    push de
    call MEM_LINE_FIRST
    pop  de
.loop:
    ld   a, d
    or   e
    ret  z
    ld   a, h
    or   l
    ret  z
    dec  de
    push de
    call MEM_LINE_NEXT
    pop  de
    jr   .loop

; ============================================================================
; SH_JUMP_TO_LINE -- the cursor to source line HL (1-based; one beyond the last: the append line)
; and its text into the edit buffer (V2_JUMP_TO_ERROR_LINE)
; SH_SET_EDIT_FROM_INDEX -- the same for line CUR_EDIT_INDEX (0-based) (V2_SET_EDIT_FROM_INDEX)
; SH_LOAD_EDIT -- the edit buffer from the cursor's line (empty on the append line), the cursor at
; its start (V2_LOAD_EDIT)
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_JUMP_TO_LINE:
    dec  hl
    ld   (CUR_EDIT_INDEX), hl
SH_SET_EDIT_FROM_INDEX:
    ld   de, (CUR_EDIT_INDEX)
    call SH_FIND_INDEX
    ld   a, h
    or   l
    jr   nz, .found
    dec  hl                            ; $FFFF: the append line
.found:
    ld   (CUR_EDIT_POS), hl
SH_LOAD_EDIT:
    ld   de, EDIT_LINE_BUF
    xor  a
    ld   (de), a
    call SH_POS_IS_APPEND
    call nz, SH_COPY_TEXT
    ld   hl, 0
    ld   (EDIT_BUF_OFFSET), hl
    ret

; ============================================================================
; SH_COPY_TEXT -- copy a record's text (127 characters at most) to DE with a NUL (V2_COPY_RECORD)
; In:  HL = the record. Out: DE -> the NUL. Destroys: AF, B, HL
; ============================================================================
SH_COPY_TEXT:
    inc  hl
    inc  hl
    ld   b, EDIT_LINE_BUF_LEN - 1
.copy:
    ld   a, (hl)
    cp   $0D
    jr   z, .end
    ld   (de), a
    inc  hl
    inc  de
    djnz .copy
.end:
    xor  a
    ld   (de), a
    ret

; ============================================================================
; SH_SETTLED -- a settled (not edited) line ready to draw: its text in TOKEN_BUF with its C
; keywords marked (SH_KW_MARK)
; In:  HL = the record. Out: HL = TOKEN_BUF. Destroys: AF, BC, DE
; ============================================================================
SH_SETTLED:
    ld   de, TOKEN_BUF
    call SH_COPY_TEXT
    ld   hl, TOKEN_BUF
    push hl
    call SH_KW_MARK
    pop  hl
    ret

; ============================================================================
; SH_NAV -- the editor engine's navigation hook (EDITOR_NAV_HOOK; V2_NAV)
; In:  A = EDIR_UP, EDIR_DOWN (between the screen rows of a wrapped line, else to the line above or
;      below: an edit is stored first, SH_NAV_COMMIT), EDIR_DELETE_LINE (CAPS SHIFT + 1; DELETE on
;      an empty line) or EDIR_INSERT_LINE (CAPS SHIFT + ENTER: a blank line before this one)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_NAV:
    cp   EDIR_DELETE_LINE
    jr   z, .delete
    cp   EDIR_INSERT_LINE
    jr   z, .insert
    cp   EDIR_UP
    jr   z, .wrap_up
    cp   EDIR_DOWN
    ret  nz
    call .rowcol                       ; DOWN: the next screen row of a wrapped line ...
    ld   a, (EDIT_WRAP_COUNT)
    dec  a
    cp   b
    jr   z, .down                      ; ... from its last row, the next line
    inc  b
    jr   .setrow
.wrap_up:
    call .rowcol
    ld   a, b
    or   a
    jr   z, .up
    dec  b
.setrow:
    call EDITOR_WRAP_ROWCOL_TO_OFFSET
    ld   (EDIT_BUF_OFFSET), a
    xor  a
    ld   (EDIT_BUF_OFFSET + 1), a
    ret
.rowcol:                               ; B, C = the cursor's row and column in its line
    ld   hl, EDIT_LINE_BUF
    call EDITOR_WRAP_CALC
    jp   EDITOR_WRAP_OFFSET_TO_ROWCOL
.down:
    call SH_COUNT_LINES
    ld   hl, (CUR_EDIT_INDEX)
    or   a
    sbc  hl, de
    ret  nc                            ; the append line: nothing below it
    call SH_NAV_COMMIT
    ret  c
    ld   hl, (CUR_EDIT_INDEX)
    inc  hl
    jr   .go
.up:
    ld   hl, (CUR_EDIT_INDEX)
    ld   a, h
    or   l
    ret  z
    call SH_NAV_COMMIT
    ret  c
    ld   hl, (CUR_EDIT_INDEX)
    dec  hl
.go:
    ld   (CUR_EDIT_INDEX), hl
    jp   SH_SET_EDIT_FROM_INDEX
.delete:
    call SH_POS_IS_APPEND
    ret  z
    ld   d, h
    ld   e, l
    call MEM_LINE_DELETE_RANGE
    call SH_COUNT_LINES
    ld   hl, (CUR_EDIT_INDEX)
    or   a
    sbc  hl, de
    jr   c, .reload
    ld   (CUR_EDIT_INDEX), de          ; the last line went: the append line
.reload:
    jp   SH_SET_EDIT_FROM_INDEX
.insert:
    call SH_POS_IS_APPEND
    ret  z
    call SH_NAV_COMMIT
    ret  c
    ld   hl, (CUR_EDIT_POS)
    ld   de, SH_BLANK_RECORD
    call MEM_LINE_INSERT
    ret  c
    jp   SH_LOAD_EDIT
SH_BLANK_RECORD:
    DB   1, 0, $0D

; ============================================================================
; SH_NAV_COMMIT -- before the cursor leaves a line: store the edit buffer if it is not empty and
; differs from the stored line (or the line is the append line), as ENTER would (V2_NAV_COMMIT)
; Out: C: PROGRAM FULL (reported; the buffer and the cursor stay). After storing on the append
; line, CUR_EDIT_INDEX is the new append line's
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_NAV_COMMIT:
    ld   a, (EDIT_LINE_BUF)
    or   a
    ret  z                             ; empty: nothing to keep (carry clear)
    call SH_POS_IS_APPEND
    jr   z, .differs
    inc  hl
    inc  hl
    ld   de, EDIT_LINE_BUF
.cmp:
    ld   a, (de)
    or   a
    jr   z, .end
    cp   (hl)
    jr   nz, .differs
    inc  hl
    inc  de
    jr   .cmp
.end:
    ld   a, (hl)
    cp   $0D
    ret  z                             ; unchanged (carry clear)
.differs:
    call SH_STORE_EDIT
    jr   c, .full
    xor  a
    ld   (V2_REDRAW_SCOPE), a          ; the line count may change: a full redraw
    ld   hl, (CUR_EDIT_POS)
    ld   a, h
    inc  a
    ret  nz                            ; (carry clear)
    call SH_COUNT_LINES
    ld   (CUR_EDIT_INDEX), de
    or   a
    ret
.full:
    ld   hl, SH_MSG_FULL
    call SH_SHOW_MESSAGE
    scf
    ret

; ============================================================================
; SH_REDRAW -- the editor engine's redraw hook (EDITOR_REDRAW_HOOK; V2_REDRAW): the source from
; VIEW_TOP_INDEX (SH_VIEW) on rows 0-22, settled lines with their keywords bold, the cursor's line
; from the edit buffer (plain), the status row, the cursor. V2_REDRAW_SCOPE (set by the engine)
; selects a selective redraw: 1 = typing (SH_REDRAW_ACTIVE), 2 = UP/DOWN (SH_REDRAW_NAV); each
; falls back to the full redraw when it cannot prove that nothing else moves
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_REDRAW:
    ld   a, (V2_REDRAW_SCOPE)
    or   a
    jr   z, .full
    ld   b, a
    xor  a
    ld   (V2_REDRAW_SCOPE), a
    djnz .nav
    call SH_REDRAW_ACTIVE
    ret  nc
    jr   .full
.nav:
    call SH_REDRAW_NAV
    ret  nc
.full:
    call GFX_CLS
    call SH_COUNT_LINES
    ld   (SH_LINE_COUNT), de
    call SH_VIEW
    ld   de, (VIEW_TOP_INDEX)
    call SH_FIND_INDEX
    xor  a
    ld   (SH_DRAW_ROW), a
.record:
    ld   a, h
    or   l
    jr   z, .sentinel
    ld   (SH_CMD_PTR), hl
    ld   de, (CUR_EDIT_POS)
    or   a
    sbc  hl, de
    ld   hl, (SH_CMD_PTR)
    jr   z, .cursor_line
    call SH_SETTLED
    call SH_DRAW_NEXT
    jr   .next
.cursor_line:
    call .active
.next:
    ld   hl, (SH_CMD_PTR)
    call MEM_LINE_NEXT
    ld   a, (SH_DRAW_ROW)
    cp   23
    jr   c, .record
    jr   .status
.sentinel:
    call SH_POS_IS_APPEND
    call z, .active
.status:
    call SH_DRAW_STATUS
    jr   SH_RD_CURSOR
.active:                               ; the cursor's line: the edit buffer, plain
    ld   a, (SH_DRAW_ROW)
    ld   (BASIC_ACTIVE_ROW), a
    ld   hl, EDIT_LINE_BUF
    jp   SH_DRAW_NEXT

; ============================================================================
; SH_RD_DRAW_ACTIVE -- draw the edit buffer at BASIC_ACTIVE_ROW, then the cursor (V2_RD_DRAW_ACTIVE)
; Out: carry clear
; SH_RD_CURSOR -- the cursor's cell inverted, if on the screen; remembers the cursor line's index
; and height for the selective redraws (V2_RD_CURSOR)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_RD_DRAW_ACTIVE:
    ld   hl, EDIT_LINE_BUF
    ld   a, (BASIC_ACTIVE_ROW)
    ld   b, a
    call SH_DRAW_TEXT
    call SH_RD_CURSOR
    or   a
    ret
SH_RD_CURSOR:
    ld   hl, (CUR_EDIT_INDEX)
    ld   (V2_RD_INDEX), hl
    ld   hl, EDIT_LINE_BUF
    call EDITOR_WRAP_CALC
    ld   a, (EDIT_WRAP_COUNT)
    ld   (V2_RD_WRAPS), a
    call EDITOR_WRAP_OFFSET_TO_ROWCOL
    ld   a, (BASIC_ACTIVE_ROW)
    add  a, b
    cp   23
    ret  nc
    ld   b, a
    jp   GFX_INVERT_ATTR

; ============================================================================
; SH_REDRAW_ACTIVE -- typing: redraw only the cursor line's rows when its height is unchanged
; (V2_REDRAW_ACTIVE). LEAP-C: when its height changed (it started or stopped wrapping onto another
; row) and the view stays (SH_VIEW), the lines above it are left alone: its rows and those below
; are cleared and redrawn (V2 redrew the whole screen)
; Out: C: the view moves (a full redraw is needed). NC: done
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_REDRAW_ACTIVE:
    ld   hl, EDIT_LINE_BUF
    call EDITOR_WRAP_CALC
    ld   a, (EDIT_WRAP_COUNT)
    ld   hl, V2_RD_WRAPS
    cp   (hl)
    jr   nz, .below
.redo:                                 ; A = its rows
    ld   c, a
    ld   a, (BASIC_ACTIVE_ROW)
    call SH_RD_CLEAR_ROWS
    jr   SH_RD_DRAW_ACTIVE
.below:
    ld   hl, (VIEW_TOP_INDEX)
    push hl
    call SH_VIEW
    pop  de
    ld   hl, (VIEW_TOP_INDEX)
    or   a
    sbc  hl, de
    scf
    ret  nz                            ; the view moves
    ld   a, (BASIC_ACTIVE_ROW)
    ld   (SH_DRAW_ROW), a
    ld   c, a
    ld   a, 23
    sub  c
    ld   c, a                          ; the rows from the cursor line's to the status row
    ld   a, (SH_DRAW_ROW)
    call SH_RD_CLEAR_ROWS
    call SH_POS_IS_APPEND
    jr   nz, .from
    ld   hl, 0                         ; the append line: SH_REDRAW's sentinel draws it
.from:
    call SH_REDRAW.record              ; the cursor line and the lines after it, the status, the cursor
    or   a
    ret

; ============================================================================
; SH_REDRAW_NAV -- UP/DOWN (V2_REDRAW_NAV): (a) the same line (the cursor moved between its rows):
; the line again; (b) the line above or below while the view stays at line 0 (both lines among
; the first 21, SH_VIEW) and the new line fits above the status row: the old line again as a
; settled line, the new one as the cursor line, the status row
; Out: C: a full redraw is needed. NC: done
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_REDRAW_NAV:
    ld   hl, (CUR_EDIT_INDEX)
    ld   de, (V2_RD_INDEX)
    or   a
    sbc  hl, de                        ; new - old
    jr   nz, .moved
    ld   a, (V2_RD_WRAPS)              ; (a)
    jr   SH_REDRAW_ACTIVE.redo
.moved:
    ld   b, 0                          ; B = 0: DOWN, 1: UP
    dec  hl
    ld   a, h
    or   l
    jr   z, .dir
    inc  hl
    inc  hl
    ld   a, h
    or   l
    jp   nz, .full
    inc  b
.dir:
    ld   hl, (VIEW_TOP_INDEX)          ; the view must be at line 0 ...
    ld   a, h
    or   l
    jp   nz, .full
    ld   hl, (CUR_EDIT_INDEX)
    ld   de, SH_VIEW_MAX + 1
    sbc  hl, de                        ; (carry clear)
    jr   nc, .full                     ; ... and stay there
    push bc
    ld   de, (V2_RD_INDEX)
    call SH_FIND_INDEX                 ; the old line's record, or 0: the append line
    ld   (SH_CMD_PTR), hl
    ld   a, h
    or   l
    jr   z, .old_blank
    call SH_SETTLED                    ; TOKEN_BUF: its text, keywords marked
    call EDITOR_WRAP_CALC
    ld   a, (EDIT_WRAP_COUNT)
    ld   hl, V2_RD_WRAPS
    cp   (hl)
    jr   nz, .full_pop                 ; not as tall as the edit buffer was
.old_blank:
    ld   hl, EDIT_LINE_BUF
    call EDITOR_WRAP_CALC              ; the new line's height
    ld   a, (EDIT_WRAP_COUNT)
    ld   (V2_RD_NEWH), a
    pop  bc
    ld   a, (BASIC_ACTIVE_ROW)
    dec  b
    jr   z, .up
    ld   hl, V2_RD_WRAPS               ; DOWN: the new line starts below the old one
    add  a, (hl)
    jr   .rows
.up:
    ld   hl, V2_RD_NEWH                ; UP: it ends above the old one
    sub  (hl)
    jr   c, .full
.rows:
    ld   (V2_RD_NEWROW), a
    ld   hl, V2_RD_NEWH
    add  a, (hl)
    cp   24
    jr   nc, .full                     ; it would not end above the status row: the view moves
    ld   a, (BASIC_ACTIVE_ROW)         ; the old line: its rows cleared, drawn settled
    ld   hl, V2_RD_WRAPS
    ld   c, (hl)
    call SH_RD_CLEAR_ROWS
    ld   hl, (SH_CMD_PTR)
    ld   a, h
    or   l
    jr   z, .new                       ; the empty append line: nothing to draw
    ld   hl, TOKEN_BUF                 ; (still its marked text)
    ld   a, (BASIC_ACTIVE_ROW)
    ld   b, a
    call SH_DRAW_TEXT
.new:
    ld   a, (V2_RD_NEWROW)
    ld   (BASIC_ACTIVE_ROW), a
    ld   hl, V2_RD_NEWH
    ld   c, (hl)
    call SH_RD_CLEAR_ROWS
    call SH_DRAW_STATUS
    jp   SH_RD_DRAW_ACTIVE
.full_pop:
    pop  bc
.full:
    scf
    ret

; ============================================================================
; SH_RD_CLEAR_ROWS -- clear C screen rows from row A (rows 23 and below are left alone): the bitmap,
; and the attributes to the text's (paper 7, ink 0), which also removes the cursor (V2_RD_CLEAR_ROWS)
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_RD_CLEAR_ROWS:
    cp   23
    ret  nc
    push af
    push bc
    call SH_CLEAR_ROW
    pop  bc
    pop  af
    ld   l, a
    ld   h, 0
    add  hl, hl
    add  hl, hl
    add  hl, hl
    add  hl, hl
    add  hl, hl                        ; row * 32
    ld   de, ATTR_ADDR
    add  hl, de
    ld   b, 32
.attr:
    ld   (hl), %00111000               ; paper 7, ink 0
    inc  hl
    djnz .attr
    inc  a
    dec  c
    jr   nz, SH_RD_CLEAR_ROWS
    ret

; ============================================================================
; SH_CLEAR_ROW -- clear screen row A's bitmap (0-23), the attributes untouched (in the editor's
; selective redraws and on the status row: the platform's GFX_CLEAR_ROW_TEXT prints 32 spaces,
; about 23 kT; this, about 6 kT)
; Destroys: AF, BC, DE, HL
; ============================================================================
SH_CLEAR_ROW:
    ld   b, a
    and  $18
    or   SCREEN_ADDR >> 8
    ld   h, a
    ld   a, b
    rrca
    rrca
    rrca
    and  $E0
    ld   l, a                          ; HL = the row's first byte (scanline 0)
    ld   b, 8
.scan:
    push bc
    push hl
    ld   d, h
    ld   e, l
    inc  e
    ld   (hl), 0
    ld   bc, 31
    ldir
    pop  hl
    pop  bc
    inc  h
    djnz .scan
    ret

; ============================================================================
; SH_VIEW -- VIEW_TOP_INDEX: the first line on the screen. As V2: up to 20 lines (SH_VIEW_MAX)
; above the cursor's line; fewer when they need more screen rows than there are above it, so that
; the cursor's line is always whole on rows 0-22
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_VIEW:
    ld   hl, EDIT_LINE_BUF
    call EDITOR_WRAP_CALC
    ld   hl, (CUR_EDIT_INDEX)
    ld   bc, SH_VIEW_MAX
    or   a
    sbc  hl, bc
    jr   nc, .top
    add  hl, bc
    ld   c, l                          ; fewer lines above it: from line 0 (B = 0)
    ld   hl, 0
.top:                                  ; HL = the first line, C = the lines above the cursor line
    ld   (VIEW_TOP_INDEX), hl
    ld   a, (EDIT_WRAP_COUNT)
    ld   b, a                          ; B = the rows they need: the cursor line's ...
    ld   a, c
    or   a
    ret  z
    push bc
    ex   de, hl
    call SH_FIND_INDEX
    pop  bc
    ld   de, SH_HEIGHTS
.walk:                                 ; ... and each line's above it
    push bc
    push de
    push hl
    ld   de, TOKEN_BUF
    call SH_COPY_TEXT
    ld   hl, TOKEN_BUF
    call EDITOR_WRAP_CALC
    pop  hl
    call MEM_LINE_NEXT
    pop  de
    pop  bc
    ld   a, (EDIT_WRAP_COUNT)
    ld   (de), a
    inc  de
    add  a, b
    ld   b, a
    dec  c
    jr   nz, .walk
    ld   de, SH_HEIGHTS
.trim:                                 ; lines off the top until they fit in rows 0-22
    ld   a, b
    cp   24
    ret  c
    ld   a, (de)
    inc  de
    neg
    add  a, b
    ld   b, a
    ld   hl, (VIEW_TOP_INDEX)
    inc  hl
    ld   (VIEW_TOP_INDEX), hl
    jr   .trim

; ============================================================================
; SH_DRAW_TEXT -- draw a line from screen row B down, wrapped as the editor wraps it
; (EDITOR_WRAP_CALC), stopping at the status row (V2_DRAW_TEXT). A character with bit 7 set (a
; keyword's, SH_KW_MARK) is drawn bold without it
; SH_DRAW_NEXT -- the same from row SH_DRAW_ROW
; In:  HL = the NUL-terminated text
; Out: SH_DRAW_ROW = the row after the line (at most 23)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_DRAW_NEXT:
    ld   a, (SH_DRAW_ROW)
    ld   b, a
SH_DRAW_TEXT:
    ld   a, b
    ld   (SH_DRAW_ROW), a
    ld   (SH_DRAW_PTR), hl
    call EDITOR_WRAP_CALC
    ld   a, (EDIT_WRAP_COUNT)
    ld   hl, EDIT_WRAP_START
.row:                                  ; A = the line's rows left, HL -> this row's start offset
    ld   (SH_DRAW_LEFT), a
    ld   a, (SH_DRAW_ROW)
    cp   23
    ret  nc
    push hl
    ld   e, (hl)
    ld   d, 0
    ld   bc, EDIT_WRAP_LEN - EDIT_WRAP_START
    add  hl, bc
    ld   b, (hl)                       ; B = its length
    ld   hl, (SH_DRAW_PTR)
    add  hl, de                        ; HL -> its first character
    ld   c, 0                          ; C = the column
    inc  b
    jr   .count
.char:
    ld   a, (hl)
    inc  hl
    push hl
    push bc
    ld   e, a
    ld   a, (SH_DRAW_ROW)
    ld   b, a
    ld   a, e
    ld   hl, GFX_PUTCHAR
    bit  7, a
    jr   z, .put
    res  7, a
    ld   hl, GFX_PUTCHAR_BOLD
.put:
    call SH_JP_HL
    pop  bc
    pop  hl
    inc  c
.count:
    djnz .char
    pop  hl
    inc  hl
    ld   a, (SH_DRAW_ROW)
    inc  a
    ld   (SH_DRAW_ROW), a
    ld   a, (SH_DRAW_LEFT)
    dec  a
    jr   nz, .row
    ret
SH_JP_HL:
    jp   (hl)

; ============================================================================
; STARTUP_CHIME -- the boot chime: V2's chord (C4/E4/G4 on AY channels A/B/C, a staggered entrance
; ramped 4-8-12, a hold, a release 8-4-0), as V2 production builds it (V2_MAINT_CHIME_C), through
; SOUND_EXROM (B = register, C = value, both kept) and the platform's frame wait
; Destroys: AF, BC, DE, HL
; ============================================================================
STARTUP_CHIME:
    ld   hl, CHIME_REGS
    ld   b, 0
.init:
    ld   c, (hl)
    call SOUND_EXROM                   ; R0-R10 from CHIME_REGS
    inc  hl
    inc  b
    ld   a, b
    cp   11
    jr   c, .init
    ld   b, 8                          ; attack: channel A, then B, then C
.chan:
    ld   c, 4
.up:
    call SOUND_EXROM                   ; level 4, 8, 12, three frames each
    call .wait3
    ld   a, c
    add  a, 4
    ld   c, a
    cp   16
    jr   c, .up
    inc  b
    ld   a, b
    cp   11
    jr   c, .chan
    ld   de, 19                        ; hold the full chord (22 frames after C's last step)
    call AY_WAIT_FRAMES
    ld   c, 8                          ; release: all three at 8, then 4, then 0
.rel:
    ld   b, 8
.relch:
    call SOUND_EXROM
    inc  b
    ld   a, b
    cp   11
    jr   c, .relch
    call .wait3
    ld   a, c
    sub  4
    ld   c, a
    jr   nc, .rel
    ret
.wait3:
    ld   de, 3
    jp   AY_WAIT_FRAMES
CHIME_REGS:
    ; tone periods C4/E4/G4 (421, 334, 281), noise period, mixer (tones on, noise off), levels 0
    DB   165, 1, 78, 1, 25, 1, 0, 248, 0, 0, 0

; ---------------------------------------------------------------- texts
SH_KW_RUN:      DB "RUN", 0
SH_KW_LIST:     DB "LIST", 0
SH_KW_NEW:      DB "NEW", 0
SH_MSG_FULL:    DB "PROGRAM FULL", 0
SH_MSG_RUNTIME: DB "RUNTIME "
SH_MSG_ERROR:   DB "ERROR", 0
SH_MSG_BREAK:   DB "BREAK", 0
SH_TXT_LINE:    DB " LINE ", 0
