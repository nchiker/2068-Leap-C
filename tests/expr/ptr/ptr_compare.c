// Pointer comparisons are unsigned; equality with null; pointers to pointers.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int a[4];
int main(void)
{
    int *p;
    int *q;
    int **pp;
    char *hi;
    char *lo;
    p = &a[1];
    q = &a[3];
    ck(1, p < q, 1);
    ck(2, q > p, 1);
    ck(3, p <= p, 1);
    ck(4, q >= p, 1);
    ck(5, p == q, 0);
    ck(6, p != q, 1);
    ck(7, p == 0, 0);
    ck(8, !p, 0);
    p = 0;
    ck(9, p == 0, 1);
    ck(10, !p, 1);
    pp = &q;
    **pp = 99;
    ck(11, a[3], 99);
    *pp = &a[0];
    ck(12, q == a, 1);
    hi = (char *)0xF000;
    lo = (char *)0x7000;
    ck(13, hi > lo, 1);
    ck(14, lo < hi, 1);
    return bad;
}
