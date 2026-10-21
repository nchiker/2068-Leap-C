// Floats as conditions and in ?:, && || ! (Phase 8): the run-time tests (F_TST) and constant ones
// folded; a float loop counter.
// expect: exit 0
// mem: c+0 0100000001000000010000000200010000000300
// screen: 0 0.0 0.5 1.0 1.5 2.0 2.5
float z = 0.0;
float h = 0.5;
int c[10];
float pick(int k, float a, float b)
{
    return k ? a : b;
}
int main(void)
{
    float f;
    cls();
    c[0] = !z;
    c[1] = !h;
    c[2] = z || h;
    c[3] = z && h;
    c[4] = h ? 1 : 0;
    c[5] = 0.0 ? 1 : 0;
    c[6] = !0.0 + (0.25 && 1);
    c[7] = pick(0, 1.5, 2.5) == 2.5;
    c[8] = 0;
    if (z)
        c[8] = 1;
    while (h > 0.0)
        h = h - 0.25;
    c[9] = (h == 0.0) + 2;
    for (f = 0.0; f < 3.0; f += 0.5)
        printf("%.1f ", f);
    return 0;
}
