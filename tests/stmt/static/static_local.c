// static locals keep their values between calls; initialised once.
// expect: exit 0
int counter(void)
{
    static int n;
    static int start = 100;
    n++;
    return start + n;
}
int depth(int k)
{
    static int calls;
    calls++;
    if (k > 0) return depth(k - 1);
    return calls;
}
int main(void)
{
    counter();
    counter();
    if (counter() != 103) return 1;
    if (depth(5) != 6) return 2;
    if (depth(0) != 7) return 3;
    return 0;
}
