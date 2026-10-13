// A string literal made while code is emitted in the same region: data grows down from the
// region's top while the code grows up; both stay intact.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
char big[8100];
int main(void)
{
    char *s;
    char *t;
    s = "first string, made while main's code is in region 1";
    t = "second";
    ck(1, s[0], 'f');
    ck(2, t[5], 'd');
    ck(3, s[6], 's');
    return bad;
}
