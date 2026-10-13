// Arguments are pushed right to left (first argument lowest), all evaluated, and popped by the caller.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int f(int a, int b, int c, int d) { return a * 1000 + b * 100 + c * 10 + d; }
int g6(int a, int b, int c, int d, int e, int f) { return a - b + c - d + e - f; }
int seq;
int nx(void) { return ++seq; }
int main(void)
{
    ck(1, f(1, 2, 3, 4), 1234);
    ck(2, g6(60, 50, 40, 30, 20, 10), 30);
    seq = 0;
    ck(3, f(nx(), nx(), nx(), nx()), 4321);
    ck(4, f(f(0, 0, 0, 1), 2, f(0, 0, 0, 3), 4), 1234);
    return bad;
}
