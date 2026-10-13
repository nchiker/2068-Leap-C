// Golden: -a: call MATH_NEGATE16 (the kept ROM routine).
// golden: f DF00 DD6E04DD6605 CD{MATH_NEGATE16} E7
// expect: exit 0
int f(int a) { return -a; }
int main(void) { return 0; }
