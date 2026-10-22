// A loaded library that exports a name the ROM's library also has (testlib's abs): the ROM's table is
// searched first, so the ROM's abs() is bound and the library's is never reached (Phase 10).
// library: testlib
// expect: exit 0
int main(void)
{
    if (abs(-5) != 5 || abs(7) != 7)
        return 1;
    return t_args(0, 0, 0);
}
