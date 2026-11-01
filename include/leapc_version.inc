; include/leapc_version.inc -- the ROM's version, shown on the status row at power-on (1.0; Leap V2.1's VER).
; Edit at each release; not generated from git, so that a build stays reproducible (make repro).
; At most 28 characters (the status row's text, left of the swatch).
SH_VERSION:     DB "2068 LEAP-C 1.0", 0
