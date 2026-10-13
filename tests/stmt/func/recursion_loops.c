// Recursion with loops inside: the number of partitions of n (p(20) = 627).
// expect: exit 627
int parts(int n, int max)
{
    int k;
    int t;
    if (n == 0) return 1;
    t = 0;
    for (k = 1; k <= max && k <= n; k++)
        t += parts(n - k, k);
    return t;
}
int main(void) { return parts(20, 20); }
