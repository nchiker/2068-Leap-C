// An index without its `]`.
// expect: error E_SYNTAX 6
int a[3];
int main(void)
{
    return a[1; /*E*/
}
