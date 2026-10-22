// Unsigned division by a divisor above 32767: the remainder needs 17 bits on the way (RT_UDIV)
// (Phase 9: ROM coverage).
// expect: exit 0
unsigned a = 65535u, b = 40000u;
int main(void)
{
    if (a / b != 1 || a % b != 25535u)
        return 1;
    if (60001u / 30000u != 2 || 60001u % 30000u != 1)
        return 2;
    return 0;
}
