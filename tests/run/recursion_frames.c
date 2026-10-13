// Each recursion level has its own locals: values survive the recursive calls below them.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int walk(int n, int acc)
{
    int mine;
    char tag;
    mine = n * 3;
    tag = n;
    acc = n ? walk(n - 1, acc + mine) : acc;
    ck(n + 1, mine, n * 3);
    ck(n + 100, tag, n);
    return acc;
}
int main(void)
{
    ck(1000, walk(20, 0), 630);
    return bad;
}
