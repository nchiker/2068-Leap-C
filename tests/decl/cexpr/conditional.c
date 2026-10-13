// sym: A enumc int val=10
// sym: B enumc int val=20
// sym: C enumc int val=3
// sym: u obj [2]char
enum { A = 1 ? 10 : 20, B = 0 ? 10 : 20, C = 1 ? 0 ? 1 : 3 : 5 };
char u[sizeof(1 ? 1 : 2u)];
