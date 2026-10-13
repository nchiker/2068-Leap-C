// Golden: A call through a pointer: call RT_CALLHL.
// golden: f DF00 210300E5 DD6E04DD6605 CD{RT_CALLHL} C1 E7
// expect: exit 0
int f(int (*p)(int)) { return p(3); }
int main(void) { return 0; }
