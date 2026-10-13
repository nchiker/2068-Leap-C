// Addresses of locals and parameters: pointers into the frame, written through.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
void set(int *p, int v) { *p = v; }
int f(int a)
{
    int b;
    set(&a, 10);
    set(&b, 20);
    return a + b;
}
int main(void)
{
    int x;
    char y;
    char *py;
    set(&x, 3);
    py = &y;
    *py = 'k';
    ck(1, x, 3);
    ck(2, y, 'k');
    ck(3, f(1), 30);
    return bad;
}
