// print() leaves the print position after the text; puts() adds a new line and returns a
// non-negative value; putchar() returns its character; '\n' starts the next line.
// expect: exit 0
// screen: 0 ABCdef
// screen: 1 LINE 2
// screen: 2 X
// screen: 3 Y=1
int main(void)
{
    int r;
    cls();
    print("ABC");
    print("def");
    putchar('\n');
    r = puts("LINE 2");
    if (r < 0) return 1;
    if (putchar('X') != 'X') return 2;
    print("\nY=1");
    return 0;
}
