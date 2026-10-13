// The address of a function never defined, in a static initialiser.
// expect: error E_UNDEFFN 4
int g(void);
int (*fp)(void) = g; /*E*/
int main(void) { return 0; }
