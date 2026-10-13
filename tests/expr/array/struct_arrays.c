// Arrays of structs with array members: member chains, indexes and offsets.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct item { char name[4]; int qty; struct { int x; int y; } pos; };
struct item inv[3];
int main(void)
{
    int i;
    i = 2;
    inv[i].qty = 5;
    inv[i].name[3] = 'Z';
    inv[1].pos.y = -9;
    ck(1, inv[2].qty, 5);
    ck(2, inv[i].name[3], 'Z');
    ck(3, inv[i - 1].pos.y, -9);
    ck(4, (int)&inv[1].pos.y - (int)inv, 18);
    ck(5, sizeof inv[0], 10);
    return bad;
}
