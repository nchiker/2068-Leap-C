// An assignment to a constant.
// expect: error E_LVALUE 5
int main(void)
{
    5 = 3; /*E*/
    return 0;
}
