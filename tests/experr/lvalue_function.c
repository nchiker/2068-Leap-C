// A function is not an lvalue.
// expect: error E_LVALUE 6
int g(void) { return 0; }
int main(void)
{
    g = 0; /*E*/
    return 0;
}
