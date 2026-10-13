// Member access chains through ., -> and nested structs; self-referential lists.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct node { int v; struct node *next; };
struct node n1;
struct node n2;
struct node n3;
struct wrap { int pad; struct node inner; struct node *ptr; };
struct wrap w;
int main(void)
{
    struct node *p;
    n1.v = 1; n2.v = 2; n3.v = 3;
    n1.next = &n2; n2.next = &n3; n3.next = 0;
    p = &n1;
    ck(1, p->next->next->v, 3);
    ck(2, p->next->v + n1.next->next->v, 5);
    ck(3, p->next->next->next == 0, 1);
    w.inner.v = 11;
    w.ptr = &w.inner;
    w.ptr->next = &n2;
    ck(4, w.ptr->v, 11);
    ck(5, w.inner.next->v, 2);
    ck(6, (&w)->ptr->next->next->v, 3);
    return bad;
}
