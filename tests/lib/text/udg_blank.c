// Codes 144-164 (the UDGs) show as spaces until a program defines them: the cold start clears the
// UDG table (Phase 9: a real machine powers on with its RAM's contents; tools/poweron.py boots from
// such RAM and runs this case from it).
// expect: exit 0
int main(void)
{
    int c, x, y, n;
    cls();
    for (c = 144; c <= 164; c++)
        putchar(c);
    n = 0;
    for (y = 0; y < 8; y++)
        for (x = 0; x < 21 * 8; x++)
            n += point(x, y);
    return n;
}
