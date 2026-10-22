// Codes 128-143 are the block graphics: bit 0 sets the cell's top-right quarter, bit 1 the top-left,
// bit 2 the bottom-right, bit 3 the bottom-left (Phase 9: ROM coverage found them untested).
// expect: exit 512
int main(void)
{
    int c, x, y, n = 0;
    cls();
    for (c = 128; c < 144; c++)
        putchar(c);
    for (y = 0; y < 8; y++)
        for (x = 0; x < 128; x++)
            n += point(x, y);
    if (!point(12, 0) || point(8, 0) || point(12, 4))
        return -1;
    if (!point(16, 0) || point(20, 0) || point(16, 4))
        return -2;
    if (!point(120, 7) || !point(127, 0))
        return -3;
    return n;
}
