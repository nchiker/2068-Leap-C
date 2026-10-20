// The pragma's name is not macro-expanded (directive tokens never are): `hires` defined as a macro
// does not change `#pragma hires`.
// expect: exit 1
#define hires 1
#pragma hires
int main(void) { mode(1); return hires; }
