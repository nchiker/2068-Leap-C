// at() sets the print position (rows beyond 23 clamp to 23, columns wrap at 32); tab() sets the
// column only.
// expect: exit 0
// screen: 3           R3C10
// screen: 4 A   B
// screen: 23 LAST   C
int main(void)
{
    cls();
    at(3, 10);
    print("R3C10");
    at(4, 0);
    print("A");
    tab(4);
    print("B");
    at(99, 0);
    print("LAST");
    tab(32 + 7);
    print("C");
    return 0;
}
