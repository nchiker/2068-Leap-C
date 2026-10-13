// BREAK during beep() (the EXROM trampoline: NOBRK) waits for the trampoline's end: the beep ends
// early, the EXROM is paged out, the AY is silent, then the program ends with runtime error 5 at
// the line of the function that called beep().
// expect: rterror 5
// rtline: 11
// rundepth: 1
// break: at AY_WAIT_FRAMES
// breakdeferred
// noaudit
// ay: 8=0 9=0 10=0
void tune(void)
{
    beep(3000, 5);
    beep(3000, 7);
}
int main(void)
{
    tune();
    return 0;
}
