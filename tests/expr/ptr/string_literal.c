// String literals: static char arrays; indexing, pointers into them, adjacent concatenation.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
char *s = "hello";
int main(void)
{
    char *t;
    t = "wor" "ld";
    ck(1, s[1], 'e');
    ck(2, *(s + 4), 'o');
    ck(3, "abc"[2], 'c');
    ck(4, t[4], 'd');
    ck(5, t[5], 0);
    ck(6, sizeof "abc", 4);
    ck(7, *t, 'w');
    return bad;
}
