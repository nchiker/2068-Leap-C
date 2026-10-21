// inverse(1) swaps ink and paper in the attribute plotting gives a cell (spec.md 7.1); the pixel is
// still set (Sinclair BASIC's INVERSE 1 PLOT clears it instead).
// expect: exit 0
// pixel: 10 10 1
// attr: 1 1 0x07
// attr: 2 2 0x38
int main(void)
{
    cls();
    inverse(1);
    plot(10, 10);
    inverse(0);
    plot(20, 20);
    return !point(10, 10);
}
