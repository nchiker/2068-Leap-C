// Golden: a == 0: ld a,h / or l.
// golden: f DF00 DD6E04DD6605 7CB5 2100002001 2C E7
// expect: exit 0
int f(int a) { return a == 0; }
int main(void) { return 0; }
