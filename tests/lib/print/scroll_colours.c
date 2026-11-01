// 1.0: output that scrolls paints the new bottom row in the print colours (paper 1, ink 7: $0F), not the
// platform's default white paper: rows 22 and 23 after 30 lines, at their last column (never printed on).
// expect: exit 3
int main(void)
{
    int i;
    unsigned char *a;
    int r;
    paper(1);
    ink(7);
    cls();
    for (i = 0; i < 30; i++)
        printf("%d\n", i);
    r = 0;
    a = (unsigned char *)(0x5800 + 23 * 32 + 31);
    if (*a == 0x0F) r = r + 1;
    a = (unsigned char *)(0x5800 + 22 * 32 + 31);
    if (*a == 0x0F) r = r + 2;
    return r;
}
