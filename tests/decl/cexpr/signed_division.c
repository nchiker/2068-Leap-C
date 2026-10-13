// Signed / truncates toward zero; % has the dividend's sign (spec.md 4.4).
// sym: A enumc int val=-3
// sym: B enumc int val=-2
// sym: C enumc int val=2
// sym: D enumc int val=-3
// sym: E enumc int val=0
// sym: F enumc int val=0
enum { A = -7 / 2, B = -17 % 5, C = 17 % -5, D = 7 / -2, E = 5 / 0, F = 5 % 0 };
