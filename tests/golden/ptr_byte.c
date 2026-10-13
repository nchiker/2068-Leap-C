// Golden: A byte through a pointer: ld l,(hl) / ld h,0.
// golden: f DF00 DD6E04DD6605 6E2600 E7
// expect: exit 0
int f(char *p) { return *p; }
int main(void) { return 0; }
