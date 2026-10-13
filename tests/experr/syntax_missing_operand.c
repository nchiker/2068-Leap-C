// A binary operator without its right operand.
// expect: error E_SYNTAX 6
int main(void)
{
    int x;
    x = 1 + ; /*E*/
    return 0;
}
