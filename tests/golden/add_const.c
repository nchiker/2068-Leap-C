// Golden: a + 1000: ld bc,nn / add hl,bc.
// golden: f DF00 DD6E04DD6605 01E80309 E7
// expect: exit 0
int f(int a) { return a + 1000; }
int main(void) { return 0; }
