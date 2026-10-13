// A constant condition selects one operand at compile time; the other is not evaluated (no call).
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
int hit(void) { n++; return 9; }
int main(void)
{
    n = 0;
    ck(1, 1 ? 4 : hit(), 4);
    ck(2, 0 ? hit() : 6, 6);
    ck(3, n, 0);
    ck(4, sizeof(1 ? (char)0 : 0), 2);
    return bad;
}
