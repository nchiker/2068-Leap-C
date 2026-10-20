// #pragma hires: a global that only region 4 could hold is "program too big".
// expect: error E_TOOBIG 7
#pragma hires
char a[8192];
char b[4480];
char c[1024];
char d[1];
int main(void) { return 0; }
