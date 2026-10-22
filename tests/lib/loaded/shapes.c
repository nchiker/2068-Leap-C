// The example library (libs/shapes.asm, Phase 10): circle() with its points in all eight octants, each once (so
// over(1) draws it once, and twice to nothing), box() with its edges, isqrt().
// library: shapes
// expect: exit 0
// pixel: 140 100 1
// pixel: 100 60 1
// pixel: 60 100 1
// pixel: 100 140 1
// pixel: 128 128 1
// pixel: 100 100 0
// pixel: 10 10 1
// pixel: 20 15 1
// pixel: 15 10 1
// pixel: 15 12 0
// pixel: 250 2 0
// pixel: 253 5 0
// pixel: 210 100 1
// pixel: 200 90 1
// pixel: 190 100 1
// pixel: 200 110 1
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 128 0 1
int main(void)
{
    if (isqrt(0) != 0 || isqrt(15) != 3 || isqrt(16) != 4 || isqrt(65535u) != 255 || isqrt(10000) != 100)
        return 1;
    circle(100, 100, 40);
    circle(250, 5, 3);
    over(1);
    circle(250, 5, 3);
    circle(200, 100, 10);
    over(0);
    box(20, 15, 10, 10);
    box(-5, -5, 300, 200);
    plot(128, 128);
    return 0;
}
