// An automatic array with an initialiser: not supported (spec.md 4.7). Automatic scalars may have
// any initialiser since Phase 2 (tests/stmt/init).
// expect: error E_NOTSUP 5
void f(void) {
  int a[2] = { 1, 2 };
}
