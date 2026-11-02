; ============================================================================
; kernel/graphics/graphics.asm — text-mode character output
;
; CURRENT STATUS: assembled into the working ROM and exercised under
; Fuse by the automated graphics and language regression tests. Glyph
; appearance still ultimately requires visual judgment; the addressing
; and drawing paths have executable coverage.
;
; CONFIDENCE LEVELS DIFFER within this file, worth being explicit about:
;   - Screen ADDRESSING (ROW_BASE_TABLE, GFX_PUTCHAR's address math) was
;     verified NUMERICALLY with a Python script before any assembly was
;     written — the standard Spectrum-family screen layout formula was
;     checked against 576 spot-check (row, col, scanline) combinations,
;     not just hand-traced. High confidence.
;   - The FONT DATA (FONT_TABLE) has no equivalent numerical check —
;     there's no formula to verify glyph shapes against, only human
;     judgement. Each glyph was designed deliberately as ASCII art (not
;     recalled from a specific ROM's font from memory, to avoid
;     transcription errors) and visually rendered for self-review before
;     conversion to hex, but this is NOT the same confidence level as
;     the addressing math. Treat glyph shapes as needing YOUR visual
;     confirmation once actually on screen — that's the one part of
;     this file I can't self-verify at all.
;
; Owns: the screen bitmap/attribute addressing scheme, and character
; output (GFX_PUTCHAR, GFX_CLS, GFX_PRINT_STRING, GFX_INVERT_ATTR).
; FONT_TABLE covers space, 0-9, A-Z, a-z, and 31 punctuation characters
; (94 glyphs total: " ! @ # $ % & ' ( ) _ : . , = + - ; / * < > ?, and
; LEAP-C DELTA D8: [ ] { } | ~ ^ \) — grown
; as needed rather than up front. The quote character was added once
; PRINT "..." string literals made it a real blocker; most of the rest
; cover kernel/io's confirmed-confidence subset of SYMBOL SHIFT's
; punctuation table (see that module's header — the full real table is
; more complex, some keys give BASIC keyword tokens instead of symbols,
; only what's independently confirmed is implemented on either side).
; / and * were added once basic/'s expression evaluator actually needed
; them for division and multiplication — this project already shipped
; the "character typed correctly but invisible, no glyph for it" bug
; once (the quote character, early on); adding a SYMBOL SHIFT
; punctuation mapping without also adding its glyph would repeat that
; exact mistake, so both are always added together now.
; ============================================================================

    IFNDEF GFX_EDITOR_TEXT_ONLY          ; Leap-C (delta D12): the EXROM assembles only GFX_PUTCHAR_BOLD
                                         ; and GFX_PRINT_STRING, the editor's text output
    INCLUDE "include/hardware.inc"
    INCLUDE "include/sysvars.inc"

; ---- character grid ----
GFX_ROWS   EQU 24
GFX_COLS   EQU 32
ATTR_DEFAULT EQU $38     ; PAPER 7 (white), INK 0 (black) — this
                        ; project's default attribute, used by both
                        ; GFX_CLS and GFX_CLEAR_ROW; previously a bare
                        ; $38 in just GFX_CLS, promoted to a symbolic
                        ; constant now that a second routine needs the
                        ; same value
ATTR_STATUS_BAR EQU $07   ; PAPER 0 (black), INK 7 (white) — ATTR_
                          ; DEFAULT with ink/paper swapped, i.e. what
                          ; GFX_INVERT_ATTR_STATIC would produce
                          ; starting from ATTR_DEFAULT. Verified
                          ; against GFX_ATTR_SWAP's own bit logic
                          ; (ink bits shifted into paper position,
                          ; paper bits shifted into ink position)
                          ; rather than just asserted. Used by basic/'s
                          ; status bar to set the inverted attribute
                          ; directly (GFX_SET_ATTR) instead of clear-
                          ; then-toggle (GFX_CLEAR_ROW + GFX_INVERT_
                          ; ATTR_STATIC), eliminating a briefly-visible
                          ; non-inverted intermediate state that a
                          ; two-step clear-then-toggle sequence can't
                          ; avoid — found from the user reporting a
                          ; smaller, but still-present, flash even
                          ; after the toggle bug itself was fixed

; Status bar branding swatch — three solid-color cells in the status
; bar's reserved right-hand columns, echoing the red/green/blue bars
; under the real TS2068's "PERSONAL COLOR COMPUTER" logo. PAPER-only
; (INK bits left 0/black) since these attributes are applied to blank
; (space) cells — with no set pixels, only PAPER ever shows, so INK is
; irrelevant here. Standard Spectrum-family color numbering: 1=blue,
; 2=red, 4=green.
ATTR_SWATCH_RED   EQU $10   ; PAPER 2 (red),   INK 0
ATTR_SWATCH_GREEN EQU $20   ; PAPER 4 (green), INK 0
ATTR_SWATCH_BLUE  EQU $08   ; PAPER 1 (blue),  INK 0

BORDER_DEFAULT  EQU 7     ; white — matches ATTR_DEFAULT's white PAPER,
                          ; so a freshly-reset screen has a consistent
                          ; white background top to bottom, border
                          ; included. Used by basic/'s cold-boot setup
                          ; and NEW (both real "start fresh" moments) —
                          ; deliberately NOT applied by GFX_CLS itself,
                          ; since real Sinclair BASIC's CLS clears only
                          ; the text screen and never touches the
                          ; border; folding a border reset into GFX_CLS
                          ; would incorrectly wipe a program's own
                          ; BORDER setting on every ordinary mid-program
                          ; CLS statement, not just at a genuine reset

; ============================================================================
; GFX_CLS
; Clears the screen bitmap to all-off and the attribute area to a
; default (white paper, black ink — INK 0, PAPER 7 = $38).
; In:  none
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_CLS:
    ld   hl, SCREEN_ADDR
    ld   de, SCREEN_ADDR + 1
    ld   bc, 6144 - 1           ; bitmap is 6144 bytes ($4000-$57FF)
    xor  a
    ld   (hl), a
    ldir

    ld   a, ATTR_DEFAULT           ; PAPER 7, INK 0 — falls straight
                                   ; into GFX_PAINT_ATTR below for the
                                   ; actual attribute-area fill, same
                                   ; loop, no ROM-budget cost for
                                   ; duplicating it here
; ============================================================================
; GFX_PAINT_ATTR
; Paints the whole attribute area (all 24 rows x 32 columns) to one
; caller-supplied attribute byte — the bitmap itself is untouched, so
; this is purely a re-color, not a clear. GFX_CLS falls straight through
; into this same code (having just set A = ATTR_DEFAULT) rather than
; duplicating the loop, so GFX_CLS's own contract (always resets to
; white paper/black ink, matching its existing callers throughout this
; project) is unchanged for every caller that only ever calls GFX_CLS;
; this label just gives BASIC_STMT_CLS a way to follow a real GFX_CLS
; with a repaint to whatever CURRENT_INK/CURRENT_PAPER (etc.) actually
; says, without touching GFX_CLS's own behavior.
; In:  A = attribute byte to fill every cell with
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_PAINT_ATTR:
    ld   hl, ATTR_ADDR
    ld   de, ATTR_ADDR + 1
    ld   bc, 768 - 1
    ld   (hl), a
    ldir
    ret

; LEAP-C DELTA D6: GFX_SPRITE_INVALIDATE removed. It cleared V2's sprite-slot
; state (SPRITE_SLOT_SHOWN, SPRITE_DISPLAY_DEPTH) for BASIC's sprite slots,
; which Leap-C does not have: nothing reads those cells
; (tools/check_ram_layout.py). Its calls in GFX_CLS, GFX_SCROLL_TEXT_UP,
; GFX_SCROLL_TEXT_DOWN and GFX_SET_MODE are removed with it.

; ============================================================================
; GFX_ROW_BASE_ADDR
; Looks up a text row's bitmap base address (scanline 0, column 0) —
; same ROW_BASE_TABLE[row] lookup GFX_PUTCHAR/GFX_CHAR_SETUP already do
; inline, factored out here so GFX_SCROLL_TEXT_UP/_DOWN (via GFX_COPY_
; ROW_BITMAP) don't duplicate it a third time.
; In:  A = row (0-23, caller's responsibility — no bounds check)
; Out: HL = that row's bitmap base address
; Destroys: AF, DE
; ============================================================================
GFX_ROW_BASE_ADDR:
    ld   h, 0
    ld   l, a
    add  hl, hl                    ; row * 2 (2 bytes per table entry)
    ld   de, ROW_BASE_TABLE
    add  hl, de
    ld   e, (hl)
    inc  hl
    ld   d, (hl)
    ex   de, hl
    ret

; ============================================================================
; LEAP-C DELTA D26: the scroll (release 1.2.0). V2's GFX_SCROLL_TEXT_UP and GFX_COPY_ROW_BITMAP
; (each scanline of each row a separate LDIR) and GFX_SCROLL_OUTPUT_UP's extra row are replaced by
; 2068-Forth v2.0's GFX_SCROLL_ROWS and GFX_LDI_BLOCKS (its Display speed milestone): a scanline of a
; third holds the bytes of its 8 rows in one run, so each scanline is moved in a few long runs of
; unrolled LDI. A scroll took about 237,000 T; the same bytes move now (see platform/UPSTREAM.md).
; ============================================================================

; ============================================================================
; GFX_SCROLL_OUTPUT_UP -- scroll all 24 rows up one row (bitmap and attributes) and clear the new
; row 23 (ATTR_DEFAULT; the library repaints it in the print colours)
; In:  none
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SCROLL_OUTPUT_UP:
    ld   a, 7                       ; rows 17-23 of the last third
    call GFX_SCROLL_ROWS
    ld   b, 23
    ld   a, ATTR_DEFAULT
    jp   GFX_CLEAR_ROW

; ============================================================================
; GFX_SCROLL_ROWS -- rows 1 to 16 + A move up one row, bitmap and attributes
; A scanline of a third holds its 8 rows' bytes in a run, so each scanline of the first two thirds
; is two copies (rows 1-7 to 0-6, the next third's row 0 to row 7) and of the last third one (its
; rows 1 to A to 0 to A - 1), in 32-byte blocks (GFX_LDI_BLOCKS).
; In:  A = the rows moved within the last third (1-7)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SCROLL_ROWS:
    push af
    add  a, 16                      ; the attributes: one block a row
    ld   hl, ATTR_ADDR + 32
    ld   de, ATTR_ADDR
    call GFX_LDI_BLOCKS
    ld   de, SCREEN_ADDR            ; scanline 0 of the first third
.scanline:
    ld   h, d
    ld   l, 32                      ; HL = the same scanline of row 1
    ld   a, d
    cp   HIGH SCREEN_ADDR + $10
    jr   nc, .last
    ld   a, 7
    call GFX_LDI_BLOCKS             ; rows 1-7 to 0-6
    ld   a, h
    add  a, 7
    ld   h, a                       ; the next third's row 0
    ld   a, 1
    call GFX_LDI_BLOCKS             ; to row 7; DE = the next scanline (or third)
    jr   .scanline
.last:
    pop  af
    push af
    call GFX_LDI_BLOCKS
    ld   e, a                       ; A = 0
    inc  d                          ; the next scanline
    ld   a, d
    cp   HIGH SCREEN_ADDR + $18
    jr   c, .scanline
    pop  af
    ret
    ASSERT LOW SCREEN_ADDR == 0 && LOW ATTR_ADDR == 0

; ============================================================================
; GFX_LDI_BLOCKS -- copy A blocks of 32 bytes (unrolled LDI: 16 T a byte, LDIR's 21)
; In:  HL = source, DE = destination, A = blocks (1-255)
; Out: HL, DE past the blocks, A = 0
; Destroys: F, BC
; ============================================================================
GFX_LDI_BLOCKS:
    REPT 32
    ldi
    ENDR
    dec  a
    jr   nz, GFX_LDI_BLOCKS
    ret

; ============================================================================
; GFX_SCROLL_TEXT_DOWN
; Mirror of GFX_SCROLL_TEXT_UP: scrolls rows 0-22 DOWN by one text row
; instead — row 0's content becomes row 1's, ... row 21's becomes
; row 22's. Row 0 itself is left UNTOUCHED for the caller to draw.
;
; Row-pair copies are processed in DESCENDING destination order (22,
; 21, ..., 1) for the same memmove reasoning as GFX_SCROLL_TEXT_UP's
; own header, mirrored: row 21's content must be read (as the source
; for dst=22) before it's overwritten (as the destination when
; dst=21) — "copy backward when dst > src".
; In:  none
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
    IFNDEF V2_PRODUCTION          ; RC: unused by the V2 images (legacy builds keep it; Leap-C never assembles
                                  ; it: GFX_COPY_ROW_BITMAP, which it calls, went with delta D26)
GFX_SCROLL_TEXT_DOWN:
    ld   hl, ATTR_ADDR + 22*32 - 1   ; last byte of rows 0-21 (source)
    ld   de, ATTR_ADDR + 23*32 - 1   ; last byte of rows 1-22 (dest) —
    ld   bc, 22*32                   ; overlapping, dst > src, needs the
    lddr                             ; backward-copying LDDR, not LDIR

    ld   a, 22
    ld   (GFX_SCROLL_DST_ROW), a
.row_loop:
    ld   a, (GFX_SCROLL_DST_ROW)
    dec  a
    ld   (GFX_SCROLL_SRC_ROW), a
    call GFX_COPY_ROW_BITMAP
    ld   a, (GFX_SCROLL_DST_ROW)
    dec  a
    ld   (GFX_SCROLL_DST_ROW), a
    jr   nz, .row_loop
    ret
    ENDIF

; ============================================================================
; GFX_SET_BORDER
; Sets the screen border colour via the ULA port ($FE) — same
; Spectrum-family hardware convention every other screen routine in
; this file already assumes (see GFX_CLS's attribute-byte layout for
; the sibling INK/PAPER encoding). Only bits 0-2 of the port select
; the border colour; the EAR/MIC bits (used by kernel/storage's tape
; routines) live higher up in the same byte and must NOT be
; disturbed here. REAL BUG FOUND AND FIXED: this used to just mask
; its own colour and write straight to the port, silently zeroing
; bits 3+ every time — the comment promised not to disturb EAR/MIC
; but there was no shadow anywhere for it to preserve them FROM, so
; the promise wasn't actually kept. Now reads PORT_FE_SHADOW
; (updated by both this routine and STORAGE_PULSE), replaces only
; the colour bits, and writes the merged byte back to both the port
; and the shadow.
; In:  A = colour (0-7; only the low 3 bits are used, same 0=black..
;      7=white encoding as every other colour value in this project)
; Out: none
; Destroys: AF, B (B holds the colour bits while the shadow byte is
;      read and merged — checked against all three current call
;      sites, none rely on B surviving, but this must stay accurate
;      for any future caller)
; ============================================================================
GFX_SET_BORDER:
    and  $07                     ; keep only the colour bits — never
                                 ; let stray high bits from the
                                 ; caller reach EAR/MIC
    ld   b, a                    ; stash the new colour bits
    ld   a, (PORT_FE_SHADOW)
    and  $F8                     ; clear the old colour bits, keep
                                 ; everything else (EAR/MIC) as-is
    or   b
    ld   (PORT_FE_SHADOW), a
    out  (PORT_ULA), a
    ret

; ============================================================================
; LEAP-C DELTA D28: text (release 1.2.0), from 2068-Forth v2.0 (its Words and keys milestone).
; FONT_TABLE is printable ASCII in code order, so a glyph is FONT_TABLE + (code - 32) * 8: one
; subtraction, where V2 tested ranges and then scanned a table of 31 punctuation pairs (up to
; 1,471 T for `$`). The cell's bitmap address is computed from the row and column, and the eight
; scanlines are copied unrolled; GFX_PRINT_STRING_ATTR sets the attribute from the address it
; already has instead of a bounds-checked GFX_SET_ATTR call. GFX_PUTCHAR keeps BC now.
; ============================================================================

; ============================================================================
; GFX_CHAR_TO_FONT_OFFSET -- the glyph pointer for a character code
; Despite the name this returns an absolute address: FONT_TABLE + (code - 32) * 8 for printable
; ASCII, BLOCK_GFX_SCRATCH (built here) for codes 128-143, UDG_TABLE + offset for 144-164.
; In:  A = character code
; Out: carry clear + HL = the 8-byte glyph; carry set if the code has no glyph (0-31, 127, 165 up;
;      GFX_PUTCHAR draws a space)
; Destroys: AF, DE, HL (BC is kept)
; ============================================================================
GFX_CHAR_TO_FONT_OFFSET:
    sub  " "
    cp   "~" - " " + 1
    jr   nc, .not_ascii
    ld   de, FONT_TABLE
.scale:                             ; HL = DE + A * 8 (A <= 94: A * 2 fits a byte)
    add  a, a
    ld   l, a
    ld   h, 0
    add  hl, hl
    add  hl, hl
    add  hl, de                     ; carry clear: no overflow
    ret

.not_ascii:
    add  a, " "                     ; A = the code again
    cp   128
    ret  c                          ; 0-31 and 127: carry set, no glyph
    sub  UDG_CODE_BASE              ; 144
    jr   c, .is_block_graphics      ; 128-143
    cp   UDG_COUNT
    ccf
    ret  c                          ; 165 up: no glyph
    ld   de, UDG_TABLE              ; 144-164: UDG_TABLE + (code - 144) * 8; the UDGs are RAM
    jr   .scale

.is_block_graphics:
    ; Codes 128-143 (A = code - 144: the same low nibble): the glyph is built in BLOCK_GFX_SCRATCH
    ; from the code's low nibble (bit0 = top-right, bit1 = top-left, bit2 = bottom-right, bit3 =
    ; bottom-left; each a solid 4x4 block). Each half is four identical rows: the low bit of its
    ; pair selects the right nibble ($0F), the next the left ($F0); E shifts down two bits between
    ; halves (top, then bottom). Delta D21's clean-room routine.
    push bc
    ld   e, a
    ld   hl, BLOCK_GFX_SCRATCH
    ld   b, 2                        ; two halves
