// Macros inside declarators (the compiler rescans those too): pointers to arrays, parameters.
// expect: exit 0
#define N 3
#define PTR *
#define ROW (*rows)[N]
int m[2][N];
int sum(int ROW, int n)
{
    int i;
    int j;
    int s;
    s = 0;
    for (i = 0; i < n; i++)
        for (j = 0; j < N; j++)
            s += rows[i][j];
    return s;
}
int main(void)
{
    int PTR p;
    int (*q)[N];
    int i;
    for (i = 0; i < 2 * N; i++) m[i / N][i % N] = i;
    q = m;
    p = &m[1][2];
    if (*p != 5) return 1;
    if (q[1][0] != 3) return 2;
    return sum(m, 2) - 15;
}
