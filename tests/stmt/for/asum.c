// The spike's `asum`: the single-pass for layout.
// expect: exit 4950
int a[100];
int asum(int n)
{
    int i;
    int t;
    t = 0;
    for (i = 0; i < n; i++)
        t += a[i];
    return t;
}
int main(void)
{
    int i;
    for (i = 0; i < 100; i++) a[i] = i;
    return asum(100);
}
