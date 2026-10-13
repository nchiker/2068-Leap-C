// Recursion: factorial, as in the code-shape spike.
// expect: exit 5040
int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }
int main(void) { return fact(7); }
