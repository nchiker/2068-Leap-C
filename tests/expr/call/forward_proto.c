// Calls through a prototype before the definition, and function addresses taken before it.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int dbl(int);
int (*fp)(int) = dbl;
int main(void)
{
    int (*q)(int);
    q = dbl;
    ck(1, dbl(4), 8);
    ck(2, fp(5), 10);
    ck(3, q(6), 12);
    ck(4, q == fp, 1);
    return bad;
}
int dbl(int x) { return x + x; }
