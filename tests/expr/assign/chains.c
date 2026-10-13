// Assignment chains, the value and type of an assignment, assignments inside operands.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int x;
int y;
char c;
int main(void)
{
    int z;
    x = y = z = 5;
    ck(1, x + y + z, 15);
    x = (c = 0x1FF) + 1;
    ck(2, x, 256);
    ck(3, c, 255);
    y = 2;
    ck(4, (y = y * 3) + 1, 7);
    z = x = 7;
    ck(5, z, 7);
    ck(6, (x += 3) * 2, 20);
    return bad;
}
