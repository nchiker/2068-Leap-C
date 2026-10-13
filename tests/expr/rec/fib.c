// Double recursion: fib(15).
// expect: exit 610
int fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
int main(void) { return fib(15); }
// noaudit
