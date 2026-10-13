// Calls nested in arguments, in operands on both sides of operators, and in conditions.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int sq(int x) { return x * x; }
int add(int a, int b) { return a + b; }
int main(void)
{
    ck(1, add(sq(2), sq(3)), 13);
    ck(2, sq(add(1, 2)) - add(sq(1), 1), 7);
    ck(3, sq(sq(2)) / add(1, 1), 8);
    ck(4, add(sq(2), 1) > sq(2) ? add(1, 2) : sq(5), 3);
    ck(5, add(add(add(1, 2), add(3, 4)), add(5, add(6, 7))), 28);
    return bad;
}
