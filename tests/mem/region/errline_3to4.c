// A runtime error in the part of a function that continues from image region 3 into region 4
// (which lies below region 1 in memory) has no source line: RT_ERRLOC takes the newest function
// starting at most 8 KB below the failing address, and none does (spec.md 5.9: line 0, unknown;
// never a wrong line). first() starts in region 3 and calls sound() with a bad register at its end.
// expect: rterror 4
// rtline: 0
// region: first 3
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
    sound(99, 1);
}
int main(void)
{
    first();
    return g;
}
