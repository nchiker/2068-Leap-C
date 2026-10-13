// Golden: a % 7: call RT_MODS.
// golden: f DF00 DD6E04DD6605 110700 EB CD{RT_MODS} E7
// expect: exit 0
int f(int a) { return a % 7; }
int main(void) { return 0; }
