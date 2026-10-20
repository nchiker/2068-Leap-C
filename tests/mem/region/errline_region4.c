// A runtime error in a function wholly in image region 4 reports its line (the newest function
// starting at most 8 KB below the failing address).
// expect: rterror 4
// rtline: 54
// region: first 3
// region: second 4
char a[8192];
char b[4480];
char c[824];
int g;
void first(void)
{
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
void second(void)
{
    sound(99, 1);
}
int main(void)
{
    first();
    second();
    return g;
}
