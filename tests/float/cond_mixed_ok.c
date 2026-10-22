// ?: with a float and an integer operand: the usual arithmetic conversions make both float (C89 6.3.15),
// in either order, at run time and with a constant condition (fix: was TYPE MISMATCH).
// expect: exit 0
// screen: 0 1.0 0.5 3.0
int k;
unsigned u = 40000u;
int main(void)
{
    float a, b, c, d, e;
    k = 0;
    a = k ? 1.5 : 2;
    b = k ? 2 : 1.5;
    k = 1;
    c = k ? 1.5 : 2;
    d = k ? 2 : 1.5;
    e = 1 ? 3 : 0.5;
    if (a != 2 || b != 1.5 || c != 1.5 || d != 2 || e != 3)
        return 1;
    if ((0 ? 0.5 : -7) != -7)
        return 2;
    if ((k ? u : 0.5) != 40000.0)
        return 3;
    printf("%.1f %.1f %.1f", k ? 1 : 0.5, !k ? 1 : 0.5, 0 ? 0.25 : 3);
    return 0;
}
