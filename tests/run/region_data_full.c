// Image region 1 is full of static data before the first function: the code starts in region 2
// (spec.md 3.2: regions in order, code up from the low end).
// expect: exit 7
// region: big 1
// region: main 2
char big[8192];
int seven(void) { return 7; }
int main(void) { big[8191] = 1; return seven() + big[0]; }
