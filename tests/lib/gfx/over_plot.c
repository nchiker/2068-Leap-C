// over(1) plots by XOR: a pixel plotted twice is clear again; a line drawn twice disappears.
// expect: exit 0
// pixel: 7 7 0
// pixel: 60 70 0
int main(void)
{
    cls();
    over(1);
    plot(7, 7);
    if (!point(7, 7)) return 1;
    plot(7, 7);
    if (point(7, 7)) return 2;
    draw(50, 70, 70, 70);
    if (!point(60, 70)) return 3;
    draw(50, 70, 70, 70);
    if (point(60, 70)) return 4;
    return 0;
}
