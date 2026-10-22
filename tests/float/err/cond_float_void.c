// ?: with a float and a void operand: TYPE MISMATCH (C89 6.3.15), in either order.
// expect: error E_TYPE 7
int k;
void v(void) { }
int main(void)
{
    k ? 1.5 : v();
    return 0;
}
