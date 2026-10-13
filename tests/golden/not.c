// Golden: !a: ld a,h / or l; Z.
// golden: f DF00 DD6E04DD6605 7CB5 2100002001 2C E7
// expect: exit 0
int f(int a) { return !a; }
int main(void) { return 0; }
