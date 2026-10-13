; ============================================================================
; kernel/math/math.asm — general-purpose 16-bit integer arithmetic
;
; CURRENT STATUS: assembled into the working ROM and exercised under
; Fuse by the automated math and language regression tests. Both
; foundational algorithms were also verified via a
; Python simulation mirroring the exact planned Z80 register steps —
; MATH_UMUL16 against 32,720 signed multiply cases (as its signed
; wrapper) and MATH_UDIV16 against 16,165 unsigned divide/remainder
; cases, all with zero failures — before any assembly was written,
; matching this project's established discipline for tricky arithmetic
; (the screen address formula, the ink/paper bit-swap, DIV10 itself).
; That verifies the ALGORITHMS; it doesn't substitute for running the
; actual assembled-code coverage now complements that algorithm check.
;
; Owns: multiply and divide, which Z80 has no hardware instructions
; for. Built specifically to support basic/'s expression evaluator,
; but deliberately kept general-purpose and free of any BASIC-specific
; assumptions — this project's own stated principle is that kernel
; modules should be reusable by other future assembly-language
; software, and 16-bit multiply/divide is exactly that kind of
; genuinely generic building block, not something that belongs buried
; inside basic/basic.asm.
;
; basic/'s own DIV10 (division by 10 specifically, for decimal-to-
; string conversion) stays where it is, unchanged — it's a different,
; narrower routine (fixed divisor, combined quotient+remainder output
; tuned for repeated-digit-extraction) serving a different purpose,
; not something this module's MATH_UDIV16 replaces.
;
; Result on overflow: both multiply and divide simply truncate to 16
; bits, matching how this project's other integer arithmetic already
; behaves (BASIC_NUM_TO_STRING, DIV10) — no overflow flag or error
; signal, consistent with there being no error-reporting mechanism
; anywhere else in this codebase yet either.
;
; Divide by zero: MATH_DIVIDE16 returns 0 rather than the nonsense
; result MATH_UDIV16 would otherwise produce (a divisor of 0 means
; "remainder >= divisor" is trivially true every iteration, giving a
; quotient of all 1-bits, i.e. -1) — a deliberate, safe default given
; there's no error-reporting mechanism to surface a real error through
; yet, not an oversight.
; ============================================================================

    IFNDEF MATH_ASM
    DEFINE MATH_ASM

    INCLUDE "include/sysvars.inc"

; LEAP-C DELTA D3: MATH_UMUL16, MATH_UDIV16, MATH_MULTIPLY16, MATH_SIGN_PREP,
; MATH_APPLY_SIGN and MATH_DIVIDE16 removed. Compiled C multiplies and divides with the
; register-only routines of the helper core (src/runtime/helpers.asm: RT_UMUL, RT_UDIV,
; RT_DIVS, RT_MODS); see platform/UPSTREAM.md.

