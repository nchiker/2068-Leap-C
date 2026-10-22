// A loaded library's function with three int arguments (Phase 10): the parameter list (int, int, int) that
// LIB_PARAMS gained for libraries, the arguments through the jump table's LX_ARGS, LX_MUL in the library.
// library: testlib
// expect: exit 0
int main(void)
{
    int k = 4;
    if (t_args(1, 2, 3) != 123)
        return 1;
    if (t_args(-1, 0, 7) != -93)
        return 2;
    if (t_args(k, k + 1, k * 2) != 458)
        return 3;
    return t_args(0, 0, 0);
}
