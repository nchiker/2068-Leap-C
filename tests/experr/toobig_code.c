// Every image region is full of static data: no room for code (E_TOOBIG at the first function).
// expect: error E_TOOBIG 7
char a[8192];
char b[4480];
char c[1024];
char d[6144];
int main(void) { return 0; }
