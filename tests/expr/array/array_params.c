// Array parameters are pointers; 2-D array parameters; writes through them reach the caller.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int g[2][3];
void fill(int (*p)[3], int v) { p[1][2] = v; p[0][0] = v + 1; }
int get(int t[], int i) { return t[i]; }
int main(void)
{
    int l[5];
    fill(g, 7);
    ck(1, g[1][2], 7);
    ck(2, g[0][0], 8);
    l[4] = 44;
    ck(3, get(l, 4), 44);
    ck(4, get(g[1], 2), 7);
    return bad;
}
