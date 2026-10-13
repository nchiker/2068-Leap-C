// Golden: a != b: or a / sbc hl,de; NZ.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 B7ED52 2100002801 2C E7
// expect: exit 0
int f(int a, int b) { return a != b; }
int main(void) { return 0; }
