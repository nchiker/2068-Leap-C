// 15 pending words of f and 18 of g: 33, NESTING TOO DEEP at g's line.
// expect: error E_NESTING 7
int f();
int g();
int main(void)
{
    return f(g(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18),
             2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16);
}
int f(int a) { return a; }
int g(int a) { return a; }
