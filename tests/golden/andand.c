// Golden: a && b: jp z to the false value for each operand; ld hl,1 / jr / ld hl,0.
// golden: f DF00 DD6E04DD6605 7CB5 CA.... DD6E06DD6607 7CB5 CA.... 2101001803210000 E7
// expect: exit 0
int f(int a, int b) { return a && b; }
int main(void) { return 0; }
