// Casts between pointers and integers, and between pointer types.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int w;
int main(void)
{
    int *p;
    char *c;
    unsigned a;
    p = &w;
    a = (unsigned)p;
    c = (char *)p;
    *c = 0x34;
    *(c + 1) = 0x12;
    ck(1, w, 0x1234);
    ck(2, (int *)a == p, 1);
    ck(3, (unsigned)(p + 1) - a, 2);
    ck(4, (unsigned)((char *)p + 1) - a, 1);
    return bad;
}
