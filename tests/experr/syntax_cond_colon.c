// A conditional without its `:`.
// expect: error E_SYNTAX 7
int main(void)
{
    int x;
    x = 1;
    x = x ? 2 ; /*E*/
    return 0;
}
