// Floating constants with a decimal point (Phase 8; spec.md 4.9). Their values: the float core's
// conversion (tools/fpmodel.py), here pinned to the exact Sinclair 5-byte forms.
// expect: id:x = fltx:8140000000 ; fltx:8100000000 fltx:8100000000 fltx:0000000000 fltx:8370000000
// expect: fltx:8408000000 fltx:9171206000 flt:3.14159 flt:0.1 fltx:8100000000
x = 1.5; 1. 1.0 0.0 07.5
08.5 123456.75 3.14159 0.1 1.000000000000000000001
