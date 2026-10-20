// 33 argument words pending: NESTING TOO DEEP (the stack between two frame checks must stay
// within ENTER's margin, include/leapc_layout.inc).
// expect: error E_NESTING 9
int f();
int main(void)
{
    return f(
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    27, 28, 29, 30, 31, 32, 33
    );
}
int f(int a) { return a; }
