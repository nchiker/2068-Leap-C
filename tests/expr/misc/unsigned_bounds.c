// Signed/unsigned boundaries: -32768, 32767, 65535; mixed comparisons convert to unsigned.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    int i;
    unsigned u;
    i = 32767;
    i++;
    ck(1, i == -32767 - 1, 1);
    ck(2, i < 0, 1);
    u = 0;
    u--;
    ck(3, u == 65535, 1);
    ck(4, -1 < u, 0);
    ck(5, (unsigned)i > 32767, 1);
    ck(6, i / -1 == i, 1);
    ck(7, i % -1, 0);
    ck(8, -i == i, 1);
    ck(9, u / 3, 21845);
    ck(10, u % 10, 5);
    return bad;
}
