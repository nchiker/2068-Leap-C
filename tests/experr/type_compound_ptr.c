// p += q: the result of the addition is not defined for two pointers.
// expect: error E_OPERAND 9
int main(void)
{
    int *p;
    int *q;
    p = 0;
    q = 0;
    p += q; /*E*/
    return 0;
}
