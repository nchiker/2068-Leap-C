// Pointers to different types need a cast.
// expect: error E_TYPE 8
int main(void)
{
    int *p;
    char *q;
    q = 0;
    p = q; /*E*/
    return 0;
}
