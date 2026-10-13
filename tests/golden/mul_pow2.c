// Golden: a * 8: add hl,hl three times.
// golden: f DF00 DD6E04DD6605 292929 E7
// expect: exit 0
int f(int a) { return a * 8; }
int main(void) { return 0; }
