// Timing fixture (Phase 9): recursion (calls, frames on the stack at $F800-$FEFF).
int fib(int n)
{
    return n < 2 ? n : fib(n - 1) + fib(n - 2);
}
int main(void)
{
    return fib(18);
}
