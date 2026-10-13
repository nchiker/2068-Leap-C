// Golden: A local char (IX-1): ld (ix+d),l and ld l,(ix+d) / ld h,0.
// golden: f DF01 214100 DD75FF DD6EFF2600 E7
// expect: exit 0
int f(void) { char c; c = 65; return c; }
int main(void) { return 0; }
