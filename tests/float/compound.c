// Compound assignment with floats (Phase 8): float objects with float and integer right operands, an
// integer object with a float right operand (the result truncated), through pointers and arrays.
// expect: exit 0
// mem: a+0 8434000000808000000083100000008848000000
// mem: n+0 08001900fbff
float a[4] = { 10.0, 2.5, -1.0, 100.0 };
int n[3] = { 7, 100, -5 };
float g = 0.5;
int main(void)
{
    float *p;
    int i;
    p = a;
    a[0] += 1.25;
    p[1] -= 3;
    i = 2;
    a[i] *= -4.5;
    *(p + 3) /= g;
    n[0] += 1.7;
    n[1] *= 0.25;
    n[2] -= g;
    return 0;
}
