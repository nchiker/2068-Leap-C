// BREAK while tape_load() searches for its header (no tape: silence) stops the transfer and the program:
// runtime error 5 at the line of the function that called tape_load(); the paging, NOBRK's section and
// the AY are as after any end.
// expect: rterror 5
// rtline: 11
// break: at TAPE_BLOCK
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
char buf[16];
int main(void)
{
    return tape_load("abcdefghij", buf, 16);
}
