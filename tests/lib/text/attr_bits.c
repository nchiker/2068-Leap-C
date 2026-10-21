// bright, flash, inverse and over take n & 1: 2 is 0, 3 is 1 (spec.md 7.1).
// expect: exit 0
// attr: 0 0 0x38
// attr: 0 1 0xB8
// attr: 0 2 0x07
int main(void)
{
    cls();
    bright(2);
    flash(2);
    print("A");
    flash(3);
    print("B");
    flash(0);
    inverse(3);
    print("C");
    inverse(2);
    over(3);
    over(2);
    return 0;
}
