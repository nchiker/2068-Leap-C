// plot and draw give the cells they touch the print attribute: ink, paper, bright and flash.
// expect: exit 0
// attr: 0 0 0x7A
// attr: 0 1 0x7A
// attr: 1 0 0x38
// attr: 5 5 0x8C
int main(void)
{
    cls();
    ink(2);
    paper(7);
    bright(1);
    draw(0, 0, 15, 0);
    ink(4);
    paper(1);
    bright(0);
    flash(1);
    plot(44, 44);
    return 0;
}
