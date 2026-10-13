// Unsigned operands make the operation unsigned (spec.md 4.3).
// sym: A enumc int val=32767
// sym: B enumc int val=1
// sym: C enumc int val=0
// sym: D enumc int val=21845
// sym: E enumc int val=1
enum { A = 65535u >> 1, B = -1 > 0u, C = -1 > 0, D = 65535u / 3, E = 40000 > 30000 };
