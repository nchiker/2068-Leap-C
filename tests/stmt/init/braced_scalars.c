// An automatic scalar's initialiser may be in braces, with a trailing comma (C89 6.5.7; Phase 8).
// expect: exit 0
int g(void) { return 4; }
int main(void)
{
    int k = { 3 }, j = { k + g(), };
    char c = { 'A' };
    char *p = { &c };
    float f = { 2.5 };
    if (k != 3 || j != 7 || *p != 'A') return 1;
    if (f * 2 != 5) return 2;
    return 0;
}
