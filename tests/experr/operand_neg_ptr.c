// Unary minus of a pointer.
// expect: error E_OPERAND 7
int main(void)
{
    char *p;
    p = 0;
    return (int)-p; /*E*/
}
