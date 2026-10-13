// Golden: A word stored through a pointer held in HL: ex de,hl / value / rst STI.
// golden: f DF00 DD6E04DD6605 EB DD6E06DD6607 D7 E7
// expect: exit 0
void f(int *p, int v) { *p = v; }
int main(void) { return 0; }
