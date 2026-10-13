// attr(row, col) returns a cell's attribute byte; 0 outside the screen.
// expect: exit 0
int main(void)
{
    cls();
    if (attr(0, 0) != 0x38) return 1;
    paper(4);
    ink(1);
    bright(1);
    at(3, 7);
    print("X");
    if (attr(3, 7) != 0x61) return 2;
    if (attr(23, 31) != 0x38) return 3;
    if (attr(24, 0) != 0 || attr(0, 32) != 0 || attr(-1, 0) != 0 || attr(0, 300) != 0) return 4;
    return 0;
}
