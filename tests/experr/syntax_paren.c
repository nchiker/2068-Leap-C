// A parenthesis not closed.
// expect: error E_SYNTAX 6
int main(void)
{
    int x;
    x = (1 + 2; /*E*/
    return 0;
}
