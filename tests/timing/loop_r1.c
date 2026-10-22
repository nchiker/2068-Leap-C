// Timing fixture (Phase 9, tools/timingcmp.py): an integer loop, its code in image region 1 ($C000-$DFFF,
// chunk 6: memory the display does not contend).
// region: main 1
int main(void)
{
    unsigned i, s = 0;
    for (i = 0; i < 10000; i++)
        s += i ^ (i >> 3);
    return s;
}
