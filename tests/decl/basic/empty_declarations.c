// `struct s {...};` and `enum {...};` declare tags/constants only; no objects.
// tag: s struct size=2
// sym: K enumc int val=4
// nosym: s
struct s { int x; };
enum { K = 4 };
