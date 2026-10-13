// An undeclared variable.
// expect: error E_UNDECL 6
int main(void)
{
    int x;
    x = y; /*E*/
    return 0;
}
