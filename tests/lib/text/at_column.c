// at(row, col): the column is taken & 31 (33 is 1); puts returns 10 (spec.md 7.1).
// expect: exit 0
// screen: 2  X
// screen: 3 Y
int main(void)
{
    int r;
    cls();
    at(2, 33);
    putchar('X');
    at(3, 0);
    r = puts("Y");
    return r != 10;
}
