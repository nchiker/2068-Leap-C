// Unsigned division over 3,000 operand pairs, divisors from 1 to 65535: q * b + r == a and r < b
// (the helper core's RT_UDIV, its 17-bit remainder included; Phase 9: ROM coverage).
// expect: exit 0
// maxi: 400000000
unsigned x = 12345;
unsigned next(void)
{
    x ^= x << 7;
    x ^= x >> 9;
    x ^= x << 8;
    return x;
}
int main(void)
{
    unsigned a, b, q, r;
    int k;
    for (k = 0; k < 3000; k++) {
        a = next();
        b = next() | (k & 1 ? 32768u : 0);
        if (b == 0)
            b = 1;
        q = a / b;
        r = a % b;
        if (q * b + r != a || r >= b)
            return k + 1;
    }
    return 0;
}
