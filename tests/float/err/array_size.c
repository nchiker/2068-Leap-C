// An array size must be an integer constant expression; a float one needs a cast.
// expect: error E_CONSTEXPR 3
int a[2.5];
int main(void)
{
    return 0;
}
