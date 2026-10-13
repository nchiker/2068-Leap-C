// void functions called as statements and in comma expressions; side effects through globals.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int n;
void bump(int by) { n += by; }
void reset(void) { n = 0; }
int main(void)
{
    reset();
    bump(3);
    bump(4);
    ck(1, n, 7);
    ck(2, (bump(1), n), 8);
    reset();
    ck(3, n, 0);
    return bad;
}
