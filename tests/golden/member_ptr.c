// Golden: A member through a pointer: the offset with inc hl, then rst LDI.
// golden: f DF00 DD6E04DD6605 2323 CF E7
// expect: exit 0
struct s { int x; int y; };
int f(struct s *p) { return p->y; }
int main(void) { return 0; }
