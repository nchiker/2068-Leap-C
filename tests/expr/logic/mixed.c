// Logical operators with comparisons and pointers; ! on every type; && binds tighter than ||.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    int a;
    int b;
    char *p;
    a = 3; b = -3;
    p = 0;
    ck(1, a > 0 && b < 0, 1);
    ck(2, a < 0 || b > 0 || a == 3, 1);
    ck(3, a && b || 0 && 1, 1);
    ck(4, !p && a, 1);
    ck(5, !!a, 1);
    ck(6, !(a - 3), 1);
    ck(7, (a == 3) + (b == -3) + !p, 3);
    ck(8, a > b && b > a || a == -b, 1);
    return bad;
}
