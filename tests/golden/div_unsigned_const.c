// Golden: a / 10 unsigned: ld de,10 / ex de,hl / call RT_DIVU.
// golden: f DF00 DD6E04DD6605 110A00 EB CD{RT_DIVU} E7
// expect: exit 0
unsigned f(unsigned a) { return a / 10; }
int main(void) { return 0; }
