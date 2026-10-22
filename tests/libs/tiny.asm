; ============================================================================
; tests/libs/tiny.asm -- a second test library (Phase 10): LIB replaces one library with another, and the
; functions of the one before are gone
; ============================================================================
    INCLUDE "leapc_lib.inc"
    ORG  LX_BASE
    LX_HEADER 1
    LX_EXPORT "tiny", tiny, LXR_INT, LXP_NONE   ; 7
    LX_EXPORTS_END

tiny:
    ld   hl, 7
    ret
