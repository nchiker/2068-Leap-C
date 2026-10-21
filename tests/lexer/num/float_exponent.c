// Floating constants with an exponent (Phase 8): e or E, an optional sign, digits; a point is optional.
// expect: id:x = fltx:9143500000 ; fltx:9143500000 fltx:9143500000 fltx:7027c5ac47 fltx:8734000000
// expect: fltx:0000000000 flt:1.7e38 flt:2.9e-39
x = 1e5; 1.e5 1e+5 1E-5 09e1
1e-40 1.7e38 2.9e-39
