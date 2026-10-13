// && and || evaluate the right operand only when needed; results are 0 or 1.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
int t(int v) { n++; return v; }
int main(void)
{
    n = 0;
    ck(1, t(0) && t(1), 0);
    ck(2, n, 1);
    ck(3, t(1) || t(0), 1);
    ck(4, n, 2);
    ck(5, t(2) && t(3), 1);
    ck(6, n, 4);
    ck(7, t(0) || t(0), 0);
    ck(8, n, 6);
    ck(9, 0 && t(1), 0);
    ck(10, 1 || t(1), 1);
    ck(11, n, 6);
    ck(12, t(5) && 0, 0);
    ck(13, 1 && t(7), 1);
    ck(14, n, 8);
    return bad;
}
