// The spike's `sum`: while with a compound assignment and a pre-decrement.
// expect: exit 32640
int sum(int n)
{
    int s;
    s = 0;
    while (n) {
        s += n;
        --n;
    }
    return s;
}
int main(void) { return sum(255); }
