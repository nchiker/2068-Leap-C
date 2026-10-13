// Golden: a < b signed: rst CMPLT; the value: ld hl,0 / jr nc / inc l.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 EB EF 2100003001 2C E7
// expect: exit 0
int f(int a, int b) { return a < b; }
int main(void) { return 0; }
