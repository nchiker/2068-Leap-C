// The spike's `move` (a while over structs through a pointer).
// expect: exit 0
struct pt { int x; int y; char c; };
struct pt pts[20];
void move(struct pt *p, int n, int dx)
{
    while (n--) {
        p->x += dx;
        p->y += p->x;
        p++;
    }
}
int main(void)
{
    int i;
    for (i = 0; i < 20; i++) { pts[i].x = i; pts[i].y = 0; }
    move(pts, 20, 3);
    for (i = 0; i < 20; i++)
        if (pts[i].x != i + 3 || pts[i].y != i + 3) return i + 1;
    return 0;
}
