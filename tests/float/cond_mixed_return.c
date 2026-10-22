// ?: with a float and an integer operand in a return and an argument (C89 6.3.15: the integer is converted,
// then the float result converts to the function's type); nested ?: with mixed arms; a char and a signed char arm.
// expect: exit 0
// screen: 0 2.5 -3.0 7.0
int f(int k) { return k ? 1.5 : 2; }
int g(int k) { return k ? 2 : 1.5; }
float h(float x) { return x; }
int main(void)
{
    char c = 200;
    signed char s = -3;
    int k = 1;
    if (f(0) != 2 || f(1) != 1 || g(0) != 1 || g(1) != 2)
        return 1;
    if (h(k ? c : 0.5) != 200 || h(!k ? c : 0.5) != 0.5)
        return 2;
    printf("%.1f %.1f %.1f", k ? (k ? 2.5 : 1) : 0, k ? s : 0.25, !k ? 0.5 : k ? 7 : 1.5);
    return 0;
}
