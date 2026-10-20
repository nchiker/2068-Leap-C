// Pragma names are case-sensitive.
// expect: error E_NOTSUP 4
int x;
#pragma HIRES
int main(void) { return 0; }
