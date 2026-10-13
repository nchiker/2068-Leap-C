// Adding two pointers.
// expect: error E_OPERAND 6
int a[2];
int main(void)
{
    return (int)(a + a); /*E*/
}
