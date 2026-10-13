// * of an int.
// expect: error E_OPERAND 7
int main(void)
{
    int x;
    x = 0;
    return *x; /*E*/
}
