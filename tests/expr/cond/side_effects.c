// Only the selected operand of ?: is evaluated; nested conditionals; pointer results.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
int hit(int v) { n++; return v; }
int a;
int b;
int main(void)
{
    int x;
    n = 0;
    x = 1;
    ck(1, x ? hit(10) : hit(20), 10);
    ck(2, n, 1);
    ck(3, !x ? hit(10) : hit(20), 20);
    ck(4, n, 2);
    ck(5, x > 0 ? x > 1 ? 1 : 2 : 3, 2);
    *(x ? &a : &b) = 5;
    ck(6, a, 5);
    ck(7, b, 0);
    ck(8, (x ? 0 : 1) ? 7 : 8, 8);
    return bad;
}
