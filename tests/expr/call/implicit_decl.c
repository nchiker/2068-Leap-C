// A call to an undeclared function declares it implicitly (int f()), resolved when it is defined.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    ck(1, later(2, 3), 23);
    ck(2, later(4, 5) + later(1, 1), 56);
    return bad;
}
int later(int a, int b) { return a * 10 + b; }
