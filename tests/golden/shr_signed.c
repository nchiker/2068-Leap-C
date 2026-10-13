// Golden: a >> 3 signed: call RT_SAR.
// golden: f DF00 DD6E04DD6605 110300 EB CD{RT_SAR} E7
// expect: exit 0
int f(int a) { return a >> 3; }
int main(void) { return 0; }
