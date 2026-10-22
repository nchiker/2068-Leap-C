// ?: with a void and a float operand: TYPE MISMATCH (C89 6.3.15).
// expect: error E_TYPE 7
int k;
void v(void) { }
int main(void)
{
    k ? v() : 1.5;
    return 0;
}
