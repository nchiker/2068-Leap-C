// A table of function pointers used in a loop and a switch.
// expect: exit 0
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }
int (*ops[3])(int, int) = { add, sub, mul };
int apply(int op, int a, int b)
{
    switch (op) {
    case 0: case 1: case 2: return ops[op](a, b);
    }
    return -1;
}
int main(void)
{
    int i;
    int r;
    r = 0;
    for (i = 0; i < 3; i++) r = r * 100 + apply(i, 7, 3);
    if (r != 10 * 10000 + 4 * 100 + 21) return 1;
    if (apply(3, 1, 1) != -1) return 2;
    return 0;
}
