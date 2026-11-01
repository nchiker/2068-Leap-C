// mode(1): plot colours the 8 pixels' own colour byte, at the same offset in $6000-$77FF as their bitmap byte
// in $4000-$57FF (platform delta D22). Rows 1 and 8 swap places under V2's row-by-row formula.
// expect: exit 3
#pragma hires
int main(void)
{
    unsigned char *row1;
    unsigned char *row8;
    int r;
    row1 = (unsigned char *)0x6103;
    row8 = (unsigned char *)0x6023;
    mode(1);
    ink(2);
    plot(24, 1);
    ink(4);
    plot(24, 8);
    r = 0;
    if (*row1 == 0x3A) r = r + 1;
    if (*row8 == 0x3C) r = r + 2;
    mode(0);
    return r;
}
