// Deep recursion with two parameters: ackermann(2, 3).
// expect: exit 9
int ack(int m, int n) { return m == 0 ? n + 1 : n == 0 ? ack(m - 1, 1) : ack(m - 1, ack(m, n - 1)); }
int main(void) { return ack(2, 3); }
// noaudit
