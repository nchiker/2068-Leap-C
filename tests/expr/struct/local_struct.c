// Structs in the frame: members by . and through a pointer to the local; struct pointer parameters.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct pt { int x; int y; char tag; };
void move(struct pt *p, int dx, int dy) { p->x += dx; p->y += dy; p->tag++; }
int main(void)
{
    struct pt a;
    struct pt *q;
    a.x = 10; a.y = 20; a.tag = 'a';
    move(&a, 3, -4);
    ck(1, a.x, 13);
    ck(2, a.y, 16);
    ck(3, a.tag, 'b');
    q = &a;
    q->y = q->x * 2;
    ck(4, a.y, 26);
    return bad;
}
