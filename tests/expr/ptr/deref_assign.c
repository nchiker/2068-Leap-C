// Loads and stores through pointers: words (LDI/STI), bytes, signed bytes; values of the assignments.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int w;
char c;
signed char sc;
unsigned u;
int main(void)
{
    int *pw;
    char *pc;
    signed char *ps;
    unsigned *pu;
    pw = &w; pc = &c; ps = &sc; pu = &u;
    ck(1, *pw = 1234, 1234);
    ck(2, w, 1234);
    ck(3, *pc = 300, 44);
    ck(4, c, 44);
    ck(5, *ps = 200, -56);
    ck(6, sc, -56);
    ck(7, *ps, -56);
    *pu = 65535;
    ck(8, *pu > 32767, 1);
    ck(9, *pw + *pc, 1278);
    *pw = *pc = 7;
    ck(10, w, 7);
    return bad;
}
