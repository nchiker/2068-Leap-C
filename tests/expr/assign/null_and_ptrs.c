// Assignments of null pointer constants and between compatible pointers.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct s { int a; };
struct s v;
int main(void)
{
    struct s *p;
    struct s *q;
    char *c;
    p = 0;
    ck(1, p == 0, 1);
    p = &v;
    q = p;
    q->a = 3;
    ck(2, v.a, 3);
    c = (char *)p;
    ck(3, (int)c == (int)&v, 1);
    return bad;
}
