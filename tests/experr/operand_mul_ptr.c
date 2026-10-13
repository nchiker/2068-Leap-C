// Multiplication of a pointer.
// expect: error E_OPERAND 9
int main(void)
{
    int x;
    int *p;
    p = 0;
    x = 1;
    return x * p; /*E*/
}
