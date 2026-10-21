// Pointer arithmetic takes an integer, not a float.
// expect: error E_OPERAND 6
char s[4];
int main(void)
{
    return *(s + 1.0);
}
