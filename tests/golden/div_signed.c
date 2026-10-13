// Golden: a / b signed: ex de,hl / call RT_DIVS (left in DE).
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 EB CD{RT_DIVS} E7
// expect: exit 0
int f(int a, int b) { return a / b; }
int main(void) { return 0; }
