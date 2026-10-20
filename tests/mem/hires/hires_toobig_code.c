// #pragma hires: regions 1-3 are full of data, so main's code has nowhere to go (without the
// pragma it would be placed in region 4: tests/lib/gfx/mode_refused.c).
// expect: error E_TOOBIG 8
#pragma hires
char a[8192];
char b[4480];
char c[1024];
int main(void) { return 0; }
