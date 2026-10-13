// Multi-dimensional arrays: indexing with run-time and constant subscripts, row decay, element addresses.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int m[3][4];
char c[2][3][5];
int main(void)
{
    int i;
    int j;
    int *row;
    i = 2; j = 3;
    m[i][j] = 23;
    m[1][2] = 12;
    ck(1, m[2][3], 23);
    ck(2, m[i - 1][j - 1], 12);
    row = m[1];
    ck(3, row[2], 12);
    ck(4, (int)&m[2][0] - (int)m, 16);
    c[1][2][4] = 'q';
    ck(5, c[i - 1][i][j + 1], 'q');
    ck(6, (int)&c[1][2][4] - (int)c, 29);
    ck(7, sizeof m[1], 8);
    ck(8, sizeof c[1], 15);
    ck(9, *(*(m + 2) + 3), 23);
    return bad;
}
