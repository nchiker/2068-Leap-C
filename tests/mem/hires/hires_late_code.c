// After a late #pragma hires no new global goes to region 4: e (200 bytes, larger than what is
// left in regions 1-3) is "program too big" although region 4 still has room.
// expect: error E_TOOBIG 9
char a[8100];
char b[4480];
char c[1024];
char d[200];
#pragma hires
char e[200];
int main(void) { return 0; }
