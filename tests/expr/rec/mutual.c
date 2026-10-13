// Mutual recursion through a prototype.
// expect: exit 11
int odd(int);
int even(int n) { return n == 0 ? 1 : odd(n - 1); }
int odd(int n) { return n == 0 ? 0 : even(n - 1); }
int main(void) { return even(40) * 10 + odd(7); }
