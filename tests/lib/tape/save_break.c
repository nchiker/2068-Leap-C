// BREAK during tape_save() (held from its first block) stops it after the header's first byte, sends no
// data block and ends the program: runtime error 5 at the calling function's line.
// expect: rterror 5
// rtline: 10
// break: at TAPE_BLOCK
// noaudit
// maxi: 60000000
// rundepth: 1
char buf[16];
int main(void)
{
    tape_save("abc", buf, 16);
    return 0;
}
