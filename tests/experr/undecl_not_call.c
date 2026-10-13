// An undeclared name not followed by ( is not declared implicitly.
// expect: error E_UNDECL 6
int main(void)
{
    int (*p)(void);
    p = later; /*E*/
    return 0;
}
