// if and if/else on every kind of condition: comparison, value, pointer, constant.
// expect: exit 0
int g;
int f(int x) { if (x > 0) return 1; else if (x < 0) return -1; else return 0; }
int main(void)
{
    int *p;
    p = 0;
    if (f(5) != 1) return 1;
    if (f(-5) != -1) return 2;
    if (f(0) != 0) return 3;
    if (p) return 4;
    p = &g;
    if (!p) return 5;
    if (0) return 6;
    if (1) g = 7; else return 8;
    if (g != 7) return 9;
    if (g == 7) { g = 1; } else { g = 2; }
    return g - 1;
}
