// A call in an array size.
// expect: error E_CONSTEXPR 6
int f(void) { return 3; }
int main(void)
{
    int a[f()]; /*E*/
    return 0;
}
