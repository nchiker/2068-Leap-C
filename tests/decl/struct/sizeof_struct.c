// sym: a obj [9]char
// sym: b obj [18]char
// sym: c obj [2]char
struct s { int x; char c[7]; };
char a[sizeof(struct s)];
char b[sizeof(struct s [2])];
char c[sizeof(struct s *)];
