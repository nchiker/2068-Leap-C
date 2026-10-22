// Timing fixture (Phase 9): the same loop with region 1 full of data, so its code is in region 2
// ($E000-$F17F: not contended).
// region: main 2
char a[8192];
int main(void)
{
    unsigned i, s = 0;
    for (i = 0; i < 10000; i++)
        s += i ^ (i >> 3);
    return s;
}
