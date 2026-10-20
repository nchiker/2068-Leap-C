// The argument words pending in the enclosing calls count: when g's arguments are counted, f's
// 15 later arguments are already pushed (arguments are evaluated last first). 15 + 17 = 32.
// expect: exit 33
int f();
int g();
int main(void)
{
    return f(g(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
             2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16);
}
int f(int a, int b) { return a + b; }
int g(int a, int b) { return a + b + 28; }
