// A character without a glyph shows as a space (spec.md 7.1): its cell has no pixel set.
// expect: exit 0
int main(void)
{
    int x, y, n;
    cls();
    paper(7);
    putchar(200);
    putchar(127);
    putchar(1);
    n = 0;
    for (y = 0; y < 8; y++)
        for (x = 0; x < 24; x++)
            n += point(x, y);
    return n;
}
