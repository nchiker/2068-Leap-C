// Statements other than blocks, expressions and return arrive in Phase 2.
// expect: error E_NOTSUP 5
int main(void)
{
    if (1) /*E*/
        return 1;
    return 0;
}
