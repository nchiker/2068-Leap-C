// A loaded library ends the program with a runtime error (LX_ERROR, here 4: BAD ARGUMENT), reported at the line
// of the program's function that called it (LIB_CALLER, recorded by LX_ARGS), as the ROM's library does
// (Phase 10).
// library: testlib
// expect: rterror 4
// rtline: 11
int check(int n)
{
    return n;
}
void fail(int n)
{
    check(n);
    t_error(n);
}
int main(void)
{
    fail(4);
    return 0;
}
