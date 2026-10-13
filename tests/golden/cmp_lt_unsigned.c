// Golden: a < b unsigned: or a / sbc hl,de.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 B7ED52 2100003001 2C E7
// expect: exit 0
int f(unsigned a, unsigned b) { return a < b; }
int main(void) { return 0; }
