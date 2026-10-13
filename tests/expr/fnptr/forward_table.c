// A static table of addresses of functions defined later (fixup chains through static data).
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int one(void);
int two(void);
int (*t[4])(void) = { one, two, two, one };
int main(void)
{
    ck(1, t[0](), 1);
    ck(2, t[1]() + t[2]() + t[3](), 5);
    return bad;
}
int one(void) { return 1; }
int two(void) { return 2; }
