// Golden: A global char: ld hl,(nn) / ld h,0 and ld a,l / ld (nn),a.
// golden: f DF00 2A{&c}2600 23 7D32{&c} 2A{&c}2600 E7
// expect: exit 0
char c;
int f(void) { c = c + 1; return c; }
int main(void) { return 0; }
