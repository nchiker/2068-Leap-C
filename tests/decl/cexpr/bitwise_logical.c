// sym: A enumc int val=0x0F00
// sym: B enumc int val=0x0FF3
// sym: C enumc int val=0x00F3
// sym: D enumc int val=-256
// sym: E enumc int val=1
// sym: F enumc int val=0
// sym: G enumc int val=1
// sym: H enumc int val=0
// sym: I enumc int val=1
enum { A = 0x0FF0 & 0xFF00, B = 0x0FF0 | 0x0003, C = 0x0FF0 ^ 0x0F03, D = ~0xFF,
       E = 2 && 3, F = 2 && 0, G = 0 || 7, H = !5, I = !0 };
