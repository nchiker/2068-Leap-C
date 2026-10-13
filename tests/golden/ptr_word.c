// Golden: A word through a pointer: rst LDI.
// golden: f DF00 DD6E04DD6605 CF E7
// expect: exit 0
int f(int *p) { return *p; }
int main(void) { return 0; }
