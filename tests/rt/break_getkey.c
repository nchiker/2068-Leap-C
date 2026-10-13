// BREAK while getkey() waits ends the program at the line of the function that called getkey().
// expect: rterror 5
// rtline: 9
// break: after 100000
// breakpc: IO_READ_KEY IO_READ_KEY_NONBLOCK
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
int main(void)
{
    return getkey();
}
