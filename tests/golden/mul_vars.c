// Golden: a * b: call RT_MUL.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 CD{RT_MUL} E7
// expect: exit 0
int f(int a, int b) { return a * b; }
int main(void) { return 0; }
