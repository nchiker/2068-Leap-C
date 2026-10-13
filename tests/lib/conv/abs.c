// abs(n); abs(-32768) wraps to -32768 (C: undefined; here as the two's complement).
// expect: exit 0
int main(void)
{
    if (abs(5) != 5 || abs(-5) != 5 || abs(0) != 0 || abs(-32767) != 32767) return 1;
    if (abs(-32768) != -32768) return 2;
    return 0;
}
