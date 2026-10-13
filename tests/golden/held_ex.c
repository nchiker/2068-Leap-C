// Golden: g() + a: the left result stays in HL (ex de,hl, no push).
// golden: f DF00 CD{&g} EB DD6E04DD6605 19 E7
// expect: exit 0
int g(void) { return 4; }
int f(int a) { return g() + a; }
int main(void) { return 0; }
