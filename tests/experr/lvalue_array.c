// Arrays are not modifiable lvalues.
// expect: error E_LVALUE 7
int a[3];
int b[3];
int main(void)
{
    a = b; /*E*/
    return 0;
}
