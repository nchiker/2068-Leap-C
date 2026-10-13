// In `x = 1 = 2` the second assignment has a constant left operand.
// expect: error E_LVALUE 6
int x;
int main(void)
{
    x = 1 = 2; /*E*/
    return 0;
}
