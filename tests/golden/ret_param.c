// Golden: ENTER 0, load a parameter (IX+4), LEAVE.
// golden: f DF00 DD6E04 DD6605 E7
// expect: exit 0
int f(int a) { return a; }
int main(void) { return 0; }
