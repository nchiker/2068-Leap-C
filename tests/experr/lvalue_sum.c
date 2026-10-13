// An assignment to the value of an expression.
// expect: error E_LVALUE 6
int x;
int main(void)
{
    (x + 1) = 2; /*E*/
    return 0;
}
