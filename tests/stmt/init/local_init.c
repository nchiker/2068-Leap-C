// Automatic scalars initialised with any expression; const locals; a pointer initialiser.
// expect: exit 0
int g = 40;
int twice(int x) { return x * 2; }
int main(void)
{
    int a = 1, b = a + 1;
    const int c = twice(b) + g;
    char ch = 300;
    signed char sc = -3;
    int *p = &g;
    unsigned u = 65535u;
    if (a != 1 || b != 2) return 1;
    if (c != 44) return 2;
    if (ch != 44) return 3;
    if (sc != -3) return 4;
    if (*p != 40) return 5;
    if (u != 65535u) return 6;
    return 0;
}
