// Code crosses from image region 2 into region 3 inside a loop: region 1 is full of data, region 2
// has about 200 bytes left, first() needs about 300. The loop's backward jump goes from region 3
// to region 2, its forward exit from region 2 to region 3.
// expect: exit 366
// region: first 2
// region: second 3
char a[8192];
char b[4280];
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
int second(void) { return g * 2 + a[8191] + b[4279]; }
int main(void)
{
    a[8191] = 1;
    b[4279] = 5;
    return first() + second();
}
