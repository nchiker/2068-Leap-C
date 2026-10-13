// local: k obj int flags=static,defined val=0xDFFE
// local: m obj [2][2]char flags=static,defined val=0xDFFA
void f(void) { static int k = 5 * 5; static char m[2][2] = { 1, 2, 3 }; }
