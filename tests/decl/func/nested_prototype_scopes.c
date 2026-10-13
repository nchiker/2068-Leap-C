// Parameter names in nested prototypes are local to their prototype scope.
// sym: f func fn(*fn(int)int,int)void flags=defined
// local: x obj int flags=param val=0
// local: cb obj *fn(int)int flags=param val=0
// local: n obj int flags=param val=2
void f(int (*cb)(int x), int n) { }
