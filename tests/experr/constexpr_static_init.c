// A static initialiser that is not constant.
// expect: error E_CONSTEXPR 4
int h(void) { return 1; }
int g = h(); /*E*/
int main(void) { return g; }
