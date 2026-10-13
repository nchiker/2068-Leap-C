// Golden: a + b: the right operand, ex de,hl, the left operand, add hl,de.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 19 E7
// expect: exit 0
int f(int a, int b) { return a + b; }
int main(void) { return 0; }
