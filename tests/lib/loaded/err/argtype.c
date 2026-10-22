// A loaded library's function is called with its signature's prototype: a pointer for an int parameter is
// TYPE MISMATCH (Phase 10).
// library: testlib
// expect: error E_TYPE 8
char buf[4];
int main(void)
{
    return t_args(buf, 2, 3);
}
