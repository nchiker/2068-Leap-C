// A floating constant ends at the first character that cannot continue it.
// expect: fltx:8140000000 + fltx:8100000000 - id:a fltx:8140000000 ) num:1 . id:x
1.5+1.-a 1.5)1 .x
