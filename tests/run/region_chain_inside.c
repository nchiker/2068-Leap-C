// Code crosses from image region 1 into region 2 inside a function: 202 bytes are left for code
// in region 1, the function needs about 300, and the compiler links the parts with a jp.
// expect: exit 0
// region: first 1
// region: second 2
char big[7990];
int g;
int first(void)
{
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    return g;
}
int second(void) { return 5; }
int main(void) { g = 0; return first() - 40 + second() - 5; }
