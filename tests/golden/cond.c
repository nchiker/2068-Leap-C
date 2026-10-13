// Golden: a ? 5 : 7: jp z / ld hl,5 / jp / ld hl,7.
// golden: f DF00 DD6E04DD6605 7CB5 CA.... 210500 C3.... 210700 E7
// expect: exit 0
int f(int a) { return a ? 5 : 7; }
int main(void) { return 0; }