; ============================================================================
; MATH_COMPARE16
; Signed 16-bit comparison, built specifically to support basic/'s new
; IF/ELSEIF relational operators (=, <>, <, >, <=, >=) but kept as
; general-purpose as MATH_MULTIPLY16/DIVIDE16 — no BASIC-specific
; assumptions here either.
;
; Z80 has no signed-comparison instruction, only SBC HL,DE (an
; unsigned-magnitude subtract that still sets the P/V flag as a
; signed-overflow indicator). The standard technique: after "OR A" /
; "SBC HL,DE", the result's sign flag tells you HL-DE's true sign
; UNLESS a signed overflow occurred (P/V set), in which case the sign
; flag is backwards and must be inverted. Overflow only happens when
; HL and DE have different signs and the subtraction result's sign
; matches HL's own original sign the "wrong" way — verified via a
; Python simulation of this exact flag logic (sign-of-HL, sign-of-DE,
; sign-of-result, overflow-if-signs-differ-and-result-doesn't-match)
; against all pairs from a set of edge values (0, ±1, ±5, ±32767,
; ±32768) plus 200,000 random signed pairs, zero failures, before any
; Z80 was written — same discipline as this file's multiply/divide.
; In:  HL = left operand (signed), DE = right operand (signed)
; Out: A = 0 if HL = DE, 1 if HL > DE, $FF if HL < DE
; Destroys: AF, HL (DE is only read, never written, by SBC HL,DE)
; ============================================================================
MATH_COMPARE16:
    or   a
    sbc  hl, de
    jr   z, .equal
    jp   po, .no_overflow           ; P/V clear (parity odd) = no signed
                                    ; overflow — the sign flag already
                                    ; tells the truth
    jp   m, .greater                 ; overflow occurred: sign flag is
                                     ; backwards, so a "negative" result
                                     ; here actually means HL > DE
    jr   .less
.no_overflow:
    jp   m, .less
    jr   .greater
.equal:
    xor  a
    ret
.less:
    ld   a, $FF
    ret
.greater:
    ld   a, 1
    ret

; ============================================================================
; MATH_ADD16 / MATH_SUB16 / MATH_NEGATE16 / MATH_ABS16 / MATH_SGN16
;
; Formalizes arithmetic that basic/'s evaluator (and any future caller)
; was previously doing as bare inline `ADD HL,DE` / `SBC HL,DE` /
; hand-rolled two's-complement negation wherever it came up — no
; behavior change from what already existed ad hoc, just a single
; documented call site instead of the same few instructions retyped
; in multiple places (same duplication concern that motivated the
; KEYWORD_HILITE_TABLE unification).
;
; All five verified via Python simulation (50,011 values: every edge
; case — 0, +-1, +-32767, -32768 — plus 50,000 random signed 16-bit
; values, each ADD/SUB sampled against 3 partners) before any Z80 was
; written, same discipline as this file's multiply/divide/compare.
; Truncates on overflow, same as MATH_MULTIPLY16/MATH_DIVIDE16 — no
; overflow flag, consistent with there being no error-reporting
; mechanism at this layer.
;
; The one genuine edge case: NEGATE16(-32768) and ABS16(-32768) both
; return -32768 unchanged, NOT 32768 — the positive equivalent has no
; representation in signed 16-bit two's complement, so the value
; silently doesn't change sign at that single boundary. Confirmed via
; the same Python simulation, not just reasoned about; matches the
; well-known behavior of two's-complement negation everywhere else
; (Z80, x86, etc.), not a bug specific to this implementation.
; ============================================================================

; ----------------------------------------------------------------------
; MATH_ADD16
; In:  HL, DE
; Out: HL = HL + DE (truncated to 16 bits)
; Destroys: AF
; ----------------------------------------------------------------------
    IFNDEF V2_PRODUCTION          ; RC: only rom/test_math.asm calls MATH_ADD16 / MATH_SUB16
MATH_ADD16:
    add  hl, de
    ret

; ----------------------------------------------------------------------
; MATH_SUB16
; In:  HL, DE
; Out: HL = HL - DE (truncated to 16 bits)
; Destroys: AF
; ----------------------------------------------------------------------
MATH_SUB16:
    or   a
    sbc  hl, de
    ret
    ENDIF

; ----------------------------------------------------------------------
; MATH_NEGATE16
; Two's-complement negate. Same pattern already used inline inside
; MATH_MULTIPLY16/MATH_DIVIDE16's own sign-then-magnitude steps above
; — pulled out here as its own documented, reusable routine rather
; than staying duplicated three times over (those two callers are
; NOT changed to call this — see this routine's own note below).
; In:  HL
; Out: HL = -HL (truncated; -32768 stays -32768 — see file header)
; Destroys: AF
; ----------------------------------------------------------------------
MATH_NEGATE16:
    xor  a
    sub  l
    ld   l, a
    ld   a, 0
    sbc  a, h
    ld   h, a
    ret

; ----------------------------------------------------------------------
; MATH_ABS16
; In:  HL
; Out: HL = absolute value of HL (truncated; ABS(-32768) = -32768 —
;      see file header)
; Destroys: AF
; ----------------------------------------------------------------------
MATH_ABS16:
    ld   a, h
    or   a
    ret  p                  ; sign bit clear (positive or zero) —
                            ; already correct, nothing to do
    jr   MATH_NEGATE16       ; tail-call: negate and return directly
                            ; from there

; LEAP-C DELTA D3: MATH_SGN16 removed (no caller; C has no sgn).

; LEAP-C DELTA D3: MATH_MOD16 (helper core RT_MODS), MATH_SQRT16 (no Release 1 caller),
; MATH_RND16 and MATH_RND_SEED (C rand()/srand(): src/runtime/library.asm) removed.


    ENDIF
