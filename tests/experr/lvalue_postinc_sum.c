// ++ of the value of an expression.
// expect: error E_LVALUE 7
int x;
int y;
int main(void)
{
    (x + y)++; /*E*/
    return 0;
}
