// printf's %f (spec.md 7.1, Phase 8): 6 decimals by default, %.N with N 0-9 (rounded half up), a
// width right-aligns, every integer digit is printed, a negative value has its '-'.
// expect: exit 0
// screen: 0 3.141590|3|3.14|-3|3|1
// screen: 1 10000000000.0|-0.0001
// screen: 2 123.456000000|0.000|100.00
// screen: 3 -1.5|0.000|65535.75
// screen: 4 [    3.14][  -2.500]
// screen: 5 0.333333 0.300000000 x=2.500
// screen: 6 17000000006329125039606067229954
// screen: 7 4608768
float pi = 3.14159;
int main(void)
{
    float t;
    float x;
    cls();
    printf("%f|%.0f|%.2f|%.0f|%.0f|%.0f\n", pi, pi, pi, -2.5, 2.5, 0.5);
    printf("%.1f|%.4f\n", 1e10, -0.000123);
    printf("%.9f|%.3f|%.2f\n", 123.456, 1e-5, 99.999);
    printf("%.1f|%.3f|%.2f\n", -1.5, 0.0, 65535.75);
    printf("[%8.2f][%8.3f]\n", pi, -2.5);
    t = 1.0;
    x = 0.1;
    printf("%f %.9f x=%.3f\n", t / 3, x * 3, 2.5);
    printf("%.0f", 1.7e38);
    return 0;
}
