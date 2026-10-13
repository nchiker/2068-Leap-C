// Golden: a << n: call RT_SHL.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 EB CD{RT_SHL} E7
// expect: exit 0
int f(int a, int n) { return a << n; }
int main(void) { return 0; }
