// Golden: A constant: ld hl,nn.
// golden: f DF00 21D204 E7
// expect: exit 0
int f(void) { return 1234; }
int main(void) { return 0; }
