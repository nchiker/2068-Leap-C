// draw() joins two points with a line (both ends included), in any direction; coordinates off
// the screen are moved to its edge.
// expect: exit 0
// pixel: 10 10 1
// pixel: 20 10 1
// pixel: 15 10 1
// pixel: 30 5 1
// pixel: 30 25 1
// pixel: 40 40 1
// pixel: 50 50 1
// pixel: 45 45 1
// pixel: 255 100 1
// pixel: 0 191 1
int main(void)
{
    int x;
    cls();
    draw(10, 10, 20, 10);
    draw(30, 25, 30, 5);
    draw(50, 50, 40, 40);
    draw(300, 100, 250, 100);
    draw(-20, 500, 0, 191);
    for (x = 10; x <= 20; x++)
        if (!point(x, 10)) return 1;
    if (point(9, 10) || point(21, 10)) return 2;
    if (!point(30, 15) || !point(45, 45)) return 3;
    for (x = 250; x <= 255; x++)
        if (!point(x, 100)) return 4;
    return 0;
}
