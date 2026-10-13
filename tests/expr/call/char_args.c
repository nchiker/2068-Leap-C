// char and signed char parameters and return values: conversions at the call and the return.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
char pc(char c) { return c; }
signed char ps(signed char c) { return c; }
char inc(char c) { return c + 1; }
int widen(signed char c, char d) { return c + d; }
int main(void)
{
    ck(1, pc(300), 44);
    ck(2, ps(255), -1);
    ck(3, inc(255), 0);
    ck(4, widen(-1, 255), 254);
    ck(5, widen(200, 200), 144);
    return bad;
}
