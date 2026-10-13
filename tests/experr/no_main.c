// A program without main cannot be run (reported at the last line).
// expect: error E_NOMAIN 4
int f(void) { return 1; }
int x; /*E*/
