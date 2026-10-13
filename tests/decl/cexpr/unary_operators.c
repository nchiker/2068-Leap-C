// sym: A enumc int val=5
// sym: B enumc int val=-5
// sym: C enumc int val=-1
// sym: D enumc int val=0
// sym: u obj [2]char
// sym: v obj [2]char
enum { A = +5, B = -+5, C = ~0, D = ~65535u };
char u[sizeof(-(char)1)];
char v[sizeof(~(unsigned char)1)];
