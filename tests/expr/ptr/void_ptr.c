// void * converts to and from other object pointers without a cast.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int x;
char b[4];
int main(void)
{
    void *v;
    int *p;
    char *c;
    v = &x;
    p = v;
    *p = 42;
    ck(1, x, 42);
    v = b;
    c = v;
    c[2] = 9;
    ck(2, b[2], 9);
    ck(3, (char *)v + 2 == &b[2], 1);
    return bad;
}
