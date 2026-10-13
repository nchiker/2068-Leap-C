// An integer cannot take a pointer.
// expect: error E_TYPE 8
int main(void)
{
    int x;
    int *p;
    p = 0;
    x = p; /*E*/
    return 0;
}
