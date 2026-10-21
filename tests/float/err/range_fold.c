// A constant expression beyond the range, or a constant division by 0, fails at compile time.
// expect: error E_RANGE 3
float f = 1.0 / 0.0;
int main(void)
{
    return 0;
}
