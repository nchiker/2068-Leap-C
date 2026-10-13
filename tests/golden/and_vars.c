// Golden: a & b: ld a,h / and d / ld h,a / ld a,l / and e / ld l,a.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 7CA2677DA36F E7
// expect: exit 0
int f(int a, int b) { return a & b; }
int main(void) { return 0; }
