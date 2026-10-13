// A pointer cannot take a nonzero integer.
// expect: error E_TYPE 6
int main(void)
{
    int *p;
    p = 5; /*E*/
    return 0;
}
