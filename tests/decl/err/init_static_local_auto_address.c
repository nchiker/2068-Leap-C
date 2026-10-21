// expect: error E_CONSTEXPR 2
void f(void) { static int k; static int *p = &k; int j; static int *q = &j; }
