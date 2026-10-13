// A cast is not an lvalue.
// expect: error E_LVALUE 6
int x;
int main(void)
{
    (char)x += 1; /*E*/
    return 0;
}
