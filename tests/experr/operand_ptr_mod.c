// % of a pointer.
// expect: error E_OPERAND 7
int main(void)
{
    int *p;
    p = 0;
    return p % 2; /*E*/
}
