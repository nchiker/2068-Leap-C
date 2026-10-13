// A struct defined in a block is a new type there; the outer tag is unchanged.
// tag: s struct size=2 members=a@0:int
// local: in obj [5]char
// sym: out obj [2]char
struct s { int a; };
void f(void) { struct s { char b[5]; } v; char in[sizeof v]; }
char out[sizeof(struct s)];
