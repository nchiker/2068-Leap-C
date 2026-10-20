// A constant above 65535.
// expect: error E_RANGE 6
int main(void)
{
    int x;
    x = 70000;
    return x;
}
