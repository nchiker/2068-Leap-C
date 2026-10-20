// Code crosses from image region 3 into region 4 inside a loop: regions 1 and 2 are full of data,
// region 3 has about 200 bytes left.
// expect: exit 366
// region: first 3
// region: second 4
char a[8192];
char b[4480];
char c[824];
int g;
int first(void)
{
    int i;
    for (i = 0; i < 3; i++) {
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
        g = g + 1;
    }
    return g;
}
int second(void) { return g * 2 + a[8191] + b[4479] + c[823]; }
int main(void)
{
    a[8191] = 1;
    b[4479] = 2;
    c[823] = 3;
    return first() + second();
}
