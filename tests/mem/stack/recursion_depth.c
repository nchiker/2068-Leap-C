// The deepest recursion of the reference function (one int parameter, one int local: 8 bytes a
// level) from main: it ends with a stack overflow at the floor, and `depth` records how deep it got:
// 190 levels, ($FEF2 - $F900) / 8.
// The value pins the stack's capacity (include/leapc_layout.inc: frames from the program's start
// down to the floor $F900).
// expect: rterror 1
// mem: depth be00
// noaudit
int depth;
int f(int n)
{
    int x;
    x = n;
    depth = n;
    return f(n + 1) + x;
}
int main(void)
{
    return f(1);
}
