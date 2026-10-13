// sizeof does not evaluate its operand: no call, no assignment, no increment happens.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
int f(void) { n = 99; return 1; }
int main(void)
{
    int x;
    x = 1;
    ck(1, sizeof(f()), 2);
    ck(2, sizeof(x = 5), 2);
    ck(3, sizeof x++, 2);
    ck(4, n, 0);
    ck(5, x, 1);
    ck(6, sizeof(char) + sizeof(&f), 3);
    return bad;
}
