// Character constants and arithmetic on characters (unsigned char semantics).
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    char c;
    c = 'A';
    ck(1, c + 1, 'B');
    ck(2, c - 'A' + 'a', 'a');
    ck(3, '\n', 10);
    ck(4, '\377', 255);
    c = '\377';
    ck(5, c > 0, 1);
    ck(6, c + 1, 256);
    return bad;
}
