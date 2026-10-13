// Mutual recursion through a prototype; forward calls resolved later.
// expect: exit 0
int odd(int n);
int even(int n) { if (n == 0) return 1; return odd(n - 1); }
int odd(int n) { if (n == 0) return 0; return even(n - 1); }
int main(void)
{
    if (!even(10) || even(7)) return 1;
    if (!odd(9) || odd(4)) return 2;
    return later(3) - 9;
}
int later(int x) { return x * 3; }
