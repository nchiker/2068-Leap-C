// 32 argument words pending at once (LEAPC_ARGS_MAX) are allowed: a call of a function without
// a prototype with 32 arguments, and printf with its format and 31 values.
// expect: exit 33
// screen: 0 1234567890123456
// screen: 1 789012345678901
int f();
int main(void)
{
    printf("%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d\n%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d",
           1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7,
           8, 9, 0, 1);
    return f(
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    27, 28, 29, 30, 31, 32
    );
}
int f(int a, int b) { return a + b + 30; }
