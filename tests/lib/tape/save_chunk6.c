// tape_save() of a global in image region 1 (chunk 6, where the EXROM is mapped while the header logic
// runs): the program continues after the transfer (header and data block, about 7 s of tape) with its
// data, the paging and NOBRK as before; tools/tapetest.py checks the signal itself.
// expect: exit 9
// maxi: 60000000
// cell: NOBRK 0
// cell: BANK_EXROM_DEPTH 0
// region: data 1
char data[10] = "CHUNK SIX";
int main(void)
{
    tape_save("chunk6", data, 9);
    return data[8] - 'X' + 9;
}
