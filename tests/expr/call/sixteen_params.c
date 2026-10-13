// The 16-parameter limit: arguments at IX+4 .. IX+34 are all reachable inline.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int f(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j, int k, int l, int m, int n, int o, int p)
{ return a + 2 * p + o - n + m - l + k - j + i - h + g - f + e - d + c - b; }
int main(void)
{
    ck(1, f(100, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), 137);
    return bad;
}
