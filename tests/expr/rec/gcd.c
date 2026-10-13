// Euclid with % and recursion; unsigned arguments.
// expect: exit 6063
unsigned gcd(unsigned a, unsigned b) { return b ? gcd(b, a % b) : a; }
int main(void) { return gcd(65520, 1071) + gcd(48, 18) * 1000; }
