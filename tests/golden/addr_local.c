// Golden: The address of a local: push ix / pop hl / ld bc,d / add hl,bc.
// golden: f DF02 DDE5E101FEFF09 E7
// expect: exit 0
int *f(void) { int x; return &x; }
int main(void) { return 0; }
