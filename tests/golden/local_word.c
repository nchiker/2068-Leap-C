// Golden: A local word (IX-2): store and load inline.
// golden: f DF02 210500 DD75FE DD74FF DD6EFE DD66FF E7
// expect: exit 0
int f(void) { int x; x = 5; return x; }
int main(void) { return 0; }
