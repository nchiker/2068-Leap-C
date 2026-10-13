// Parameters and the body's outer declarations share one scope; the body's locals start at 0.
// local: n obj int flags=param val=0
// local: p obj *char flags=param val=2
// local: i obj int flags=auto val=0
// local: s obj [4]char flags=auto val=2
void f(int n, char *p) { int i; char s[sizeof n * 2]; }
