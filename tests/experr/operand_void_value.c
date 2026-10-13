// The value of a void function used.
// expect: error E_OPERAND 6
void f(void) { }
int main(void)
{
    return f() + 1; /*E*/
}
