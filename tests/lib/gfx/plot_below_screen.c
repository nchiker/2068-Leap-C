// plot and draw never write past the bottom of the screen: plot(10, 200) does nothing and
// draw(0, 180, 10, 250) stops at row 191, in both modes. A pixel row of 192-255 would address
// $5800-$5FFF (the attributes and system variables) and, in hi-res colour mode, $7800-$7FFF
// (2068-Forth's second fix in 734a966). Leap-C: GFX_PLOT_CLIPPED returns for y >= 192, draw
// clamps its ends (LIB_CLAMPY).
// expect: exit 0
#pragma hires
int sum(unsigned char *p, int n)
{
    int s = 0;
    while (n--)
        s = s + s + *p++ + (s < 0);
    return s;
}

int main(void)
{
    int a, h;
    cls();
    a = sum((unsigned char *)0x5800, 704);
    h = sum((unsigned char *)0x7800, 2048);
    plot(10, 200);
    if (sum((unsigned char *)0x5800, 704) != a)
        return 1;
    draw(0, 180, 10, 250);
    if (sum((unsigned char *)0x5800, 704) != a)
        return 2;
    if (!point(10, 191) || !point(0, 180))
        return 3;
    if (sum((unsigned char *)0x7800, 2048) != h)
        return 4;
    mode(1);
    cls();
    a = sum((unsigned char *)0x5800, 704);
    h = sum((unsigned char *)0x7800, 2048);
    plot(10, 200);
    if (sum((unsigned char *)0x7800, 2048) != h || sum((unsigned char *)0x5800, 704) != a)
        return 5;
    draw(0, 180, 10, 250);
    if (sum((unsigned char *)0x7800, 2048) != h || sum((unsigned char *)0x5800, 704) != a)
        return 6;
    if (!point(10, 191))
        return 7;
    mode(0);
    return 0;
}
