// cls() paints every cell with the current colours (not inverted: inverse() is for printing) and
// moves the print position to (0, 0).
// expect: exit 0
// attr: 5 5 0x33
// attr: 23 31 0x33
// attr: 0 0 0x1E
// screen: 0 H
int main(void)
{
    at(10, 10);
    ink(3);
    paper(6);
    inverse(1);
    cls();
    print("H");
    return 0;
}
