// Enumerator values can use earlier enumerators.
// sym: A enumc int val=4
// sym: B enumc int val=16
// sym: C enumc int val=17
// sym: D enumc int val=255
enum { A = 4, B = A * A, C, D = (1 << 8) - 1 };
