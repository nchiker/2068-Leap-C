// An assignment to a function result.
// expect: error E_LVALUE 6
int f(void) { return 1; }
int main(void)
{
    f() = 1; /*E*/
    return 0;
}
