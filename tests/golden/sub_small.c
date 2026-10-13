// Golden: a - 2: dec hl twice.
// golden: f DF00 DD6E04DD6605 2B2B E7
// expect: exit 0
int f(int a) { return a - 2; }
int main(void) { return 0; }
