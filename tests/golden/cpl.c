// Golden: ~a: call RT_CPL.
// golden: f DF00 DD6E04DD6605 CD{RT_CPL} E7
// expect: exit 0
int f(int a) { return ~a; }
int main(void) { return 0; }
