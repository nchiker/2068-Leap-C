// cls() clears to the current colours, bright and flash included (inverse not applied).
// expect: exit 0
// attr: 0 0 0xF1
// attr: 23 31 0xF1
int main(void)
{
    ink(1);
    paper(6);
    bright(1);
    flash(1);
    inverse(1);
    cls();
    return 0;
}
