// Timing fixture (Phase 9): the same loop with regions 1-3 full of data, so its code is in region 4
// ($6000-$77FF: memory the display contends, as the TS2068's second display file).
// region: main 4
char a[8192];
char b[4480];
char c[1024];
int main(void)
{
    unsigned i, s = 0;
    for (i = 0; i < 10000; i++)
        s += i ^ (i >> 3);
    return s;
}
