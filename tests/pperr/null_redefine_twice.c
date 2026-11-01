// 1.0: replacing the predefined NULL is allowed once; a program's own NULL defined again is ALREADY DEFINED.
// expect: error E_REDEF 4
#define NULL 0
#define NULL 0
int main(void) { return 0; }
