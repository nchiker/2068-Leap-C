// An automatic struct with an initialiser is not supported (spec.md 4.7).
// expect: error E_NOTSUP 3
void f(void) { struct { int a; } s = { 1 }; }
