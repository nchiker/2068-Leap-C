// Golden: Indexing a global int array: add hl,hl / ld de,a / add hl,de / rst LDI (the spike's asum template).
// golden: f DF00 DD6E04DD6605 29 11{&a}19 CF E7
// expect: exit 0
int a[10];
int f(int i) { return a[i]; }
int main(void) { return 0; }
