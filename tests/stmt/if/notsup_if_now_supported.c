// M1.3's tests/experr/notsup_if.c pinned `if` as "not supported" until Phase 2. The same program
// compiles and runs now.
// expect: exit 1
int main(void)
{
    if (1) /*E*/
        return 1;
    return 0;
}
