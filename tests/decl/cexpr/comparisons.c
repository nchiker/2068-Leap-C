// sym: A enumc int val=1
// sym: B enumc int val=0
// sym: C enumc int val=1
// sym: D enumc int val=1
// sym: E enumc int val=0
// sym: F enumc int val=1
// sym: G enumc int val=1
// sym: H enumc int val=0
// 32768 is an unsigned int (M1.1), so -32768 is the unsigned 32768:
// sym: I enumc int val=0
enum { A = 3 < 4, B = 3 > 4, C = 4 <= 4, D = 5 >= 4, E = 3 == 4, F = 3 != 4,
       G = (-32767 - 1) < 32767, H = 32768 < 32767, I = -32768 < 32767 };
