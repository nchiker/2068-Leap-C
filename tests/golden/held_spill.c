// Golden: g() + g(): the left result is pushed when the right one needs code (push hl / pop de).
// golden: f DF00 CD{&g} E5 CD{&g} D1 19 E7
// expect: exit 0
int g(void) { return 4; }
int f(void) { return g() + g(); }
int main(void) { return 0; }
