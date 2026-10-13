// 180 levels of recursion with a parameter and a local fit the stack (about 8 bytes per level).
// expect: exit 16290
// noaudit
int sum(int n)
{
    int k;
    k = n;
    return n ? k + sum(n - 1) : 0;
}
int main(void) { return sum(180); }
