// A definition: parameters are in the body's outer scope with argument offsets 0, 2, 4.
// sym: add func fn(int,int,*char)int flags=defined
// local: a obj int val=0 flags=param
// local: b obj int val=2 flags=param
// local: s obj *char val=4 flags=param
int add(int a, int b, char *s) { }
