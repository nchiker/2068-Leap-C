// A loaded library plots through the jump table (LX_PLOT): the print attribute and over mode as plot(); points
// off the screen are left out (Phase 10).
// library: testlib
// expect: exit 0
// pixel: 10 20 1
// pixel: 11 20 0
// pixel: 255 191 1
// pixel: 0 0 0
// attr: 2 1 0x0E
int main(void)
{
    ink(6);
    paper(1);
    t_plot(10, 20);
    t_plot(255, 191);
    t_plot(256, 0);
    t_plot(-1, 0);
    t_plot(0, 192);
    over(1);
    t_plot(11, 20);
    t_plot(11, 20);
    return point(10, 20) - 1;
}
