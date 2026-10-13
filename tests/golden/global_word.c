// Golden: A global word: ld hl,(nn) / inc hl / ld (nn),hl.
// golden: f DF00 2A{&g} 23 22{&g} 2A{&g} E7
// expect: exit 0
int g;
int f(void) { g = g + 1; return g; }
int main(void) { return 0; }
