// Golden: A signed char is sign-extended: ld a,l / rla / sbc a,a / ld h,a.
// golden: f DF00 2A{&s}7D179F67 E7
// expect: exit 0
signed char s;
int f(void) { return s; }
int main(void) { return 0; }
