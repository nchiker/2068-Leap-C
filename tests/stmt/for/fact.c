// The spike's `fact` with if and return.
// expect: exit 5040
int fact(int n)
{
    int r;
    if (n <= 1)
        return 1;
    r = n * fact(n - 1);
    return r;
}
int main(void) { return fact(7); }
