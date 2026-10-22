// A loaded library's float service, LX_FOP (the float core on F_ACC, a pinned cell), and a float result
// (Phase 10): (float) a + b and (float) a / b, used in expressions, assigned and printed.
// library: testlib
// expect: exit 0
// screen: 0 3.500 -1.000 0.333
float f;
int main(void)
{
    f = t_fdiv(7, 2);
    if (f != 3.5 || t_fadd(30000, 30000) != 60000.0 || t_fadd(-5, 2) != -3)
        return 1;
    printf("%.3f %.3f %.3f", f, t_fadd(-3, 2), t_fdiv(1, 3));
    if ((int)t_fdiv(-7, 2) != -3)
        return 2;
    return 0;
}
