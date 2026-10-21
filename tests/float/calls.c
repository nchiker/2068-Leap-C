// Float arguments and results (Phase 8; spec.md 5.2): a float argument is 3 words (5 bytes and a pad),
// mixed with int and char arguments; recursion; function pointers and an array of them; a function
// without a prototype; library functions taking int arguments convert a float (C89 6.3.2.2).
// expect: exit 0
// mem: r+0 84000000008373000000841c0000008360000000
// mem: r+20 842000000082400000007f500000008100000000
// mem: c+0 0300 0700 4100
float r[8];
int c[3];
float mix(int a, float b, char c, float d, int e)
{
    return a + b * c - d / e;
}
float pw(float x, int n)
{
    if (n == 0)
        return 1.0;
    return x * pw(x, n - 1);
}
float add(float x, float y) { return x + y; }
float sub(float x, float y) { return x - y; }
float (*ops[2])(float, float) = { add, sub };
float late();
int main(void)
{
    float (*f)(float, float);
    int i;
    i = 0;
    r[i++] = mix(1, 2.5, 4, 9.0, 3);
    r[i++] = pw(1.5, 5);
    f = sub;
    r[i++] = f(10.0, 0.25);
    r[i++] = ops[0](1.0, ops[1](8.0, 2));
    r[i++] = late(2.5, 4);
    r[i++] = add(1, 2);
    r[i++] = (*ops[1])(r[0], r[1]);
    r[i++] = pw(2, 10) / 1024;
    c[0] = abs(-3.75);
    c[1] = (int)add(3.5, 4.0);
    c[2] = 'A' + 0.75;
    return 0;
}
float late(float x, int k)
{
    return x * k;
}
