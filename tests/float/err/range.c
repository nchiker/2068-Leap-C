// A floating constant beyond the range (about 1.7e38): NUMBER TOO LARGE.
// expect: error E_RANGE 6
int main(void)
{
    float f;
    f = 3.5e38;
    return 0;
}
