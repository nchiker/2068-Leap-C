// Golden: a >> n unsigned: call RT_SHR.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 EB CD{RT_SHR} E7
// expect: exit 0
unsigned f(unsigned a, unsigned n) { return a >> n; }
int main(void) { return 0; }
