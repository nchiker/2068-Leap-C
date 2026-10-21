// Integers and floats mixed (Phase 8): compound assignments both ways, unsigned and char extremes, through
// pointers, members, arrays, unprototyped calls, static locals, comparisons, casts, sizeof, the range.
// expect: exit 0
struct s { char c; float f; unsigned u; } st = { 1, 2.5, 3 };
float g(float a, int b) { return a * b; }
float h();
int noproto();
float arr[3] = { 0.5, 1, 1.5 };
unsigned char uc;
float fstat(void) { static float acc = 0.25; acc *= 2; return acc; }
int main(void)
{
    float f = 3.75, *p = &f;
    unsigned u = 65535;
    int i = -3, k;
    char c = 200;
    signed char sc = -100;
    f += i;                       /* 0.75 */
    if (f != 0.75) return 1;
    i += 1.9;                     /* -3 + 1.9 = -1.1 -> -1 */
    if (i != -1) return 2;
    f = u;                        /* 65535.0, not -1 */
    if (f != 65535) return 3;
    u = 40000.9;
    if (u != 40000) return 4;
    f = c;                        /* 200 */
    if (f != 200) return 5;
    f = sc;
    if (f != -100) return 6;
    uc = 300.7;                   /* 300 & 255 = 44 */
    if (uc != 44) return 7;
    *p *= 2;                      /* -200 */
    if (f != -200) return 8;
    st.f += st.c + st.u;          /* 6.5 */
    if (st.f != 6.5) return 9;
    arr[1] -= 0.25;
    if (arr[1] != 0.75 || arr[0] + arr[2] != 2) return 10;
    if (g(1.5, 4) != 6) return 11;
    if (h(2.0) != 4) return 12;
    if (noproto(7) != 8) return 13;
    if (fstat() != 0.5 || fstat() != 1) return 14;
    k = 0.5 + 0.5;
    if (k != 1) return 15;
    if (!(1 < 1.5) || 2 > 2.5 || -1 >= -0.5) return 16;
    if (!(u > 1.0)) return 17;
    f = -0.0;
    if (f != 0 || !(!f)) return 18;
    f = 1e30;
    if (f * 1e-30 < 0.999999 || f * 1e-30 > 1.000001) return 19;
    f = 1;
    for (k = 0; k < 126; k++) f = f * 2;
    if (f < 8.5e37) return 20;
    i = (int)-2.5;
    if (i != -2) return 21;
    i = (unsigned char)258.5;
    if (i != 2) return 22;
    if (sizeof(f + 1) != 5 || sizeof 1.0 != 5) return 23;
    f = 7;
    f /= 2;
    if (f != 3.5) return 24;
    i = 7;
    i *= 0.5;
    if (i != 3) return 25;
    return 0;
}
float h(float x) { return x * x; }
int noproto(int n) { return n + 1; }
