// A floating division by zero inside a loaded library's function (LX_FOP) is runtime error 6, reported at
// the line of the program's function that called the library, as for the ROM's own library (Phase 10).
// library: testlib
// expect: rterror 6
// rtline: 6
float ratio(int a, int b)
{
    return t_fdiv(a, b);
}
int main(void)
{
    puts("BEFORE");
    ratio(1, 2);
    return ratio(1, 0);
}
