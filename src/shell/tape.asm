; ============================================================================
; src/shell/tape.asm -- the cassette (EXROM, the shell's component; spec.md 6.1, 7, 8; project_plan.md Phase 7)
;
; SAVE "name", LOAD "name" / LOAD "", VERIFY "name" / VERIFY "" (the source: header type 0, the line store
; verbatim), and the EXROM part of the library's tape_save / tape_load (data: header type 3). Both stamp and
; check the version word LEAPC_TAPE_VERSION ($8C00, spec.md 8.1) through the platform's STORAGE_SAVE and
; STORAGE_LOAD (kernel/storage/storage.asm, in this image), whose header logic runs here with the EXROM paged
; in. Their block I/O (STORAGE_SEND_BLOCK, STORAGE_RECEIVE_BLOCK) is in HOME (platform delta D9): the
; platform's calls of those names land on SH_TAPE_SEND and SH_TAPE_RECV, which reach it through the HOME
; trampoline TAPE_BLOCK, so every block moves with chunk 6 paged out (spec.md 8.3). The headers are in the
; platform's STORAGE_HEADER_BUF and the names in TAPE_NAME, outside chunk 6.
;
; As V2 (rom/exrom_v2_shell.asm at the V2 reference tag: V2_SAVE, V2_LOAD, V2_VERIFY, adapted): a LOAD that
; fails before the data block, or with a bad version word, changes nothing; a VERIFY never writes; a tape
; that verifies must end where the source does. Leap-C adds: a LOAD whose program fits above the current
; source goes there first (TAPE_DEST) and replaces the source only once it has arrived whole and its records
; are sound, so a failed LOAD keeps the source in every case where both fit; the status row shows SAVING,
; LOADING or VERIFYING and the tape's name meanwhile; SPACE (BREAK) during a SAVE stops it.
; ============================================================================

STORAGE_DATA_TYPE   EQU 3               ; tape_save's header type (spec.md 8.3: the stock CODE type)
TR_FAILED           EQU 1               ; SH_LOAD_IO's failures: nothing was written ...
TR_TOUCHED          EQU 2               ; ... part of the destination was written ...
TR_VERSION          EQU 3               ; ... the header's version word is not Leap-C's (nothing written) ...
TR_BREAK            EQU 4               ; ... SPACE (BREAK) aborted it before any byte was written ...
TR_BREAKT           EQU 5               ; ... or after (Phase 10: a LOAD into the source, or a LIB into the region, is
                                        ; then not trusted; SH_TAPE_DONE reports both as BREAK)
    ASSERT TR_TOUCHED == ((1 - STORAGE_LOAD_DATA_TOUCHED) & $FF) && TR_VERSION == ((1 - STORAGE_LOAD_BAD_VERSION) & $FF)
    ASSERT TR_BREAKT == TR_TOUCHED + TR_BREAK - TR_FAILED

; ============================================================================
; SH_SAVE -- SAVE "name": the source to tape (spec.md 8.1). The report: SAVED name, or BREAK (SPACE stopped
; it), BAD NAME (no name, more than 10 characters, or more on the line), NO PROGRAM (an empty source: a
; block of no bytes cannot be loaded); and SOURCE s B  FREE f B
; SH_LOAD -- LOAD "name" / LOAD "": the next program tape of that name (any) replaces the source. The
; report: LOADED name (the tape's), or LOAD FAILED, BAD TAPE VERSION, BREAK, BAD NAME. The cursor ends on
; the append line after the last line loaded. A failed LOAD leaves the source as it was, unless the tape's
; program did not fit above it and part of it was received: then the source is empty (it cannot be trusted)
; SH_VERIFY -- VERIFY "name" / VERIFY "": the tape against the source, nothing written. The report: VERIFIED
; name, or VERIFY FAILED, BAD TAPE VERSION, BREAK, BAD NAME
; In:  HL -> the edit buffer after the command's opening quote (SH_QWORD)
; Out: carry clear (a command ran). Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_VERIFY:
    ld   a, 1
    jr   SH_LOAD_V
SH_LOAD:
    xor  a
SH_LOAD_V:                             ; A = STORAGE_VERIFY_MODE
    push af
    call SH_CMD_NAME                   ; B = the name's length (0: any)
    pop  hl
    jp   c, SH_BAD_NAME
    ld   a, h
    ld   (STORAGE_VERIFY_MODE), a
    ld   hl, (VARS_START)
    ld   de, PROG_AREA_START
    or   a
    sbc  hl, de
    ex   de, hl                        ; DE = the most: the line store's room (spec.md 8.1: never chunk 6)
    push hl
    pop  ix
    call SH_HOOK_ON
    call SH_LOAD_AT                    ; C = 0: DE = the tape's length; HL = where the data block went:
    ld   a, (STORAGE_VERIFY_MODE)      ; above the source (staged), or PROG_AREA_START
    or   a
    jr   nz, .verify
    or   c
    jr   nz, .failed
    push hl
    push de
    call SH_CHECK_STORE                ; the program's records sound?
    pop  bc
    pop  hl
    ld   a, TR_TOUCHED
    jr   c, .failed                    ; no: as a failure after writing
    ld   de, PROG_AREA_START
    ldir                               ; (staged: down onto the source; else onto itself)
    ld   (PROG_END), de
    ld   (ARRAYS_END), de
    call SH_RESET_EDIT
    call SH_COUNT_LINES
    ld   (CUR_EDIT_INDEX), de          ; the cursor on the append line after the last line
    xor  a
    ld   hl, SH_MSG_LOADED
    jr   SH_TAPE_DONE
.failed:                               ; A = TR_*, HL = the data block's destination
    ld   c, a
    cp   TR_TOUCHED
    jr   z, .touched
    cp   TR_BREAKT                     ; (Phase 10: BREAK once part of the data block had arrived kept the
    jr   nz, .keep                     ; source, partly overwritten when it arrived in place)
.touched:
    ld   de, PROG_AREA_START
    or   a
    sbc  hl, de
    jr   nz, .keep                     ; staged above the source: the source is intact
    call MEM_INIT                      ; received into the source: it cannot be trusted (V2's rule)
    call SH_RESET_EDIT
.keep:
    ld   a, c
    ld   hl, SH_MSG_LFAIL
    jr   SH_TAPE_DONE
.verify:
    xor  a
    ld   (STORAGE_VERIFY_MODE), a
    ld   a, c
    ld   hl, SH_MSG_VFAIL
    or   a
    jr   nz, SH_TAPE_DONE
    ld   hl, (PROG_END)                ; the tape must end where the source does (V2 R10.9 D2)
    ld   bc, PROG_AREA_START
    sbc  hl, bc                        ; (carry clear)
    sbc  hl, de
    ld   hl, SH_MSG_VFAIL
    ld   a, TR_FAILED
    jr   nz, SH_TAPE_DONE
    xor  a
    ld   hl, SH_MSG_VERIFIED
    ; falls into SH_TAPE_DONE

; ============================================================================
; SH_TAPE_DONE -- the end of a tape command: the progress hook off, then its report
; In:  A = 0 (done: HL = the text, the tape's name is appended), or TR_* (HL = the command's failure text, for
;      TR_FAILED and TR_TOUCHED)
; SH_TAPE_REPORT -- the report HL / SOURCE s B  FREE f B
; Out: carry clear. Destroys: AF, BC, DE, HL
; SH_TAPE_NAMED -- the progress hook off; SH_REPORT_BUF = the text at HL and the tape's name. Out: DE -> the NUL
; SH_TAPE_OFF -- the progress hook off, interrupts on (the tape routines disable them). Destroys: DE
; ============================================================================
SH_TAPE_DONE:
    or   a
    jr   nz, .failed
    call SH_TAPE_NAMED
    jr   SH_TAPE_SOURCE
.failed:
    call SH_TAPE_OFF
    cp   TR_VERSION
    jr   c, SH_TAPE_REPORT
    ld   hl, SH_MSG_VERSION
    jr   z, SH_TAPE_REPORT
    ld   hl, SH_MSG_BREAK
SH_TAPE_REPORT:
    ld   de, SH_REPORT_BUF
    call SH_APPEND
SH_TAPE_SOURCE:
    ld   de, SH_STATUS_BUF
    call SH_SOURCE
    jp   SH_REPORT
SH_BAD_NAME:
    ld   hl, SH_MSG_BADNAME
    jr   SH_TAPE_REPORT
SH_TAPE_OFF:
    ld   de, 0
    ld   (STORAGE_PROGRESS_HOOK), de
    ei
    ret
SH_TAPE_NAMED:
    call SH_TAPE_OFF
    ld   de, SH_REPORT_BUF
    call SH_APPEND
    ; falls into SH_HEADER_NAME
; ============================================================================
; SH_HEADER_NAME -- append the name in the tape header (STORAGE_HEADER_BUF: the one saved or found) at DE
; Out: DE -> the NUL after it. Destroys: AF, BC, HL
; ============================================================================
SH_HEADER_NAME:
    ld   hl, STORAGE_HEADER_BUF + STORAGE_HEADER_NAME_OFF
    ld   bc, TAPE_NAME_LEN
    ldir
    xor  a
    ld   (de), a
    ret

SH_SAVE:
    call SH_CMD_NAME
    jr   c, SH_BAD_NAME
    ld   a, b
    or   a
    jr   z, SH_BAD_NAME                ; SAVE "": a name is needed
    ld   hl, (PROG_END)
    ld   bc, PROG_AREA_START
    or   a
    sbc  hl, bc
    ex   de, hl                        ; DE = the source's bytes
    ld   hl, SH_MSG_NOPROG
    jr   z, SH_TAPE_REPORT
    push bc
    pop  ix
    call SH_HOOK_ON
    call SH_SAVE_IO
    ld   hl, SH_MSG_SAVED
    jr   SH_TAPE_DONE
; ============================================================================
; SH_LIB -- LIB "name" / LIB "": the next library tape of that name (any) into image region 3 (Phase 10;
; spec.md 7.2, 8.4): header type LX_TYPE, at most 1 KB. Its version word is the library's magic and ABI: the
; platform's STORAGE_LOAD refuses another magic, or an ABI above this ROM's (STORAGE_VERSION_WORD: the package
; word, LX_WORD), at the header, before any byte is written (BAD TAPE VERSION). As LOAD's, the data block arrives
; above the source when there is room (SH_TAPE_HOOK: TAPE_DEST) and moves into the region only once it is whole,
; else straight into the region. The report: LIBRARY name: n FUNCTIONS (the image header's export count), or
; LOAD FAILED, BAD TAPE VERSION, BREAK, BAD NAME; then SOURCE s B  FREE f B. A failure once part
; of the data block was written into the region leaves no library loaded; any other keeps the one before
; In:  HL -> the edit buffer after the command's opening quote (SH_QWORD)
; Out: carry clear (a command ran). Destroys: AF, BC, DE, HL, IX
; SH_UNLIB -- LIB alone: no library loaded (the status row: NO LIBRARY)
; ============================================================================
SH_LIB:
    call SH_CMD_NAME                   ; B = the name's length (0: any)
    jp   c, SH_BAD_NAME
    call SH_HOOK_ON
    ld   a, LX_TYPE
    ld   (STORAGE_REQUEST_TYPE), a
    ld   ix, LX_BASE
    ld   de, LX_END - LX_BASE
    call SH_LOAD_AT                    ; A = 0: DE = the image's length; HL = where the data block went
    jr   nz, .failed
    ld   b, d
    ld   c, e
    ld   de, LX_BASE
    ldir                               ; (staged: into the region; else onto itself)
    ld   a, LX_BASE >> 8
    ld   (LIB_LOADED), a
    ld   hl, SH_TXT_LIBRARY            ; "LIBRARY name: n FUNCTIONS"
    call SH_TAPE_NAMED
.trim:                                 ; (the header's name is padded with spaces)
    dec  de
    ld   a, (de)
    cp   ' '
    jr   z, .trim
    inc  de
    ld   hl, SH_TXT_COLON
    call SH_APPEND
    ld   hl, (LX_HDR_COUNT)
    ld   h, 0
    call SH_APPEND_NUM                 ; (at most 99 functions fit the row: tools/lib2tape.py)
    ld   hl, SH_TXT_FUNCTIONS
    call SH_APPEND
    jp   SH_TAPE_SOURCE
.failed:                               ; A = C = TR_*, HL = where the data block went
    ld   de, LX_BASE
    sbc  hl, de                        ; (carry clear)
    jr   nz, .keep                     ; staged above the source: the region is as it was
    cp   TR_TOUCHED
    jr   z, .unload
    cp   TR_BREAKT
    jr   nz, .keep
.unload:                               ; part of the data block in the region: no library
    xor  a
    ld   (LIB_LOADED), a
.keep:
    ld   a, c
    ld   hl, SH_MSG_LFAIL
    jp   SH_TAPE_DONE
SH_UNLIB:
    xor  a
    ld   (LIB_LOADED), a
    ld   hl, SH_MSG_NOLIB
    jp   SH_SHOW_MESSAGE

; ============================================================================
; SH_CMD_NAME -- the quoted name of a tape command into TAPE_NAME (SH_NAME); only spaces may follow it
; In:  HL -> after the opening quote. Out: NC: B = its length (0-10). C: a bad name
; Destroys: AF, C, DE, HL
; ============================================================================
SH_CMD_NAME:
    ld   c, '"'
    call SH_NAME
    ret  c
    call SH_SPACES
    or   a
    ret  z                             ; (carry clear)
    scf
    ret

; ============================================================================
; SH_NAME -- a tape name: the characters at HL up to the terminator C (at most TAPE_NAME_LEN), into TAPE_NAME
; padded with spaces (HL may be TAPE_NAME itself: the library's name is padded in place)
; Out: NC: B = its length, HL -> after the terminator. C: no terminator within TAPE_NAME_LEN characters (a NUL
;      ends the text)
; Destroys: AF, DE
; ============================================================================
SH_NAME:
    ld   de, TAPE_NAME
    ld   b, 0
.char:
    ld   a, (hl)
    inc  hl
    cp   c
    jr   z, .pad
    or   a
    scf
    ret  z                             ; the text ends first
    ld   (de), a
    inc  de
    inc  b
    ld   a, TAPE_NAME_LEN
    cp   b
    jr   nc, .char
    ret                                ; (carry set: too long)
.pad:
    ld   a, TAPE_NAME_LEN
    sub  b
    ret  z                             ; (carry clear)
    push bc
    ld   b, a
    ld   a, ' '
.sp:
    ld   (de), a
    inc  de
    djnz .sp
    pop  bc
    or   a
    ret

; ============================================================================
; SH_CHECK_STORE -- are the DE bytes at HL line-store records ([length:2][text][CR], the length 1-128: the
; text and its CR), ending exactly at HL + DE, and at least one? A LOADed program must be, or the editor and
; the compiler, which walk the records by their lengths, could not (SAVE never writes an empty program)
; Out: NC: yes. Destroys: AF, BC, DE, HL
; ============================================================================
SH_CHECK_STORE:
    ld   a, d
    or   e
    scf
    ret  z
    ex   de, hl
    add  hl, de
    ld   b, h
    ld   c, l                          ; BC = the end
    ex   de, hl
.rec:
    or   a
    sbc  hl, bc
    add  hl, bc
    ret  z                             ; at the end (carry clear)
    ccf
    ret  c                             ; past it
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    inc  hl
    ld   a, e
    dec  a
    cp   EDIT_LINE_BUF_LEN
    ccf
    ret  c                             ; a length outside 1-128
    inc  d
    dec  d
    scf
    ret  nz
    add  hl, de
    dec  hl
    ld   a, (hl)
    inc  hl
    cp   $0D
    jr   z, .rec
    scf
    ret

; ============================================================================
; SH_HOOK_ON -- a shell command's transfer: a program tape (header type 0), the progress hook SH_TAPE_HOOK
; (SH_TAPE_DONE removes it, so the library's transfers never draw). TAPE_DEST is 0 outside a LOAD (SH_LOAD
; clears it after its transfer)
; Destroys: AF, HL
; ============================================================================
SH_HOOK_ON:
    xor  a
    ld   (STORAGE_REQUEST_TYPE), a
    ld   hl, SH_TAPE_HOOK
    ld   (STORAGE_PROGRESS_HOOK), hl
    ret

; ============================================================================
; SH_TAPE_HOOK -- STORAGE_PROGRESS_HOOK during SAVE, LOAD and VERIFY (STORAGE_REPORT_PROGRESS calls it between
; blocks, never inside one): the status row shows SAVING name, LOADING or VERIFYING while it searches, and
; LOADING name or VERIFYING name once the header is found. At a LOAD's header, the staging decision: the data
; block goes above the source (TAPE_DEST = PROG_END) when both fit below VARS_START
; Destroys: AF, BC, DE, HL (STORAGE_REPORT_PROGRESS keeps the registers of its caller)
; ============================================================================
SH_TAPE_HOOK:
    ld   a, (STORAGE_OP_STATE)
    ld   hl, SH_TXT_SAVING
    cp   1
    jr   z, .named                     ; 1: SAVING name (before each block)
    ld   b, a
    ld   hl, SH_TXT_LOADING
    ld   a, (STORAGE_VERIFY_MODE)
    or   a
    jr   z, .mode
    ld   hl, SH_TXT_VERIFYING
.mode:
    ld   c, a
    ld   a, b
    cp   3
    jp   z, SH_STATUS_ROW              ; 3: searching
    cp   7
    ret  nz                            ; 2, 4, 6: the command reports the end
    inc  c
    dec  c
    jr   nz, .named                    ; 7: the header found; VERIFY reads where IX says
    push hl
    ld   hl, (VARS_START)
    ld   de, (PROG_END)
    or   a
    sbc  hl, de                        ; the room above the source ...
    ld   bc, (STORAGE_HEADER_BUF + STORAGE_HEADER_LENGTH_OFF)
    sbc  hl, bc                        ; ... holds the program?
    jr   c, .direct
    ld   (TAPE_DEST), de
.direct:
    pop  hl
.named:
    ld   de, SH_STATUS_BUF
    call SH_APPEND
    call SH_HEADER_NAME
    ld   hl, SH_STATUS_BUF
    jp   SH_STATUS_ROW

; ============================================================================
; SH_SAVE_IO -- STORAGE_SAVE: DE bytes from IX, header type STORAGE_REQUEST_TYPE, named TAPE_NAME
; Out: A = 0, or TR_BREAK (SPACE stopped it). Destroys: AF, BC, DE, HL, IX
; SH_LOAD_IO -- STORAGE_LOAD (or verify, STORAGE_VERIFY_MODE): the next tape of type STORAGE_REQUEST_TYPE named
; TAPE_NAME (B = 0: any name) into IX, at most DE bytes
; Out: A = 0: DE = its length; else TR_FAILED, TR_TOUCHED, TR_VERSION, TR_BREAK, TR_BREAKT. Destroys: AF, BC, DE,
;      HL, IX
; SH_LOAD_AT -- SH_LOAD_IO into IX, which SH_TAPE_HOOK may stage above the source for a LOAD or LIB (TAPE_DEST,
; then cleared)
; Out: HL = where the data block went (the IX given, or the staged place), C = A = SH_LOAD_IO's result (Z: 0),
;      DE = the length. Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_SAVE_IO:
    xor  a
    ld   (TAPE_ABORT), a
    ld   hl, TAPE_NAME
    ld   b, TAPE_NAME_LEN
    call STORAGE_SAVE
    ld   a, (TAPE_ABORT)
    or   a
    ret  z
    ld   a, TR_BREAK
    ret
SH_LOAD_AT:
    push ix
    call SH_LOAD_IO
    ld   c, a
    ld   hl, (TAPE_DEST)
    ld   a, h
    or   l
    jr   z, .at                        ; (received at IX)
    ex   (sp), hl                      ; staged: there instead
    ld   hl, 0
    ld   (TAPE_DEST), hl
.at:
    pop  hl
    ld   a, c
    or   a
    ret
SH_LOAD_IO:
    ld   hl, TAPE_NAME
    call STORAGE_LOAD                  ; NC: A = 0. C: A = 0 / STORAGE_LOAD_DATA_TOUCHED / STORAGE_LOAD_BAD_VERSION,
    ret  nc                            ; B = nonzero: SPACE held
    neg
    inc  a                             ; TR_FAILED / TR_TOUCHED / TR_VERSION
    cp   TR_VERSION
    ret  z
    inc  b
    dec  b
    ret  z
    add  a, TR_BREAK - TR_FAILED       ; SPACE: TR_BREAK, or TR_BREAKT once part of the data block was written
    ret

; ============================================================================
; SH_TAPE_SEND -- the platform's STORAGE_SEND_BLOCK in this image (STORAGE_SAVE's two calls): HOME's, through
; TAPE_BLOCK (chunk 6 = RAM). Once a block is aborted (SPACE), the next is not sent (TAPE_ABORT)
; SH_TAPE_RECV -- the platform's STORAGE_RECEIVE_BLOCK in this image (STORAGE_LOAD's calls): HOME's, through
; TAPE_BLOCK, into TAPE_DEST instead of IX when the shell's LOAD staged the data block (SH_TAPE_HOOK)
; In, Out: as STORAGE_SEND_BLOCK, STORAGE_RECEIVE_BLOCK. Destroys: AF, AF', BC, DE, HL, IX
; ============================================================================
SH_TAPE_SEND:
    ld   hl, TAPE_ABORT
    inc  (hl)
    dec  (hl)
    ret  nz
    ld   hl, TAPE_SEND_BLOCK
    call TAPE_BLOCK
    ret  c                             ; sent (carry: the last SPACE test found it up)
    ld   hl, TAPE_ABORT
    inc  (hl)
    ret
SH_TAPE_RECV:
    push af
    ld   hl, (TAPE_DEST)
    ld   a, h
    or   l
    jr   z, .at
    push hl
    pop  ix
.at:
    pop  af
    ld   hl, TAPE_RECV_BLOCK
    jp   TAPE_BLOCK

; ============================================================================
; SH_LIBTAPE -- the library's tape_save and tape_load (HOME LIB_TAPE, through LEAPC_EXROM_TAPE): a data tape
; (header type 3) named by a C string (1-10 characters for tape_save; 0-10 for tape_load, "": any)
; In:  A = nonzero: tape_save, 0: tape_load; DE = the address; BC = the length (tape_save) or the most to load;
;      TAPE_NAME = the name's first 11 bytes
; Out: A = 0 and HL = the result (tape_save: 0; tape_load: the length loaded, or -TR_FAILED, -TR_TOUCHED,
;      -TR_VERSION), or A = RTE_ARG (the name, or tape_save's length 0) or RTE_BREAK (SPACE aborted it)
; Destroys: AF, BC, DE, HL, IX
; ============================================================================
SH_LIBTAPE:
    push af
    push de
    pop  ix                            ; IX = the address
    push bc
    ld   a, STORAGE_DATA_TYPE
    ld   (STORAGE_REQUEST_TYPE), a
    xor  a
    ld   (STORAGE_VERIFY_MODE), a
    ld   hl, TAPE_NAME
    ld   c, a                          ; the C string's NUL ends it
    call SH_NAME                       ; B = its length
    pop  de                            ; DE = the length
    pop  hl                            ; H = the selector
    ld   a, RTE_ARG
    ret  c
    inc  h
    dec  h
    jr   z, .load
    ld   a, b
    or   a
    ld   a, RTE_ARG
    ret  z                             ; no name
    ld   a, d
    or   e
    ld   a, RTE_ARG
    ret  z                             ; no bytes
    call SH_SAVE_IO
    ld   hl, 0
    jr   .result
.load:
    call SH_LOAD_IO
    ex   de, hl
.result:
    or   a
    ret  z
    cp   TR_BREAK
    jr   nc, .brk                      ; (TR_BREAK, TR_BREAKT)
    neg
    ld   l, a
    ld   h, $FF                        ; HL = -TR_*
    xor  a
    ret
.brk:
    ld   a, RTE_BREAK
    ret
