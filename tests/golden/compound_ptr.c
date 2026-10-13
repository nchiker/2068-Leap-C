// Golden: op= through a pointer: push hl / rst LDI / ... / pop de / rst STI (the spike's p->x += dx).
// golden: f DF00 DD6E04DD6605 E5 CF EB DD6E06DD6607 19 D1 D7 E7
// expect: exit 0
void f(int *p, int v) { *p += v; }
int main(void) { return 0; }
