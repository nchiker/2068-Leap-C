// Compound assignment and ++/-- on struct members, via . and ->.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct c { unsigned n; char b; int arr[3]; };
struct c g;
int main(void)
{
    struct c *p;
    p = &g;
    g.n = 65535;
    g.n++;
    ck(1, g.n, 0);
    p->b = 250;
    p->b += 10;
    ck(2, g.b, 4);
    p->arr[1] = 5;
    p->arr[1] *= 3;
    ck(3, g.arr[1], 15);
    ck(4, p->arr[1]--, 15);
    ck(5, g.arr[1], 14);
    ck(6, --p->arr[1], 13);
    return bad;
}
