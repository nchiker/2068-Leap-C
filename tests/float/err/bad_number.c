// A malformed floating constant: BAD NUMBER.
// expect: error E_NUMBER 6
int main(void)
{
    float f;
    f = 1.5e+x;
    return 0;
}
