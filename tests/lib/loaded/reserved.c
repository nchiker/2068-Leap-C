// A call of a reserved slot of the jump table (slot 14) ends the program with runtime error 4 at the program's
// call, so a library built for a later ABI that LIB refused cannot be reached by mistake (Phase 10).
// library: testlib
// expect: rterror 4
// rtline: 6
int main(void)
{
    t_reserved();
    return 0;
}
