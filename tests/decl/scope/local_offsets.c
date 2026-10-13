// Automatic objects get frame offsets in declaration order (spec.md 5.2: IX+0 upward).
// local: a obj int flags=auto val=0
// local: c obj char flags=auto val=2
// local: buf obj [10]char flags=auto val=3
// local: p obj *int flags=auto val=13
// frame: 15
void f(void) { int a; char c; char buf[10]; int *p; }
