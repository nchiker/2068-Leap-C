// Golden: g++; as a statement: the dec hl that restores the old value is dropped.
// golden: f DF00 2A{&g} 23 22{&g} E7
// expect: exit 0
int g;
void f(void) { g++; }
int main(void) { return 0; }
