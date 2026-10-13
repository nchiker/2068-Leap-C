// Arrays of function pointers in static data, called by index; pointers compared; (*p)() calls.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }
int (*ops[3])(int, int) = { add, sub, mul };
int main(void)
{
    int i;
    i = 2;
    ck(1, ops[0](6, 3), 9);
    ck(2, ops[1](6, 3), 3);
    ck(3, ops[i](6, 3), 18);
    ck(4, (*ops[i - 1])(10, 4), 6);
    ck(5, ops[2] == mul, 1);
    ck(6, ops[0] != ops[1], 1);
    return bad;
}
