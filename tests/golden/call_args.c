// Golden: g(1, 2): arguments pushed right to left, popped by the caller (pop bc).
// golden: f DF00 210200E5 210100E5 CD{&g} C1C1 E7
// expect: exit -1
int g(int a, int b);
int f(void) { return g(1, 2); }
int g(int a, int b) { return a - b; }
int main(void) { return f(); }
