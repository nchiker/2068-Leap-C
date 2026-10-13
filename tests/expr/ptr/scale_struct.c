// Pointer arithmetic over a 5-byte struct and over 3-byte array rows (pointer to array).
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct s { int a; int b; char c; };
struct s v[6];
typedef char row[3];
row m[4];
int main(void)
{
    struct s *p;
    row *q;
    int i;
    p = v;
    i = 4;
    ck(1, (int)(p + i) - (int)v, 20);
    p = p + 2;
    p->b = 77;
    ck(2, v[2].b, 77);
    ck(3, (p + 1) - v, 3);
    p++;
    ck(4, p - v, 3);
    --p;
    ck(5, p - v, 2);
    q = m;
    q += 2;
    ck(6, (int)q - (int)m, 6);
    (*q)[1] = 'z';
    ck(7, m[2][1], 'z');
    ck(8, q - m, 2);
    return bad;
}
