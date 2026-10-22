// The parameter lists LIB_PARAMS gained for libraries (Phase 10): five ints (the fifth from the stack), (int,
// int, void *) and (int, void *); any object pointer converts to void *.
// library: testlib
// expect: exit 0
// mem: v 0F00
// mem: s 2A
int v;
char s[2];
int main(void)
{
    if (t_five(10, 2, 3, 4, 50) != 40)
        return 1;
    t_store(10, 5, &v);
    t_poke(42, s);
    return 0;
}
