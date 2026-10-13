// `struct s;` in a block declares a new incomplete s there (C89 6.5.2.3); it can then be
// completed in the block without touching the file-scope s.
// local: k obj [3]char flags=auto
// tag: s struct size=2 members=a@0:int
// sym: out obj [2]char
struct s { int a; };
void f(void) { struct s; struct s *p; struct s { char c[3]; } v; char k[sizeof v]; }
char out[sizeof(struct s)];
