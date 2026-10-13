// & of a value.
// expect: error E_LVALUE 7
int x;
int main(void)
{
    int *p;
    p = &(x + 1); /*E*/
    return 0;
}
