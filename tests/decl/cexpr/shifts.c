// << and >> (signed >> is arithmetic: spec.md 4.4); the result has the left operand's type.
// sym: A enumc int val=256
// sym: B enumc int val=-4
// sym: C enumc int val=16383
// sym: D enumc int val=0
// sym: E enumc int val=-1
// sym: F enumc int val=-32768
enum { A = 1 << 8, B = -16 >> 2, C = 65535u >> 2, D = 1 << 16, E = -1 >> 20, F = 1 << 15 };
