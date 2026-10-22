// A loaded library prints through the jump table: LX_PUTC (a character, '\n' a new line) and LX_PUTS (a
// string), at the print position and in the print attribute, as putchar() and print() do (Phase 10).
// library: testlib
// expect: exit 65
// screen: 0 AB
// screen: 1 LIBRARY TEXT
// screen: 2   X
// attr: 2 2 0x0A
int main(void)
{
    int c;
    c = t_putc('A');
    t_putc('B');
    t_putc('\n');
    t_puts("LIBRARY TEXT\n");
    at(2, 2);
    paper(1);
    ink(2);
    t_putc('X');
    return c;
}
