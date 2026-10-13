// Text continues on the next row after column 31; below row 23 the screen scrolls up one row
// (here once: the text printed at row 5 moves to row 4).
// expect: exit 0
// screen: 4 01234567890123456789012345678901
// screen: 5 WRAPPED
// screen: 21 ROW 22
// screen: 22 ROW 23
// screen: 23 AFTER
int main(void)
{
    cls();
    at(5, 0);
    print("01234567890123456789012345678901WRAPPED");
    at(22, 0);
    print("ROW 22\n");
    print("ROW 23\nAFTER");
    return 0;
}