.bg_half:
    ld   a, e
    rra                              ; carry = right quarter
    sbc  a, a                        ; $FF if ink, else $00
    and  $0F
    ld   c, a                        ; right nibble
    ld   a, e
    rra
    rra                              ; carry = left quarter
    sbc  a, a
    and  $F0
    or   c                           ; A = row pattern for this half
    ld   c, 4
.bg_row:
    ld   (hl), a
    inc  hl
    dec  c
    jr   nz, .bg_row
    srl  e
    srl  e                           ; next pair of quarters
    djnz .bg_half
    pop  bc
    ld   hl, BLOCK_GFX_SCRATCH
    or   a                           ; carry clear = success
    ret
    ASSERT (UDG_CODE_BASE & $0F) == 0

; ============================================================================
; GFX_CHAR_SETUP -- a character's glyph and its cell's bitmap address (GFX_PUTCHAR, _OVER, and the
; EXROM's GFX_PUTCHAR_BOLD)
; In:  A = character code, B = row (0-23), C = column (0-31)
; Out: carry set if the position is off the grid; else carry clear, HL = the glyph (a code with no
;      glyph: the space's), DE = the cell's scanline-0 bitmap address
; Destroys: AF, DE, HL (BC is kept)
; ============================================================================
GFX_CHAR_SETUP:
    ld   d, a                       ; the character; A is scratch for the checks
    ld   a, b
    cp   24
    ccf
    ret  c
    ld   a, c
    cp   32
    ccf
    ret  c
    ld   a, d
    call GFX_CHAR_TO_FONT_OFFSET    ; keeps BC
    jr   nc, .have_glyph
    ld   hl, FONT_TABLE             ; no glyph: a space
.have_glyph:
    ; the cell's address: 010tt000 rrrccccc (tt = row / 8, rrr = row MOD 8, ccccc = column)
    ld   a, b
    and  $18
    or   HIGH SCREEN_ADDR
    ld   d, a
    ld   a, b
    rrca
    rrca
    rrca
    and  $E0
    add  a, c                       ; carry clear: rrr00000 + column < 256
    ld   e, a
    ret
    ASSERT LOW SCREEN_ADDR == 0 && (HIGH SCREEN_ADDR & $1F) == 0

; ============================================================================
; GFX_PUTCHAR -- draw one character in the grid (bitmap only; the attribute is not touched)
; In:  A = character code, B = row (0-23), C = column (0-31)
; Out: carry set if the position is off the grid (nothing drawn); else carry clear and DE = the
;      cell's top-left bitmap address + 8 scanlines (D + 8: the cell's attribute is at
;      ATTR_ADDR + (D / 8 - 9) * 256 + E)
; Destroys: AF, DE, HL (BC is kept)
; ============================================================================
GFX_PUTCHAR:
    call GFX_CHAR_SETUP
    ret  c
    REPT 7                          ; the 8 scanlines, 256 bytes apart
    ld   a, (hl)
    ld   (de), a
    inc  hl
    inc  d
    ENDR
    ld   a, (hl)
    ld   (de), a
    inc  d
    ret

; ============================================================================
; GFX_PUTCHAR_OVER -- GFX_PUTCHAR by exclusive-or (over(1))
; In, Out, Destroys: as GFX_PUTCHAR
; ============================================================================
GFX_PUTCHAR_OVER:
    call GFX_CHAR_SETUP
    ret  c
    REPT 7
    ld   a, (de)
    xor  (hl)
    ld   (de), a
    inc  hl
    inc  d
    ENDR
    ld   a, (de)
    xor  (hl)
    ld   (de), a
    inc  d
    ret
    ENDIF
    IFNDEF GFX_NO_EDITOR_TEXT            ; Leap-C (delta D12): GFX_PUTCHAR_BOLD and GFX_PRINT_STRING are
                                         ; the EXROM editor's only, so they are assembled in the EXROM
; ============================================================================
; GFX_PUTCHAR_BOLD
; Plots one character with a synthesized bold effect: each scanline
; byte is ORed with itself shifted right by one pixel (via RRCA),
; widening every stroke by a pixel rather than needing a whole second
; font. Verified numerically against representative font bytes before
; writing this — separated strokes (like 'A''s legs) stay separated,
; just each a pixel wider; solid bars extend cleanly; space stays
; blank. Used for keyword highlighting in the editor.
; In:  A = ASCII character, B = row (0-23), C = column (0-31)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_PUTCHAR_BOLD:
    call GFX_CHAR_SETUP
    ret  c                                 ; out of range — see
                                          ; GFX_PUTCHAR's own comment
    ld   b, 8
.scanline_loop:
    ld   a, (hl)
    ld   c, a                    ; C = original byte — B is the scanline
                                 ; counter here, not the row parameter
                                 ; anymore (GFX_CHAR_SETUP already
                                 ; consumed that), so C is free to use
    rrca                          ; shift right 1, wrapping bit0 into
                                 ; bit7 — harmless here since font bytes
                                 ; only use their top 5 bits, bit0 is
                                 ; always 0 in every glyph we have
    or   c                         ; OR with the original -> widened stroke
    ex   de, hl
    ld   (hl), a
    inc  h
    ex   de, hl
    inc  hl
    djnz .scanline_loop
    ret

; ============================================================================
; GFX_PRINT_STRING
; Prints a null-terminated string starting at a character-grid position,
; advancing one column per character. Does not wrap at end of line or
; scroll — caller's responsibility to stay in bounds (TODO for a real
; PRINT statement implementation later).
; In:  HL = pointer to null-terminated string, B = row, C = column
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_PRINT_STRING:
.loop:
    ld   a, (hl)
    or   a
    ret  z
    push hl
    push bc                  ; GFX_PUTCHAR destroys BC entirely (see its
                             ; own header) — without saving it here, the
                             ; row in B would be garbage after the first
                             ; character, corrupting every one after it.
                             ; Caught by checking GFX_PUTCHAR's contract
                             ; against what this loop assumed, not by
                             ; running it.
    call GFX_PUTCHAR
    pop  bc
    pop  hl
    inc  hl
    inc  c
    jr   .loop

    ENDIF
    IFNDEF GFX_EDITOR_TEXT_ONLY
; ============================================================================
; GFX_PRINT_STRING_ATTR
; Prints a null-terminated string with BASIC-style attributes. At column 32
; it wraps; past row 23 it scrolls all 24 output rows and continues on the
; newly cleared bottom row. It also sets the attribute cell
; under each character to a given byte — built for basic/'s INK/PAPER/
; FLASH/INVERSE support, which needs printed text to actually carry
; the current attribute state, unlike every other caller of
; GFX_PRINT_STRING (HELP screens, error messages, the editor), which
; always wants the plain default/inherited attribute and must NOT be
; affected by this. Kept as a separate routine rather than adding an
; attribute parameter to GFX_PRINT_STRING itself, so none of those
; existing callers need to change.
;
; The attribute value is stashed in PRINT_ATTR_SCRATCH (a real RAM
; sysvar, sysvars.inc), not a register — GFX_PUTCHAR destroys AF/DE/HL
; (and, before Leap-C delta D28, BC too), so a bare register holding the
; attribute would not survive the call. This
; is the same "value must survive a call -> use memory, not a
; register" pattern this project has hit repeatedly (see
; MEM_LINE_FIRST/NEXT's own DE-clobbering history) — BUT NOTE: this
; scratch value must live in RAM specifically, never in a `DB` byte
; embedded in this file's own code. A `DB` byte sits in ROM once
; assembled, and this entire codebase assembles into ROM — writing to
; a ROM-resident "variable" via `ld (addr), a` is a silent no-op on
; real hardware, so the byte always reads back its compile-time
; initial value, never whatever was "written" at runtime. This was a
; real, shipped bug: an earlier version of this routine used exactly
; that pattern (a local `.attr_scratch: DB 0`), and every PRINT wrote
; attribute $00 (black-on-black) regardless of INK/PAPER, found via a
; real memory dump showing GFX_CLS's own fill elsewhere on screen was
; correctly $38 while PRINT's own writes were stuck at $00. See
; docs/programmers_reference.md's "INK / PAPER / FLASH / INVERSE /
; OVER" section for the full writeup.
; In:  HL = pointer to null-terminated string, B = row, C = column,
;      A = attribute byte to set at every printed cell, D = OVER flag
; Out: B/C = row/column immediately after the final character
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_PRINT_STRING_ATTR:
    ld   (PRINT_ATTR_SCRATCH), a
    ld   a, d
    ld   (PRINT_OVER_SCRATCH), a
.loop:
    ld   a, (hl)
    or   a
    ret  z
    push hl
    ld   a, (PRINT_OVER_SCRATCH)
    or   a
    ld   a, (hl)                     ; (LD keeps the flags)
    jr   nz, .over
    call GFX_PUTCHAR                 ; (D28: keeps BC; DE = the cell + 8 scanlines)
    jr   .glyph_done
.over:
    call GFX_PUTCHAR_OVER
.glyph_done:
    ld   a, d                        ; LEAP-C DELTA D28: the attribute from the address GFX_PUTCHAR
    rrca                             ; left (010tt000 + 8: bits 3-4 hold tt + 1), not a
    rrca                             ; bounds-checked GFX_SET_ATTR call, now gone (B and C are on the grid)
    rrca                             ; 9 + tt
    add  a, HIGH ATTR_ADDR - 9
    ld   d, a                        ; DE = ATTR_ADDR + row * 32 + column
    ld   a, (PRINT_ATTR_SCRATCH)
    ld   (de), a
    pop  hl
    inc  hl
    inc  c
    ld   a, c
    cp   32
    jr   c, .loop
    ld   c, 0
    inc  b
    ld   a, b
    cp   24
    jr   c, .loop
    push hl
    call GFX_SCROLL_OUTPUT_UP
    pop  hl
    ld   b, 23
    ld   c, 0
    jr   .loop
    ASSERT LOW ATTR_ADDR == 0 && HIGH ATTR_ADDR == HIGH SCREEN_ADDR + $18

; ============================================================================
; GFX_ATTR_SWAP (internal — not in kernel_api.inc)
; Shared address computation and ink/paper bit-swap for
; GFX_INVERT_ATTR and GFX_INVERT_ATTR_STATIC — written once here rather
; than duplicated in both, given how much trouble duplicated addressing
; logic has already caused in this project. The bit-swap instruction
; sequence was verified numerically against all 256 possible attribute
; byte values before being trusted — see docs/programmers_reference.md's
; kernel/graphics section.
;
; REAL BUG FOUND AND FIXED (word-wrap cursor investigation): this had
; no bounds check at all, unlike GFX_SET_ATTR's own row*32+col address
; computation (see that routine's own comment — it already documents
; this exact class of gap). EDITOR_WRAP_OFFSET_TO_ROWCOL (kernel/
; editor) legitimately returns column 32 — one past the valid 0-31
; range — whenever the cursor sits exactly at the end of a full 32-
; character wrapped row (a real, ordinary case, not a rare edge
; condition: it happens on every line whose content is ever an exact
; multiple of 32 chars at the cursor's position). Column 32 fed
; straight into row*32+col addressing lands exactly on (row+1,
; column 0) instead — one cell into the START of the next physical
; screen row, silently corrupting whatever's shown there. Traced from
; a real debug.bin dump (word-wrap "phantom cursor block" report):
; row+1's bitmap was blank (correctly cleared) but its column-0
; attribute byte was stuck inverted — exactly what an out-of-range
; write here produces, and exactly why it persisted even after the
; row's own leftover-row cleanup ran earlier in the same redraw pass
; (this call happens AFTER that cleanup, re-dirtying the cell it had
; just cleared). Fixed with the same bounds check GFX_SET_ATTR already
; has, returning early with carry SET on out-of-range — both callers
; below now check `ret c` immediately after this call, before doing
; anything else, so an out-of-range request is a clean no-op instead
; of a silent corruption, matching this project's now-consistent "clip
; rather than corrupt" answer to this class of bug.
; In:  B = row (0-23), C = column (0-31)
; Out: HL = address of the attribute byte, A = swapped ink/paper with
;      FLASH/BRIGHT preserved unchanged (caller decides whether to
;      force FLASH on before writing it back). Carry SET and nothing
;      else valid if B/C were out of range — caller must check this
;      before using HL/A.
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_ATTR_SWAP:
    call GFX_CELL_ATTR_ADDR
    ret  c

    ld   a, (hl)
    ld   b, a                     ; B = original attribute byte

    and  %00000111                 ; A = ink bits (low position)
    rlca
    rlca
    rlca                             ; shift into paper's bit position
    ld   c, a                         ; C = ink bits, now in paper position

    ld   a, b
    and  %00111000                     ; A = paper bits
    rrca
    rrca
    rrca                                 ; shift into ink's bit position
    or   c                                ; combine with the shifted ink
    ld   c, a                              ; C = swapped ink/paper (bits 5-0)

    ld   a, b
    and  %11000000                          ; A = FLASH/BRIGHT, unchanged
    or   c                                    ; A = swapped attribute,
                                             ; FLASH/BRIGHT as they were
    or   a                                    ; explicit carry clear —
                                             ; the last op above (or) is
                                             ; already guaranteed to
                                             ; clear carry, but spelled
                                             ; out for anyone reading
                                             ; this contract without
                                             ; re-deriving it
    ret

; ============================================================================
; GFX_INVERT_ATTR
; Swaps ink and paper in the attribute byte at one character cell AND
; sets the hardware FLASH bit — the ULA itself then auto-blinks that
; cell between inverted and normal colors, ~1.5Hz, entirely in hardware.
; No interrupt or timer code needed on our end (kernel/interrupt doesn't
; exist yet, but this doesn't need it) — offloading blink timing to the
; ULA is the standard Spectrum-family way to do this. Used as the
; editor's cursor indicator specifically — for a STATIC inverted
; highlight that shouldn't blink (e.g. a status bar), use
; GFX_INVERT_ATTR_STATIC instead. Using this routine for
; basic/'s new status line by mistake was a real bug: the whole status
; bar inherited the cursor's blink, which is why it appeared to
; "flash" — caught from a screenshot and fixed by splitting this
; routine's address/swap logic out into GFX_ATTR_SWAP so both variants
; share it rather than duplicating it.
; In:  B = row (0-23), C = column (0-31)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_INVERT_ATTR:
    call GFX_ATTR_SWAP
    ret  c                                    ; out of range — GFX_ATTR_
                                             ; SWAP's own bounds check
                                             ; already fired; nothing to
                                             ; write, HL/A aren't valid
    or   %10000000                            ; force FLASH on — the ULA
                                             ; hardware itself blinks any
                                             ; cell with this bit set,
                                             ; ~1.5Hz, entirely in
                                             ; hardware — no interrupt or
                                             ; timer code needed on our
                                             ; end at all. Combined with
                                             ; the ink/paper swap above,
                                             ; this alternates between
                                             ; inverted and normal colors
                                             ; automatically.
    ld   (hl), a
    ret

; ============================================================================
; GFX_INVERT_ATTR_STATIC
; Same ink/paper swap as GFX_INVERT_ATTR, WITHOUT forcing the hardware
; FLASH bit — a genuinely static inverted highlight, for things like a
; status bar that should stand out visually but not blink like the
; cursor does. FLASH is left exactly as it already was at that cell
; (normally off, since nothing else sets it) rather than forced either
; way.
; In:  B = row (0-23), C = column (0-31)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
    IFNDEF V2_PRODUCTION          ; RC: unused by the V2 images (legacy builds keep it)
GFX_INVERT_ATTR_STATIC:
    call GFX_ATTR_SWAP
    ret  c                                    ; out of range — see
                                             ; GFX_INVERT_ATTR's own
                                             ; identical check just above
    ld   (hl), a
    ret
    ENDIF

; LEAP-C DELTA D28: GFX_SET_ATTR removed: its callers (V2's GFX_PRINT_STRING_ATTR, GFX_CLEAR_ROW and
; GFX_WRITE_PIXEL) now write the attribute from an address they already have.

; ============================================================================
; GFX_SET_MODE
; Switches between Normal and High Resolution Graphics video modes —
; MODE's mechanism. Real port $FF write, done safely: $FF is a shared,
; multi-function register (see hardware.inc's PORT_SCLD comment for
; the full bit layout), so this always reads PORT_FF_SHADOW, replaces
; only the video-mode bits (0-2), and writes the merged byte back to
; both the shadow and the port — same established pattern as GFX_SET_
; BORDER already uses for port $FE, adopted here from the start rather
; than repeating the bug that pattern exists to prevent (an earlier
; version of GFX_SET_BORDER had no shadow and silently zeroed bits it
; didn't mean to touch).
;
; Entering High Resolution Graphics mode clears its attribute region
; (SECOND_DISPLAY_ADDR, 6144 bytes) to ATTR_DEFAULT first — that
; memory has never been written by anything in this ROM before (real
; hardware-topology consequence of the RAM migration: this region is
; now genuinely unused by anything except this mode, not just
; "probably zero"), so its content is whatever was there at power-on,
; not necessarily zero. Left uninitialized, the first real pixels
; drawn there would render with an unpredictable — possibly identical
; ink/paper — color. Clearing to ATTR_DEFAULT (PAPER 7/INK 0, the same
; default GFX_CLS already uses) rather than to raw zero deliberately
; avoids repeating the exact "invisible white-on-white" class of
; confusion a real test program already hit once with INK/PAPER (see
; docs/programmers_reference.md's Tier-2 session writeup) — zero would
; decode as PAPER 0/INK 0 here, black-on-black, same trap.
; In:  A = mode (0 = Normal, 1 = High Resolution Graphics — this
;      project's own friendly numbering, NOT the raw port $FF value;
;      caller (BASIC_STMT_MODE) validates this is 0 or 1 first)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
; ============================================================================
; GFX_SET_MODE
; Switches video mode via port $FF (PORT_SCLD) — 0 (Normal) or 1 (High
; Resolution Graphics). Mode 2 (64-Column) was removed 2026-08-20 —
; real overhead vs. value trade-off, freed for more core language
; features (see this project's own working memory for the accounting;
; the routine itself, GFX_SET_PALETTE, and the PALETTE statement were
; the only things that existed purely to serve it).
; In:  A = mode (0 or 1 — BASIC_STMT_MODE validates this before
;      calling)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SET_MODE:
    ld   (GFX_MODE), a
    cp   1
    jr   z, .highres

    ; Normal (or any other value — BASIC_STMT_MODE validates 0-1, so
    ; this path is really just "0"): video byte = 0, bits 0-2 clear
    ld   a, (PORT_FF_SHADOW)
    and  %11111000
    jr   .write_port

.highres:
    ld   a, (PORT_FF_SHADOW)
    and  %11111000                 ; clear bits 0-2, keep 3-7 (ink/
                                   ; paper select, INTEN, EXROM —
                                   ; none of them this project's to
                                   ; disturb)
    or   2

.write_port:
    ld   (PORT_FF_SHADOW), a
    out  (PORT_SCLD), a

    ld   a, (GFX_MODE)
    cp   1
    jr   z, .clear_highres
    ret                              ; Normal mode needs no memory
                                    ; initialization — the primary
                                    ; screen is already maintained by
                                    ; every existing routine

.clear_highres:
    ; clear the High Resolution Graphics attribute region to
    ; ATTR_DEFAULT
    ld   hl, SECOND_DISPLAY_ADDR
    ld   de, SECOND_DISPLAY_ADDR + 1
    ld   bc, 6144 - 1
    ld   a, ATTR_DEFAULT
    ld   (hl), a
    ldir
    ret

; ============================================================================
; GFX_CLEAR_ROW -- clear one text row (bitmap and attributes) to blank cells of attribute A
; LEAP-C DELTA D26: the bytes 32 spaces would leave (the space glyph is 8 zero bytes) written
; directly, as Leap V2's own later GFX_CLEAR_ROW and 2068-Forth v2.0's; V2's drew 32 spaces and set 32
; attributes through GFX_PUTCHAR and GFX_SET_ATTR (about 33,000 T).
; In:  B = row (0-23), A = the attribute
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_CLEAR_ROW:
    push af
    ld   c, 0
    call GFX_CELL_ATTR_ADDR         ; HL = the row's first attribute (BC kept)
    pop  af
    ld   c, GFX_COLS
.attr:
    ld   (hl), a
    inc  l                          ; (a row's 32 attributes never cross a page)
    dec  c
    jr   nz, .attr
    ld   a, b
    call GFX_ROW_BASE_ADDR          ; HL = scanline 0, column 0
    ld   e, l
    xor  a
    ld   c, 8
.scan:
    ld   b, GFX_COLS
.byte:
    ld   (hl), a
    inc  l
    djnz .byte
    ld   l, e                       ; column 0,
    inc  h                          ; the next scanline
    dec  c
    jr   nz, .scan
    ret

; LEAP-C DELTA D8: GFX_CLEAR_ROW_TEXT (the status bar's bitmap-only row clear) removed: the
; Leap-C shell clears rows itself (src/shell/shell.asm SH_CLEAR_ROW), and nothing else calls it.

; ============================================================================
; LEAP-C DELTA D25: pixels and lines (release 1.2.0). V2's GFX_PIXEL_ADDR_SETUP, GFX_WRITE_PIXEL,
; GFX_LINE (memory cells, two MATH_COMPARE16 calls and a full address per pixel: about 1,450 T a
; pixel) and BIT_MASK_TABLE are replaced by a port of 2068-Forth v2.0's line (its Display speed
; milestone): the major-axis Bresenham loop with r, dmin and dmaj in the alternate registers, the
; address and mask stepped from pixel to pixel, the attribute written only where the cell (mode 1:
; the 8x1 byte) changes. Leap-C keeps its own rules: draw() moves off-screen ends to the edge before
; GFX_LINE (so the ends here are bytes on the screen and the line never leaves it), and over(1)
; draws by exclusive-or. The pixels and attributes are those of V2's loop for every line
; (tools/linetest.py); see platform/UPSTREAM.md.
;
; LINE's flags, in E while drawing: bit 0 y is the major axis, bit 1 x goes left, bit 2 y goes up,
; bit 3 mode 1 (8x1 colour), bit 4 the attribute is pending, bit 5 over (XOR). The alternate
; registers hold r (HL'), dmin (DE') and dmaj (BC'); nothing else in Leap-C uses them.
; ============================================================================

; ============================================================================
; GFX_PIXEL_AT -- a pixel's bitmap address and bit mask
; In:  C = x (0-255), B = y (0-191; not checked)
; Out: HL = the bitmap byte's address, A = the bit mask (bit 7 = leftmost pixel)
; Destroys: F (BC and DE are kept)
; ============================================================================
GFX_PIXEL_AT:
    ld   a, b
    and  7
    ld   h, a
    ld   a, b
    rra
    rra
    rra
    and  $18
    or   h
    or   HIGH SCREEN_ADDR
    ld   h, a                       ; 010tt sss: the third, the scanline
    ld   a, b
    rla
    rla
    and  $E0
    ld   l, a
    ld   a, c
    rrca
    rrca
    rrca
    and  $1F
    or   l
    ld   l, a                       ; rrr ccccc: the row in the third, the column
    ld   a, c
    and  7
    push bc
    ld   b, a
    inc  b
    ld   a, 1
.mask:
    rrca
    djnz .mask
    pop  bc
    ret
    ASSERT LOW SCREEN_ADDR == 0

; ============================================================================
; GFX_READ_PIXEL -- whether a pixel is set (point())
; In:  C = x (0-255), B = y (0-191, the caller checks)
; Out: A = 1 if the pixel is set, 0 if not
; Destroys: AF, HL
; ============================================================================
GFX_READ_PIXEL:
    call GFX_PIXEL_AT
    and  (hl)
    ret  z
    ld   a, 1
    ret

; ============================================================================
; GFX_PLOT_CLIPPED -- one pixel, set (or XORed) and coloured; nothing off the screen
; In:  HL = x, DE = y (signed 16-bit), A = the attribute byte, B = over (0: set, else XOR)
; Out: none
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_PLOT_CLIPPED:
    ld   c, a
    ld   a, h
    or   d
    ret  nz                         ; x or y outside 0-255
    ld   a, e
    cp   192
    ret  nc
    ld   d, c                       ; D = the attribute
    ld   a, b
    or   a
    ld   b, e                       ; B = y
    ld   c, l                       ; C = x
    ld   e, $10                     ; the attribute pending
    jr   z, .set
    ld   e, $30                     ; ... and over
.set:
    ld   a, (GFX_MODE)
    add  a, a
    add  a, a
    add  a, a
    or   e
    ld   e, a                       ; bit 3: mode 1
    call GFX_PIXEL_AT
    ld   c, a
    ld   b, 1                       ; one point: GFX_LINE's loop ends after it
    jr   GFX_LINE.draw

; ============================================================================
; GFX_LINE -- the points of Bresenham's line from (X0, Y0) to (X1, Y1), both ends drawn, each set
; (OR; over: XOR) and giving its cell the attribute. The major axis (the larger of |dx| and |dy|; x
; on a tie) steps at every point, the minor one when the error r (0 to dmaj - 1, from dmaj / 2)
; reaches dmaj after adding dmin: the points of V2's e2 form (err = dx - dy).
; In:  GFX_LINE_X0/Y0/X1/Y1 (bytes, on the screen: draw() moves the ends there), GFX_LINE_ATTR,
;      GFX_LINE_OVER
; Out: none
; Destroys: AF, BC, DE, HL, BC', DE', HL'
; ============================================================================
GFX_LINE:
    ld   a, (GFX_MODE)
    ld   c, a                       ; becomes bit 3 after the three shifts below
    ld   a, (GFX_LINE_Y0)
    ld   b, a
    ld   a, (GFX_LINE_Y1)
    call LINE_DELTA                 ; A = |dy|, carry: up
    rl   c
    ld   d, a
    ld   a, (GFX_LINE_X0)
    ld   b, a
    ld   a, (GFX_LINE_X1)
    call LINE_DELTA                 ; A = |dx|, carry: left
    rl   c
    ld   e, a
    cp   d                          ; carry: |dx| < |dy|
    rl   c
    bit  0, c
    jr   z, .xmaj
    ld   e, d                       ; E = dmaj = |dy|
    ld   d, a                       ; D = dmin = |dx|
.xmaj:
    ld   b, e                       ; B = dmaj
    push de
    exx
    pop  bc                         ; C = dmaj, B = dmin
    ld   e, b
    xor  a
    ld   d, a                       ; DE' = dmin
    ld   b, a                       ; BC' = dmaj
    ld   a, c
    srl  a
    ld   l, a
    ld   h, d                       ; HL' = r = dmaj / 2
    exx
    ld   a, (GFX_LINE_OVER)
    or   a
    ld   a, c
    jr   z, .flags
    or   $20                        ; over
.flags:
    or   $10                        ; the first point's attribute
    ld   e, a                       ; E = the flags
    ld   a, (GFX_LINE_ATTR)
    ld   d, a                       ; D = the attribute
    inc  b                          ; B = the points: dmaj + 1 (0: 256)
    push bc
    ld   bc, (GFX_LINE_X0)          ; C = x0, B = y0
    call GFX_PIXEL_AT
    pop  bc
    ld   c, a                       ; C = the mask, HL = the address
.draw:
    bit  4, e
    call nz, LINE_ATTR
    ld   a, (hl)
    xor  c
    bit  5, e
    jr   nz, .put                   ; over: XOR
    or   c                          ; else set: (b XOR m) OR m = b OR m
.put:
    ld   (hl), a
    dec  b
    ret  z                          ; the last point
    bit  0, e                       ; the major axis
    call z, LINE_XSTEP
    bit  0, e
    call nz, LINE_YSTEP
    exx                             ; r += dmin; the minor axis steps if r reaches dmaj (r -= dmaj)
    add  hl, de                     ; (r, dmin, dmaj < 256: no carry out, so SBC subtracts exactly)
    sbc  hl, bc
    jr   nc, .minor
    add  hl, bc
    exx
    jr   .draw
.minor:
    exx
    bit  0, e
    call nz, LINE_XSTEP
    bit  0, e
    call z, LINE_YSTEP
    jr   .draw
    ASSERT GFX_LINE_Y0 == GFX_LINE_X0 + 1

; ============================================================================
; LINE_XSTEP, LINE_YSTEP -- the address and mask one pixel on in x (left if E bit 1) or y (up if E
; bit 2); where the byte (mode 1) or the cell (mode 0) changes, E bit 4: the attribute is written
; with the next pixel. The line stays on the screen (its ends are on it), except for a step after
; the last point, which the loop never takes.
; In:  HL = the address, C = the mask, E = LINE's flags
; Destroys: AF
; ============================================================================
LINE_YSTEP:
    bit  2, e
    jr   nz, .up
    inc  h
    ld   a, h
    and  7
    jr   nz, LINE_PEND_HIRES        ; the same cell row
    ld   a, l
    add  a, 32
    ld   l, a
    jr   c, LINE_PEND               ; the next third (H already is)
    ld   a, h
    sub  8
    ld   h, a
    jr   LINE_PEND
.up:
    ld   a, h
    dec  h
    and  7
    jr   nz, LINE_PEND_HIRES
    ld   a, l
    sub  32
    ld   l, a
    jr   c, LINE_PEND               ; the third above (H already is)
    ld   a, h
    add  a, 8
    ld   h, a
    jr   LINE_PEND
LINE_XSTEP:
    bit  1, e
    jr   nz, .left
    rrc  c
    ret  nc
    inc  l
    jr   LINE_PEND
.left:
    rlc  c
    ret  nc
    dec  l
    jr   LINE_PEND
LINE_PEND_HIRES:
    bit  3, e
    ret  z
LINE_PEND:
    set  4, e                       ; the attribute is written with the next pixel
    ret

; ============================================================================
; LINE_ATTR -- colour the bitmap byte at HL with D: mode 0 its cell's attribute, mode 1 (E bit 3)
; its own attribute byte at HL + $2000 (the second display file is laid out like the bitmap)
; In:  HL = the bitmap byte, D = the attribute, E = LINE's flags
; Out: E bit 4 (the attribute pending) clear
; Destroys: AF
; ============================================================================
LINE_ATTR:
    res  4, e
    bit  3, e
    jr   nz, .byte
    push hl
    ld   a, h
    rrca
    rrca
    rrca
    and  3
    or   HIGH ATTR_ADDR
    ld   h, a                       ; the cell: ATTR_ADDR + the third * 256 + L
    ld   (hl), d
    pop  hl
    ret
.byte:
    set  5, h
    ld   (hl), d
    res  5, h
    ret
    ASSERT LOW ATTR_ADDR == 0 && SECOND_DISPLAY_ADDR == SCREEN_ADDR + $2000

; LINE_DELTA -- A = |A - B|, carry if A < B. Destroys: F
LINE_DELTA:
    sub  b
    ret  nc
    neg                             ; (A was not 0: NEG sets the carry)
    ret

; GFX_FILL/GFX_FILL_PUSH/GFX_FILL_POP/GFX_FILL_TRY_NEIGHBOR/GFX_FILL_
; VISITED_CHECK_SET and GFX_CIRCLE/GFX_CIRCLE_PLOT_OFFSET/PLOT_POLES/
; PLOT_GENERAL all removed 2026-09-19 (Phase 0 P0.4): CIRCLE and FILL
; are now a combined loadable RAM extension (rom/extensions/
; shapes.asm), a self-contained port of this exact code (SHAPES_-
; prefixed routines there) -- see that file's own header for the
; full reasoning. (BIT_MASK_TABLE, which the reasoning kept here, went
; with Leap-C delta D25: GFX_PIXEL_AT makes its masks.)

; ---- screen-row base addresses, computed and verified numerically
; (see file header) rather than derived by hand from the bit-shuffle
; formula ----
; (PUNCT_CHAR_TABLE, V2's punctuation -> font index scan, went with Leap-C delta D28.)

; Block-graphics (128-143) and UDG (144-164) character-code ranges —
; see GFX_CHAR_TO_FONT_OFFSET's .is_block_graphics/.is_udg. UDG_COUNT
; itself lives in include/sysvars.inc alongside UDG_TABLE (it sizes
; that RAM block, not just this code-range check); UDG_CODE_BASE is
; purely a character-code constant, so it stays here with the rest of
; this file's character-range logic instead.
UDG_CODE_BASE EQU 144

ROW_BASE_TABLE:
    DW   $4000, $4020, $4040, $4060, $4080, $40A0, $40C0, $40E0
    DW   $4800, $4820, $4840, $4860, $4880, $48A0, $48C0, $48E0
    DW   $5000, $5020, $5040, $5060, $5080, $50A0, $50C0, $50E0

; ---- font: printable ASCII, codes 32-126 in code order (95 glyphs, 8 bytes each): the glyph of a
; code is FONT_TABLE + (code - 32) * 8 (Leap-C delta D28, as 2068-Forth v2.0's; V2's order was
; space, 0-9, A-Z, a-z, then punctuation reached through PUNCT_CHAR_TABLE). The glyphs are V2's with
; Leap-C deltas D8 (C's [ ] { } | ~ ^ \, in the letters' columns $80-$08 except '\', bit 0 clear
; for GFX_PUTCHAR_BOLD), D13 and D24. ----
FONT_TABLE:
    ; ' '
    DB   $00, $00, $00, $00, $00, $00, $00, $00
    ; '!'
    DB   $20, $20, $20, $20, $20, $00, $20, $00
    ; '"'
    DB   $50, $50, $00, $00, $00, $00, $00, $00
    ; '#'
    DB   $50, $50, $F8, $50, $F8, $50, $50, $00
    ; '$'
    DB   $20, $78, $A0, $70, $28, $F0, $20, $00
    ; '%'
    DB   $88, $10, $20, $20, $40, $88, $00, $00
    ; '&'
    DB   $60, $90, $60, $68, $90, $98, $68, $00
    ; '''
    DB   $20, $20, $00, $00, $00, $00, $00, $00
    ; '('
    DB   $10, $20, $40, $40, $40, $20, $10, $00
    ; ')'
    DB   $40, $20, $10, $10, $10, $20, $40, $00
    ; '*' — vertical spine + diagonal rays converging at center,
    ; six-pointed asterisk. Same review discipline (needed once B=*
    ; was added for basic/'s multiplication operator)
    DB   $00, $10, $54, $38, $54, $10, $00, $00
    ; '+'
    DB   $00, $20, $20, $F8, $20, $20, $00, $00
    ; ','
    DB   $00, $00, $00, $00, $00, $20, $20, $40
    ; '-'
    DB   $00, $00, $00, $F8, $00, $00, $00, $00
    ; '.'
    DB   $00, $00, $00, $00, $00, $00, $20, $00
    ; '/' — diagonal stroke, lower-left to upper-right. Designed and
    ; visually reviewed as ASCII art before committing (see this
    ; project's established discipline for glyphs — needed once V=/
    ; was added for basic/'s division operator)
    DB   $00, $04, $08, $10, $20, $40, $00, $00
    ; '0'
    DB   $70, $88, $98, $A8, $C8, $88, $70, $00
    ; '1'  (Leap-C delta D13: a flag and a full base, unlike 'l')
    DB   $20, $60, $A0, $20, $20, $20, $F8, $00
    ; '2'
    DB   $70, $88, $08, $10, $20, $40, $F8, $00
    ; '3'
    DB   $F0, $08, $10, $30, $08, $88, $70, $00
    ; '4'
    DB   $10, $30, $50, $90, $F8, $10, $10, $00
    ; '5'
    DB   $F8, $80, $F0, $08, $08, $88, $70, $00
    ; '6'
    DB   $30, $40, $80, $F0, $88, $88, $70, $00
    ; '7'
    DB   $F8, $08, $10, $20, $40, $40, $40, $00
    ; '8'
    DB   $70, $88, $88, $70, $88, $88, $70, $00
    ; '9'
    DB   $70, $88, $88, $78, $08, $10, $60, $00
    ; ':'
    DB   $00, $20, $00, $00, $20, $00, $00, $00
    ; ';'
    DB   $00, $20, $00, $00, $20, $20, $40, $00
    ; '<' — simple angle-bracket chevron, apex pointing left, single-
    ; pixel diagonal strokes converging on the left edge (column 0)
    ; and opening back out to column 3 top/bottom — stays within the
    ; same column range ($80-$08) every letter/digit glyph already
    ; uses, unlike '/' which intentionally reaches further right.
    ; Needed once basic/'s new IF condition relational operators
    ; (kernel/io's SYMBOL SHIFT+R) made '<' a real, typeable character
    ; rather than only usable via LOAD/hand-edited program text.
    ; Visually reviewed as ASCII art before committing, same discipline
    ; as every other glyph here.
    DB   $10, $20, $40, $80, $40, $20, $10, $00
    ; '='
    DB   $00, $00, $F8, $00, $F8, $00, $00, $00
    ; '>' — exact horizontal mirror of '<' within the same column
    ; range, apex pointing right toward column 4 instead of column 0.
    ; Needed alongside '<' for the same reason (kernel/io's SYMBOL
    ; SHIFT+T).
    DB   $40, $20, $10, $08, $10, $20, $40, $00
    ; '?' — top hook reuses '2''s exact top-curve shape (rows 0-2:
    ; arc, then right-hand downstroke), tapering to a single point at
    ; row 4 instead of '2''s full-width bottom bar, then a blank row
    ; and a centered dot — same gap-then-dot closing shape already
    ; established by '!' elsewhere in this table. Designed and
    ; visually reviewed as ASCII art before committing, same
    ; discipline as every other glyph here — not transcribed from any
    ; real ROM's font. Needed once kernel/io's SYMBOL SHIFT+C mapping
    ; was added (see that table's header) — mapping and glyph always
    ; ship together per this project's established rule.
    DB   $70, $88, $08, $10, $20, $00, $20, $00
    ; '@'
    DB   $70, $88, $B0, $B0, $80, $88, $70, $00
    ; 'A'
    DB   $20, $50, $88, $88, $F8, $88, $88, $00
    ; 'B'
    DB   $F0, $88, $88, $F0, $88, $88, $F0, $00
    ; 'C'
    DB   $70, $88, $80, $80, $80, $88, $70, $00
    ; 'D'
    DB   $F0, $88, $88, $88, $88, $88, $F0, $00
    ; 'E'
    DB   $F8, $80, $80, $F0, $80, $80, $F8, $00
    ; 'F'
    DB   $F8, $80, $80, $F0, $80, $80, $80, $00
    ; 'G'
    DB   $70, $88, $80, $B8, $88, $88, $70, $00
    ; 'H'
    DB   $88, $88, $88, $F8, $88, $88, $88, $00
    ; 'I'
    DB   $70, $20, $20, $20, $20, $20, $70, $00
    ; 'J'
    DB   $08, $08, $08, $08, $08, $88, $70, $00
    ; 'K'
    DB   $88, $90, $A0, $C0, $A0, $90, $88, $00
    ; 'L'
    DB   $80, $80, $80, $80, $80, $80, $F8, $00
    ; 'M'
    DB   $88, $D8, $A8, $88, $88, $88, $88, $00
    ; 'N'
    DB   $88, $C8, $A8, $98, $88, $88, $88, $00
    ; 'O'
    DB   $70, $88, $88, $88, $88, $88, $70, $00
    ; 'P'
    DB   $F0, $88, $88, $F0, $80, $80, $80, $00
    ; 'Q'
    DB   $70, $88, $88, $88, $A8, $90, $68, $00
    ; 'R'
    DB   $F0, $88, $88, $F0, $A0, $90, $88, $00
    ; 'S'
    DB   $70, $88, $80, $70, $08, $88, $70, $00
    ; 'T'
    DB   $F8, $20, $20, $20, $20, $20, $20, $00
    ; 'U'
    DB   $88, $88, $88, $88, $88, $88, $70, $00
    ; 'V'
    DB   $88, $88, $88, $88, $88, $50, $20, $00
    ; 'W'
    DB   $88, $88, $88, $A8, $A8, $D8, $88, $00
    ; 'X'
    DB   $88, $50, $20, $20, $20, $50, $88, $00
    ; 'Y'
    DB   $88, $50, $20, $20, $20, $20, $20, $00
    ; 'Z'
    DB   $F8, $08, $10, $20, $40, $80, $F8, $00
    ; '[' and ']': brackets as tall as the letters
    DB   $70, $40, $40, $40, $40, $40, $70, $00
    ; '\': the mirror of '/'
    DB   $00, $40, $20, $10, $08, $04, $00, $00
    DB   $70, $10, $10, $10, $10, $10, $70, $00
    ; '^': a caret at the top of the cell
    DB   $20, $50, $88, $00, $00, $00, $00, $00
    ; '_'
    DB   $00, $00, $00, $00, $00, $00, $F8, $00
    ; '`'  (Leap-C delta D28: no glyph, as before: the backtick prints as a space)
    DB   $00, $00, $00, $00, $00, $00, $00, $00
    ; 'a'
    DB   $00, $00, $70, $08, $78, $88, $78, $00
    ; 'b'
    DB   $80, $80, $B0, $C8, $88, $88, $F0, $00
    ; 'c'
    DB   $00, $00, $70, $88, $80, $88, $70, $00
    ; 'd'
    DB   $08, $08, $68, $98, $88, $88, $78, $00
    ; 'e'
    DB   $00, $00, $70, $88, $F8, $80, $70, $00
    ; 'f'
    DB   $30, $40, $F0, $40, $40, $40, $40, $00
    ; 'g'  Leap-C delta D24: the bowl on the x-height (rows 2-5), the descender in rows 6-7
    DB   $00, $00, $78, $88, $88, $78, $08, $70
    ; 'h'
    DB   $80, $80, $B0, $C8, $88, $88, $88, $00
    ; 'i'
    DB   $20, $00, $60, $20, $20, $20, $70, $00
    ; 'j'
    DB   $10, $00, $30, $10, $10, $10, $90, $60
    ; 'k'
    DB   $80, $80, $90, $A0, $C0, $A0, $90, $00
    ; 'l'  (Leap-C delta D13: a tail to the right, no base, unlike '1')
    DB   $60, $20, $20, $20, $20, $20, $18, $00
    ; 'm'
    DB   $00, $00, $D0, $A8, $A8, $88, $88, $00
    ; 'n'
    DB   $00, $00, $B0, $C8, $88, $88, $88, $00
    ; 'o'
    DB   $00, $00, $70, $88, $88, $88, $70, $00
    ; 'p'  Leap-C delta D24: the bowl on the x-height (rows 2-5), the descender in rows 6-7
    DB   $00, $00, $F0, $88, $88, $F0, $80, $80
    ; 'q'  Leap-C delta D24: the bowl on the x-height (rows 2-5), the descender in rows 6-7
    DB   $00, $00, $78, $88, $88, $78, $08, $08
    ; 'r'
    DB   $00, $00, $B0, $C8, $80, $80, $80, $00
    ; 's'
    DB   $00, $00, $78, $80, $70, $08, $F0, $00
    ; 't'
    DB   $40, $40, $F0, $40, $40, $48, $30, $00
    ; 'u'
    DB   $00, $00, $88, $88, $88, $98, $68, $00
    ; 'v'
    DB   $00, $00, $88, $88, $88, $50, $20, $00
    ; 'w'
    DB   $00, $00, $88, $88, $A8, $A8, $50, $00
    ; 'x'
    DB   $00, $00, $88, $50, $20, $50, $88, $00
    ; 'y'
    DB   $00, $00, $88, $88, $88, $78, $08, $70
    ; 'z'
    DB   $00, $00, $F8, $10, $20, $40, $F8, $00
    ; '{' and '}': braces with a centre point, each the other's mirror
    DB   $18, $20, $20, $40, $20, $20, $18, $00
    ; '|': a solid bar (the gap of '!' tells them apart)
    DB   $20, $20, $20, $20, $20, $20, $20, $00
    DB   $C0, $20, $20, $10, $20, $20, $C0, $00
    ; '~': a centred wave
    DB   $00, $00, $40, $A8, $10, $00, $00, $00

; ============================================================================
; Sprites — GFX_SPRITE_CAPTURE / GFX_SPRITE_DRAW (2026-08-19)
;
; A save/restore pair for a rectangular region of the screen (bitmap +
; attributes), on top of the same screen-addressing math GFX_CHAR_SETUP/
; GFX_SET_ATTR already use and have hardware-confirmed. Together these
; two also implement a generic screen-to-screen COPY (capture from one
; position, draw at another) — matching this project's own deferred
; design note ("COPY/sprite save-restore") with one reusable pair
; rather than two separate mechanisms.
;
; Deliberately CELL-ALIGNED ONLY: the rectangle's top-left and size are
; always whole 8x8 character cells (row 0-23, col 0-31), never
; arbitrary pixel positions. This is the same "coarse but correct"
; scoping precedent GFX_CPLOT's own quadrant granularity already set —
; and here it's not just simplicity, it sidesteps a real ambiguity:
; a screen attribute belongs to a whole 8x8 cell, so a pixel-unaligned
; sprite would have no single well-defined attribute to capture at its
; own edges. Smooth pixel-level sprite movement is real future work,
; not attempted here — moving a sprite means capture-background/
; restore-background/draw-again, one 8-pixel step at a time.
;
; Buffer format: one 9-byte record per cell, row-major (top-left to
; bottom-right, rows outer) — 8 bitmap scanline bytes (top to bottom)
; followed by 1 attribute byte. Total buffer size needed = width_cells
; * height_cells * 9 bytes. The caller owns this buffer (no dynamic
; allocation exists in this project) — typically one "sprite" buffer
; and one "background save" buffer per on-screen sprite, sized for
; whatever cell rectangle that sprite uses.
; ============================================================================

; ============================================================================
; GFX_CELL_BITMAP_ADDR
; Row/col -> bitmap screen address, scanline 0 of that cell. Exactly
; the same ROW_BASE_TABLE[row]+col math GFX_CHAR_SETUP already uses and
; has hardware-confirmed (see that routine) — factored out here as its
; own small routine rather than reused directly, matching this file's
; own established precedent of small parallel address-math routines
; for contexts that don't need GFX_CHAR_SETUP's other half (font
; lookup) — GFX_CPLOT's own ROW_BASE_TABLE use is the same pattern.
; In:  B = row (0-23), C = col (0-31) — NOT bounds-checked here; callers
;      in this file always validate via GFX_SPRITE_BOUNDS_CHECK first
; Out: HL = bitmap address (scanline 0 of the cell)
; Destroys: AF, DE
; ============================================================================
GFX_CELL_BITMAP_ADDR:
    ld   a, b
    call GFX_ROW_BASE_ADDR
    ex   de, hl                       ; DE = row_base
    ld   a, c
    add  a, e
    ld   e, a
    jr   nc, .no_carry
    inc  d
.no_carry:
    ex   de, hl                        ; HL = row_base + col
    ret

; ============================================================================
; GFX_CELL_ATTR_ADDR
; Row/col -> attribute byte address. Shared by GFX_ATTR_SWAP, GFX_SET_ATTR,
; and the sprite paths so the bounds and address formula have one owner.
; In:  B = row (0-23), C = col (0-31)
; Out: carry clear + HL = attribute byte address; carry set if out of range
; Destroys: AF, DE
; ============================================================================
GFX_CELL_ATTR_ADDR:
    ld   a, b
    cp   24
    jr   nc, .out_of_range
    ld   a, c
    cp   32
    jr   nc, .out_of_range
    ld   h, 0
    ld   l, b
    add  hl, hl                      ; x2
    add  hl, hl                      ; x4
    add  hl, hl                      ; x8
    add  hl, hl                      ; x16
    add  hl, hl                      ; x32 -> row*32
    ld   de, ATTR_ADDR
    add  hl, de
    ld   d, 0
    ld   e, c
    add  hl, de                       ; HL = ATTR_ADDR + row*32 + col
    ret
.out_of_range:
    scf
    ret

; ============================================================================
; GFX_SPRITE_BOUNDS_CHECK
; Shared by GFX_SPRITE_CAPTURE and GFX_SPRITE_DRAW — both need the
; identical "does this whole rectangle fit on the 32x24 cell grid"
; check before touching anything.
; In:  B = top row, C = top col, D = width cells, E = height cells
; Out: carry clear if the whole rectangle fits; carry set otherwise
;      (width or height 0, or top+size overflowing the 32x24 grid) —
;      REJECTED outright rather than clipped, unlike GFX_PLOT_CLIPPED's
;      own convention: clipping here would silently leave the caller's
;      fixed-size buffer mismatched against what actually got
;      written/read, corrupting its own internal layout rather than
;      just drawing less on screen.
; Destroys: AF
; ============================================================================
GFX_SPRITE_BOUNDS_CHECK:
    ld   a, d
    or   a
    jr   z, .fail                      ; width 0 is invalid
    ld   a, e
    or   a
    jr   z, .fail                      ; height 0 is invalid

    ld   a, b
    add  a, e
    jr   c, .fail
    cp   25
    jr   nc, .fail                     ; top_row + height > 24

    ld   a, c
    add  a, d
    jr   c, .fail
    cp   33
    jr   nc, .fail                     ; top_col + width > 32

    or   a
    ret
.fail:
    scf
    ret

; ============================================================================
; GFX_SPRITE_CELL_ROWCOL
; SPRITE_TOP_ROW/COL + SPRITE_ROW_IDX/COL_IDX -> the real screen cell
; for CAPTURE/DRAW's current loop iteration. Small enough it could be
; inlined at both call sites, but it's called twice per cell in both
; routines (once for the bitmap address, again for the attribute
; address, since the scanline-copy loop between them clobbers B/C) —
; worth the one shared definition.
; In:  none (reads SPRITE_TOP_ROW/TOP_COL/ROW_IDX/COL_IDX)
; Out: B = real row, C = real col
; Destroys: AF, HL
; ============================================================================
GFX_SPRITE_CELL_ROWCOL:
    ld   a, (SPRITE_TOP_ROW)
    ld   hl, SPRITE_ROW_IDX
    add  a, (hl)
    ld   b, a
    ld   a, (SPRITE_TOP_COL)
    ld   hl, SPRITE_COL_IDX
    add  a, (hl)
    ld   c, a
    ret

; ============================================================================
; GFX_SPRITE_SETUP (internal)
; Shared prologue for GFX_SPRITE_CAPTURE/GFX_SPRITE_DRAW — bounds-checks
; the rectangle and stages it into SPRITE_BUF_PTR/TOP_ROW/TOP_COL/W/H/
; ROW_IDX, exactly the same regardless of which direction (capture vs
; draw) the caller's own row/col loop below will go. Confirmed
; byte-identical between the two routines before factoring this out.
; In:  B = top row (0-23), C = top col (0-31), D = width cells (1-32),
;      E = height cells (1-24), HL = buffer address
; Out: carry clear on success (staged); carry set if the rectangle
;      doesn't fit (GFX_SPRITE_BOUNDS_CHECK) — SPRITE_* state untouched
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SPRITE_SETUP:
    call GFX_SPRITE_BOUNDS_CHECK
    ret  c

    ld   (SPRITE_BUF_PTR), hl
    ld   a, b
    ld   (SPRITE_TOP_ROW), a
    ld   a, c
    ld   (SPRITE_TOP_COL), a
    ld   a, d
    ld   (SPRITE_W), a
    ld   a, e
    ld   (SPRITE_H), a
    xor  a
    ld   (SPRITE_ROW_IDX), a
    ret

; ============================================================================
; GFX_SPRITE_TRANSFER (internal)
; Shared row/col loop behind GFX_SPRITE_CAPTURE/GFX_SPRITE_DRAW — same
; nested cell loop, cell-address computation, and DE-clobber protection
; (see the "REAL BUG FOUND 2026-08-19" note below) either way; only the
; copy DIRECTION differs, set by SPRITE_XFER_DIR (0 = capture: screen
; -> buffer; nonzero = draw: buffer -> screen). HL is always the screen
; address, DE always the buffer address, in both directions — this
; canonical convention (DRAW previously used the opposite: HL=buffer,
; DE=screen) is what lets the two directions share one attribute-copy
; sequence below without needing the original's two different orders
; (CAPTURE read-after-address-compute vs DRAW read-before-address-
; compute) — confirmed identical to the original per-direction
; behavior by direct A/B comparison under live ZEsarUX before this
; replaced the two separate routines.
; Caller must have already called GFX_SPRITE_SETUP.
; In:  none (reads SPRITE_TOP_ROW/COL/W/H/ROW_IDX and SPRITE_BUF_PTR,
;      staged by GFX_SPRITE_SETUP; SPRITE_XFER_DIR set by the caller)
; Out: carry clear (matches both wrappers' own "always succeeds once
;      SETUP has passed" contract)
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SPRITE_TRANSFER:
.row_loop:
    xor  a
    ld   (SPRITE_COL_IDX), a
.col_loop:
    call GFX_SPRITE_CELL_ROWCOL         ; B = real row, C = real col
    call GFX_CELL_BITMAP_ADDR           ; HL = screen bitmap addr
                                        ; (scanline 0) — B/C untouched
                                        ; by this call (see its own
                                        ; header)
    ld   de, (SPRITE_BUF_PTR)           ; DE = buffer pointer

    ld   a, (SPRITE_XFER_DIR)
    or   a
    ld   b, 8
    jr   nz, .draw_scan
.cap_scan:
    ld   a, (hl)
    ld   (de), a
    inc  de
    ld   a, h
    add  a, 1                          ; next scanline: +256 to the
                                       ; SCREEN address (same non-linear
                                       ; screen layout GFX_PUTCHAR/
                                       ; GFX_CPLOT already step through
                                       ; this same way)
    ld   h, a
    djnz .cap_scan
    jr   .scan_done
.draw_scan:
    ld   a, (de)
    ld   (hl), a
    inc  de
    ld   a, h
    add  a, 1
    ld   h, a
    djnz .draw_scan
.scan_done:
    ; DE now holds the buffer's attribute-slot address (buf_ptr+8)
    ; either way — canonical DE=buffer convention, unlike the two
    ; routines this replaced. HL (screen) is stale past this cell's
    ; last scanline and gets recomputed below regardless.
    ;
    ; REAL BUG FOUND (2026-08-19, z80sim, not caught by inspection or
    ; check_asm.py, in the original two-routine version this replaced):
    ; DE holds the buffer's attribute-slot address at this point — but
    ; GFX_CELL_ATTR_ADDR's own documented contract destroys DE (it uses
    ; DE as scratch internally, same as GFX_SET_ATTR's proven address
    ; math it mirrors). An earlier version called GFX_SPRITE_CELL_
    ; ROWCOL/GFX_CELL_ATTR_ADDR here with no protection, silently
    ; clobbering DE before the attribute copy below ever ran — exactly
    ; lesson 1's register-survival bug class. Fix (still in force here):
    ; stash DE across both calls.
    push de
    call GFX_SPRITE_CELL_ROWCOL
    call GFX_CELL_ATTR_ADDR             ; HL = screen attr addr
    pop  de                             ; DE = buffer's attribute slot,
                                        ; restored
    ld   a, (SPRITE_XFER_DIR)           ; re-read fresh — the two calls
                                        ; above destroy AF, so a value
                                        ; loaded before them wouldn't
                                        ; survive
    or   a
    jr   nz, .draw_attr
    ld   a, (hl)                        ; capture: read screen attr
    ld   (de), a                        ; write buffer
    jr   .attr_done
.draw_attr:
    ld   a, (de)                        ; draw: read buffer attr
    ld   (hl), a                        ; write screen
.attr_done:
    inc  de
    ld   (SPRITE_BUF_PTR), de           ; advance past this cell's 9
                                        ; bytes total

    ld   a, (SPRITE_COL_IDX)
    inc  a
    ld   (SPRITE_COL_IDX), a
    ld   hl, SPRITE_W
    cp   (hl)
    jr   c, .col_loop

    ld   a, (SPRITE_ROW_IDX)
    inc  a
    ld   (SPRITE_ROW_IDX), a
    ld   hl, SPRITE_H
    cp   (hl)
    jr   c, .row_loop

    or   a                              ; success
    ret

; ============================================================================
; GFX_SPRITE_CAPTURE
; Captures a rectangular region of the screen (bitmap + attributes)
; into a caller-provided buffer — the "save" half of a save/restore
; sprite pair (GFX_SPRITE_DRAW is the "restore/show" half). See this
; section's own header above for the buffer format and cell-alignment
; scoping.
; In:  B = top row (0-23), C = top col (0-31), D = width cells (1-32),
;      E = height cells (1-24), HL = buffer address
; Out: carry clear on success (buffer filled); carry set + buffer
;      untouched if the rectangle doesn't fit (GFX_SPRITE_BOUNDS_CHECK)
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SPRITE_CAPTURE:
    call GFX_SPRITE_SETUP
    ret  c
    xor  a
    ld   (SPRITE_XFER_DIR), a           ; 0 = capture
    jr   GFX_SPRITE_TRANSFER

; ============================================================================
; GFX_SPRITE_DRAW
; Draws a buffer previously filled by GFX_SPRITE_CAPTURE back onto the
; screen at a (possibly different) cell position — the "restore/show"
; half of the pair. A straight overwrite (bitmap + attribute both
; replaced outright), not an OR/XOR blend — this is the classic "save-
; under" sprite technique: showing a sprite means capturing the
; background first, then drawing the sprite buffer; hiding/moving it
; means drawing the saved background buffer back, exactly this same
; routine either way. No XOR-drawing is used anywhere, deliberately —
; on attribute-clash hardware, XOR-plotting individual sprite pixels
; can't cleanly erase against a background of different colors, while
; save-under works uniformly regardless of what's underneath.
; In:  B = top row (0-23), C = top col (0-31), D = width cells (1-32),
;      E = height cells (1-24), HL = buffer address (must have been
;      filled by a prior GFX_SPRITE_CAPTURE call with the SAME width/
;      height — this routine has no way to verify that)
; Out: carry clear on success (screen updated); carry set + screen
;      untouched if the rectangle doesn't fit (GFX_SPRITE_BOUNDS_CHECK)
; Destroys: AF, BC, DE, HL
; ============================================================================
GFX_SPRITE_DRAW:
    call GFX_SPRITE_SETUP
    ret  c
    ld   a, 1
    ld   (SPRITE_XFER_DIR), a           ; nonzero = draw
    jr   GFX_SPRITE_TRANSFER
    ENDIF
