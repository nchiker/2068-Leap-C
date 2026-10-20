// Control flow across image regions 1 and 2 (region 1 has about 250 bytes left for code): an
// if/else whose branches are in different regions, a goto back across the boundary, a switch
// whose table and cases are in both regions, and calls through a table of function pointers
// to functions in both regions.
// expect: exit 0
// region: early 1
// region: late 2
char big[7920];
int g;
int bad;
void ck(int n, int got, int want) { if (!bad && got != want) bad = n; }
int early(int x) { return x + 1; }
int pick(int k)
{
    int r;
    r = 0;
again:
    if (k > 2) {
        r = r + 100;
    } else {
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        r = r + 1;
    }
    switch (k) {
    case 0: r = r + 10; break;
    case 1: r = r + 20; break;
    case 7: r = r + 30; break;
    default: r = r + 40;
    }
    if (r < 50) {
        k = k + 3;
        goto again;
    }
    return r;
}
int late(int x) { return x + 2; }
int (*tab[2])(int);
int main(void)
{
    tab[0] = early;
    tab[1] = late;
    ck(1, pick(0), 151);
    ck(2, pick(7), 130);
    ck(3, tab[0](1) + tab[1](1), 5);
    ck(4, g, 20);
    return bad;
}
