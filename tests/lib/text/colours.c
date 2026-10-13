// ink, paper, bright and flash set the attribute's fields (ink and paper n & 7, bright and flash
// n & 1); printing uses it; inverse(1) swaps ink and paper for printing. Default: paper 7, ink 0.
// expect: exit 0
// attr: 0 0 0x38
// attr: 1 0 0x0A
// attr: 1 1 0x51
// attr: 1 2 0xCA
// attr: 2 0 0x4A
// attr: 2 1 0x38
int main(void)
{
    cls();
    print("D");
    at(1, 0);
    ink(2);
    paper(1);
    print("A");
    inverse(1);
    bright(1);
    print("B");
    inverse(0);
    flash(1);
    print("C");
    flash(0);
    at(2, 0);
    ink(10);
    paper(9);
    print("E");
    return 0;
}
