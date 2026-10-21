// An automatic scalar's initialiser may be in braces, with a trailing comma (C89 6.5.7; Phase 8).
// local: k obj int
// local: j obj int
void f(void) { int k = { 3 }, j = { k + 1, }; }
