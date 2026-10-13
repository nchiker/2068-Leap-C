// Locals of sibling blocks share frame bytes; each block sees its own values.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    int a;
    a = 1;
    {
        int b;
        b = 2;
        a += b;
    }
    {
        int c;
        int d;
        c = 3;
        d = 4;
        a += c * d;
    }
    ck(1, a, 15);
    return bad;
}
