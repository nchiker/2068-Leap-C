// C89 precedence and associativity of the binary operators.
// sym: A enumc int val=7
// sym: B enumc int val=1
// sym: C enumc int val=2
// sym: D enumc int val=1
// sym: E enumc int val=12
// sym: F enumc int val=1
// sym: G enumc int val=6
enum { A = 1 + 2 * 3, B = 10 - 5 - 4, C = 16 / 4 / 2, D = 1 < 2 == 1,
       E = 1 << 2 + 1 | 4, F = 1 | 2 && 0 || 1, G = 3 & 2 | 4 ^ 0 };
