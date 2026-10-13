// A pointer to an incomplete struct, completed later: the same type.
// sym: p obj *struct t
// sym: v obj struct t size=3
// tag: t struct size=3
struct t *p;
struct t { int a; char b; };
struct t v;
