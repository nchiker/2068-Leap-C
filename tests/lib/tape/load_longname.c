// tape_load() with a name of 11 characters: runtime error 4; a name of exactly 10 is accepted (the
// helper's call stops at BREAK, see load_break.c), so the error is the length, not the call.
// expect: rterror 4
// rtline: 6
char buf[8];
int main(void)
{
    tape_load("abcdefghijk", buf, 8);
    return 0;
}
