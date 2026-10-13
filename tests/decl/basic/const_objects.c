// const marks the object (spec.md 4.2), not a pointer's target; arrays: their elements.
// sym: a obj int flags=const
// sym: p obj *char flags=
// sym: q obj *char flags=
// sym: v obj [2]int flags=const
// sym: w obj uint flags=const
const int a;
const char *p;
char * const q;
const int v[2];
unsigned const w;
