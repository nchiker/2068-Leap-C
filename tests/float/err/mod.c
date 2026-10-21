// % takes integers only (C89 6.3.5): a float operand is BAD OPERAND TYPE.
// expect: error E_OPERAND 5
int main(void)
{
    return 5 % 2.0;
}
