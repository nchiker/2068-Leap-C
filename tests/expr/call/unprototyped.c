// Calls to functions declared without a prototype: default promotions.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int f();
int g() { return 7; }
int main(void)
{
    char c;
    c = 250;
    ck(1, f(c, 5), 255);
    ck(2, g(), 7);
    return bad;
}
int f(int a, int b) { return a + b; }
