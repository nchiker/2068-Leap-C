// A loaded library's function is called with its signature's prototype: the wrong number of arguments is
// WRONG ARGUMENT COUNT (Phase 10).
// library: testlib
// expect: error E_ARGS 7
int main(void)
{
    return t_args(1, 2);
}
