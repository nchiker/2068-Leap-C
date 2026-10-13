// The comma operator: left operands evaluated for their effects, value and type of the last.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
int main(void)
{
    int a;
    char c;
    a = (n = 3, n + 1);
    ck(1, a, 4);
    ck(2, (a++, a++, a), 6);
    ck(3, sizeof(c, a), 2);
    ck(4, (c = 1, c = 2, c), 2);
    return bad;
}
