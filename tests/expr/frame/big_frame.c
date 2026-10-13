// A 190-byte frame: locals more than 128 bytes below IX are reached through address templates.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int deep(int a, int b)
{
    char pad[180];
    int far1;
    int near1;
    char farc;
    far1 = a;
    near1 = b;
    farc = 77;
    pad[0] = 1;
    pad[179] = 2;
    far1 += pad[0] + pad[179];
    farc++;
    return far1 * 100 + near1 + farc;
}
int main(void) { ck(1, deep(5, 6), 884); return bad; }
