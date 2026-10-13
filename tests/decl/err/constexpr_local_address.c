// expect: error E_CONSTEXPR 3
void f(void) {
  int y; static int *p = &y;
}
