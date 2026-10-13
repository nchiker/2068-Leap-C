// `else` belongs to the nearest `if` (C89 6.6.4.1).
// expect: exit 12
int t(int a, int b)
{
    int r;
    r = 0;
    if (a)
        if (b) r = 1;
        else r = 2;
    return r;
}
int main(void) { return t(1, 1) * 10 + t(1, 0) + t(0, 1) + t(0, 0); }
