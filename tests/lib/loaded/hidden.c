// A program's own declaration of a name hides a loaded library's function of that name, as it hides the
// ROM's (Phase 10): the binding is only for names no declaration names.
// library: testlib
// expect: exit 0
int t_count(void)
{
    return 99;
}
int main(void)
{
    if (t_count() != 99 || t_count() != 99)
        return 1;
    return 0;
}
