// A loaded library's function and the ROM services it calls stay within the stack the runtime allows
// between two frame checks (spec.md 3.2): the deepest byte of a print, a float operation and a plot from the
// library (Phase 10).
// library: testlib
// stacklow: $FEA0
// expect: exit 0
int main(void)
{
    t_puts("STACK");
    t_fdiv(1, 3);
    t_plot(5, 5);
    return 0;
}
