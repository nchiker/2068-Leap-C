// Casts truncate and extend constants (char is unsigned; signed char sign-extends).
// sym: A enumc int val=44
// sym: B enumc int val=-56
// sym: C enumc int val=200
// sym: D enumc int val=-1
// sym: E enumc int val=255
enum { A = (char)300, B = (signed char)200, C = (unsigned char)200, D = (int)65535u,
       E = (char)-1 };
