// plot() sets a pixel (x 0-255, y 0-191 from the top) and gives its cell the print attribute;
// point() reads pixels; off the screen plot() does nothing and point() returns 0.
// expect: exit 0
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 100 50 1
// pixel: 101 50 0
// attr: 6 12 0x39
int main(void)
{
    cls();
    plot(0, 0);
    plot(255, 191);
    ink(1);
    plot(100, 50);
    plot(-1, 5);
    plot(256, 5);
    plot(5, 192);
    plot(5, -1);
    if (point(0, 0) != 1 || point(255, 191) != 1 || point(100, 50) != 1) return 1;
    if (point(101, 50) != 0 || point(1, 0) != 0) return 2;
    if (point(-1, 0) != 0 || point(256, 0) != 0 || point(0, 192) != 0 || point(0, -1) != 0) return 3;
    return 0;
}
